from datetime import date, datetime
from typing import Any

from app.models.market.option_contract import OptionContract


def normalize_schwab_option(
    raw_contract: dict[str, Any],
) -> OptionContract:
    """
    Convert one raw Schwab option contract into an OptionContract.

    Args:
        raw_contract: A single option-contract dictionary returned by Schwab.

    Returns:
        A normalized OptionContract object.

    Raises:
        ValueError: If a required field is missing or invalid.
    """

    try:
        symbol = str(raw_contract["symbol"])
        expiration_date = _parse_expiration_date(
            raw_contract["expirationDate"]
        )
        strike = float(raw_contract["strikePrice"])
        option_type = str(raw_contract["putCall"]).upper()

    except KeyError as error:
        missing_field = error.args[0]

        raise ValueError(
            f"Schwab option contract is missing required field: "
            f"{missing_field}"
        ) from error

    return OptionContract(
        symbol=symbol,
        expiration_date=expiration_date,
        strike=strike,
        option_type=option_type,
        bid=_to_float(raw_contract.get("bid")),
        ask=_to_float(raw_contract.get("ask")),
        last=_to_float(raw_contract.get("last")),
        delta=_to_optional_float(raw_contract.get("delta")),
        volume=_to_int(raw_contract.get("totalVolume")),
        open_interest=_to_int(raw_contract.get("openInterest")),
        days_to_expiration=_to_int(
            raw_contract.get("daysToExpiration")
        ),
    )


def _parse_expiration_date(value: Any) -> date:
    """
    Convert a Schwab expiration-date value into a Python date.

    The function supports ISO date strings, datetime objects, date objects,
    and Unix timestamps expressed in seconds or milliseconds.
    """

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        cleaned_value = value.strip()

        try:
            return date.fromisoformat(cleaned_value[:10])
        except ValueError as error:
            raise ValueError(
                f"Invalid expiration date: {value}"
            ) from error

    if isinstance(value, (int, float)):
        timestamp = float(value)

        # Millisecond timestamps are much larger than second timestamps.
        if timestamp > 10_000_000_000:
            timestamp /= 1000

        return datetime.fromtimestamp(timestamp).date()

    raise ValueError(
        f"Unsupported expiration-date value: {value!r}"
    )


def _to_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_optional_float(value: Any) -> float | None:
    """Convert a value to float while preserving missing values as None."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to an integer."""

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default