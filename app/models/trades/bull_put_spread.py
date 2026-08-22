from dataclasses import dataclass

from app.models.market.option_contract import OptionContract


@dataclass
class BullPutSpread:
    """
    Represents a complete bull put credit spread.
    """

    short_put: OptionContract
    long_put: OptionContract

    strategy_type = "BULL_PUT"
    strategy_name = "Bull Put Credit Spread"
    option_type = "PUT"
    direction = "BULLISH"

    @property
    def short_leg(self) -> OptionContract:
        return self.short_put

    @property
    def long_leg(self) -> OptionContract:
        return self.long_put

    @property
    def width(self) -> float:
        """Width of the spread."""

        return self.short_put.strike - self.long_put.strike

    @property
    def credit(self) -> float:
        """
        Estimated credit received.

        Uses natural prices for now.
        """

        return self.short_put.bid - self.long_put.ask

    @property
    def max_profit(self) -> float:
        """
        Maximum possible profit.
        """

        return self.credit * 100

    @property
    def max_loss(self) -> float:
        """
        Maximum possible loss.
        """

        return (self.width - self.credit) * 100

    @property
    def risk_reward_ratio(self) -> float:
        """
        Return reward / risk.
        """

        if self.max_loss == 0:
            return 0

        return self.max_profit / self.max_loss

    @property
    def return_on_risk(self) -> float:
        """Return maximum profit divided by maximum loss."""
        if self.max_loss <= 0:
            return 0.0
        return self.max_profit / self.max_loss

    @property
    def breakeven(self) -> float:
        """Expiration breakeven price for the short put spread."""
        return self.short_put.strike - self.credit

