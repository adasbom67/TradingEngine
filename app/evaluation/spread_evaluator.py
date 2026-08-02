from collections.abc import Iterable

from app.evaluation.base_evaluator import BaseEvaluator
from app.evaluation.evaluation_context import EvaluationContext
from app.models.trades.trade_candidate import TradeCandidate


class SpreadEvaluator:
    """Run evaluators and combine their results on a trade candidate."""

    def __init__(self, evaluators: Iterable[BaseEvaluator]) -> None:
        self._evaluators = tuple(evaluators)
        if not self._evaluators:
            raise ValueError("At least one evaluator is required.")

    def evaluate(self, context: EvaluationContext) -> TradeCandidate:
        total_score = 0.0
        reasons: list[str] = []
        warnings: list[str] = []
        breakdown: dict[str, float] = {}

        for evaluator in self._evaluators:
            result = evaluator.evaluate(context)
            name = evaluator.__class__.__name__.removesuffix("Evaluator")
            breakdown[name] = result.score
            total_score += result.score
            reasons.extend(result.reasons)
            warnings.extend(result.warnings)

        candidate = context.candidate
        candidate.score = total_score / len(self._evaluators)
        candidate.score_breakdown = breakdown
        candidate.reasons = reasons
        candidate.warnings = warnings
        return candidate
