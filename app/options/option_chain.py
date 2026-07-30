from datetime import date, datetime, timedelta

import pandas as pd

from app.brokers.schwab_client import SchwabClient


def flatten_put_chain(option_chain: dict) -> pd.DataFrame:
    """
    Convert Schwab's nested put option-chain response
    into one row per option contract.
    """

    put_map = option_chain.get("putExpDateMap", {})
    contracts = []

    for expiration_key, strike_map in put_map.items():
        expiration_text = expiration_key.split(":")[0]
        expiration_date = datetime.strptime(
            expiration_text,
            "%Y-%m-%d",
        ).date()

        for strike_text, option_list in strike_map.items():
            for option in option_list:
                bid = float(option.get("bid", 0) or 0)
                ask = float(option.get("ask", 0) or 0)

                midpoint = (
                    (bid + ask) / 2
                    if bid > 0 and ask > 0
                    else 0
                )

                contracts.append(
                    {
                        "symbol": option.get("symbol"),
                        "expiration_date": expiration_date,
                        "days_to_expiration": option.get(
                            "daysToExpiration"
                        ),
                        "strike": float(
                            option.get("strikePrice", strike_text)
                        ),
                        "bid": bid,
                        "ask": ask,
                        "midpoint": midpoint,
                        "mark": float(
                            option.get("mark", midpoint) or midpoint
                        ),
                        "delta": float(
                            option.get("delta", 0) or 0
                        ),
                        "volume": int(
                            option.get("totalVolume", 0) or 0
                        ),
                        "open_interest": int(
                            option.get("openInterest", 0) or 0
                        ),
                        "in_the_money": bool(
                            option.get("inTheMoney", False)
                        ),
                    }
                )

    return pd.DataFrame(contracts)


def get_put_candidates(
    client: SchwabClient,
    symbol: str,
    minimum_dte: int = 25,
    maximum_dte: int = 50,
    minimum_open_interest: int = 100,
    minimum_volume: int = 10,
) -> pd.DataFrame:
    """Retrieve and filter put contracts for analysis."""

    today = date.today()

    option_chain = client.get_put_option_chain(
        symbol=symbol,
        from_date=today + timedelta(days=minimum_dte),
        to_date=today + timedelta(days=maximum_dte),
        strike_count=40,
    )

    contracts = flatten_put_chain(option_chain)

    if contracts.empty:
        return contracts

    underlying_price = float(
        option_chain.get("underlyingPrice", 0) or 0
    )

    if underlying_price <= 0:
        underlying = option_chain.get("underlying", {})
        underlying_price = float(
            underlying.get("mark", 0)
            or underlying.get("last", 0)
            or 0
        )

    contracts["underlying_price"] = underlying_price

    contracts["distance_otm_pct"] = (
        (underlying_price - contracts["strike"])
        / underlying_price
        * 100
    )

    candidates = contracts[
        (contracts["strike"] < underlying_price)
        & (contracts["bid"] > 0)
        & (contracts["ask"] > 0)
        & (
            contracts["open_interest"]
            >= minimum_open_interest
        )
        & (contracts["volume"] >= minimum_volume)
    ].copy()

    return candidates.sort_values(
        by=["expiration_date", "strike"],
        ascending=[True, False],
    ).reset_index(drop=True)