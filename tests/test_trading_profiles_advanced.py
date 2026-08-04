from pathlib import Path
from app.api.trading_profiles import TradingProfile, TradingProfileStore

def test_profile_rename_duplicate_and_default(tmp_path: Path):
    store = TradingProfileStore(tmp_path / "profiles.json")
    store.save(TradingProfile(name="Income", symbols=["SPY"]))
    duplicate = store.duplicate("Income", "Income Copy")
    assert duplicate["name"] == "Income Copy"
    renamed = store.rename("Income Copy", "High Premium")
    assert renamed["name"] == "High Premium"
    default = store.set_default("High Premium")
    assert default["is_default"] is True
    assert sum(profile["is_default"] for profile in store.list_profiles()) == 1
