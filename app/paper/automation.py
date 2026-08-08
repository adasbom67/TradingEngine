from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from app.models.trades.trade_candidate import TradeCandidate
from app.config.strategy_config import PutSpreadConfig
from app.paper.models import PaperObservation, PaperPosition
from app.paper.service import PaperTradingService


@dataclass(frozen=True)
class PaperAutomationResult:
    symbol: str
    action: str
    decision: str
    reason: str
    position: PaperPosition | None = None
    observation: PaperObservation | None = None


class PaperTradeAutomation:
    """Apply live scanner decisions to a persistent paper account."""

    def __init__(
        self,
        service: PaperTradingService,
        config: PutSpreadConfig | None = None,
    ) -> None:
        self._service = service
        self._config = config or PutSpreadConfig()
        self._enforce_account_limits = config is not None

    def process(
        self,
        symbol: str,
        candidates: Sequence[TradeCandidate],
        *,
        quantity: int = 1,
        observed_on: date | None = None,
    ) -> PaperAutomationResult:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be blank.")
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        account = self._service.status()
        if account.has_open_symbol(normalized):
            reason = "An open paper position already exists for this symbol."
            observation = self._service.record_observation(
                normalized,
                "SKIP",
                reason,
                candidate_count=len(candidates),
                observed_on=observed_on,
            )
            return PaperAutomationResult(
                normalized, "NO_TRADE", "SKIP", reason, observation=observation
            )

        if not candidates:
            reason = "The live scanner returned no eligible candidates."
            observation = self._service.record_observation(
                normalized,
                "NO_CANDIDATE",
                reason,
                candidate_count=0,
                observed_on=observed_on,
            )
            return PaperAutomationResult(
                normalized,
                "NO_TRADE",
                "NO_CANDIDATE",
                reason,
                observation=observation,
            )

        ordered = sorted(candidates, key=lambda item: (item.rank or 10**9, -item.score))
        selected = ordered[0]
        decision = selected.decision.upper()
        reason = "; ".join(selected.decision_reasons) or f"Scanner decision: {decision}."
        spread = selected.spread

        if decision != "TRADE":
            observation = self._service.record_observation(
                normalized,
                decision,
                reason,
                candidate_count=len(candidates),
                observed_on=observed_on,
                selected_short_strike=spread.short_put.strike,
                selected_long_strike=spread.long_put.strike,
                selected_expiration=spread.short_put.expiration_date,
                selected_credit=spread.credit,
                selected_score=selected.score,
            )
            return PaperAutomationResult(
                normalized, "NO_TRADE", decision, reason, observation=observation
            )

        approved_quantity = quantity
        if selected.maximum_quantity > 0:
            approved_quantity = min(quantity, selected.maximum_quantity)

        if self._enforce_account_limits:
            if len(account.open_positions) >= self._config.maximum_open_positions:
                reason = "Maximum open-position limit reached."
                observation = self._service.record_observation(
                    normalized, "PASS", reason, candidate_count=len(candidates),
                    observed_on=observed_on, selected_short_strike=spread.short_put.strike,
                    selected_long_strike=spread.long_put.strike,
                    selected_expiration=spread.short_put.expiration_date,
                    selected_credit=spread.credit, selected_score=selected.score,
                )
                return PaperAutomationResult(
                    normalized, "NO_TRADE", "PASS", reason, observation=observation
                )

            per_contract_risk = spread.max_loss
            risk_cap = min(
                self._config.maximum_risk_per_trade,
                account.equity * self._config.maximum_account_risk_percent,
            )
            risk_quantity = int(risk_cap // per_contract_risk) if per_contract_risk > 0 else 0
            total_risk_room = max(
                account.equity * self._config.maximum_total_risk_percent
                - account.committed_risk,
                0.0,
            )
            total_risk_quantity = (
                int(total_risk_room // per_contract_risk) if per_contract_risk > 0 else 0
            )
            approved_quantity = min(approved_quantity, risk_quantity, total_risk_quantity)
        if selected.maximum_quantity == 0:
            reason = "Portfolio constraints approved zero contracts."
            observation = self._service.record_observation(
                normalized,
                "PASS",
                reason,
                candidate_count=len(candidates),
                observed_on=observed_on,
                selected_short_strike=spread.short_put.strike,
                selected_long_strike=spread.long_put.strike,
                selected_expiration=spread.short_put.expiration_date,
                selected_credit=spread.credit,
                selected_score=selected.score,
            )
            return PaperAutomationResult(
                normalized, "NO_TRADE", "PASS", reason, observation=observation
            )

        if approved_quantity <= 0:
            reason = "Paper-account risk limits approved zero contracts."
            observation = self._service.record_observation(
                normalized, "PASS", reason, candidate_count=len(candidates),
                observed_on=observed_on, selected_short_strike=spread.short_put.strike,
                selected_long_strike=spread.long_put.strike,
                selected_expiration=spread.short_put.expiration_date,
                selected_credit=spread.credit, selected_score=selected.score,
            )
            return PaperAutomationResult(
                normalized, "NO_TRADE", "PASS", reason, observation=observation
            )

        position = self._service.open_position(
            normalized,
            spread.short_put.expiration_date,
            spread.short_put.strike,
            spread.long_put.strike,
            spread.credit,
            quantity=approved_quantity,
            opened_on=observed_on,
            entry_decision=decision,
            entry_score=selected.score,
            entry_thesis=selected.decision_reasons,
            entry_reasons=selected.reasons,
            entry_warnings=selected.warnings,
            market_regime=selected.market_regime,
        )
        observation = self._service.record_observation(
            normalized,
            "TRADE",
            reason,
            candidate_count=len(candidates),
            observed_on=observed_on,
            selected_short_strike=spread.short_put.strike,
            selected_long_strike=spread.long_put.strike,
            selected_expiration=spread.short_put.expiration_date,
            selected_credit=spread.credit,
            selected_score=selected.score,
            position_id=position.position_id,
        )
        return PaperAutomationResult(
            normalized,
            "OPENED",
            "TRADE",
            reason,
            position=position,
            observation=observation,
        )
