from __future__ import annotations

import base64, json, os, secrets, urllib.parse, webbrowser
from pathlib import Path
import httpx
from dotenv import load_dotenv

AUTHORIZE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
QUOTE_URL = "https://api.schwabapi.com/marketdata/v1/quotes"

def main():
    load_dotenv()
    key = os.getenv("SCHWAB_APP_KEY")
    secret = os.getenv("SCHWAB_APP_SECRET")
    callback = os.getenv("SCHWAB_CALLBACK_URL")
    if not all([key, secret, callback]):
        raise RuntimeError("Missing Schwab settings in .env")

    state = secrets.token_urlsafe(18)
    auth_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode({
        "client_id": key,
        "redirect_uri": callback,
        "state": state,
    })

    print("SCHWAB STANDALONE OAUTH VERIFICATION")
    print(f"Callback URL: {callback}")
    print("Complete the Schwab login in the browser.")
    print("Then paste the ENTIRE callback URL into this terminal.")
    print("Do not paste the callback URL into ChatGPT.\n")
    webbrowser.open(auth_url)
    print("Authorization URL:", auth_url, "\n")

    redirected = input("Redirect URL> ").strip()
    q = urllib.parse.parse_qs(urllib.parse.urlparse(redirected).query)
    code = q.get("code", [None])[0]
    if not code:
        raise RuntimeError("No authorization code found in redirect URL")

    creds = base64.b64encode(f"{key}:{secret}".encode()).decode()

    with httpx.Client(timeout=30.0) as c:
        r = c.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback,
            },
        )
        print("\nToken endpoint HTTP status:", r.status_code)
        token = r.json()

        if r.status_code != 200:
            print(json.dumps({
                "error": token.get("error"),
                "error_description": token.get("error_description")
            }, indent=2))
            return

        summary = {
            "token_type": token.get("token_type"),
            "scope": token.get("scope"),
            "expires_in": token.get("expires_in"),
            "has_access_token": bool(token.get("access_token")),
            "has_refresh_token": bool(token.get("refresh_token")),
            "has_id_token": bool(token.get("id_token")),
            "keys_returned": sorted(token.keys()),
        }
        print("\nTOKEN RESPONSE SUMMARY")
        print(json.dumps(summary, indent=2))

        if not token.get("refresh_token"):
            print("\nRESULT: FAIL - Schwab itself returned no refresh_token.")
            return

        qresp = c.get(
            QUOTE_URL,
            headers={"Authorization": f"Bearer {token['access_token']}"},
            params={"symbols": "SPY"},
        )
        print("\nSPY quote HTTP status:", qresp.status_code)
        if qresp.status_code != 200:
            print(qresp.text[:500])
            return

        out = Path("schwab_verified_token.json")
        out.write_text(json.dumps(token, indent=2), encoding="utf-8")
        print("\nRESULT: PASS")
        print("Refresh token present and SPY quote succeeded.")
        print("Saved locally to:", out.resolve())

if __name__ == "__main__":
    main()
