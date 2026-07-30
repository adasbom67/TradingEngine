from typing import Any

from app.config.strategy_config import PutSpreadConfig
from app.models.market.price_snapshot import PriceSnapshot
from app.models.market.trend_analysis import TrendAnalysis
from app.strategies.base_strategy import BaseStrategy


class BullPutSpreadStrategy(BaseStrategy):
    """
    Strategy for identifying bullish put credit spread opportunities.
    """

    def __init__(self, config: PutSpreadConfig) -> None:
        super().__init__(
            name="Bull Put Spread",
            description="Bullish put credit spread strategy.",
        )
        self.config = config

    def validate(self) -> None:
        """Validate the strategy configuration."""
        self.config.validate()

    def analyze(self, snapshot: PriceSnapshot) -> TrendAnalysis:
        """
        Evaluate whether the underlying meets the trend requirements
        for a bull put spread.
        """

        reasons: list[str] = []
        score = 0
        passed = True

        if self.config.require_20_sma_above_200_sma:
            if snapshot.is_20_above_200():
                reasons.append("20 SMA above 200 SMA")
                score += 40
            else:
                reasons.append("20 SMA below 200 SMA")
                passed = False

        if self.config.require_price_above_200_sma:
            if snapshot.is_above_200_sma():
                reasons.append("Price above 200 SMA")
                score += 40
            else:
                reasons.append("Price below 200 SMA")
                passed = False

        if self.config.require_price_below_20_sma:
            if snapshot.is_pullback_to_20():
                reasons.append("Pullback to 20 SMA")
                score += 20
            else:
                reasons.append("Not on a pullback")
                passed = False

        return TrendAnalysis(
            passed=passed,
            score=score,
            reasons=reasons,
        )

    def generate_candidates(self, option_chain: Any) -> list[Any]:
        """
        Temporarily return an empty candidate list.

        Candidate-selection logic will be implemented later.
        """
        return []
