from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.operator_console import create_app


def test_operator_console_serves_built_ui_when_configured(tmp_path, monkeypatch):
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "index.html").write_text(
        "<html><body>TradingEngine Desktop</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setenv("TRADINGENGINE_UI_DIR", str(ui))
    monkeypatch.setenv("TRADINGENGINE_DESKTOP", "1")

    client = TestClient(create_app())

    page = client.get("/")
    version = client.get("/api/version")

    assert page.status_code == 200
    assert "TradingEngine Desktop" in page.text
    assert version.status_code == 200
    assert version.json()["environment"] == "desktop"


def test_api_remains_available_when_ui_is_mounted(tmp_path, monkeypatch):
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "index.html").write_text("desktop", encoding="utf-8")
    monkeypatch.setenv("TRADINGENGINE_UI_DIR", str(ui))

    response = TestClient(create_app()).get("/api/version")

    assert response.status_code == 200
    assert "version" in response.json()
