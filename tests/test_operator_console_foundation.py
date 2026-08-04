from fastapi.testclient import TestClient

from app.api.operator_console import create_app


def test_version_endpoint():
    client = TestClient(create_app())
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_dashboard_is_read_only():
    client = TestClient(create_app())
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.json()["execution_mode"] == "READ_ONLY"


def test_no_live_order_routes_are_exposed():
    paths = {route.path for route in create_app().routes}
    assert not any(
        token in path.lower()
        for path in paths
        for token in ("submit", "place-order", "cancel-order", "replace-order")
    )
