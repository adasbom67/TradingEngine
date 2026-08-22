from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date


@dataclass
class PaperPosition:
    position_id: str
    symbol: str
    opened_on: date
    expiration: date
    short_strike: float
    long_strike: float
    entry_credit: float
    quantity: int = 1
    current_debit: float | None = None
    closed_on: date | None = None
    exit_debit: float | None = None
    exit_reason: str | None = None
    last_marked_on: date | None = None
    entry_decision: str = "MANUAL"
    entry_score: float | None = None
    entry_thesis: list[str] = field(default_factory=list)
    entry_reasons: list[str] = field(default_factory=list)
    entry_warnings: list[str] = field(default_factory=list)
    entry_constraints: dict = field(default_factory=dict)
    market_regime: str | None = None
    source_scan_reference: str | None = None
    selected_pricing_method: str | None = None
    quote_audit_status: str | None = None
    experimental: bool = False
    strategy_type: str = "BULL_PUT"

    @property
    def is_open(self) -> bool:
        return self.closed_on is None

    @property
    def width(self) -> float:
        return abs(self.short_strike - self.long_strike)

    @property
    def maximum_risk(self) -> float:
        return (self.width - self.entry_credit) * 100 * self.quantity

    @property
    def unrealized_pnl(self) -> float:
        if not self.is_open or self.current_debit is None:
            return 0.0
        return (self.entry_credit - self.current_debit) * 100 * self.quantity

    @property
    def realized_pnl(self) -> float:
        if self.is_open or self.exit_debit is None:
            return 0.0
        return (self.entry_credit - self.exit_debit) * 100 * self.quantity

    @property
    def days_held(self) -> int:
        end = self.closed_on or self.last_marked_on or date.today()
        return max((end - self.opened_on).days, 0)

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("opened_on", "expiration", "closed_on", "last_marked_on"):
            value = data[key]
            data[key] = value.isoformat() if value else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PaperPosition":
        values = dict(data)
        for key in ("opened_on", "expiration", "closed_on", "last_marked_on"):
            if values.get(key):
                values[key] = date.fromisoformat(values[key])
        return cls(**values)


@dataclass
class PaperObservation:
    observed_on: date
    symbol: str
    decision: str
    reason: str
    candidate_count: int = 0
    selected_short_strike: float | None = None
    selected_long_strike: float | None = None
    selected_expiration: date | None = None
    selected_credit: float | None = None
    selected_score: float | None = None
    position_id: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["observed_on"] = self.observed_on.isoformat()
        if self.selected_expiration:
            data["selected_expiration"] = self.selected_expiration.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PaperObservation":
        values = dict(data)
        values["observed_on"] = date.fromisoformat(values["observed_on"])
        if values.get("selected_expiration"):
            values["selected_expiration"] = date.fromisoformat(
                values["selected_expiration"]
            )
        return cls(**values)


@dataclass
class PaperDailySnapshot:
    snapshot_on: date
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    committed_risk: float
    open_positions: int

    def to_dict(self) -> dict:
        data = asdict(self)
        data["snapshot_on"] = self.snapshot_on.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PaperDailySnapshot":
        values = dict(data)
        values["snapshot_on"] = date.fromisoformat(values["snapshot_on"])
        return cls(**values)


@dataclass
class PaperAccount:
    initial_cash: float = 100_000.0
    positions: list[PaperPosition] = field(default_factory=list)
    observations: list[PaperObservation] = field(default_factory=list)
    snapshots: list[PaperDailySnapshot] = field(default_factory=list)

    @property
    def realized_pnl(self) -> float:
        return sum(position.realized_pnl for position in self.positions)

    @property
    def unrealized_pnl(self) -> float:
        return sum(position.unrealized_pnl for position in self.positions)

    @property
    def equity(self) -> float:
        return self.initial_cash + self.realized_pnl + self.unrealized_pnl

    @property
    def open_positions(self) -> list[PaperPosition]:
        return [position for position in self.positions if position.is_open]

    @property
    def closed_positions(self) -> list[PaperPosition]:
        return [position for position in self.positions if not position.is_open]

    @property
    def committed_risk(self) -> float:
        return sum(position.maximum_risk for position in self.open_positions)

    @property
    def available_buying_power(self) -> float:
        return max(0.0, self.equity - self.committed_risk)

    @property
    def win_rate(self) -> float:
        closed = self.closed_positions
        if not closed:
            return 0.0
        return sum(position.realized_pnl > 0 for position in closed) / len(closed)

    @property
    def maximum_drawdown(self) -> float:
        values = [self.initial_cash] + [item.equity for item in self.snapshots]
        peak = values[0]
        drawdown = 0.0
        for value in values:
            peak = max(peak, value)
            drawdown = max(drawdown, peak - value)
        return drawdown

    def has_open_symbol(self, symbol: str) -> bool:
        normalized = symbol.strip().upper()
        return any(position.symbol == normalized for position in self.open_positions)

    def has_open_strategy(self, symbol: str, strategy_type: str) -> bool:
        normalized = symbol.strip().upper()
        strategy = strategy_type.strip().upper()
        return any(
            position.symbol == normalized and position.strategy_type == strategy
            for position in self.open_positions
        )

    def to_dict(self) -> dict:
        return {
            "initial_cash": self.initial_cash,
            "positions": [position.to_dict() for position in self.positions],
            "observations": [item.to_dict() for item in self.observations],
            "snapshots": [item.to_dict() for item in self.snapshots],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PaperAccount":
        return cls(
            initial_cash=float(data.get("initial_cash", 100_000.0)),
            positions=[PaperPosition.from_dict(item) for item in data.get("positions", [])],
            observations=[PaperObservation.from_dict(item) for item in data.get("observations", [])],
            snapshots=[PaperDailySnapshot.from_dict(item) for item in data.get("snapshots", [])],
        )
