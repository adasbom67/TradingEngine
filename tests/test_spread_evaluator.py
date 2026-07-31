import pytest

from app.config.strategy_config import PutSpreadConfig
from app.evaluation.base_evaluator import BaseEvaluator
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluation_result import EvaluationResult
from app.evaluation.spread_evaluator import SpreadEvaluator
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from tests.helpers import create_option, create_price_snapshot


class StubEvaluator(BaseEvaluator):
    def __init__(self, result: EvaluationResult) -> None:
        self._result = result

    def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        return self._result


def create_context(candidate: TradeCandidate | None = None) -> EvaluationContext:
    if candidate is None:
        candidate = TradeCandidate(
            spread=BullPutSpread(
                short_put=create_option(500),
                long_put=create_option(495),
            )
        )

    return EvaluationContext(
        candidate=candidate,
        price_snapshot=create_price_snapshot(),
        trend_analysis=TrendAnalysis(passed=True, score=100),
        strategy_config=PutSpreadConfig(),
    )


def test_requires_at_least_one_evaluator():
    with pytest.raises(ValueError, match="At least one evaluator"):
        SpreadEvaluator([])


def test_averages_evaluator_scores():
    evaluator = SpreadEvaluator(
        [
            StubEvaluator(EvaluationResult(score=80)),
            StubEvaluator(EvaluationResult(score=60)),
        ]
    )

    candidate = evaluator.evaluate(create_context())

    assert candidate.score == 70.0


def test_aggregates_reasons_and_warnings_in_evaluator_order():
    evaluator = SpreadEvaluator(
        [
            StubEvaluator(
                EvaluationResult(
                    score=80,
                    reasons=["Trend passed"],
                    warnings=["RSI elevated"],
                )
            ),
            StubEvaluator(
                EvaluationResult(
                    score=60,
                    reasons=["Credit acceptable"],
                    warnings=["Low volume"],
                )
            ),
        ]
    )

    candidate = evaluator.evaluate(create_context())

    assert candidate.reasons == ["Trend passed", "Credit acceptable"]
    assert candidate.warnings == ["RSI elevated", "Low volume"]


def test_replaces_stale_candidate_results():
    candidate = TradeCandidate(
        spread=BullPutSpread(
            short_put=create_option(500),
            long_put=create_option(495),
        ),
        score=99,
        reasons=["Old reason"],
        warnings=["Old warning"],
    )
    evaluator = SpreadEvaluator(
        [
            StubEvaluator(
                EvaluationResult(
                    score=75,
                    reasons=["Current reason"],
                    warnings=[],
                )
            )
        ]
    )

    result = evaluator.evaluate(create_context(candidate))

    assert result is candidate
    assert result.score == 75.0
    assert result.reasons == ["Current reason"]
    assert result.warnings == []
