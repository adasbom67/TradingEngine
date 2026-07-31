import pytest

from app.evaluation.base_evaluator import BaseEvaluator
from app.evaluation.evaluation_result import EvaluationResult
from app.models.trades.trade_candidate import TradeCandidate
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.market.option_contract import OptionContract
from app.evaluation.evaluation_context import EvaluationContext


def create_option(strike: float) -> OptionContract:
    return OptionContract(
        symbol=f"SPY240920P{int(strike * 1000):08d}",
        expiration_date="2024-09-20",
        strike=strike,
        option_type="PUT",
        bid=1.50,
        ask=1.60,
        last=1.55,
        delta=-0.20,
        volume=100,
        open_interest=500,
        days_to_expiration=45,
    )


class DummyEvaluator(BaseEvaluator):
    def evaluate(self, context: EvaluationContext,) -> EvaluationResult:
        return EvaluationResult(
            score=10,
            reasons=["Dummy evaluator"],
            warnings=[],
        )


def test_dummy_evaluator_returns_result():
    spread = BullPutSpread(
        short_put=create_option(500),
        long_put=create_option(495),
    )

    candidate = TradeCandidate(spread=spread)

    evaluator = DummyEvaluator()

    result = evaluator.evaluate(candidate)

    assert result.score == 10
    assert result.reasons == ["Dummy evaluator"]
    assert result.warnings == []


def test_base_evaluator_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseEvaluator()