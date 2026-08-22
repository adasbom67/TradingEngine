from __future__ import annotations

import base64, json, os, secrets, urllib.parse, webbrowser
from pathlib import Path
import httpx
from dotenv import load_dotenv

AUTHORIZE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
QUOTE_URL = "https://api.schwabapi.com/marketdata/v1/quotes"


def _query_value_preserving_plus(url: str, name: str) -> str | None:
    """Decode a callback parameter without changing a literal '+' into a space."""
    query = urllib.parse.urlsplit(url).query
    for field in query.split("&"):
        raw_name, separator, raw_value = field.partition("=")
        if separator and urllib.parse.unquote(raw_name) == name:
            return urllib.parse.unquote(raw_value)
    return None


def _redirect_target(url: str) -> tuple[str, str, int | None, str]:
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path or "/"
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port, path

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
    if _redirect_target(redirected) != _redirect_target(callback):
        raise RuntimeError(
            "The pasted redirect URL does not target the configured callback URL. "
            f"Expected {callback!r}. Check the callback value in the Schwab developer portal."
        )

    error = _query_value_preserving_plus(redirected, "error")
    if error:
        description = _query_value_preserving_plus(redirected, "error_description")
        raise RuntimeError(f"Schwab authorization failed: {error}: {description or 'no description'}")

    returned_state = _query_value_preserving_plus(redirected, "state")
    if returned_state != state:
        raise RuntimeError("The callback state did not match this login attempt. Start again with a fresh URL.")

    code = _query_value_preserving_plus(redirected, "code")
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
            print("\nThe code was generated for this run and was parsed without converting '+' characters.")
            print("If Schwab still reports invalid_grant, verify in the developer portal that:")
            print(f"  1. The app callback is exactly: {callback}")
            print("  2. The app status is Ready for Use")
            print("Then run this script again; authorization codes cannot be reused.")
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
