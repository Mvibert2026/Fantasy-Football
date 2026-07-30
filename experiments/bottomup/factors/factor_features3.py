"""Factor batch 3 features -- NGS separation, explosive rushing, OC tenure.

Design: `docs/ranking/factor-batch-3-precommit.md`, committed BEFORE any arm was
fitted. Wraps `factor_features2.build_factor2_features` and only ever APPENDS
columns, so batch 1 and batch 2 both keep reproducing bit for bit and every
batch-3 arm differs from its primary by exactly the block it declares.

THREE BLOCKS PLUS ONE REUSE.

  S  SEPARATION (WR, TE)   `sep_1`, `sep_known_1` -- last season's NGS average
     separation at the catch point. The only signal in `nfl.db` that is not a
     function of box-score volume, which is the whole reason it is worth a slot:
     everything else the model holds is a rearrangement of targets, carries and
     yards, and consensus prices those already.

     THE COVERAGE FLAG IS THE HAZARD, NOT THE FEATURE. NGS publishes ~95 WR and
     ~31 TE a season -- having a row is very nearly "was a starter last year".
     Batch 2 lost three arms to exactly this shape (`move_known` was 95-97% of
     an apparently large effect). So `sep_known_1` NEVER travels inside the
     treatment arm: the treatment carries the separation value alone with
     unknowns imputed to the same-season median, and the flag is registered as
     its own control arm in the same family.

  X  EXPLOSIVE RUSHING (RB)  `expl_w`, `expl_rel_w`, `expl_known` -- the share of
     a back's carries gaining >= 10 yards, empirical-Bayes shrunk toward the
     pooled rate with k0 = 50 carries FIXED A PRIORI (not tuned).

     `expl_rel_w` is a DIFFERENT QUESTION, not a robustness check: own rate minus
     his club-mates' rate over the same window. If explosiveness is the offensive
     line rather than the back, the club-relative version is where that shows up.

  T  COORDINATOR TENURE (QB, WR, TE, RB)  `oc_tenure`, `oc_tenure_known` --
     consecutive seasons the club's current play-caller has held the job,
     counting season N as year 1. Strictly generalises batch 2's `new_oc`
     (new_oc == 1 iff oc_tenure == 1), which is why the two are registered as
     separate arms rather than one.

     CENSORING, HANDLED NOT HIDDEN. A tenure computed off a source that begins in
     year Y understates every spell that began before Y, in one direction, for
     exactly the longest-serving coordinators. `play_callers_preseason` was
     backfilled to 2004 for this batch so the chain can be walked up to twelve
     seasons; any spell still touching the first observed season is marked
     `oc_tenure_known = 0` and imputed, and the censoring rate is reported.

  C  `new_oc` at QB -- batch 2's own C1 block, unchanged, at the one position
     batch 2 never ran. Comes free from `use_batch2=True`.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from experiments.bottomup.components.pos_data import SeasonPanel
from experiments.bottomup.components.pos_features import LAG_WEIGHTS, N_LAGS
from experiments.bottomup.factors.factor_features2 import (
    _normalise_coach, build_factor2_features,
)

#: Empirical-Bayes shrinkage constant for the explosive-rush rate, in units of
#: carries. FIXED A PRIORI at 50 -- the same order as the RB universe's own
#: qualification bar (25 carries) -- and never tuned against any result.
EXPL_K0 = 50.0

#: How far back the coordinator chain is walked. 15 seasons exceeds every OC
#: spell in the modern league; a chain that reaches the source's first season is
#: reported as censored rather than truncated silently.
OC_MAX_BACK = 15

#: THE SOURCE FLOOR, and it is a measured limit rather than a chosen one.
#: A backfill of `coord_preseason.py` to 2004 was run for this batch and FAILED
#: for a documented reason: 96 of 192 team-seasons in 2004-2009 return
#: `no_revision_before_kickoff` because the club staff navbox TEMPLATES did not
#: exist on Wikipedia before roughly 2010. What landed was 5 clubs in 2007, 4 in
#: 2008 and 12 in 2009 -- partial, and partial in a club-specific way, so a chain
#: that happened to reach a covered club would look longer than an identical
#: chain at an uncovered one. That is worse than a clean floor, so the sparse
#: 2007-2009 rows are deliberately NOT used and the chain stops at 2010.
#:
#: Censoring measured under this floor, target seasons 2014-2024: exactly ONE
#: club-season per year (3.1%), zero in 2024. Censored rows are flagged
#: `oc_tenure_known = 0` and imputed; they are not reported as tenure.
OC_FIRST_SEASON = 2010


def _median_fill(v: np.ndarray) -> np.ndarray:
    """Unknown -> the median of what IS known. Never 0: a zero is a claim about
    the player, a median is an admission that we do not know."""
    v = np.asarray(v, dtype=float)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
    return np.where(np.isfinite(v), v, med)


# ------------------------------------------------------------- S: separation
def _separation(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                ) -> Dict[str, np.ndarray]:
    ngs = panel.ngs_before(target_season - 1)
    prev = ngs[ngs["season"] == target_season - 1]
    if len(prev):
        s = prev.drop_duplicates("player_id").set_index("player_id")["avg_separation"]
        raw = np.asarray(f["player_id"].map(s), dtype=float)
    else:
        raw = np.full(len(f), np.nan)
    return {"sep_1": _median_fill(raw),
            "sep_known_1": np.isfinite(raw).astype(float)}


# ------------------------------------------------------- X: explosive rushing
def _explosive(panel: SeasonPanel, f: pd.DataFrame, target_season: int
               ) -> Dict[str, np.ndarray]:
    cutoff = target_season - 1
    rush = panel.rush_before(cutoff)
    n = len(f)
    if not len(rush):
        z = np.zeros(n)
        return {"expl_w": z, "expl_rel_w": z.copy(), "expl_known": z.copy()}

    # pooled prior: every rushing attempt strictly before the target season
    prior = float(rush["expl10"].sum() / max(rush["pbp_carries"].sum(), 1.0))

    # player's principal club per season (most carries), for the club-relative arm
    idx = rush.groupby(["season", "player_id"])["pbp_carries"].idxmax()
    principal = rush.loc[idx, ["season", "player_id", "team"]]
    own = rush.groupby(["season", "player_id"], as_index=False).agg(
        c=("pbp_carries", "sum"), e=("expl10", "sum"))
    own = own.merge(principal, on=["season", "player_id"], how="left")
    club = rush.groupby(["season", "team"], as_index=False).agg(
        club_c=("pbp_carries", "sum"), club_e=("expl10", "sum"))
    own = own.merge(club, on=["season", "team"], how="left")
    own["mate_c"] = (own["club_c"] - own["c"]).clip(lower=0.0)
    own["mate_e"] = (own["club_e"] - own["e"]).clip(lower=0.0)

    num = np.zeros(n); den = np.zeros(n)
    mnum = np.zeros(n); mden = np.zeros(n)
    pid = f["player_id"]
    for k in range(1, N_LAGS + 1):
        lag = own[own["season"] == target_season - k].set_index("player_id")
        if not len(lag):
            continue
        w = LAG_WEIGHTS[k - 1]
        for dst, col in ((num, "e"), (den, "c"), (mnum, "mate_e"), (mden, "mate_c")):
            dst += w * np.asarray(pid.map(lag[col]).astype(float).fillna(0.0))

    known = den > 0
    expl = (num + EXPL_K0 * prior) / (den + EXPL_K0)
    mate = np.where(mden > 0, (mnum + EXPL_K0 * prior) / (mden + EXPL_K0), prior)
    out = {"expl_w": np.where(known, expl, prior),
           "expl_rel_w": np.where(known, expl - mate, 0.0),
           "expl_known": known.astype(float)}

    # ---- POST-HOC, added after X1/X2 graded. Not in the pre-commitment and
    # carrying a lower evidential standard, exactly as batch 1 §4 required.
    #
    # THE OBJECTION X1 HAS TO ANSWER: an empirical-Bayes shrunk rate is pulled
    # toward the prior in proportion to its DENOMINATOR, so |expl_w - prior| is a
    # monotone function of lagged carries. A linear model handed that column may
    # be improving because it re-encodes prior VOLUME in a shape the existing
    # columns cannot express, not because explosiveness predicts anything.
    #
    # Two instruments, both fitted the same way as X1:
    #   expl_placebo_w -- identical shrinkage geometry, numerator replaced by a
    #       Binomial(den, prior) draw. Same volume-dependent dispersion, ZERO
    #       player-specific signal. If this also helps, X1 is the geometry.
    #   expl_raw_w     -- the unshrunk rate num/den, prior where den = 0. Same
    #       player signal, NO volume-dependent dispersion. If this also helps,
    #       X1 is the football.
    rng = np.random.default_rng(20260730 + target_season)
    den_i = np.rint(np.clip(den, 0, None)).astype(int)
    pl_num = rng.binomial(np.clip(den_i, 0, None), prior).astype(float)
    out["expl_placebo_w"] = np.where(
        known, (pl_num + EXPL_K0 * prior) / (den + EXPL_K0), prior)
    out["expl_raw_w"] = np.where(known & (den > 0),
                                 np.divide(num, np.where(den > 0, den, 1.0)), prior)

    # THE SECOND OBJECTION, also post-hoc: explosive rate is an efficiency stat,
    # and the model ALREADY holds an efficiency stat -- yards per carry, as a
    # shrunk rate. It uses it for the yards channel and never offers it to the
    # VOLUME channel. If plain lagged YPC bought the same thing, "explosive rate"
    # would be a repackaging rather than a new input, and saying so is the
    # difference between a finding and a press release.
    ypc_num = np.zeros(n)
    ypc_den = np.zeros(n)
    hist = panel.before(cutoff)
    for k in range(1, N_LAGS + 1):
        lag = hist[hist["season"] == target_season - k].set_index("player_id")
        if not len(lag):
            continue
        w = LAG_WEIGHTS[k - 1]
        ypc_num += w * np.asarray(pid.map(lag["rush_yards"]).astype(float).fillna(0.0))
        ypc_den += w * np.asarray(pid.map(lag["carries"]).astype(float).fillna(0.0))
    ypc_prior = float(np.sum(ypc_num) / max(np.sum(ypc_den), 1.0))
    out["ypc_lag_w"] = (ypc_num + EXPL_K0 * ypc_prior) / (ypc_den + EXPL_K0)
    return out


# --------------------------------------------------------- T: coordinator tenure
def _oc_key(df: pd.DataFrame) -> pd.Series:
    """Play-caller identity per club. Identical rule to batch 2's C1 -- a club
    with no OC line is one where the head coach called plays, so the key is
    COALESCE(oc, head coach). Kept in feature code, not in the stored table."""
    if not len(df):
        return pd.Series(dtype=object)
    k = df["coach_id"].where(df["coach_id"].notna(), df["head_coach"])
    k = k.map(_normalise_coach)
    k = k.where(k.astype(str).str.len() > 0, None)
    return pd.Series(k.to_numpy(), index=df["team"].to_numpy())


def _tenure_table(panel: SeasonPanel, target_season: int
                  ) -> Tuple[pd.Series, pd.Series]:
    """(tenure years, censored flag) per club, entering `target_season`."""
    keys: Dict[int, pd.Series] = {}
    floor = max(OC_FIRST_SEASON, target_season - OC_MAX_BACK)
    for s in range(target_season, floor - 1, -1):
        co = panel.preseason_coordinators(s)
        if not len(co):
            break
        keys[s] = _oc_key(co)
    if target_season not in keys:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    earliest = min(keys)

    tenure, censored = {}, {}
    for team, k0 in keys[target_season].items():
        if k0 is None:
            continue
        t, s, cens = 1, target_season - 1, False
        while s in keys:
            prev = keys[s].get(team)
            if prev is None or prev != k0:
                break
            t += 1
            if s == earliest:
                cens = True          # chain still alive at the source's first year
                break
            s -= 1
        tenure[team] = float(t)
        censored[team] = float(cens)
    return pd.Series(tenure, dtype=float), pd.Series(censored, dtype=float)


def _club_of(panel: SeasonPanel, f: pd.DataFrame, target_season: int) -> pd.Series:
    """Each player's season-N club: the pre-season roster where it has him under
    contract, else his N-1 club. Same rule as batch 2's C1, restated rather than
    imported so a change to one cannot silently move the other."""
    ros = panel.preseason_roster(target_season)
    hist = panel.before(target_season - 1)
    prev = hist[hist["season"] == target_season - 1]
    now = (ros[ros["under_contract"] == 1].drop_duplicates("player_id")
           .set_index("player_id")["team"]) if len(ros) else pd.Series(dtype=object)
    was = prev.drop_duplicates("player_id").set_index("player_id")["team"]
    return f["player_id"].map(now).fillna(f["player_id"].map(was))


def _oc_tenure(panel: SeasonPanel, f: pd.DataFrame, target_season: int
               ) -> Dict[str, np.ndarray]:
    tenure, censored = _tenure_table(panel, target_season)
    club = _club_of(panel, f, target_season)
    if not len(tenure):
        return {"oc_tenure": np.zeros(len(f)), "oc_tenure_known": np.zeros(len(f))}
    t = np.asarray(club.map(tenure), dtype=float)
    c = np.asarray(club.map(censored).fillna(1.0), dtype=float)
    known = np.isfinite(t) & (c < 0.5)
    return {"oc_tenure": _median_fill(np.where(known, t, np.nan)),
            "oc_tenure_known": known.astype(float)}


# --------------------------------------------------------------- the builder
def build_factor3_features(panel: SeasonPanel, universe: pd.DataFrame,
                           target_season: int, use_proxy: bool = False,
                           use_batch2: bool = False,
                           blocks: Tuple[str, ...] = ()) -> pd.DataFrame:
    """`blocks` names exactly which batch-3 block to compute.

    Deliberately NOT a single boolean. `sep` and `expl` read nothing but history,
    while `oc` reads the season-N coordinator table and the pre-season roster --
    both `proxy`-tagged. Building all three unconditionally would make every
    batch-3 arm log proxy reads, and the audit assertion "this arm provably never
    touched a season-N read" would stop meaning anything. Two arms, two audits.
    """
    f = build_factor2_features(panel, universe, target_season,
                               use_proxy=use_proxy, use_batch2=use_batch2)
    if not blocks:
        return f
    block: Dict[str, np.ndarray] = {}
    if "sep" in blocks:
        block.update(_separation(panel, f, target_season))
    if "expl" in blocks:
        block.update(_explosive(panel, f, target_season))
    if "oc" in blocks:
        block.update(_oc_tenure(panel, f, target_season))
    return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)
