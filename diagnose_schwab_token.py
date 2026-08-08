from __future__ import annotations

import json
from pathlib import Path

from app.brokers.schwab_auth import create_schwab_client


def safe_token_summary(path: Path) -> dict:
    if not path.exists():
        return {"exists": False}

    payload = json.loads(path.read_text(encoding="utf-8"))
    token = payload.get("token", payload) if isinstance(payload, dict) else {}
    return {
        "exists": True,
        "top_level_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
        "token_keys": sorted(token.keys()) if isinstance(token, dict) else [],
        "token_type": token.get("token_type") if isinstance(token, dict) else None,
        "has_access_token": bool(token.get("access_token")) if isinstance(token, dict) else False,
        "has_refresh_token": bool(token.get("refresh_token")) if isinstance(token, dict) else False,
        "expires_in": token.get("expires_in") if isinstance(token, dict) else None,
    }


def main() -> None:
    token_path = Path("token.json")
    print("Token summary:")
    print(json.dumps(safe_token_summary(token_path), indent=2))
    print()

    client = create_schwab_client()
    print("Client created successfully.")

    for symbol in ("SPY", "QQQ"):
        response = client.get_quote(symbol)
        print(f"{symbol} status: {response.status_code}")
        print(f"{symbol} response: {response.text[:500]}")
        print()


if __name__ == "__main__":
    main()
