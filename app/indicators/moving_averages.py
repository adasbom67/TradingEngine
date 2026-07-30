import pandas as pd


def add_moving_averages(
    prices: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 200,
) -> pd.DataFrame:
    """
    Add short-term and long-term simple moving averages.

    The DataFrame must contain a 'close' column.
    """

    if "close" not in prices.columns:
        raise ValueError("DataFrame must contain a 'close' column.")

    result = prices.copy()

    result[f"sma_{short_window}"] = (
        result["close"]
        .rolling(window=short_window)
        .mean()
    )

    result[f"sma_{long_window}"] = (
        result["close"]
        .rolling(window=long_window)
        .mean()
    )

    return result