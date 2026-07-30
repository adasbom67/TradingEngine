from dataclasses import dataclass


@dataclass
class PriceSnapshot:
    """
    Represents the current technical state of an underlying security.
    """

    symbol: str

    current_price: float

    sma20: float
    sma200: float

    rsi: float | None = None
    atr: float | None = None

    def is_above_20_sma(self) -> bool:
        """Return True if price is above the 20-day SMA."""
        return self.current_price > self.sma20

    def is_above_200_sma(self) -> bool:
        """Return True if price is above the 200-day SMA."""
        return self.current_price > self.sma200

    def is_20_above_200(self) -> bool:
        """Return True if the 20-day SMA is above the 200-day SMA."""
        return self.sma20 > self.sma200

    def is_pullback_to_20(self) -> bool:
        """
        Return True if price is below the 20-day SMA.

        This is useful for strategies that prefer entering
        on a pullback within an overall uptrend.
        """
        return self.current_price < self.sma20