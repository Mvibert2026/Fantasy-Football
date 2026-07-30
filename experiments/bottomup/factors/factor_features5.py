"""Factor batch 5 features -- pass-catcher opportunity.

Design: `docs/ranking/factor-batch-5-precommit.md`, committed `c857c67` BEFORE
any arm was fitted. Wraps `factor_features3.build_factor3_features` and only ever
APPENDS columns, so batches 1-3 all keep reproducing bit for bit and every
batch-5 arm differs from its primary by exactly the block it declares.

TWO BLOCKS.

  R  ROUTES (WR, TE, RB)  `tprr_w`, `rpg_w`, `fdrr_w`, `routes_known` -- route
     participation, the input `CLAUDE.md` §5 lists as a known gap and which
     batch 2 §7 had to refuse a sentence about because "route participation is
     not in `nfl.db` at all". That sentence is wrong: it is derivable, as a
     LABELLED PROXY, from `participation.offense_players`, a table that has been
     sitting in the database unused since ingest.

     THE PROXY, AND ITS THREE NAMED DEPARTURES FROM A CHARTED ROUTE COUNT:
       1. on the field for a dropback != ran a route. A back kept in to block is
          counted. Worst at RB, best at WR -- and that is the direction that
          would make the RB cell look better than it is.
       2. the denominator is inflated ~10-20%: `pass = 1` takes in sacks,
          scrambles and penalty-wiped plays, and our `pbp` has no `season_type`
          column so the postseason is in (the same condition batch 3 accepted
          for `expl10`). Level, not ordering, and not look-ahead.
       3. `participation.offense_positions` is NULL throughout, so position comes
          from the panel. Only universe positions are ever computed.

  D  RECEIVING FIRST DOWNS (WR, TE, RB)  `fd_pg_w`, `fdpt_w`, `fd_known` --
     from `ff_opportunity.rec_first_down`. The dispatch pointed at
     `pbp.first_down_pass`; THAT COLUMN DOES NOT EXIST in this database's `pbp`
     (25 columns, and no `ydstogo` either, so it cannot be derived).

     Block D ships NO CONTROL ARM and the justification is a measurement, not a
     convenience: coverage is CONSTANT AT 1.000 on the graded population
     (missing rate 0.0000 at WR n=2,294, TE n=1,037, RB n=1,102, every season
     2009-2024, players with >=15 targets). A zero-variance control cannot carry
     an effect and would consume campaign m for nothing. Block R, whose flag is
     not constant, keeps three controls.

WHY THIS MODULE HOLDS ITS OWN DATA GATE INSTEAD OF EXTENDING `SeasonPanel`.
Three other factor agents are working the same checkout. Adding fields to a
shared dataclass is how two agents silently overwrite each other. `_Gate` below
reproduces `SeasonPanel`'s semantics exactly -- refuses any cutoff >= the sealed
holdout, asserts `max(season) <= cutoff` on the way out, and logs into the
panel's OWN `access_log` under the `feature` tag. Consequence, and it is the
strong one: every batch-5 arm can be PROVEN to have made zero season-N proxy
reads, because `allow_preseason_proxy` stays False and `WalkForward.run` raises
on any violation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from experiments.bottomup.components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, CutoffViolation, HoldoutViolation, SeasonPanel,
)
from experiments.bottomup.components.pos_features import LAG_WEIGHTS, N_LAGS
from experiments.bottomup.factors.factor_features3 import build_factor3_features

#: Empirical-Bayes shrinkage for the two per-route rates, in units of routes.
#: FIXED A PRIORI at 100 -- a few games of a rotational receiver -- and never
#: tuned against any result. Same discipline as batch 3's EXPL_K0 = 50 carries.
TPRR_K0 = 100.0

#: Empirical-Bayes shrinkage for first downs per target, in units of targets.
#: FIXED A PRIORI at 20, just above the WR/TE universe's own 15-target bar.
FDPT_K0 = 20.0

#: First season with route participation. Measured, not assumed: full 11-man
#: offensive personnel on every joined pass play, 2016-2025.
ROUTES_FIRST_SEASON = 2016


# ---------------------------------------------------------------- the gate
class _Gate:
    """The same contract as `SeasonPanel.before()`, for the two batch-5 sources.

    Loaded once per process. Every read is gated on the sealed holdout, asserted
    against its own cutoff on the way out, and logged onto the panel's access log
    as a `feature` read -- never as a `proxy`, because neither source touches
    season N.
    """

    def __init__(self, db_path: Path = DEFAULT_DB) -> None:
        self._routes = _load_routes(db_path)
        self._fd = _load_first_downs(db_path)

    @staticmethod
    def _check(cutoff: int) -> None:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")

    def routes_before(self, panel: SeasonPanel, cutoff: int) -> pd.DataFrame:
        self._check(cutoff)
        out = self._routes[self._routes["season"] <= cutoff]
        if len(out) and int(out["season"].max()) > cutoff:
            raise CutoffViolation("routes cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return out

    def fd_before(self, panel: SeasonPanel, cutoff: int) -> pd.DataFrame:
        self._check(cutoff)
        out = self._fd[self._fd["season"] <= cutoff]
        if len(out) and int(out["season"].max()) > cutoff:
            raise CutoffViolation("first-down cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return out


_GATE: Optional[_Gate] = None


def gate(db_path: Path = DEFAULT_DB) -> _Gate:
    global _GATE
    if _GATE is None:
        _GATE = _Gate(db_path)
    return _GATE


# ---------------------------------------------------------------- loaders
_ROUTE_SQL = """
SELECT p.season AS season, p.offense_players AS offense_players
FROM participation p
JOIN pbp b ON p.nflverse_game_id = b.game_id AND p.play_id = b.play_id
WHERE b.pass = 1 AND p.offense_players IS NOT NULL AND p.offense_players <> ''
  AND p.season < ?
"""


def _load_routes(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Per (player, season): the number of dropbacks he was on the field for.

    A PROXY for routes run, labelled as one everywhere it surfaces. The three
    departures from a charted count are in the module docstring and in
    `docs/ranking/factor-batch-5-precommit.md` §4; none of them was discovered
    after a result was seen.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(_ROUTE_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if len(d) and (d["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("participation holdout rows leaked past the SQL gate")
    if not len(d):
        return pd.DataFrame(columns=["season", "player_id", "routes"])
    d["player_id"] = d["offense_players"].str.split(";")
    d = d[["season", "player_id"]].explode("player_id")
    d = d[d["player_id"].astype(str).str.len() > 0]
    out = (d.groupby(["season", "player_id"], as_index=False).size()
             .rename(columns={"size": "routes"}))
    out["routes"] = out["routes"].astype(float)
    return out


_FD_SQL = """
SELECT CAST(season AS INTEGER) AS season, player_id,
       SUM(rec_first_down) AS rec_fd, SUM(rec_attempt) AS fo_targets
FROM ff_opportunity
WHERE week <= 18 AND player_id IS NOT NULL AND player_id <> ''
  AND CAST(season AS INTEGER) < ?
GROUP BY CAST(season AS INTEGER), player_id
"""


def _load_first_downs(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Per (player, season): receiving first downs and the ffopportunity target
    count they were earned on. `week <= 18` keeps it regular season, which is a
    real difference from the route proxy's denominator and is stated rather than
    smoothed over."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        d = pd.read_sql_query(_FD_SQL, conn, params=(HOLDOUT_SEASON,))
    finally:
        conn.close()
    if len(d) and (d["season"] >= HOLDOUT_SEASON).any():
        raise HoldoutViolation("ff_opportunity holdout rows leaked past the SQL gate")
    return d


# ---------------------------------------------------------------- helpers
def _median_fill(v: np.ndarray) -> np.ndarray:
    """Unknown -> the median of what IS known. Never 0: a zero is a claim about
    the player, a median is an admission that we do not know. Batch 3's rule."""
    v = np.asarray(v, dtype=float)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
    return np.where(np.isfinite(v), v, med)


def _lag_weights(f: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """The SAME recency weighting `pos_features.build_features` already applies:
    LAG_WEIGHTS scaled by the share of each season the player was available for.
    Reused rather than re-parameterised -- no new decay knob is introduced."""
    n = len(f)
    w = np.zeros((n, N_LAGS))
    for k in range(1, N_LAGS + 1):
        gs = np.asarray(f.get(f"gshare_{k}", pd.Series(np.zeros(n))), dtype=float)
        w[:, k - 1] = LAG_WEIGHTS[k - 1] * np.minimum(np.nan_to_num(gs), 1.0)
    return w, w.sum(axis=1)


def _weighted_rate(f: pd.DataFrame, num: Dict[int, np.ndarray],
                   den: Dict[int, np.ndarray], k0: float,
                   ) -> Tuple[np.ndarray, np.ndarray]:
    """Lag-weighted numerator and denominator, then empirical-Bayes shrunk to the
    pooled rate over the same window. Returns (rate, denominator_total)."""
    n = len(f)
    a = np.zeros(n)
    b = np.zeros(n)
    for k in range(1, N_LAGS + 1):
        a += LAG_WEIGHTS[k - 1] * num[k]
        b += LAG_WEIGHTS[k - 1] * den[k]
    pooled = float(a.sum() / b.sum()) if b.sum() > 0 else 0.0
    rate = (a + k0 * pooled) / (b + k0)
    return rate, b


def _per_game(f: pd.DataFrame, val: Dict[int, np.ndarray]) -> np.ndarray:
    """Lag-weighted per-game rate, identical in shape to `build_features.wavg`."""
    w, wsum = _lag_weights(f)
    n = len(f)
    num = np.zeros(n)
    for k in range(1, N_LAGS + 1):
        g = np.asarray(f.get(f"games_{k}", pd.Series(np.zeros(n))), dtype=float)
        g = np.where(g > 0, g, np.nan)
        num += w[:, k - 1] * np.nan_to_num(val[k] / g, nan=0.0)
    return np.where(wsum > 0, num / np.where(wsum > 0, wsum, 1.0), np.nan)


def _lag_map(src: pd.DataFrame, f: pd.DataFrame, target_season: int, col: str
             ) -> Dict[int, np.ndarray]:
    """`col` per lag season, 0 where the player has no row that year."""
    out: Dict[int, np.ndarray] = {}
    pid = f["player_id"]
    for k in range(1, N_LAGS + 1):
        lag = src[src["season"] == target_season - k]
        if len(lag):
            s = lag.drop_duplicates("player_id").set_index("player_id")[col]
            out[k] = np.asarray(pid.map(s).astype(float).fillna(0.0))
        else:
            out[k] = np.zeros(len(f))
    return out


# ----------------------------------------------------------------- block R
def _routes_block(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                  ) -> Dict[str, np.ndarray]:
    g = gate()
    r = g.routes_before(panel, target_season - 1)
    fd = g.fd_before(panel, target_season - 1)
    n = len(f)
    if not len(r):
        z = np.zeros(n)
        return {"tprr_w": z, "rpg_w": z.copy(), "fdrr_w": z.copy(),
                "routes_known": z.copy()}

    routes = _lag_map(r, f, target_season, "routes")
    tgt = {k: np.asarray(f.get(f"tgt_{k}", pd.Series(np.zeros(n))),
                         dtype=float) for k in range(1, N_LAGS + 1)}
    fdn = _lag_map(fd, f, target_season, "rec_fd")

    tprr, rt_total = _weighted_rate(f, tgt, routes, TPRR_K0)
    fdrr, _ = _weighted_rate(f, fdn, routes, TPRR_K0)
    rpg = _per_game(f, routes)

    # `routes_known` is "we have evidence of him running routes in the window",
    # NOT "the table has a row" -- participation covers every play from 2016, so
    # the only zeros are players who were not on an NFL field. That is exactly
    # the `move_known` shape batch 2 was burned by, which is why it is a
    # registered control arm rather than a passenger inside the treatment.
    known = (rt_total > 0).astype(float)
    return {"tprr_w": np.where(known > 0, tprr, np.nan),
            "rpg_w": np.nan_to_num(rpg, nan=0.0),
            "fdrr_w": np.where(known > 0, fdrr, np.nan),
            "routes_known": known}


# ----------------------------------------------------------------- block D
def _firstdown_block(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                     ) -> Dict[str, np.ndarray]:
    fd = gate().fd_before(panel, target_season - 1)
    n = len(f)
    if not len(fd):
        z = np.zeros(n)
        return {"fd_pg_w": z, "fdpt_w": z.copy(), "fd_known": z.copy()}

    fdn = _lag_map(fd, f, target_season, "rec_fd")
    tgt = {k: np.asarray(f.get(f"tgt_{k}", pd.Series(np.zeros(n))),
                         dtype=float) for k in range(1, N_LAGS + 1)}
    fdpt, tg_total = _weighted_rate(f, fdn, tgt, FDPT_K0)
    fd_pg = _per_game(f, fdn)

    # A player with no ffopportunity row and no targets is a legitimate zero, not
    # a coverage hole. `fd_known` marks the hole only: he HAD targets and the
    # source has nothing. Measured 0.0000 of the graded population -- which is
    # why block D registers no control arm, on a measurement rather than a
    # convenience (precommit §4).
    hole = np.zeros(n, dtype=bool)
    pid = f["player_id"]
    for k in range(1, N_LAGS + 1):
        lag = fd[fd["season"] == target_season - k]
        has = pid.isin(set(lag["player_id"])) if len(lag) else pd.Series(False, index=f.index)
        hole |= (tgt[k] > 0) & (~np.asarray(has))
    return {"fd_pg_w": np.nan_to_num(fd_pg, nan=0.0),
            "fdpt_w": np.where(tg_total > 0, fdpt, np.nan),
            "fd_known": (~hole).astype(float)}


# --------------------------------------------------------------- the builder
def build_factor5_features(panel: SeasonPanel, universe: pd.DataFrame,
                           target_season: int, use_proxy: bool = False,
                           use_batch2: bool = False,
                           blocks: Tuple[str, ...] = ()) -> pd.DataFrame:
    """`blocks` names exactly which batch-5 block to compute.

    Deliberately NOT a single boolean, for the same reason batch 3 made it a
    tuple: a block that is not declared must not be built, so an arm's audit
    proves what it read rather than merely asserting it. Neither batch-5 block
    reads season N, so both log as `feature`; the tuple is still honoured so
    that a NULL result can never be blamed on a column the arm did not declare.
    """
    f = build_factor3_features(panel, universe, target_season,
                               use_proxy=use_proxy, use_batch2=use_batch2)
    if not blocks:
        return f
    block: Dict[str, np.ndarray] = {}
    if "routes" in blocks:
        block.update(_routes_block(panel, f, target_season))
    if "firstdown" in blocks:
        block.update(_firstdown_block(panel, f, target_season))
    out = pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)
    # median-fill AFTER assembly so the median is taken over the season's own
    # known players, which is what batch 3 does and what the write-up claims.
    for c in ("tprr_w", "fdrr_w", "fdpt_w"):
        if c in out.columns:
            out[c] = _median_fill(out[c].to_numpy(dtype=float))
    return out
