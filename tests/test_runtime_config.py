import json

import pytest

from app.config.runtime_config import RuntimeConfigError, RuntimeConfigLoader


def test_runtime_config_loads_and_validates(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps({"environment": "paper", "version": "0.9.1"}))
    config = RuntimeConfigLoader(path).load()
    assert config.environment == "paper"
    assert config.version == "0.9.1"
    assert config.risk.maximum_open_positions == 5


def test_runtime_config_rejects_invalid_risk(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps({"risk": {"maximum_open_positions": 0}}))
    with pytest.raises(RuntimeConfigError, match="greater than zero"):
        RuntimeConfigLoader(path).load()


def test_runtime_config_requires_object_root(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text("[]")
    with pytest.raises(RuntimeConfigError, match="root must be an object"):
        RuntimeConfigLoader(path).load()
