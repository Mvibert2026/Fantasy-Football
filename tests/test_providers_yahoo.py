"""
Tests for the Yahoo provider adapter (providers/yahoo.py), written before
wiring it into any script. All fetches go through an injected fake `get_fn`
returning the constructed fixtures in tests/fixtures/yahoo/ -- no Yahoo host
is contacted anywhere in this suite, consistent with this build's
constraint (no live credentials exist yet, and Yahoo hosts are not fetched
by agents per the standing block).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from providers.base import ProviderUnavailable
from providers.yahoo import YahooProvider
from providers.yahoo_oauth import TokenSet, TokenStore, YahooOAuthClient, YahooOAuthConfig

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "yahoo"


def _load(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def config():
    return YahooOAuthConfig(client_id="cid", client_secret="secret")


@pytest.fixture
def fresh_store(tmp_path):
    store = TokenStore(path=tmp_path / "token.json")
    store.save(TokenSet("AT", "RT", expires_at=time.time() + 3600))
    return store


class TestFromEnv:
    def test_raises_provider_unavailable_without_credentials(self, monkeypatch, tmp_path):
        monkeypatch.delenv("YAHOO_CLIENT_ID", raising=False)
        monkeypatch.delenv("YAHOO_CLIENT_SECRET", raising=False)
        monkeypatch.chdir(tmp_path)  # no .env here to accidentally pick up
        with pytest.raises(ProviderUnavailable) as exc:
            YahooProvider.from_env()
        assert "YAHOO_CLIENT_ID" in str(exc.value)

    def test_raises_provider_unavailable_without_prior_authorization(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("YAHOO_CLIENT_ID", "cid")
        monkeypatch.setenv("YAHOO_CLIENT_SECRET", "secret")
        empty_store = TokenStore(path=tmp_path / "no_token_here.json")
        with pytest.raises(ProviderUnavailable) as exc:
            YahooProvider.from_env(token_store=empty_store)
        assert "yahoo_connect.py" in str(exc.value)

    def test_succeeds_with_credentials_and_token(self, monkeypatch, fresh_store):
        monkeypatch.setenv("YAHOO_CLIENT_ID", "cid")
        monkeypatch.setenv("YAHOO_CLIENT_SECRET", "secret")
        provider = YahooProvider.from_env(token_store=fresh_store)
        assert provider.platform == "yahoo"

    def test_error_message_never_a_bare_traceback(self, monkeypatch, tmp_path):
        # ProviderUnavailable's whole point: honest, stated, checkable failure.
        monkeypatch.delenv("YAHOO_CLIENT_ID", raising=False)
        monkeypatch.delenv("YAHOO_CLIENT_SECRET", raising=False)
        monkeypatch.chdir(tmp_path)
        try:
            YahooProvider.from_env()
        except ProviderUnavailable as exc:
            assert ".env.example" in str(exc)
        else:
            pytest.fail("expected ProviderUnavailable")


class TestGetLeagueSettings:
    def test_returns_parsed_settings(self, config, fresh_store):
        raw = _load("league_settings_response.json")
        provider = YahooProvider(
            YahooOAuthClient(config), fresh_store, get_fn=lambda url, token: raw
        )
        settings = provider.get_league_settings("461.l.154693")
        assert settings.name == "Westwood"
        assert settings.max_teams == 10

    def test_passes_bearer_token_and_hits_settings_endpoint(self, config, fresh_store):
        calls = []

        def fake_get(url, token):
            calls.append((url, token))
            return _load("league_settings_response.json")

        provider = YahooProvider(YahooOAuthClient(config), fresh_store, get_fn=fake_get)
        provider.get_league_settings("461.l.154693")
        assert len(calls) == 1
        url, token = calls[0]
        assert "461.l.154693" in url
        assert "settings" in url
        assert token == "AT"

    def test_retries_once_after_401_with_refreshed_token(self, config, tmp_path):
        store = TokenStore(path=tmp_path / "token.json")
        store.save(TokenSet("STALE_AT", "RT1", expires_at=time.time() + 3600))

        calls = []

        def fake_get(url, token):
            calls.append(token)
            if token == "STALE_AT":
                raise PermissionError("401")
            return _load("league_settings_response.json")

        def fake_post(url, data, auth):
            from types import SimpleNamespace

            return SimpleNamespace(
                status_code=200,
                json=lambda: {"access_token": "NEW_AT", "refresh_token": "RT2", "expires_in": 3600},
                text="",
            )

        oauth_client = YahooOAuthClient(config, post_fn=fake_post)
        provider = YahooProvider(oauth_client, store, get_fn=fake_get)
        settings = provider.get_league_settings("461.l.154693")
        assert calls == ["STALE_AT", "NEW_AT"]
        assert settings.name == "Westwood"
        assert store.load().access_token == "NEW_AT"

    def test_raises_provider_unavailable_when_no_token_survives_401(self, config, tmp_path):
        store = TokenStore(path=tmp_path / "no_token.json")
        # No token saved at all -- get_valid_access_token itself will raise.
        provider = YahooProvider(
            YahooOAuthClient(config), store, get_fn=lambda *a, **k: pytest.fail("unreachable")
        )
        with pytest.raises(ProviderUnavailable):
            provider.get_league_settings("461.l.154693")


class TestGetDraftResults:
    def test_final_draft_results_not_flagged_live(self, config, fresh_store):
        raw = _load("draft_results_response.json")
        provider = YahooProvider(
            YahooOAuthClient(config), fresh_store, get_fn=lambda url, token: raw
        )
        result = provider.get_draft_results("461.l.154693")
        assert result.is_live_estimate is False
        assert len(result.picks) == 3

    def test_live_draft_picks_flagged_and_caveated(self, config, fresh_store):
        raw = _load("draft_results_response.json")
        provider = YahooProvider(
            YahooOAuthClient(config), fresh_store, get_fn=lambda url, token: raw
        )
        result = provider.get_live_draft_picks("461.l.154693")
        assert result.is_live_estimate is True
        assert result.caveat is not None
        # Never asserts reliability -- design for it, do not depend on it.
        assert "unverified" in result.caveat.lower() or "single" in result.caveat.lower()

    def test_no_pick_write_capability_exists_on_the_provider(self, config, fresh_store):
        # There is deliberately no add_pick/submit_pick/draft_player method:
        # research doc SS3.3 -- no wrapper documents a draft-pick write
        # endpoint. Asserted structurally so a future edit adding one trips
        # this test and has to justify it against that finding explicitly.
        provider = YahooProvider(YahooOAuthClient(config), fresh_store)
        write_like = [
            m
            for m in dir(provider)
            if not m.startswith("_")
            and any(k in m for k in ("draft_player", "submit_pick", "make_pick", "add_pick"))
        ]
        assert write_like == []


class TestDiscoverLeagues:
    def test_returns_raw_body_unprocessed(self, config, fresh_store):
        raw = {"fantasy_content": {"users": "whatever"}}
        provider = YahooProvider(
            YahooOAuthClient(config), fresh_store, get_fn=lambda url, token: raw
        )
        assert provider.discover_leagues() == raw
