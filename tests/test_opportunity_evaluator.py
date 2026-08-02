import pytest

from app.config.strategy_config import PutSpreadConfig
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluators.opportunity_evaluator import OpportunityEvaluator
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from tests.helpers import create_option, create_price_snapshot


def test_opportunity_evaluator_sets_probability_and_return_on_risk():
    candidate = TradeCandidate(BullPutSpread(
        short_put=create_option(500, bid=1.50, ask=1.60, delta=-0.20),
        long_put=create_option(495, bid=0.70, ask=0.80, delta=-0.10),
    ))
    context = EvaluationContext(
        candidate=candidate,
        price_snapshot=create_price_snapshot(),
        trend_analysis=TrendAnalysis(passed=True, score=100),
        strategy_config=PutSpreadConfig(),
    )

    result = OpportunityEvaluator().evaluate(context)

    assert candidate.probability_of_profit == pytest.approx(0.80)
    assert candidate.return_on_risk == pytest.approx(70 / 430)
    assert 0 <= result.score <= 100
    assert result.reasons


def test_probability_proxy_is_bounded():
    evaluator = OpportunityEvaluator()
    assert evaluator._probability_of_profit(None) == 0
    assert evaluator._probability_of_profit(-1.5) == 0
    assert evaluator._probability_of_profit(0.0) == 1
