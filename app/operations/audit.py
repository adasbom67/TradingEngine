from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditTrail:
    """Append-only JSONL audit trail for decisions and operational actions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def record(self, event: str, **details: Any) -> dict[str, Any]:
        if not event.strip():
            raise ValueError("Audit event cannot be blank.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **details,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry
