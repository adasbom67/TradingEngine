from fastapi.testclient import TestClient

from app.api.operator_console import create_app


def test_dashboard_reports_research_mode_and_safety_state():
    client = TestClient(create_app())

    response = client.get("/api/dashboard")

    assert response.status_code == 200

    payload = response.json()

    assert payload["operating_mode"] == "RESEARCH"
    assert payload["execution_mode"] == "READ_ONLY"
    assert payload["platform"]["api"]["status"] == "HEALTHY"
    assert payload["platform"]["live_trading"]["status"] == "DISABLED"
