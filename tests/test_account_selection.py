from __future__ import annotations

import pytest

from app.trading.account_selection import (
    AccountSelectionRequired,
    configured_account_hash,
    mask_sensitive,
    select_account,
)
from app.trading.models import BrokerAccount
from app.web.settings import LocalSettings, LocalSettingsStore


def _accounts():
    return [
        BrokerAccount("12341088", "AAAABBBBCCCCDDDDEEEEFFFF11112222"),
        BrokerAccount("87658659", "99998888777766665555444433332222"),
    ]


def _clear_local_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        LocalSettingsStore,
        "load",
        lambda self: LocalSettings(),
    )


def test_environment_account_hash_has_precedence(monkeypatch):
    _clear_local_settings(monkeypatch)
    monkeypatch.setenv("SCHWAB_LIVE_ACCOUNT_HASH", _accounts()[1].account_hash)
    value, source = configured_account_hash()
    assert value == _accounts()[1].account_hash
    assert source == "environment"


def test_unconfigured_when_environment_and_local_settings_are_empty(monkeypatch):
    _clear_local_settings(monkeypatch)
    monkeypatch.delenv("SCHWAB_LIVE_ACCOUNT_HASH", raising=False)
    value, source = configured_account_hash()
    assert value == ""
    assert source == "unconfigured"


def test_single_linked_account_is_selected_without_configuration(monkeypatch):
    _clear_local_settings(monkeypatch)
    monkeypatch.delenv("SCHWAB_LIVE_ACCOUNT_HASH", raising=False)
    selection = select_account([_accounts()[0]])
    assert selection.account.account_id.endswith("1088")
    assert selection.source == "single_linked_account"


def test_multiple_accounts_require_explicit_selection_and_mask_output(monkeypatch):
    _clear_local_settings(monkeypatch)
    monkeypatch.delenv("SCHWAB_LIVE_ACCOUNT_HASH", raising=False)
    accounts = _accounts()
    with pytest.raises(AccountSelectionRequired) as caught:
        select_account(accounts)
    message = caught.value.user_message()
    assert "Multiple Schwab accounts" in message
    assert "****1088" in message
    assert "****8659" in message
    assert accounts[0].account_hash not in message
    assert accounts[1].account_hash not in message
    assert "SCHWAB_LIVE_ACCOUNT_HASH" in message


def test_local_settings_account_hash_is_supported(monkeypatch):
    monkeypatch.delenv("SCHWAB_LIVE_ACCOUNT_HASH", raising=False)
    selected = _accounts()[0]
    monkeypatch.setattr(
        LocalSettingsStore,
        "load",
        lambda self: LocalSettings(
            schwab_live_account_hash=selected.account_hash,
            selected_account_last_four="1088",
        ),
    )
    value, source = configured_account_hash()
    assert value == selected.account_hash
    assert source == "local_settings"


def test_environment_overrides_local_settings(monkeypatch):
    local_account = _accounts()[0]
    environment_account = _accounts()[1]
    monkeypatch.setattr(
        LocalSettingsStore,
        "load",
        lambda self: LocalSettings(
            schwab_live_account_hash=local_account.account_hash,
            selected_account_last_four="1088",
        ),
    )
    monkeypatch.setenv("SCHWAB_LIVE_ACCOUNT_HASH", environment_account.account_hash)
    value, source = configured_account_hash()
    assert value == environment_account.account_hash
    assert source == "environment"


def test_unknown_configured_hash_is_not_echoed(monkeypatch):
    _clear_local_settings(monkeypatch)
    monkeypatch.setenv("SCHWAB_LIVE_ACCOUNT_HASH", "TOPSECRETACCOUNTIDENTIFIER")
    with pytest.raises(AccountSelectionRequired) as caught:
        select_account(_accounts())
    message = caught.value.user_message()
    assert "TOPSECRETACCOUNTIDENTIFIER" not in message


def test_mask_sensitive_displays_fingerprint_only():
    assert mask_sensitive("1234567890ABCDEF") == "1234...CDEF"


def test_tracked_runtime_config_does_not_define_live_account_hash():
    import json
    from pathlib import Path

    payload = json.loads(Path("config/runtime.json").read_text(encoding="utf-8"))
    assert "account_hash" not in payload.get("trading", {})
