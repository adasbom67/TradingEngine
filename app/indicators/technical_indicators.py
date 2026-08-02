from __future__ import annotations

from collections.abc import Sequence
from math import fsum
from typing import Any


class IndicatorDataError(ValueError):
    """Raised when candle data is missing or invalid."""


class TechnicalIndicators:
    """Deterministic technical-indicator calculations from daily candles."""

    @staticmethod
    def closes(candles: Sequence[dict[str, Any]]) -> list[float]:
        return TechnicalIndicators._series(candles, "close")

    @staticmethod
    def simple_moving_average(values: Sequence[float], period: int) -> float:
        TechnicalIndicators._validate_period(period)
        if len(values) < period:
            raise IndicatorDataError(
                f"At least {period} values are required; received {len(values)}."
            )
        window = [float(value) for value in values[-period:]]
        return fsum(window) / period

    @staticmethod
    def rsi(values: Sequence[float], period: int = 14) -> float:
        """Return Wilder RSI using all supplied closes after the seed window."""
        TechnicalIndicators._validate_period(period)
        if len(values) < period + 1:
            raise IndicatorDataError(
                f"At least {period + 1} closes are required for RSI."
            )

        closes = [float(value) for value in values]
        changes = [current - previous for previous, current in zip(closes, closes[1:])]
        gains = [max(change, 0.0) for change in changes]
        losses = [max(-change, 0.0) for change in changes]

        average_gain = fsum(gains[:period]) / period
        average_loss = fsum(losses[:period]) / period

        for gain, loss in zip(gains[period:], losses[period:]):
            average_gain = ((average_gain * (period - 1)) + gain) / period
            average_loss = ((average_loss * (period - 1)) + loss) / period

        if average_loss == 0:
            return 100.0 if average_gain > 0 else 50.0
        if average_gain == 0:
            return 0.0

        relative_strength = average_gain / average_loss
        return 100.0 - (100.0 / (1.0 + relative_strength))

    @staticmethod
    def atr(candles: Sequence[dict[str, Any]], period: int = 14) -> float:
        """Return Wilder ATR from high, low, and close candle fields."""
        TechnicalIndicators._validate_period(period)
        if len(candles) < period + 1:
            raise IndicatorDataError(
                f"At least {period + 1} candles are required for ATR."
            )

        highs = TechnicalIndicators._series(candles, "high")
        lows = TechnicalIndicators._series(candles, "low")
        closes = TechnicalIndicators._series(candles, "close")

        true_ranges: list[float] = []
        for index in range(1, len(candles)):
            true_ranges.append(
                max(
                    highs[index] - lows[index],
                    abs(highs[index] - closes[index - 1]),
                    abs(lows[index] - closes[index - 1]),
                )
            )

        average_true_range = fsum(true_ranges[:period]) / period
        for true_range in true_ranges[period:]:
            average_true_range = (
                (average_true_range * (period - 1)) + true_range
            ) / period
        return average_true_range

    @staticmethod
    def _series(candles: Sequence[dict[str, Any]], field: str) -> list[float]:
        if not candles:
            raise IndicatorDataError("At least one candle is required.")

        values: list[float] = []
        for index, candle in enumerate(candles):
            if not isinstance(candle, dict):
                raise IndicatorDataError(f"Candle {index} must be an object.")
            value = candle.get(field)
            try:
                values.append(float(value))
            except (TypeError, ValueError) as exc:
                raise IndicatorDataError(
                    f"Candle {index} has an invalid {field}: {value!r}."
                ) from exc
        return values

    @staticmethod
    def _validate_period(period: int) -> None:
        if period <= 0:
            raise ValueError("Indicator period must be greater than zero.")
