"""
ESPN provider adapter -- exists to complete the seam, not to work.

docs/research/yahoo-espn-league-connection-2026-07-30.md SS4: ESPN has no
public API, no developer program, no OAuth. The only working mechanism
community libraries use is copying `espn_s2`/`SWID` cookies out of a
logged-in browser by hand, and Disney's Terms of Use SS2.B.x expressly
prohibits automated access "including ... for the purposes of creating or
developing any AI Tool" -- this project is exactly that. SS2.A additionally
excludes AI training/use from the personal-use license, and SS3.H excludes
commercial/business-related use. There is no sanctioned channel to fall
back to if the forbidden one is avoided, unlike Yahoo where OAuth is the
sanctioned channel.

This class exists only so `LeagueProvider` has a second implementation on
record and any call site written against the interface (rather than against
`YahooProvider` directly) is honest about ESPN's status instead of silently
missing a branch. It always raises ProviderUnavailable -- permanently, not
conditionally like Yahoo's missing-credentials case. If a league is on
ESPN, its settings are manual entry (CLAUDE.md SS7's existing pattern)
unless the founder decides otherwise, which is his call, not this code's.
"""

from __future__ import annotations

from providers.base import DraftResult, LeagueSettings, LeagueProvider, ProviderUnavailable

_REASON = (
    "ESPN is unavailable, permanently: no public API or developer program exists. "
    "The only working mechanism (espn_s2/SWID cookie replay) is named and prohibited by "
    "Disney's Terms of Use SS2.B.x (automated access, expressly including AI tools), SS2.A "
    "(excludes AI use from the personal-use license), and SS3.H (excludes commercial use). "
    "See docs/research/yahoo-espn-league-connection-2026-07-30.md SS4. "
    "If a league is on ESPN, enter its settings by hand."
)


class ESPNProvider(LeagueProvider):
    platform = "espn"

    def get_league_settings(self, league_key: str) -> LeagueSettings:
        raise ProviderUnavailable(_REASON)

    def get_draft_results(self, league_key: str) -> DraftResult:
        raise ProviderUnavailable(_REASON)
