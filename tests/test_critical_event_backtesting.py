from datetime import datetime, timedelta, timezone

from app.backtesting.critical_events import (
    CriticalEventBacktestConfig,
    CriticalEventHistoricalBacktester,
)


def history(count=180):
    start = datetime(2025, 1, 2, tzinfo=timezone.utc)
    candles = []
    for index in range(count):
        close = 100 + index * 0.04 + (0.8 if index % 7 == 0 else 0)
        width = 0.25 if index % 12 < 5 else 0.8
        candles.append({
            "datetime": int((start + timedelta(days=index)).timestamp() * 1000),
            "open": close,
            "high": close + width,
            "low": close - width,
            "close": close,
            "volume": 3000 if index % 13 == 0 else 1000,
        })
    return {"candles": candles}


def test_critical_event_backtest_reports_forward_horizons_and_holdout():
    result = CriticalEventHistoricalBacktester().run(
        "spy", history(), CriticalEventBacktestConfig(minimum_signal_score=0)
    )

    assert result["symbol"] == "SPY"
    assert result["signal_count"] > 0
    assert set(result["horizons"]) == {"1", "3", "5", "10", "20"}
    assert result["configuration"]["historical_score_maximum"] == 6
    assert result["walk_forward"]["method"] == "CHRONOLOGICAL_70_30_HOLDOUT"
    assert result["walk_forward"]["testing"]["count"] > 0


def test_signal_generation_uses_only_supplied_history():
    normalized = CriticalEventHistoricalBacktester._normalize(history(100))
    before, metrics_before = CriticalEventHistoricalBacktester._signal(normalized[:80])
    changed_future = [dict(item, close=item["close"] * 3) for item in normalized[80:]]
    after, metrics_after = CriticalEventHistoricalBacktester._signal(
        (normalized[:80] + changed_future)[:80]
    )

    assert before == after
    assert metrics_before == metrics_after


def test_modeled_costs_make_entry_more_expensive_than_theoretical_value():
    result = CriticalEventHistoricalBacktester().run(
        "SPY", history(), CriticalEventBacktestConfig(minimum_signal_score=0)
    )
    signal = result["recent_signals"][0]
    theoretical = CriticalEventHistoricalBacktester._straddle_value(
        signal["price"], signal["strike"], 32, signal["modeled_entry_iv"]
    )

    assert signal["modeled_entry_debit"] > theoretical
    assert 0 <= result["horizons"]["20"]["modeled_win_rate"] <= 1
    sensitivity = result["horizons"]["20"]["execution_sensitivity"]
    assert set(sensitivity) == {
        "ZERO_SPREAD", "MODEST_2C_PER_LEG", "CONSERVATIVE_5C_PER_LEG"
    }
    assert sensitivity["ZERO_SPREAD"]["average_modeled_pnl"] > sensitivity["MODEST_2C_PER_LEG"]["average_modeled_pnl"]
    assert sensitivity["MODEST_2C_PER_LEG"]["average_modeled_pnl"] > sensitivity["CONSERVATIVE_5C_PER_LEG"]["average_modeled_pnl"]
