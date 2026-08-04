from fastapi.testclient import TestClient

from app.api.operator_console import create_app


def _payload(**overrides):
    payload = {
        "symbol": "SPY",
        "initial_capital": 100000,
        "minimum_dte": 30,
        "maximum_dte": 45,
        "spread_width": 5,
        "period_years": 5,
    }
    payload.update(overrides)
    return payload


def test_backtest_validation_rejects_reversed_dte_range():
    client = TestClient(create_app())
    response = client.post(
        "/api/backtests",
        json=_payload(minimum_dte=45, maximum_dte=30),
    )
    assert response.status_code == 422


def test_backtest_validation_rejects_nonpositive_width():
    client = TestClient(create_app())
    response = client.post("/api/backtests", json=_payload(spread_width=0))
    assert response.status_code == 422


def test_backtest_endpoint_serializes_result(monkeypatch):
    expected = {
        "configuration": {"symbol": "SPY"},
        "summary": {"trade_count": 0},
        "by_regime": [],
        "by_exit_reason": [],
        "recent_trades": [],
        "disclosure": "test",
    }
    monkeypatch.setattr(
        "app.api.operator_console.run_backtest",
        lambda request: expected,
    )
    client = TestClient(create_app())
    response = client.post("/api/backtests", json=_payload(symbol="spy"))

    assert response.status_code == 200
    assert response.json()["configuration"]["symbol"] == "SPY"


def test_no_live_order_routes_are_exposed():
    paths = {route.path.lower() for route in create_app().routes}
    blocked_tokens = ("submit", "place-order", "cancel-order", "replace-order")
    assert not any(
        token in path
        for path in paths
        for token in blocked_tokens
    )
