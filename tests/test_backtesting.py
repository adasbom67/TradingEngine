from datetime import datetime, timedelta, timezone

from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig, BacktestResult, BacktestTrade
from app.reports.backtest_report import BacktestReport


def payload(count=260, start=100.0, step=0.2):
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    candles=[]
    for i in range(count):
        close=start+i*step
        candles.append({"datetime": int((base+timedelta(days=i)).timestamp()*1000), "open": close-0.1, "high": close+1, "low": close-1, "close": close, "volume":1000})
    return {"candles":candles}


def test_backtester_generates_trades_without_lookahead():
    result=HistoricalBacktester().run("SPY", payload(280), BacktestConfig(entry_dte=35, exit_dte=7))
    assert result.trades
    assert all(t.exit_date > t.entry_date for t in result.trades)


def test_backtest_metrics():
    t1=BacktestTrade("SPY", datetime(2025,1,1).date(), datetime(2025,1,2).date(), 100,95,1,.5,50,"PROFIT_TARGET",1,110,111)
    t2=BacktestTrade("SPY", datetime(2025,1,3).date(), datetime(2025,1,4).date(), 100,95,1,2,-100,"STOP_LOSS",1,110,99)
    r=BacktestResult("SPY", [t1,t2], 1000)
    assert r.total_pnl == -50
    assert r.win_rate == .5
    assert r.maximum_drawdown == 100


def test_report_discloses_approximation():
    text=BacktestReport().format(BacktestResult("SPY"))
    assert "approximated" in text
    assert "not a reconstruction" in text


def test_config_validation():
    try:
        BacktestConfig(lookback_days=10).validate()
    except ValueError as exc:
        assert "200" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_pricing_model_varies_credit_with_market_inputs():
    from app.backtesting.pricing import ApproximateSpreadPricer

    pricer = ApproximateSpreadPricer()
    low_vol = pricer.value(500, 480, 475, 35, atr=3)
    high_vol = pricer.value(500, 480, 475, 35, atr=12)

    assert high_vol.debit > low_vol.debit
    assert 0 <= low_vol.debit <= 5
    assert 0 <= high_vol.debit <= 5


def test_stop_loss_execution_is_capped_at_stop_plus_slippage():
    class SequencePricer:
        def __init__(self):
            self.calls = 0

        def value(self, *args, **kwargs):
            from app.backtesting.pricing import SpreadValuation

            self.calls += 1
            if self.calls == 1:
                return SpreadValuation(1.0, 2.0, 1.0, 0.20)
            return SpreadValuation(4.0, 5.0, 1.0, 0.20)

    result = HistoricalBacktester(SequencePricer()).run(
        "SPY",
        payload(260),
        BacktestConfig(
            entry_dte=35,
            exit_dte=7,
            minimum_days_between_entries=1000,
            entry_slippage=0.0,
            exit_slippage=0.05,
        ),
    )

    trade = result.trades[0]
    assert trade.exit_reason == "STOP_LOSS"
    assert trade.exit_debit == 3.30
    assert trade.exit_debit <= trade.stop_debit + 0.25 + 0.05
    assert trade.exit_debit < 5.0


def test_trade_contains_calibration_diagnostics():
    result = HistoricalBacktester().run("SPY", payload(280))
    assert result.trades
    trade = result.trades[0]
    assert trade.entry_credit >= 0.20
    assert trade.entry_atr > 0
    assert trade.entry_volatility > 0
    assert trade.target_debit >= 0
    assert trade.stop_debit > trade.entry_credit
    assert trade.maximum_loss > 0


def test_result_groups_performance_by_regime_and_exit_reason():
    t1 = BacktestTrade(
        "SPY", datetime(2025, 1, 1).date(), datetime(2025, 1, 2).date(),
        100, 95, 1, .5, 50, "PROFIT_TARGET", 1, 110, 111,
        market_regime="BULLISH",
    )
    t2 = BacktestTrade(
        "SPY", datetime(2025, 1, 3).date(), datetime(2025, 1, 4).date(),
        100, 95, 1, 2, -100, "STOP_LOSS", 1, 110, 99,
        market_regime="NEUTRAL",
    )
    result = BacktestResult("SPY", [t1, t2], 1000)

    assert {group.name for group in result.by_regime()} == {"BULLISH", "NEUTRAL"}
    assert {group.name for group in result.by_exit_reason()} == {
        "PROFIT_TARGET", "STOP_LOSS"
    }


def test_trade_records_regime_and_excursion_diagnostics():
    result = HistoricalBacktester().run("SPY", payload(280))
    trade = result.trades[0]

    assert trade.market_regime in {
        "BULLISH", "NEUTRAL", "BEARISH", "HIGH_VOLATILITY"
    }
    assert trade.entry_sma20 > 0
    assert trade.entry_sma200 > 0
    assert 0 <= trade.entry_rsi <= 100
    assert trade.maximum_favorable_excursion >= 0
    assert trade.maximum_adverse_excursion <= 0


def test_report_includes_regime_and_exit_breakdowns():
    result = HistoricalBacktester().run("SPY", payload(280))
    text = BacktestReport().format(result)

    assert "Performance by market regime:" in text
    assert "Performance by exit reason:" in text
    assert "MFE" in text
    assert "MAE" in text


def test_same_bar_target_and_stop_uses_conservative_stop_first():
    class SequencePricer:
        def __init__(self):
            self.calls = 0

        def value(self, *args, **kwargs):
            from app.backtesting.pricing import SpreadValuation

            self.calls += 1
            if self.calls == 1:
                return SpreadValuation(1.0, 2.0, 1.0, 0.20)
            # high/low/close values on the first monitored bar:
            values = (0.20, 4.00, 1.00)
            value = values[(self.calls - 2) % 3]
            return SpreadValuation(value, value + 1, 1.0, 0.20)

    result = HistoricalBacktester(SequencePricer()).run(
        "SPY",
        payload(260),
        BacktestConfig(
            entry_dte=35,
            exit_dte=7,
            minimum_days_between_entries=1000,
            entry_slippage=0.0,
            exit_slippage=0.0,
        ),
    )

    assert result.trades[0].exit_reason == "STOP_LOSS"
    assert result.trades[0].exit_debit > result.trades[0].entry_credit


def test_optimizer_runs_requested_grid_and_ranks_results():
    from app.backtesting.optimizer import BacktestOptimizer

    optimization = BacktestOptimizer().run(
        "SPY",
        payload(280),
        BacktestConfig(minimum_days_between_entries=1000),
        exit_dtes=(7, 14),
        profit_targets=(40.0, 50.0),
        stop_losses=(150.0,),
        trend_exits=(False,),
        strike_threat_exits=(False,),
    )

    assert len(optimization.runs) == 4
    assert optimization.best is not None
    assert len(optimization.ranked) == 4


def test_optimization_report_contains_comparison_and_best_configuration():
    from app.backtesting.optimizer import BacktestOptimizer
    from app.reports.backtest_optimization_report import BacktestOptimizationReport

    optimization = BacktestOptimizer().run(
        "SPY",
        payload(280),
        BacktestConfig(minimum_days_between_entries=1000),
        exit_dtes=(7,),
        profit_targets=(50.0,),
        stop_losses=(200.0,),
        trend_exits=(False, True),
        strike_threat_exits=(False,),
    )
    text = BacktestOptimizationReport().format(optimization)

    assert "Backtest optimization: SPY" in text
    assert "Best configuration:" in text
    assert "Trend exit:" in text


def test_strike_threat_exit_can_close_before_planned_exit():
    result = HistoricalBacktester().run(
        "SPY",
        payload(280, start=100.0, step=0.2),
        BacktestConfig(
            minimum_days_between_entries=1000,
            enable_strike_threat_exit=True,
            strike_threat_buffer_atr=100.0,
        ),
    )

    assert result.trades[0].exit_reason == "STRIKE_THREAT"
    assert result.trades[0].exit_dte > 7


def test_config_rejects_negative_strike_threat_buffer():
    try:
        BacktestConfig(strike_threat_buffer_atr=-0.1).validate()
    except ValueError as exc:
        assert "buffer" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")
