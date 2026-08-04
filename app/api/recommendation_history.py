from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HISTORY_PATH = Path("data/recommendation_scan_history.json")
DEFAULT_HISTORY_LIMIT = 100


class RecommendationHistoryStore:
    def __init__(
        self,
        path: Path = HISTORY_PATH,
        maximum_entries: int = DEFAULT_HISTORY_LIMIT,
    ) -> None:
        self._path = path
        self._maximum_entries = maximum_entries

    def save(
        self,
        request_payload: dict[str, Any],
        result_payload: dict[str, Any],
    ) -> dict[str, Any]:
        scanned_at = result_payload.get("scanned_at") or datetime.now(
            timezone.utc
        ).isoformat()
        entry = {
            "id": uuid.uuid4().hex,
            "scanned_at": scanned_at,
            "symbols": result_payload.get("symbols", []),
            "constraints": request_payload.get("constraints", {}),
            "summary": result_payload.get("summary", {}),
            "candidates": result_payload.get("candidates", []),
            "rejected_candidates": result_payload.get(
                "rejected_candidates",
                [],
            ),
            "diagnostics": result_payload.get("diagnostics", []),
            "pricing_disclosure": result_payload.get(
                "pricing_disclosure",
                "",
            ),
        }
        entries = self._read()
        entries.insert(0, entry)
        self._write(entries[: self._maximum_entries])
        return entry

    def list_entries(self, limit: int = 25) -> list[dict[str, Any]]:
        return [
            {
                "id": entry["id"],
                "scanned_at": entry["scanned_at"],
                "symbols": entry.get("symbols", []),
                "summary": entry.get("summary", {}),
            }
            for entry in self._read()[:limit]
        ]

    def get(self, history_id: str) -> dict[str, Any] | None:
        return next(
            (
                entry
                for entry in self._read()
                if entry.get("id") == history_id
            ),
            None,
        )

    def clear(self) -> None:
        self._write([])

    def _read(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Could not read recommendation scan history: {exc}"
            ) from exc
        if not isinstance(payload, list):
            raise RuntimeError(
                "Recommendation scan history must contain a JSON list."
            )
        return payload

    def _write(self, entries: list[dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(
            prefix="recommendation_history_",
            suffix=".json",
            dir=str(self._path.parent),
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(entries, stream, indent=2, sort_keys=True)
                stream.write("\n")
            os.replace(temporary, self._path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
