from app.config.strategy_config import PutSpreadConfig
from app.indicators.market_regime import MarketRegimeClassifier
from app.models.market.market_regime import MarketRegimeType
from app.models.market.price_snapshot import PriceSnapshot


def test_classifies_bullish_regime():
    snapshot = PriceSnapshot("SPY", 110, 105, 100, atr=2)
    regime = MarketRegimeClassifier().classify(snapshot, PutSpreadConfig())
    assert regime.regime == MarketRegimeType.BULLISH


def test_classifies_high_volatility_before_trend():
    snapshot = PriceSnapshot("SPY", 110, 105, 100, atr=5)
    regime = MarketRegimeClassifier().classify(snapshot, PutSpreadConfig())
    assert regime.regime == MarketRegimeType.HIGH_VOLATILITY
