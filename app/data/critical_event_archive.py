from __future__ import annotations

import json
import os
import sqlite3
import zlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.models.market.option_contract import OptionContract


class CriticalEventArchive:
    """Bounded local archive for future option-quote replay and calibration."""

    def __init__(
        self,
        path: str | Path = "data/critical_event_archive.sqlite3",
        *,
        enabled: bool = True,
        interval_minutes: int = 15,
        retention_days: int = 730,
        maximum_mib: int = 1024,
    ) -> None:
        self.path = Path(path)
        self.enabled = enabled
        self.interval_minutes = max(interval_minutes, 1)
        self.retention_days = max(retention_days, 1)
        self.maximum_bytes = max(maximum_mib, 16) * 1024 * 1024
        if self.enabled:
            self._initialize()

    @classmethod
    def from_environment(cls) -> "CriticalEventArchive":
        return cls(
            path=os.getenv("CRITICAL_EVENT_ARCHIVE_PATH", "data/critical_event_archive.sqlite3"),
            enabled=os.getenv("CRITICAL_EVENT_ARCHIVE_ENABLED", "1") == "1",
            interval_minutes=int(os.getenv("CRITICAL_EVENT_ARCHIVE_INTERVAL_MINUTES", "15")),
            retention_days=int(os.getenv("CRITICAL_EVENT_ARCHIVE_RETENTION_DAYS", "730")),
            maximum_mib=int(os.getenv("CRITICAL_EVENT_ARCHIVE_MAX_MIB", "1024")),
        )

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=15000")
        return connection

    def _initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY,
                    captured_at TEXT NOT NULL,
                    bucket INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    underlying_price REAL NOT NULL,
                    daily_bar_count INTEGER NOT NULL,
                    intraday_bar_count INTEGER NOT NULL,
                    feature_blob BLOB NOT NULL,
                    estimated_bytes INTEGER NOT NULL,
                    UNIQUE(symbol, bucket)
                );
                CREATE TABLE IF NOT EXISTS contracts (
                    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
                    contract_symbol TEXT NOT NULL,
                    expiration TEXT NOT NULL,
                    strike REAL NOT NULL,
                    option_type TEXT NOT NULL,
                    bid REAL NOT NULL,
                    ask REAL NOT NULL,
                    last REAL NOT NULL,
                    implied_volatility REAL,
                    delta REAL,
                    volume INTEGER NOT NULL,
                    open_interest INTEGER NOT NULL,
                    quote_time TEXT,
                    PRIMARY KEY(snapshot_id, contract_symbol)
                );
                CREATE TABLE IF NOT EXISTS tracked_contracts (
                    symbol TEXT PRIMARY KEY,
                    expiration TEXT NOT NULL,
                    underlying_symbol TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_snapshots_time ON snapshots(captured_at);
                CREATE INDEX IF NOT EXISTS idx_contract_replay ON contracts(contract_symbol, snapshot_id);
            """)

    def capture(
        self,
        symbol: str,
        underlying_price: float,
        contracts: list[OptionContract],
        scored_candidates: list[dict[str, Any]],
        *,
        daily_bar_count: int,
        intraday_bar_count: int,
        captured_at: datetime | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {"stored": False, "reason": "DISABLED"}
        observed = captured_at or datetime.now(timezone.utc)
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        observed = observed.astimezone(timezone.utc)
        bucket = int(observed.timestamp() // (self.interval_minutes * 60))
        try:
            with self._connect() as connection:
                tracked = {
                    row[0] for row in connection.execute(
                        "SELECT symbol FROM tracked_contracts WHERE expiration >= ?",
                        (observed.date().isoformat(),),
                    )
                }
                selected_symbols = {
                    option_symbol
                    for candidate in scored_candidates
                    for option_symbol in (
                        candidate.get("option", {}).get("call_symbol"),
                        candidate.get("option", {}).get("put_symbol"),
                    )
                    if option_symbol
                }
                tracked.update(selected_symbols)
                # Persist only contracts the scanner actually evaluated and keep
                # following those symbols on later scans. The feature blob already
                # preserves every evaluated pair and its score. Avoiding the full
                # nearby surface cuts expected storage by an order of magnitude.
                retained = [item for item in contracts if item.symbol in tracked]
                feature_blob = zlib.compress(
                    json.dumps(scored_candidates, separators=(",", ":"), sort_keys=True).encode("utf-8"),
                    level=9,
                )
                estimated_bytes = len(feature_blob) + len(retained) * 176 + 512
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO snapshots(captured_at,bucket,symbol,underlying_price,daily_bar_count,intraday_bar_count,feature_blob,estimated_bytes) VALUES(?,?,?,?,?,?,?,?)",
                    (observed.isoformat(), bucket, symbol, underlying_price, daily_bar_count, intraday_bar_count, feature_blob, estimated_bytes),
                )
                if cursor.rowcount == 0:
                    return {"stored": False, "reason": "INTERVAL_DEDUPLICATED"}
                snapshot_id = cursor.lastrowid
                connection.executemany(
                    "INSERT INTO contracts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [
                        (snapshot_id, item.symbol, item.expiration_date.isoformat(), item.strike,
                         item.option_type, item.bid, item.ask, item.last, item.implied_volatility,
                         item.delta, item.volume, item.open_interest,
                         item.quote_time.isoformat() if item.quote_time else None)
                        for item in retained
                    ],
                )
                connection.executemany(
                    "INSERT OR REPLACE INTO tracked_contracts(symbol,expiration,underlying_symbol) VALUES(?,?,?)",
                    [
                        (item.symbol, item.expiration_date.isoformat(), symbol)
                        for item in contracts if item.symbol in selected_symbols
                    ],
                )
                self._prune(connection, observed)
                return {"stored": True, "contracts": len(retained), "estimated_bytes": estimated_bytes}
        except Exception as exc:
            return {"stored": False, "reason": "ARCHIVE_ERROR", "message": str(exc)}

    def _prune(self, connection, observed):
        cutoff = (observed - timedelta(days=self.retention_days)).isoformat()
        connection.execute("DELETE FROM snapshots WHERE captured_at < ?", (cutoff,))
        connection.execute("DELETE FROM tracked_contracts WHERE expiration < ?", (observed.date().isoformat(),))
        logical_bytes = connection.execute("SELECT COALESCE(SUM(estimated_bytes),0) FROM snapshots").fetchone()[0]
        target = int(self.maximum_bytes * 0.90)
        if logical_bytes > self.maximum_bytes:
            rows = connection.execute("SELECT id,estimated_bytes FROM snapshots ORDER BY captured_at").fetchall()
            removed = 0
            ids = []
            for snapshot_id, estimated in rows:
                ids.append((snapshot_id,))
                removed += estimated
                if logical_bytes - removed <= target:
                    break
            connection.executemany("DELETE FROM snapshots WHERE id=?", ids)

    def status(self) -> dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "path": str(self.path), "maximum_bytes": self.maximum_bytes}
        with self._connect() as connection:
            snapshot_count, logical_bytes, oldest, newest = connection.execute(
                "SELECT COUNT(*),COALESCE(SUM(estimated_bytes),0),MIN(captured_at),MAX(captured_at) FROM snapshots"
            ).fetchone()
            contract_count = connection.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
        physical_bytes = self.path.stat().st_size if self.path.exists() else 0
        average = logical_bytes / snapshot_count if snapshot_count else 0
        projected_annual = round(average * 4 * 26 * 252)
        return {
            "enabled": True,
            "path": str(self.path),
            "interval_minutes": self.interval_minutes,
            "retention_days": self.retention_days,
            "maximum_bytes": self.maximum_bytes,
            "physical_bytes": physical_bytes,
            "logical_estimated_bytes": logical_bytes,
            "snapshot_count": snapshot_count,
            "contract_count": contract_count,
            "oldest_snapshot": oldest,
            "newest_snapshot": newest,
            "projected_annual_bytes": projected_annual,
            "scope": "evaluated entry pairs plus continuing quotes for tracked contracts; one snapshot per symbol per 15-minute bucket",
        }
