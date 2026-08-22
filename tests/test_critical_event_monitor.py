from datetime import datetime, timezone

from app.monitoring.critical_event_monitor import CriticalEventMonitor, is_high_confidence, is_regular_market_hours


def candidate(score=8, phase="IGNITION", strike=650):
    return {"symbol": "SPY", "total_score": score, "phase": phase,
            "scores": {"option_value": 2, "ignition": 2, "liquidity": 2},
            "option": {"expiration": "2026-09-18", "strike": strike}, "reasons": []}


def test_high_confidence_requires_score_phase_value_ignition_and_liquidity():
    assert is_high_confidence(candidate())
    assert not is_high_confidence(candidate(score=7))
    assert not is_high_confidence(candidate(phase="WATCH"))


def test_alert_requires_two_consecutive_scans_and_deduplicates_contract():
    monitor = CriticalEventMonitor(lambda: {"candidates": []})
    now = datetime.now(timezone.utc)
    assert monitor._review([candidate()], now) == []


def test_confirmation_streak_is_bound_to_the_same_contract():
    monitor = CriticalEventMonitor(lambda: {"candidates": []})
    now = datetime.now(timezone.utc)

    assert monitor._review([candidate(strike=650)], now) == []
    assert monitor._review([candidate(strike=651)], now) == []
    assert len(monitor._review([candidate(strike=651)], now)) == 1
    assert monitor._review([candidate()], now) == []
    assert len(monitor._review([candidate()], now)) == 1
    assert monitor._review([candidate()], now) == []


def test_market_hours_are_eastern_weekdays():
    assert is_regular_market_hours(datetime(2026, 8, 17, 15, 0, tzinfo=timezone.utc))
    assert not is_regular_market_hours(datetime(2026, 8, 16, 15, 0, tzinfo=timezone.utc))
