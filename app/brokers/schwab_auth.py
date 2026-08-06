from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from schwab.auth import client_from_manual_flow, client_from_token_file


class SchwabConfigurationError(RuntimeError):
    """Raised when required Schwab connection settings are missing."""


def create_schwab_client() -> Any:
    """Create an authenticated Schwab client.

    Existing tokens are always preferred. The manual OAuth flow is used only
    when the configured token file does not yet exist.
    """
    load_dotenv()

    app_key = os.getenv("SCHWAB_APP_KEY")
    app_secret = os.getenv("SCHWAB_APP_SECRET")
    callback_url = os.getenv("SCHWAB_CALLBACK_URL")
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
        raise SchwabConfigurationError(
            "Missing required Schwab environment variables: " + ", ".join(missing)
        )

    if token_path.exists():
        return client_from_token_file(
            token_path=str(token_path),
            api_key=app_key,
            app_secret=app_secret,
        )

    return client_from_manual_flow(
        api_key=app_key,
        app_secret=app_secret,
        callback_url=callback_url,
        token_path=str(token_path),
    )
