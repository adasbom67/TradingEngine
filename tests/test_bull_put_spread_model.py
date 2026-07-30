from datetime import date

from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread

import pytest

def make_contract(strike, bid, ask):

    return OptionContract(
        symbol="SPY",
        expiration_date=date(2026, 9, 18),
        strike=strike,
        option_type="PUT",
        bid=bid,
        ask=ask,
        last=bid,
        delta=-0.20,
        volume=500,
        open_interest=1000,
        days_to_expiration=35,
    )


def test_bull_put_spread_metrics():

    short_put = make_contract(
        strike=680,
        bid=1.80,
        ask=1.90,
    )

    long_put = make_contract(
        strike=675,
        bid=1.10,
        ask=1.20,
    )

    spread = BullPutSpread(
        short_put=short_put,
        long_put=long_put,
    )


    assert spread.width == 5

    assert spread.credit == pytest.approx(0.60)

    assert spread.max_profit == pytest.approx(60.0)

    assert spread.max_loss == pytest.approx(440.0)