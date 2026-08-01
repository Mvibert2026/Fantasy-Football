"""The scoring layer: stat lines → points under any league config. Pure
arithmetic on stored columns — this module contains no fit call by
construction, which is the whole portability claim (ADR-069 §3).

`score_stat_lines` is a thin, named wrapper over the component model's own
`score_components`, so there is exactly one scoring implementation in the
project and this layer cannot drift from it.

Bonus thresholds: probabilities are stored per (family, threshold) as
`p_<fam>_<t>` columns. Any config whose thresholds are a subset of the modelled
families (rec/rush 100/150/200, pass 300/350/400) re-scores with zero fitting.
A config naming an unmodelled threshold needs its own exceedance curve — a
stat-data fit, not a league fit — and this function REFUSES rather than
silently dropping the bonus.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from ..components.pos_model import LEAGUE_SCORING, score_components

#: CLAUDE.md §7 — Westwood, half-PPR, stacking yardage bonuses.
WESTWOOD = dict(LEAGUE_SCORING)

#: A generic 12-team full-PPR room: the ruleset consensus boards are built for.
FULL_PPR_NO_BONUS: Dict = dict(
    per_reception=1.0,
    rec_yards_per_point=10.0, rec_td=6.0,
    rush_yards_per_point=10.0, rush_td=6.0,
    pass_yards_per_point=25.0, pass_td=4.0, interception=-2.0,
    fumble_lost=-2.0,
    bonuses={},
)

#: Standard (no PPR), 6-point passing TDs.
STANDARD_6PT_PASS: Dict = dict(
    per_reception=0.0,
    rec_yards_per_point=10.0, rec_td=6.0,
    rush_yards_per_point=10.0, rush_td=6.0,
    pass_yards_per_point=25.0, pass_td=6.0, interception=-2.0,
    fumble_lost=-2.0,
    bonuses={},
)

CONFIGS = {"westwood": WESTWOOD, "full_ppr": FULL_PPR_NO_BONUS,
           "std_6pt_pass": STANDARD_6PT_PASS}

_MODELLED = {"rec": (100, 150, 200), "rush": (100, 150, 200),
             "pass": (300, 350, 400)}


def score_stat_lines(stat_lines: pd.DataFrame, scoring: Dict) -> np.ndarray:
    for fam, table in scoring.get("bonuses", {}).items():
        for t, _b in table:
            if t not in _MODELLED.get(fam, ()):
                raise ValueError(
                    f"threshold {fam}@{t} has no stored exceedance curve; "
                    f"fit one from stat data before scoring this config")
    return score_components(stat_lines, scoring, bonuses=True)


def rank_within_position(stat_lines: pd.DataFrame, scoring: Dict
                         ) -> pd.DataFrame:
    """The v2 ordering path: points from stat lines under `scoring`, ranked
    within (season, position). Deterministic tie-break by player_id. No
    consensus column is read — there is none in the stat-line contract."""
    d = stat_lines.copy()
    d["points_cfg"] = score_stat_lines(d, scoring)
    d = d.sort_values(["season", "position", "points_cfg", "player_id"],
                      ascending=[True, True, False, True], kind="stable")
    d["pos_rank_cfg"] = d.groupby(["season", "position"]).cumcount() + 1
    return d
