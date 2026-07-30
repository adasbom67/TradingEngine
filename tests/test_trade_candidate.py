from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate


def create_option(strike: float) -> OptionContract:
    return OptionContract(
        symbol=f"SPY240920P{int(strike * 1000):08d}",
        expiration_date="2024-09-20",
        strike=strike,
        option_type="PUT",
        bid=1.50,
        ask=1.60,
        last=1.55,
        delta=-0.20,
        volume=100,
        open_interest=500,
        days_to_expiration=45,
    )


def test_trade_candidate_defaults():
    short_put = create_option(500)
    long_put = create_option(495)

    spread = BullPutSpread(
        short_put=short_put,
        long_put=long_put,
    )

    candidate = TradeCandidate(spread=spread)

    assert candidate.spread == spread
    assert candidate.score == 0.0
    assert candidate.rank == 0
    assert candidate.reasons == []
    assert candidate.warnings == []