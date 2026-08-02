from __future__ import annotations

from app.evaluation.base_evaluator import BaseEvaluator
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluation_result import EvaluationResult
from app.evaluation.probability_engine import ProbabilityEngine


class OpportunityEvaluator(BaseEvaluator):
    """Score spread economics, managed expected value, and liquidity."""

    def __init__(self, probability_engine: ProbabilityEngine | None = None) -> None:
        self._probability_engine = probability_engine or ProbabilityEngine()

    def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        spread = context.candidate.spread
        config = context.strategy_config
        metrics = self._probability_engine.evaluate(spread, config)

        return_on_risk = spread.return_on_risk
        liquidity = self._liquidity_score(context)
        credit_quality = min(
            spread.credit / max(config.minimum_credit, 0.01),
            2.0,
        ) / 2.0
        risk_efficiency = min(
            return_on_risk / max(config.target_return_on_risk, 0.01),
            1.0,
        )

        score = (
            metrics.probability_of_profit * config.opportunity_weight_probability
            + risk_efficiency * config.opportunity_weight_return_on_risk
            + liquidity * config.opportunity_weight_liquidity
            + credit_quality * config.opportunity_weight_credit
        )

        candidate = context.candidate
        candidate.probability_of_profit = metrics.probability_of_profit
        candidate.return_on_risk = return_on_risk
        candidate.expected_value = metrics.managed_expected_value
        candidate.unmanaged_expected_value = metrics.unmanaged_expected_value
        candidate.managed_expected_value = metrics.managed_expected_value
        candidate.profit_target_amount = metrics.profit_target_amount
        candidate.stop_loss_amount = metrics.stop_loss_amount

        reasons = [
            f"Estimated probability of profit is {metrics.probability_of_profit:.1%}.",
            f"Managed expected value is ${metrics.managed_expected_value:.2f} per spread.",
            f"Profit target amount is ${metrics.profit_target_amount:.2f}.",
            f"Stop-loss amount is ${metrics.stop_loss_amount:.2f}.",
            f"Return on risk is {return_on_risk:.1%}.",
            f"Estimated credit is ${spread.credit:.2f}.",
        ]
        warnings: list[str] = []

        if metrics.managed_expected_value < config.minimum_managed_expected_value:
            warnings.append("Managed expected value is negative.")
        if metrics.unmanaged_expected_value < 0:
            warnings.append("Expiration max-loss expected value is negative.")
        if return_on_risk < config.minimum_return_on_risk:
            warnings.append(
                f"Return on risk is below the {config.minimum_return_on_risk:.1%} preference."
            )
        if metrics.probability_of_profit < config.minimum_probability_of_profit:
            warnings.append(
                "Estimated probability of profit is below the configured preference."
            )
        if liquidity < 0.5:
            warnings.append("Liquidity quality is weak relative to configured thresholds.")

        return EvaluationResult(
            score=max(0.0, min(score, 100.0)),
            reasons=reasons,
            warnings=warnings,
        )

    @staticmethod
    def _probability_of_profit(delta: float | None) -> float:
        if delta is None:
            return 0.0
        return max(0.0, min(1.0, 1.0 - abs(delta)))

    @staticmethod
    def _liquidity_score(context: EvaluationContext) -> float:
        spread = context.candidate.spread
        config = context.strategy_config
        legs = (spread.short_put, spread.long_put)

        scores: list[float] = []
        for leg in legs:
            quote_width = max(leg.ask - leg.bid, 0.0)
            width_score = 1.0 - min(
                quote_width / max(config.maximum_bid_ask_spread, 0.01),
                1.0,
            )
            oi_score = min(
                leg.open_interest / max(config.minimum_open_interest, 1),
                2.0,
            ) / 2.0
            volume_score = min(
                leg.volume / max(config.minimum_volume, 1),
                2.0,
            ) / 2.0
            scores.append((width_score + oi_score + volume_score) / 3.0)

        return sum(scores) / len(scores)
