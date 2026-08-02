import pytest

from app.indicators.technical_indicators import (
    IndicatorDataError,
    TechnicalIndicators,
)


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


def test_simple_moving_average_uses_latest_window():
    values = [1, 2, 3, 4, 5]
    assert TechnicalIndicators.simple_moving_average(values, 3) == 4.0


def test_rsi_is_100_for_continuous_gains():
    assert TechnicalIndicators.rsi(list(range(1, 17)), 14) == 100.0


def test_rsi_is_50_for_flat_prices():
    assert TechnicalIndicators.rsi([10.0] * 16, 14) == 50.0


def test_atr_uses_wilder_true_range():
    candles = make_candles(16)
    assert TechnicalIndicators.atr(candles, 14) == 2.0


def test_indicator_rejects_insufficient_data():
    with pytest.raises(IndicatorDataError, match="200"):
        TechnicalIndicators.simple_moving_average([1.0] * 199, 200)
