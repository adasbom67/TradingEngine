from __future__ import annotations

import json

from app.trading.models import (
    BrokerAccountSnapshot,
    BrokerOrder,
    BrokerPosition,
    OrderPlan,
    ReconciliationResult,
)
from app.trading.service import DryRunResult


class TradingReport:
    def account(self, snapshot: BrokerAccountSnapshot) -> str:
        return "\n".join([
            "Schwab Account (Read Only)",
            "",
            f"Account: {snapshot.account.masked_id}",
            f"Type: {snapshot.account.account_type}",
            f"Account value: ${snapshot.account_value:,.2f}",
            f"Buying power: ${snapshot.buying_power:,.2f}",
            f"Cash available: ${snapshot.cash_available:,.2f}",
        ])

    def positions(self, rows: list[BrokerPosition]) -> str:
        lines = ["Schwab Positions (Read Only)", ""]
        if not rows:
            return "\n".join(lines + ["No positions."])
        for row in rows:
            lines.append(
                f"{row.symbol:<24} qty {row.quantity:>8.2f}  "
                f"value ${row.market_value:>12,.2f}"
            )
        return "\n".join(lines)

    def orders(self, rows: list[BrokerOrder]) -> str:
        lines = ["Schwab Orders (Read Only)", ""]
        if not rows:
            return "\n".join(lines + ["No orders in the selected period."])
        for row in rows:
            lines.append(
                f"{row.broker_order_id:<14} {row.status:<18} "
                f"{row.symbol or '-':<24} qty {row.quantity}"
            )
        return "\n".join(lines)

    def plan(self, plan: OrderPlan) -> str:
        lines = [
            "Dry-Run Bull Put Order Plan",
            "",
            f"Plan ID: {plan.plan_id}",
            f"Symbol: {plan.symbol}",
            f"Quantity: {plan.quantity}",
            f"Limit credit: ${plan.limit_price:.2f}",
            f"Maximum risk: ${plan.maximum_risk:,.2f}",
            "Legs:",
        ]
        lines.extend(
            f"- {leg.instruction.value:<14} {leg.symbol}" for leg in plan.legs
        )
        lines.extend(["", "LIVE SUBMISSION IS NOT AVAILABLE IN v0.10.1."])
        return "\n".join(lines)

    def dry_run(self, result: DryRunResult) -> str:
        lines = [
            self.plan(result.plan),
            "",
            f"Validation: {'PASS' if result.validation.valid else 'FAIL'}",
        ]
        lines.extend(f"ERROR: {item}" for item in result.validation.errors)
        lines.extend(f"WARNING: {item}" for item in result.validation.warnings)
        if result.preview:
            lines.extend([
                "",
                "Local preview:",
                json.dumps(result.preview, indent=2, sort_keys=True),
            ])
        return "\n".join(lines)

    def reconciliation(self, result: ReconciliationResult) -> str:
        lines = [
            "Read-Only Account Reconciliation",
            "",
            f"Account: {result.account.account.masked_id}",
            f"Positions: {len(result.positions)}",
            f"Recent orders: {len(result.orders)}",
            f"Status: {'MATCHED' if result.successful else 'REVIEW REQUIRED'}",
        ]
        lines.extend(
            f"- {issue.category}: {issue.message}" for issue in result.issues
        )
        return "\n".join(lines)
