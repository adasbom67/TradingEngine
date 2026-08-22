from dataclasses import dataclass

from app.models.market.option_contract import OptionContract


@dataclass
class BearCallSpread:
    """A risk-defined bear call credit spread."""

    short_call: OptionContract
    long_call: OptionContract

    strategy_type = "BEAR_CALL"
    strategy_name = "Bear Call Credit Spread"
    option_type = "CALL"
    direction = "BEARISH"

    @property
    def short_leg(self) -> OptionContract:
        return self.short_call

    @property
    def long_leg(self) -> OptionContract:
        return self.long_call

    @property
    def width(self) -> float:
        return self.long_call.strike - self.short_call.strike

    @property
    def credit(self) -> float:
        return self.short_call.bid - self.long_call.ask

    @property
    def max_profit(self) -> float:
        return self.credit * 100

    @property
    def max_loss(self) -> float:
        return (self.width - self.credit) * 100

    @property
    def risk_reward_ratio(self) -> float:
        return 0.0 if self.max_loss <= 0 else self.max_profit / self.max_loss

    @property
    def return_on_risk(self) -> float:
        return self.risk_reward_ratio

    @property
    def breakeven(self) -> float:
        return self.short_call.strike + self.credit
