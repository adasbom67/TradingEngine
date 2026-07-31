from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract


class OptionChainFilter:
    """Select liquid put contracts that satisfy strategy constraints."""

    def filter_puts(
        self,
        chain: OptionChain,
        config: PutSpreadConfig,
    ) -> list[OptionContract]:
        config.validate()

        eligible = [
            contract
            for contract in chain.puts()
            if self._is_eligible(contract, config)
        ]

        return sorted(
            eligible,
            key=lambda contract: (
                str(contract.expiration_date),
                -contract.strike,
                contract.symbol,
            ),
        )

        
    @staticmethod
    def _is_eligible(
        contract: OptionContract,
        config: PutSpreadConfig,
    ) -> bool:
        if not config.minimum_dte <= contract.days_to_expiration <= config.maximum_dte:
            return False

        if contract.delta is None:
            return False

        absolute_delta = abs(contract.delta)
        if not config.minimum_delta <= absolute_delta <= config.maximum_delta:
            return False

        if contract.bid < config.minimum_bid:
            return False

        if contract.open_interest < config.minimum_open_interest:
            return False

        if contract.volume < config.minimum_volume:
            return False

        if contract.ask < contract.bid:
            return False

        if contract.ask - contract.bid > config.maximum_bid_ask_spread:
            return False

        return True
