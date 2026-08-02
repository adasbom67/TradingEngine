from app.config.strategy_config import PutSpreadConfig
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluators.market_regime_evaluator import MarketRegimeEvaluator
from app.evaluation.evaluators.opportunity_evaluator import OpportunityEvaluator
from app.evaluation.evaluators.trend_evaluator import TrendEvaluator
from app.evaluation.spread_evaluator import SpreadEvaluator
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from tests.helpers import create_option, create_price_snapshot


def test_spread_evaluator_records_score_breakdown():
    candidate = TradeCandidate(BullPutSpread(
        create_option(500, bid=1.50, ask=1.60, delta=-0.20),
        create_option(495, bid=0.70, ask=0.80, delta=-0.10),
    ))
    evaluator = SpreadEvaluator([
        TrendEvaluator(), MarketRegimeEvaluator(), OpportunityEvaluator()
    ])
    result = evaluator.evaluate(EvaluationContext(
        candidate, create_price_snapshot(), TrendAnalysis(True, 100), PutSpreadConfig()
    ))
    assert set(result.score_breakdown) == {"Trend", "MarketRegime", "Opportunity"}
    assert 0 <= result.score <= 100
