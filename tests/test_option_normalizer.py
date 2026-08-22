from datetime import date, datetime, timezone

import pytest

from app.brokers.schwab.option_normalizer import (
    normalize_schwab_option,
)


def test_normalize_schwab_option() -> None:
    """Verify that one Schwab contract is normalized correctly."""

    raw_contract = {
        "symbol": "SPY  260918P00700000",
        "putCall": "PUT",
        "strikePrice": 700.0,
        "expirationDate": "2026-09-18T20:00:00.000+00:00",
        "bid": 2.10,
        "ask": 2.18,
        "last": 2.14,
        "delta": -0.20,
        "totalVolume": 325,
        "openInterest": 2450,
        "daysToExpiration": 50,
        "volatility": 18.75,
        "quoteTimeInLong": 1789761600000,
    }

    contract = normalize_schwab_option(raw_contract)

    assert contract.symbol == "SPY  260918P00700000"
    assert contract.expiration_date == date(2026, 9, 18)
    assert contract.strike == 700.0
    assert contract.option_type == "PUT"
    assert contract.bid == 2.10
    assert contract.ask == 2.18
    assert contract.last == 2.14
    assert contract.delta == -0.20
    assert contract.volume == 325
    assert contract.open_interest == 2450
    assert contract.days_to_expiration == 50
    assert contract.implied_volatility == 18.75
    assert contract.quote_time == datetime.fromtimestamp(1789761600, tz=timezone.utc)


def test_normalizer_handles_missing_optional_values() -> None:
    """Verify that optional missing values receive safe defaults."""

    raw_contract = {
        "symbol": "SPY  260918P00700000",
        "putCall": "PUT",
        "strikePrice": 700.0,
        "expirationDate": "2026-09-18",
    }

    contract = normalize_schwab_option(raw_contract)

    assert contract.bid == 0.0
    assert contract.ask == 0.0
    assert contract.last == 0.0
    assert contract.delta is None
    assert contract.volume == 0
    assert contract.open_interest == 0
    assert contract.days_to_expiration == 0
    assert contract.implied_volatility is None
    assert contract.quote_time is None


def test_normalizer_rejects_missing_required_field() -> None:
    """Verify that missing essential data raises a clear error."""

    raw_contract = {
        "symbol": "SPY  260918P00700000",
        "putCall": "PUT",
        "expirationDate": "2026-09-18",
    }

    with pytest.raises(
        ValueError,
        match="strikePrice",
    ):
        normalize_schwab_option(raw_contract)
