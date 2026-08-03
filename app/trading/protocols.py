from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.trading.models import (
    BrokerAccount, BrokerAccountSnapshot, BrokerOrder, BrokerPosition, OrderPlan,
)


class TradingBroker(Protocol):
    """Read-only broker contract for Phase 8A. No mutation methods are exposed."""

    def get_accounts(self) -> list[BrokerAccount]: ...
    def get_account(self, account_hash: str) -> BrokerAccountSnapshot: ...
    def get_positions(self, account_hash: str) -> list[BrokerPosition]: ...
    def get_orders(
        self, account_hash: str, *, from_time: datetime, to_time: datetime
    ) -> list[BrokerOrder]: ...
    def preview_order(self, account_hash: str, order: OrderPlan) -> dict: ...
