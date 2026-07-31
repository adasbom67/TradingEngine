from app.config.strategy_config import PutSpreadConfig
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluators.trend_evaluator import TrendEvaluator
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from tests.helpers import create_option, create_price_snapshot


def test_uses_configurable_trend_weights():
    config = PutSpreadConfig(
        trend_weight_sma_alignment=10,
        trend_weight_price_above_200=20,
        trend_weight_price_above_20=30,
        trend_weight_trend_confirmation=40,
    )
    context = EvaluationContext(
        candidate=TradeCandidate(
            spread=BullPutSpread(
                short_put=create_option(500),
                long_put=create_option(495),
            )
        ),
        price_snapshot=create_price_snapshot(),
        trend_analysis=TrendAnalysis(passed=True, score=100),
        strategy_config=config,
    )

    result = TrendEvaluator().evaluate(context)

    assert result.score == 100


def test_excludes_failed_conditions_from_score():
    config = PutSpreadConfig(
        trend_weight_sma_alignment=10,
        trend_weight_price_above_200=20,
        trend_weight_price_above_20=30,
        trend_weight_trend_confirmation=40,
    )
    snapshot = create_price_snapshot()
    snapshot.current_price = 590.0
    context = EvaluationContext(
        candidate=TradeCandidate(
            spread=BullPutSpread(
                short_put=create_option(500),
                long_put=create_option(495),
            )
        ),
        price_snapshot=snapshot,
        trend_analysis=TrendAnalysis(passed=False, score=0),
        strategy_config=config,
    )

    result = TrendEvaluator().evaluate(context)

    assert result.score == 30
    assert "Trend analysis failed." in result.warnings
