from abc import ABC, abstractmethod
from typing import Any

from app.models.market.option_chain import OptionChain


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    Every strategy must provide validation, analysis,
    and candidate-generation behavior.
    """

    def __init__(self, name: str, description: str) -> None:
        """
        Initialize the strategy.

        Args:
            name: Human-readable strategy name.
            description: Short explanation of the strategy.
        """
        self.name = name
        self.description = description

    @abstractmethod
    def validate(self) -> None:
        """
        Validate the strategy's configuration.

        Raises:
            ValueError: If the strategy configuration is invalid.
        """
        raise NotImplementedError

    @abstractmethod
    def analyze(self, option_chain: OptionChain) -> dict[str, Any]:
        """
        Analyze market data for this strategy.

        Args:
            option_chain: Normalized option-chain data.

        Returns:
            A dictionary containing analysis results.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_candidates(
        self,
        option_chain: OptionChain,
    ) -> list[Any]:
        """
        Generate possible trades from an option chain.

        Args:
            option_chain: Normalized option-chain data.

        Returns:
            A list of strategy-specific trade candidates.
        """
        raise NotImplementedError