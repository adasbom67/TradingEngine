import pytest

from app.models.market.option_chain import OptionChain
from app.strategies.base_strategy import BaseStrategy


def test_base_strategy_cannot_be_created_directly() -> None:
    """Verify that the abstract strategy cannot be instantiated."""

    with pytest.raises(TypeError):
        BaseStrategy(
            name="Test Strategy",
            description="Used only for testing.",
        )


def test_incomplete_strategy_cannot_be_created() -> None:
    """Verify that subclasses must implement every abstract method."""

    class IncompleteStrategy(BaseStrategy):
        def validate(self) -> None:
            pass

    with pytest.raises(TypeError):
        IncompleteStrategy(
            name="Incomplete Strategy",
            description="Missing required methods.",
        )


def test_complete_strategy_can_be_created() -> None:
    """Verify that a complete strategy implementation can be instantiated."""

    class CompleteStrategy(BaseStrategy):
        def validate(self) -> None:
            pass

        def analyze(
            self,
            option_chain: OptionChain,
        ) -> dict[str, object]:
            return {
                "underlying_symbol": option_chain.underlying_symbol,
            }

        def generate_candidates(
            self,
            option_chain: OptionChain,
        ) -> list[object]:
            return []

    strategy = CompleteStrategy(
        name="Complete Strategy",
        description="Implements the full strategy contract.",
    )

    assert strategy.name == "Complete Strategy"
    assert strategy.description == (
        "Implements the full strategy contract."
    )