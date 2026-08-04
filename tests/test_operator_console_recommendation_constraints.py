from app.api.recommendations import (
    RecommendationConstraints,
    RecommendationRequest,
    _rejection_reasons,
)


def _candidate():
    return {
        "spread_width": 5.0,
        "return_on_risk": 0.15,
        "probability_of_profit": 0.76,
        "expected_value": 12.0,
        "managed_expected_value": 2.0,
        "net_position_delta": 0.08,
        "maximum_risk": 437.0,
        "score": 91.0,
        "decision": "PASS",
        "warnings": [],
        "quote": {
            "scoring_credit": 0.63,
            "natural_credit": 0.55,
            "midpoint_credit": 0.64,
            "conservative_credit": 0.55,
            "short_open_interest": 1000,
            "long_open_interest": 800,
            "short_volume": 100,
            "long_volume": 50,
            "short_bid": 2.0,
            "short_ask": 2.1,
            "long_bid": 1.4,
            "long_ask": 1.45,
        },
    }


def test_minimum_credit_per_contract_uses_selected_pricing_method():
    constraints = RecommendationConstraints(
        minimum_credit_per_contract=60,
        pricing_method="NATURAL",
    )
    reasons = _rejection_reasons(_candidate(), constraints)
    assert any("Credit per contract" in reason for reason in reasons)


def test_blank_constraints_accept_candidate():
    assert _rejection_reasons(_candidate(), RecommendationConstraints()) == []


def test_request_normalizes_symbols_and_validates_dte():
    request = RecommendationRequest(
        symbols=["spy", " SPY ", "qqq"],
        constraints={"minimum_dte": 30, "maximum_dte": 45},
    )
    assert request.symbols == ["SPY", "QQQ"]
