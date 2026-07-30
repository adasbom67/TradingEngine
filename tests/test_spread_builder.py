from datetime import date

import pytest

from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_contract import OptionContract
from app.options.spread_builder import SpreadBuilder


def make_put(
    *,
    strike: float,
    bid: float,
    ask: float,
    expiration_date: date = date(2026, 9, 18),
    option_type: str = "PUT",
) -> OptionContract:
    return OptionContract(
        symbol=f"SPY-{expiration_date}-{strike}-{option_type}",
        expiration_date=expiration_date,
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        delta=-0.20,
        volume=500,
        open_interest=1000,
        days_to_expiration=35,
    )


def test_builds_five_dollar_wide_spreads():
    config = PutSpreadConfig(
        allowed_spread_widths=(5.0,),
    )
    builder = SpreadBuilder(config)

    puts = [
        make_put(strike=680, bid=1.80, ask=1.90),
        make_put(strike=675, bid=1.10, ask=1.20),
        make_put(strike=670, bid=0.60, ask=0.70),
    ]

    spreads = builder.build_spreads(puts)

    assert len(spreads) == 2

    assert spreads[0].short_put.strike == 680
    assert spreads[0].long_put.strike == 675
    assert spreads[0].width == pytest.approx(5.0)

    assert spreads[1].short_put.strike == 675
    assert spreads[1].long_put.strike == 670
    assert spreads[1].width == pytest.approx(5.0)


def test_builds_multiple_configured_widths():
    config = PutSpreadConfig(
        allowed_spread_widths=(5.0, 10.0),
    )
    builder = SpreadBuilder(config)

    puts = [
        make_put(strike=680, bid=2.00, ask=2.10),
        make_put(strike=675, bid=1.20, ask=1.30),
        make_put(strike=670, bid=0.50, ask=0.60),
    ]

    spreads = builder.build_spreads(puts)

    strike_pairs = {
        (
            spread.short_put.strike,
            spread.long_put.strike,
        )
        for spread in spreads
    }

    assert strike_pairs == {
        (680, 675),
        (680, 670),
        (675, 670),
    }


def test_does_not_build_unconfigured_width():
    config = PutSpreadConfig(
        allowed_spread_widths=(5.0,),
    )
    builder = SpreadBuilder(config)

    puts = [
        make_put(strike=680, bid=2.00, ask=2.10),
        make_put(strike=670, bid=0.50, ask=0.60),
    ]

    spreads = builder.build_spreads(puts)

    assert spreads == []


def test_requires_matching_expiration_dates():
    config = PutSpreadConfig(
        allowed_spread_widths=(5.0,),
    )
    builder = SpreadBuilder(config)

    puts = [
        make_put(
            strike=680,
            bid=1.80,
            ask=1.90,
            expiration_date=date(2026, 9, 18),
        ),
        make_put(
            strike=675,
            bid=1.10,
            ask=1.20,
            expiration_date=date(2026, 9, 25),
        ),
    ]

    spreads = builder.build_spreads(puts)

    assert spreads == []


def test_ignores_call_contracts():
    config = PutSpreadConfig(
        allowed_spread_widths=(5.0,),
    )
    builder = SpreadBuilder(config)

    contracts = [
        make_put(
            strike=680,
            bid=1.80,
            ask=1.90,
            option_type="PUT",
        ),
        make_put(
            strike=675,
            bid=1.10,
            ask=1.20,
            option_type="CALL",
        ),
    ]

    spreads = builder.build_spreads(contracts)

    assert spreads == []


def test_rejects_non_positive_credit_spread():
    config = PutSpreadConfig(
        allowed_spread_widths=(5.0,),
    )
    builder = SpreadBuilder(config)

    puts = [
        make_put(
            strike=680,
            bid=1.00,
            ask=1.10,
        ),
        make_put(
            strike=675,
            bid=1.10,
            ask=1.20,
        ),
    ]

    spreads = builder.build_spreads(puts)

    assert spreads == []


def test_empty_contract_list_returns_empty_list():
    config = PutSpreadConfig()
    builder = SpreadBuilder(config)

    spreads = builder.build_spreads([])

    assert spreads == []