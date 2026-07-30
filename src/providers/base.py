"""
Provider adapter interface (CLAUDE.md SS4: "Adapter pattern behind a generic
interface -- adding ESPN/Sleeper later = a new adapter, not a rewrite").

WHY THIS EXISTS. FR-062 asked whether a Yahoo league connection is possible.
The answer (docs/research/yahoo-espn-league-connection-2026-07-30.md,
thread 095) is yes for Yahoo (OAuth2, self-serve) and a clean, permanent no
for ESPN (no sanctioned channel; the only working mechanism -- cookie replay
-- is named and prohibited by Disney's Terms of Use SS2.B.x/SS2.A/SS3.H). This
module is the seam both live behind, so a future Sleeper adapter (its API is
public, undocumented auth needed) is a third implementation of the same
interface, not a parallel code path threaded through the app.

WHAT THIS DOES NOT DO. No network call lives here. This file is pure shape:
dataclasses mirroring the fields the research established Yahoo's API (via
yfpy's documented models, see providers/yahoo.py's module docstring for why
yfpy itself is not vendored) and ESPN's community libraries expose, plus the
ProviderUnavailable exception every adapter raises instead of crashing when
it cannot serve a request -- "unavailable, permanently and for a stated
reason," the same idiom the assistant's reasoning lane uses elsewhere in this
project, not a stack trace.

RETENTION. Nothing in this package writes to data/nfl.db. Yahoo's developer
terms reportedly require deletion of Yahoo user data not explicitly listed as
storable indefinitely within 24 hours (docs/research/...-2026-07-30.md SS6,
tagged [SNIPPET] -- never independently verified against legal.yahoo.com in
any session because Yahoo hosts are not fetched here). Until that is
resolved, "persist a league into nfl.db" is exactly the design the terms are
read to forbid. Every adapter in this package is fetch-on-demand only; see
scripts/yahoo_pull_league_settings.py for the intended call shape and
docs/decisions.md (this thread's ADR) for the full reasoning.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ProviderUnavailable(Exception):
    """Raised instead of crashing when an adapter cannot serve a request.

    Always carries a stated, checkable reason -- "no credentials configured
    (see .env.example)" or "no sanctioned API exists (Disney ToU SS2.B.x)" --
    never a bare network exception. Two flavors exist in practice:
    permanent (ESPN: no amount of retrying or configuration fixes it) and
    conditional (Yahoo: fixable by supplying credentials or re-authorizing).
    Callers should not need to inspect which; the message says so.
    """


@dataclass(frozen=True)
class Bonus:
    """A single yardage-bonus threshold: cross `target`, earn `points`.

    Field names and shape are modeled on yfpy v17.0.0's `Bonus` class
    (`points`, `target` -- verified by fetching yfpy's models.py source,
    docs/research/yahoo-espn-league-connection-2026-07-30.md SS3.1). yfpy
    itself is not a runtime dependency here (see providers/yahoo.py); this
    dataclass exists so a league's stacking bonuses -- CLAUDE.md SS7's
    Westwood table, currently transcribed from a screenshot -- can be
    represented in the same shape Yahoo's own source of truth uses, once a
    real credential lets us fetch it.
    """

    points: float
    target: float


@dataclass(frozen=True)
class StatModifier:
    """One scored stat category: its per-unit value plus any bonuses."""

    stat_id: int
    name: str
    value: float
    bonuses: List[Bonus] = field(default_factory=list)


@dataclass(frozen=True)
class RosterPositionSpec:
    position: str
    count: int
    is_starting_position: bool
    is_bench: bool


@dataclass(frozen=True)
class LeagueSettings:
    """Provider-agnostic league configuration snapshot.

    Deliberately narrower than yfpy's full `Settings` model (SS3.1 lists 30+
    attributes) -- only the fields CLAUDE.md SS7 and league_config.LeagueConfig
    actually need are surfaced as first-class; everything else survives in
    `raw` for audit, never silently dropped.
    """

    league_key: str
    name: str
    platform: str
    max_teams: int
    scoring_type: str  # e.g. "head" (head-to-head)
    num_playoff_teams: int
    playoff_start_week: int
    uses_playoff_reseeding: bool
    roster_positions: List[RosterPositionSpec]
    stat_modifiers: List[StatModifier]
    raw: dict = field(default_factory=dict)
    parse_warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DraftPick:
    pick: int
    round: int
    team_key: str
    player_key: str
    cost: Optional[float] = None  # auction only


@dataclass(frozen=True)
class DraftResult:
    """Result of a draft-results fetch.

    `is_live_estimate` distinguishes a post-draft, authoritative pull from an
    in-progress poll. The in-progress case rests on a single, undated SDK
    docstring (SS3.3 of the research doc) -- design for it, never assert it
    works. `caveat` carries that provenance forward so a caller (or the
    founder) is never left inferring reliability from the absence of a
    warning.
    """

    picks: List[DraftPick]
    is_live_estimate: bool
    caveat: Optional[str] = None


class LeagueProvider(ABC):
    """Generic interface every platform adapter implements.

    Implementations: providers/yahoo.py (real, gated on credentials),
    providers/espn.py (always raises ProviderUnavailable -- see its module
    docstring). A Sleeper adapter, if ever built, is a third class here, not
    a special case threaded through src/league_builder.py or the app.
    """

    platform: str

    @abstractmethod
    def get_league_settings(self, league_key: str) -> LeagueSettings:
        """Fetch a league's settings. Raises ProviderUnavailable if it can't."""

    @abstractmethod
    def get_draft_results(self, league_key: str) -> DraftResult:
        """Fetch completed (or in-progress, best-effort) draft picks."""
