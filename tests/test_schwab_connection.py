import json
import time
import urllib.parse

from app.brokers import schwab_connection


def _configure(monkeypatch, token_path):
    monkeypatch.setenv("SCHWAB_APP_KEY", "app-key")
    monkeypatch.setenv("SCHWAB_APP_SECRET", "app-secret")
    monkeypatch.setenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")
    monkeypatch.setenv("SCHWAB_TOKEN_PATH", str(token_path))


def _write_token(path, created_at):
    path.write_text(
        json.dumps(
            {
                "creation_timestamp": created_at,
                "token": {"refresh_token": "refresh-token"},
            }
        ),
        encoding="utf-8",
    )


def test_connection_status_reports_connected_and_expired(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    _configure(monkeypatch, token_path)
    _write_token(token_path, time.time())
    assert schwab_connection.schwab_connection_status()["status"] == "CONNECTED"

    _write_token(
        token_path,
        time.time() - schwab_connection.REFRESH_TOKEN_LIFETIME_SECONDS - 1,
    )
    status = schwab_connection.schwab_connection_status()
    assert status["status"] == "EXPIRED"
    assert status["requires_reconnect"] is True


def test_authorization_flow_preserves_plus_and_installs_token(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    _configure(monkeypatch, token_path)
    started = schwab_connection.begin_schwab_authorization()
    state = urllib.parse.parse_qs(
        urllib.parse.urlsplit(started["authorization_url"]).query
    )["state"][0]

    captured = {}

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "token_type": "Bearer",
                "expires_in": 1800,
            }

    def fake_post(url, **kwargs):
        captured.update(kwargs["data"])
        return Response()

    monkeypatch.setattr(schwab_connection.httpx, "post", fake_post)
    status = schwab_connection.complete_schwab_authorization(
        f"https://127.0.0.1/?code=abc+def%40&state={urllib.parse.quote(state)}"
    )

    assert captured["code"] == "abc+def@"
    assert status["status"] == "CONNECTED"
    saved = json.loads(token_path.read_text(encoding="utf-8"))
    assert saved["token"]["refresh_token"] == "refresh-token"


def test_authentication_error_detection():
    assert schwab_connection.is_schwab_authentication_error(
        "Refresh token is invalid, expired or revoked"
    )
    assert not schwab_connection.is_schwab_authentication_error("Market is closed")
