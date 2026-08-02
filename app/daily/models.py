from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.models.trades.trade_candidate import TradeCandidate


@dataclass(frozen=True)
class DailySymbolResult:
    symbol: str
    candidates: list[TradeCandidate] = field(default_factory=list)
    error: str | None = None

    @property
    def best(self) -> TradeCandidate | None:
        return self.candidates[0] if self.candidates else None


@dataclass(frozen=True)
class DailyRecommendationResult:
    generated_at: datetime
    strategy: str
    watchlist: str
    symbols: list[DailySymbolResult]
