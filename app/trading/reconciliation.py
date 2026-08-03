from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.trading.models import ReconciliationIssue, ReconciliationResult
from app.trading.protocols import TradingBroker


class ReadOnlyReconciliationService:
    def reconcile(self, broker: TradingBroker, account_hash: str) -> ReconciliationResult:
        account = broker.get_account(account_hash)
        positions = tuple(broker.get_positions(account_hash))
        now = datetime.now(timezone.utc)
        orders = tuple(broker.get_orders(account_hash, from_time=now-timedelta(days=30), to_time=now))
        issues: list[ReconciliationIssue] = []
        if account.account.account_hash != account_hash:
            issues.append(ReconciliationIssue("ACCOUNT_MISMATCH", "Broker account hash did not match the requested account."))
        if account.account_value < 0:
            issues.append(ReconciliationIssue("INVALID_ACCOUNT_VALUE", "Broker account value cannot be negative."))
        return ReconciliationResult(account, positions, orders, tuple(issues))
