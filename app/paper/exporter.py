from __future__ import annotations

import csv
from pathlib import Path

from app.paper.models import PaperAccount


class PaperTradingExporter:
    """Export paper-trading activity to CSV files for external analysis."""

    def export(self, account: PaperAccount, directory: str | Path) -> list[Path]:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        paths = [
            self._positions(account, target / "paper_positions.csv"),
            self._observations(account, target / "paper_observations.csv"),
            self._snapshots(account, target / "paper_equity_curve.csv"),
        ]
        return paths

    @staticmethod
    def _positions(account: PaperAccount, path: Path) -> Path:
        fields = [
            "position_id", "symbol", "opened_on", "expiration", "short_strike",
            "long_strike", "entry_credit", "quantity", "current_debit",
            "closed_on", "exit_debit", "exit_reason", "last_marked_on",
            "maximum_risk", "realized_pnl", "unrealized_pnl",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for item in account.positions:
                row = item.to_dict()
                row.update(
                    maximum_risk=item.maximum_risk,
                    realized_pnl=item.realized_pnl,
                    unrealized_pnl=item.unrealized_pnl,
                )
                writer.writerow({key: row.get(key) for key in fields})
        return path

    @staticmethod
    def _observations(account: PaperAccount, path: Path) -> Path:
        fields = [
            "observed_on", "symbol", "decision", "reason", "candidate_count",
            "selected_short_strike", "selected_long_strike",
            "selected_expiration", "selected_credit", "selected_score", "position_id",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for item in account.observations:
                writer.writerow(item.to_dict())
        return path

    @staticmethod
    def _snapshots(account: PaperAccount, path: Path) -> Path:
        fields = [
            "snapshot_on", "equity", "realized_pnl", "unrealized_pnl",
            "committed_risk", "open_positions",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for item in account.snapshots:
                writer.writerow(item.to_dict())
        return path
