from __future__ import annotations

from app.config.strategy_config import PutSpreadConfig
from app.models.market.market_regime import MarketRegime, MarketRegimeType
from app.models.market.price_snapshot import PriceSnapshot


class MarketRegimeClassifier:
    """Classify trend and volatility into a simple, explainable regime."""

    def classify(
        self,
        snapshot: PriceSnapshot,
        config: PutSpreadConfig,
    ) -> MarketRegime:
        reasons: list[str] = []
        atr_percent = (
            snapshot.atr / snapshot.current_price
            if snapshot.atr is not None and snapshot.current_price > 0
            else 0.0
        )

        if atr_percent >= config.high_volatility_atr_percent:
            reasons.append(
                f"ATR is {atr_percent:.1%} of price, above the high-volatility threshold."
            )
            return MarketRegime(
                MarketRegimeType.HIGH_VOLATILITY,
                min(1.0, atr_percent / config.high_volatility_atr_percent),
                reasons,
            )

        bullish_checks = (
            snapshot.is_20_above_200(),
            snapshot.is_above_200_sma(),
            snapshot.is_above_20_sma(),
        )
        bullish_count = sum(bullish_checks)

        if bullish_count == 3:
            reasons.extend([
                "20-day SMA is above the 200-day SMA.",
                "Price is above both tracked moving averages.",
            ])
            return MarketRegime(
                MarketRegimeType.BULLISH,
                1.0,
                reasons,
            )

        if not snapshot.is_above_200_sma() and not snapshot.is_20_above_200():
            reasons.extend([
                "Price is below the 200-day SMA.",
                "20-day SMA is not above the 200-day SMA.",
            ])
            return MarketRegime(
                MarketRegimeType.BEARISH,
                1.0,
                reasons,
            )

        reasons.append("Trend signals are mixed.")
        return MarketRegime(
            MarketRegimeType.NEUTRAL,
            2.0 / 3.0 if bullish_count in (1, 2) else 0.5,
            reasons,
        )
