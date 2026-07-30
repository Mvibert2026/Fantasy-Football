"""Factor batch 2 features -- vacated opportunity on REAL rosters, and the
player's offensive coordinator.

These are the two inputs behind the founder's own two examples of what a
bottom-up model should be able to say (`FR-2026-07-30-bottom-up-causal-insights`):

    "So and so has a new OC and we expect routes run to increase."
    "Or the starter from last year left."

Wraps `factor_features.build_factor_features` and appends columns; it never
modifies one, so batch 1 keeps reproducing bit-for-bit and every batch-2 arm
differs from the primary by exactly the block it declares.

FOUR BLOCKS.

  V2 DEPARTURE (team level)   vac2_tshare / vac2_cshare -- share of the club's
      N-1 targets and carries held by players who are NOT under contract to that
      club at season-N Week 1. The clean redo of batch 1's V1, which had to use a
      Week-1 DEPTH CHART and therefore counted 91 of 2,166 prior-season producers
      as departed while they were still under contract, 40 of them on IR.

  V3 ABSENCE (team level)     vac3_tshare / vac3_cshare -- same, widened from
      "left the club" to "cannot play in Week 1" (adds IR, PUP, suspended,
      practice squad). Different question, registered separately, NOT a
      robustness check on V2.

  V4 AHEAD-OF-ME (PLAYER level)  vac_ahead_t / vac_ahead_c -- the share of the
      club's N-1 opportunity vacated by departed players who had MORE of it than
      this player did. This is the actual mechanism the founder is describing:
      opportunity opens ABOVE you, not below you. Two players on the same club
      get different values, which no team-level vacancy feature can do, and
      which is the whole point of a bottom-up model that can hold a player-level
      opinion. Untested anywhere in this project before now.

  M1 MOVED (player level)     moved_club -- this player is under contract to a
      DIFFERENT club than the one he produced for in N-1. Batch 1's §4 found the
      team-change flag helping (-0.46 RB, -0.15 WR MAE) while the vacancy
      MAGNITUDE hurt, and logged "he moved may be worth more than how much
      opened" as an untested idea. This is that test.

  C1 NEW OC (player level)    new_oc -- this player's club changed offensive
      coordinator between N-1 and N, plus `oc_known` so a null join is visible
      rather than being read as "no change".

EVERY BLOCK READS SEASON-N DATA and every one of them goes through a `proxy`-
tagged panel accessor, so an arm that did not declare it can still be PROVEN not
to have touched it by the same audit assertion batch 1 already runs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.bottomup.components.pos_data import SeasonPanel
from experiments.bottomup.factors.factor_features import build_factor_features


# --------------------------------------------------------------- helpers
def _prev_production(panel: SeasonPanel, target_season: int):
    """Season N-1 player production and club totals. Strictly <= N-1."""
    cutoff = target_season - 1
    hist = panel.before(cutoff)
    team = panel.team_before(cutoff)
    prev = hist[hist["season"] == cutoff][
        ["player_id", "team", "targets", "carries"]].copy()
    tt = team[team["season"] == cutoff][
        ["team", "team_targets", "team_carries"]].copy()
    return prev, tt


def _team_vacancy(prev: pd.DataFrame, tt: pd.DataFrame,
                  stays: pd.Series, prefix: str) -> pd.DataFrame:
    """Club-level vacated share under one definition of 'stays'."""
    gone = prev[~stays.to_numpy()].groupby("team", sort=False).agg(
        vt=("targets", "sum"), vc=("carries", "sum")).reset_index()
    tv = tt.merge(gone, on="team", how="left").fillna({"vt": 0.0, "vc": 0.0})
    tv[f"{prefix}_tshare"] = np.where(tv["team_targets"] > 0,
                                      tv["vt"] / tv["team_targets"], np.nan)
    tv[f"{prefix}_cshare"] = np.where(tv["team_carries"] > 0,
                                      tv["vc"] / tv["team_carries"], np.nan)
    return tv.set_index("team")[[f"{prefix}_tshare", f"{prefix}_cshare"]]


def _ahead_of_me(prev: pd.DataFrame, tt: pd.DataFrame, stays: np.ndarray,
                 col: str, team_col: str) -> pd.Series:
    """For every N-1 player: share of his club's N-1 `col` held by DEPARTED
    club-mates who out-produced him in `col`.

    Computed by sorting each club's players descending on `col` and taking the
    cumulative departed volume strictly above each player. Ties are handled by
    the sort being stable and by comparing on value, not rank, so two players
    with identical volume see the same number.
    """
    p = prev[["player_id", "team", col]].copy()
    p["gone_vol"] = np.where(stays, 0.0, p[col].to_numpy(dtype=float))
    out = {}
    for team, g in p.groupby("team", sort=False):
        g = g.sort_values(col, ascending=False)
        v = g[col].to_numpy(dtype=float)
        gv = g["gone_vol"].to_numpy(dtype=float)
        cum = np.concatenate([[0.0], np.cumsum(gv)])[:-1]      # strictly above
        # collapse ties to the value at the first row of the tie group
        for i in range(1, len(v)):
            if v[i] == v[i - 1]:
                cum[i] = cum[i - 1]
        denom = tt.loc[tt["team"] == team, team_col]
        d = float(denom.iloc[0]) if len(denom) and float(denom.iloc[0]) > 0 else np.nan
        for pid, c in zip(g["player_id"], cum):
            out[pid] = c / d if np.isfinite(d) else np.nan
    return pd.Series(out, dtype=float)


def _fill_median(s: pd.Series, name: str) -> np.ndarray:
    """Unknown -> population median, never 0. A zero here would read as
    'nothing opened', which is a claim; the median is an admission."""
    v = np.asarray(s, dtype=float)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
    return np.where(np.isfinite(v), v, med)


# --------------------------------------------------------------- the block
def _batch2(panel: SeasonPanel, f: pd.DataFrame, target_season: int
            ) -> pd.DataFrame:
    prev, tt = _prev_production(panel, target_season)
    ros = panel.preseason_roster(target_season)                # proxy-tagged read

    contract = set(zip(ros.loc[ros["under_contract"] == 1, "player_id"],
                       ros.loc[ros["under_contract"] == 1, "team"]))
    avail = set(zip(ros.loc[ros["available"] == 1, "player_id"],
                    ros.loc[ros["available"] == 1, "team"]))

    stays_c = pd.Series([(p, t) in contract for p, t in
                         zip(prev["player_id"], prev["team"])], index=prev.index)
    stays_a = pd.Series([(p, t) in avail for p, t in
                         zip(prev["player_id"], prev["team"])], index=prev.index)

    v2 = _team_vacancy(prev, tt, stays_c, "vac2")
    v3 = _team_vacancy(prev, tt, stays_a, "vac3")

    # each player's season-N club: where the roster has him under contract,
    # else his N-1 club. A player under contract to two clubs at Week 1 does not
    # exist, so the first match is the only match.
    now_team = (ros[ros["under_contract"] == 1].drop_duplicates("player_id")
                .set_index("player_id")["team"]) if len(ros) else pd.Series(dtype=object)
    prev_team = prev.drop_duplicates("player_id").set_index("player_id")["team"]
    t_now = f["player_id"].map(now_team)
    t_prev = f["player_id"].map(prev_team)
    club = t_now.fillna(t_prev)

    out = pd.DataFrame(index=f.index)
    out["vac_club_known"] = club.notna().astype(float)
    for tbl in (v2, v3):
        for c in tbl.columns:
            out[c] = _fill_median(club.map(tbl[c]), c)

    # V4 -- player level, keyed on the player himself, not on his club
    ah_t = _ahead_of_me(prev, tt, stays_c.to_numpy(), "targets", "team_targets")
    ah_c = _ahead_of_me(prev, tt, stays_c.to_numpy(), "carries", "team_carries")
    # a player with no N-1 production has nobody above him on a club he was not
    # on: 0.0 is the correct value here, not the median.
    out["vac_ahead_t"] = np.nan_to_num(np.asarray(f["player_id"].map(ah_t),
                                                  dtype=float), nan=0.0)
    out["vac_ahead_c"] = np.nan_to_num(np.asarray(f["player_id"].map(ah_c),
                                                  dtype=float), nan=0.0)

    # M1 -- moved clubs
    out["moved_club"] = (t_now.notna() & t_prev.notna()
                         & (t_now != t_prev)).astype(float)
    out["move_known"] = (t_now.notna() & t_prev.notna()).astype(float)

    # C1 -- the player's offensive coordinator, and whether it changed
    oc_now = panel.preseason_coordinators(target_season)       # proxy-tagged read
    oc_prev = panel.preseason_coordinators(target_season - 1)

    def _key(df: pd.DataFrame) -> pd.Series:
        if not len(df):
            return pd.Series(dtype=object)
        # a club with no OC line is one where the head coach called plays; that
        # is a real and common arrangement, so key on the HC rather than dropping
        # the club. The substitution is HERE, in feature code, where it is
        # visible and can be turned off -- not baked into the stored table.
        k = df["coach_id"].where(df["coach_id"].notna(),
                                 "HC:" + df["head_coach"].astype(str))
        return pd.Series(k.to_numpy(), index=df["team"].to_numpy())

    k_now, k_prev = _key(oc_now), _key(oc_prev)
    c_now = club.map(k_now) if len(k_now) else pd.Series(np.nan, index=f.index)
    c_prev = club.map(k_prev) if len(k_prev) else pd.Series(np.nan, index=f.index)
    known = c_now.notna() & c_prev.notna()
    out["oc_known"] = known.astype(float)
    # unknown -> 0.0 AND oc_known=0, so the model can separate "no change" from
    # "we do not know", which a single column cannot express
    out["new_oc"] = np.where(known, (c_now != c_prev).astype(float), 0.0)
    return out


def build_factor2_features(panel: SeasonPanel, universe: pd.DataFrame,
                           target_season: int, use_proxy: bool = False,
                           use_batch2: bool = False) -> pd.DataFrame:
    f = build_factor_features(panel, universe, target_season, use_proxy=use_proxy)
    if use_batch2:
        f = pd.concat([f, _batch2(panel, f, target_season)], axis=1)
    return f
