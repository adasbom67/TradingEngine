from fastapi.testclient import TestClient

from app.api.operator_console import create_app


def test_recommendation_scan_validates_symbols():
    client = TestClient(create_app())
    response = client.post("/api/recommendations/scan", json={"symbols": []})
    assert response.status_code == 422


def test_recommendation_request_accepts_both_credit_spread_directions():
    from app.api.recommendations import RecommendationRequest

    request = RecommendationRequest(
        symbols=["SPY"], strategies=["BULL_PUT", "BEAR_CALL"]
    )
    assert request.strategies == ["BULL_PUT", "BEAR_CALL"]


def test_recommendation_engine_scans_each_requested_strategy(monkeypatch):
    from types import SimpleNamespace

    from app.api.recommendations import RecommendationRequest, run_recommendation_scan
    from app.evaluation.pipeline_diagnostics import PipelineDiagnostics

    class Scanner:
        def __init__(self, market_data, pipeline, market_analysis=None):
            self.strategy_type = pipeline.strategy_type

        def scan_live_with_diagnostics(self, symbol, config):
            diagnostics = PipelineDiagnostics(strategy_type=self.strategy_type)
            diagnostics.total_contracts = 1
            return [], diagnostics

    monkeypatch.setattr("app.api.recommendations.create_schwab_client", lambda: object())
    monkeypatch.setattr(
        "app.api.recommendations.create_default_candidate_pipeline",
        lambda strategy_type="BULL_PUT": SimpleNamespace(strategy_type=strategy_type),
    )
    monkeypatch.setattr("app.api.recommendations.LiveCandidateScanner", Scanner)

    result = run_recommendation_scan(
        RecommendationRequest(
            symbols=["SPY"], strategies=["BULL_PUT", "BEAR_CALL"]
        )
    )
    assert result["strategies"] == ["BULL_PUT", "BEAR_CALL"]
    assert {item["strategy_type"] for item in result["diagnostics"]} == {
        "BULL_PUT",
        "BEAR_CALL",
    }


def test_off_hours_scan_disables_only_baseline_current_volume_gate(monkeypatch):
    from types import SimpleNamespace

    from app.api.recommendations import RecommendationRequest, run_recommendation_scan
    from app.evaluation.pipeline_diagnostics import PipelineDiagnostics

    observed = []

    class Scanner:
        def __init__(self, market_data, pipeline, market_analysis=None):
            self.strategy_type = pipeline.strategy_type

        def scan_live_with_diagnostics(self, symbol, config):
            observed.append(config.enforce_minimum_volume)
            return [], PipelineDiagnostics(strategy_type=self.strategy_type)

    monkeypatch.setattr("app.api.recommendations.create_schwab_client", lambda: object())
    monkeypatch.setattr(
        "app.api.recommendations.create_default_candidate_pipeline",
        lambda strategy_type="BULL_PUT": SimpleNamespace(strategy_type=strategy_type),
    )
    monkeypatch.setattr("app.api.recommendations.LiveCandidateScanner", Scanner)
    monkeypatch.setattr(
        "app.api.recommendations.recommendation_market_session",
        lambda: {
            "status": "PREMARKET",
            "is_regular_hours": False,
            "provisional": True,
            "observed_at": "2026-08-17T07:00:00-04:00",
            "message": "Provisional.",
        },
    )

    result = run_recommendation_scan(RecommendationRequest(symbols=["SPY"]))

    assert observed == [False]
    assert result["market_session"]["provisional"] is True


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
    monkeypatch.setattr(
        "app.api.operator_console.schwab_connection_status",
        lambda: {"status": "CONNECTED", "requires_reconnect": False},
    )
    client = TestClient(create_app())
    response = client.post("/api/recommendations/scan", json={"symbols": ["spy"]})
    assert response.status_code == 200
    assert response.json()["execution_mode"] == "READ_ONLY"


def test_recommendation_scan_requests_reconnect_before_running(monkeypatch):
    monkeypatch.setattr(
        "app.api.operator_console.schwab_connection_status",
        lambda: {
            "status": "EXPIRED",
            "requires_reconnect": True,
            "message": "Schwab connection expired.",
        },
    )
    client = TestClient(create_app())
    response = client.post("/api/recommendations/scan", json={"symbols": ["SPY"]})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "SCHWAB_RECONNECT_REQUIRED"


def test_no_live_submission_route_is_added():
    paths = {route.path.lower() for route in create_app().routes}
    assert not any("submit" in path or "place-order" in path for path in paths)
