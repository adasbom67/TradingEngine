import os
from pathlib import Path
from datetime import date

import pandas as pd
from dotenv import load_dotenv
from schwab.auth import client_from_manual_flow, client_from_token_file

load_dotenv()

class SchwabClient:
    """Authenticated interface to Schwab market data."""

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parents[2]

        self.client_id = os.getenv("SCHWAB_CLIENT_ID")
        self.client_secret = os.getenv("SCHWAB_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SCHWAB_REDIRECT_URI")
        self.token_path = project_root / "token.json"

        if not self.client_id:
            raise ValueError("Missing SCHWAB_CLIENT_ID in .env file")

        if not self.client_secret:
            raise ValueError("Missing SCHWAB_CLIENT_SECRET in .env file")

        if not self.redirect_uri:
            raise ValueError("Missing SCHWAB_REDIRECT_URI in .env file")

        self.client = self._create_client()

    def _create_client(self):
        """
        Load an existing token or start manual authentication
        when no token file exists.
        """

        if self.token_path.exists():
            return client_from_token_file(
                token_path=str(self.token_path),
                api_key=self.client_id,
                app_secret=self.client_secret,
            )

        return client_from_manual_flow(
            api_key=self.client_id,
            app_secret=self.client_secret,
            callback_url=self.redirect_uri,
            token_path=str(self.token_path),
        )

    def get_quote(self, symbol: str) -> dict:
        """Retrieve the current quote for a symbol."""

        symbol = symbol.upper().strip()

        response = self.client.get_quote(symbol)
        response.raise_for_status()

        return response.json()

    def get_daily_price_history(self, symbol: str) -> pd.DataFrame:
        """Retrieve daily candles and return them as a DataFrame."""

        symbol = symbol.upper().strip()

        response = self.client.get_price_history_every_day(symbol)
        response.raise_for_status()

        payload = response.json()
        candles = payload.get("candles", [])

        if not candles:
            raise ValueError(f"No price-history data returned for {symbol}.")

        prices = pd.DataFrame(candles)

        required_columns = {
            "datetime",
            "open",
            "high",
            "low",
            "close",
            "volume",
        }

        missing_columns = required_columns - set(prices.columns)

        if missing_columns:
            raise ValueError(
                f"Price-history response is missing: {missing_columns}"
            )

        prices["date"] = pd.to_datetime(
            prices["datetime"],
            unit="ms",
        )

        prices = prices[
            [
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

        return prices.sort_values("date").reset_index(drop=True)

    def get_put_option_chain(
        self,
        symbol: str,
        from_date: date | None = None,
        to_date: date | None = None,
        strike_count: int = 30,
    ) -> dict:
        """Retrieve put option contracts for an underlying symbol."""

        symbol = symbol.upper().strip()

        response = self.client.get_option_chain(
            symbol,
            contract_type=self.client.Options.ContractType.PUT,
            strike_count=strike_count,
            include_underlying_quote=True,
            from_date=from_date,
            to_date=to_date,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") == "FAILED":
            raise ValueError(
                f"Option-chain request failed for {symbol}: "
                f"{payload.get('error', 'Unknown error')}"
            )

        return payload