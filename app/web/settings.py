from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalSettings:
    schwab_live_account_hash: str = ""
    selected_account_last_four: str = ""


class LocalSettingsStore:
    """Atomic, Git-ignored machine-local operator settings."""

    def __init__(self, path: str | Path = "data/local_settings.json") -> None:
        self.path = Path(path)

    def load(self) -> LocalSettings:
        if not self.path.exists():
            return LocalSettings()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Local settings must contain a JSON object.")
        return LocalSettings(
            schwab_live_account_hash=str(payload.get("schwab_live_account_hash", "")),
            selected_account_last_four=str(payload.get("selected_account_last_four", "")),
        )

    def save_account(self, account_hash: str, last_four: str) -> LocalSettings:
        if not account_hash.strip():
            raise ValueError("Account hash cannot be blank.")
        value = LocalSettings(account_hash.strip(), last_four[-4:])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps({
            "schwab_live_account_hash": value.schwab_live_account_hash,
            "selected_account_last_four": value.selected_account_last_four,
        }, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
        return value
