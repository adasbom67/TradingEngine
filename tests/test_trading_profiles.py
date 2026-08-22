from pathlib import Path

from app.api.recommendations import RecommendationConstraints
from app.api.trading_profiles import TradingProfile, TradingProfileStore


def test_profile_store_round_trip(tmp_path: Path):
    store = TradingProfileStore(tmp_path / "profiles.json")
    profile = TradingProfile(
        name="Conservative Income",
        symbols=["spy", "qqq"],
        constraints=RecommendationConstraints(minimum_credit_per_contract=75),
    )
    saved = store.save(profile)
    assert saved["symbols"] == ["SPY", "QQQ"]
    assert saved["strategies"] == ["BULL_PUT"]
    assert store.list_profiles()[0]["constraints"]["minimum_credit_per_contract"] == 75


def test_profile_preserves_both_strategy_directions(tmp_path: Path):
    store = TradingProfileStore(tmp_path / "profiles.json")
    saved = store.save(
        TradingProfile(
            name="Two Sided Credit",
            symbols=["SPY"],
            strategies=["BULL_PUT", "BEAR_CALL"],
        )
    )
    assert saved["strategies"] == ["BULL_PUT", "BEAR_CALL"]


def test_profile_save_updates_case_insensitively(tmp_path: Path):
    store = TradingProfileStore(tmp_path / "profiles.json")
    store.save(TradingProfile(name="Income", symbols=["SPY"]))
    store.save(TradingProfile(name="income", symbols=["QQQ"]))
    profiles = store.list_profiles()
    assert len(profiles) == 1
    assert profiles[0]["symbols"] == ["QQQ"]


def test_profile_delete(tmp_path: Path):
    store = TradingProfileStore(tmp_path / "profiles.json")
    store.save(TradingProfile(name="Income", symbols=["SPY"]))
    assert store.delete("Income") is True
    assert store.list_profiles() == []
