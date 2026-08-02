from datetime import datetime, timedelta, timezone

from app.backtesting.models import BacktestConfig, BacktestResult, BacktestTrade
from app.backtesting.optimizer import OptimizationParameters, OptimizationResult, OptimizationRun
from app.backtesting.walk_forward import WalkForwardTester
from app.reports.walk_forward_report import WalkForwardReport


def history(count=500):
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return {
        "candles": [
            {
                "datetime": int((base + timedelta(days=i)).timestamp() * 1000),
                "open": 100+i*.1,
                "high": 101+i*.1,
                "low": 99+i*.1,
                "close": 100+i*.1,
                "volume": 1000,
            }
            for i in range(count)
        ]
    }


class FakeOptimizer:
    def run(self, symbol, payload, base, **kwargs):
        result = BacktestResult(symbol, [], base.initial_capital)
        params = OptimizationParameters(7, 50, 200, False, False)
        return OptimizationResult(symbol, (OptimizationRun(params, result),))


class FakeBacktester:
    def __init__(self):
        self.calls = []

    def run(self, symbol, payload, config, *, start_date=None, end_date=None):
        self.calls.append((start_date, end_date))
        trade = BacktestTrade(
            symbol, start_date, end_date, 100, 95, 1, .5, 50,
            "PROFIT_TARGET", 1, 110, 111,
        )
        return BacktestResult(symbol, [trade], config.initial_capital)


def test_walk_forward_uses_unseen_test_windows():
    backtester = FakeBacktester()
    result = WalkForwardTester(FakeOptimizer(), backtester).run(
        "SPY",
        history(500),
        BacktestConfig(lookback_days=200, entry_dte=35, exit_dte=7),
        training_bars=260,
        testing_bars=60,
        step_bars=60,
    )
    assert len(result.folds) == 4
    assert all(start is not None and end is not None for start, end in backtester.calls)
    assert result.test_trade_count == 4
    assert result.total_test_pnl == 200


def test_walk_forward_report_has_fold_results():
    result = WalkForwardTester(FakeOptimizer(), FakeBacktester()).run(
        "SPY", history(320), BacktestConfig(), training_bars=260, testing_bars=60
    )
    text = WalkForwardReport().format(result)
    assert "Walk-Forward Test: SPY" in text
    assert "Fold results:" in text
