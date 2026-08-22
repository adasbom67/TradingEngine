from __future__ import annotations

import base64
import json
import os
import secrets
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


AUTHORIZE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
REFRESH_TOKEN_LIFETIME_SECONDS = 7 * 24 * 60 * 60
EXPIRING_WARNING_SECONDS = 24 * 60 * 60
AUTHORIZATION_STATE_LIFETIME_SECONDS = 10 * 60

_pending_states: dict[str, float] = {}
_pending_states_lock = threading.Lock()


class SchwabConnectionError(RuntimeError):
    """Raised when the local Schwab OAuth flow cannot be completed."""


def _settings() -> tuple[str, str, str, Path]:
    load_dotenv()
    app_key = os.getenv("SCHWAB_APP_KEY", "").strip()
    app_secret = os.getenv("SCHWAB_APP_SECRET", "").strip()
    callback_url = os.getenv("SCHWAB_CALLBACK_URL", "").strip()
    token_path = Path(os.getenv("SCHWAB_TOKEN_PATH", "token.json"))
    missing = [
        name
        for name, value in (
            ("SCHWAB_APP_KEY", app_key),
            ("SCHWAB_APP_SECRET", app_secret),
            ("SCHWAB_CALLBACK_URL", callback_url),
        )
        if not value
    ]
    if missing:
        raise SchwabConnectionError(
            "Missing Schwab configuration: " + ", ".join(missing)
        )
    return app_key, app_secret, callback_url, token_path


def _query_value_preserving_plus(url: str, name: str) -> str | None:
    query = urllib.parse.urlsplit(url).query
    for field in query.split("&"):
        raw_name, separator, raw_value = field.partition("=")
        if separator and urllib.parse.unquote(raw_name) == name:
            return urllib.parse.unquote(raw_value)
    return None


def _redirect_target(url: str) -> tuple[str, str, int | None, str]:
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme.lower(),
        (parsed.hostname or "").lower(),
        parsed.port,
        parsed.path or "/",
    )


def _iso_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def schwab_connection_status() -> dict[str, Any]:
    try:
        _, _, callback_url, token_path = _settings()
    except SchwabConnectionError as exc:
        return {
            "status": "NOT_CONFIGURED",
            "configured": False,
            "requires_reconnect": True,
            "message": str(exc),
        }

    base: dict[str, Any] = {
        "configured": True,
        "callback_url": callback_url,
        "token_path": str(token_path.resolve()),
    }
    if not token_path.is_file():
        return {
            **base,
            "status": "DISCONNECTED",
            "requires_reconnect": True,
            "message": "Schwab has not been connected yet.",
        }

    try:
        payload = json.loads(token_path.read_text(encoding="utf-8"))
        created_at = float(payload["creation_timestamp"])
        token = payload["token"]
        if not isinstance(token, dict) or not token.get("refresh_token"):
            raise ValueError("refresh token is missing")
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {
            **base,
            "status": "INVALID",
            "requires_reconnect": True,
            "message": f"The saved Schwab token cannot be used ({exc}).",
        }

    now = time.time()
    expires_at = created_at + REFRESH_TOKEN_LIFETIME_SECONDS
    remaining = expires_at - now
    details = {
        **base,
        "created_at": _iso_timestamp(created_at),
        "refresh_expires_at": _iso_timestamp(expires_at),
        "remaining_seconds": max(0, int(remaining)),
    }
    if remaining <= 0:
        return {
            **details,
            "status": "EXPIRED",
            "requires_reconnect": True,
            "message": "The Schwab refresh token is approximately seven days old and must be renewed.",
        }
    if remaining <= EXPIRING_WARNING_SECONDS:
        hours = max(1, round(remaining / 3600))
        return {
            **details,
            "status": "EXPIRING",
            "requires_reconnect": False,
            "message": f"Schwab is connected, but reauthorization is due in about {hours} hour(s).",
        }
    days = max(1, round(remaining / 86400))
    return {
        **details,
        "status": "CONNECTED",
        "requires_reconnect": False,
        "message": f"Schwab is connected. Reauthorization is due in about {days} day(s).",
    }


def begin_schwab_authorization() -> dict[str, str]:
    app_key, _, callback_url, _ = _settings()
    state = secrets.token_urlsafe(24)
    now = time.time()
    with _pending_states_lock:
        expired = [
            value
            for value, created_at in _pending_states.items()
            if now - created_at > AUTHORIZATION_STATE_LIFETIME_SECONDS
        ]
        for value in expired:
            _pending_states.pop(value, None)
        _pending_states[state] = now
    authorization_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": app_key,
            "redirect_uri": callback_url,
            "state": state,
        }
    )
    return {"authorization_url": authorization_url, "callback_url": callback_url}


def complete_schwab_authorization(redirect_url: str) -> dict[str, Any]:
    app_key, app_secret, callback_url, token_path = _settings()
    redirect_url = redirect_url.strip()
    if _redirect_target(redirect_url) != _redirect_target(callback_url):
        raise SchwabConnectionError(
            f"The pasted URL does not match the configured callback {callback_url!r}."
        )

    error = _query_value_preserving_plus(redirect_url, "error")
    if error:
        description = _query_value_preserving_plus(redirect_url, "error_description")
        raise SchwabConnectionError(
            f"Schwab authorization failed: {error}: {description or 'no description'}"
        )

    returned_state = _query_value_preserving_plus(redirect_url, "state")
    with _pending_states_lock:
        state_created_at = _pending_states.pop(returned_state, None) if returned_state else None
    if state_created_at is None or time.time() - state_created_at > AUTHORIZATION_STATE_LIFETIME_SECONDS:
        raise SchwabConnectionError(
            "This callback does not belong to the current login attempt or has expired. Start again."
        )

    code = _query_value_preserving_plus(redirect_url, "code")
    if not code:
        raise SchwabConnectionError("No authorization code was found in the callback URL.")

    credentials = base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()
    try:
        response = httpx.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url,
            },
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        raise SchwabConnectionError(f"Could not reach Schwab's token service: {exc}") from exc

    try:
        token = response.json()
    except ValueError as exc:
        raise SchwabConnectionError(
            f"Schwab returned an unreadable token response (HTTP {response.status_code})."
        ) from exc
    if response.status_code != 200:
        description = token.get("error_description") or token.get("error") or "unknown error"
        raise SchwabConnectionError(f"Schwab rejected the authorization code: {description}")
    required = ("access_token", "refresh_token", "token_type", "expires_in")
    missing = [name for name in required if not token.get(name)]
    if missing:
        raise SchwabConnectionError(
            "Schwab's token response was incomplete: " + ", ".join(missing)
        )

    now = int(time.time())
    normalized = dict(token)
    normalized["expires_at"] = now + int(token["expires_in"])
    payload = {"creation_timestamp": now, "token": normalized}
    token_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = token_path.with_name(token_path.name + ".tmp")
    temporary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary_path.replace(token_path)
    return schwab_connection_status()


def is_schwab_authentication_error(message: str) -> bool:
    lowered = message.lower()
    markers = (
        "invalid_grant",
        "refresh token is invalid",
        "refresh token invalid",
        "authorization code is invalid",
        "expired or revoked",
        "unsupported_token_type",
    )
    return any(marker in lowered for marker in markers)
