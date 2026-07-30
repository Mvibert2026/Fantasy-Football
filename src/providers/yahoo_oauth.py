"""
Yahoo OAuth2 (Installed Application) flow -- FR-062, thread 095.

WHY IMPLEMENTED DIRECTLY, NOT VIA `yfpy`. `yfpy` is the SDK the research doc
(docs/research/yahoo-espn-league-connection-2026-07-30.md SS2/SS3) verified
the shapes against, but `yfpy`'s OAuth dependency chain (`yahoo-oauth` ->
`myql`, `rauth`) failed to build in this environment: `pip install yfpy`
raised `AttributeError: install_layout` from `myql`'s and `rauth`'s
`setup.py` under current `setuptools` -- both packages are unmaintained
legacy Yahoo Query Language (YQL) helpers this project has no use for (YQL
was retired years ago; the Fantasy Sports v2 REST API this module targets
does not need it). Per CLAUDE.md's "a source swap is not a substitution"
guardrail, that was verified by running the install, not assumed from a
docstring. This module talks to Yahoo's OAuth2 endpoints directly with
`requests` (already a clean, maintained dependency) and mirrors the request
shape documented across five independent SDKs (redirect URI
`https://localhost:<port>`, "Installed Application" type, Basic-auth token
exchange) rather than vendoring a library that does not currently install.

FLOW (per yfpy's README, [VERIFIED] in the research doc SS2.2):
1. Register an app at https://developer.yahoo.com/apps/create/ as an
   "Installed Application", redirect URI `https://localhost:<port>`,
   API Permissions -> Fantasy Sports -> Read. Get a Client ID + Secret.
2. `build_authorization_url()` sends the user to Yahoo's consent screen.
3. Yahoo displays a verification code on-screen for the user to copy back
   (no listening server needed -- this is Yahoo's own documented UX for the
   Installed Application type, not a design choice made here).
4. `exchange_code_for_token()` trades that code for an access + refresh
   token pair.
5. `refresh_access_token()` mints a new access token when the old one
   expires (reported hourly, [SECONDARY], SS2.2).

RETENTION. `TokenStore` persists exactly the access token, refresh token,
and expiry -- nothing about league content. That matches the research doc's
[SNIPPET]-tagged reading of what's storable indefinitely (GUID + token
value). If that reading turns out wrong, this is the one place to fix.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import requests

AUTHORIZATION_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
DEFAULT_REDIRECT_URI = "https://localhost:8080"

# Not committed (.gitignore); the only Yahoo-derived data persisted anywhere
# in this project, per this module's docstring.
DEFAULT_TOKEN_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / ".yahoo_token.json"
)


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (stdlib only -- no python-dotenv dependency).

    Only fills variables not already set in the environment, so a real
    environment variable (CI, shell export) always wins over the file.
    Silently no-ops if the file doesn't exist -- most sessions won't have one.
    """
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class YahooOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str = DEFAULT_REDIRECT_URI

    @classmethod
    def from_env(cls, env_path: Optional[Path] = None) -> "YahooOAuthConfig":
        """Load from environment / `.env`. Raises ValueError, not KeyError,
        with a message naming exactly what's missing and where to put it --
        callers (providers/yahoo.py) wrap this into ProviderUnavailable."""
        _load_dotenv(
            env_path or Path(__file__).resolve().parent.parent.parent / ".env"
        )
        client_id = os.environ.get("YAHOO_CLIENT_ID", "").strip()
        client_secret = os.environ.get("YAHOO_CLIENT_SECRET", "").strip()
        redirect_uri = os.environ.get("YAHOO_REDIRECT_URI", "").strip() or DEFAULT_REDIRECT_URI
        missing = [
            name
            for name, val in (
                ("YAHOO_CLIENT_ID", client_id),
                ("YAHOO_CLIENT_SECRET", client_secret),
            )
            if not val
        ]
        if missing:
            raise ValueError(
                f"missing {', '.join(missing)} -- set in .env (see .env.example), "
                "not committed, per CLAUDE.md SS10"
            )
        return cls(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)


@dataclass
class TokenSet:
    access_token: str
    refresh_token: str
    expires_at: float  # unix timestamp

    @property
    def is_expired(self) -> bool:
        # 60s safety margin so a request in flight doesn't cross the boundary.
        return time.time() >= (self.expires_at - 60)

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TokenSet":
        return cls(
            access_token=d["access_token"],
            refresh_token=d["refresh_token"],
            expires_at=d["expires_at"],
        )


class TokenStore:
    """File-backed token cache. See module docstring re: retention."""

    def __init__(self, path: Path = DEFAULT_TOKEN_PATH):
        self.path = path

    def load(self) -> Optional[TokenSet]:
        if not self.path.exists():
            return None
        try:
            return TokenSet.from_dict(json.loads(self.path.read_text()))
        except (json.JSONDecodeError, KeyError):
            return None

    def save(self, tokens: TokenSet) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(tokens.to_dict(), indent=2))
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass  # best-effort on platforms without POSIX perms


# Injectable so tests never perform a real HTTP call -- see
# tests/test_providers_yahoo_oauth.py, which supplies a fake transport
# returning fixture responses instead of hitting api.login.yahoo.com.
PostFn = Callable[[str, dict, tuple], requests.Response]


def _default_post(url: str, data: dict, auth: tuple) -> requests.Response:
    return requests.post(url, data=data, auth=auth, timeout=15)


class YahooOAuthClient:
    def __init__(self, config: YahooOAuthConfig, post_fn: PostFn = _default_post):
        self.config = config
        self._post = post_fn

    def build_authorization_url(self) -> str:
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "language": "en-us",
        }
        return f"{AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, verification_code: str) -> TokenSet:
        resp = self._post(
            TOKEN_URL,
            {
                "grant_type": "authorization_code",
                "redirect_uri": self.config.redirect_uri,
                "code": verification_code,
            },
            (self.config.client_id, self.config.client_secret),
        )
        return self._parse_token_response(resp)

    def refresh_access_token(self, refresh_token: str) -> TokenSet:
        resp = self._post(
            TOKEN_URL,
            {
                "grant_type": "refresh_token",
                "redirect_uri": self.config.redirect_uri,
                "refresh_token": refresh_token,
            },
            (self.config.client_id, self.config.client_secret),
        )
        return self._parse_token_response(resp)

    @staticmethod
    def _parse_token_response(resp: requests.Response) -> TokenSet:
        if resp.status_code != 200:
            raise ValueError(
                f"Yahoo token endpoint returned {resp.status_code}: {resp.text[:500]}"
            )
        body = resp.json()
        return TokenSet(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
            expires_at=time.time() + float(body.get("expires_in", 3600)),
        )

    def get_valid_access_token(self, store: TokenStore) -> str:
        """The one call sites should normally use: returns a fresh access
        token, refreshing and re-saving to `store` if the cached one has
        expired. Raises ValueError if no token has ever been obtained --
        that first run must go through the interactive authorize step
        (scripts/yahoo_connect.py)."""
        tokens = store.load()
        if tokens is None:
            raise ValueError(
                "no cached Yahoo token -- run scripts/yahoo_connect.py once to authorize"
            )
        if tokens.is_expired:
            tokens = self.refresh_access_token(tokens.refresh_token)
            store.save(tokens)
        return tokens.access_token
