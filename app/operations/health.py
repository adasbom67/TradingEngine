from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from app.config.runtime_config import RuntimeConfig


class HealthStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    status: HealthStatus
    message: str


@dataclass(frozen=True)
class HealthReport:
    checks: tuple[HealthCheckResult, ...]

    @property
    def healthy(self) -> bool:
        return all(check.status is not HealthStatus.FAIL for check in self.checks)

    @property
    def exit_code(self) -> int:
        return 0 if self.healthy else 1


class HealthChecker:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config

    def run(self) -> HealthReport:
        checks = [
            self._check_required_environment(),
            self._check_directory("data_directory", self.config.paths.data_directory),
            self._check_directory("reports_directory", self.config.paths.reports_directory),
            self._check_directory("logging_directory", self.config.logging.directory),
            self._check_json_file("watchlist_file", self.config.paths.watchlist_file),
            self._check_json_file("schedule_file", self.config.paths.schedule_file),
            self._check_optional_json_file(
                "paper_ledger_file", self.config.paths.paper_ledger_file
            ),
        ]
        return HealthReport(tuple(checks))

    @staticmethod
    def _check_required_environment() -> HealthCheckResult:
        names = ("SCHWAB_APP_KEY", "SCHWAB_APP_SECRET", "SCHWAB_CALLBACK_URL")
        missing = [name for name in names if not os.getenv(name)]
        if missing:
            return HealthCheckResult(
                "schwab_environment",
                HealthStatus.FAIL,
                "Missing: " + ", ".join(missing),
            )
        return HealthCheckResult(
            "schwab_environment", HealthStatus.PASS, "Required variables are present."
        )

    @staticmethod
    def _check_directory(name: str, value: str) -> HealthCheckResult:
        path = Path(value)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".healthcheck"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            return HealthCheckResult(name, HealthStatus.FAIL, str(exc))
        return HealthCheckResult(name, HealthStatus.PASS, f"Writable: {path}")

    @staticmethod
    def _read_json(path: Path) -> None:
        json.loads(path.read_text(encoding="utf-8"))

    def _check_json_file(self, name: str, value: str) -> HealthCheckResult:
        path = Path(value)
        if not path.exists():
            return HealthCheckResult(name, HealthStatus.FAIL, f"Missing: {path}")
        try:
            self._read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            return HealthCheckResult(name, HealthStatus.FAIL, str(exc))
        return HealthCheckResult(name, HealthStatus.PASS, f"Valid JSON: {path}")

    def _check_optional_json_file(self, name: str, value: str) -> HealthCheckResult:
        path = Path(value)
        if not path.exists():
            return HealthCheckResult(
                name,
                HealthStatus.WARN,
                f"Not initialized yet: {path}",
            )
        return self._check_json_file(name, value)
