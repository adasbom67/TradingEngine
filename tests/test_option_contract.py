from datetime import date

from app.models.market.option_contract import OptionContract


def test_option_contract_creation():
    """Verify that an OptionContract is created correctly."""

    contract = OptionContract(
        symbol="SPY",
        expiration_date=date(2026, 9, 18),
        strike=700.0,
        option_type="PUT",
        bid=2.10,
        ask=2.18,
        last=2.14,
        delta=-0.20,
        volume=325,
        open_interest=2450,
        days_to_expiration=50,
    )

    assert contract.symbol == "SPY"
    assert contract.strike == 700.0
    assert contract.option_type == "PUT"
    assert contract.bid == 2.10
    assert contract.ask == 2.18
    assert contract.delta == -0.20
    assert contract.volume == 325
    assert contract.open_interest == 2450
    assert contract.days_to_expiration == 50