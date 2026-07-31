from app.models.market.option_contract import OptionContract
from app.models.market.option_chain import OptionChain
from app.models.market.price_snapshot import PriceSnapshot


def create_option(
    strike: float,
    option_type: str = "PUT",
    bid: float = 1.50,
    ask: float = 1.60,
    delta: float = -0.20,
    volume: int = 100,
    open_interest: int = 500,
    days_to_expiration: int = 45,
) -> OptionContract:
    """
    Create a reusable OptionContract for unit tests.
    """

    return OptionContract(
        symbol=f"SPY240920{option_type[0]}{int(strike * 1000):08d}",
        expiration_date="2024-09-20",
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        delta=delta,
        volume=volume,
        open_interest=open_interest,
        days_to_expiration=days_to_expiration,
    )


def create_price_snapshot() -> PriceSnapshot:
    """
    Create a reusable PriceSnapshot for unit tests.
    """

    return PriceSnapshot(
        symbol="SPY",
        current_price=605.00,
        sma20=600.00,
        sma200=575.00,
        rsi=55.0,
        atr=8.5,
    )


def create_option_chain() -> OptionChain:
    """
    Create an empty OptionChain for unit tests.
    """

    return OptionChain(
        underlying_symbol="SPY",
        underlying_price=605.00,
        contracts=[],
    )