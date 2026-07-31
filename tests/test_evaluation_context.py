import pytest

from app.config.strategy_config import PutSpreadConfig
from app.evaluation.evaluation_context import EvaluationContext
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from tests.helpers import create_option, create_price_snapshot


def create_trade_candidate() -> TradeCandidate:
    spread = BullPutSpread(
        short_put=create_option(500),
        long_put=create_option(495),
    )

    return TradeCandidate(spread=spread)


def test_evaluation_context_stores_required_information():
    candidate = create_trade_candidate()
    price_snapshot = create_price_snapshot()

    trend_analysis = TrendAnalysis(
        passed=True,
        score=100,
        reasons=[
            "20-day SMA is above 200-day SMA.",
            "Price is above 200-day SMA.",
        ],
    )

    strategy_config = PutSpreadConfig()

    context = EvaluationContext(
        candidate=candidate,
        price_snapshot=price_snapshot,
        trend_analysis=trend_analysis,
        strategy_config=strategy_config,
    )

    assert context.candidate is candidate
    assert context.price_snapshot is price_snapshot
    assert context.trend_analysis is trend_analysis
    assert context.strategy_config is strategy_config


def test_evaluation_context_is_immutable():
    context = EvaluationContext(
        candidate=create_trade_candidate(),
        price_snapshot=create_price_snapshot(),
        trend_analysis=TrendAnalysis(
            passed=True,
            score=100,
            reasons=["Bullish trend"],
        ),
        strategy_config=PutSpreadConfig(),
    )

    with pytest.raises(AttributeError):
        context.price_snapshot = create_price_snapshot()