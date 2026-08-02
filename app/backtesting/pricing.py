from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, log, sqrt


@dataclass(frozen=True)
class SpreadValuation:
    debit: float
    short_put_value: float
    long_put_value: float
    annualized_volatility: float


class ApproximateSpreadPricer:
    """Black-Scholes based approximation for a vertical put spread.

    This is deliberately isolated from the simulator so it can later be
    replaced by historical option-chain data without changing trade logic.
    """

    def value(
        self,
        underlying_price: float,
        short_strike: float,
        long_strike: float,
        dte: int,
        atr: float,
        risk_free_rate: float = 0.04,
        volatility_floor: float = 0.10,
        volatility_ceiling: float = 0.80,
    ) -> SpreadValuation:
        if underlying_price <= 0:
            raise ValueError("Underlying price must be positive.")
        if not 0 < long_strike < short_strike:
            raise ValueError("Long strike must be positive and below short strike.")
        if dte < 0:
            raise ValueError("DTE cannot be negative.")
        if atr <= 0:
            raise ValueError("ATR must be positive.")

        width = short_strike - long_strike
        volatility = atr / underlying_price * sqrt(252.0)
        volatility = min(max(volatility, volatility_floor), volatility_ceiling)

        if dte == 0:
            short_value = max(short_strike - underlying_price, 0.0)
            long_value = max(long_strike - underlying_price, 0.0)
        else:
            years = dte / 365.0
            short_value = self._put_value(
                underlying_price, short_strike, years, risk_free_rate, volatility
            )
            long_value = self._put_value(
                underlying_price, long_strike, years, risk_free_rate, volatility
            )

        debit = min(max(short_value - long_value, 0.0), width)
        return SpreadValuation(
            debit=debit,
            short_put_value=short_value,
            long_put_value=long_value,
            annualized_volatility=volatility,
        )

    @staticmethod
    def _put_value(
        spot: float,
        strike: float,
        years: float,
        rate: float,
        volatility: float,
    ) -> float:
        denominator = volatility * sqrt(years)
        d1 = (
            log(spot / strike)
            + (rate + 0.5 * volatility * volatility) * years
        ) / denominator
        d2 = d1 - denominator
        return strike * exp(-rate * years) * ApproximateSpreadPricer._normal_cdf(-d2) \
            - spot * ApproximateSpreadPricer._normal_cdf(-d1)

    @staticmethod
    def _normal_cdf(value: float) -> float:
        return 0.5 * (1.0 + erf(value / sqrt(2.0)))
