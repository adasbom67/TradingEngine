from __future__ import annotations

import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config.runtime_config import RuntimeConfig


@dataclass(frozen=True)
class DiagnosticReport:
    generated_at: str
    payload: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(self.payload, indent=2, sort_keys=True)


class DiagnosticCollector:
    def collect(self, config: RuntimeConfig, *, version_file: str | Path = "VERSION") -> DiagnosticReport:
        version_path = Path(version_file)
        installed_version = (
            version_path.read_text(encoding="utf-8").strip()
            if version_path.exists()
            else "unknown"
        )
        paths = {
            "data": self._path_status(Path(config.paths.data_directory)),
            "reports": self._path_status(Path(config.paths.reports_directory)),
            "logs": self._path_status(Path(config.logging.directory)),
            "paper_ledger": self._path_status(Path(config.paths.paper_ledger_file)),
            "scheduler_state": self._path_status(Path(config.paths.scheduler_state_file)),
        }
        payload: dict[str, Any] = {
            "application": {
                "configured_version": config.version,
                "installed_version": installed_version,
                "environment": config.environment,
            },
            "runtime": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "executable": sys.executable,
            },
            "paths": paths,
        }
        return DiagnosticReport(datetime.now(timezone.utc).isoformat(), payload)

    @staticmethod
    def _path_status(path: Path) -> dict[str, Any]:
        return {
            "path": str(path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        }

    def write(self, report: DiagnosticReport, directory: str | Path) -> Path:
        target_directory = Path(directory)
        target_directory.mkdir(parents=True, exist_ok=True)
        stamp = report.generated_at.replace(":", "").replace("-", "").replace("+", "_")
        path = target_directory / f"diagnostics_{stamp}.json"
        path.write_text(report.to_json() + "\n", encoding="utf-8")
        return path
