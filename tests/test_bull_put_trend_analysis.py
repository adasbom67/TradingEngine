from app.config.strategy_config import PutSpreadConfig
from app.models.market.price_snapshot import PriceSnapshot
from app.strategies.bull_put_spread import BullPutSpreadStrategy


def test_perfect_bullish_trend():

    strategy = BullPutSpreadStrategy(PutSpreadConfig())

    snapshot = PriceSnapshot(
        symbol="SPY",
        current_price=700,
        sma20=695,
        sma200=680,
    )

    result = strategy.analyze(snapshot)

    assert result.passed
    assert result.score == 80

def test_price_below_200():

    strategy = BullPutSpreadStrategy(PutSpreadConfig())

    snapshot = PriceSnapshot(
        symbol="SPY",
        current_price=670,
        sma20=690,
        sma200=680,
    )

    result = strategy.analyze(snapshot)

    assert not result.passed

def test_pullback_required():

    config = PutSpreadConfig(
        require_price_below_20_sma=True
    )

    strategy = BullPutSpreadStrategy(config)

    snapshot = PriceSnapshot(
        symbol="SPY",
        current_price=690,
        sma20=695,
        sma200=680,
    )

    result = strategy.analyze(snapshot)

    assert result.passed
    assert result.score == 100