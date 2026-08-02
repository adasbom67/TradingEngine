from dataclasses import dataclass
from enum import Enum


class MarketRegimeType(str, Enum):
    """High-level market environment used by bullish spread strategies."""

    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    HIGH_VOLATILITY = "high_volatility"


@dataclass(frozen=True)
class MarketRegime:
    """Classified market environment with an explanatory confidence score."""

    regime: MarketRegimeType
    confidence: float
    reasons: list[str]
