from __future__ import annotations

import json
import os
import signal
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import FrameType
from typing import Any, Callable


class InstanceAlreadyRunningError(RuntimeError):
    pass


class InstanceLock(AbstractContextManager["InstanceLock"]):
    """Simple process lock using an atomic lock-file create operation."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._acquired = False

    def acquire(self) -> "InstanceLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise InstanceAlreadyRunningError(
                f"Another TradingEngine process may be running: {self.path}"
            ) from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
        self._acquired = True
        return self

    def release(self) -> None:
        if self._acquired:
            try:
                self.path.unlink(missing_ok=True)
            finally:
                self._acquired = False

    def __enter__(self) -> "InstanceLock":
        return self.acquire()

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.release()


@dataclass
class ShutdownController:
    requested: bool = False
    reason: str | None = None

    def request(self, reason: str) -> None:
        self.requested = True
        self.reason = reason

    def install_signal_handlers(self) -> None:
        def handler(signum: int, frame: FrameType | None) -> None:
            try:
                name = signal.Signals(signum).name
            except ValueError:
                name = str(signum)
            self.request(f"signal:{name}")

        for signal_name in ("SIGINT", "SIGTERM"):
            value = getattr(signal, signal_name, None)
            if value is not None:
                signal.signal(value, handler)


class RecoveryCheckpoint:
    """Atomic JSON checkpoint used to resume interrupted operational workflows."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, operation: str, status: str, **details: Any) -> dict[str, Any]:
        if not operation.strip() or not status.strip():
            raise ValueError("operation and status cannot be blank.")
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "status": status,
            "details": details,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
        return payload

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Recovery checkpoint must contain a JSON object.")
        return payload

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)
