"""Contract test for docs/handoffs/ bug (2026-07-29): the founder selected
"Ethan's Expert League" on the live site and got a load failure, because
`data/export/ethans_expert_league/` carried only 4 of the 6 artifacts the
frontend's loader (`frontend/ui/data/load.ts`) requires unconditionally for
every non-primary league: board/availability/league/glossary/nulls/opponents
(ADR-041). Two artifacts are genuinely, structurally optional and are NOT
asserted here:

  - rosters.json (contract 1.8.0+) -- `load.ts`'s `fetchRostersOrNull` treats
    a 404 as "this league predates the artifact", not a load error.
  - strategies.json (Monte Carlo) -- `load.ts` only fetches it when the
    league's `_leagues.json` manifest entry lists it at all
    (`hasStrategies`), and `yahoo_standard_mock` is the real, on-disk proof
    that its absence is handled gracefully, not a bug.

This test reads `data/export/` directly (no `nfl.db` needed) so it runs even
when the DB isn't available, and it is a pure filesystem/contract assertion,
not analysis code -- no `sqlite3.connect` here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

EXPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "export"

# The six artifacts ADR-041 requires in every non-primary league's export
# directory, and that frontend/ui/data/load.ts's `leagueIdsOf` fetches and
# league_id-checks unconditionally (rosters/strategies are conditional,
# see module docstring).
REQUIRED_PER_LEAGUE_ARTIFACTS = {
    "board.json", "availability.json", "league.json",
    "glossary.json", "nulls.json", "opponents.json",
}


def _league_dirs() -> list[Path]:
    if not EXPORT_DIR.exists():
        return []
    return sorted(p for p in EXPORT_DIR.iterdir() if p.is_dir())


@pytest.mark.parametrize(
    "league_dir", _league_dirs(), ids=lambda p: p.name,
)
def test_every_non_primary_league_export_has_required_artifact_set(league_dir):
    present = {p.name for p in league_dir.iterdir() if p.suffix == ".json"}
    missing = REQUIRED_PER_LEAGUE_ARTIFACTS - present
    assert not missing, (
        f"data/export/{league_dir.name}/ is missing {sorted(missing)} -- the frontend "
        f"loader (frontend/ui/data/load.ts) requires all of "
        f"{sorted(REQUIRED_PER_LEAGUE_ARTIFACTS)} unconditionally for a non-primary "
        f"league (ADR-041). This is the exact failure class the founder hit switching "
        f"to Ethan's Expert League on 2026-07-29."
    )


def test_at_least_one_non_primary_league_dir_exists():
    """A guard against this file silently testing nothing: if every league
    directory were removed, the parametrized test above would report zero
    cases and pass vacuously."""
    assert _league_dirs(), "expected at least one data/export/<league_id>/ directory"


def test_primary_league_export_has_the_full_artifact_set():
    """The primary/default league lives at the unprefixed data/export/ path
    (ADR-041), not a subdirectory, and additionally carries strategies.json
    (Monte Carlo has been run for it) plus rosters.json -- both required
    here since the primary league is never in the "not yet run" state the
    per-league test above allows for."""
    present = {p.name for p in EXPORT_DIR.iterdir() if p.suffix == ".json"}
    required = REQUIRED_PER_LEAGUE_ARTIFACTS | {"rosters.json", "strategies.json"}
    missing = required - present
    assert not missing, f"data/export/ is missing {sorted(missing)}"


def test_strategies_json_contract_version_matches_export_contract():
    """Bug 2 (docs/handoffs/042, docs/backlog-triage-2026-07-29.md):
    strategies.json must not be stamped with a stale contract version -- the
    app's own version banner flags this drift to the founder directly."""
    import json

    import export_contract as ec

    strategies_path = EXPORT_DIR / "strategies.json"
    if not strategies_path.exists():
        pytest.skip("strategies.json not generated")
    data = json.loads(strategies_path.read_text(encoding="utf-8"))
    assert data["contract_version"] == ec.CONTRACT_VERSION, (
        f"strategies.json is stamped {data['contract_version']!r} but "
        f"CONTRACT_VERSION is {ec.CONTRACT_VERSION!r} -- re-run "
        f"src/export_strategies.py and commit the regenerated file."
    )
