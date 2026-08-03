from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    PAPER = "paper"
    DRY_RUN = "dry_run"
    LIVE = "live"


class AssetType(str, Enum):
    OPTION = "OPTION"
    EQUITY = "EQUITY"


class Instruction(str, Enum):
    BUY_TO_OPEN = "BUY_TO_OPEN"
    SELL_TO_OPEN = "SELL_TO_OPEN"
    BUY_TO_CLOSE = "BUY_TO_CLOSE"
    SELL_TO_CLOSE = "SELL_TO_CLOSE"


class OrderSide(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class OrderState(str, Enum):
    PLANNED = "PLANNED"
    PREVIEWED = "PREVIEWED"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"
    SUBMITTING = "SUBMITTING"
    SUBMISSION_UNKNOWN = "SUBMISSION_UNKNOWN"
    SUBMITTED = "SUBMITTED"
    WORKING = "WORKING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class BrokerAccount:
    account_id: str
    account_hash: str
    account_type: str = "UNKNOWN"

    @property
    def masked_id(self) -> str:
        value = self.account_id.strip()
        return "*" * max(len(value) - 4, 0) + value[-4:]


@dataclass(frozen=True)
class BrokerAccountSnapshot:
    account: BrokerAccount
    account_value: float
    buying_power: float
    cash_available: float = 0.0
    captured_at: datetime | None = None


@dataclass(frozen=True)
class OrderLeg:
    symbol: str
    asset_type: AssetType
    instruction: Instruction
    quantity: int
    underlying: str
    expiration: date
    strike: float
    option_type: str = "PUT"


@dataclass(frozen=True)
class OrderPlan:
    plan_id: str
    symbol: str
    quantity: int
    side: OrderSide
    limit_price: float
    duration: str
    session: str
    legs: tuple[OrderLeg, ...]
    created_at: datetime
    source_candidate_score: float | None = None
    source_decision: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def maximum_risk(self) -> float:
        strikes = sorted((leg.strike for leg in self.legs), reverse=True)
        if len(strikes) != 2:
            return 0.0
        width = strikes[0] - strikes[1]
        if self.side is OrderSide.CREDIT:
            return max((width - self.limit_price) * 100 * self.quantity, 0.0)
        return self.limit_price * 100 * self.quantity


@dataclass(frozen=True)
class OrderValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BrokerOrder:
    broker_order_id: str
    status: str
    entered_at: datetime | None = None
    symbol: str | None = None
    quantity: int = 0
    price: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrokerPosition:
    symbol: str
    quantity: float
    market_value: float = 0.0
    average_price: float = 0.0
    asset_type: str = "UNKNOWN"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReconciliationIssue:
    category: str
    message: str


@dataclass(frozen=True)
class ReconciliationResult:
    account: BrokerAccountSnapshot
    positions: tuple[BrokerPosition, ...]
    orders: tuple[BrokerOrder, ...]
    issues: tuple[ReconciliationIssue, ...] = ()

    @property
    def successful(self) -> bool:
        return not self.issues
