from app.api.recommendations import (
    RecommendationConstraints,
    _rejection_analysis,
    _scan_outcome,
    _what_if_hints,
)


def test_rejection_analysis_counts_and_orders_reasons():
    analysis = _rejection_analysis([
        {"reasons": ["Credit per contract $50.00 is below $75.00.", "Return on risk is below the minimum."]},
        {"reasons": ["Credit per contract $55.00 is below $75.00."]},
    ])
    assert analysis[0]["count"] == 1 or analysis[0]["count"] == 2
    assert sum(item["count"] for item in analysis) == 3


def test_scan_outcome_distinguishes_zero_pipeline_candidates():
    assert _scan_outcome(0, 0, 0, 0) == "NO_PIPELINE_CANDIDATES"
    assert _scan_outcome(5, 0, 5, 0) == "ALL_REJECTED"
    assert _scan_outcome(5, 1, 4, 0) == "RESULTS"
    assert _scan_outcome(0, 0, 0, 1) == "ERROR"


def test_what_if_hint_uses_active_credit_constraint():
    analysis = [{"reason": "Credit per contract $50.00 is below $75.00.", "count": 4, "candidate_percent": 100.0}]
    hints = _what_if_hints(RecommendationConstraints(minimum_credit_per_contract=75), analysis)
    assert hints[0]["constraint"] == "minimum_credit_per_contract"
    assert "$75" in hints[0]["suggestion"]
