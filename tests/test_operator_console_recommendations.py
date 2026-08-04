from fastapi.testclient import TestClient

from app.api.operator_console import create_app


def test_recommendation_scan_validates_symbols():
    client = TestClient(create_app())
    response = client.post("/api/recommendations/scan", json={"symbols": []})
    assert response.status_code == 422


def test_recommendation_endpoint_serializes_result(monkeypatch):
    expected = {
        "as_of": "2026-08-03",
        "symbols": ["SPY"],
        "candidates": [],
        "diagnostics": [],
        "summary": {
            "candidate_count": 0,
            "trade_count": 0,
            "watch_count": 0,
            "pass_count": 0,
        },
        "execution_mode": "READ_ONLY",
    }
    monkeypatch.setattr(
        "app.api.operator_console.run_recommendation_scan",
        lambda request: expected,
    )
    client = TestClient(create_app())
    response = client.post("/api/recommendations/scan", json={"symbols": ["spy"]})
    assert response.status_code == 200
    assert response.json()["execution_mode"] == "READ_ONLY"


def test_no_live_submission_route_is_added():
    paths = {route.path.lower() for route in create_app().routes}
    assert not any("submit" in path or "place-order" in path for path in paths)
