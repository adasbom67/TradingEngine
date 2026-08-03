from __future__ import annotations

from dataclasses import dataclass

from app.trading.models import OrderPlan, OrderValidationResult
from app.trading.protocols import TradingBroker
from app.trading.validation import OrderPlanValidator


@dataclass(frozen=True)
class DryRunResult:
    account_hash: str
    plan: OrderPlan
    validation: OrderValidationResult
    preview: dict


class DryRunTradingService:
    def __init__(self, broker: TradingBroker, validator: OrderPlanValidator | None = None) -> None:
        self._broker = broker
        self._validator = validator or OrderPlanValidator()

    def execute(self, account_hash: str, plan: OrderPlan) -> DryRunResult:
        validation = self._validator.validate(plan)
        preview = self._broker.preview_order(account_hash, plan) if validation.valid else {}
        return DryRunResult(account_hash, plan, validation, preview)
