from __future__ import annotations

from typing import Any

from app.config.strategy_config import PutSpreadConfig
from app.indicators.technical_indicators import TechnicalIndicators
from app.models.market.price_snapshot import PriceSnapshot
from app.models.market.trend_analysis import TrendAnalysis


class MarketAnalysisBuilder:
    """Build domain market-analysis objects from Schwab daily candles."""

    def __init__(self, indicators: TechnicalIndicators | None = None) -> None:
        self._indicators = indicators or TechnicalIndicators()

    def build(
        self,
        symbol: str,
        price_history: dict[str, Any],
        config: PutSpreadConfig,
    ) -> tuple[PriceSnapshot, TrendAnalysis]:
        candles = price_history.get("candles")
        if not isinstance(candles, list):
            raise ValueError("Price-history payload must contain a candles list.")

        closes = self._indicators.closes(candles)
        snapshot = PriceSnapshot(
            symbol=symbol.strip().upper(),
            current_price=closes[-1],
            sma20=self._indicators.simple_moving_average(closes, 20),
            sma200=self._indicators.simple_moving_average(closes, 200),
            rsi=self._indicators.rsi(closes, 14),
            atr=self._indicators.atr(candles, 14),
        )
        return snapshot, self._build_trend_analysis(snapshot, config)

    @staticmethod
    def _build_trend_analysis(
        snapshot: PriceSnapshot,
        config: PutSpreadConfig,
    ) -> TrendAnalysis:
        checks: list[tuple[bool, str]] = []

        if config.require_20_sma_above_200_sma:
            checks.append((
                snapshot.is_20_above_200(),
                "20-day SMA is above the 200-day SMA.",
            ))
        if config.require_price_above_200_sma:
            checks.append((
                snapshot.is_above_200_sma(),
                "Price is above the 200-day SMA.",
            ))
        if config.require_price_below_20_sma:
            checks.append((
                snapshot.is_pullback_to_20(),
                "Price is below the 20-day SMA.",
            ))

        passed = all(result for result, _ in checks)
        reasons = [message for result, message in checks if result]
        if not checks:
            score = 100
        else:
            score = round(
                100 * sum(result for result, _ in checks) / len(checks)
            )
        return TrendAnalysis(passed=passed, score=score, reasons=reasons)
