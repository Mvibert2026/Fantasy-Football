"""
Tests for the Yahoo OAuth2 flow (providers/yahoo_oauth.py), written before
the parts of providers/yahoo.py that depend on it.

No real HTTP call happens anywhere in this file -- every test either checks
pure string/URL construction or injects a fake `post_fn` returning a
constructed response, per this build's constraint that correctness cannot
depend on live credentials (none exist yet).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from providers.yahoo_oauth import (
    DEFAULT_REDIRECT_URI,
    TokenSet,
    TokenStore,
    YahooOAuthClient,
    YahooOAuthConfig,
)


def _fake_response(status_code=200, body=None, text=""):
    return SimpleNamespace(
        status_code=status_code,
        json=lambda: body or {},
        text=text,
    )


# ------------------------------------------------------------- config


class TestYahooOAuthConfig:
    def test_from_env_raises_clear_error_when_missing(self, monkeypatch, tmp_path):
        monkeypatch.delenv("YAHOO_CLIENT_ID", raising=False)
        monkeypatch.delenv("YAHOO_CLIENT_SECRET", raising=False)
        empty_env = tmp_path / ".env"  # doesn't exist -- loader must no-op
        with pytest.raises(ValueError) as exc:
            YahooOAuthConfig.from_env(env_path=empty_env)
        assert "YAHOO_CLIENT_ID" in str(exc.value)
        assert "YAHOO_CLIENT_SECRET" in str(exc.value)
        assert ".env.example" in str(exc.value)

    def test_from_env_reports_only_the_missing_one(self, monkeypatch, tmp_path):
        monkeypatch.setenv("YAHOO_CLIENT_ID", "abc")
        monkeypatch.delenv("YAHOO_CLIENT_SECRET", raising=False)
        with pytest.raises(ValueError) as exc:
            YahooOAuthConfig.from_env(env_path=tmp_path / ".env")
        assert "YAHOO_CLIENT_SECRET" in str(exc.value)
        assert "YAHOO_CLIENT_ID" not in str(exc.value)

    def test_from_env_succeeds_with_both_set(self, monkeypatch, tmp_path):
        monkeypatch.setenv("YAHOO_CLIENT_ID", "abc")
        monkeypatch.setenv("YAHOO_CLIENT_SECRET", "def")
        monkeypatch.delenv("YAHOO_REDIRECT_URI", raising=False)
        config = YahooOAuthConfig.from_env(env_path=tmp_path / ".env")
        assert config.client_id == "abc"
        assert config.client_secret == "def"
        assert config.redirect_uri == DEFAULT_REDIRECT_URI

    def test_from_env_reads_dotenv_file(self, monkeypatch, tmp_path):
        monkeypatch.delenv("YAHOO_CLIENT_ID", raising=False)
        monkeypatch.delenv("YAHOO_CLIENT_SECRET", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("YAHOO_CLIENT_ID=fromfile\nYAHOO_CLIENT_SECRET=alsofile\n")
        config = YahooOAuthConfig.from_env(env_path=env_file)
        assert config.client_id == "fromfile"
        assert config.client_secret == "alsofile"

    def test_real_env_var_wins_over_dotenv_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("YAHOO_CLIENT_ID", "real_env")
        monkeypatch.setenv("YAHOO_CLIENT_SECRET", "real_env_secret")
        env_file = tmp_path / ".env"
        env_file.write_text("YAHOO_CLIENT_ID=fromfile\nYAHOO_CLIENT_SECRET=alsofile\n")
        config = YahooOAuthConfig.from_env(env_path=env_file)
        assert config.client_id == "real_env"


# ------------------------------------------------------------- authorization url


class TestAuthorizationUrl:
    def test_contains_required_params(self):
        config = YahooOAuthConfig(client_id="cid", client_secret="secret")
        url = YahooOAuthClient(config).build_authorization_url()
        assert url.startswith("https://api.login.yahoo.com/oauth2/request_auth?")
        assert "client_id=cid" in url
        assert "response_type=code" in url
        assert "localhost" in url  # redirect_uri echoed


# ------------------------------------------------------------- token exchange / refresh


class TestTokenExchange:
    def test_exchange_code_returns_token_set(self):
        config = YahooOAuthConfig(client_id="cid", client_secret="secret")

        def fake_post(url, data, auth):
            assert url.endswith("/get_token")
            assert data["grant_type"] == "authorization_code"
            assert data["code"] == "verify123"
            assert auth == ("cid", "secret")
            return _fake_response(
                200, {"access_token": "AT1", "refresh_token": "RT1", "expires_in": 3600}
            )

        client = YahooOAuthClient(config, post_fn=fake_post)
        tokens = client.exchange_code_for_token("verify123")
        assert tokens.access_token == "AT1"
        assert tokens.refresh_token == "RT1"
        assert tokens.expires_at > time.time()

    def test_exchange_code_raises_on_non_200(self):
        config = YahooOAuthConfig(client_id="cid", client_secret="secret")
        client = YahooOAuthClient(
            config, post_fn=lambda *a, **k: _fake_response(400, text="bad request")
        )
        with pytest.raises(ValueError, match="400"):
            client.exchange_code_for_token("bad")

    def test_refresh_uses_refresh_token_grant(self):
        config = YahooOAuthConfig(client_id="cid", client_secret="secret")

        def fake_post(url, data, auth):
            assert data["grant_type"] == "refresh_token"
            assert data["refresh_token"] == "RT1"
            return _fake_response(
                200, {"access_token": "AT2", "refresh_token": "RT2", "expires_in": 3600}
            )

        client = YahooOAuthClient(config, post_fn=fake_post)
        tokens = client.refresh_access_token("RT1")
        assert tokens.access_token == "AT2"


# ------------------------------------------------------------- TokenSet


class TestTokenSet:
    def test_not_expired_when_fresh(self):
        t = TokenSet("AT", "RT", expires_at=time.time() + 3600)
        assert t.is_expired is False

    def test_expired_when_past(self):
        t = TokenSet("AT", "RT", expires_at=time.time() - 10)
        assert t.is_expired is True

    def test_expired_within_safety_margin(self):
        # 30s left is inside the 60s margin -- must be treated as expired
        # so a request in flight doesn't cross the real boundary.
        t = TokenSet("AT", "RT", expires_at=time.time() + 30)
        assert t.is_expired is True


# ------------------------------------------------------------- TokenStore


class TestTokenStore:
    def test_load_returns_none_when_no_file(self, tmp_path):
        store = TokenStore(path=tmp_path / "nope.json")
        assert store.load() is None

    def test_save_then_load_round_trips(self, tmp_path):
        store = TokenStore(path=tmp_path / "token.json")
        t = TokenSet("AT", "RT", expires_at=1234.0)
        store.save(t)
        loaded = store.load()
        assert loaded.access_token == "AT"
        assert loaded.refresh_token == "RT"
        assert loaded.expires_at == 1234.0

    def test_load_returns_none_on_corrupt_file(self, tmp_path):
        path = tmp_path / "token.json"
        path.write_text("not json")
        store = TokenStore(path=path)
        assert store.load() is None

    def test_save_creates_parent_directory(self, tmp_path):
        store = TokenStore(path=tmp_path / "nested" / "dir" / "token.json")
        store.save(TokenSet("AT", "RT", expires_at=1.0))
        assert store.path.exists()


# ------------------------------------------------------------- get_valid_access_token


class TestGetValidAccessToken:
    def test_raises_when_never_authorized(self, tmp_path):
        config = YahooOAuthConfig(client_id="cid", client_secret="secret")
        client = YahooOAuthClient(config)
        store = TokenStore(path=tmp_path / "token.json")
        with pytest.raises(ValueError, match="yahoo_connect"):
            client.get_valid_access_token(store)

    def test_returns_cached_token_when_fresh(self, tmp_path):
        config = YahooOAuthConfig(client_id="cid", client_secret="secret")
        client = YahooOAuthClient(config, post_fn=lambda *a, **k: pytest.fail("should not refresh"))
        store = TokenStore(path=tmp_path / "token.json")
        store.save(TokenSet("AT", "RT", expires_at=time.time() + 3600))
        assert client.get_valid_access_token(store) == "AT"

    def test_refreshes_and_saves_when_expired(self, tmp_path):
        config = YahooOAuthConfig(client_id="cid", client_secret="secret")

        def fake_post(url, data, auth):
            return _fake_response(
                200, {"access_token": "NEW_AT", "refresh_token": "NEW_RT", "expires_in": 3600}
            )

        client = YahooOAuthClient(config, post_fn=fake_post)
        store = TokenStore(path=tmp_path / "token.json")
        store.save(TokenSet("OLD_AT", "OLD_RT", expires_at=time.time() - 100))
        token = client.get_valid_access_token(store)
        assert token == "NEW_AT"
        assert store.load().access_token == "NEW_AT"
