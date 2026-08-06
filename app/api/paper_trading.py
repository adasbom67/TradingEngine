from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.paper.ledger import PaperLedger
from app.paper.models import PaperAccount, PaperPosition
from app.paper.service import PaperTradingService


class PaperInitializeRequest(BaseModel):
    initial_cash: float = Field(default=100_000.0, gt=0)
    overwrite: bool = False


class PaperOpenPositionRequest(BaseModel):
    symbol: str
    expiration: date
    short_strike: float
    long_strike: float
    entry_credit: float
    quantity: int = Field(default=1, ge=1)
    opened_on: date | None = None


class PaperMarkRequest(BaseModel):
    current_debit: float = Field(ge=0)
    marked_on: date | None = None


class PaperCloseRequest(BaseModel):
    exit_debit: float = Field(ge=0)
    reason: str
    closed_on: date | None = None


class PaperSnapshotRequest(BaseModel):
    snapshot_on: date | None = None


def _position_payload(position: PaperPosition) -> dict:
    payload = position.to_dict()
    payload.update({
        "is_open": position.is_open,
        "width": position.width,
        "maximum_risk": position.maximum_risk,
        "unrealized_pnl": position.unrealized_pnl,
        "realized_pnl": position.realized_pnl,
        "days_held": position.days_held,
    })
    return payload


def _account_payload(account: PaperAccount, ledger_path: Path) -> dict:
    return {
        "mode": "PAPER",
        "execution_mode": "SIMULATION_ONLY",
        "ledger_path": str(ledger_path),
        "initialized": ledger_path.exists(),
        "summary": {
            "initial_cash": account.initial_cash,
            "equity": account.equity,
            "realized_pnl": account.realized_pnl,
            "unrealized_pnl": account.unrealized_pnl,
            "committed_risk": account.committed_risk,
            "available_buying_power": account.available_buying_power,
            "open_position_count": len(account.open_positions),
            "closed_position_count": len(account.closed_positions),
            "win_rate": account.win_rate,
            "maximum_drawdown": account.maximum_drawdown,
        },
        "open_positions": [_position_payload(item) for item in account.open_positions],
        "closed_positions": [_position_payload(item) for item in reversed(account.closed_positions)],
        "observations": [item.to_dict() for item in reversed(account.observations[-100:])],
        "snapshots": [item.to_dict() for item in account.snapshots[-250:]],
        "safeguards": {
            "broker_orders_enabled": False,
            "live_trading_enabled": False,
            "simulation_only": True,
            "message": "Paper Trading writes only to the local simulation ledger. No Schwab order is created or submitted.",
        },
    }


def create_paper_trading_router(ledger_path: str | Path = "data/paper_account.json") -> APIRouter:
    path = Path(ledger_path)
    service = PaperTradingService(PaperLedger(path))
    router = APIRouter(prefix="/api/paper", tags=["paper-trading"])

    def account_response() -> dict:
        return _account_payload(service.status(), path)

    @router.get("/account")
    def get_account() -> dict:
        return account_response()

    @router.post("/initialize")
    def initialize(request: PaperInitializeRequest) -> dict:
        try:
            service.initialize(request.initial_cash, overwrite=request.overwrite)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return account_response()

    @router.post("/positions")
    def open_position(request: PaperOpenPositionRequest) -> dict:
        try:
            position = service.open_position(request.symbol, request.expiration, request.short_strike, request.long_strike, request.entry_credit, quantity=request.quantity, opened_on=request.opened_on)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"position": _position_payload(position), "account": account_response()}

    @router.post("/positions/{position_id}/mark")
    def mark_position(position_id: str, request: PaperMarkRequest) -> dict:
        try:
            position = service.mark_position(position_id, request.current_debit, marked_on=request.marked_on)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"position": _position_payload(position), "account": account_response()}

    @router.post("/positions/{position_id}/close")
    def close_position(position_id: str, request: PaperCloseRequest) -> dict:
        try:
            position = service.close_position(position_id, request.exit_debit, request.reason, closed_on=request.closed_on)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"position": _position_payload(position), "account": account_response()}

    @router.post("/snapshot")
    def record_snapshot(request: PaperSnapshotRequest) -> dict:
        service.record_snapshot(snapshot_on=request.snapshot_on)
        return account_response()

    return router
