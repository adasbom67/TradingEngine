from __future__ import annotations

from datetime import date
from uuid import uuid4

from app.paper.ledger import PaperLedger
from app.paper.models import (
    PaperAccount,
    PaperDailySnapshot,
    PaperObservation,
    PaperPosition,
)


class PaperTradingService:
    def __init__(self, ledger: PaperLedger | None = None) -> None:
        self._ledger = ledger or PaperLedger()

    def status(self) -> PaperAccount:
        return self._ledger.load()

    def initialize(self, initial_cash: float, *, overwrite: bool = False) -> PaperAccount:
        if initial_cash <= 0:
            raise ValueError("Initial cash must be positive.")
        current = self._ledger.load()
        if (current.positions or current.observations or current.snapshots) and not overwrite:
            raise ValueError("Paper account already contains activity.")
        account = PaperAccount(initial_cash=initial_cash)
        self._ledger.save(account)
        return account

    def open_position(
        self,
        symbol: str,
        expiration: date,
        short_strike: float,
        long_strike: float,
        entry_credit: float,
        *,
        quantity: int = 1,
        opened_on: date | None = None,
        entry_decision: str = "MANUAL",
        allow_watch_simulation: bool = False,
        entry_score: float | None = None,
        entry_thesis: list[str] | None = None,
        entry_reasons: list[str] | None = None,
        entry_warnings: list[str] | None = None,
        entry_constraints: dict | None = None,
        market_regime: str | None = None,
        source_scan_reference: str | None = None,
        selected_pricing_method: str | None = None,
        quote_audit_status: str | None = None,
    ) -> PaperPosition:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be blank.")
        if short_strike <= long_strike:
            raise ValueError("Short strike must be above long strike.")
        if entry_credit <= 0 or entry_credit >= short_strike - long_strike:
            raise ValueError("Entry credit must be positive and less than spread width.")
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        open_date = opened_on or date.today()
        if expiration <= open_date:
            raise ValueError("Expiration must be after the open date.")
        decision = entry_decision.strip().upper()
        if decision == "PASS":
            raise ValueError("PASS recommendations cannot be opened in Paper Trading.")
        if decision == "WATCH" and not allow_watch_simulation:
            raise ValueError(
                "WATCH recommendations require explicit experimental simulation approval."
            )
        if decision not in {"TRADE", "WATCH", "MANUAL"}:
            raise ValueError(f"Unsupported paper-entry decision: {decision or 'blank'}.")

        account = self._ledger.load()
        if account.has_open_symbol(normalized):
            raise ValueError(f"An open paper position already exists for {normalized}.")
        position = PaperPosition(
            position_id=uuid4().hex[:12],
            symbol=normalized,
            opened_on=open_date,
            expiration=expiration,
            short_strike=float(short_strike),
            long_strike=float(long_strike),
            entry_credit=float(entry_credit),
            quantity=quantity,
            current_debit=float(entry_credit),
            last_marked_on=open_date,
            entry_decision=decision,
            entry_score=entry_score,
            entry_thesis=list(entry_thesis or []),
            entry_reasons=list(entry_reasons or []),
            entry_warnings=list(entry_warnings or []),
            entry_constraints=dict(entry_constraints or {}),
            market_regime=market_regime,
            source_scan_reference=source_scan_reference,
            selected_pricing_method=selected_pricing_method,
            quote_audit_status=quote_audit_status,
            experimental=decision == "WATCH",
        )
        account.positions.append(position)
        self._ledger.save(account)
        return position

    def record_observation(
        self,
        symbol: str,
        decision: str,
        reason: str,
        *,
        candidate_count: int = 0,
        observed_on: date | None = None,
        selected_short_strike: float | None = None,
        selected_long_strike: float | None = None,
        selected_expiration: date | None = None,
        selected_credit: float | None = None,
        selected_score: float | None = None,
        position_id: str | None = None,
    ) -> PaperObservation:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be blank.")
        if not decision.strip():
            raise ValueError("Decision cannot be blank.")
        if not reason.strip():
            raise ValueError("Observation reason cannot be blank.")
        if candidate_count < 0:
            raise ValueError("Candidate count cannot be negative.")

        observation = PaperObservation(
            observed_on=observed_on or date.today(),
            symbol=normalized,
            decision=decision.strip().upper(),
            reason=reason.strip(),
            candidate_count=candidate_count,
            selected_short_strike=selected_short_strike,
            selected_long_strike=selected_long_strike,
            selected_expiration=selected_expiration,
            selected_credit=selected_credit,
            selected_score=selected_score,
            position_id=position_id,
        )
        account = self._ledger.load()
        account.observations.append(observation)
        self._ledger.save(account)
        return observation

    def mark_position(
        self,
        position_id: str,
        current_debit: float,
        *,
        marked_on: date | None = None,
    ) -> PaperPosition:
        if current_debit < 0:
            raise ValueError("Current debit cannot be negative.")
        account = self._ledger.load()
        position = self._find_open(account, position_id)
        position.current_debit = min(current_debit, position.width)
        position.last_marked_on = marked_on or date.today()
        self._ledger.save(account)
        return position

    def close_position(
        self,
        position_id: str,
        exit_debit: float,
        reason: str,
        *,
        closed_on: date | None = None,
    ) -> PaperPosition:
        if exit_debit < 0:
            raise ValueError("Exit debit cannot be negative.")
        if not reason.strip():
            raise ValueError("Exit reason cannot be blank.")
        account = self._ledger.load()
        position = self._find_open(account, position_id)
        close_date = closed_on or date.today()
        if close_date < position.opened_on:
            raise ValueError("Close date cannot precede open date.")
        position.exit_debit = min(exit_debit, position.width)
        position.current_debit = position.exit_debit
        position.closed_on = close_date
        position.last_marked_on = close_date
        position.exit_reason = reason.strip().upper()
        self._ledger.save(account)
        return position

    def record_snapshot(self, *, snapshot_on: date | None = None) -> PaperDailySnapshot:
        account = self._ledger.load()
        current_date = snapshot_on or date.today()
        snapshot = PaperDailySnapshot(
            snapshot_on=current_date,
            equity=account.equity,
            realized_pnl=account.realized_pnl,
            unrealized_pnl=account.unrealized_pnl,
            committed_risk=account.committed_risk,
            open_positions=len(account.open_positions),
        )
        account.snapshots = [
            item for item in account.snapshots if item.snapshot_on != current_date
        ]
        account.snapshots.append(snapshot)
        account.snapshots.sort(key=lambda item: item.snapshot_on)
        self._ledger.save(account)
        return snapshot

    @staticmethod
    def _find_open(account: PaperAccount, position_id: str) -> PaperPosition:
        for position in account.positions:
            if position.position_id == position_id and position.is_open:
                return position
        raise ValueError(f"Open paper position not found: {position_id}")
