from __future__ import annotations

import json
from pathlib import Path

from app.paper.models import PaperAccount


class PaperLedger:
    def __init__(self, path: str | Path = "data/paper_account.json") -> None:
        self.path = Path(path)

    def load(self) -> PaperAccount:
        if not self.path.exists():
            return PaperAccount()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Paper ledger must contain a JSON object.")
        return PaperAccount.from_dict(payload)

    def save(self, account: PaperAccount) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(account.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.path)
