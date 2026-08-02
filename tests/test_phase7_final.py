import json

import pytest

from app.config.service import ConfigService
from app.operations.metrics import MetricsRecorder


def test_config_service_caches_and_reloads(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps({"environment": "test", "version": "1"}))
    service = ConfigService(path)
    assert service.load().version == "1"
    path.write_text(json.dumps({"environment": "test", "version": "2"}))
    assert service.load().version == "1"
    assert service.reload().version == "2"


def test_config_service_snapshot_exposes_path(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps({"environment": "test"}))
    snapshot = ConfigService(path).snapshot()
    assert snapshot.path == path
    assert snapshot.config.environment == "test"


def test_metrics_recorder_records_success(tmp_path):
    path = tmp_path / "metrics.jsonl"
    with MetricsRecorder(path).measure("unit"):
        pass
    payload = json.loads(path.read_text())
    assert payload["operation"] == "unit"
    assert payload["successful"] is True
    assert payload["duration_ms"] >= 0


def test_metrics_recorder_records_failure(tmp_path):
    path = tmp_path / "metrics.jsonl"
    with pytest.raises(RuntimeError):
        with MetricsRecorder(path).measure("failure"):
            raise RuntimeError("boom")
    payload = json.loads(path.read_text())
    assert payload["successful"] is False
    assert "boom" in payload["detail"]


def test_install_script_exists():
    from pathlib import Path
    assert Path("install.py").exists()


def test_upgrade_script_exists():
    from pathlib import Path
    assert Path("upgrade.py").exists()
