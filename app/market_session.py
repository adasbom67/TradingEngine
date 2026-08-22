from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo


EASTERN = ZoneInfo("America/New_York")


def recommendation_market_session(now: datetime | None = None) -> dict[str, Any]:
    """Describe whether option-volume data belongs to the active regular session."""
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    eastern = instant.astimezone(EASTERN)

    if eastern.weekday() >= 5:
        status = "CLOSED"
    elif eastern.time() < time(9, 30):
        status = "PREMARKET"
    elif eastern.time() < time(16, 0):
        status = "REGULAR"
    else:
        status = "AFTER_HOURS"

    regular = status == "REGULAR"
    return {
        "status": status,
        "is_regular_hours": regular,
        "provisional": not regular,
        "observed_at": eastern.isoformat(),
        "message": (
            "Regular U.S. market hours: current-session option volume is enforced."
            if regular
            else "Outside regular U.S. market hours: results are provisional and "
            "current-session option volume is not used as a hard eligibility gate."
        ),
    }
