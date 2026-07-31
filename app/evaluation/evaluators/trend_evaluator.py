from app.evaluation.base_evaluator import BaseEvaluator
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluation_result import EvaluationResult


class TrendEvaluator(BaseEvaluator):
    """
    Scores the overall market trend for a bull put spread.
    """

    def evaluate(
        self,
        context: EvaluationContext,
    ) -> EvaluationResult:

        score = 0
        reasons: list[str] = []
        warnings: list[str] = []

        snapshot = context.price_snapshot
        trend = context.trend_analysis

        # 20 SMA above 200 SMA
        if snapshot.sma20 > snapshot.sma200:
            score += 40
            reasons.append("20-day SMA is above the 200-day SMA.")
        else:
            reasons.append("20-day SMA is below the 200-day SMA.")

        # Price above 200 SMA
        if snapshot.current_price > snapshot.sma200:
            score += 25
            reasons.append("Price is above the 200-day SMA.")
        else:
            reasons.append("Price is below the 200-day SMA.")

        # Price above 20 SMA
        if snapshot.current_price > snapshot.sma20:
            score += 20
            reasons.append("Price is above the 20-day SMA.")
        else:
            reasons.append("Price is below the 20-day SMA.")

        # Existing trend analysis
        if trend.passed:
            score += 15
            reasons.append("Trend analysis passed.")
        else:
            warnings.append("Trend analysis failed.")

        return EvaluationResult(
            score=score,
            reasons=reasons,
            warnings=warnings,
        )