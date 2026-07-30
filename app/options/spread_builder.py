from math import isclose

from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread


class SpreadBuilder:
    """
    Builds valid bull put spreads from eligible put contracts.

    The builder constructs spreads only. It does not rank them,
    size positions, or decide whether a trade should be executed.
    """

    def __init__(self, config: PutSpreadConfig) -> None:
        self.config = config

    def build_spreads(
        self,
        eligible_puts: list[OptionContract],
    ) -> list[BullPutSpread]:
        """
        Build every valid bull put spread using the configured widths.
        """

        puts = [
            contract
            for contract in eligible_puts
            if contract.option_type.upper() == "PUT"
        ]

        spreads: list[BullPutSpread] = []

        for short_put in puts:
            matching_long_puts = self._find_matching_long_puts(
                short_put=short_put,
                puts=puts,
            )

            for long_put in matching_long_puts:
                spread = BullPutSpread(
                    short_put=short_put,
                    long_put=long_put,
                )

                if self._is_valid_spread(spread):
                    spreads.append(spread)

        return self._sort_spreads(spreads)

    def _find_matching_long_puts(
        self,
        short_put: OptionContract,
        puts: list[OptionContract],
    ) -> list[OptionContract]:
        """
        Find lower-strike puts with the same expiration and an allowed width.
        """

        matching_puts: list[OptionContract] = []

        for long_put in puts:
            if long_put is short_put:
                continue

            if long_put.expiration_date != short_put.expiration_date:
                continue

            if long_put.strike >= short_put.strike:
                continue

            width = short_put.strike - long_put.strike

            if self._is_allowed_width(width):
                matching_puts.append(long_put)

        return matching_puts

    def _is_allowed_width(self, width: float) -> bool:
        """
        Return True when width matches one of the configured widths.

        isclose() protects against small floating-point differences.
        """

        return any(
            isclose(
                width,
                allowed_width,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
            for allowed_width in self.config.allowed_spread_widths
        )

    def _is_valid_spread(self, spread: BullPutSpread) -> bool:
        """
        Validate the completed spread.

        A valid bull put spread must:
        - contain two puts;
        - have matching expirations;
        - have a lower long strike;
        - have positive width;
        - produce a positive credit;
        - have credit smaller than spread width.
        """

        short_put = spread.short_put
        long_put = spread.long_put

        if short_put.option_type.upper() != "PUT":
            return False

        if long_put.option_type.upper() != "PUT":
            return False

        if short_put.expiration_date != long_put.expiration_date:
            return False

        if long_put.strike >= short_put.strike:
            return False

        if spread.width <= 0:
            return False

        if spread.credit <= 0:
            return False

        if spread.credit >= spread.width:
            return False

        return True

    def _sort_spreads(
        self,
        spreads: list[BullPutSpread],
    ) -> list[BullPutSpread]:
        """
        Return spreads in a predictable order.

        Higher short strikes appear first. For the same short strike,
        narrower spreads appear first.
        """

        return sorted(
            spreads,
            key=lambda spread: (
                -spread.short_put.strike,
                spread.width,
            ),
        )