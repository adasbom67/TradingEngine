from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from schwab.client import Client


class SchwabMarketDataError(RuntimeError):
    """Raised when Schwab market-data retrieval fails."""


class SchwabMarketDataClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    def get_put_option_chain(self, symbol: str, from_date: date | None = None,
                             to_date: date | None = None,
                             strike_count: int | None = None) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("Symbol cannot be blank.")

        response = self._client.get_option_chain(
            normalized_symbol,
            contract_type=Client.Options.ContractType.PUT,
            strike_count=strike_count,
            include_underlying_quote=True,
            from_date=from_date,
            to_date=to_date,
        )
        try:
            response.raise_for_status()
        except Exception as exc:
            status_code = getattr(response, "status_code", "unknown")
            body = getattr(response, "text", "")
            detail = f" Status: {status_code}."
            if body:
                detail += f" Response: {body[:500]}"
            raise SchwabMarketDataError(
                f"Schwab option-chain request failed for {normalized_symbol}.{detail}"
            ) from exc
        payload = response.json()
        if not isinstance(payload, dict):
            raise SchwabMarketDataError("Schwab returned an invalid option-chain payload.")
        return payload

    def get_daily_price_history(
        self,
        symbol: str,
        period_years: int = 2,
    ) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("Symbol cannot be blank.")

        end_datetime = datetime.now(timezone.utc)
        start_datetime = end_datetime - timedelta(days=period_years * 366)

        response = self._client.get_price_history_every_day(
            normalized_symbol,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            need_extended_hours_data=False,
            need_previous_close=True,
        )

        try:
            response.raise_for_status()
        except Exception as exc:
            status_code = getattr(response, "status_code", "unknown")
            body = getattr(response, "text", "")
            detail = f" Status: {status_code}."

            if body:
                detail += f" Response: {body[:500]}"

            raise SchwabMarketDataError(
                f"Schwab price-history request failed for "
                f"{normalized_symbol}.{detail}"
            ) from exc

        payload = response.json()

        if not isinstance(payload, dict):
            raise SchwabMarketDataError(
                "Schwab returned an invalid price-history payload."
            )

        candles = payload.get("candles")

        if not isinstance(candles, list) or not candles:
            raise SchwabMarketDataError(
                f"Schwab returned no daily candles for {normalized_symbol}."
            )

        return payload