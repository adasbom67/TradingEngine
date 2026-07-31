from datetime import date

from app.config.strategy_config import PutSpreadConfig
from app.strategies.bull_put_spread_builder import BullPutSpreadBuilder
from tests.helpers import create_option


def test_builds_only_same_expiration_allowed_width_profitable_spreads():
    short_put = create_option(500, bid=1.50, ask=1.60)
    valid_long = create_option(495, bid=0.70, ask=0.80)
    wrong_width = create_option(494, bid=0.50, ask=0.60)
    other_expiration = create_option(495, bid=0.70, ask=0.80)
    other_expiration.expiration_date = date(2024, 9, 27)

    candidates = BullPutSpreadBuilder().build(
        [short_put, valid_long, wrong_width, other_expiration],
        PutSpreadConfig(minimum_credit=0.50),
    )

    assert len(candidates) == 1
    assert candidates[0].spread.short_put is short_put
    assert candidates[0].spread.long_put is valid_long
    assert candidates[0].spread.credit == 0.70


def test_rejects_spread_above_maximum_risk():
    short_put = create_option(500, bid=0.60, ask=0.70)
    long_put = create_option(495, bid=0.05, ask=0.10)

    candidates = BullPutSpreadBuilder().build(
        [short_put, long_put],
        PutSpreadConfig(minimum_credit=0.50, maximum_risk_per_trade=400),
    )

    assert candidates == []
