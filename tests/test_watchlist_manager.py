import pytest

from app.watchlists.manager import WatchlistManager


def test_watchlist_manager_initializes_and_updates(tmp_path):
    manager = WatchlistManager(tmp_path / "watchlists.json")
    store = manager.initialize()
    assert store.default == "core"
    assert manager.symbols() == ["SPY", "QQQ", "IWM", "DIA"]
    manager.create("income", ["spy", "tlt"], make_default=True)
    manager.add("income", ["QQQ", "SPY"])
    assert manager.symbols() == ["SPY", "TLT", "QQQ"]
    manager.remove("income", ["tlt"])
    assert manager.symbols("income") == ["SPY", "QQQ"]


def test_watchlist_manager_rejects_unknown_name(tmp_path):
    manager = WatchlistManager(tmp_path / "watchlists.json")
    manager.initialize()
    with pytest.raises(KeyError, match="Unknown watchlist"):
        manager.symbols("missing")
