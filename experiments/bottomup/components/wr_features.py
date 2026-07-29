"""Lagged feature construction for the WR component model.

Every feature here is a function of seasons <= target_season - 1, plus two
April-of-N facts (draft round/pick for that year's rookies) and one calendar
fact (season length). Nothing reads season N production. The panel's `before()`
gate is the enforcement; this module never touches `_frame` directly.

Rate features are built as (numerator, denominator) pairs rather than as
pre-divided ratios, so the model can shrink them by their own sample size
instead of treating a 4-target season as equal evidence to a 150-target one.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .wr_data import SeasonPanel, season_length

# Recency weights on the three prior seasons. Fixed a priori at a mild decay,
# NOT tuned -- tuning three weights on 13 seasons is how a model overfits and
# calls it insight. Whether a steeper or flatter decay helps is a registered
# question, not a knob to turn here.
LAG_WEIGHTS = (0.55, 0.30, 0.15)
N_LAGS = 3


def _safe_div(a, b, fill=np.nan):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    out = np.full(a.shape, fill, dtype=float)
    ok = b > 0
    out[ok] = a[ok] / b[ok]
    return out


def build_features(panel: SeasonPanel, universe: pd.DataFrame,
                   target_season: int) -> pd.DataFrame:
    """One row per universe player, columns = pre-season-N information only."""
    cutoff = target_season - 1
    hist = panel.before(cutoff)
    team = panel.team_before(cutoff)

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

    # ---- per-lag raw quantities
    acc: Dict[str, np.ndarray] = {}
    n = len(f)
    weights = np.zeros((n, N_LAGS))
    for k in range(1, N_LAGS + 1):
        s = target_season - k
        lag = hist[hist["season"] == s].set_index("player_id")
        idx = f["player_id"]
        present = idx.isin(lag.index).to_numpy()

        def col(name, default=0.0):
            v = idx.map(lag[name]) if name in lag.columns else pd.Series(np.nan, index=f.index)
            return np.asarray(v.astype(float).fillna(default))

        g = col("games")
        acc[f"games_{k}"] = g
        acc[f"gshare_{k}"] = g / season_length(s)
        acc[f"tgt_{k}"] = col("targets")
        acc[f"rec_{k}"] = col("receptions")
        acc[f"recyds_{k}"] = col("rec_yards")
        acc[f"rectd_{k}"] = col("rec_tds")
        acc[f"ay_{k}"] = col("air_yards")
        acc[f"carries_{k}"] = col("carries")
        acc[f"rushyds_{k}"] = col("rush_yards")
        acc[f"rushtd_{k}"] = col("rush_tds")
        acc[f"fum_{k}"] = col("fumbles_lost")
        acc[f"pts_{k}"] = col("points")
        tt = col("team_targets", default=np.nan)
        acc[f"tshare_{k}"] = _safe_div(acc[f"tgt_{k}"], tt, fill=0.0)
        acc[f"present_{k}"] = present.astype(float)
        # a season only carries weight in proportion to how much of it happened
        weights[:, k - 1] = LAG_WEIGHTS[k - 1] * np.minimum(g / season_length(s), 1.0)

    for k, v in acc.items():
        f[k] = v

    wsum = weights.sum(axis=1)
    f["evidence"] = wsum          # 0 for a rookie, ~1 for a 3-year full-time WR

    def wavg(prefix, per_game=False):
        num = np.zeros(n)
        for k in range(1, N_LAGS + 1):
            x = acc[f"{prefix}_{k}"]
            if per_game:
                gl = np.where(acc[f"games_{k}"] > 0, acc[f"games_{k}"], np.nan)
                x = np.nan_to_num(x / gl, nan=0.0)
            num += weights[:, k - 1] * x
        return np.where(wsum > 0, num / np.where(wsum > 0, wsum, 1.0), np.nan)

    f["tpg_w"] = wavg("tgt", per_game=True)
    f["tshare_w"] = wavg("tshare")
    f["gshare_w"] = wavg("gshare")
    f["carries_pg_w"] = wavg("carries", per_game=True)
    f["rushyds_pg_w"] = wavg("rushyds", per_game=True)
    f["ppg_w"] = wavg("pts", per_game=True)

    # ---- rate numerators/denominators, recency-weighted, kept unfused
    for name, num_p, den_p in [("cr", "rec", "tgt"), ("ypr", "recyds", "rec"),
                               ("tdpt", "rectd", "tgt"), ("adot", "ay", "tgt"),
                               ("ypc", "rushyds", "carries"),
                               ("fumpg", "fum", "games")]:
        num = np.zeros(n)
        den = np.zeros(n)
        for k in range(1, N_LAGS + 1):
            num += LAG_WEIGHTS[k - 1] * acc[f"{num_p}_{k}"]
            den += LAG_WEIGHTS[k - 1] * acc[f"{den_p}_{k}"]
        f[f"{name}_num"] = num
        f[f"{name}_den"] = den

    # ---- age (birthdate is time-invariant; no leakage path)
    bd = panel.birthdates.set_index("player_id")["birthdate"]
    born = pd.to_datetime(f["player_id"].map(bd), errors="coerce", format="mixed")
    ref = pd.Timestamp(f"{target_season}-09-01")
    f["age"] = (ref - born).dt.days / 365.25

    # ---- draft capital (April of N for that year's rookies; earlier for vets)
    dr = panel.draft.set_index("player_id")
    f["draft_round"] = f["player_id"].map(dr["draft_round"]) if len(dr) else np.nan
    f["draft_pick"] = f["player_id"].map(dr["draft_pick"]) if len(dr) else np.nan
    f["undrafted"] = f["draft_pick"].isna().astype(int)
    f["log_draft_pick"] = np.log(f["draft_pick"].fillna(300.0).clip(lower=1))

    return f


def outcome_components(panel: SeasonPanel, universe: pd.DataFrame,
                       target_season: int) -> pd.DataFrame:
    """Realised season-N components. EVALUATION AND TRAINING TARGETS ONLY.

    Called with target_season strictly less than the season being projected in
    every walk-forward fit; the caller is responsible for that and the panel
    gate backstops it.
    """
    out = panel.outcomes(target_season)
    keep = ["player_id", "name", "position", "games", "points", "targets",
            "receptions", "rec_yards", "rec_tds", "rec_bonus",
            "carries", "rush_yards", "rush_tds", "fumbles_lost",
            "g100", "g150", "g200"]
    m = universe[["player_id", "entry"]].merge(out[keep], on="player_id", how="left")
    for c in keep[3:]:
        m[c] = m[c].fillna(0.0)
    m["season"] = target_season
    m["season_len"] = season_length(target_season)
    return m
