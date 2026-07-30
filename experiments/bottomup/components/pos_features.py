"""Lagged feature construction for the multi-position component model.

Every feature is a function of seasons <= target_season - 1, plus two April-of-N
facts (draft round/pick for that year's rookies) and one calendar fact (season
length). Nothing reads season-N production. The panel's `before()` gate is the
enforcement; this module never touches `_frame` directly.

Rate features are built as (numerator, denominator) PAIRS rather than pre-divided
ratios, so the model can shrink them by their own sample size instead of treating
a 4-target season as equal evidence to a 150-target one.

THE THREE AVAILABILITY ARMS (see `component-model-multipos-precommit.md` §4) are
all built here, always. Which subset a model consumes is the model's choice; the
features themselves are computed once so the arms differ by exactly one thing.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from .pos_data import SeasonPanel, season_length

# Recency weights on the three prior seasons. Fixed a priori at a mild decay,
# NOT tuned. Tuning three weights on 13 seasons is how a model overfits and calls
# it insight. Whether a steeper decay helps is a registered question, not a knob.
LAG_WEIGHTS = (0.55, 0.30, 0.15)
N_LAGS = 3

# ---- availability feature blocks, one per pre-declared arm -------------------
AVAIL_A = ["gshare_w", "gshare_1", "present_1", "age", "age2", "evidence"]
AVAIL_B = AVAIL_A + ["inj_missed_share_1", "unexp_missed_share_1"]
AVAIL_C = AVAIL_A + ["gshare_max3"]
# Arms D and E are POST-HOC. They were added after arms A-C had been run, and
# they are not in the pre-commitment. They are here because measuring arm B
# turned up a data-quality fact that changes what the right experiment is: the
# injury report covers 2.5-4.8% of absences of nine games or more, while a
# depth-chart appearance covers 36-97% of the same weeks. Reported at a LOWER
# evidential standard than A-C and labelled as such wherever they appear.
AVAIL_D = AVAIL_A + ["rostered_absent_share_1", "offroster_share_1"]
AVAIL_E = AVAIL_D + ["depth_first_share_1"]
AVAIL_ARMS = {"A": AVAIL_A, "B": AVAIL_B, "C": AVAIL_C, "D": AVAIL_D, "E": AVAIL_E}
POSTHOC_ARMS = ("D", "E")


def _safe_div(a, b, fill=np.nan):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    out = np.full(a.shape, fill, dtype=float)
    ok = b > 0
    out[ok] = a[ok] / b[ok]
    return out


# Per-lag raw quantities the feature builder accumulates. (column, alias).
_LAG_COLS = [
    ("games", "games"), ("targets", "tgt"), ("receptions", "rec"),
    ("rec_yards", "recyds"), ("rec_tds", "rectd"), ("air_yards", "ay"),
    ("carries", "carries"), ("rush_yards", "rushyds"), ("rush_tds", "rushtd"),
    ("attempts", "att"), ("completions", "cmp"), ("pass_yards", "passyds"),
    ("pass_tds", "passtd"), ("interceptions", "ints"), ("sacks", "sacks"),
    ("fumbles_lost", "fum"), ("points", "pts"),
]

# Recency-weighted (numerator, denominator) rate pairs, kept unfused so the model
# can shrink each by its own sample size.
_RATE_PAIRS = [
    ("cr", "rec", "tgt"),            # catch rate
    ("ypr", "recyds", "rec"),        # yards per reception
    ("tdpt", "rectd", "tgt"),        # receiving TD per target
    ("adot", "ay", "tgt"),           # average depth of target
    ("ypc", "rushyds", "carries"),   # yards per carry
    ("tdpc", "rushtd", "carries"),   # rushing TD per carry
    ("ypa", "passyds", "att"),       # yards per pass attempt
    ("tdpa", "passtd", "att"),       # passing TD per attempt
    ("intpa", "ints", "att"),        # interception per attempt
    ("cmppa", "cmp", "att"),         # completion rate
    ("sackpa", "sacks", "att"),      # sack rate
    ("fumpg", "fum", "games"),       # fumbles lost per game
]


def build_features(panel: SeasonPanel, universe: pd.DataFrame,
                   target_season: int) -> pd.DataFrame:
    """One row per universe player, columns = pre-season-N information only."""
    cutoff = target_season - 1
    hist = panel.before(cutoff)
    team = panel.team_before(cutoff)
    inj = panel.injury_before(cutoff)
    depth = panel.depth_before(cutoff)

    hist = hist.merge(team, on=["team", "season"], how="left")

    f = universe[["player_id", "entry"]].copy()
    f["season"] = target_season
    f["season_len"] = season_length(target_season)

    # ---- career anchors (pre-cutoff only)
    first_seen = hist.groupby("player_id")["season"].min()
    f["first_season"] = f["player_id"].map(first_seen)
    f["experience"] = target_season - f["first_season"]
    f["is_rookie"] = f["first_season"].isna().astype(int)
    f.loc[f["is_rookie"] == 1, "experience"] = 0

    acc: Dict[str, np.ndarray] = {}
    n = len(f)
    weights = np.zeros((n, N_LAGS))
    gshares = np.zeros((n, N_LAGS))
    idx = f["player_id"]

    for k in range(1, N_LAGS + 1):
        s = target_season - k
        lag = hist[hist["season"] == s].set_index("player_id")
        present = idx.isin(lag.index).to_numpy()

        def col(name, default=0.0):
            if name in lag.columns:
                v = idx.map(lag[name])
            else:
                v = pd.Series(np.nan, index=f.index)
            return np.asarray(v.astype(float).fillna(default))

        for src, alias in _LAG_COLS:
            acc[f"{alias}_{k}"] = col(src)
        g = acc[f"games_{k}"]
        gs = g / season_length(s)
        acc[f"gshare_{k}"] = gs
        gshares[:, k - 1] = np.where(present, gs, np.nan)
        acc[f"present_{k}"] = present.astype(float)
        acc[f"tshare_{k}"] = _safe_div(acc[f"tgt_{k}"], col("team_targets", np.nan), fill=0.0)
        acc[f"cshare_{k}"] = _safe_div(acc[f"carries_{k}"], col("team_carries", np.nan), fill=0.0)
        acc[f"opp_{k}"] = acc[f"carries_{k}"] + acc[f"tgt_{k}"]
        # a season carries weight only in proportion to how much of it happened
        weights[:, k - 1] = LAG_WEIGHTS[k - 1] * np.minimum(gs, 1.0)

    for key, v in acc.items():
        f[key] = v

    wsum = weights.sum(axis=1)
    f["evidence"] = wsum          # 0 for a rookie, ~1 for a 3-year full-timer

    def wavg(prefix, per_game=False):
        num = np.zeros(n)
        for k in range(1, N_LAGS + 1):
            x = acc[f"{prefix}_{k}"]
            if per_game:
                gl = np.where(acc[f"games_{k}"] > 0, acc[f"games_{k}"], np.nan)
                x = np.nan_to_num(x / gl, nan=0.0)
            num += weights[:, k - 1] * x
        return np.where(wsum > 0, num / np.where(wsum > 0, wsum, 1.0), np.nan)

    for pref in ["tgt", "carries", "att", "opp", "rushyds", "recyds", "passyds", "pts"]:
        f[f"{pref}_pg_w"] = wavg(pref, per_game=True)
    f["tpg_w"] = f["tgt_pg_w"]
    f["carries_pg_w"] = f["carries_pg_w"]
    f["ppg_w"] = f["pts_pg_w"]
    f["tshare_w"] = wavg("tshare")
    f["cshare_w"] = wavg("cshare")
    f["gshare_w"] = wavg("gshare")
    # RB reparameterisation: receiving share of a single touch budget
    f["recshare_opp_w"] = np.where(f["opp_pg_w"] > 0,
                                   f["tgt_pg_w"] / f["opp_pg_w"].replace(0, np.nan), np.nan)

    for name, num_p, den_p in _RATE_PAIRS:
        num = np.zeros(n)
        den = np.zeros(n)
        for k in range(1, N_LAGS + 1):
            num += LAG_WEIGHTS[k - 1] * acc[f"{num_p}_{k}"]
            den += LAG_WEIGHTS[k - 1] * acc[f"{den_p}_{k}"]
        f[f"{name}_num"] = num
        f[f"{name}_den"] = den

    # ---- ARM C: the free control. Best games-share in the last three seasons.
    # Uses NO injury data. Declared in advance precisely so that "the injuries
    # table buys nothing a one-line feature does not" stays a reachable finding.
    with np.errstate(all="ignore"):
        f["gshare_max3"] = np.nan_to_num(np.nanmax(gshares, axis=1), nan=0.0)

    # ---- ARM B: the injury decomposition. Lag 1 only -- that is where the
    # defect is (one absent season read as permanent decline), and lag 1 is the
    # only lag with injury coverage across the whole walk-forward window
    # (injury reports start 2010; the earliest lag-1 season used is 2011).
    s1 = target_season - 1
    i1 = inj[inj["season"] == s1].set_index("player_id")
    out_wks = np.asarray(idx.map(i1["inj_out_wks"]).astype(float).fillna(0.0)) \
        if len(i1) else np.zeros(n)
    rep_wks = np.asarray(idx.map(i1["inj_report_wks"]).astype(float).fillna(0.0)) \
        if len(i1) else np.zeros(n)
    slen1 = float(season_length(s1))
    missed = np.clip(slen1 - acc["games_1"], 0.0, slen1)
    inj_missed = np.minimum(out_wks, missed)
    f["inj_out_wks_1"] = out_wks
    f["inj_report_wks_1"] = rep_wks
    f["missed_wks_1"] = missed
    f["inj_missed_share_1"] = inj_missed / slen1
    f["unexp_missed_share_1"] = (missed - inj_missed) / slen1

    # ---- ARMS D/E: the same decomposition from the depth chart instead.
    # POST-HOC (see AVAIL_D comment). `rostered_absent` = weeks the player was on
    # a depth chart and produced no stat line -- injured, suspended, benched or
    # inactive, undifferentiated but ROSTERED. `offroster` = weeks he was on no
    # depth chart at all -- cut, retired, unsigned. Arm B could not tell those
    # apart for long absences and that is exactly where a projection goes wrong.
    d1 = depth[depth["season"] == s1].set_index("player_id")
    dwk = np.asarray(idx.map(d1["depth_wks"]).astype(float).fillna(0.0)) \
        if len(d1) else np.zeros(n)
    dfirst = np.asarray(idx.map(d1["depth_first_wks"]).astype(float).fillna(0.0)) \
        if len(d1) else np.zeros(n)
    rostered_absent = np.clip(np.minimum(dwk - acc["games_1"], missed), 0.0, slen1)
    f["depth_wks_1"] = dwk
    f["rostered_absent_share_1"] = rostered_absent / slen1
    f["offroster_share_1"] = (missed - rostered_absent) / slen1
    f["depth_first_share_1"] = dfirst / slen1

    # ---- age (birthdate is time-invariant; no leakage path)
    bd = panel.birthdates.set_index("player_id")["birthdate"]
    born = pd.to_datetime(f["player_id"].map(bd), errors="coerce", format="mixed")
    f["age"] = (pd.Timestamp(f"{target_season}-09-01") - born).dt.days / 365.25

    # ---- draft capital (April of N for that year's rookies; earlier for vets)
    dr = panel.draft.set_index("player_id")
    f["draft_round"] = f["player_id"].map(dr["draft_round"]) if len(dr) else np.nan
    f["draft_pick"] = f["player_id"].map(dr["draft_pick"]) if len(dr) else np.nan
    f["undrafted"] = f["draft_pick"].isna().astype(int)
    f["log_draft_pick"] = np.log(f["draft_pick"].fillna(300.0).clip(lower=1))

    return f


_OUTCOME_COLS = [
    "games", "points", "targets", "receptions", "rec_yards", "rec_tds",
    "carries", "rush_yards", "rush_tds", "attempts", "completions",
    "pass_yards", "pass_tds", "interceptions", "sacks", "fumbles_lost",
    "rec_bonus", "rush_bonus", "pass_bonus", "total_bonus",
    "g100", "g150", "g200", "r100", "r150", "r200", "p300", "p350", "p400",
]


def outcome_components(panel: SeasonPanel, universe: pd.DataFrame,
                       target_season: int) -> pd.DataFrame:
    """Realised season-N components. EVALUATION AND TRAINING TARGETS ONLY.

    Called with target_season strictly less than the season being projected in
    every walk-forward fit; the caller is responsible for that and the panel gate
    backstops it. Absent from the season entirely => 0 points, 0 games, and the
    player STAYS IN. That is the survivorship guarantee.
    """
    out = panel.outcomes(target_season)
    keep = ["player_id", "name", "position"] + _OUTCOME_COLS
    m = universe[["player_id", "entry"]].merge(out[keep], on="player_id", how="left")
    for c in _OUTCOME_COLS:
        m[c] = m[c].fillna(0.0)
    m["season"] = target_season
    m["season_len"] = season_length(target_season)
    return m
