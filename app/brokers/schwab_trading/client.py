from __future__ import annotations

from datetime import datetime
from typing import Any

from app.brokers.schwab_trading.errors import SchwabTradingResponseError
from app.trading.models import (
    BrokerAccount, BrokerAccountSnapshot, BrokerOrder, BrokerPosition, OrderPlan,
)


class SchwabTradingClient:
    """Read-only Schwab trading adapter plus local dry-run preview.

    Phase 8A deliberately exposes no submit, cancel, or replace method.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    @staticmethod
    def _payload(response: Any, description: str) -> Any:
        try:
            response.raise_for_status()
        except Exception as exc:
            status = getattr(response, "status_code", "unknown")
            body = getattr(response, "text", "")
            raise SchwabTradingResponseError(
                f"Schwab {description} request failed. Status: {status}. {body[:500]}"
            ) from exc
        return response.json()

    def get_accounts(self) -> list[BrokerAccount]:
        response = self._client.get_account_numbers()
        payload = self._payload(response, "account numbers")
        if not isinstance(payload, list):
            raise SchwabTradingResponseError("Schwab account-number payload must be a list.")
        result = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            account_id = str(item.get("accountNumber", ""))
            account_hash = str(item.get("hashValue", ""))
            if account_id and account_hash:
                result.append(BrokerAccount(account_id, account_hash, str(item.get("type", "UNKNOWN"))))
        return result

    def get_account(self, account_hash: str) -> BrokerAccountSnapshot:
        payload = self._payload(self._client.get_account(account_hash), "account")
        container = payload.get("securitiesAccount", payload) if isinstance(payload, dict) else {}
        balances = container.get("currentBalances", {}) if isinstance(container, dict) else {}
        account_id = str(container.get("accountNumber", account_hash[-4:]))
        account = BrokerAccount(account_id, account_hash, str(container.get("type", "UNKNOWN")))
        account_value = float(balances.get("liquidationValue", balances.get("accountValue", 0.0)) or 0.0)
        buying_power = float(balances.get("buyingPower", balances.get("availableFunds", 0.0)) or 0.0)
        cash = float(balances.get("cashBalance", balances.get("cashAvailableForTrading", 0.0)) or 0.0)
        return BrokerAccountSnapshot(account, account_value, buying_power, cash)

    def get_positions(self, account_hash: str) -> list[BrokerPosition]:
        try:
            from schwab.client import Client
            fields = Client.Account.Fields.POSITIONS
            response = self._client.get_account(account_hash, fields=fields)
        except Exception:
            response = self._client.get_account(account_hash)
        payload = self._payload(response, "positions")
        container = payload.get("securitiesAccount", payload) if isinstance(payload, dict) else {}
        rows = container.get("positions", []) if isinstance(container, dict) else []
        result = []
        for row in rows if isinstance(rows, list) else []:
            instrument = row.get("instrument", {}) if isinstance(row, dict) else {}
            quantity = float(row.get("longQuantity", 0.0) or 0.0) - float(row.get("shortQuantity", 0.0) or 0.0)
            result.append(BrokerPosition(
                symbol=str(instrument.get("symbol", "")), quantity=quantity,
                market_value=float(row.get("marketValue", 0.0) or 0.0),
                average_price=float(row.get("averagePrice", 0.0) or 0.0),
                asset_type=str(instrument.get("assetType", "UNKNOWN")), raw=dict(row),
            ))
        return result

    def get_orders(self, account_hash: str, *, from_time: datetime, to_time: datetime) -> list[BrokerOrder]:
        response = self._client.get_orders_for_account(
            account_hash, from_entered_datetime=from_time, to_entered_datetime=to_time
        )
        payload = self._payload(response, "orders")
        rows = payload if isinstance(payload, list) else []
        result = []
        for row in rows:
            legs = row.get("orderLegCollection", []) if isinstance(row, dict) else []
            symbol = None
            if legs and isinstance(legs[0], dict):
                symbol = legs[0].get("instrument", {}).get("symbol")
            entered = row.get("enteredTime")
            try:
                entered_at = datetime.fromisoformat(entered.replace("Z", "+00:00")) if entered else None
            except (TypeError, ValueError):
                entered_at = None
            result.append(BrokerOrder(
                broker_order_id=str(row.get("orderId", "")), status=str(row.get("status", "UNKNOWN")),
                entered_at=entered_at, symbol=symbol,
                quantity=int(row.get("quantity", 0) or 0),
                price=float(row["price"]) if row.get("price") is not None else None,
                raw=dict(row),
            ))
        return result

    def preview_order(self, account_hash: str, order: OrderPlan) -> dict:
        # Schwab-py 1.5.1 does not expose a guaranteed preview endpoint. Phase 8A
        # therefore returns a deterministic local preview and never submits.
        return {
            "mode": "DRY_RUN",
            "submission_enabled": False,
            "account": "*" * max(len(account_hash) - 4, 0) + account_hash[-4:],
            "plan_id": order.plan_id,
            "symbol": order.symbol,
            "quantity": order.quantity,
            "order_type": "NET_CREDIT",
            "limit_price": order.limit_price,
            "maximum_risk": order.maximum_risk,
            "legs": [
                {"symbol": leg.symbol, "instruction": leg.instruction.value, "quantity": leg.quantity}
                for leg in order.legs
            ],
        }
