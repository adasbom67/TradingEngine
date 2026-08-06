from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from schwab.auth import client_from_manual_flow


def main() -> None:
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
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))

    print("Starting Schwab manual authentication.")
    print(f"Callback URL: {callback_url}")
    print(f"Token destination: {token_path.resolve()}")
    print()
    print("Follow the prompts. After Schwab redirects your browser, copy the")
    print("entire URL from the browser address bar and paste it into this terminal.")
    print()

    client_from_manual_flow(
        api_key=app_key,
        app_secret=app_secret,
        callback_url=callback_url,
        token_path=str(token_path),
    )

    print()
    print(f"Success: Schwab token saved to {token_path.resolve()}")


if __name__ == "__main__":
    main()
