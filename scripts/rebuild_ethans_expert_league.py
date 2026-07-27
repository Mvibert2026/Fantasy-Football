"""One-off rebuild of league 2 ("Ethan's Expert League") at teams=10.

Handoff 067, pm reply 2026-07-27: founder override, verbatim -- "Ethan's
expert league may likely only end up being 10 people, treat it as a 10
person league unless otherwise directed." The Yahoo league-settings
screenshot (`docs/screenshots/Yahoo League 2 settings.png`) DID say
"Max Teams: 12" -- that transcription was correct and is not being "fixed"
here. The founder is directing us to build for 10 real participants instead
of the platform's configured slot count, because they expect the league to
actually fill with 10. Record both facts; a future session re-reading the
screenshot should not silently revert this to 12.

Same placeholder-flagging convention already used for user_draft_slot=1
(see league_builder.create_league()'s docstring and
tests/test_league2_ethans_expert.py's module docstring): LeagueConfig has
no free-text metadata field, so the override is recorded here, in the test
docstring, and in the 067 handoff reply -- not invented as a new schema
field for a single instance.

Run once via:
    python scripts/rebuild_ethans_expert_league.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import db as dbmod  # noqa: E402
import league_builder as lb  # noqa: E402

LEAGUE2_KWARGS = dict(
    name="Ethan's Expert League (Yahoo 834236)",
    # teams=10, NOT 12. Screenshot said "Max Teams: 12" (platform slot count,
    # verified correct at transcription time). Founder override 2026-07-27:
    # build for 10 real participants until told otherwise.
    teams=10,
    starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "K": 1, "DEF": 1},
    flex_slots=1,
    flex_eligible=("RB", "WR", "TE"),
    bench=5,
    ir=1,
    user_draft_slot=1,  # PLACEHOLDER -- founder has not supplied their actual draft slot
    platform="yahoo",
    draft_type="snake",
    ppr=0.5,
    scoring_overrides={
        "interception": -1,
        "passing_yards": {"per": 25, "bonuses": []},
        "rushing_yards": {"per": 10, "bonuses": []},
        "receiving_yards": {"per": 10, "bonuses": []},
    },
    playoff_teams=4,
    playoff_weeks=(16, 17),
    league_id="ethans_expert_league",
)


def main() -> None:
    conn = dbmod.connect()
    try:
        cfg, written = lb.create_and_export_league(conn=conn, **LEAGUE2_KWARGS)
    finally:
        conn.close()
    print(f"teams={cfg.teams}")
    for p in written:
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
