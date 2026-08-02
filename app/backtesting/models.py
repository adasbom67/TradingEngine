from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float = 100_000.0
    lookback_days: int = 200
    entry_dte: int = 35
    exit_dte: int = 7
    spread_width: float = 5.0
    short_strike_distance_atr: float = 1.5
    profit_target_percent: float = 50.0
    stop_loss_percent: float = 200.0
    minimum_days_between_entries: int = 5
    risk_free_rate: float = 0.04
    volatility_floor: float = 0.10
    volatility_ceiling: float = 0.80
    entry_slippage: float = 0.03
    exit_slippage: float = 0.03
    maximum_stop_gap_debit: float = 0.25
    minimum_entry_credit: float = 0.20
    maximum_entry_credit_percent_of_width: float = 0.35
    high_volatility_atr_percent: float = 0.025
    enable_trend_exit: bool = False
    enable_strike_threat_exit: bool = False
    strike_threat_buffer_atr: float = 0.25

    def validate(self) -> None:
        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive.")
        if self.lookback_days < 200:
            raise ValueError("Lookback must be at least 200 trading days.")
        if self.entry_dte <= self.exit_dte:
            raise ValueError("Entry DTE must exceed exit DTE.")
        if self.spread_width <= 0:
            raise ValueError("Spread width must be positive.")
        if self.short_strike_distance_atr <= 0:
            raise ValueError("Short-strike ATR distance must be positive.")
        if not 0 < self.profit_target_percent <= 100:
            raise ValueError("Profit target percent must be in (0, 100].")
        if self.stop_loss_percent <= 0:
            raise ValueError("Stop loss percent must be positive.")
        if self.minimum_days_between_entries < 0:
            raise ValueError("Minimum days between entries cannot be negative.")
        if not 0 <= self.risk_free_rate < 1:
            raise ValueError("Risk-free rate must be in [0, 1).")
        if not 0 < self.volatility_floor <= self.volatility_ceiling:
            raise ValueError("Volatility bounds are invalid.")
        if self.entry_slippage < 0 or self.exit_slippage < 0:
            raise ValueError("Slippage cannot be negative.")
        if self.maximum_stop_gap_debit < 0:
            raise ValueError("Maximum stop-gap debit cannot be negative.")
        if self.minimum_entry_credit < 0:
            raise ValueError("Minimum entry credit cannot be negative.")
        if not 0 < self.maximum_entry_credit_percent_of_width < 1:
            raise ValueError("Maximum entry-credit percentage must be between zero and one.")
        if self.high_volatility_atr_percent <= 0:
            raise ValueError("High-volatility ATR percentage must be positive.")
        if self.strike_threat_buffer_atr < 0:
            raise ValueError("Strike-threat ATR buffer cannot be negative.")


@dataclass(frozen=True)
class BacktestTrade:
    symbol: str
    entry_date: date
    exit_date: date
    short_strike: float
    long_strike: float
    entry_credit: float
    exit_debit: float
    pnl: float
    exit_reason: str
    days_held: int
    entry_price: float
    exit_price: float
    reasons: tuple[str, ...] = ()
    entry_dte: int = 0
    exit_dte: int = 0
    entry_atr: float = 0.0
    entry_volatility: float = 0.0
    target_debit: float = 0.0
    stop_debit: float = 0.0
    maximum_loss: float = 0.0
    theoretical_entry_value: float = 0.0
    exit_theoretical_value: float = 0.0
    entry_sma20: float = 0.0
    entry_sma200: float = 0.0
    entry_rsi: float = 0.0
    market_regime: str = "UNKNOWN"
    underlying_return_percent: float = 0.0
    maximum_favorable_excursion: float = 0.0
    maximum_adverse_excursion: float = 0.0


@dataclass(frozen=True)
class BacktestGroupMetrics:
    name: str
    trade_count: int
    win_rate: float
    total_pnl: float
    average_pnl: float
    profit_factor: float


@dataclass
class BacktestResult:
    symbol: str
    trades: list[BacktestTrade] = field(default_factory=list)
    initial_capital: float = 100_000.0

    @property
    def total_pnl(self) -> float:
        return sum(t.pnl for t in self.trades)

    @property
    def ending_capital(self) -> float:
        return self.initial_capital + self.total_pnl

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        return sum(t.pnl > 0 for t in self.trades) / len(self.trades)

    @property
    def average_pnl(self) -> float:
        return self.total_pnl / len(self.trades) if self.trades else 0.0

    @property
    def average_winner(self) -> float:
        winners = [t.pnl for t in self.trades if t.pnl > 0]
        return sum(winners) / len(winners) if winners else 0.0

    @property
    def average_loser(self) -> float:
        losers = [t.pnl for t in self.trades if t.pnl < 0]
        return sum(losers) / len(losers) if losers else 0.0

    @property
    def average_days_held(self) -> float:
        return (
            sum(t.days_held for t in self.trades) / len(self.trades)
            if self.trades
            else 0.0
        )

    @property
    def profit_factor(self) -> float:
        return self._profit_factor(self.trades)

    @property
    def maximum_drawdown(self) -> float:
        equity = self.initial_capital
        peak = equity
        max_dd = 0.0
        for trade in self.trades:
            equity += trade.pnl
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        return max_dd

    @property
    def longest_losing_streak(self) -> int:
        longest = current = 0
        for trade in self.trades:
            if trade.pnl < 0:
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        return longest

    def by_regime(self) -> list[BacktestGroupMetrics]:
        groups: dict[str, list[BacktestTrade]] = defaultdict(list)
        for trade in self.trades:
            groups[trade.market_regime].append(trade)
        return [self._group_metrics(name, groups[name]) for name in sorted(groups)]

    def by_exit_reason(self) -> list[BacktestGroupMetrics]:
        groups: dict[str, list[BacktestTrade]] = defaultdict(list)
        for trade in self.trades:
            groups[trade.exit_reason].append(trade)
        return [self._group_metrics(name, groups[name]) for name in sorted(groups)]

    @classmethod
    def _group_metrics(
        cls,
        name: str,
        trades: list[BacktestTrade],
    ) -> BacktestGroupMetrics:
        total = sum(t.pnl for t in trades)
        count = len(trades)
        return BacktestGroupMetrics(
            name=name,
            trade_count=count,
            win_rate=sum(t.pnl > 0 for t in trades) / count if count else 0.0,
            total_pnl=total,
            average_pnl=total / count if count else 0.0,
            profit_factor=cls._profit_factor(trades),
        )

    @staticmethod
    def _profit_factor(trades: list[BacktestTrade]) -> float:
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        return gross_profit / gross_loss if gross_loss else float("inf") if gross_profit else 0.0
