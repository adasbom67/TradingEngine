from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable

from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig, BacktestResult
from app.backtesting.optimizer import BacktestOptimizer, OptimizationParameters


@dataclass(frozen=True)
class WalkForwardFold:
    training_start: date
    training_end: date
    testing_start: date
    testing_end: date
    parameters: OptimizationParameters
    training_result: BacktestResult
    testing_result: BacktestResult


@dataclass(frozen=True)
class WalkForwardResult:
    symbol: str
    folds: tuple[WalkForwardFold, ...]

    @property
    def total_test_pnl(self) -> float:
        return sum(fold.testing_result.total_pnl for fold in self.folds)

    @property
    def test_trade_count(self) -> int:
        return sum(len(fold.testing_result.trades) for fold in self.folds)

    @property
    def test_win_rate(self) -> float:
        trades = [trade for fold in self.folds for trade in fold.testing_result.trades]
        return sum(trade.pnl > 0 for trade in trades) / len(trades) if trades else 0.0

    @property
    def profitable_folds(self) -> int:
        return sum(fold.testing_result.total_pnl > 0 for fold in self.folds)


class WalkForwardTester:
    """Optimize on rolling training windows and validate on unseen test windows."""

    def __init__(
        self,
        optimizer: BacktestOptimizer | None = None,
        backtester: HistoricalBacktester | None = None,
    ) -> None:
        self._backtester = backtester or HistoricalBacktester()
        self._optimizer = optimizer or BacktestOptimizer(self._backtester)

    def run(
        self,
        symbol: str,
        price_history: dict[str, Any],
        base_config: BacktestConfig | None = None,
        *,
        training_bars: int = 504,
        testing_bars: int = 126,
        step_bars: int | None = None,
        exit_dtes: Iterable[int] = (7, 14, 21),
        profit_targets: Iterable[float] = (40.0, 50.0, 60.0),
        stop_losses: Iterable[float] = (150.0, 200.0),
        trend_exits: Iterable[bool] = (False,),
        strike_threat_exits: Iterable[bool] = (False,),
    ) -> WalkForwardResult:
        base = base_config or BacktestConfig()
        base.validate()
        if training_bars < base.lookback_days + base.entry_dte:
            raise ValueError("Training window is too short for the backtest configuration.")
        if testing_bars <= 0:
            raise ValueError("Testing window must be positive.")
        step = step_bars or testing_bars
        if step <= 0:
            raise ValueError("Step size must be positive.")

        candles = self._sorted_candles(price_history)
        minimum = training_bars + testing_bars
        if len(candles) < minimum:
            raise ValueError("Price history is too short for walk-forward testing.")

        folds: list[WalkForwardFold] = []
        train_start = 0
        while train_start + minimum <= len(candles):
            train_end = train_start + training_bars
            test_end = train_end + testing_bars
            training = {"candles": candles[train_start:train_end]}
            optimization = self._optimizer.run(
                symbol,
                training,
                base,
                exit_dtes=exit_dtes,
                profit_targets=profit_targets,
                stop_losses=stop_losses,
                trend_exits=trend_exits,
                strike_threat_exits=strike_threat_exits,
            )
            best = optimization.best
            if best is None:
                break
            parameters = best.parameters
            selected = BacktestConfig(
                **{
                    **base.__dict__,
                    "exit_dte": parameters.exit_dte,
                    "profit_target_percent": parameters.profit_target_percent,
                    "stop_loss_percent": parameters.stop_loss_percent,
                    "enable_trend_exit": parameters.enable_trend_exit,
                    "enable_strike_threat_exit": parameters.enable_strike_threat_exit,
                }
            )
            testing_start_date = self._to_date(candles[train_end]["datetime"])
            testing_end_date = self._to_date(candles[test_end - 1]["datetime"])
            # Include prior bars for indicators, but only allow entries in the test window.
            warmup_start = max(0, train_end - base.lookback_days)
            testing_payload = {"candles": candles[warmup_start:test_end]}
            testing_result = self._backtester.run(
                symbol,
                testing_payload,
                selected,
                start_date=testing_start_date,
                end_date=testing_end_date,
            )
            folds.append(
                WalkForwardFold(
                    training_start=self._to_date(candles[train_start]["datetime"]),
                    training_end=self._to_date(candles[train_end - 1]["datetime"]),
                    testing_start=testing_start_date,
                    testing_end=testing_end_date,
                    parameters=parameters,
                    training_result=best.result,
                    testing_result=testing_result,
                )
            )
            train_start += step
        return WalkForwardResult(symbol=symbol.strip().upper(), folds=tuple(folds))

    @staticmethod
    def _sorted_candles(payload: dict[str, Any]) -> list[dict[str, Any]]:
        candles = payload.get("candles") if isinstance(payload, dict) else None
        if not isinstance(candles, list) or not candles:
            raise ValueError("Price history must contain candles.")
        return sorted(candles, key=lambda item: item["datetime"])

    @staticmethod
    def _to_date(value: int | float) -> date:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date()
