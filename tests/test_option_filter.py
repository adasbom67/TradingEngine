from datetime import date

from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract
from app.options.option_filter import OptionFilter


def make_contract(
    *,
    option_type: str = "PUT",
    dte: int = 35,
    delta: float | None = -0.20,
    bid: float = 0.60,
    ask: float = 0.70,
    volume: int = 50,
    open_interest: int = 500,
) -> OptionContract:
    """
    Create an option contract with valid default values.

    Individual tests override only the field being tested.
    """

    return OptionContract(
        symbol="SPY  260904P00650000",
        expiration_date=date(2026, 9, 4),
        strike=650.0,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=0.65,
        delta=delta,
        volume=volume,
        open_interest=open_interest,
        days_to_expiration=dte,
    )


def make_chain(
    contracts: list[OptionContract],
) -> OptionChain:
    """Create a test option chain."""

    return OptionChain(
        underlying_symbol="SPY",
        underlying_price=700.0,
        contracts=contracts,
    )


def test_filter_returns_valid_put():
    config = PutSpreadConfig()
    option_filter = OptionFilter(config)

    valid_put = make_contract()
    chain = make_chain([valid_put])

    results = option_filter.filter_puts(chain)

    assert results == [valid_put]


def test_filter_ignores_calls():
    config = PutSpreadConfig()
    option_filter = OptionFilter(config)

    call = make_contract(option_type="CALL")
    chain = make_chain([call])

    results = option_filter.filter_puts(chain)

    assert results == []


def test_filter_accepts_negative_put_delta():
    config = PutSpreadConfig()
    option_filter = OptionFilter(config)

    put = make_contract(delta=-0.20)
    chain = make_chain([put])

    results = option_filter.filter_puts(chain)

    assert results == [put]


def test_filter_rejects_contract_outside_dte_range():
    config = PutSpreadConfig()
    option_filter = OptionFilter(config)

    short_dated_put = make_contract(dte=20)
    chain = make_chain([short_dated_put])

    results = option_filter.filter_puts(chain)

    assert results == []


def test_filter_rejects_missing_delta():
    config = PutSpreadConfig()
    option_filter = OptionFilter(config)

    put = make_contract(delta=None)
    chain = make_chain([put])

    results = option_filter.filter_puts(chain)

    assert results == []


def test_filter_rejects_insufficient_liquidity():
    config = PutSpreadConfig()
    option_filter = OptionFilter(config)

    low_liquidity_put = make_contract(
        volume=5,
        open_interest=50,
    )
    chain = make_chain([low_liquidity_put])

    results = option_filter.filter_puts(chain)

    assert results == []


def test_filter_rejects_wide_bid_ask_spread():
    config = PutSpreadConfig()
    option_filter = OptionFilter(config)

    wide_spread_put = make_contract(
        bid=0.50,
        ask=0.80,
    )
    chain = make_chain([wide_spread_put])

    results = option_filter.filter_puts(chain)

    assert results == []