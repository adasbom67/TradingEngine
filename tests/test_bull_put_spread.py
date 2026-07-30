from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_chain import OptionChain
from app.strategies.bull_put_spread import BullPutSpreadStrategy
from app.models.market.price_snapshot import PriceSnapshot


def test_bull_put_spread_strategy_creation() -> None:
    """Verify that the bull put spread strategy can be created."""

    config = PutSpreadConfig()

    strategy = BullPutSpreadStrategy(config)

    assert strategy.name == "Bull Put Spread"
    assert strategy.config is config


def test_bull_put_spread_analyze() -> None:
    """Verify that the strategy analyzes a bullish price snapshot."""

    config = PutSpreadConfig()
    strategy = BullPutSpreadStrategy(config)

    snapshot = PriceSnapshot(
        symbol="SPY",
        current_price=700.0,
        sma20=695.0,
        sma200=680.0,
    )

    result = strategy.analyze(snapshot)

    assert result.passed
    assert result.score == 80


def test_bull_put_spread_generates_empty_candidate_list() -> None:
    """Verify the temporary candidate-generation behavior."""

    config = PutSpreadConfig()
    strategy = BullPutSpreadStrategy(config)

    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700.0,
        contracts=[],
    )

    candidates = strategy.generate_candidates(chain)

    assert candidates == []