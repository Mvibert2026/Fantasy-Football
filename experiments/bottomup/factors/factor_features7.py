"""Factor batch 7 features -- running-back usage and efficiency.

Design: `docs/ranking/factor-batch-7-precommit.md`, committed BEFORE any arm was
fitted. Wraps `pos_features.build_features` and only ever APPENDS columns, so the
batch-7 primary is bit-for-bit the RB primary that every earlier batch used and
every arm differs from it by exactly the block it declares.

WHY THIS MODULE DOES NOT TOUCH `pos_data.py`. Four factor batches are running
concurrently against one checkout. Every new source below therefore loads through
a batch-7-local `Sources` object that carries its OWN holdout gate, its OWN
cutoff assertion, and pushes its reads onto `panel.access_log` under the existing
`feature` tag -- so `WalkForward`'s look-ahead audit sees them exactly as it sees
`panel.before()`, without a shared file being edited by two agents at once.

SIX BLOCKS. Every one is seasons <= N-1 only; NOTHING here reads season N, so
every batch-7 arm can be PROVEN to have made zero proxy reads rather than
believed to have.

  Z  RED-ZONE SNAP RATE (N14)  `rz20_snap_w`, `i5_snap_w`, `rzsnap_known`
     Share of his club's red-zone (and inside-5) scrimmage snaps that the player
     was ON THE FIELD for, in the games he appeared in.

     THIS IS PRESENCE, NOT TOUCHES, and that is the whole point. Registry #10 is
     red-zone TOUCHES -- carries and targets inside the 20. A snap rate counts
     the plays where the coach chose to have him out there at all, including the
     ones where the ball went elsewhere. The two are different objects and the
     claim under test (Barfield) is explicitly about the presence one.

     Denominator is team red-zone plays IN GAMES HE APPEARED IN, not the team's
     season total. A season-total denominator multiplies role by availability,
     and `gshare_w` is already in every spec -- the feature would be re-encoding
     a column the model already holds.

     Source `participation`.`offense_players` x `pbp`.`yardline_100`, 2016+.

  G  INSIDE-5 TD CONVERSION (N15)  `i5_conv_w`, `i5_conv_placebo_w`, `i5_known`
     Empirical-Bayes shrunk (inside-5 rush TDs / inside-5 rush attempts), MINUS
     the pooled prior, so the feature is literally "vs the league base rate" as
     the factor is specified. k0 = 10 attempts, FIXED A PRIORI.

     OVERLAP DECLARED, NOT CLAIMED AWAY. `ff_opportunity`'s xFP construction
     models expected TDs from field position and is being tested concurrently by
     batch 6. Inside-5 conversion is a component of the same mechanism. No
     independence from that arm is claimed here and none has been established.

     NOT registry #19. That was TD-rate shrinkage (a change to how `tdpc` is
     pooled) and measured HARMFUL. This is a covariate built from a different
     denominator -- goal-line attempts only, not all carries.

  Y  YAC PER RECEPTION (N16)  `yac_per_rec_w`, `yac_known`
     Empirical-Bayes shrunk receiving yards after catch per reception, minus the
     pooled prior. k0 = 25 receptions, FIXED A PRIORI.

     A DATA CORRECTION TRAVELS WITH THIS BLOCK. The dispatch specifies `pbp`
     `yards_after_catch`, 1999+. `pbp` in this database HAS NO SUCH COLUMN (24
     columns, no YAC) and starts in 2009. The real source is
     `player_weekly_stats.receiving_yards_after_catch`, and it is NOT 1999+
     either: it is identically zero for 2000-2005 and real from 2006. Measured,
     not assumed -- see the results document.

  S  RECEIVING SHARE OF OWN POINTS (N17)  `recpts_share_w`, `recpts_ge40`
     Receiving fantasy points / (receiving + rushing fantasy points), scored
     under THIS league's rules including the stacking yardage bonuses, which the
     panel already carries per family. `recpts_ge40` is McFarland's own 40% cut.

  P  SNAP-SHARE PERSISTENCE (N18)  `snapshare_w`, `snap_ge60_w`, `snap_known`
     Recency-weighted mean offensive snap percentage, and the >=60% gate that is
     McFarland's actual claim. Source `snap_counts` 2013+, joined to gsis through
     `player_ids` (99.3% of RB player-seasons, 99.6% snap-weighted).

  L  LATE-SEASON ROLE TRAJECTORY (N19)  `late_ratio_w`, `late_lift_grp`,
     `late_known`
     `late_ratio_w` is the player's OWN weeks-13+ opportunity per game divided by
     his weeks-1-12 opportunity per game. `late_lift_grp` is the GROUP mean of
     that ratio for his (draft-round bucket x career-year bucket) cell, estimated
     on seasons <= N-1 ONLY.

     THIS LEAGUE MAKES IT DECISION-RELEVANT. Playoffs are weeks 16-17 with no
     reseeding, so late-season role is worth more here than in a league that ends
     in week 14. The registry has nothing like it.

     THE RESTATEMENT RISK IS THE POINT. Career year is nearly collinear with
     `age` and `experience`, both of which are already in every spec. The
     pre-commitment's independence gate exists for exactly this block.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from experiments.bottomup.components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, HoldoutViolation, CutoffViolation, SeasonPanel,
)
from experiments.bottomup.components.pos_features import (
    LAG_WEIGHTS, N_LAGS, build_features,
)

# ---------------------------------------------------------------- constants
#: Empirical-Bayes shrinkage constant for inside-5 TD conversion, in units of
#: inside-5 rush ATTEMPTS. FIXED A PRIORI at 10 -- a heavily used goal-line back
#: takes 15-25 inside-5 carries a season, so 10 is roughly half a season of
#: evidence. Never tuned against any result.
I5_K0 = 10.0

#: Same, for YAC per reception, in units of RECEPTIONS. FIXED A PRIORI at 25 --
#: the same order as the RB universe's own qualification bar. Never tuned.
YAC_K0 = 25.0

#: First season each new source carries real data. Used only to report coverage;
#: the arms' target-season floors are declared in the pre-commitment, not here.
PARTICIPATION_FIRST = 2016
SNAPS_FIRST = 2013
YAC_FIRST = 2006

#: Week at which the fantasy "late season" starts. This league's playoffs are
#: weeks 16-17, so weeks 13+ is the run-in plus the playoffs. Fixed a priori.
LATE_WEEK = 13

#: McFarland's own cuts, used verbatim rather than re-derived on our data.
ROUND_BUCKETS = ((1, 1, "r1"), (2, 3, "r23"), (4, 5, "r45"), (6, 7, "r67"))
CAREER_BUCKETS = ((0, 1, "y1"), (2, 3, "y23"), (4, 5, "y45"), (6, 7, "y67"),
                  (8, 9, "y89"), (10, 99, "y10p"))


def _median_fill(v: np.ndarray) -> np.ndarray:
    """Unknown -> the median of what IS known. Never 0: a zero is a claim about
    the player, a median is an admission that we do not know."""
    v = np.asarray(v, dtype=float)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
    return np.where(np.isfinite(v), v, med)


def _lag_weights(f: pd.DataFrame) -> np.ndarray:
    """Reconstruct `build_features`' own per-lag weights from its output columns,
    so a batch-7 weighted average uses the SAME weighting as `tpg_w` and
    `carries_pg_w` rather than a second, subtly different one."""
    n = len(f)
    w = np.zeros((n, N_LAGS))
    for k in range(1, N_LAGS + 1):
        gs = f.get(f"gshare_{k}", pd.Series(np.zeros(n))).to_numpy(dtype=float)
        w[:, k - 1] = LAG_WEIGHTS[k - 1] * np.minimum(np.nan_to_num(gs), 1.0)
    return w


# ============================================================ the source pack
@dataclass
class Batch7Sources:
    """Batch-7-local historical sources, each with its own holdout + cutoff gate.

    Deliberately NOT bolted onto `SeasonPanel`. Three other factor agents are
    editing this checkout concurrently and `pos_data.py` is shared; a batch-local
    pack cannot collide with them. Every accessor pushes a ("feature", cutoff)
    entry onto the panel's access log, so `WalkForward`'s existing look-ahead
    audit -- which asserts `max_feature_cutoff < target` -- covers these reads
    with no change to the harness.
    """

    rz: pd.DataFrame = field(default_factory=pd.DataFrame)      # RZ/I5 snaps
    i5: pd.DataFrame = field(default_factory=pd.DataFrame)      # inside-5 rush
    yac: pd.DataFrame = field(default_factory=pd.DataFrame)     # YAC/receptions
    snaps: pd.DataFrame = field(default_factory=pd.DataFrame)   # season snap %
    half: pd.DataFrame = field(default_factory=pd.DataFrame)    # early/late opp
    draft_round: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))

    def _gate(self, cutoff: int) -> None:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")

    def _cut(self, name: str, df: pd.DataFrame, cutoff: int,
             panel: SeasonPanel) -> pd.DataFrame:
        self._gate(cutoff)
        out = df[df["season"] <= cutoff].copy() if len(df) else df.copy()
        if len(out) and int(out["season"].max()) > cutoff:
            raise CutoffViolation(f"batch7 {name} cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return out

    def rz_before(self, cutoff, panel):    return self._cut("rz", self.rz, cutoff, panel)
    def i5_before(self, cutoff, panel):    return self._cut("i5", self.i5, cutoff, panel)
    def yac_before(self, cutoff, panel):   return self._cut("yac", self.yac, cutoff, panel)
    def snaps_before(self, cutoff, panel): return self._cut("snaps", self.snaps, cutoff, panel)
    def half_before(self, cutoff, panel):  return self._cut("half", self.half, cutoff, panel)


_SOURCES: Optional[Batch7Sources] = None


def sources(db_path: Path = DEFAULT_DB) -> Batch7Sources:
    global _SOURCES
    if _SOURCES is None:
        _SOURCES = _load_sources(db_path)
    return _SOURCES


# ------------------------------------------------------------------ loaders
def _pfr_to_gsis(conn) -> pd.Series:
    """`snap_counts` is keyed on PFR ids; everything else here is gsis. The
    crosswalk is `player_ids`, pivoted through `mfl_id`."""
    ids = pd.read_sql_query(
        "SELECT mfl_id, source, source_id FROM player_ids "
        "WHERE source IN ('gsis','pfr')", conn)
    g = ids[ids["source"] == "gsis"].set_index("mfl_id")["source_id"]
    p = ids[ids["source"] == "pfr"].set_index("mfl_id")["source_id"]
    xw = pd.DataFrame({"gsis": g, "pfr": p}).dropna()
    return pd.Series(xw["gsis"].to_numpy(), index=xw["pfr"].to_numpy())


def _load_redzone_snaps(conn) -> pd.DataFrame:
    """(season, player_id) -> red-zone and inside-5 snap COUNTS, plus the team
    red-zone/inside-5 plays that ran in the games he appeared in.

    Built one season at a time and aggregated immediately: the fully exploded
    (play x player) frame is ~3.6M rows and there is no reason to hold it.
    """
    seasons = [s for (s,) in conn.execute(
        "SELECT DISTINCT season FROM participation WHERE season < ? ORDER BY season",
        (HOLDOUT_SEASON,))]
    out = []
    for s in seasons:
        d = pd.read_sql_query(
            "SELECT p.nflverse_game_id AS gid, p.possession_team AS team, "
            "       p.offense_players AS op, b.yardline_100 AS yl "
            "FROM participation p JOIN pbp b "
            "  ON b.game_id = p.nflverse_game_id AND b.play_id = p.play_id "
            "WHERE p.season = ? AND (b.rush_attempt = 1 OR b.pass_attempt = 1) "
            "  AND p.offense_players IS NOT NULL AND p.offense_players <> '' "
            "  AND p.possession_team IS NOT NULL", conn, params=(s,))
        if not len(d):
            continue
        d["rz20"] = (d["yl"] <= 20).astype(float)
        d["i5"] = (d["yl"] <= 5).astype(float)
        # team totals per game, from the PLAY-level frame (never exploded)
        tg = d.groupby(["gid", "team"], as_index=False).agg(
            team_plays=("rz20", "size"), team_rz20=("rz20", "sum"),
            team_i5=("i5", "sum"))
        # player x play
        e = d.loc[:, ["gid", "team", "rz20", "i5"]].copy()
        e["player_id"] = d["op"].str.split(";")
        e = e.explode("player_id", ignore_index=True)
        e = e[e["player_id"].astype(str).str.len() > 0]
        pg = e.groupby(["gid", "team", "player_id"], as_index=False).agg(
            snaps=("rz20", "size"), rz20=("rz20", "sum"), i5=("i5", "sum"))
        pg = pg.merge(tg, on=["gid", "team"], how="left")
        agg = pg.groupby("player_id", as_index=False).agg(
            rz20=("rz20", "sum"), i5=("i5", "sum"),
            team_rz20=("team_rz20", "sum"), team_i5=("team_i5", "sum"),
            games=("gid", "nunique"))
        agg.insert(0, "season", s)
        out.append(agg)
    if not out:
        return pd.DataFrame(columns=["season", "player_id", "rz20", "i5",
                                     "team_rz20", "team_i5", "games"])
    return pd.concat(out, ignore_index=True)


def _load_inside5(conn) -> pd.DataFrame:
    """(season, player_id) -> inside-5 rush attempts and inside-5 rush TDs."""
    return pd.read_sql_query(
        "SELECT season, rusher_player_id AS player_id, "
        "       COUNT(*) AS i5_att, SUM(COALESCE(touchdown,0)) AS i5_td "
        "FROM pbp WHERE season < ? AND rush_attempt = 1 AND yardline_100 <= 5 "
        "  AND rusher_player_id IS NOT NULL "
        "GROUP BY season, rusher_player_id", conn, params=(HOLDOUT_SEASON,))


def _load_yac(conn) -> pd.DataFrame:
    """(season, player_id) -> receptions and receiving yards after catch."""
    return pd.read_sql_query(
        "SELECT season, player_id, SUM(COALESCE(receptions,0)) AS rec, "
        "       SUM(COALESCE(receiving_yards_after_catch,0)) AS yac "
        "FROM player_weekly_stats WHERE season < ? AND season_type = 'REG' "
        "GROUP BY season, player_id", conn, params=(HOLDOUT_SEASON,))


def _load_snap_share(conn) -> pd.DataFrame:
    """(season, player_id) -> mean offensive snap percentage across games with
    at least one offensive snap, and the count of such games."""
    d = pd.read_sql_query(
        "SELECT season, pfr_player_id, offense_pct FROM snap_counts "
        "WHERE season < ? AND game_type = 'REG' AND offense_snaps > 0",
        conn, params=(HOLDOUT_SEASON,))
    if not len(d):
        return pd.DataFrame(columns=["season", "player_id", "snap_pct", "snap_games"])
    xw = _pfr_to_gsis(conn)
    d["player_id"] = d["pfr_player_id"].map(xw)
    d = d[d["player_id"].notna()]
    return d.groupby(["season", "player_id"], as_index=False).agg(
        snap_pct=("offense_pct", "mean"), snap_games=("offense_pct", "size"))


def _load_half_season(conn) -> pd.DataFrame:
    """(season, player_id) -> opportunity (carries + targets) and games played,
    split at `LATE_WEEK`. Opportunity rather than fantasy points because the
    endpoint these arms are graded on is a VOLUME component."""
    d = pd.read_sql_query(
        "SELECT season, player_id, week, COALESCE(carries,0) AS carries, "
        "       COALESCE(targets,0) AS targets "
        "FROM player_weekly_stats WHERE season < ? AND season_type = 'REG'",
        conn, params=(HOLDOUT_SEASON,))
    if not len(d):
        return pd.DataFrame(columns=["season", "player_id", "early_opp",
                                     "early_g", "late_opp", "late_g"])
    d["opp"] = d["carries"] + d["targets"]
    d["late"] = (d["week"] >= LATE_WEEK).astype(int)
    d = d[d["opp"] > 0]
    g = d.groupby(["season", "player_id", "late"], as_index=False).agg(
        opp=("opp", "sum"), g=("opp", "size"))
    w = g.pivot_table(index=["season", "player_id"], columns="late",
                      values=["opp", "g"], fill_value=0.0).reset_index()
    w.columns = ["season", "player_id", "early_opp", "late_opp", "early_g", "late_g"]
    return w


def _load_draft_round(conn) -> pd.Series:
    d = pd.read_sql_query(
        "SELECT gsis_id, MIN(round) AS round FROM draft_picks "
        "WHERE gsis_id IS NOT NULL AND round IS NOT NULL GROUP BY gsis_id", conn)
    return pd.Series(d["round"].astype(float).to_numpy(),
                     index=d["gsis_id"].to_numpy())


def _load_sources(db_path: Path = DEFAULT_DB) -> Batch7Sources:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        src = Batch7Sources(
            rz=_load_redzone_snaps(conn),
            i5=_load_inside5(conn),
            yac=_load_yac(conn),
            snaps=_load_snap_share(conn),
            half=_load_half_season(conn),
            draft_round=_load_draft_round(conn),
        )
    finally:
        conn.close()
    for name in ("rz", "i5", "yac", "snaps", "half"):
        df = getattr(src, name)
        if len(df) and int(df["season"].max()) >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"batch7 source {name} contains the holdout")
    return src


# ================================================================== the blocks
def _same_position(panel: SeasonPanel, hist: pd.DataFrame, cutoff: int,
                   position: Optional[str]) -> pd.DataFrame:
    """Restrict a history frame to player-seasons at the modelled position.

    NOT cosmetic. Every pooled prior below is an empirical-Bayes shrinkage
    target, and the pools differ enormously by position: RB yards-after-catch per
    reception runs far above the all-position mean, and inside-5 conversion is
    dominated by quarterback sneaks. Shrinking a lightly-used back toward an
    all-position constant would bias exactly the players the shrinkage exists to
    protect, in a known direction. The pool is the position's own.
    """
    if position is None or not len(hist):
        return hist
    pos = panel.before(cutoff)[["season", "player_id", "position"]]
    pos = pos[pos["position"] == position][["season", "player_id"]]
    return hist.merge(pos, on=["season", "player_id"], how="inner")


def _weighted_lag(f: pd.DataFrame, hist: pd.DataFrame, num_col: str,
                  den_col: str, target_season: int
                  ) -> Tuple[np.ndarray, np.ndarray]:
    """Recency-weighted (numerator, denominator) over the three lag seasons,
    using `build_features`' own lag weights. Returns raw sums, un-divided, so the
    caller can shrink by the denominator instead of averaging ratios."""
    n = len(f)
    num, den = np.zeros(n), np.zeros(n)
    pid = f["player_id"]
    for k in range(1, N_LAGS + 1):
        lag = hist[hist["season"] == target_season - k]
        if not len(lag):
            continue
        lag = lag.drop_duplicates("player_id").set_index("player_id")
        w = LAG_WEIGHTS[k - 1]
        num += w * np.asarray(pid.map(lag[num_col]).astype(float).fillna(0.0))
        den += w * np.asarray(pid.map(lag[den_col]).astype(float).fillna(0.0))
    return num, den


# ------------------------------------------------------- Z: red-zone snap rate
def _redzone_snaps(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                   ) -> Dict[str, np.ndarray]:
    src = sources()
    hist = src.rz_before(target_season - 1, panel)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"rz20_snap_w": z, "i5_snap_w": z.copy(), "rzsnap_known": z.copy()}
    rz_n, rz_d = _weighted_lag(f, hist, "rz20", "team_rz20", target_season)
    i5_n, i5_d = _weighted_lag(f, hist, "i5", "team_i5", target_season)
    known = rz_d > 0
    rz = np.where(rz_d > 0, np.divide(rz_n, np.where(rz_d > 0, rz_d, 1.0)), np.nan)
    i5 = np.where(i5_d > 0, np.divide(i5_n, np.where(i5_d > 0, i5_d, 1.0)), np.nan)
    return {"rz20_snap_w": _median_fill(rz), "i5_snap_w": _median_fill(i5),
            "rzsnap_known": known.astype(float)}


# -------------------------------------------------- G: inside-5 TD conversion
def _inside5(panel: SeasonPanel, f: pd.DataFrame, target_season: int,
             position: Optional[str] = None) -> Dict[str, np.ndarray]:
    src = sources()
    hist = src.i5_before(target_season - 1, panel)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"i5_conv_w": z, "i5_conv_placebo_w": z.copy(), "i5_known": z.copy()}
    pool = _same_position(panel, hist, target_season - 1, position)
    prior = float(pool["i5_td"].sum() / max(pool["i5_att"].sum(), 1.0))
    num, den = _weighted_lag(f, hist, "i5_td", "i5_att", target_season)
    known = den > 0
    conv = (num + I5_K0 * prior) / (den + I5_K0)
    # PLACEBO CONTROL, registered in advance, not discovered afterwards. An
    # empirical-Bayes shrunk rate is pulled toward the prior in proportion to its
    # DENOMINATOR, so |conv - prior| is a monotone function of goal-line volume.
    # A model handed that column could improve because it re-encodes goal-line
    # VOLUME in a shape the existing columns cannot express. The placebo has
    # identical shrinkage geometry and ZERO player-specific signal.
    rng = np.random.default_rng(20260730 + target_season)
    den_i = np.rint(np.clip(den, 0, None)).astype(int)
    pl = rng.binomial(np.clip(den_i, 0, None), prior).astype(float)
    return {"i5_conv_w": np.where(known, conv - prior, 0.0),
            "i5_conv_placebo_w": np.where(
                known, (pl + I5_K0 * prior) / (den + I5_K0) - prior, 0.0),
            "i5_known": known.astype(float)}


# ------------------------------------------------------- Y: YAC per reception
def _yac(panel: SeasonPanel, f: pd.DataFrame, target_season: int,
         position: Optional[str] = None) -> Dict[str, np.ndarray]:
    src = sources()
    hist = src.yac_before(target_season - 1, panel)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"yac_per_rec_w": z, "yac_known": z.copy()}
    pool = _same_position(panel, hist, target_season - 1, position)
    prior = float(pool["yac"].sum() / max(pool["rec"].sum(), 1.0))
    num, den = _weighted_lag(f, hist, "yac", "rec", target_season)
    known = den > 0
    rate = (num + YAC_K0 * prior) / (den + YAC_K0)
    return {"yac_per_rec_w": np.where(known, rate - prior, 0.0),
            "yac_known": known.astype(float)}


# --------------------------------------------- S: receiving share of own points
def _rec_points_share(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                      ) -> Dict[str, np.ndarray]:
    """Under THIS league's scoring, stacking bonuses included. The panel already
    carries `rec_bonus` and `rush_bonus` per player-season, so this is the real
    league-specific split rather than a half-PPR approximation of it."""
    hist = panel.before(target_season - 1)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"recpts_share_w": z, "recpts_ge40": z.copy(), "recpts_known": z.copy()}
    h = hist.copy()
    h["rec_pts"] = (0.5 * h["receptions"].fillna(0.0)
                    + h["rec_yards"].fillna(0.0) / 10.0
                    + 6.0 * h["rec_tds"].fillna(0.0)
                    + h["rec_bonus"].fillna(0.0))
    h["rush_pts"] = (h["rush_yards"].fillna(0.0) / 10.0
                     + 6.0 * h["rush_tds"].fillna(0.0)
                     + h["rush_bonus"].fillna(0.0))
    h["all_pts"] = h["rec_pts"] + h["rush_pts"]
    num, den = _weighted_lag(f, h, "rec_pts", "all_pts", target_season)
    known = den > 0
    share = np.where(known, np.divide(num, np.where(den > 0, den, 1.0)), np.nan)
    share = np.clip(_median_fill(share), 0.0, 1.0)
    return {"recpts_share_w": share,
            "recpts_ge40": (share >= 0.40).astype(float) * known.astype(float),
            "recpts_known": known.astype(float)}


# ------------------------------------------------- P: snap-share persistence
def _snap_share(panel: SeasonPanel, f: pd.DataFrame, target_season: int
                ) -> Dict[str, np.ndarray]:
    src = sources()
    hist = src.snaps_before(target_season - 1, panel)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"snapshare_w": z, "snap_ge60_w": z.copy(), "snap_known": z.copy()}
    h = hist.copy()
    h["num"] = h["snap_pct"] * h["snap_games"]
    num, den = _weighted_lag(f, h, "num", "snap_games", target_season)
    known = den > 0
    share = np.where(known, np.divide(num, np.where(den > 0, den, 1.0)), np.nan)
    share = _median_fill(share)
    return {"snapshare_w": share,
            "snap_ge60_w": (share >= 0.60).astype(float) * known.astype(float),
            "snap_known": known.astype(float)}


# ------------------------------------------- L: late-season role trajectory
def _bucket(v: float, table) -> str:
    for lo, hi, name in table:
        if lo <= v <= hi:
            return name
    return "udfa" if table is ROUND_BUCKETS else "yUNK"


def _late_season(panel: SeasonPanel, f: pd.DataFrame, target_season: int,
                 position: Optional[str] = None) -> Dict[str, np.ndarray]:
    src = sources()
    hist = src.half_before(target_season - 1, panel)
    n = len(f)
    if not len(hist):
        z = np.zeros(n)
        return {"late_ratio_w": np.ones(n), "late_lift_grp": np.ones(n),
                "late_known": z}
    h = hist.copy()
    h["early_pg"] = np.where(h["early_g"] > 0, h["early_opp"] / h["early_g"].replace(0, np.nan), np.nan)
    h["late_pg"] = np.where(h["late_g"] > 0, h["late_opp"] / h["late_g"].replace(0, np.nan), np.nan)
    ok = np.isfinite(h["early_pg"]) & np.isfinite(h["late_pg"]) & (h["early_pg"] > 0)
    h["ratio"] = np.where(ok, np.clip(h["late_pg"] / h["early_pg"].replace(0, np.nan), 0.0, 3.0), np.nan)
    h["has"] = np.isfinite(h["ratio"]).astype(float)
    h["ratio0"] = np.nan_to_num(h["ratio"], nan=0.0)

    # ---- the player's OWN trajectory, recency-weighted across his lag seasons
    num, den = _weighted_lag(f, h, "ratio0", "has", target_season)
    known = den > 0
    own = np.where(known, np.divide(num, np.where(den > 0, den, 1.0)), np.nan)

    # ---- the GROUP mean, from seasons <= N-1 only. Career year is measured
    # relative to each row's own season, so a 2016 rookie contributes to the
    # year-1 cell, not to whatever bucket he sits in today.
    hh = _same_position(panel, h[np.isfinite(h["ratio"])].copy(),
                        target_season - 1, position)
    first = (panel.before(target_season - 1).groupby("player_id")["season"].min())
    hh["career"] = hh["season"] - hh["player_id"].map(first)
    hh["rd"] = hh["player_id"].map(src.draft_round)
    hh["rb"] = [_bucket(v, ROUND_BUCKETS) if np.isfinite(v) else "udfa"
                for v in hh["rd"].astype(float)]
    hh["cb"] = [_bucket(v, CAREER_BUCKETS) if np.isfinite(v) else "yUNK"
                for v in hh["career"].astype(float)]
    grp = hh.groupby(["rb", "cb"])["ratio"].agg(["mean", "size"])
    pooled = float(hh["ratio"].mean()) if len(hh) else 1.0
    # cells with fewer than 30 player-seasons fall back to the pooled mean rather
    # than reporting a three-player average as a group effect
    grp_mean = grp["mean"].where(grp["size"] >= 30, pooled)

    rd = f["player_id"].map(src.draft_round).astype(float)
    career = (target_season - f["player_id"].map(first)).astype(float)
    rb = [_bucket(v, ROUND_BUCKETS) if np.isfinite(v) else "udfa" for v in rd]
    cb = [_bucket(v, CAREER_BUCKETS) if np.isfinite(v) else "yUNK" for v in career]
    lift = np.array([float(grp_mean.get((a, b), pooled)) for a, b in zip(rb, cb)])

    return {"late_ratio_w": np.where(np.isfinite(own), own, pooled),
            "late_lift_grp": lift,
            "late_known": known.astype(float)}


# ------------------------------------------------------------------ builder
_BLOCKS = {
    "rz": _redzone_snaps,
    "i5": _inside5,
    "yac": _yac,
    "recshare": _rec_points_share,
    "snap": _snap_share,
    "late": _late_season,
}


#: blocks whose pooled prior / group mean must be computed on the modelled
#: position's own rows rather than on every player in the league
_POS_AWARE = {"i5", "yac", "late"}


def build_factor7_features(panel: SeasonPanel, universe: pd.DataFrame,
                           target_season: int,
                           blocks: Tuple[str, ...] = (),
                           position: Optional[str] = None) -> pd.DataFrame:
    """`blocks` names exactly which batch-7 block to compute.

    With `blocks=()` this IS `pos_features.build_features` and nothing else, so
    the batch-7 primary is the same object every earlier batch's RB primary was.
    Computing only the declared block means an arm's feature frame provably never
    contains a column it did not register.
    """
    f = build_features(panel, universe, target_season)
    if not blocks:
        return f
    block: Dict[str, np.ndarray] = {}
    for b in blocks:
        if b not in _BLOCKS:
            raise KeyError(f"no batch-7 block {b!r}")
        kw = {"position": position} if b in _POS_AWARE else {}
        block.update(_BLOCKS[b](panel, f, target_season, **kw))
    return pd.concat([f, pd.DataFrame(block, index=f.index)], axis=1)
