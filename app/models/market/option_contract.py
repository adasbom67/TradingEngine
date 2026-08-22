from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class OptionContract:
    """
    Represents a single option contract in a normalized format.

    All broker-specific data should eventually be converted into this
    model before it is used by strategies.
    """

    symbol: str
    expiration_date: date
    strike: float

    option_type: str      # "PUT" or "CALL"

    bid: float
    ask: float
    last: float

    delta: Optional[float]

    volume: int
    open_interest: int

    days_to_expiration: int

    # Optional market-quality fields supplied by brokers that expose them.
    implied_volatility: Optional[float] = None
    quote_time: Optional[datetime] = None
