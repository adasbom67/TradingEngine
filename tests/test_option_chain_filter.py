from datetime import date

from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_chain import OptionChain
from app.selection.option_chain_filter import OptionChainFilter
from tests.helpers import create_option


def test_filters_puts_by_all_configured_rules():
    valid = create_option(500)
    wrong_type = create_option(500, option_type="CALL")
    bad_delta = create_option(499, delta=-0.40)
    no_delta = create_option(498, delta=None)
    bad_dte = create_option(497, days_to_expiration=10)
    low_bid = create_option(496, bid=0.10, ask=0.15)
    low_oi = create_option(495, open_interest=99)
    low_volume = create_option(494, volume=9)
    wide_market = create_option(493, bid=1.00, ask=1.30)

    chain = OptionChain("SPY", 605.0, [
        valid, wrong_type, bad_delta, no_delta, bad_dte,
        low_bid, low_oi, low_volume, wide_market,
    ])

    result = OptionChainFilter().filter_puts(chain, PutSpreadConfig())

    assert result == [valid]


def test_returns_deterministic_expiration_and_strike_order():
    later_low = create_option(495)
    later_high = create_option(500)
    earlier = create_option(490)
    earlier.expiration_date = date(2024, 9, 13)

    chain = OptionChain("SPY", 605.0, [later_low, earlier, later_high])

    result = OptionChainFilter().filter_puts(chain, PutSpreadConfig())

    assert result == [earlier, later_high, later_low]
