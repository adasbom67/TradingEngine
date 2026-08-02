from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping

from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig, BacktestResult, BacktestTrade


@dataclass(frozen=True)
class RejectedPortfolioTrade:
    trade: BacktestTrade
    reason: str


@dataclass
class PortfolioBacktestResult:
    initial_capital: float
    trades: list[BacktestTrade] = field(default_factory=list)
    rejected: list[RejectedPortfolioTrade] = field(default_factory=list)
    symbol_results: dict[str, BacktestResult] = field(default_factory=dict)

    @property
    def total_pnl(self) -> float:
        return sum(trade.pnl for trade in self.trades)

    @property
    def ending_capital(self) -> float:
        return self.initial_capital + self.total_pnl

    @property
    def win_rate(self) -> float:
        return (
            sum(trade.pnl > 0 for trade in self.trades) / len(self.trades)
            if self.trades
            else 0.0
        )

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        if gross_loss:
            return gross_profit / gross_loss
        return float("inf") if gross_profit else 0.0

    @property
    def maximum_drawdown(self) -> float:
        equity = peak = self.initial_capital
        drawdown = 0.0
        for trade in sorted(self.trades, key=lambda item: (item.exit_date, item.entry_date)):
            equity += trade.pnl
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
        return drawdown

    @property
    def max_concurrent_positions(self) -> int:
        events: list[tuple[date, int]] = []
        for trade in self.trades:
            events.append((trade.entry_date, 1))
            events.append((trade.exit_date, -1))
        # Process exits before entries on the same date.
        events.sort(key=lambda event: (event[0], event[1]))
        current = maximum = 0
        for _, change in events:
            current += change
            maximum = max(maximum, current)
        return maximum

    def pnl_by_symbol(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for trade in self.trades:
            totals[trade.symbol] = totals.get(trade.symbol, 0.0) + trade.pnl
        return dict(sorted(totals.items()))


class PortfolioBacktester:
    """Combine symbol backtests while enforcing shared portfolio constraints."""

    def __init__(self, backtester: HistoricalBacktester | None = None) -> None:
        self._backtester = backtester or HistoricalBacktester()

    def run(
        self,
        price_histories: Mapping[str, dict[str, Any]],
        config: BacktestConfig | None = None,
        *,
        max_open_positions: int = 5,
        max_risk_per_trade: float | None = None,
    ) -> PortfolioBacktestResult:
        cfg = config or BacktestConfig()
        cfg.validate()
        if max_open_positions <= 0:
            raise ValueError("Maximum open positions must be positive.")
        risk_limit = max_risk_per_trade if max_risk_per_trade is not None else float("inf")
        if risk_limit <= 0:
            raise ValueError("Maximum risk per trade must be positive.")

        symbol_results: dict[str, BacktestResult] = {}
        candidates: list[BacktestTrade] = []
        for raw_symbol, history in price_histories.items():
            symbol = raw_symbol.strip().upper()
            if not symbol:
                raise ValueError("Portfolio symbols cannot be blank.")
            result = self._backtester.run(symbol, history, cfg)
            symbol_results[symbol] = result
            candidates.extend(result.trades)

        candidates.sort(key=lambda trade: (trade.entry_date, trade.symbol, trade.exit_date))
        accepted: list[BacktestTrade] = []
        rejected: list[RejectedPortfolioTrade] = []

        for trade in candidates:
            if trade.maximum_loss > risk_limit:
                rejected.append(RejectedPortfolioTrade(trade, "RISK_LIMIT"))
                continue
            concurrent = sum(
                existing.entry_date <= trade.entry_date < existing.exit_date
                for existing in accepted
            )
            if concurrent >= max_open_positions:
                rejected.append(RejectedPortfolioTrade(trade, "POSITION_LIMIT"))
                continue
            accepted.append(trade)

        return PortfolioBacktestResult(
            initial_capital=cfg.initial_capital,
            trades=accepted,
            rejected=rejected,
            symbol_results=symbol_results,
        )
