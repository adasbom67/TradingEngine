from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_WATCHLISTS = {
    "core": ["SPY", "QQQ", "IWM", "DIA"],
    "sectors": ["XLF", "XLK", "XLE", "XLI", "SMH", "TLT"],
}


@dataclass(frozen=True)
class WatchlistStore:
    default: str
    watchlists: dict[str, list[str]]


class WatchlistManager:
    """Persist and manage named symbol watchlists in a small JSON file."""

    def __init__(self, path: str | Path = "config/watchlists.json") -> None:
        self.path = Path(path)

    def initialize(self, overwrite: bool = False) -> WatchlistStore:
        if self.path.exists() and not overwrite:
            return self.load()
        store = WatchlistStore(default="core", watchlists=dict(DEFAULT_WATCHLISTS))
        self.save(store)
        return store

    def load(self) -> WatchlistStore:
        if not self.path.exists():
            return self.initialize()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        default = str(data.get("default", "core")).strip().lower()
        raw = data.get("watchlists", {})
        if not isinstance(raw, dict) or not raw:
            raise ValueError("Watchlist file must contain at least one named watchlist.")
        watchlists = {
            str(name).strip().lower(): self._normalize(symbols)
            for name, symbols in raw.items()
        }
        if default not in watchlists:
            raise ValueError("Default watchlist does not exist.")
        return WatchlistStore(default=default, watchlists=watchlists)

    def save(self, store: WatchlistStore) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"default": store.default, "watchlists": store.watchlists}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def names(self) -> list[str]:
        return sorted(self.load().watchlists)

    def symbols(self, name: str | None = None) -> list[str]:
        store = self.load()
        key = (name or store.default).strip().lower()
        if key not in store.watchlists:
            raise KeyError(f"Unknown watchlist: {key}")
        return list(store.watchlists[key])

    def create(self, name: str, symbols: list[str], make_default: bool = False) -> WatchlistStore:
        store = self.load()
        key = self._name(name)
        if key in store.watchlists:
            raise ValueError(f"Watchlist already exists: {key}")
        updated = dict(store.watchlists)
        updated[key] = self._normalize(symbols)
        result = WatchlistStore(default=key if make_default else store.default, watchlists=updated)
        self.save(result)
        return result

    def add(self, name: str, symbols: list[str]) -> WatchlistStore:
        store = self.load()
        key = self._name(name)
        if key not in store.watchlists:
            raise KeyError(f"Unknown watchlist: {key}")
        updated = dict(store.watchlists)
        updated[key] = self._normalize(updated[key] + symbols)
        result = WatchlistStore(store.default, updated)
        self.save(result)
        return result

    def remove(self, name: str, symbols: list[str]) -> WatchlistStore:
        store = self.load()
        key = self._name(name)
        if key not in store.watchlists:
            raise KeyError(f"Unknown watchlist: {key}")
        remove = set(self._normalize(symbols))
        updated = dict(store.watchlists)
        updated[key] = [symbol for symbol in updated[key] if symbol not in remove]
        result = WatchlistStore(store.default, updated)
        self.save(result)
        return result

    def set_default(self, name: str) -> WatchlistStore:
        store = self.load()
        key = self._name(name)
        if key not in store.watchlists:
            raise KeyError(f"Unknown watchlist: {key}")
        result = WatchlistStore(key, dict(store.watchlists))
        self.save(result)
        return result

    @staticmethod
    def _name(name: str) -> str:
        key = name.strip().lower()
        if not key:
            raise ValueError("Watchlist name cannot be blank.")
        return key

    @staticmethod
    def _normalize(symbols: list[str]) -> list[str]:
        normalized: list[str] = []
        for symbol in symbols:
            value = str(symbol).strip().upper()
            if value and value not in normalized:
                normalized.append(value)
        if not normalized:
            raise ValueError("A watchlist must contain at least one symbol.")
        return normalized
