from datetime import date

from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract


def create_contract(
    option_type: str,
    strike: float,
    expiration: date,
) -> OptionContract:
    return OptionContract(
        symbol=f"SPY-{strike}",
        expiration_date=expiration,
        strike=strike,
        option_type=option_type,
        bid=1.0,
        ask=1.1,
        last=1.05,
        delta=-0.20 if option_type == "PUT" else 0.20,
        volume=100,
        open_interest=1000,
        days_to_expiration=30,
    )


def test_option_chain_contract_count():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700.0,
        contracts=[
            create_contract("PUT", 690, date(2026, 9, 18)),
            create_contract("CALL", 710, date(2026, 9, 18)),
        ],
    )

    assert chain.contract_count() == 2


def test_option_chain_puts():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700.0,
        contracts=[
            create_contract("PUT", 690, date(2026, 9, 18)),
            create_contract("PUT", 680, date(2026, 9, 18)),
            create_contract("CALL", 710, date(2026, 9, 18)),
        ],
    )

    puts = chain.puts()

    assert len(puts) == 2
    assert all(contract.option_type == "PUT" for contract in puts)


def test_option_chain_calls():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700.0,
        contracts=[
            create_contract("PUT", 690, date(2026, 9, 18)),
            create_contract("CALL", 710, date(2026, 9, 18)),
            create_contract("CALL", 720, date(2026, 9, 18)),
        ],
    )

    calls = chain.calls()

    assert len(calls) == 2
    assert all(contract.option_type == "CALL" for contract in calls)


def test_option_chain_expirations():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700.0,
        contracts=[
            create_contract("PUT", 690, date(2026, 8, 21)),
            create_contract("CALL", 710, date(2026, 9, 18)),
            create_contract("PUT", 680, date(2026, 8, 21)),
        ],
    )

    expirations = chain.expirations()

    assert expirations == [
        date(2026, 8, 21),
        date(2026, 9, 18),
    ]