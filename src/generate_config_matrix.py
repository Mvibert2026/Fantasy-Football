"""
Multi-config board/VBD matrix (ADR-047) -- first stage of the global
(multi-format) work. Generates board.json + league.json for every
combination of:

  - team count: 8, 10, 12, 14
  - scoring: standard (0 PPR), half (0.5 PPR), full (1.0 PPR) -- reception
    value ONLY. All other scoring (yardage bonuses, TD values, INT, defense)
    is held at this project's existing LEAGUE ruleset (scoring.py), which
    also happens to match ESPN's confirmed platform defaults exactly (same
    +1/+1.5/+2 bonus tiers at the same 100/150/200/300/350/400 thresholds) --
    see ADR-047. A genuinely platform-accurate bonus structure for Yahoo
    (unconfirmed) or NFL.com/Sleeper (unconfirmed roster AND scoring) is
    future work, not guessed here.
  - roster shape: ESPN-default, Yahoo-default -- the two platforms whose
    roster structure the user's researcher confirmed on 2026-07-26.
    NFL.com (FLEX is W/R only, no TE -- a real, distinct shape) and Sleeper
    (nothing platform-confirmed) are DEFERRED, not guessed at.

24 configs total (4 team counts x 3 scoring x 2 roster shapes).

BOARD-ONLY AT THIS STAGE. `export_contract.write_all` also writes
availability.json and does not crash without a availability CSV (it writes
empty by_player/by_tier -- the same "not yet run for this league" state
every fresh non-primary league starts in, not special-cased here). No
Monte Carlo simulation runs for these 24 configs, and strategies.json is not
generated at all. Both are materially more expensive and explicitly out of
scope for this pass -- see ADR-047 and status.md.
"""

from __future__ import annotations

import copy
from typing import Dict, List

import db as dbmod
import export_contract as ec
import league_config as lc
from scoring import LEAGUE

TEAM_COUNTS = (8, 10, 12, 14)
SCORING_VARIANTS: Dict[str, float] = {"standard": 0.0, "half": 0.5, "full": 1.0}

# Platform defaults supplied 2026-07-26 (researcher pass). Roster VERIFIED for
# both; ESPN scoring unverified (bot-detection blocked the fetch), Yahoo
# scoring verified half-PPR -- both are superseded here anyway by the
# explicit standard/half/full scoring axis, which is the point of the matrix.
ROSTER_SHAPES: Dict[str, dict] = {
    "espn": dict(
        starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DEF": 1, "K": 1},
        flex_slots=1, flex_eligible=("RB", "WR", "TE"), bench=7, ir=1,
    ),
    "yahoo": dict(
        # FLEX is RB/WR ONLY -- no TE. Confirmed, not the ESPN-style default;
        # hardcoding RB/WR/TE here would mismodel this platform (the same
        # warning the researcher gave for NFL.com's W/R-only flex, which
        # applies here too, just for a different platform).
        starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DEF": 1, "K": 1},
        flex_slots=1, flex_eligible=("RB", "WR"), bench=5, ir=1,
    ),
}


def scoring_variant(ppr: float) -> dict:
    cfg = copy.deepcopy(LEAGUE)
    cfg["offense"]["receptions"] = ppr
    return cfg


def build_configs() -> List[lc.LeagueConfig]:
    configs = []
    for platform, shape in ROSTER_SHAPES.items():
        for teams in TEAM_COUNTS:
            for scoring_name, ppr in SCORING_VARIANTS.items():
                league_id = f"{platform}_{teams}_{scoring_name}"
                cfg = lc.LeagueConfig(
                    league_id=league_id,
                    name=f"{platform.upper()}-default, {teams} teams, {scoring_name} scoring",
                    platform=platform,
                    teams=teams,
                    scoring=scoring_variant(ppr),
                    starters=dict(shape["starters"]),
                    flex_slots=shape["flex_slots"],
                    flex_eligible=shape["flex_eligible"],
                    bench=shape["bench"],
                    ir=shape["ir"],
                    user_draft_slot=max(1, teams // 2),
                    draft_type="snake",
                )
                configs.append(cfg)
    return configs


def generate_all(conn=None) -> List[str]:
    """Save every config to data/leagues/ and export board.json/league.json
    (+ an empty-content availability.json) for each. Returns the list of
    league_ids written. ~7s per config per the primary/Yahoo-mock timing
    measurements in data-contract.md -- ~24 x 7s = ~3 minutes total."""
    own_conn = conn is None
    conn = conn or dbmod.connect()
    written_ids = []
    try:
        for cfg in build_configs():
            cfg.save()
            out_dir = ec.export_dir_for(cfg.league_id)
            ec.write_all(out_dir, conn, cfg=cfg)
            written_ids.append(cfg.league_id)
    finally:
        if own_conn:
            conn.close()
    return written_ids


def main() -> None:
    written = generate_all()
    print(f"generated {len(written)} configs:")
    for league_id in written:
        print(f"  {league_id}")


if __name__ == "__main__":
    main()
