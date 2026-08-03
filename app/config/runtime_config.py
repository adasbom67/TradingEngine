from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class RuntimeConfigError(ValueError):
    """Raised when runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class LoggingSettings:
    level: str = "INFO"
    directory: str = "logs"
    filename: str = "tradingengine.jsonl"
    audit_filename: str = "audit.jsonl"
    max_bytes: int = 5_000_000
    backup_count: int = 5

    def validate(self) -> None:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in allowed:
            raise RuntimeConfigError(f"Unsupported logging level: {self.level}")
        if not self.directory.strip():
            raise RuntimeConfigError("Logging directory cannot be blank.")
        if not self.filename.strip() or not self.audit_filename.strip():
            raise RuntimeConfigError("Log filenames cannot be blank.")
        if self.max_bytes <= 0:
            raise RuntimeConfigError("max_bytes must be greater than zero.")
        if self.backup_count < 0:
            raise RuntimeConfigError("backup_count cannot be negative.")


@dataclass(frozen=True)
class PathSettings:
    data_directory: str = "data"
    reports_directory: str = "reports"
    watchlist_file: str = "config/watchlists.json"
    schedule_file: str = "config/schedule.json"
    scheduler_state_file: str = "data/scheduler_state.json"
    paper_ledger_file: str = "data/paper_account.json"

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if not str(value).strip():
                raise RuntimeConfigError(f"Path setting {name} cannot be blank.")


@dataclass(frozen=True)
class RiskSettings:
    maximum_open_positions: int = 5
    maximum_risk_per_trade: float = 500.0
    maximum_committed_risk_percent: float = 5.0
    daily_loss_limit_percent: float = 2.0

    def validate(self) -> None:
        if self.maximum_open_positions <= 0:
            raise RuntimeConfigError("maximum_open_positions must be greater than zero.")
        if self.maximum_risk_per_trade <= 0:
            raise RuntimeConfigError("maximum_risk_per_trade must be greater than zero.")
        for field_name in (
            "maximum_committed_risk_percent",
            "daily_loss_limit_percent",
        ):
            value = getattr(self, field_name)
            if not 0 < value <= 100:
                raise RuntimeConfigError(f"{field_name} must be between 0 and 100.")


@dataclass(frozen=True)
class ResilienceSettings:
    retry_attempts: int = 3
    retry_initial_delay_seconds: float = 0.5
    retry_backoff_multiplier: float = 2.0
    retry_maximum_delay_seconds: float = 5.0
    instance_lock_file: str = "data/tradingengine.lock"
    recovery_checkpoint_file: str = "data/recovery_checkpoint.json"

    def validate(self) -> None:
        if self.retry_attempts <= 0:
            raise RuntimeConfigError("retry_attempts must be greater than zero.")
        if self.retry_initial_delay_seconds < 0:
            raise RuntimeConfigError("retry_initial_delay_seconds cannot be negative.")
        if self.retry_backoff_multiplier < 1:
            raise RuntimeConfigError("retry_backoff_multiplier must be at least 1.")
        if self.retry_maximum_delay_seconds < 0:
            raise RuntimeConfigError("retry_maximum_delay_seconds cannot be negative.")
        if not self.instance_lock_file.strip() or not self.recovery_checkpoint_file.strip():
            raise RuntimeConfigError("Resilience file paths cannot be blank.")


@dataclass(frozen=True)
class TradingSettings:
    execution_mode: str = "dry_run"
    approved_symbols: tuple[str, ...] = ("SPY", "QQQ", "IWM", "DIA")
    live_submission_enabled: bool = False

    def validate(self) -> None:
        if self.execution_mode not in {"paper", "dry_run", "live"}:
            raise RuntimeConfigError("trading.execution_mode must be paper, dry_run, or live.")
        if self.execution_mode == "live" or self.live_submission_enabled:
            raise RuntimeConfigError("Live submission is unavailable in v0.10.2.")
        if not self.approved_symbols:
            raise RuntimeConfigError("trading.approved_symbols cannot be empty.")


@dataclass(frozen=True)
class PaperTradingSettings:
    initial_cash: float = 100_000.0
    ledger_file: str = "data/paper_account.json"
    capital_source: str = "fixed"

    def validate(self) -> None:
        if self.initial_cash <= 0:
            raise RuntimeConfigError("paper_trading.initial_cash must be greater than zero.")
        if not self.ledger_file.strip():
            raise RuntimeConfigError("paper_trading.ledger_file cannot be blank.")
        if self.capital_source not in {"fixed", "schwab_snapshot"}:
            raise RuntimeConfigError(
                "paper_trading.capital_source must be fixed or schwab_snapshot."
            )


@dataclass(frozen=True)
class RuntimeConfig:
    environment: str = "development"
    version: str = "0.10.2"
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    paths: PathSettings = field(default_factory=PathSettings)
    risk: RiskSettings = field(default_factory=RiskSettings)
    resilience: ResilienceSettings = field(default_factory=ResilienceSettings)
    trading: TradingSettings = field(default_factory=TradingSettings)
    paper_trading: PaperTradingSettings = field(default_factory=PaperTradingSettings)

    def validate(self) -> None:
        if self.environment not in {"development", "paper", "production", "test"}:
            raise RuntimeConfigError(
                "environment must be one of development, paper, production, or test."
            )
        if not self.version.strip():
            raise RuntimeConfigError("version cannot be blank.")
        self.logging.validate()
        self.paths.validate()
        self.risk.validate()
        self.resilience.validate()
        self.trading.validate()
        self.paper_trading.validate()

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "RuntimeConfig":
        config = cls(
            environment=str(payload.get("environment", "development")),
            version=str(payload.get("version", "0.10.2")),
            logging=LoggingSettings(**payload.get("logging", {})),
            paths=PathSettings(**payload.get("paths", {})),
            risk=RiskSettings(**payload.get("risk", {})),
            resilience=ResilienceSettings(**payload.get("resilience", {})),
            trading=TradingSettings(**{**payload.get("trading", {}), "approved_symbols": tuple(payload.get("trading", {}).get("approved_symbols", ("SPY", "QQQ", "IWM", "DIA")))}),
            paper_trading=PaperTradingSettings(**payload.get("paper_trading", {})),
        )
        config.validate()
        return config


class RuntimeConfigLoader:
    def __init__(self, path: str | Path = "config/runtime.json") -> None:
        self.path = Path(path)

    def load(self) -> RuntimeConfig:
        if not self.path.exists():
            raise RuntimeConfigError(f"Runtime configuration not found: {self.path}")
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeConfigError(
                f"Runtime configuration contains invalid JSON: {self.path}"
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeConfigError("Runtime configuration root must be an object.")
        return RuntimeConfig.from_mapping(payload)
