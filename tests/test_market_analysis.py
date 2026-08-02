from app.config.strategy_config import PutSpreadConfig
from app.indicators.market_analysis import MarketAnalysisBuilder


def make_candles(count: int) -> list[dict[str, float]]:
    return [
        {
            "open": float(index),
            "high": float(index + 2),
            "low": float(index),
            "close": float(index + 1),
        }
        for index in range(1, count + 1)
    ]


def test_builds_snapshot_and_passing_trend_analysis():
    snapshot, trend = MarketAnalysisBuilder().build(
        "spy",
        {"candles": make_candles(220)},
        PutSpreadConfig(),
    )

    assert snapshot.symbol == "SPY"
    assert snapshot.current_price == 221.0
    assert snapshot.sma20 == 211.5
    assert snapshot.sma200 == 121.5
    assert snapshot.rsi == 100.0
    assert snapshot.atr == 2.0
    assert trend.passed is True
    assert trend.score == 100


def test_pullback_requirement_can_fail_trend_analysis():
    _, trend = MarketAnalysisBuilder().build(
        "SPY",
        {"candles": make_candles(220)},
        PutSpreadConfig(require_price_below_20_sma=True),
    )

    assert trend.passed is False
    assert trend.score == 67
