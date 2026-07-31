from dataclasses import dataclass


@dataclass
class PutSpreadConfig:
    """
    Configuration settings for selecting and managing
    bullish put credit spreads.
    """

    # Underlying trend rules
    require_price_above_200_sma: bool = True
    require_20_sma_above_200_sma: bool = True
    require_price_below_20_sma: bool = False

    # Trend evaluation weights
    trend_weight_sma_alignment: int = 40
    trend_weight_price_above_200: int = 25
    trend_weight_price_above_20: int = 20
    trend_weight_trend_confirmation: int = 15

    # Option expiration rules
    minimum_dte: int = 30
    maximum_dte: int = 45

    # Short-put selection rules
    minimum_delta: float = 0.15
    maximum_delta: float = 0.25
    minimum_bid: float = 0.20
    minimum_open_interest: int = 100
    minimum_volume: int = 10
    maximum_bid_ask_spread: float = 0.15

    # Spread construction rules
    allowed_spread_widths: tuple[float, ...] = (5.0,)
    minimum_credit: float = 0.50

    # Exit rules
    profit_target_percent: float = 50.0
    stop_loss_percent: float = 200.0
    exit_dte: int = 7

    # Risk-management rules
    maximum_risk_per_trade: float = 500.00
    maximum_open_positions: int = 5

    def validate(self) -> None:
        """
        Validate all configuration values.

        Raises:
            ValueError: If any configuration value is invalid.
        """

        if self.minimum_dte < 0:
            raise ValueError(
                "Minimum DTE cannot be negative."
            )

        if self.maximum_dte < self.minimum_dte:
            raise ValueError(
                "Maximum DTE must be greater than or equal to minimum DTE."
            )

        if not 0 <= self.minimum_delta <= 1:
            raise ValueError(
                "Minimum delta must be between 0 and 1."
            )

        if not 0 <= self.maximum_delta <= 1:
            raise ValueError(
                "Maximum delta must be between 0 and 1."
            )

        if self.maximum_delta < self.minimum_delta:
            raise ValueError(
                "Maximum delta must be greater than or equal to minimum delta."
            )

        if self.minimum_bid < 0:
            raise ValueError(
                "Minimum bid cannot be negative."
            )

        if self.minimum_open_interest < 0:
            raise ValueError(
                "Minimum open interest cannot be negative."
            )

        if self.minimum_volume < 0:
            raise ValueError(
                "Minimum volume cannot be negative."
            )

        if self.maximum_bid_ask_spread < 0:
            raise ValueError(
                "Maximum bid-ask spread cannot be negative."
            )

        if self.minimum_credit < 0:
            raise ValueError(
                "Minimum credit cannot be negative."
            )

        if not 0 < self.profit_target_percent <= 100:
            raise ValueError(
                "Profit target percent must be greater than 0 "
                "and no more than 100."
            )

        if self.stop_loss_percent <= 0:
            raise ValueError(
                "Stop-loss percent must be greater than zero."
            )

        if self.exit_dte < 0:
            raise ValueError(
                "Exit DTE cannot be negative."
            )

        if self.maximum_risk_per_trade <= 0:
            raise ValueError(
                "Maximum risk per trade must be greater than zero."
            )

        if self.maximum_open_positions <= 0:
            raise ValueError(
                "Maximum open positions must be greater than zero."
            )

        if not self.allowed_spread_widths:
            raise ValueError(
                "At least one spread width is required."
            )

        if any(
            width <= 0
            for width in self.allowed_spread_widths
        ):
            raise ValueError(
                "Spread widths must be greater than zero."
            )

        trend_weights = (
            self.trend_weight_sma_alignment,
            self.trend_weight_price_above_200,
            self.trend_weight_price_above_20,
            self.trend_weight_trend_confirmation,
        )

        if any(weight < 0 for weight in trend_weights):
            raise ValueError(
                "Trend evaluation weights cannot be negative."
            )

        if sum(trend_weights) != 100:
            raise ValueError(
                "Trend evaluation weights must total 100."
            )


DEFAULT_STRATEGIES = {
    "Conservative": PutSpreadConfig(
        minimum_delta=0.10,
        maximum_delta=0.15,
        minimum_dte=30,
        maximum_dte=45,
        minimum_credit=0.30,
    ),
    "Balanced": PutSpreadConfig(),
    "Aggressive": PutSpreadConfig(
        minimum_delta=0.25,
        maximum_delta=0.35,
        minimum_dte=30,
        maximum_dte=60,
        minimum_credit=1.00,
    ),
}