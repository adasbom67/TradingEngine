import pandas as pd


def select_short_puts(
    puts: pd.DataFrame,
    minimum_delta: float = 0.15,
    maximum_delta: float = 0.25,
    minimum_bid: float = 0.20,
    minimum_open_interest: int = 100,
    minimum_volume: int = 10,
) -> pd.DataFrame:
    """
    Select put options that may be suitable as the short leg
    of a bullish put credit spread.

    Put deltas are normally negative. For example:

        -0.15
        -0.20
        -0.25

    This function compares the absolute value of delta.
    """

    if puts.empty:
        return pd.DataFrame()

    required_columns = {
        "expiration_date",
        "days_to_expiration",
        "strike",
        "bid",
        "ask",
        "mark",
        "delta",
        "volume",
        "open_interest",
        "distance_otm_pct",
    }

    missing_columns = required_columns - set(puts.columns)

    if missing_columns:
        raise ValueError(
            f"Put option data is missing columns: {missing_columns}"
        )

    candidates = puts.copy()

    numeric_columns = [
        "strike",
        "bid",
        "ask",
        "mark",
        "delta",
        "volume",
        "open_interest",
        "distance_otm_pct",
    ]

    for column in numeric_columns:
        candidates[column] = pd.to_numeric(
            candidates[column],
            errors="coerce",
        )

    candidates = candidates.dropna(
        subset=[
            "strike",
            "bid",
            "ask",
            "delta",
            "open_interest",
            "volume",
        ]
    )

    candidates["absolute_delta"] = candidates["delta"].abs()
    candidates["bid_ask_spread"] = candidates["ask"] - candidates["bid"]

    candidates = candidates[
        candidates["absolute_delta"].between(
            minimum_delta,
            maximum_delta,
        )
        & (candidates["bid"] >= minimum_bid)
        & (candidates["open_interest"] >= minimum_open_interest)
        & (candidates["volume"] >= minimum_volume)
    ]

    candidates = candidates.sort_values(
        by=[
            "days_to_expiration",
            "absolute_delta",
            "open_interest",
        ],
        ascending=[
            True,
            False,
            False,
        ],
    )

    return candidates.reset_index(drop=True)