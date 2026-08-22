from datetime import datetime, timezone

from app.market_session import recommendation_market_session


def eastern_time(hour: int, minute: int = 0) -> datetime:
    # August is daylight time, so Eastern is UTC-4.
    return datetime(2026, 8, 17, hour + 4, minute, tzinfo=timezone.utc)


def test_regular_session_enforces_current_volume():
    session = recommendation_market_session(eastern_time(10))

    assert session["status"] == "REGULAR"
    assert session["is_regular_hours"] is True
    assert session["provisional"] is False


def test_premarket_session_is_provisional():
    session = recommendation_market_session(eastern_time(7))

    assert session["status"] == "PREMARKET"
    assert session["is_regular_hours"] is False
    assert session["provisional"] is True


def test_weekend_session_is_closed_and_provisional():
    saturday = datetime(2026, 8, 22, 14, tzinfo=timezone.utc)
    session = recommendation_market_session(saturday)

    assert session["status"] == "CLOSED"
    assert session["provisional"] is True
