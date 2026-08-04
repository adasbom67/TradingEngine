from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.api.recommendations import RecommendationConstraints


PROFILE_PATH = Path("config/trading_profiles.json")


class TradingProfile(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    symbols: list[str] = Field(default_factory=list, max_length=20)
    constraints: RecommendationConstraints = Field(
        default_factory=RecommendationConstraints
    )
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = re.sub(r"\s+", " ", value.strip())
        if not normalized:
            raise ValueError("Profile name cannot be blank.")
        return normalized

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            symbol = value.strip().upper()
            if symbol and symbol not in result:
                result.append(symbol)
        return result


class ProfileRenameRequest(BaseModel):
    new_name: str = Field(min_length=1, max_length=80)


class ProfileDuplicateRequest(BaseModel):
    new_name: str = Field(min_length=1, max_length=80)


class TradingProfileStore:
    def __init__(self, path: Path = PROFILE_PATH) -> None:
        self._path = path

    def list_profiles(self) -> list[dict[str, Any]]:
        payload = self._read()
        return sorted(
            payload,
            key=lambda item: (
                not bool(item.get("is_default")),
                item["name"].lower(),
            ),
        )

    def get(self, name: str) -> dict[str, Any] | None:
        target = name.strip().casefold()
        return next(
            (
                profile
                for profile in self.list_profiles()
                if profile["name"].casefold() == target
            ),
            None,
        )

    def save(self, profile: TradingProfile) -> dict[str, Any]:
        profiles = self.list_profiles()
        serialized = profile.model_dump(mode="json")
        replaced = False

        for index, existing in enumerate(profiles):
            if existing["name"].casefold() == profile.name.casefold():
                if existing.get("is_default") and not profile.is_default:
                    serialized["is_default"] = True
                profiles[index] = serialized
                replaced = True
                break

        if not replaced:
            profiles.append(serialized)

        if serialized.get("is_default"):
            profiles = self._with_single_default(profiles, profile.name)

        self._write(profiles)
        return self.get(profile.name) or serialized

    def delete(self, name: str) -> bool:
        profiles = self.list_profiles()
        remaining = [
            profile
            for profile in profiles
            if profile["name"].casefold() != name.strip().casefold()
        ]
        if len(remaining) == len(profiles):
            return False
        self._write(remaining)
        return True

    def rename(self, name: str, new_name: str) -> dict[str, Any] | None:
        existing = self.get(name)
        if existing is None:
            return None

        normalized_new = TradingProfile(
            name=new_name,
            symbols=existing.get("symbols", []),
            constraints=existing.get("constraints", {}),
            is_default=bool(existing.get("is_default")),
        )
        if (
            name.strip().casefold() != normalized_new.name.casefold()
            and self.get(normalized_new.name) is not None
        ):
            raise ValueError("A profile with the new name already exists.")

        self.delete(name)
        return self.save(normalized_new)

    def duplicate(self, name: str, new_name: str) -> dict[str, Any] | None:
        existing = self.get(name)
        if existing is None:
            return None
        if self.get(new_name) is not None:
            raise ValueError("A profile with the new name already exists.")

        duplicate = TradingProfile(
            name=new_name,
            symbols=existing.get("symbols", []),
            constraints=existing.get("constraints", {}),
            is_default=False,
        )
        return self.save(duplicate)

    def set_default(self, name: str) -> dict[str, Any] | None:
        existing = self.get(name)
        if existing is None:
            return None
        profiles = self._with_single_default(self.list_profiles(), name)
        self._write(profiles)
        return self.get(name)

    @staticmethod
    def _with_single_default(
        profiles: list[dict[str, Any]],
        name: str,
    ) -> list[dict[str, Any]]:
        target = name.strip().casefold()
        for profile in profiles:
            profile["is_default"] = profile["name"].casefold() == target
        return profiles

    def _read(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read trading profiles: {exc}") from exc

        if not isinstance(payload, list):
            raise RuntimeError("Trading profiles file must contain a JSON list.")

        return [
            TradingProfile.model_validate(item).model_dump(mode="json")
            for item in payload
        ]

    def _write(self, profiles: list[dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(
            prefix="trading_profiles_",
            suffix=".json",
            dir=str(self._path.parent),
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(profiles, stream, indent=2, sort_keys=True)
                stream.write("\n")
            os.replace(temporary, self._path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
