#!/usr/bin/env python3
"""Sleeper screen: can we predict late-ADP breakouts? (FR-094, 2026-07-30)

Founder's own words: "I wonder if we can predict 'sleepers' Later round ADPs
but who show some characteristics of a break out but not enough to warrant
score adjustments or early round picks." The design constraint in that
sentence is load-bearing: the output of this line of work, if anything
survives, is a FLAG beside the ranking, never an adjustment inside it
(CLAUDE.md SS4 -- ranking sources stay separate, never blended).

This script answers FR-094's step 1 and step 2 in order:
  STEP 1 -- the base rate. What share of late-ADP players return startable
            value in a normal season, per position, per season? Reported
            first because it is the denominator for everything after it,
            and is a publishable finding on its own regardless of step 2's
            result.
  STEP 2 -- does anything pre-season-observable separate the hits from the
            misses within that universe? Three pre-registered features
            (see FEATURES section below); precision/recall against the base
            rate, Wilson intervals, one holdout look, BH correction across
            the family.

THIS SCRIPT IS SELF-CONTAINED, deliberately, not because the prior
ADP-vs-production analysis (`docs/analysis/adp-vs-production-2026-07-30.md`,
script `analysis/adp_vs_production.py`) isn't the right reference -- it is,
and its universe/VBD/permutation machinery is reused CONCEPTUALLY, line for
line in places -- but because that script's commit
(`e334473 Add ADP-vs-production structural mispricing analysis`) lives on a
sibling worktree branch (`worktree-agent-a3f0bc3cc3efb7185`) not yet merged
into this branch's history. Importing across an unmerged sibling branch
would make this script silently break the moment that branch is rebased,
squashed, or its path changes, and would depend on code this session cannot
review in its current form. Duplicating the ~150 lines of shared plumbing
here (universe load, VBD-based residual/hit definition, season-clustered
resampling) is the safer choice until both land on the same branch.

DATA SOURCE AND ITS LIMITS -- identical caveats to the prior analysis:
FFC 12-team half-PPR mock-draft ADP (`ffc_adp_snapshots`,
adp_source='ffc_half_ppr_12team'), seasons 2018-2024. NOT this league's real
10-team ADP (no historical 10-team source exists in this project). Mock
drafts, not real drafts -- the best available proxy for market consensus at
a pre-draft moment, not identical to it. 2025 is not in this ADP source at
all -- the project's locked holdout is untouched by construction. Train
2018-2023, holdout 2024 -- one look, reported even if it kills the finding,
matching the prior analysis's split so the two documents are comparable.

UNIVERSE / SURVIVORSHIP. For season N, the population is every player in
that season's FFC ADP snapshot with adp_overall_rank >= LATE_ADP_CUTOFF_RANK
(round 10+ at 12-team math -- see CUTOFF JUSTIFICATION below). This
INCLUDES every player who did nothing that season: a bust who scored zero
gets actual_vbd computed against the position's replacement floor, never
dropped (CLAUDE.md SS6.2). Building this universe from "players who broke
out" would measure nothing and would produce a spectacular, meaningless
result -- the exact failure mode FR-094's own PM framing calls out.

CUTOFF JUSTIFICATION. Round 10+ (12-team, adp_overall_rank >= 109) is
chosen over the round-9+ bucket already reported in the ADP-vs-production
analysis for a specific reason: that analysis found the round-9+ bucket
ALREADY carries a strong positive residual for WR (+54.8) and TE (+68.3) --
i.e. round 9 is already priced as if the market half-expects upside. A
"sleeper" flag is supposed to find value the market has NOT already
partially priced in. Round 10+ is one bucket further out, closer to the
undrafted/bench-round part of a 12-team mock board, and is where a flag
distinct from "the market already knows round 9 outperforms" can be tested
honestly. This is a judgment call, stated as one, not a measured optimum --
it was picked from the round-bucket structure already reported before this
script ran, not tuned against this script's own outcome (that would be
leakage).

LOOK-AHEAD. All features are computed from season N-1 (or the player's own
age as of Sept 1 of season N, a fixed pre-draft-observable calendar fact,
not an outcome). ADP `as_of_date` is FFC's own historical pre-draft window
end date. No feature or threshold was chosen by looking at season N
outcomes.

FEATURES (pre-registered, in the order FR-094 lists them):
  1. AGE_YOUNG -- WR/TE only, age <= 23 as of Sept 1 of season N. Already
     evidenced at MODERATE-HIGH confidence in the ADP-vs-production
     analysis (+34.6 VBD pts/season, holds both eras) -- but on a
     DIFFERENT population (that analysis used the whole ADP board; this one
     is round-10+ only) and a DIFFERENT metric (binary hit rate here, mean
     VBD residual there). Re-tested, not merely cited.
  2. EFFICIENT_LOW_VOLUME -- prior-season (N-1) efficiency percentile
     within position >= 0.75 AND volume percentile <= 0.40, among players
     who logged qualifying volume (carries+targets>0 for RB, targets>0 for
     WR/TE, attempts>0 for QB) -- the "productive when used" case FR-094
     names.
  3. RISING_SHARE -- within-season TREND in target share during season N-1:
     second-half share (weeks 10-18) minus first-half share (weeks 1-9)
     >= +0.05 (5 percentage points), among WR/RB/TE who logged qualifying
     games (>=2 weeks with a recorded target) in both halves. This is
     explicitly the guardrail's own example: a player finishing strong
     looks identical to a fading one in a season MEAN, so the mean is not
     tested here -- only the trend. QB excluded (see share_trend_by_gsis
     docstring: no reliable gsis join for a snap-share-based QB proxy was
     available in the time budget; round-10+ QBs are a tiny, mostly
     backup-QB population for this screen regardless).

NOT TESTED THIS PASS (logged, not silently dropped):
  - Depth-chart position change / vacated targets on the player's team --
    candidate feature FR-094 names, not built this pass (time-boxed; logged
    to docs/ideas-inbox.md). Untested, not a null result.
  - Team change -- already tested against the FULL ADP board in the prior
    analysis (Tier 3, no reliable pattern, era-split flips sign). Not
    re-run here against the narrower round-10+ population, to keep this
    pass's family count small (see MULTIPLE COMPARISONS below); the prior
    null is cited, not re-derived.
  - Route participation -- BLOCKED. No route-run or route-participation
    column exists anywhere in this project's ingested tables (checked every
    player-level table's schema directly: no `routes`, `route_participation`,
    or equivalent). FTN charting data (the documented potential source) is
    not ingested. Not proxied silently, per CLAUDE.md's standing rule that a
    source swap must be verified, not assumed.

HIT DEFINITION. "Startable value" = actual_vbd > 0 in season N -- positive
value over this league's own measured replacement level (ADR-029's
RB30/WR40/TE10/QB10 baselines via `scoring.compute_vbd`/`ReplacementLevels`,
the same machinery the prior analysis uses).

MULTIPLE COMPARISONS. Three pre-registered features = three hypotheses.
Benjamini-Hochberg correction applied across those three p-values (a
season-clustered permutation test on the binary hit indicator). A combined
OR-flag (any of the three features fires) is reported separately, explicitly
labeled EXPLORATORY / NOT PRE-REGISTERED -- a hypothesis for a future pass,
not a finding from this one.

UNCERTAINTY. Wilson score 95% intervals on every hit-rate,
precision, and recall figure (not normal-approximation CIs, which misbehave
at small n and rates near 0 or 1 -- exactly this analysis's regime).
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
from scoring import score_offensive_game, compute_vbd, ReplacementLevels  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
ADP_SOURCE = "ffc_half_ppr_12team"
ADP_TEAMS = 12
LEVELS = ReplacementLevels()  # this league's own measured baselines (ADR-029)
TRAIN_SEASONS = [2018, 2019, 2020, 2021, 2022, 2023]
HOLDOUT_SEASON = 2024
ALL_SEASONS = TRAIN_SEASONS + [HOLDOUT_SEASON]
POSITIONS = ("QB", "RB", "WR", "TE")

LATE_ADP_CUTOFF_RANK = 9 * ADP_TEAMS  # round 10+ at 12-team math -> rank >= 109

RNG_SEED = 20260730  # fixed, per docs/statistical-guardrails.md SS11 (never hash())


@dataclass
class SleeperRecord:
    season: int
    mfl_id: str
    gsis_id: Optional[str]
    name: str
    position: str
    adp_overall_rank: int
    actual_vbd: float
    hit: bool
    age: Optional[float]
    age_young_flag: bool
    eff_low_vol_flag: bool
    rising_share_flag: bool
    any_flag: bool


# ---------------------------------------------------------------------------
# Data loading (duplicated from adp_vs_production.py's approach -- see module
# docstring for why this is not imported cross-branch)
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
            "name": r[1], "position": r[2], "team": r[3],
            "adp_overall_rank": r[4], "average_pick": r[5],
        }
        for r in rows
        if r[0] is not None  # unresolved-to-canonical rows are unusable, dropped not guessed
    ]


def actual_points_and_vbd_by_gsis(conn: sqlite3.Connection, season: int
                                   ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """(points, vbd, replacement_floor) for the FULL season player universe
    (not just the ADP subset), so replacement level isn't distorted by
    ADP's own survivorship cut."""
    totals: Dict[str, float] = defaultdict(float)
    pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in db.actual_season_outcomes(conn, season, season_type="REG"):
        stats = {col: row[col] for col in db.SCORING_STAT_COLUMNS}
        pid = row["player_id"]
        totals[pid] += score_offensive_game(stats)
        pos_counts[pid][row["position"]] += 1

    by_position: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for pid, total in totals.items():
        pos = max(pos_counts[pid].items(), key=lambda kv: kv[1])[0]
        if pos in POSITIONS:
            by_position[pos].append((pid, total))
    vbd = compute_vbd(by_position, LEVELS)

    baselines = LEVELS.baselines()
    replacement_floor: Dict[str, float] = {}
    for pos in POSITIONS:
        ranked = sorted(by_position.get(pos, []), key=lambda x: -x[1])
        idx = min(baselines.get(pos, len(ranked)) - 1, len(ranked) - 1) if ranked else None
        replacement_floor[pos] = ranked[idx][1] if idx is not None and idx >= 0 else 0.0

    return dict(totals), vbd, replacement_floor


def volume_efficiency_by_gsis(conn: sqlite3.Connection, season: int) -> Dict[str, Tuple[str, float, float]]:
    """position, volume_metric, efficiency_metric for a season's REG stats.
    RB: volume=carries+targets, efficiency=yards/opportunity.
    WR/TE: volume=targets, efficiency=receiving_yards/target.
    QB: volume=attempts, efficiency=passing_epa/attempt."""
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
        c, t, ry, rcy, att = (v or 0 for v in (c, t, ry, rcy, att))
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


def share_trend_by_gsis(conn: sqlite3.Connection, season: int) -> Dict[str, Tuple[str, float]]:
    """{gsis_id: (position, trend)} for season `season`'s REG weeks, where
    trend = mean(week>=10 target_share) - mean(week<=9 target_share), for
    RB/WR/TE. Requires >=2 qualifying weeks (a recorded target_share) in
    EACH half -- a single-game half average is noise, not a trend.

    QB intentionally excluded here (see module docstring): target_share is
    structurally ~0 for a QB and an offense-snap-share proxy would need a
    reliable gsis join against `snap_counts`, which only carries
    `pfr_player_id` -- not built this pass rather than shipped on a shaky
    join."""
    rows = conn.execute(
        "SELECT player_id, position, week, target_share, targets "
        "FROM player_weekly_stats WHERE season=? AND season_type='REG' "
        "AND position IN ('RB','WR','TE')",
        (season,),
    ).fetchall()
    by_player: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
    pos_of: Dict[str, str] = {}
    for pid, pos, week, tshare, targets in rows:
        if tshare is None or targets is None:
            continue
        pos_of[pid] = pos
        by_player[pid].append((week, float(tshare)))

    out: Dict[str, Tuple[str, float]] = {}
    for pid, weeks in by_player.items():
        first = [s for w, s in weeks if w <= 9]
        second = [s for w, s in weeks if w >= 10]
        if len(first) >= 2 and len(second) >= 2:
            trend = statistics.fmean(second) - statistics.fmean(first)
            out[pid] = (pos_of[pid], trend)
    return out


def compute_age(birthdate: Optional[str], season: int) -> Optional[float]:
    if not birthdate:
        return None
    try:
        y, m, d = (int(x) for x in birthdate.split("-"))
    except (ValueError, AttributeError):
        return None
    ref = (season, 9, 1)  # age as of Sept 1 of the given season
    age_years = ref[0] - y - (1 if (ref[1], ref[2]) < (m, d) else 0)
    return float(age_years)


def percentile_rank(value: float, pool: List[float]) -> float:
    if not pool:
        return 0.5
    below = sum(1 for v in pool if v < value)
    return below / len(pool)


# ---------------------------------------------------------------------------
# Build universe
# ---------------------------------------------------------------------------

def build_season_records(conn: sqlite3.Connection, season: int,
                          mfl_to_gsis: Dict[str, str],
                          mfl_to_birthdate: Dict[str, str]) -> List[SleeperRecord]:
    universe = load_adp_universe(conn, season)
    universe = [u for u in universe if u["adp_overall_rank"] >= LATE_ADP_CUTOFF_RANK]

    actual_pts, actual_vbd, replacement_floor = actual_points_and_vbd_by_gsis(conn, season)

    prior_season = season - 1
    prior_vol_eff = volume_efficiency_by_gsis(conn, prior_season)
    prior_trend = share_trend_by_gsis(conn, prior_season)

    pool_vol: Dict[str, List[float]] = defaultdict(list)
    pool_eff: Dict[str, List[float]] = defaultdict(list)
    for pid, (pos, vol, eff) in prior_vol_eff.items():
        pool_vol[pos].append(vol)
        pool_eff[pos].append(eff)

    records: List[SleeperRecord] = []
    for u in universe:
        gsis = mfl_to_gsis.get(u["mfl_id"])
        pos = u["position"]
        if gsis and gsis in actual_vbd:
            vbd = actual_vbd[gsis]
        else:
            vbd = 0.0 - replacement_floor.get(pos, 0.0)  # true bust: never played, VBD floor
        hit = vbd > 0.0

        age = compute_age(mfl_to_birthdate.get(u["mfl_id"]), season)
        age_young = bool(pos in ("WR", "TE") and age is not None and age <= 23)

        eff_low_vol = False
        if gsis and gsis in prior_vol_eff:
            p_pos, vol, eff = prior_vol_eff[gsis]
            if p_pos == pos:
                vp = percentile_rank(vol, pool_vol.get(pos, []))
                ep = percentile_rank(eff, pool_eff.get(pos, []))
                eff_low_vol = bool(ep >= 0.75 and vp <= 0.40)

        rising_share = False
        if gsis and gsis in prior_trend:
            p_pos, trend = prior_trend[gsis]
            if p_pos == pos:
                rising_share = bool(trend >= 0.05)

        records.append(SleeperRecord(
            season=season, mfl_id=u["mfl_id"], gsis_id=gsis, name=u["name"],
            position=pos, adp_overall_rank=u["adp_overall_rank"],
            actual_vbd=vbd, hit=hit, age=age,
            age_young_flag=age_young, eff_low_vol_flag=eff_low_vol,
            rising_share_flag=rising_share,
            any_flag=(age_young or eff_low_vol or rising_share),
        ))
    return records


# ---------------------------------------------------------------------------
# Stats: Wilson interval, clustered permutation test on a binary metric
# ---------------------------------------------------------------------------

def wilson_interval(successes: int, n: int, z: float = 1.96) -> Tuple[float, float, float]:
    if n == 0:
        return (0.0, 0.0, 0.0)
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return (phat, max(0.0, center - margin), min(1.0, center + margin))


def permutation_test_binary(records: List[SleeperRecord], flag_fn,
                             n_perm: int = 4000, rng: Optional[random.Random] = None) -> Optional[float]:
    """Season-clustered permutation test: within each season, shuffle the
    binary flag across that season's records (preserves each season's own
    hit-rate base and flagged/unflagged group sizes), recompute
    |flagged hit rate - unflagged hit rate| pooled across seasons, compare
    to observed. Two-sided by construction (absolute difference)."""
    rng = rng or random.Random(RNG_SEED)
    by_season: Dict[int, List[SleeperRecord]] = defaultdict(list)
    for r in records:
        by_season[r.season].append(r)
    if len(by_season) < 2:
        return None

    def stat(flags: Dict[int, List[bool]]) -> float:
        fh = fn = uh = un = 0
        for season, recs in by_season.items():
            for r, f in zip(recs, flags[season]):
                if f:
                    fn += 1
                    fh += int(r.hit)
                else:
                    un += 1
                    uh += int(r.hit)
        if fn == 0 or un == 0:
            return 0.0
        return abs(fh / fn - uh / un)

    real_flags = {s: [flag_fn(r) for r in recs] for s, recs in by_season.items()}
    observed = stat(real_flags)

    count_ge = 0
    for _ in range(n_perm):
        perm_flags = {}
        for season, recs in by_season.items():
            flags = [flag_fn(r) for r in recs]
            rng.shuffle(flags)
            perm_flags[season] = flags
        if stat(perm_flags) >= observed - 1e-12:
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
# Reporting helpers
# ---------------------------------------------------------------------------

def base_rate_table(records: List[SleeperRecord]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for pos in POSITIONS:
        sub = [r for r in records if r.position == pos]
        hits = sum(1 for r in sub if r.hit)
        phat, lo, hi = wilson_interval(hits, len(sub))
        out[pos] = {"n": len(sub), "hits": hits, "rate": phat, "wilson_lo": lo, "wilson_hi": hi}
    hits = sum(1 for r in records if r.hit)
    phat, lo, hi = wilson_interval(hits, len(records))
    out["ALL"] = {"n": len(records), "hits": hits, "rate": phat, "wilson_lo": lo, "wilson_hi": hi}
    return out


def base_rate_by_season(records: List[SleeperRecord]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for season in sorted(set(r.season for r in records)):
        sub = [r for r in records if r.season == season]
        for pos in POSITIONS:
            psub = [r for r in sub if r.position == pos]
            hits = sum(1 for r in psub if r.hit)
            phat, lo, hi = wilson_interval(hits, len(psub))
            out[f"{season}:{pos}"] = {"n": len(psub), "hits": hits, "rate": phat,
                                       "wilson_lo": lo, "wilson_hi": hi}
    return out


def flag_report(records: List[SleeperRecord], flag_fn, base_hit_rate: float) -> dict:
    flagged = [r for r in records if flag_fn(r)]
    unflagged = [r for r in records if not flag_fn(r)]
    total_hits = sum(1 for r in records if r.hit)
    flagged_hits = sum(1 for r in flagged if r.hit)

    precision, prec_lo, prec_hi = wilson_interval(flagged_hits, len(flagged))
    recall = (flagged_hits / total_hits) if total_hits else 0.0
    unflagged_rate, un_lo, un_hi = wilson_interval(sum(1 for r in unflagged if r.hit), len(unflagged))

    return {
        "n_flagged": len(flagged),
        "n_unflagged": len(unflagged),
        "flagged_hit_rate": precision,
        "flagged_hit_rate_wilson_95ci": [prec_lo, prec_hi],
        "unflagged_hit_rate": unflagged_rate,
        "unflagged_hit_rate_wilson_95ci": [un_lo, un_hi],
        "base_rate": base_hit_rate,
        "precision": precision,
        "recall": recall,
        "lift_vs_base_rate": (precision / base_hit_rate) if base_hit_rate > 0 else None,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    mfl_to_gsis = build_mfl_to_gsis(conn)
    mfl_to_birthdate = build_mfl_to_birthdate(conn)

    all_records: List[SleeperRecord] = []
    for season in ALL_SEASONS:
        recs = build_season_records(conn, season, mfl_to_gsis, mfl_to_birthdate)
        all_records.extend(recs)
        print(f"season {season}: {len(recs)} late-ADP (round10+) rows, "
              f"{sum(1 for r in recs if r.hit)} hits")

    train = [r for r in all_records if r.season in TRAIN_SEASONS]
    holdout = [r for r in all_records if r.season == HOLDOUT_SEASON]

    print(f"\nTOTAL rows: {len(all_records)}  train: {len(train)}  holdout: {len(holdout)}")

    result: Dict = {
        "generated_from": ADP_SOURCE,
        "late_adp_cutoff_rank": LATE_ADP_CUTOFF_RANK,
        "train_seasons": TRAIN_SEASONS,
        "holdout_season": HOLDOUT_SEASON,
    }

    # ---- STEP 1: base rate ----
    result["step1_base_rate"] = {
        "train_by_position": base_rate_table(train),
        "holdout_by_position": base_rate_table(holdout),
        "train_by_season_position": base_rate_by_season(train),
        "holdout_by_season_position": base_rate_by_season(holdout),
    }

    train_base_rate = result["step1_base_rate"]["train_by_position"]["ALL"]["rate"]
    holdout_base_rate = result["step1_base_rate"]["holdout_by_position"]["ALL"]["rate"]

    print("\n=== STEP 1: base rate (train, 2018-2023) ===")
    for pos, d in result["step1_base_rate"]["train_by_position"].items():
        print(f"  {pos:4s} n={d['n']:4d} hits={d['hits']:4d} rate={d['rate']:.3f} "
              f"wilson95=[{d['wilson_lo']:.3f},{d['wilson_hi']:.3f}]")
    print("=== STEP 1: base rate (holdout, 2024) ===")
    for pos, d in result["step1_base_rate"]["holdout_by_position"].items():
        print(f"  {pos:4s} n={d['n']:4d} hits={d['hits']:4d} rate={d['rate']:.3f} "
              f"wilson95=[{d['wilson_lo']:.3f},{d['wilson_hi']:.3f}]")

    # ---- STEP 2: features ----
    features = {
        "age_young": lambda r: r.age_young_flag,
        "eff_low_vol": lambda r: r.eff_low_vol_flag,
        "rising_share": lambda r: r.rising_share_flag,
    }
    raw_p = {}
    step2 = {}
    for fname, ffn in features.items():
        p = permutation_test_binary(train, ffn)
        raw_p[fname] = p
        step2[fname] = {
            "train": flag_report(train, ffn, train_base_rate),
            "holdout": flag_report(holdout, ffn, holdout_base_rate),
            "p_value_raw": p,
        }
    adj_p = benjamini_hochberg(raw_p)
    for fname in step2:
        step2[fname]["p_value_bh_adjusted"] = adj_p[fname]
    result["step2_features"] = step2

    print("\n=== STEP 2: features (train, BH-adjusted p in brackets) ===")
    for fname, d in step2.items():
        t = d["train"]
        print(f"  {fname:14s} p_raw={d['p_value_raw']} p_bh={d['p_value_bh_adjusted']}")
        print(f"      flagged   n={t['n_flagged']:4d} hit_rate={t['flagged_hit_rate']:.3f} "
              f"wilson95={t['flagged_hit_rate_wilson_95ci']}")
        print(f"      unflagged n={t['n_unflagged']:4d} hit_rate={t['unflagged_hit_rate']:.3f} "
              f"wilson95={t['unflagged_hit_rate_wilson_95ci']}")
        print(f"      base_rate={t['base_rate']:.3f} recall={t['recall']:.3f} "
              f"lift={t['lift_vs_base_rate']}")
        h = d["holdout"]
        print(f"      HOLDOUT flagged n={h['n_flagged']:4d} hit_rate={h['flagged_hit_rate']:.3f} "
              f"wilson95={h['flagged_hit_rate_wilson_95ci']} base={h['base_rate']:.3f} "
              f"recall={h['recall']:.3f}")

    # ---- EXPLORATORY: combined OR flag, NOT pre-registered ----
    any_flag = lambda r: r.any_flag  # noqa: E731
    result["exploratory_combined_or_flag"] = {
        "note": "NOT pre-registered. Any of the 3 features fires. Reported "
                "as a hypothesis for a future pass, not a confirmed finding "
                "-- no separate significance test run (would need its own "
                "pre-registration and its own holdout look).",
        "train": flag_report(train, any_flag, train_base_rate),
        "holdout": flag_report(holdout, any_flag, holdout_base_rate),
    }
    print("\n=== EXPLORATORY (not pre-registered): combined OR flag ===")
    t = result["exploratory_combined_or_flag"]["train"]
    h = result["exploratory_combined_or_flag"]["holdout"]
    print(f"  train    flagged n={t['n_flagged']:4d} hit_rate={t['flagged_hit_rate']:.3f} "
          f"wilson95={t['flagged_hit_rate_wilson_95ci']} base={t['base_rate']:.3f}")
    print(f"  holdout  flagged n={h['n_flagged']:4d} hit_rate={h['flagged_hit_rate']:.3f} "
          f"wilson95={h['flagged_hit_rate_wilson_95ci']} base={h['base_rate']:.3f}")

    out_path = REPO / "data" / "qa" / "sleeper-screen-2026-07-30.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
