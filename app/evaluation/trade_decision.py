from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.config.strategy_config import PutSpreadConfig
from app.models.trades.trade_candidate import TradeCandidate


class TradeDecision(StrEnum):
    TRADE = "TRADE"
    WATCH = "WATCH"
    PASS = "PASS"


@dataclass(frozen=True)
class DecisionResult:
    decision: TradeDecision
    reasons: tuple[str, ...]


class TradeDecisionEngine:
    """Convert candidate metrics into an explicit TRADE/WATCH/PASS result."""

    def evaluate(
        self,
        candidate: TradeCandidate,
        config: PutSpreadConfig,
    ) -> DecisionResult:
        failures: list[str] = []
        cautions: list[str] = []

        if candidate.managed_expected_value < config.minimum_managed_expected_value:
            failures.append(
                "Managed expected value is below the configured minimum."
            )
        if candidate.probability_of_profit < config.minimum_probability_of_profit:
            failures.append(
                "Probability of profit is below the configured minimum."
            )
        if candidate.return_on_risk < config.minimum_return_on_risk:
            failures.append("Return on risk is below the configured minimum.")
        if candidate.market_regime == "bearish":
            failures.append("Market regime is bearish.")
        if candidate.maximum_quantity == 0 and any(
            "Portfolio" in warning or "risk" in warning.lower()
            for warning in candidate.warnings
        ):
            failures.append("Portfolio constraints do not approve a position.")

        if candidate.market_regime == "neutral":
            cautions.append("Market regime is neutral.")
        if candidate.score < config.minimum_trade_score:
            cautions.append("Overall score is below the TRADE threshold.")
        if candidate.warnings:
            cautions.append("One or more evaluation warnings remain.")

        if failures:
            return DecisionResult(TradeDecision.PASS, tuple(failures + cautions))
        if cautions:
            return DecisionResult(TradeDecision.WATCH, tuple(cautions))
        return DecisionResult(
            TradeDecision.TRADE,
            ("All configured trade-quality requirements passed.",),
        )
