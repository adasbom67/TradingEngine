from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract


class OptionFilter:
    """
    Filters option contracts according to bull put spread
    selection requirements.
    """

    def __init__(self, config: PutSpreadConfig) -> None:
        self.config = config

    def filter_puts(
        self,
        option_chain: OptionChain,
    ) -> list[OptionContract]:
        """
        Return put contracts that satisfy every configured rule.
        """

        return [
            contract
            for contract in option_chain.puts()
            if self._passes_all_rules(contract)
        ]

    def _passes_all_rules(self, contract: OptionContract) -> bool:
        """Return True when a contract passes every filter rule."""

        return (
            self._passes_dte(contract)
            and self._passes_delta(contract)
            and self._passes_bid(contract)
            and self._passes_open_interest(contract)
            and self._passes_volume(contract)
            and self._passes_bid_ask_spread(contract)
        )

    def _passes_dte(self, contract: OptionContract) -> bool:
        """Check whether DTE is within the configured range."""

        return (
            self.config.minimum_dte
            <= contract.days_to_expiration
            <= self.config.maximum_dte
        )

    def _passes_delta(self, contract: OptionContract) -> bool:
        """
        Check whether the absolute delta is within the configured range.

        Put deltas are commonly negative, so their absolute value is used.
        """

        if contract.delta is None:
            return False

        absolute_delta = abs(contract.delta)

        return (
            self.config.minimum_delta
            <= absolute_delta
            <= self.config.maximum_delta
        )

    def _passes_bid(self, contract: OptionContract) -> bool:
        """Check whether the bid meets the minimum requirement."""

        return contract.bid >= self.config.minimum_bid

    def _passes_open_interest(
        self,
        contract: OptionContract,
    ) -> bool:
        """Check whether open interest meets the minimum requirement."""

        return (
            contract.open_interest
            >= self.config.minimum_open_interest
        )

    def _passes_volume(self, contract: OptionContract) -> bool:
        """Check whether volume meets the minimum requirement."""

        return contract.volume >= self.config.minimum_volume

    def _passes_bid_ask_spread(
        self,
        contract: OptionContract,
    ) -> bool:
        """Check whether the bid-ask spread is acceptable."""

        if contract.ask < contract.bid:
            return False

        spread = contract.ask - contract.bid

        return spread <= self.config.maximum_bid_ask_spread