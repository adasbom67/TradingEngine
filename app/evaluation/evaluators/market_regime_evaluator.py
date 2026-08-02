from app.evaluation.base_evaluator import BaseEvaluator
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluation_result import EvaluationResult
from app.indicators.market_regime import MarketRegimeClassifier
from app.models.market.market_regime import MarketRegimeType


class MarketRegimeEvaluator(BaseEvaluator):
    """Score how suitable the current regime is for a bullish put spread."""

    def __init__(self, classifier: MarketRegimeClassifier | None = None) -> None:
        self._classifier = classifier or MarketRegimeClassifier()

    def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        regime = self._classifier.classify(
            context.price_snapshot,
            context.strategy_config,
        )
        context.candidate.market_regime = regime.regime.value

        score_by_regime = {
            MarketRegimeType.BULLISH: 100.0,
            MarketRegimeType.NEUTRAL: 65.0,
            MarketRegimeType.HIGH_VOLATILITY: 45.0,
            MarketRegimeType.BEARISH: 10.0,
        }
        score = score_by_regime[regime.regime]
        reasons = [
            f"Market regime is {regime.regime.value.replace('_', ' ')}.",
            *regime.reasons,
        ]
        warnings: list[str] = []
        if regime.regime == MarketRegimeType.BEARISH:
            warnings.append("Bearish regime is unfavorable for a bullish put spread.")
        elif regime.regime == MarketRegimeType.HIGH_VOLATILITY:
            warnings.append("High volatility increases gap and assignment risk.")

        return EvaluationResult(score=score, reasons=reasons, warnings=warnings)
