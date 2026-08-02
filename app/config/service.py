from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from app.config.runtime_config import RuntimeConfig, RuntimeConfigLoader


@dataclass(frozen=True)
class ConfigSnapshot:
    path: Path
    config: RuntimeConfig


class ConfigService:
    """Thread-safe access to the validated runtime configuration."""

    def __init__(self, path: str | Path = "config/runtime.json") -> None:
        self.path = Path(path)
        self._lock = RLock()
        self._snapshot: ConfigSnapshot | None = None

    def load(self, *, force: bool = False) -> RuntimeConfig:
        with self._lock:
            if self._snapshot is None or force:
                config = RuntimeConfigLoader(self.path).load()
                self._snapshot = ConfigSnapshot(self.path, config)
            return self._snapshot.config

    def reload(self) -> RuntimeConfig:
        return self.load(force=True)

    def snapshot(self) -> ConfigSnapshot:
        return ConfigSnapshot(self.path, self.load())
