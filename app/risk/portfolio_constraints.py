from __future__ import annotations

from dataclasses import dataclass

from app.config.strategy_config import PutSpreadConfig
from app.models.portfolio.portfolio_state import PortfolioState
from app.models.trades.trade_candidate import TradeCandidate


@dataclass(frozen=True)
class PortfolioDecision:
    approved: bool
    maximum_quantity: int
    reasons: list[str]


class PortfolioConstraintService:
    """Apply account-level limits before a candidate is recommended."""

    def evaluate(
        self,
        candidate: TradeCandidate,
        portfolio: PortfolioState,
        config: PutSpreadConfig,
    ) -> PortfolioDecision:
        max_loss = candidate.spread.max_loss

        if portfolio.account_value <= 0:
            return PortfolioDecision(False, 0, ["Account value must be positive."])
        if portfolio.open_positions >= config.maximum_open_positions:
            return PortfolioDecision(False, 0, ["Maximum open positions reached."])
        if portfolio.daily_realized_loss >= config.maximum_daily_loss:
            return PortfolioDecision(False, 0, ["Maximum daily loss reached."])
        if max_loss <= 0:
            return PortfolioDecision(False, 0, ["Candidate maximum loss is invalid."])

        trade_risk_limit = min(
            config.maximum_risk_per_trade,
            portfolio.account_value * config.maximum_account_risk_percent,
        )
        remaining_total_risk = max(
            portfolio.account_value * config.maximum_total_risk_percent
            - portfolio.committed_risk,
            0.0,
        )
        risk_budget = min(
            trade_risk_limit,
            remaining_total_risk,
            portfolio.available_buying_power,
        )
        quantity = int(risk_budget // max_loss)

        if quantity < 1:
            return PortfolioDecision(
                False,
                0,
                ["Insufficient risk budget or buying power for one spread."],
            )

        return PortfolioDecision(
            True,
            quantity,
            [
                f"Maximum approved quantity is {quantity} spread(s).",
                f"Per-trade risk budget is ${trade_risk_limit:.2f}.",
            ],
        )
