from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.runtime_config import RuntimeConfig, RuntimeConfigLoader
from app.operations.audit import AuditTrail
from app.operations.health import HealthChecker, HealthReport
from app.operations.logging_config import configure_logging


@dataclass(frozen=True)
class StartupResult:
    config: RuntimeConfig
    health: HealthReport
    log_path: Path
    audit_path: Path


class StartupValidator:
    """Load configuration, initialize operational paths, and run health checks."""

    def __init__(self, config_path: str | Path = "config/runtime.json") -> None:
        self.config_path = Path(config_path)

    def run(self) -> StartupResult:
        config = RuntimeConfigLoader(self.config_path).load()
        log_path = configure_logging(config.logging)
        audit_path = Path(config.logging.directory) / config.logging.audit_filename
        trail = AuditTrail(audit_path)
        health = HealthChecker(config).run()
        trail.record(
            "startup_health",
            healthy=health.healthy,
            checks=[
                {"name": item.name, "status": item.status.value, "message": item.message}
                for item in health.checks
            ],
        )
        return StartupResult(config, health, log_path, audit_path)
