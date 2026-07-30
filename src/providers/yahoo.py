"""
Yahoo Fantasy Sports provider adapter -- FR-062, thread 095.

Implements providers/base.py::LeagueProvider against Yahoo's Fantasy Sports
v2 REST API directly (see providers/yahoo_oauth.py's module docstring for
why `yfpy` itself is not vendored: its OAuth dependency chain fails to
build here). `.raw` on every returned object always carries the full
untouched response, because providers/mapping.py's field extraction is
best-effort and has never been checked against a live Yahoo response --
build against the documented shape, verify against the founder's real
account later, per this task's own instruction.

FAILS HONESTLY, NEVER SILENTLY. `YahooProvider.from_env()` raises
ProviderUnavailable with a stated, checkable reason (missing credentials,
missing authorization) instead of letting a bare `requests` exception or a
`KeyError` bubble up. This is the "unavailable, permanently and for a
stated reason" idiom the assistant's reasoning lane already uses elsewhere
in this project.

NO PERSISTENCE. Every method here fetches on demand and returns; nothing is
written to data/nfl.db (see providers/base.py's module docstring on the
24-hour retention clause). This file is not in the sqlite3.connect()
ingestion allowlist and does not need to be -- it never opens a connection.
"""

from __future__ import annotations

from typing import Callable, Optional

import requests

from providers.base import DraftResult, LeagueSettings, LeagueProvider, ProviderUnavailable
from providers.mapping import parse_draft_results, parse_league_settings
from providers.yahoo_oauth import (
    TokenStore,
    YahooOAuthClient,
    YahooOAuthConfig,
)

API_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"

# Injectable for tests -- see tests/test_providers_yahoo.py, which supplies a
# fake GET returning recorded/constructed fixtures instead of ever reaching
# a real Yahoo host (not fetched anywhere in this build, per instruction).
GetFn = Callable[[str, str], dict]  # (url, access_token) -> parsed JSON body


def _default_get(url: str, access_token: str) -> dict:
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"format": "json"},
        timeout=15,
    )
    if resp.status_code == 401:
        raise PermissionError("Yahoo returned 401 -- access token rejected")
    resp.raise_for_status()
    return resp.json()


class YahooProvider(LeagueProvider):
    platform = "yahoo"

    def __init__(
        self,
        oauth_client: YahooOAuthClient,
        token_store: TokenStore,
        get_fn: GetFn = _default_get,
    ):
        self._oauth = oauth_client
        self._store = token_store
        self._get = get_fn

    @classmethod
    def from_env(
        cls,
        token_store: Optional[TokenStore] = None,
        get_fn: GetFn = _default_get,
    ) -> "YahooProvider":
        """The normal entry point. Raises ProviderUnavailable, never a bare
        exception, if credentials or a prior authorization are missing --
        both are the founder's to fix (see scripts/yahoo_connect.py), not a
        bug to debug."""
        try:
            config = YahooOAuthConfig.from_env()
        except ValueError as exc:
            raise ProviderUnavailable(
                f"Yahoo provider unavailable: {exc}. This is expected until real "
                "credentials are supplied; see .env.example and the setup steps in "
                "this thread's session report."
            ) from exc
        store = token_store or TokenStore()
        if store.load() is None:
            raise ProviderUnavailable(
                "Yahoo provider unavailable: credentials are configured but no token has "
                "been authorized yet. Run scripts/yahoo_connect.py once (interactive; opens "
                "a browser) to complete the one-time OAuth authorization."
            )
        return cls(YahooOAuthClient(config), store, get_fn=get_fn)

    def _authed_get(self, url: str) -> dict:
        try:
            token = self._oauth.get_valid_access_token(self._store)
        except ValueError as exc:
            raise ProviderUnavailable(f"Yahoo provider unavailable: {exc}") from exc
        try:
            return self._get(url, token)
        except PermissionError:
            # One retry after a forced refresh -- a cached token can be
            # stale even before its recorded expiry (e.g. revoked access).
            tokens = self._store.load()
            if tokens is None:
                raise ProviderUnavailable(
                    "Yahoo provider unavailable: token rejected and no cached refresh token"
                )
            refreshed = self._oauth.refresh_access_token(tokens.refresh_token)
            self._store.save(refreshed)
            return self._get(url, refreshed.access_token)

    def get_league_settings(self, league_key: str) -> LeagueSettings:
        raw = self._authed_get(f"{API_BASE}/league/{league_key}/settings")
        return parse_league_settings(raw, league_key=league_key, platform=self.platform)

    def get_draft_results(self, league_key: str) -> DraftResult:
        raw = self._authed_get(f"{API_BASE}/league/{league_key}/draftresults")
        return parse_draft_results(raw, is_live_estimate=False)

    def discover_leagues(self) -> dict:
        """Raw response from the documented league-discovery collection
        (research doc SS2.4 step 2): `users;use_login=1/games;game_keys=nfl/leagues`.
        Returns the parsed JSON body unprocessed -- deliberately not mapped
        into a dataclass, since its only real consumer is a human reading
        `league_key`s (format `{game_key}.l.{league_id}`) off the screen to
        paste into the next call. Never fetched against a live account in
        this build; the URL shape is per-SDK-documented, not observed."""
        return self._authed_get(f"{API_BASE}/users;use_login=1/games;game_keys=nfl/leagues")

    def get_live_draft_picks(self, league_key: str) -> DraftResult:
        """Best-effort read of an in-progress draft. Design for it, do not
        depend on it -- see DraftResult.caveat and providers/mapping.py's
        module docstring on why this rests on a single source. Uses the same
        endpoint as get_draft_results(); Yahoo's own docs (offline) were
        never read to confirm a distinct in-progress shape exists."""
        raw = self._authed_get(f"{API_BASE}/league/{league_key}/draftresults")
        return parse_draft_results(raw, is_live_estimate=True)
