"""Extra lagged features for factor batch 1.

Wraps `pos_features.build_features` and appends columns. It NEVER modifies one,
so every arm's shared features are bit-for-bit the primary's and an arm differs
by exactly the block it declares.

Three blocks:

  TEAM VOLUME  team_tpg_w / team_cpg_w -- the player's lag-k team's targets and
               carries per game, recency-weighted with the SAME weights
               `build_features` uses (LAG_WEIGHTS x games share). Strictly
               seasons <= N-1. Feeds factors #20 and #28.

  VACATED      vac_tshare / vac_cshare -- share of the team's N-1 targets and
               carries that belonged to players who are NOT on that team's
               season-N Week-1 depth chart. Factor #28.
               *** THIS BLOCK READS SEASON-N DATA. *** It is a declared PROXY,
               it is gated behind `use_proxy=True`, and the panel logs it under
               its own audit tag so an arm that did not ask for it can be proven
               not to have touched it. See `SeasonPanel.week1_roster`.

  STABILITY    tshare_sd3 / tshare_n3 -- dispersion of target share across the
               lag seasons the player was actually present for, and how many
               there were. Factor #13.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from experiments.bottomup.components.pos_data import (
    SeasonPanel, season_length,
)
from experiments.bottomup.components.pos_features import (
    LAG_WEIGHTS, N_LAGS, build_features,
)


def _lag_weights(f: pd.DataFrame) -> np.ndarray:
    """Reconstruct build_features' per-lag weights from its own output columns.

    Recomputed rather than returned from `build_features` so that function stays
    byte-identical and pass 1 keeps reproducing.
    """
    n = len(f)
    w = np.zeros((n, N_LAGS))
    for k in range(1, N_LAGS + 1):
        gs = f.get(f"gshare_{k}", pd.Series(np.zeros(n))).to_numpy(dtype=float)
        w[:, k - 1] = LAG_WEIGHTS[k - 1] * np.minimum(np.nan_to_num(gs), 1.0)
    return w


def _team_volume(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                 ) -> pd.DataFrame:
    """Recency-weighted team targets/carries per game, on the player's lag teams."""
    cutoff = target_season - 1
    hist = panel.before(cutoff)
    team = panel.team_before(cutoff)
    hist = hist.merge(team, on=["team", "season"], how="left")

    n = len(f)
    idx = f["player_id"]
    w = _lag_weights(f)
    num_t, num_c = np.zeros(n), np.zeros(n)
    for k in range(1, N_LAGS + 1):
        s = target_season - k
        lag = hist[hist["season"] == s].drop_duplicates("player_id").set_index("player_id")
        sl = float(season_length(s))
        for col, acc in (("team_targets", num_t), ("team_carries", num_c)):
            v = idx.map(lag[col]) if col in lag.columns else pd.Series(np.nan, index=f.index)
            acc += w[:, k - 1] * np.nan_to_num(np.asarray(v, dtype=float)) / sl
    wsum = w.sum(axis=1)
    ok = wsum > 0
    out = pd.DataFrame(index=f.index)
    out["team_tpg_w"] = np.where(ok, num_t / np.where(ok, wsum, 1.0), np.nan)
    out["team_cpg_w"] = np.where(ok, num_c / np.where(ok, wsum, 1.0), np.nan)
    return out


def _stability(f: pd.DataFrame) -> pd.DataFrame:
    """Dispersion of target share across the lags the player was present for."""
    n = len(f)
    vals = np.full((n, N_LAGS), np.nan)
    for k in range(1, N_LAGS + 1):
        present = f.get(f"present_{k}", pd.Series(np.zeros(n))).to_numpy(dtype=float)
        ts = f.get(f"tshare_{k}", pd.Series(np.zeros(n))).to_numpy(dtype=float)
        vals[:, k - 1] = np.where(present > 0, ts, np.nan)
    cnt = np.sum(np.isfinite(vals), axis=1).astype(float)
    with np.errstate(all="ignore"):
        sd = np.nanstd(vals, axis=1, ddof=0)
    out = pd.DataFrame(index=f.index)
    # one observed season has no dispersion to measure; encode "unknown" as the
    # population median rather than 0, which would read as "perfectly stable"
    sd = np.where(cnt >= 2, sd, np.nan)
    med = float(np.nanmedian(sd)) if np.isfinite(sd).any() else 0.0
    out["tshare_sd3"] = np.where(np.isfinite(sd), sd, med)
    out["tshare_sd_known"] = (cnt >= 2).astype(float)
    out["tshare_n3"] = cnt
    return out


def _vacated(panel: SeasonPanel, f: pd.DataFrame, target_season: int) -> pd.DataFrame:
    """PROXY. Share of each club's N-1 targets/carries held by players absent
    from that club's season-N Week-1 depth chart."""
    cutoff = target_season - 1
    hist = panel.before(cutoff)
    team = panel.team_before(cutoff)
    prev = hist[hist["season"] == cutoff][
        ["player_id", "team", "targets", "carries"]].copy()
    tt = team[team["season"] == cutoff][
        ["team", "team_targets", "team_carries"]].copy()

    wk1 = panel.week1_roster(target_season)          # <-- the declared proxy read
    on_now = set(zip(wk1["player_id"], wk1["team"])) if len(wk1) else set()

    prev["stays"] = [(p, t) in on_now for p, t in zip(prev["player_id"], prev["team"])]
    gone = prev[~prev["stays"]].groupby("team", sort=False).agg(
        vac_targets=("targets", "sum"), vac_carries=("carries", "sum")).reset_index()
    tv = tt.merge(gone, on="team", how="left").fillna({"vac_targets": 0.0,
                                                       "vac_carries": 0.0})
    tv["vac_tshare"] = np.where(tv["team_targets"] > 0,
                                tv["vac_targets"] / tv["team_targets"], np.nan)
    tv["vac_cshare"] = np.where(tv["team_carries"] > 0,
                                tv["vac_carries"] / tv["team_carries"], np.nan)
    tv = tv.set_index("team")

    # the player's season-N club: the proxy where it has him, else his N-1 club
    now_team = (wk1.drop_duplicates("player_id").set_index("player_id")["team"]
                if len(wk1) else pd.Series(dtype=object))
    prev_team = prev.drop_duplicates("player_id").set_index("player_id")["team"]
    t_now = f["player_id"].map(now_team)
    t_prev = f["player_id"].map(prev_team)
    club = t_now.fillna(t_prev)

    out = pd.DataFrame(index=f.index)
    out["vac_team_known"] = club.notna().astype(float)
    for c in ("vac_tshare", "vac_cshare"):
        out[c] = np.asarray(club.map(tv[c]).astype(float))
        # unknown club -> league-median vacancy, so an absent join is not read as
        # "no opportunity opened"
        med = float(np.nanmedian(tv[c])) if np.isfinite(tv[c]).any() else 0.0
        out[c] = np.where(np.isfinite(out[c]), out[c], med)
    out["changed_team"] = (t_now.notna() & t_prev.notna()
                           & (t_now != t_prev)).astype(float)
    return out


def build_factor_features(panel: SeasonPanel, universe: pd.DataFrame,
                          target_season: int, use_proxy: bool = False
                          ) -> pd.DataFrame:
    f = build_features(panel, universe, target_season)
    f = pd.concat([f, _team_volume(panel, f, target_season),
                   _stability(f)], axis=1)
    # interaction: share x team pace IS the raw per-game volume, so arm O1 can
    # recover the primary's parameterisation and is a genuine reparameterisation
    # rather than a strictly smaller model
    f["tshare_x_pace"] = f["tshare_w"].fillna(0.0) * f["team_tpg_w"].fillna(0.0)
    f["cshare_x_pace"] = f["cshare_w"].fillna(0.0) * f["team_cpg_w"].fillna(0.0)
    if use_proxy:
        f = pd.concat([f, _vacated(panel, f, target_season)], axis=1)
    return f
