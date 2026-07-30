#!/usr/bin/env python3
"""ADP vs. Production structural-mispricing analysis (founder request, 2026-07-30).

Answers: where is consensus ADP systematically wrong, in ways that repeat
across seasons? Not "who busted" -- that is hindsight. This measures whether
a PRE-DRAFT-OBSERVABLE attribute (position, ADP round, age, prior-season
games missed, team change, prior-season volume-vs-efficiency split) predicts
the sign/size of the ADP residual, using only information that existed
before that season's draft.

DATA SOURCE AND ITS LIMITS -- read before trusting any number below.
The only ADP history in this database with a genuine pre-draft `as_of_date`
is `ffc_adp_snapshots` where `adp_source='ffc_half_ppr_12team'`
(thread 055 backfill, `tools/backfill_ffc_adp_history.py`; loaded into this
worktree's nfl.db from the committed CSVs under
`data/adp-snapshots-ffc/*_12team_period*.csv` -- this worktree's own nfl.db
did not have those rows on session start even though CURRENT-STATE.md says
the backfill "landed": nfl.db is gitignored and worktrees do not inherit it
(docs/environment.md SS4), and the backfill session's DB copy never made it
into this worktree's data/ until this session loaded the committed CSVs
directly). It is FanFootballCalculator mock-draft ADP, 12-team, half-PPR,
covering seasons 2018-2024 (2025 excluded, see below). Two structural
caveats this analysis cannot remove:

1. **12-team mock ADP, not this league's 10-team real-money ADP.** The
   project has no verified 10-team historical ADP source (only a single
   current-day 2026 mfl_proxy snapshot exists at 10-team). Round buckets
   below use 12-team-per-round math; treat "round" as illustrative, not this
   league's literal draft round.
2. **Mock drafts, not real drafts.** FFC's sample is mock-draft activity,
   not real league results. It is the best available proxy for "market
   consensus at that pre-draft moment" but is not identical to it.

SEASON 2025 IS NOT IN THIS ADP SOURCE AT ALL (backfill covers 2018-2024
only) -- the project's locked holdout is therefore untouched by
construction, not by discipline. Of the seasons that DO exist here, 2024 is
held out as an internal holdout: explored/tuned on 2018-2023, touched once
at the end.

UNIVERSE / SURVIVORSHIP. For season N, the analysis population is exactly
the players who appear in that season's FFC ADP snapshot -- decided BEFORE
the season, using no outcome information. A player who busted (or got hurt,
or was cut) and generated a near-zero point total is fully retained: their
actual points defaults to 0.0 rather than being dropped for lack of a
stats row. This is deliberate (CLAUDE.md SS6.2) -- excluding them would be
exactly the survivorship bias this analysis exists to avoid.

LOOK-AHEAD. All "prior-season" features (age, games missed, team change,
volume/efficiency split) are computed from season N-1 or earlier only.
`as_of_date` on the ADP row itself is the historical mock-draft window's
END date (pre-verified against nflreadpy schedules by the backfill script),
not the day any of this was run. Actual points for season N use
`db.actual_season_outcomes` (the evaluation-only path) -- this script does
not feed any ranking-input pipeline, so `CutoffEnforcedStore` is not the
right tool here; it is retrospective *measurement*, per the dispatch.

RESIDUAL DEFINITION (VALUE OVER REPLACEMENT, not raw points, and not just
rank). Two false starts on the way to this, both caught before being
reported, both left in the module history below because they are exactly
the kind of mistake this analysis exists to prevent:

  FALSE START 1 -- per-position value curve. Building one points-value curve
  PER POSITION and ranking within it makes every position's mean residual
  trivially ~0.00 by construction (a within-position curve is a permutation
  of that position's own players). That would have made "is one position
  priced worse than others" untestable by design, not merely
  non-significant.

  FALSE START 2 -- overall RAW POINTS curve, pooling positions. Fixes false
  start 1's tautology, but produces a "QB is underpriced by +146 pts/season"
  result that is not a market inefficiency -- it is this league's own
  single-QB roster rule. A league that starts 1 QB and 5+ flex-eligible
  skill spots does not let a manager bank a QB's extra raw points the way it
  lets a WR1's; comparing raw points across positions ignores replacement
  level entirely and manufactures a "finding" out of known roster
  mechanics, not market error.

  WHAT'S ACTUALLY USED: value over replacement (VBD), via this project's own
  `scoring.compute_vbd` / `ReplacementLevels` (ADR-029's measured RB30/WR40/
  TE10/QB10 flex-adjusted baselines at this league's 10-team, 1-QB roster
  shape) -- the same replacement-level machinery `backtest.py` already uses
  to evaluate rankings, reused rather than re-invented. Replacement level is
  computed from the FULL season player universe (every player with any
  weekly stats row that season, not just the ADP-listed subset) so the
  replacement floor itself isn't distorted by ADP's own survivorship cut.
  Then, for each season:
  1. Sort the ADP universe (ALL positions together) by the real ADP overall
     rank ascending -- the market's actual cross-position ordering, the
     thing being tested.
  2. Sort the SAME universe by realized VBD descending -- the season's own
     realized cross-position "value curve": what a perfectly-ordered board
     would have delivered at each overall slot, already replacement-level-
     adjusted.
  3. expected_vbd(player) = value_curve[ADP-overall-rank - 1] (clamped).
  4. residual_points = actual_vbd - expected_vbd.
This still pools to ~0 across the whole season (a permutation of the same
underlying values), so a position family with a nonzero mean residual is a
real, non-tautological, replacement-level-aware finding, not an artifact of
roster rules. It is NOT free of same-season information by construction
(the value curve uses season N's own realized VBD) -- that is fine here
because it is used only to price the SIZE of a rank error already observed,
never as a predictive input.

MULTIPLE COMPARISONS. Six pre-registered factor families are tested (the
ones the dispatch named, in the order given): position, ADP round bucket,
age x position group, prior-season games missed, team change, prior-season
volume-vs-efficiency split. Each family yields ONE p-value (a permutation
test on the family's grouping variable, clustered by season -- see
`permutation_test_clustered`). Benjamini-Hochberg FDR correction is applied
across those six p-values, not per-bucket. Effect sizes (mean residual
points) are reported with season-clustered bootstrap 95% CIs regardless of
significance, per SS7 of the guardrails doc.

NON-STATIONARITY. Findings are reported per-era (2018-2020, pre-17-game
season, vs 2021-2023, post-expansion) in addition to pooled, because the
2021 season-length change is a real discontinuity (16 vs 17 games) that
mechanically shifts games-missed baselines and total point scales.
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sys
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
from scoring import score_offensive_game, compute_vbd, ReplacementLevels  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
ADP_SOURCE = "ffc_half_ppr_12team"
ADP_TEAMS = 12
# This league's own measured replacement levels (ADR-029): 10 teams, 1 QB
# starter, RB/WR/TE flex split measured at 0.52/0.48/0.00.
LEVELS = ReplacementLevels()
TRAIN_SEASONS = [2018, 2019, 2020, 2021, 2022, 2023]
HOLDOUT_SEASON = 2024
ALL_SEASONS = TRAIN_SEASONS + [HOLDOUT_SEASON]
ERA_A = [2018, 2019, 2020]          # 16-game seasons
ERA_B = [2021, 2022, 2023]          # 17-game seasons (train only, 2024 held out)
POSITIONS = ("QB", "RB", "WR", "TE")

RNG_SEED = 20260730  # fixed, per docs/statistical-guardrails.md SS11 (never hash())


@dataclass
class PlayerSeasonRecord:
    season: int
    mfl_id: str
    gsis_id: Optional[str]
    name: str
    position: str
    adp_overall_rank: int
    adp_position_rank: int
    adp_round_12team: int
    actual_points: float          # raw season fantasy points, reported for reference only
    expected_points: float        # expected VALUE OVER REPLACEMENT at this ADP overall rank
    residual_points: float        # actual VBD - expected VBD (the effect-size unit throughout)
    age: Optional[float]
    prior_games_missed: Optional[int]
    team_change: Optional[bool]
    prior_volume_pctile: Optional[float]
    prior_efficiency_pctile: Optional[float]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def build_mfl_to_gsis(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute("SELECT mfl_id, source_id FROM player_ids WHERE source='gsis'").fetchall()
    return {str(mfl): gsis for mfl, gsis in rows}


def build_mfl_to_birthdate(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute(
        "SELECT mfl_id, birthdate FROM players_canonical WHERE birthdate IS NOT NULL"
    ).fetchall()
    return {str(mfl): bd for mfl, bd in rows}


def load_adp_universe(conn: sqlite3.Connection, season: int) -> List[dict]:
    rows = conn.execute(
        "SELECT mfl_id, player_name, position, team, rank, average_pick "
        "FROM ffc_adp_snapshots WHERE adp_source=? AND period=? AND position IN "
        "('QB','RB','WR','TE') ORDER BY rank ASC",
        (ADP_SOURCE, season),
    ).fetchall()
    return [
        {
            "mfl_id": str(r[0]) if r[0] is not None else None,
            "name": r[1],
            "position": r[2],
            "team": r[3],
            "adp_overall_rank": r[4],
            "average_pick": r[5],
        }
        for r in rows
        if r[0] is not None  # unresolved-to-canonical rows are unusable, dropped not guessed
    ]


def actual_points_and_vbd_by_gsis(conn: sqlite3.Connection, season: int) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """(points, vbd) for the FULL season player universe -- not just the ADP
    subset -- so the replacement-level floor used by compute_vbd is not
    itself distorted by ADP's survivorship cut. Position is each player's
    modal position across their season's weekly rows (matches
    backtest.py's `_season_actuals` convention)."""
    totals: Dict[str, float] = defaultdict(float)
    pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in db.actual_season_outcomes(conn, season, season_type="REG"):
        stats = {col: row[col] for col in db.SCORING_STAT_COLUMNS}
        pid = row["player_id"]
        totals[pid] += score_offensive_game(stats)
        pos_counts[pid][row["position"]] += 1

    by_position: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    modal_pos: Dict[str, str] = {}
    for pid, total in totals.items():
        pos = max(pos_counts[pid].items(), key=lambda kv: kv[1])[0]
        modal_pos[pid] = pos
        if pos in POSITIONS:
            by_position[pos].append((pid, total))
    vbd = compute_vbd(by_position, LEVELS)

    # Replacement-level floor per position -- needed so a player with ZERO
    # stats rows (a true bust: never played) still gets a defined VBD
    # (0 - replacement), instead of being silently dropped from the
    # analysis. compute_vbd only returns entries for players who scored
    # >=1 point in some game; a total bust is exactly CLAUDE.md SS6.2's
    # "most important observation in this whole analysis" and must not
    # disappear here.
    baselines = LEVELS.baselines()
    replacement_floor: Dict[str, float] = {}
    for pos in POSITIONS:
        ranked = sorted(by_position.get(pos, []), key=lambda x: -x[1])
        idx = min(baselines.get(pos, len(ranked)) - 1, len(ranked) - 1) if ranked else None
        replacement_floor[pos] = ranked[idx][1] if idx is not None and idx >= 0 else 0.0

    return dict(totals), vbd, replacement_floor


def games_played_by_gsis(conn: sqlite3.Connection, season: int) -> Dict[str, int]:
    rows = conn.execute(
        f"SELECT player_id, COUNT(DISTINCT week) FROM {db.SCORING_VIEW} "
        "WHERE season=? AND season_type='REG' GROUP BY player_id",
        (season,),
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def team_by_gsis(conn: sqlite3.Connection, season: int) -> Dict[str, str]:
    """Most common team for a player in a given season's REG weeks."""
    rows = conn.execute(
        "SELECT player_id, team, COUNT(*) c FROM player_weekly_stats "
        "WHERE season=? AND season_type='REG' AND team IS NOT NULL "
        "GROUP BY player_id, team",
        (season,),
    ).fetchall()
    best: Dict[str, Tuple[str, int]] = {}
    for pid, team, c in rows:
        if pid not in best or c > best[pid][1]:
            best[pid] = (team, c)
    return {pid: v[0] for pid, v in best.items()}


def volume_efficiency_by_gsis(conn: sqlite3.Connection, season: int) -> Dict[str, Tuple[str, float, float]]:
    """position, volume_metric, efficiency_metric for a season's REG stats.

    RB: volume = carries + targets; efficiency = (rushing_yards + receiving_yards) /
    max(carries+targets, 1).
    WR/TE: volume = targets; efficiency = yards per target (computed directly from raw
    totals rather than trusting the pre-computed racr column, which is per-week and would
    need its own weighted aggregation).
    QB: volume = attempts; efficiency = passing_epa per attempt.
    """
    rows = conn.execute(
        "SELECT player_id, position, "
        "SUM(carries) c, SUM(targets) t, SUM(rushing_yards) ry, SUM(receiving_yards) rcy, "
        "SUM(attempts) att, SUM(passing_epa) pepa "
        "FROM player_weekly_stats WHERE season=? AND season_type='REG' "
        "GROUP BY player_id, position",
        (season,),
    ).fetchall()
    out: Dict[str, Tuple[str, float, float]] = {}
    for pid, pos, c, t, ry, rcy, att, pepa in rows:
        c = c or 0
        t = t or 0
        ry = ry or 0
        rcy = rcy or 0
        att = att or 0
        pepa = pepa or 0.0
        if pos == "RB":
            vol = c + t
            eff = (ry + rcy) / vol if vol > 0 else None
        elif pos in ("WR", "TE"):
            vol = t
            eff = rcy / t if t > 0 else None
        elif pos == "QB":
            vol = att
            eff = pepa / att if att > 0 else None
        else:
            continue
        if eff is None:
            continue
        out[pid] = (pos, float(vol), float(eff))
    return out


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------

def compute_age(birthdate: Optional[str], season: int) -> Optional[float]:
    if not birthdate:
        return None
    try:
        y, m, d = (int(x) for x in birthdate.split("-"))
    except (ValueError, AttributeError):
        return None
    # Age as of Sept 1 of the given season -- a stable, pre-draft-observable
    # reference point close to Week 1 kickoff.
    ref = (season, 9, 1)
    age_years = ref[0] - y - (1 if (ref[1], ref[2]) < (m, d) else 0)
    return float(age_years)


def percentile_rank(value: float, pool: List[float]) -> float:
    if not pool:
        return 0.5
    below = sum(1 for v in pool if v < value)
    return below / len(pool)


def build_season_records(conn: sqlite3.Connection, season: int,
                          mfl_to_gsis: Dict[str, str],
                          mfl_to_birthdate: Dict[str, str]) -> List[PlayerSeasonRecord]:
    universe = load_adp_universe(conn, season)
    actual_pts, actual_vbd, replacement_floor = actual_points_and_vbd_by_gsis(conn, season)

    prior_season = season - 1
    prior_games = games_played_by_gsis(conn, prior_season)
    prior_team = team_by_gsis(conn, prior_season)
    this_team = team_by_gsis(conn, season)
    prior_vol_eff = volume_efficiency_by_gsis(conn, prior_season)

    games_expected_prior = 17 if prior_season >= 2021 else 16

    # attach actual points + VBD + gsis to each universe row. A player with
    # no gsis match or no stats row at all is a bust: points=0, and VBD
    # falls back to the position's replacement floor (0 - replacement),
    # never dropped (CLAUDE.md SS6.2).
    for u in universe:
        gsis = mfl_to_gsis.get(u["mfl_id"])
        u["gsis_id"] = gsis
        pts = actual_pts.get(gsis, 0.0) if gsis else 0.0
        u["actual_points"] = pts
        if gsis and gsis in actual_vbd:
            u["actual_vbd"] = actual_vbd[gsis]
        else:
            u["actual_vbd"] = 0.0 - replacement_floor.get(u["position"], 0.0)

    # OVERALL (cross-position) VBD value curve -- see module docstring for
    # why this must be VBD, not raw points, and not built per-position.
    #
    # BUG CAUGHT AND FIXED HERE, NOT AFTER PUBLISHING: FFC's own `rank`
    # column is the board rank INCLUDING PK (kickers), which this analysis
    # drops (POSITIONS = QB/RB/WR/TE only). That leaves gaps in `rank`
    # within the filtered universe (e.g. season 2022: 114 raw rows, 2 of
    # them PK, ranks up to 123 with gaps) -- indexing the value curve by
    # `adp_overall_rank - 1` therefore is NOT a valid 0..n-1 index into a
    # curve built from only 112 filtered rows, and silently clamps every
    # rank beyond the filtered length onto the SAME tail slot, breaking the
    # "residual sums to ~0 within a season" identity that is this design's
    # own internal consistency check (caught by adding that check and
    # finding a nonzero season-level sum: +1465.76 pts in season 2022
    # alone, entirely a bookkeeping artifact, not a finding). Fixed by using
    # each player's ORDINAL position after sorting the FILTERED universe by
    # `adp_overall_rank` ascending, not the raw rank value itself.
    universe.sort(key=lambda u: u["adp_overall_rank"])
    overall_value_curve = sorted((u["actual_vbd"] for u in universe), reverse=True)
    n_overall = len(overall_value_curve)
    ordinal_by_id = {id(u): i for i, u in enumerate(universe)}

    # per-position ADP-within-position rank (reported on the record, used
    # only for readability / diagnostics -- NOT for computing the residual)
    pos_rank_counter: Dict[str, int] = defaultdict(int)

    records: List[PlayerSeasonRecord] = []
    for pos in POSITIONS:
        # volume/efficiency percentile pools for this position, prior season
        pool_vol = [v[1] for pid, v in prior_vol_eff.items() if v[0] == pos]
        pool_eff = [v[2] for pid, v in prior_vol_eff.items() if v[0] == pos]

        for u in [x for x in universe if x["position"] == pos]:
            pos_rank_counter[pos] += 1
            adp_pos_rank = pos_rank_counter[pos]

            overall_idx = ordinal_by_id[id(u)]
            expected = overall_value_curve[overall_idx] if n_overall else 0.0
            residual = u["actual_vbd"] - expected

            gsis = u["gsis_id"]
            age = compute_age(mfl_to_birthdate.get(u["mfl_id"]), season)

            games_missed = None
            team_change = None
            vol_pctile = None
            eff_pctile = None
            if gsis and gsis in prior_games:
                gp = prior_games[gsis]
                games_missed = max(games_expected_prior - gp, 0)
                pt = prior_team.get(gsis)
                tt = this_team.get(gsis) or u["team"]
                if pt and tt:
                    team_change = (pt != tt)
                if gsis in prior_vol_eff:
                    _, vol, eff = prior_vol_eff[gsis]
                    vol_pctile = percentile_rank(vol, pool_vol)
                    eff_pctile = percentile_rank(eff, pool_eff)
            # else: rookie / not in league prior season -- leave None, excluded
            # from those specific factor families rather than guessed.

            records.append(PlayerSeasonRecord(
                season=season, mfl_id=u["mfl_id"], gsis_id=gsis, name=u["name"],
                position=pos, adp_overall_rank=u["adp_overall_rank"],
                adp_position_rank=adp_pos_rank,
                adp_round_12team=math.ceil(u["adp_overall_rank"] / ADP_TEAMS),
                actual_points=u["actual_points"], expected_points=expected,
                residual_points=residual, age=age,
                prior_games_missed=games_missed, team_change=team_change,
                prior_volume_pctile=vol_pctile, prior_efficiency_pctile=eff_pctile,
            ))
    return records


# ---------------------------------------------------------------------------
# Statistics: season-clustered bootstrap CI + permutation test
# ---------------------------------------------------------------------------

def clustered_bootstrap_mean_ci(records: List[PlayerSeasonRecord], n_boot: int = 2000,
                                 rng: Optional[random.Random] = None) -> Tuple[float, float, float, int]:
    """Bootstrap resampling AT THE SEASON level (not player-row level), per
    guardrails SS7 -- resample which seasons are included (with replacement),
    keep all rows from a chosen season, recompute the mean each time."""
    rng = rng or random.Random(RNG_SEED)
    by_season: Dict[int, List[float]] = defaultdict(list)
    for r in records:
        by_season[r.season].append(r.residual_points)
    seasons = sorted(by_season)
    if not seasons or not records:
        return (0.0, 0.0, 0.0, 0)
    point = statistics.fmean(r.residual_points for r in records)
    boot_means = []
    for _ in range(n_boot):
        chosen = [rng.choice(seasons) for _ in seasons]
        pooled = [v for s in chosen for v in by_season[s]]
        if pooled:
            boot_means.append(statistics.fmean(pooled))
    boot_means.sort()
    lo = boot_means[int(0.025 * len(boot_means))]
    hi = boot_means[int(0.975 * len(boot_means)) - 1]
    return (point, lo, hi, len(seasons))


def permutation_test_clustered(records: List[PlayerSeasonRecord], group_fn,
                                n_perm: int = 2000, rng: Optional[random.Random] = None) -> Optional[float]:
    """Two-sided permutation test on 'does the grouping variable predict
    residual_points', clustered by season: within each season, shuffle the
    group label across players THAT SEASON (preserves each season's own
    residual distribution and group-size balance), recompute the observed
    test statistic (weighted between-group variance of means, pooled across
    seasons) under permutation, compare to the true statistic.

    Returns None if fewer than 2 groups have data.
    """
    rng = rng or random.Random(RNG_SEED)
    by_season: Dict[int, List[PlayerSeasonRecord]] = defaultdict(list)
    for r in records:
        g = group_fn(r)
        if g is not None:
            by_season[r.season].append(r)
    if not by_season:
        return None

    def stat(assign: Dict[int, List[str]]) -> float:
        groups: Dict[str, List[float]] = defaultdict(list)
        for season, recs in by_season.items():
            labels = assign[season]
            for rec, lab in zip(recs, labels):
                groups[lab].append(rec.residual_points)
        if len(groups) < 2:
            return 0.0
        grand = statistics.fmean(v for vs in groups.values() for v in vs)
        total_n = sum(len(vs) for vs in groups.values())
        return sum(len(vs) * (statistics.fmean(vs) - grand) ** 2 for vs in groups.values()) / total_n

    real_assign = {s: [group_fn(r) for r in recs] for s, recs in by_season.items()}
    observed = stat(real_assign)

    count_ge = 0
    for _ in range(n_perm):
        perm_assign = {}
        for season, recs in by_season.items():
            labels = [group_fn(r) for r in recs]
            rng.shuffle(labels)
            perm_assign[season] = labels
        if stat(perm_assign) >= observed:
            count_ge += 1
    return (count_ge + 1) / (n_perm + 1)


def benjamini_hochberg(pvalues: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    items = [(k, v) for k, v in pvalues.items() if v is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adjusted: Dict[str, Optional[float]] = {k: None for k in pvalues}
    prev = 1.0
    for i in range(m - 1, -1, -1):
        k, p = items[i]
        rank = i + 1
        val = min(prev, p * m / rank)
        adjusted[k] = val
        prev = val
    return adjusted


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def group_mean_table(records: List[PlayerSeasonRecord], group_fn, order=None) -> Dict[str, Tuple[float, float, float, int, int]]:
    groups: Dict[str, List[PlayerSeasonRecord]] = defaultdict(list)
    for r in records:
        g = group_fn(r)
        if g is not None:
            groups[g].append(r)
    out = {}
    for g, recs in groups.items():
        point, lo, hi, n_seasons = clustered_bootstrap_mean_ci(recs)
        out[g] = (point, lo, hi, len(recs), n_seasons)
    if order:
        out = {k: out[k] for k in order if k in out}
    return out


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    mfl_to_gsis = build_mfl_to_gsis(conn)
    mfl_to_birthdate = build_mfl_to_birthdate(conn)

    all_records: List[PlayerSeasonRecord] = []
    for season in ALL_SEASONS:
        recs = build_season_records(conn, season, mfl_to_gsis, mfl_to_birthdate)
        all_records.extend(recs)
        print(f"season {season}: {len(recs)} player-season rows "
              f"({sum(1 for r in recs if r.gsis_id is None)} unmatched to gsis)")

    train = [r for r in all_records if r.season in TRAIN_SEASONS]
    holdout = [r for r in all_records if r.season == HOLDOUT_SEASON]
    era_a = [r for r in all_records if r.season in ERA_A]
    era_b = [r for r in all_records if r.season in ERA_B]

    print(f"\nTOTAL rows: {len(all_records)}  train(2018-2023): {len(train)}  "
          f"holdout(2024): {len(holdout)}")

    result: Dict = {"generated_from": ADP_SOURCE, "train_seasons": TRAIN_SEASONS,
                     "holdout_season": HOLDOUT_SEASON, "n_train_rows": len(train),
                     "n_holdout_rows": len(holdout), "families": {}}

    # --- Family 1: position ---
    pos_train = group_mean_table(train, lambda r: r.position, order=POSITIONS)
    pos_era_a = group_mean_table(era_a, lambda r: r.position, order=POSITIONS)
    pos_era_b = group_mean_table(era_b, lambda r: r.position, order=POSITIONS)
    pos_holdout = group_mean_table(holdout, lambda r: r.position, order=POSITIONS)
    p_position = permutation_test_clustered(train, lambda r: r.position)
    result["families"]["position"] = {
        "train": pos_train, "era_2018_2020": pos_era_a, "era_2021_2023": pos_era_b,
        "holdout_2024": pos_holdout, "p_value_raw": p_position,
    }

    # --- Family 2: ADP round bucket (12-team math) ---
    def round_bucket(r):
        rd = r.adp_round_12team
        if rd <= 3:
            return "round_1_3"
        if rd <= 8:
            return "round_4_8"
        return "round_9_plus"
    order_rb = ["round_1_3", "round_4_8", "round_9_plus"]
    rb_train = group_mean_table(train, round_bucket, order=order_rb)
    rb_era_a = group_mean_table(era_a, round_bucket, order=order_rb)
    rb_era_b = group_mean_table(era_b, round_bucket, order=order_rb)
    rb_holdout = group_mean_table(holdout, round_bucket, order=order_rb)
    p_round = permutation_test_clustered(train, round_bucket)
    result["families"]["adp_round_bucket"] = {
        "train": rb_train, "era_2018_2020": rb_era_a, "era_2021_2023": rb_era_b,
        "holdout_2024": rb_holdout, "p_value_raw": p_round,
    }

    # --- Family 3: age x position group ---
    def age_bucket(r):
        if r.age is None:
            return None
        group = "RB" if r.position == "RB" else ("QB" if r.position == "QB" else "PASS_CATCH")
        if r.age <= 23:
            band = "<=23"
        elif r.age <= 27:
            band = "24-27"
        else:
            band = "28+"
        return f"{group}:{band}"
    order_age = [f"{g}:{b}" for g in ("QB", "RB", "PASS_CATCH") for b in ("<=23", "24-27", "28+")]
    age_train = group_mean_table(train, age_bucket, order=order_age)
    age_era_a = group_mean_table(era_a, age_bucket, order=order_age)
    age_era_b = group_mean_table(era_b, age_bucket, order=order_age)
    age_holdout = group_mean_table(holdout, age_bucket, order=order_age)
    p_age = permutation_test_clustered(train, age_bucket)
    result["families"]["age_x_position"] = {
        "train": age_train, "era_2018_2020": age_era_a, "era_2021_2023": age_era_b,
        "holdout_2024": age_holdout, "p_value_raw": p_age,
        "n_missing_birthdate": sum(1 for r in train if r.age is None),
    }

    # --- Family 4: prior-season games missed ---
    def missed_bucket(r):
        if r.prior_games_missed is None:
            return None
        gm = r.prior_games_missed
        if gm == 0:
            return "0"
        if gm <= 3:
            return "1-3"
        return "4+"
    order_missed = ["0", "1-3", "4+"]
    gm_train = group_mean_table(train, missed_bucket, order=order_missed)
    gm_era_a = group_mean_table(era_a, missed_bucket, order=order_missed)
    gm_era_b = group_mean_table(era_b, missed_bucket, order=order_missed)
    gm_holdout = group_mean_table(holdout, missed_bucket, order=order_missed)
    p_missed = permutation_test_clustered(train, missed_bucket)
    result["families"]["prior_games_missed"] = {
        "train": gm_train, "era_2018_2020": gm_era_a, "era_2021_2023": gm_era_b,
        "holdout_2024": gm_holdout, "p_value_raw": p_missed,
        "n_excluded_rookie_or_unmatched": sum(1 for r in train if r.prior_games_missed is None),
    }

    # --- Family 5: team change ---
    def team_change_bucket(r):
        if r.team_change is None:
            return None
        return "changed_team" if r.team_change else "same_team"
    order_tc = ["same_team", "changed_team"]
    tc_train = group_mean_table(train, team_change_bucket, order=order_tc)
    tc_era_a = group_mean_table(era_a, team_change_bucket, order=order_tc)
    tc_era_b = group_mean_table(era_b, team_change_bucket, order=order_tc)
    tc_holdout = group_mean_table(holdout, team_change_bucket, order=order_tc)
    p_team = permutation_test_clustered(train, team_change_bucket)
    result["families"]["team_change"] = {
        "train": tc_train, "era_2018_2020": tc_era_a, "era_2021_2023": tc_era_b,
        "holdout_2024": tc_holdout, "p_value_raw": p_team,
        "note": "coach/coordinator identity is NOT ingested in this database "
                "(no play_callers rows in this worktree's nfl.db) -- this "
                "factor measures TEAM change only, not coordinator change, "
                "which the dispatch explicitly named as the reason coach_id "
                "is first-class in this schema. Reported as a narrower "
                "proxy, not the requested factor.",
    }

    # --- Family 6: prior volume vs efficiency split ---
    def vol_eff_bucket(r):
        if r.prior_volume_pctile is None or r.prior_efficiency_pctile is None:
            return None
        v, e = r.prior_volume_pctile, r.prior_efficiency_pctile
        if v >= 0.6 and e < 0.4:
            return "high_volume_low_efficiency"
        if v < 0.4 and e >= 0.6:
            return "low_volume_high_efficiency"
        if v >= 0.6 and e >= 0.6:
            return "high_volume_high_efficiency"
        if v < 0.4 and e < 0.4:
            return "low_volume_low_efficiency"
        return "middling"
    order_ve = ["high_volume_low_efficiency", "low_volume_high_efficiency",
                "high_volume_high_efficiency", "low_volume_low_efficiency", "middling"]
    ve_train = group_mean_table(train, vol_eff_bucket, order=order_ve)
    ve_era_a = group_mean_table(era_a, vol_eff_bucket, order=order_ve)
    ve_era_b = group_mean_table(era_b, vol_eff_bucket, order=order_ve)
    ve_holdout = group_mean_table(holdout, vol_eff_bucket, order=order_ve)
    p_ve = permutation_test_clustered(train, vol_eff_bucket)
    result["families"]["prior_volume_vs_efficiency"] = {
        "train": ve_train, "era_2018_2020": ve_era_a, "era_2021_2023": ve_era_b,
        "holdout_2024": ve_holdout, "p_value_raw": p_ve,
    }

    # --- Multiple comparisons correction across the 6 families ---
    raw_p = {fam: data["p_value_raw"] for fam, data in result["families"].items()}
    adj_p = benjamini_hochberg(raw_p)
    for fam in result["families"]:
        result["families"][fam]["p_value_bh_adjusted"] = adj_p[fam]

    out_path = REPO / "data" / "qa" / "adp-vs-production-2026-07-30.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nWrote {out_path}")

    for fam, data in result["families"].items():
        print(f"\n=== {fam} === raw p={data['p_value_raw']} bh_adj={data['p_value_bh_adjusted']}")
        for g, (pt, lo, hi, n, ns) in data["train"].items():
            print(f"  {g:30s} mean_residual={pt:+7.2f}  95%CI=[{lo:+7.2f},{hi:+7.2f}]  n={n:4d} seasons={ns}")


if __name__ == "__main__":
    main()
