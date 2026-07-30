"""
One-time interactive Yahoo OAuth2 authorization -- FR-062, thread 095.

WHAT THIS DOES. Prints the URL to open, waits for the verification code
Yahoo displays after you click "Allow", exchanges it for an access + refresh
token pair, and saves them to data/.yahoo_token.json (gitignored -- see
src/providers/yahoo_oauth.py's module docstring). Run this once; every other
script and the app itself reuse the saved token, refreshing automatically
when it expires.

BEFORE RUNNING THIS:
1. Log into the Yahoo account that holds your leagues.
2. Go to https://developer.yahoo.com/apps/create/
3. Application Type: "Installed Application"
4. Redirect URI: https://localhost:8080 (or your own port -- must match
   YAHOO_REDIRECT_URI below exactly, protocol and port included)
5. API Permissions: Fantasy Sports -> Read
6. Create App -- copy the Client ID and Client Secret it shows you.
7. Put them in .env (copy .env.example if you haven't):
       YAHOO_CLIENT_ID=...
       YAHOO_CLIENT_SECRET=...
       YAHOO_REDIRECT_URI=https://localhost:8080

Then run:
    python scripts/yahoo_connect.py

This has never been run against a real Yahoo account in this project --
credentials are the founder's and have not been supplied yet. Every line of
this script is built against the registration/token-exchange flow five
independent SDKs document identically
(docs/research/yahoo-espn-league-connection-2026-07-30.md SS2), not against
a captured real response.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from providers.yahoo_oauth import (  # noqa: E402
    TokenStore,
    YahooOAuthClient,
    YahooOAuthConfig,
)


def main() -> int:
    try:
        config = YahooOAuthConfig.from_env()
    except ValueError as exc:
        print(f"Cannot start: {exc}")
        return 1

    client = YahooOAuthClient(config)
    store = TokenStore()

    print("1. Open this URL in a browser signed into the Yahoo account with your leagues:")
    print()
    print(f"   {client.build_authorization_url()}")
    print()
    print("2. Click 'Allow'. Yahoo will show a verification code on the page.")
    code = input("3. Paste that verification code here, then press Enter: ").strip()
    if not code:
        print("No code entered, aborting.")
        return 1

    tokens = client.exchange_code_for_token(code)
    store.save(tokens)
    print(f"Saved token to {store.path}. You're connected.")
    print("Next: python scripts/yahoo_pull_league_settings.py --league-key <key>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
