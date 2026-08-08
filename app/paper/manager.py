from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.config.strategy_config import PutSpreadConfig
from app.data.schwab_option_chain_adapter import SchwabOptionChainAdapter
from app.paper.models import PaperPosition
from app.paper.service import PaperTradingService


@dataclass(frozen=True)
class PaperManagementResult:
    position_id: str
    symbol: str
    action: str
    reason: str
    current_debit: float | None = None
    pnl: float = 0.0
    days_to_expiration: int | None = None


class PaperPositionManager:
    """Mark and automatically manage open paper positions from live option chains."""

    def __init__(
        self,
        service: PaperTradingService,
        market_data: SchwabMarketDataClient,
        *,
        adapter: SchwabOptionChainAdapter | None = None,
    ) -> None:
        self._service = service
        self._market_data = market_data
        self._adapter = adapter or SchwabOptionChainAdapter()

    def manage_all(
        self,
        config: PutSpreadConfig,
        *,
        as_of: date | None = None,
        auto_close: bool = True,
    ) -> list[PaperManagementResult]:
        config.validate()
        current_date = as_of or date.today()
        results: list[PaperManagementResult] = []
        for position in list(self._service.status().open_positions):
            results.append(
                self._manage_position(position, config, current_date, auto_close)
            )
        self._service.record_snapshot(snapshot_on=current_date)
        return results

    def _manage_position(
        self,
        position: PaperPosition,
        config: PutSpreadConfig,
        current_date: date,
        auto_close: bool,
    ) -> PaperManagementResult:
        try:
            raw = self._market_data.get_put_option_chain(
                position.symbol,
                from_date=position.expiration,
                to_date=position.expiration,
            )
            chain = self._adapter.to_option_chain(raw, requested_symbol=position.symbol)
            short = self._find_contract(
                chain.contracts, position.expiration, position.short_strike
            )
            long = self._find_contract(
                chain.contracts, position.expiration, position.long_strike
            )
        except Exception as exc:
            return PaperManagementResult(
                position.position_id,
                position.symbol,
                "ERROR",
                f"Unable to mark position: {exc}",
            )

        if short is None or long is None:
            return PaperManagementResult(
                position.position_id,
                position.symbol,
                "ERROR",
                "Matching option contracts were not found in the live chain.",
            )

        # Conservative close estimate: buy short at ask, sell long at bid.
        current_debit = round(min(max(short.ask - long.bid, 0.0), position.width), 4)
        marked = self._service.mark_position(
            position.position_id,
            current_debit,
            marked_on=current_date,
        )
        dte = max((position.expiration - current_date).days, 0)
        target_debit = position.entry_credit * (1 - config.profit_target_percent / 100)
        stop_debit = position.entry_credit * (1 + config.stop_loss_percent / 100)

        reason: str | None = None
        if current_debit >= stop_debit:
            reason = "STOP_LOSS"
        elif current_debit <= target_debit:
            reason = "PROFIT_TARGET"
        elif dte <= config.exit_dte:
            reason = "EXIT_DTE"

        if reason is None:
            return PaperManagementResult(
                position.position_id,
                position.symbol,
                "MARKED",
                "Position remains open.",
                current_debit=current_debit,
                pnl=marked.unrealized_pnl,
                days_to_expiration=dte,
            )

        if not auto_close:
            return PaperManagementResult(
                position.position_id,
                position.symbol,
                "EXIT_RECOMMENDED",
                reason,
                current_debit=current_debit,
                pnl=marked.unrealized_pnl,
                days_to_expiration=dte,
            )

        closed = self._service.close_position(
            position.position_id,
            current_debit,
            reason,
            closed_on=current_date,
        )
        return PaperManagementResult(
            position.position_id,
            position.symbol,
            "CLOSED",
            reason,
            current_debit=current_debit,
            pnl=closed.realized_pnl,
            days_to_expiration=dte,
        )

    @staticmethod
    def _find_contract(contracts, expiration: date, strike: float):
        for contract in contracts:
            if (
                contract.option_type.upper() == "PUT"
                and contract.expiration_date == expiration
                and abs(contract.strike - strike) < 1e-9
            ):
                return contract
        return None
