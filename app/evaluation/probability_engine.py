from __future__ import annotations

from dataclasses import dataclass

from app.config.strategy_config import PutSpreadConfig
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.bear_call_spread import BearCallSpread


@dataclass(frozen=True)
class ProbabilityMetrics:
    probability_of_profit: float
    probability_of_loss: float
    unmanaged_expected_value: float
    managed_expected_value: float
    profit_target_amount: float
    stop_loss_amount: float

    @property
    def expected_value(self) -> float:
        """Backward-compatible alias for the managed expected value."""
        return self.managed_expected_value


class ProbabilityEngine:
    """Transparent delta-based probability and managed-trade estimates."""

    def evaluate(
        self,
        spread: BullPutSpread | BearCallSpread,
        config: PutSpreadConfig | None = None,
    ) -> ProbabilityMetrics:
        strategy = config or PutSpreadConfig()
        short_delta = spread.short_leg.delta
        probability_of_loss = (
            max(0.0, min(1.0, abs(short_delta)))
            if short_delta is not None
            else 1.0
        )
        probability_of_profit = 1.0 - probability_of_loss

        unmanaged_expected_value = (
            probability_of_profit * spread.max_profit
            - probability_of_loss * spread.max_loss
        )

        profit_target_amount = min(
            spread.max_profit,
            spread.max_profit * strategy.profit_target_percent / 100.0,
        )
        stop_loss_amount = min(
            spread.max_loss,
            spread.max_profit * strategy.stop_loss_percent / 100.0,
        )
        managed_expected_value = (
            probability_of_profit * profit_target_amount
            - probability_of_loss * stop_loss_amount
        )

        return ProbabilityMetrics(
            probability_of_profit=probability_of_profit,
            probability_of_loss=probability_of_loss,
            unmanaged_expected_value=unmanaged_expected_value,
            managed_expected_value=managed_expected_value,
            profit_target_amount=profit_target_amount,
            stop_loss_amount=stop_loss_amount,
        )
