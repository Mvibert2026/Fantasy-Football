"""FR-085 Q1/Q2 -- who exactly does the early-round RB underperform, and is the
RB dead zone still there?

This module deliberately REUSES `analysis/adp_vs_production.py`'s residual
definition rather than re-deriving one, so every number here is directly
comparable to backend's 2026-07-30 report. Read that module's docstring for the
residual's construction and its two documented false starts.

WHAT THE RESIDUAL IS, AND THE ONE THING IT CANNOT DO
----------------------------------------------------
residual(player) = actual VBD - VBD of the season's own realised value curve at
that player's ADP ordinal. It is zero-sum within a season by construction: it
measures RELATIVE mispricing across the board, nothing else.

That makes it the right instrument for "is RB priced worse than WR at the same
draft cost" (Q1) and for "has that changed over time" (Q2). It is the WRONG
instrument for "should you draft an RB early" -- a player who returns less than
his slot's curve value can still be the correct pick if the drop-off behind him
is steeper than the drop-off behind the alternative. That question needs a draft
simulation and is answered in `sim.py`, not here.

TWO MARKET SOURCES
------------------
  ffc   FanballFootballCalculator half-PPR 12-team mock ADP, 2018-2024 (7
        seasons). Primary. 12-team, mock, not this league's 10-team real market.
  ecr   FantasyPros expert consensus rank, 2021-2024 (4 seasons). Independent
        second market; a different kind of consensus (experts, not mock
        drafters). 2025 is the sealed holdout and is excluded here in code, not
        by convention.

Run:
    .venv/bin/python -m experiments.strategy.residuals
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
from typing import Callable, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "analysis"))

import db  # noqa: E402
from scoring import score_offensive_game, compute_vbd, ReplacementLevels  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
POSITIONS = ("QB", "RB", "WR", "TE")
LEVELS = ReplacementLevels()
RNG_SEED = 20260730

HOLDOUT_SEASON = 2025  # sealed; never loaded by any code path in this module

FFC_SEASONS = (2018, 2019, 2020, 2021, 2022, 2023, 2024)
ECR_SEASONS = (2021, 2022, 2023, 2024)

# Era split. 2021 is the 17-game expansion, a real discontinuity. The seven FFC
# seasons split 3/2/2 so each era carries a comparable number of seasons; a
# per-season slope (which uses all seven and assumes nothing about where a break
# falls) is reported alongside, and it is the stronger of the two instruments.
ERAS_FFC = (("2018-2020", (2018, 2019, 2020)),
            ("2021-2022", (2021, 2022)),
            ("2023-2024", (2023, 2024)))


# ---------------------------------------------------------------- market boards
@dataclass
class BoardRow:
    season: int
    gsis_id: Optional[str]
    name: str
    position: str
    overall_rank: int          # ordinal within the QB/RB/WR/TE-filtered board
    raw_rank: int              # the source's own rank column (may include K/DEF)


def load_board_ffc(conn: sqlite3.Connection, season: int) -> List[BoardRow]:
    mfl_to_gsis = {str(m): g for m, g in conn.execute(
        "SELECT mfl_id, source_id FROM player_ids WHERE source='gsis'")}
    rows = conn.execute(
        "SELECT mfl_id, player_name, position, rank FROM ffc_adp_snapshots "
        "WHERE adp_source='ffc_half_ppr_12team' AND period=? "
        "AND position IN ('QB','RB','WR','TE') ORDER BY rank ASC",
        (season,)).fetchall()
    out = []
    for i, (mfl, name, pos, rank) in enumerate([r for r in rows if r[0] is not None]):
        out.append(BoardRow(season, mfl_to_gsis.get(str(mfl)), name, pos, i + 1, int(rank)))
    return out


def load_board_ecr(conn: sqlite3.Connection, season: int) -> List[BoardRow]:
    rows = conn.execute(
        "SELECT player_id, player_name, position, adp_rank FROM rankings "
        "WHERE source='fantasypros_ecr' AND season=? AND position IN ('QB','RB','WR','TE') "
        "ORDER BY adp_rank ASC", (season,)).fetchall()
    return [BoardRow(season, pid, name, pos, i + 1, int(rank))
            for i, (pid, name, pos, rank) in enumerate(rows)]


BOARD_LOADERS: Dict[str, Tuple[Callable, Sequence[int], int]] = {
    # name -> (loader, seasons, teams-per-round for the "round" label)
    "ffc": (load_board_ffc, FFC_SEASONS, 12),
    # Like-for-like control: FFC restricted to the seasons ECR covers. Without
    # this, any ffc-vs-ecr difference is confounded with the window.
    "ffc_2021_2024": (load_board_ffc, ECR_SEASONS, 12),
    "ecr": (load_board_ecr, ECR_SEASONS, 12),
}


# ---------------------------------------------------------------- realised value
def season_vbd(conn: sqlite3.Connection, season: int) -> Tuple[Dict[str, float], Dict[str, float]]:
    """(vbd by gsis_id, replacement floor by position) over the FULL season
    universe, so the floor is not distorted by the ADP board's own cut."""
    if season >= HOLDOUT_SEASON:
        raise RuntimeError(f"season {season} is at or past the sealed holdout")
    totals: Dict[str, float] = defaultdict(float)
    pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in db.actual_season_outcomes(conn, season, season_type="REG"):
        stats = {c: row[c] for c in db.SCORING_STAT_COLUMNS}
        totals[row["player_id"]] += score_offensive_game(stats)
        pos_counts[row["player_id"]][row["position"]] += 1
    by_pos: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for pid, tot in totals.items():
        pos = max(pos_counts[pid].items(), key=lambda kv: kv[1])[0]
        if pos in POSITIONS:
            by_pos[pos].append((pid, tot))
    vbd = compute_vbd(by_pos, LEVELS)
    baselines = LEVELS.baselines()
    floor = {}
    for pos in POSITIONS:
        ranked = sorted(by_pos.get(pos, []), key=lambda x: -x[1])
        if ranked:
            idx = min(baselines.get(pos, len(ranked)) - 1, len(ranked) - 1)
            floor[pos] = ranked[idx][1]
        else:
            floor[pos] = 0.0
    return vbd, floor


@dataclass
class Rec:
    season: int
    name: str
    position: str
    overall_rank: int
    pos_rank: int
    round_no: int
    actual_vbd: float
    expected_vbd: float
    residual: float


def build_records(conn: sqlite3.Connection, source: str) -> List[Rec]:
    loader, seasons, per_round = BOARD_LOADERS[source]
    out: List[Rec] = []
    for season in seasons:
        board = loader(conn, season)
        vbd, floor = season_vbd(conn, season)
        vals = []
        for b in board:
            v = vbd.get(b.gsis_id) if b.gsis_id else None
            if v is None:
                v = 0.0 - floor.get(b.position, 0.0)   # bust retained, never dropped
            vals.append(v)
        curve = sorted(vals, reverse=True)
        pos_counter: Dict[str, int] = defaultdict(int)
        for b, v in zip(board, vals):
            pos_counter[b.position] += 1
            exp = curve[b.overall_rank - 1]
            out.append(Rec(season, b.name, b.position, b.overall_rank,
                           pos_counter[b.position],
                           math.ceil(b.overall_rank / per_round),
                           v, exp, v - exp))
    return out


# ---------------------------------------------------------------- uncertainty
def season_bootstrap_mean(values_by_season: Dict[int, List[float]], n_boot: int = 4000,
                          seed: int = RNG_SEED) -> Tuple[float, float, float, int, int]:
    """Season-clustered bootstrap of a mean. Seasons are the resampling unit --
    players recur year over year, so resampling players would understate every
    interval."""
    seasons = sorted(values_by_season)
    flat = [v for s in seasons for v in values_by_season[s]]
    if not flat:
        return float("nan"), float("nan"), float("nan"), 0, 0
    point = statistics.fmean(flat)
    if len(seasons) < 2:
        return point, float("nan"), float("nan"), len(flat), len(seasons)
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        chosen = [rng.choice(seasons) for _ in seasons]
        pooled = [v for s in chosen for v in values_by_season[s]]
        if pooled:
            means.append(statistics.fmean(pooled))
    means.sort()
    lo = means[int(0.025 * len(means))]
    hi = means[min(len(means) - 1, int(0.975 * len(means)))]
    return point, lo, hi, len(flat), len(seasons)


def season_bootstrap_diff(a: Dict[int, List[float]], b: Dict[int, List[float]],
                          n_boot: int = 4000, seed: int = RNG_SEED
                          ) -> Tuple[float, float, float, int, int]:
    """Difference of two group means, resampling SEASONS jointly so the two
    groups stay paired within a resampled season."""
    seasons = sorted(set(a) & set(b))
    if not seasons:
        return float("nan"), float("nan"), float("nan"), 0, 0
    fa = [v for s in seasons for v in a[s]]
    fb = [v for s in seasons for v in b[s]]
    point = statistics.fmean(fa) - statistics.fmean(fb)
    if len(seasons) < 2:
        return point, float("nan"), float("nan"), len(fa) + len(fb), len(seasons)
    rng = random.Random(seed)
    diffs = []
    for _ in range(n_boot):
        chosen = [rng.choice(seasons) for _ in seasons]
        pa = [v for s in chosen for v in a[s]]
        pb = [v for s in chosen for v in b[s]]
        if pa and pb:
            diffs.append(statistics.fmean(pa) - statistics.fmean(pb))
    diffs.sort()
    return (point, diffs[int(0.025 * len(diffs))],
            diffs[min(len(diffs) - 1, int(0.975 * len(diffs)))], len(fa) + len(fb), len(seasons))


def grade(point: float, lo: float, hi: float) -> str:
    """Pass-1 SS0 grading, applied unchanged.

    SURVIVES  effect is many times its own standard error -- would survive any
              reasonable multiplicity correction.
    MARGINAL  clears zero but a CI endpoint sits near it. At this test count that
              is exactly what a false positive looks like; it is a hypothesis.
    NULL      does not clear zero.
    """
    if any(math.isnan(x) for x in (point, lo, hi)):
        return "NO-CI"
    if lo <= 0.0 <= hi:
        return "NULL"
    half = (hi - lo) / 2.0
    if half <= 0:
        return "NO-CI"
    z = abs(point) / (half / 1.96)
    return "SURVIVES" if z >= 3.0 else "MARGINAL"


def by_season(recs: Sequence[Rec]) -> Dict[int, List[float]]:
    out: Dict[int, List[float]] = defaultdict(list)
    for r in recs:
        out[r.season].append(r.residual)
    return dict(out)


def ols_slope_ci(xs: Sequence[float], ys: Sequence[float], n_boot: int = 4000,
                 seed: int = RNG_SEED) -> Tuple[float, float, float]:
    """Slope of y on x with a bootstrap over the (season) observations."""
    def slope(xv, yv):
        n = len(xv)
        mx, my = statistics.fmean(xv), statistics.fmean(yv)
        den = sum((x - mx) ** 2 for x in xv)
        if den == 0:
            return float("nan")
        return sum((x - mx) * (y - my) for x, y in zip(xv, yv)) / den
    point = slope(xs, ys)
    rng = random.Random(seed)
    n = len(xs)
    vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        xv = [xs[i] for i in idx]
        yv = [ys[i] for i in idx]
        s = slope(xv, yv)
        if not math.isnan(s):
            vals.append(s)
    if len(vals) < 100:
        return point, float("nan"), float("nan")
    vals.sort()
    return point, vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]


# ---------------------------------------------------------------- the questions
def round_bucket(r: Rec) -> str:
    if r.round_no <= 3:
        return "rounds_1_3"
    if r.round_no <= 8:
        return "rounds_4_8"
    return "rounds_9_plus"


ROUND_ORDER = ("rounds_1_3", "rounds_4_8", "rounds_9_plus")

# Q2 dead-zone bands, in POSITIONAL ADP rank. The classic "dead zone" claim is
# about backs priced as starters who are not bell-cows -- roughly RB13-RB30 in a
# 12-team room. Bands are declared here before any number is looked at.
RB_BANDS = (("RB1-6", 1, 6), ("RB7-12", 7, 12), ("RB13-24", 13, 24),
            ("RB25-36", 25, 36), ("RB37+", 37, 999))
WR_BANDS = (("WR1-6", 1, 6), ("WR7-12", 7, 12), ("WR13-24", 13, 24),
            ("WR25-36", 25, 36), ("WR37+", 37, 999))


def band_of(rank: int, bands) -> Optional[str]:
    for label, lo, hi in bands:
        if lo <= rank <= hi:
            return label
    return None


def run(source: str, out: Dict) -> int:
    """Returns the number of interval tests run, for the multiplicity ledger."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(db._CREATE_SCORING_VIEW_SQL)
    recs = build_records(conn, source)
    seasons = sorted({r.season for r in recs})
    print(f"\n########## source={source}  seasons={seasons}  rows={len(recs)}")
    res: Dict = {"seasons": seasons, "n_rows": len(recs)}
    n_tests = 0

    # ---- Q1: within a round bucket, RB against each other position separately.
    print("\n--- Q1: RB residual vs each other position, within round bucket "
          "(VBD pts, +ve = outperformed slot) ---")
    q1: Dict = {}
    for rb_bucket in ROUND_ORDER:
        sub = [r for r in recs if round_bucket(r) == rb_bucket]
        cell: Dict = {}
        for pos in POSITIONS:
            pr = [r for r in sub if r.position == pos]
            pt, lo, hi, n, ns = season_bootstrap_mean(by_season(pr))
            cell[pos] = dict(mean=pt, lo=lo, hi=hi, n=n, seasons=ns, grade=grade(pt, lo, hi))
            n_tests += 1
        for opp in ("WR", "TE", "QB"):
            a = by_season([r for r in sub if r.position == "RB"])
            b = by_season([r for r in sub if r.position == opp])
            pt, lo, hi, n, ns = season_bootstrap_diff(a, b)
            cell[f"RB_minus_{opp}"] = dict(mean=pt, lo=lo, hi=hi, n=n, seasons=ns,
                                           grade=grade(pt, lo, hi))
            n_tests += 1
        q1[rb_bucket] = cell
        print(f"\n  {rb_bucket}")
        for pos in POSITIONS:
            c = cell[pos]
            print(f"    {pos:14s} {c['mean']:+8.1f}  [{c['lo']:+8.1f},{c['hi']:+8.1f}]  "
                  f"n={c['n']:4d}  {c['grade']}")
        for opp in ("WR", "TE", "QB"):
            c = cell[f"RB_minus_{opp}"]
            print(f"    RB - {opp:9s} {c['mean']:+8.1f}  [{c['lo']:+8.1f},{c['hi']:+8.1f}]  "
                  f"{c['grade']}")
    res["q1_position_within_round"] = q1

    # ---- Q2a: RB residual by positional band, pooled and per era.
    print("\n--- Q2a: residual by positional ADP band (the dead-zone question) ---")
    q2: Dict = {}
    for pos, bands in (("RB", RB_BANDS), ("WR", WR_BANDS)):
        q2[pos] = {}
        for label, lo_r, hi_r in bands:
            sub = [r for r in recs if r.position == pos and lo_r <= r.pos_rank <= hi_r]
            pt, lo, hi, n, ns = season_bootstrap_mean(by_season(sub))
            n_tests += 1
            entry = dict(pooled=dict(mean=pt, lo=lo, hi=hi, n=n, seasons=ns,
                                     grade=grade(pt, lo, hi)))
            if source == "ffc":
                for era_name, era_seasons in ERAS_FFC:  # noqa: PLW2901
                    es = [r for r in sub if r.season in era_seasons]
                    ept, elo, ehi, en, ens = season_bootstrap_mean(by_season(es))
                    entry[era_name] = dict(mean=ept, lo=elo, hi=ehi, n=en, seasons=ens)
            per_season = {s: statistics.fmean([r.residual for r in sub if r.season == s])
                          for s in seasons if any(r.season == s for r in sub)}
            entry["per_season"] = per_season
            if len(per_season) >= 3:
                sl, slo, shi = ols_slope_ci(list(per_season.keys()), list(per_season.values()))
                entry["slope_per_season"] = dict(slope=sl, lo=slo, hi=shi,
                                                 grade=grade(sl, slo, shi))
                n_tests += 1
            q2[pos][label] = entry
            era_txt = ""
            if source == "ffc":
                era_txt = "  ".join(
                    f"{nm}:{q2[pos][label][nm]['mean']:+7.1f}" for nm, _ in ERAS_FFC)
            sl_txt = ""
            if "slope_per_season" in entry:
                s_ = entry["slope_per_season"]
                sl_txt = f"  slope={s_['slope']:+6.2f}/yr [{s_['lo']:+6.2f},{s_['hi']:+6.2f}] {s_['grade']}"
            print(f"  {label:8s} {pt:+8.1f} [{lo:+8.1f},{hi:+8.1f}] n={n:4d} "
                  f"{grade(pt, lo, hi):9s} {era_txt}{sl_txt}")
    res["q2_positional_bands"] = q2

    # ---- Q2a2: RB band MINUS the matching WR band. This is the control that
    # answers SS1.5 of backend's report: both bands sit at comparable positions
    # on the same realised value curve, so curve convexity / regression toward
    # the mean is held roughly constant and any gap left over is positional.
    print("\n--- Q2a2: RB band minus matching WR band (curve position held roughly constant) ---")
    band_diff: Dict = {}
    for (rb_label, rb_lo, rb_hi), (wr_label, wr_lo, wr_hi) in zip(RB_BANDS, WR_BANDS):
        a = by_season([r for r in recs if r.position == "RB" and rb_lo <= r.pos_rank <= rb_hi])
        b = by_season([r for r in recs if r.position == "WR" and wr_lo <= r.pos_rank <= wr_hi])
        pt, lo, hi, n, ns = season_bootstrap_diff(a, b)
        n_tests += 1
        # How well is curve position ACTUALLY held constant? If the two bands sit
        # at different mean overall ADP ranks they sit on different parts of the
        # value curve and the control is only partial. Reported, not assumed.
        rb_ovr = [r.overall_rank for r in recs
                  if r.position == "RB" and rb_lo <= r.pos_rank <= rb_hi]
        wr_ovr = [r.overall_rank for r in recs
                  if r.position == "WR" and wr_lo <= r.pos_rank <= wr_hi]
        mean_rb_ovr = statistics.fmean(rb_ovr) if rb_ovr else float("nan")
        mean_wr_ovr = statistics.fmean(wr_ovr) if wr_ovr else float("nan")
        band_diff[rb_label] = dict(vs=wr_label, mean=pt, lo=lo, hi=hi, n=n, seasons=ns,
                                   grade=grade(pt, lo, hi),
                                   mean_overall_rank_rb=mean_rb_ovr,
                                   mean_overall_rank_wr=mean_wr_ovr)
        print(f"  {rb_label:8s} - {wr_label:8s} {pt:+8.1f} [{lo:+8.1f},{hi:+8.1f}] "
              f"{grade(pt, lo, hi):9s} mean overall pick RB {mean_rb_ovr:6.1f} vs WR {mean_wr_ovr:6.1f}")
    res["q2a2_rb_minus_wr_by_band"] = band_diff

    # ---- Q2b: is the EARLY-round RB penalty itself shrinking?
    print("\n--- Q2b: early-round (1-3) RB minus WR gap, per season and its trend ---")
    early = [r for r in recs if round_bucket(r) == "rounds_1_3"]
    per_season_gap = {}
    for s in seasons:
        rb = [r.residual for r in early if r.season == s and r.position == "RB"]
        wr = [r.residual for r in early if r.season == s and r.position == "WR"]
        if rb and wr:
            per_season_gap[s] = statistics.fmean(rb) - statistics.fmean(wr)
    print("  per-season RB-WR gap:", {k: round(v, 1) for k, v in per_season_gap.items()})
    if len(per_season_gap) >= 3:
        sl, slo, shi = ols_slope_ci(list(per_season_gap.keys()), list(per_season_gap.values()))
        n_tests += 1
        print(f"  trend {sl:+.2f} VBD pts/season  [{slo:+.2f},{shi:+.2f}]  {grade(sl, slo, shi)}")
        res["q2b_early_rb_minus_wr_trend"] = dict(per_season=per_season_gap, slope=sl,
                                                  lo=slo, hi=shi, grade=grade(sl, slo, shi))

    out[source] = res
    return n_tests


def main() -> None:
    out: Dict = {}
    total = 0
    for source in ("ffc", "ffc_2021_2024", "ecr"):
        total += run(source, out)
    out["n_interval_tests"] = total
    print(f"\n==== {total} interval tests run in this module. "
          f"At the 5% level that is ~{0.05 * total:.1f} false 'clears zero' results "
          f"expected by chance alone. Grades above are the correction. ====")
    dest = REPO / "data" / "qa" / "fr085-residuals-2026-07-30.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
