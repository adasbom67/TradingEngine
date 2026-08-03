from __future__ import annotations

from datetime import date

from app.trading.models import Instruction, OrderPlan, OrderSide, OrderValidationResult


class OrderPlanValidator:
    def validate(self, plan: OrderPlan, *, today: date | None = None) -> OrderValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        reference = today or date.today()
        if plan.quantity <= 0:
            errors.append("Order quantity must be greater than zero.")
        if len(plan.legs) != 2:
            errors.append("Bull put spread must contain exactly two legs.")
            return OrderValidationResult(False, tuple(errors), tuple(warnings))
        short, long = plan.legs
        if short.instruction is not Instruction.SELL_TO_OPEN:
            errors.append("First leg must be SELL_TO_OPEN.")
        if long.instruction is not Instruction.BUY_TO_OPEN:
            errors.append("Second leg must be BUY_TO_OPEN.")
        if short.underlying != long.underlying or short.underlying != plan.symbol:
            errors.append("Both legs must use the same underlying as the order plan.")
        if short.expiration != long.expiration:
            errors.append("Both option legs must have the same expiration.")
        if short.expiration <= reference:
            errors.append("Option expiration must be after today.")
        if short.option_type != "PUT" or long.option_type != "PUT":
            errors.append("Bull put spread legs must be puts.")
        if short.strike <= long.strike:
            errors.append("Short put strike must be above long put strike.")
        if plan.side is not OrderSide.CREDIT:
            errors.append("Bull put entry must be a credit order.")
        width = short.strike - long.strike
        if plan.limit_price <= 0:
            errors.append("Credit limit price must be positive.")
        if plan.limit_price >= width:
            errors.append("Credit must be less than spread width.")
        if plan.duration != "DAY":
            warnings.append("Initial live release is designed for DAY orders.")
        if plan.session != "NORMAL":
            errors.append("Option spread orders must use the NORMAL session.")
        return OrderValidationResult(not errors, tuple(errors), tuple(warnings))
