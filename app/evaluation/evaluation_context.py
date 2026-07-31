from dataclasses import dataclass

from app.config.strategy_config import PutSpreadConfig
from app.models.market.price_snapshot import PriceSnapshot
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.trade_candidate import TradeCandidate


@dataclass(frozen=True)
class EvaluationContext:
    """
    Contains all information needed to evaluate a trade candidate.

    Evaluators receive one EvaluationContext instead of requiring
    several separate method arguments.
    """

    candidate: TradeCandidate
    price_snapshot: PriceSnapshot
    trend_analysis: TrendAnalysis
    strategy_config: PutSpreadConfig