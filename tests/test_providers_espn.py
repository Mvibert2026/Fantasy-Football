"""
ESPN adapter: always ProviderUnavailable, permanently. See providers/espn.py's
module docstring for the terms basis (Disney ToU SS2.B.x/SS2.A/SS3.H).
"""

from __future__ import annotations

import pytest

from providers.base import LeagueProvider, ProviderUnavailable
from providers.espn import ESPNProvider


def test_espn_provider_implements_the_interface():
    assert isinstance(ESPNProvider(), LeagueProvider)


def test_get_league_settings_always_raises():
    with pytest.raises(ProviderUnavailable) as exc:
        ESPNProvider().get_league_settings("123456")
    assert "permanently" in str(exc.value)
    assert "Disney" in str(exc.value)


def test_get_draft_results_always_raises():
    with pytest.raises(ProviderUnavailable):
        ESPNProvider().get_draft_results("123456")


def test_reason_names_the_specific_clauses():
    with pytest.raises(ProviderUnavailable) as exc:
        ESPNProvider().get_league_settings("123456")
    msg = str(exc.value)
    assert "2.B.x" in msg
    assert "2.A" in msg
    assert "3.H" in msg
