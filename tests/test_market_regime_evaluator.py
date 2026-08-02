from app.config.strategy_config import PutSpreadConfig
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluators.market_regime_evaluator import MarketRegimeEvaluator
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.trade_candidate import TradeCandidate
from app.models.trades.bull_put_spread import BullPutSpread
from tests.helpers import create_option, create_price_snapshot


def test_market_regime_evaluator_scores_bullish_environment():
    candidate = TradeCandidate(BullPutSpread(create_option(500), create_option(495)))
    result = MarketRegimeEvaluator().evaluate(EvaluationContext(
        candidate,
        create_price_snapshot(),
        TrendAnalysis(True, 100),
        PutSpreadConfig(),
    ))
    assert result.score == 100
    assert candidate.market_regime == "bullish"
