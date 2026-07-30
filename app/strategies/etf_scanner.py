from collections.abc import Iterable

import pandas as pd

from app.brokers.schwab_client import SchwabClient
from app.indicators.moving_averages import add_moving_averages


def classify_trend(
    price: float,
    sma_20: float,
    sma_200: float,
) -> str:
    """Classify the current moving-average trend."""

    if pd.isna(sma_20) or pd.isna(sma_200):
        return "Insufficient Data"

    if sma_20 > sma_200 and price > sma_20:
        return "Strong Bullish"

    if sma_20 > sma_200 and price > sma_200:
        return "Bullish Pullback"

    if sma_20 < sma_200 and price < sma_200:
        return "Bearish"

    return "Neutral"


def detect_reversal(prices: pd.DataFrame) -> dict:
    """
    Detect basic bullish stabilization or reversal signals.

    Signals:
    - Higher close than the previous session
    - Bullish candle: close above open
    - Close above previous session high
    - Two consecutive higher closes
    """

    if len(prices) < 3:
        return {
            "higher_close": False,
            "bullish_candle": False,
            "close_above_previous_high": False,
            "two_higher_closes": False,
            "reversal_score": 0,
            "reversal_confirmed": False,
        }

    latest = prices.iloc[-1]
    previous = prices.iloc[-2]
    two_days_ago = prices.iloc[-3]

    higher_close = latest["close"] > previous["close"]

    bullish_candle = latest["close"] > latest["open"]

    close_above_previous_high = (
        latest["close"] > previous["high"]
    )

    two_higher_closes = (
        latest["close"] > previous["close"]
        and previous["close"] > two_days_ago["close"]
    )

    reversal_score = sum(
        [
            higher_close,
            bullish_candle,
            close_above_previous_high,
            two_higher_closes,
        ]
    )

    reversal_confirmed = reversal_score >= 2

    return {
        "higher_close": bool(higher_close),
        "bullish_candle": bool(bullish_candle),
        "close_above_previous_high": bool(
            close_above_previous_high
        ),
        "two_higher_closes": bool(two_higher_closes),
        "reversal_score": int(reversal_score),
        "reversal_confirmed": bool(reversal_confirmed),
    }


def classify_setup(
    price: float,
    sma_20: float,
    sma_200: float,
    reversal_confirmed: bool,
) -> str:
    """Classify the symbol as a potential trading setup."""

    if pd.isna(sma_20) or pd.isna(sma_200):
        return "No Setup"

    if sma_20 > sma_200 and price > sma_20:
        return "Bullish Momentum"

    if (
        sma_20 > sma_200
        and sma_200 < price <= sma_20
        and reversal_confirmed
    ):
        return "Confirmed Bullish Pullback"

    if (
        sma_20 > sma_200
        and sma_200 < price <= sma_20
    ):
        return "Unconfirmed Bullish Pullback"

    return "No Setup"


def scan_etfs(
    client: SchwabClient,
    symbols: Iterable[str],
) -> pd.DataFrame:
    """Scan ETFs and return trend, pullback, and reversal data."""

    results: list[dict] = []

    for symbol in symbols:
        symbol = symbol.upper().strip()

        try:
            prices = client.get_daily_price_history(symbol)
            prices = add_moving_averages(prices)

            latest = prices.iloc[-1]

            price = float(latest["close"])
            sma_20 = float(latest["sma_20"])
            sma_200 = float(latest["sma_200"])

            distance_from_20 = ((price / sma_20) - 1) * 100
            distance_from_200 = ((price / sma_200) - 1) * 100

            reversal = detect_reversal(prices)

            setup = classify_setup(
                price=price,
                sma_20=sma_20,
                sma_200=sma_200,
                reversal_confirmed=reversal[
                    "reversal_confirmed"
                ],
            )

            results.append(
                {
                    "symbol": symbol,
                    "date": latest["date"].date(),
                    "price": price,
                    "sma_20": sma_20,
                    "sma_200": sma_200,
                    "distance_from_20_pct": distance_from_20,
                    "distance_from_200_pct": distance_from_200,
                    "trend": classify_trend(
                        price=price,
                        sma_20=sma_20,
                        sma_200=sma_200,
                    ),
                    "setup": setup,
                    "higher_close": reversal["higher_close"],
                    "bullish_candle": reversal[
                        "bullish_candle"
                    ],
                    "close_above_previous_high": reversal[
                        "close_above_previous_high"
                    ],
                    "two_higher_closes": reversal[
                        "two_higher_closes"
                    ],
                    "reversal_score": reversal[
                        "reversal_score"
                    ],
                    "reversal_confirmed": reversal[
                        "reversal_confirmed"
                    ],
                    "above_20_sma": price > sma_20,
                    "above_200_sma": price > sma_200,
                    "bullish_alignment": sma_20 > sma_200,
                }
            )

        except Exception as error:
            results.append(
                {
                    "symbol": symbol,
                    "date": None,
                    "price": None,
                    "sma_20": None,
                    "sma_200": None,
                    "distance_from_20_pct": None,
                    "distance_from_200_pct": None,
                    "trend": "Error",
                    "setup": "No Setup",
                    "higher_close": False,
                    "bullish_candle": False,
                    "close_above_previous_high": False,
                    "two_higher_closes": False,
                    "reversal_score": 0,
                    "reversal_confirmed": False,
                    "above_20_sma": False,
                    "above_200_sma": False,
                    "bullish_alignment": False,
                    "error": str(error),
                }
            )

    return pd.DataFrame(results)