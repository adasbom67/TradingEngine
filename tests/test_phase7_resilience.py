import json
from pathlib import Path

import pytest

from app.config.runtime_config import RuntimeConfig
from app.operations.diagnostics import DiagnosticCollector
from app.operations.lifecycle import InstanceAlreadyRunningError, InstanceLock, RecoveryCheckpoint
from app.operations.retry import RetryPolicy, retry_call


def test_retry_call_retries_then_succeeds():
    attempts = []
    def operation():
        attempts.append(1)
        if len(attempts) < 3:
            raise OSError("temporary")
        return "ok"
    result = retry_call(operation, RetryPolicy(attempts=3, initial_delay_seconds=0), sleep=lambda _: None)
    assert result == "ok"
    assert len(attempts) == 3


def test_retry_call_raises_after_limit():
    with pytest.raises(OSError):
        retry_call(lambda: (_ for _ in ()).throw(OSError("down")), RetryPolicy(attempts=2, initial_delay_seconds=0), sleep=lambda _: None)


def test_instance_lock_prevents_duplicate(tmp_path):
    path = tmp_path / "engine.lock"
    first = InstanceLock(path).acquire()
    try:
        with pytest.raises(InstanceAlreadyRunningError):
            InstanceLock(path).acquire()
    finally:
        first.release()
    assert not path.exists()


def test_recovery_checkpoint_is_atomic_and_clearable(tmp_path):
    checkpoint = RecoveryCheckpoint(tmp_path / "recovery.json")
    checkpoint.save("paper_daily", "running", symbols=["SPY"])
    assert checkpoint.load()["details"]["symbols"] == ["SPY"]
    checkpoint.clear()
    assert checkpoint.load() is None


def test_diagnostic_collector_reports_version_and_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("VERSION").write_text("0.9.2\n")
    config = RuntimeConfig.from_mapping({"version": "0.9.2", "environment": "test"})
    report = DiagnosticCollector().collect(config)
    assert report.payload["application"]["installed_version"] == "0.9.2"
    assert report.payload["runtime"]["python"]


def test_runtime_config_accepts_resilience_and_rotation():
    config = RuntimeConfig.from_mapping({
        "environment": "paper",
        "version": "0.9.2",
        "logging": {"max_bytes": 1000, "backup_count": 2},
        "resilience": {"retry_attempts": 4},
    })
    assert config.logging.max_bytes == 1000
    assert config.resilience.retry_attempts == 4
