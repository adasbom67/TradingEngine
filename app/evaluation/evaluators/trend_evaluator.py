from app.evaluation.base_evaluator import BaseEvaluator
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluation_result import EvaluationResult


class TrendEvaluator(BaseEvaluator):
    """Score the underlying trend for a bullish put credit spread."""

    def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        score = 0.0
        reasons: list[str] = []
        warnings: list[str] = []

        snapshot = context.price_snapshot
        trend = context.trend_analysis
        config = context.strategy_config

        if snapshot.sma20 > snapshot.sma200:
            score += config.trend_weight_sma_alignment
            reasons.append("20-day SMA is above the 200-day SMA.")
        else:
            warnings.append("20-day SMA is not above the 200-day SMA.")

        if snapshot.current_price > snapshot.sma200:
            score += config.trend_weight_price_above_200
            reasons.append("Price is above the 200-day SMA.")
        else:
            warnings.append("Price is not above the 200-day SMA.")

        if snapshot.current_price > snapshot.sma20:
            score += config.trend_weight_price_above_20
            reasons.append("Price is above the 20-day SMA.")
        else:
            warnings.append("Price is not above the 20-day SMA.")

        if trend.passed:
            score += config.trend_weight_trend_confirmation
            reasons.append("Trend analysis passed.")
        else:
            warnings.append("Trend analysis failed.")

        return EvaluationResult(score=score, reasons=reasons, warnings=warnings)
