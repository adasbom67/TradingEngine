from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, Iterable

from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig, BacktestResult


@dataclass(frozen=True)
class OptimizationParameters:
    exit_dte: int
    profit_target_percent: float
    stop_loss_percent: float
    enable_trend_exit: bool
    enable_strike_threat_exit: bool


@dataclass(frozen=True)
class OptimizationRun:
    parameters: OptimizationParameters
    result: BacktestResult

    @property
    def score(self) -> tuple[float, float, float]:
        """Rank by profit factor, then total P/L, then lower drawdown."""
        pf = self.result.profit_factor
        safe_pf = pf if pf != float("inf") else 1_000_000.0
        return (safe_pf, self.result.total_pnl, -self.result.maximum_drawdown)


@dataclass(frozen=True)
class OptimizationResult:
    symbol: str
    runs: tuple[OptimizationRun, ...]

    @property
    def ranked(self) -> tuple[OptimizationRun, ...]:
        return tuple(sorted(self.runs, key=lambda run: run.score, reverse=True))

    @property
    def best(self) -> OptimizationRun | None:
        ranked = self.ranked
        return ranked[0] if ranked else None


class BacktestOptimizer:
    """Run a deterministic parameter grid against the same price history."""

    def __init__(self, backtester: HistoricalBacktester | None = None) -> None:
        self._backtester = backtester or HistoricalBacktester()

    def run(
        self,
        symbol: str,
        price_history: dict[str, Any],
        base_config: BacktestConfig | None = None,
        *,
        exit_dtes: Iterable[int] = (7, 10, 14, 21),
        profit_targets: Iterable[float] = (40.0, 50.0, 60.0),
        stop_losses: Iterable[float] = (150.0, 175.0, 200.0),
        trend_exits: Iterable[bool] = (False, True),
        strike_threat_exits: Iterable[bool] = (False, True),
    ) -> OptimizationResult:
        base = base_config or BacktestConfig()
        runs: list[OptimizationRun] = []
        for exit_dte, target, stop, trend_exit, strike_exit in product(
            exit_dtes,
            profit_targets,
            stop_losses,
            trend_exits,
            strike_threat_exits,
        ):
            config = BacktestConfig(
                **{
                    **base.__dict__,
                    "exit_dte": int(exit_dte),
                    "profit_target_percent": float(target),
                    "stop_loss_percent": float(stop),
                    "enable_trend_exit": bool(trend_exit),
                    "enable_strike_threat_exit": bool(strike_exit),
                }
            )
            config.validate()
            result = self._backtester.run(symbol, price_history, config)
            runs.append(
                OptimizationRun(
                    parameters=OptimizationParameters(
                        exit_dte=config.exit_dte,
                        profit_target_percent=config.profit_target_percent,
                        stop_loss_percent=config.stop_loss_percent,
                        enable_trend_exit=config.enable_trend_exit,
                        enable_strike_threat_exit=config.enable_strike_threat_exit,
                    ),
                    result=result,
                )
            )
        return OptimizationResult(symbol=symbol.upper(), runs=tuple(runs))
