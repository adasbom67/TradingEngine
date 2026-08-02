import json
import logging

from app.config.runtime_config import LoggingSettings, PathSettings, RuntimeConfig
from app.operations.audit import AuditTrail
from app.operations.health import HealthChecker, HealthStatus
from app.operations.logging_config import configure_logging


def test_audit_trail_appends_json_lines(tmp_path):
    trail = AuditTrail(tmp_path / "audit.jsonl")
    entry = trail.record("decision", symbol="SPY", decision="WATCH")
    saved = json.loads((tmp_path / "audit.jsonl").read_text().strip())
    assert saved["event"] == "decision"
    assert saved["symbol"] == "SPY"
    assert entry["decision"] == "WATCH"


def test_structured_logging_writes_json(tmp_path):
    path = configure_logging(
        LoggingSettings(directory=str(tmp_path), filename="app.jsonl")
    )
    logging.getLogger("test").info("hello", extra={"event": "unit_test"})
    payload = json.loads(path.read_text().strip())
    assert payload["message"] == "hello"
    assert payload["event"] == "unit_test"


def test_health_checker_reports_missing_environment(monkeypatch, tmp_path):
    for name in ("SCHWAB_APP_KEY", "SCHWAB_APP_SECRET", "SCHWAB_CALLBACK_URL"):
        monkeypatch.delenv(name, raising=False)
    watch = tmp_path / "watch.json"
    schedule = tmp_path / "schedule.json"
    watch.write_text("{}")
    schedule.write_text("{}")
    config = RuntimeConfig(
        paths=PathSettings(
            data_directory=str(tmp_path / "data"),
            reports_directory=str(tmp_path / "reports"),
            watchlist_file=str(watch),
            schedule_file=str(schedule),
            scheduler_state_file=str(tmp_path / "state.json"),
            paper_ledger_file=str(tmp_path / "paper.json"),
        ),
        logging=LoggingSettings(directory=str(tmp_path / "logs")),
    )
    report = HealthChecker(config).run()
    env = next(item for item in report.checks if item.name == "schwab_environment")
    assert env.status is HealthStatus.FAIL
    assert report.exit_code == 1


def test_health_checker_passes_required_core_checks(monkeypatch, tmp_path):
    monkeypatch.setenv("SCHWAB_APP_KEY", "key")
    monkeypatch.setenv("SCHWAB_APP_SECRET", "secret")
    monkeypatch.setenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")
    watch = tmp_path / "watch.json"
    schedule = tmp_path / "schedule.json"
    watch.write_text("{}")
    schedule.write_text("{}")
    config = RuntimeConfig(
        paths=PathSettings(
            data_directory=str(tmp_path / "data"),
            reports_directory=str(tmp_path / "reports"),
            watchlist_file=str(watch),
            schedule_file=str(schedule),
            scheduler_state_file=str(tmp_path / "state.json"),
            paper_ledger_file=str(tmp_path / "paper.json"),
        ),
        logging=LoggingSettings(directory=str(tmp_path / "logs")),
    )
    report = HealthChecker(config).run()
    assert report.healthy
    assert any(item.status is HealthStatus.WARN for item in report.checks)
