from app.models.market.price_snapshot import PriceSnapshot


def test_bullish_snapshot():
    snapshot = PriceSnapshot(
        symbol="SPY",
        current_price=700,
        sma20=695,
        sma200=680,
    )

    assert snapshot.is_above_20_sma()
    assert snapshot.is_above_200_sma()
    assert snapshot.is_20_above_200()
    assert not snapshot.is_pullback_to_20()


def test_pullback_snapshot():
    snapshot = PriceSnapshot(
        symbol="SPY",
        current_price=690,
        sma20=695,
        sma200=680,
    )

    assert not snapshot.is_above_20_sma()
    assert snapshot.is_above_200_sma()
    assert snapshot.is_20_above_200()
    assert snapshot.is_pullback_to_20()


def test_bearish_snapshot():
    snapshot = PriceSnapshot(
        symbol="SPY",
        current_price=650,
        sma20=660,
        sma200=680,
    )

    assert not snapshot.is_above_20_sma()
    assert not snapshot.is_above_200_sma()
    assert not snapshot.is_20_above_200()