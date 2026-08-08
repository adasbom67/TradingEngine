from __future__ import annotations

import json
import time
from pathlib import Path

SOURCE = Path("schwab_verified_token.json")
TARGET = Path("token.json")

if not SOURCE.exists():
    raise SystemExit("schwab_verified_token.json was not found in the TradingEngine root.")

token = json.loads(SOURCE.read_text(encoding="utf-8"))
if not isinstance(token, dict):
    raise SystemExit("Verified token file is not a JSON object.")

required = ("access_token", "refresh_token", "token_type", "expires_in")
missing = [key for key in required if not token.get(key)]
if missing:
    raise SystemExit("Verified token is missing: " + ", ".join(missing))

now = int(time.time())
normalized = dict(token)
normalized["expires_at"] = now + int(token["expires_in"])

payload = {
    "creation_timestamp": now,
    "token": normalized,
}

TARGET.write_text(json.dumps(payload, indent=2), encoding="utf-8")

print("Success: token.json converted to schwab-py 1.5.1 format.")
print("Refresh token preserved:", bool(normalized.get("refresh_token")))
