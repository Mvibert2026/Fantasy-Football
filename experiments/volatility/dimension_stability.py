"""Which archetype dimensions behave like STABLE TRAITS and which are SITUATIONAL
ROLES -- measured, not assigned by intuition.

WHY. The founder's rule for the archetype proposal is *"we have multiple seasons
of history for most players -- the longer, the more confident we can be."* That is
correct for a stable trait and can be actively wrong for a situational one: a back
who was a committee player for three seasons and just became the lead back has a
long, consistent, now-wrong history, and pooling it more heavily encodes exactly
the stale role a drafter is trying to see past (`CLAUDE.md` §6.4, at player level).

So the decision rule for each dimension is empirical:

    high year-over-year autocorrelation  -> stable trait; career pooling helps
    low  year-over-year autocorrelation  -> situational; recent seasons only,
                                            and a role change should RESET rather
                                            than dilute

The hypothesis about where each dimension lands (aDOT stable, snap share
situational, ...) is a hypothesis. This module measures it. Where the measurement
and the hypothesis disagree, the measurement wins.

THE CONFOUND, CHECKED RATHER THAN ASSUMED AWAY. Career length is not a neutral
sample: players survive partly by being good, so long-career players may look more
classifiable because the marginal ones were cut before accumulating history.
Shrinking confidence by games observed would then quietly make confidence a
proxy for quality. §3 measures whether that bites.

Run:
    .venv/bin/python -m experiments.volatility.dimension_stability
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import db  # noqa: E402
from scoring import score_offensive_game  # noqa: E402
from experiments.volatility.volatility import (  # noqa: E402
    MIN_GAMES, HOLDOUT_SEASON, POSITIONS, RNG_SEED, SNAP_FIRST_SEASON,
    _snap_share_by_gsis, grade, pearson, player_bootstrap_corr, season_weeks)

DB_PATH = REPO / "data" / "nfl.db"
USAGE_FIRST_SEASON = 2009

# Candidate dimensions. Each is (label, hypothesised class, positions it applies
# to). The hypothesised class is recorded ONLY so the measurement can contradict
# it visibly -- it is never used to decide anything.
DIMENSIONS = [
    ("aDOT", "stable", ("WR", "TE", "RB")),
    ("catch_rate", "stable", ("WR", "TE", "RB")),
    ("yac_per_rec", "stable", ("WR", "TE", "RB")),
    ("qb_rush_share", "stable", ("QB",)),
    ("ypc", "stable", ("RB",)),
    ("target_share", "situational", ("WR", "TE", "RB")),
    ("snap_share_PROXY", "situational", ("WR", "TE", "RB")),
    ("rec_share_of_touches", "situational", ("RB",)),
    ("team_carry_share", "situational", ("RB",)),
    ("ppg", "reference", ("QB", "RB", "WR", "TE")),
]


def load(conn: sqlite3.Connection) -> Dict[Tuple[str, int], Dict]:
    out: Dict[Tuple[str, int], Dict] = {}
    for season in range(USAGE_FIRST_SEASON, HOLDOUT_SEASON):
        W = season_weeks(season)
        games: Dict[str, int] = defaultdict(int)
        pts: Dict[str, float] = defaultdict(float)
        pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for row in conn.execute(
                f"SELECT * FROM {db.SCORING_VIEW} WHERE season=? AND season_type='REG'",
                (season,)):
            if not (1 <= row["week"] <= W):
                continue
            pid = row["player_id"]
            games[pid] += 1
            pts[pid] += score_offensive_game({c: row[c] for c in db.SCORING_STAT_COLUMNS})
            pos_counts[pid][row["position"]] += 1
        agg: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        team_targets: Dict[str, float] = defaultdict(float)
        team_carries: Dict[str, float] = defaultdict(float)
        team_of: Dict[str, str] = {}
        for (pid, team, tg, rc, ay, ry, yac, cr, rushy, rushtd) in conn.execute(
                "SELECT player_id, team, SUM(COALESCE(targets,0)), SUM(COALESCE(receptions,0)), "
                "SUM(COALESCE(receiving_air_yards,0)), SUM(COALESCE(receiving_yards,0)), "
                "SUM(COALESCE(receiving_yards_after_catch,0)), SUM(COALESCE(carries,0)), "
                "SUM(COALESCE(rushing_yards,0)), SUM(COALESCE(rushing_tds,0)) "
                "FROM player_weekly_stats WHERE season=? AND season_type='REG' "
                "GROUP BY player_id, team", (season,)):
            a = agg[pid]
            for k, v in (("targets", tg), ("rec", rc), ("air", ay), ("recy", ry),
                         ("yac", yac), ("carries", cr), ("rushy", rushy), ("rushtd", rushtd)):
                a[k] += v or 0
            if team:
                team_targets[team] += tg or 0
                team_carries[team] += cr or 0
                team_of.setdefault(pid, team)
        snaps = _snap_share_by_gsis(conn, season)
        for pid, g in games.items():
            if g < MIN_GAMES:
                continue
            pos = max(pos_counts[pid].items(), key=lambda kv: kv[1])[0]
            if pos not in POSITIONS:
                continue
            a = agg[pid]
            tot = pts[pid]
            tt = team_targets.get(team_of.get(pid, ""), 0.0)
            tc = team_carries.get(team_of.get(pid, ""), 0.0)
            touches = a["targets"] + a["carries"]
            out[(pid, season)] = dict(
                position=pos, games=g, ppg=tot / g,
                aDOT=(a["air"] / a["targets"]) if a["targets"] >= 20 else None,
                catch_rate=(a["rec"] / a["targets"]) if a["targets"] >= 20 else None,
                yac_per_rec=(a["yac"] / a["rec"]) if a["rec"] >= 15 else None,
                ypc=(a["rushy"] / a["carries"]) if a["carries"] >= 40 else None,
                qb_rush_share=((a["rushy"] / 10.0 + a["rushtd"] * 6) / tot)
                if (pos == "QB" and tot > 0) else None,
                target_share=(a["targets"] / tt) if tt > 0 and a["targets"] >= 10 else None,
                snap_share_PROXY=snaps.get(pid),
                rec_share_of_touches=(a["targets"] / touches) if touches >= 20 else None,
                team_carry_share=(a["carries"] / tc) if tc > 0 and a["carries"] >= 20 else None,
            )
    return out


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(db._CREATE_SCORING_VIEW_SQL)
    data = load(conn)
    print(f"player-seasons {USAGE_FIRST_SEASON}-{HOLDOUT_SEASON - 1} with >= {MIN_GAMES} "
          f"games: {len(data)}")
    result: Dict = {"n": len(data), "dimensions": {}}
    n_tests = 0

    # ---- 1. year-over-year autocorrelation, per dimension per position
    print("\n=== 1. Year-over-year autocorrelation. This is what decides stable vs "
          "situational. ===")
    print(f"{'dimension':22s} {'hyp':12s} {'pos':4s} {'r(N,N+1)':>9s} {'95% CI':>19s} "
          f"{'n':>6s}  verdict")
    for label, hyp, positions in DIMENSIONS:
        result["dimensions"][label] = dict(hypothesised=hyp, by_position={})
        for pos in positions:
            pairs = []
            for (pid, season), rec in data.items():
                if rec["position"] != pos or rec.get(label) is None:
                    continue
                nxt = data.get((pid, season + 1))
                if nxt and nxt["position"] == pos and nxt.get(label) is not None:
                    pairs.append((pid, float(rec[label]), float(nxt[label])))
            r, lo, hi, n = player_bootstrap_corr(pairs)
            if n < 60:
                continue
            n_tests += 1
            # Verdict thresholds declared here, before the numbers were read.
            if math.isnan(r):
                verdict = "insufficient"
            elif r >= 0.60:
                verdict = "STABLE -- pool career"
            elif r >= 0.40:
                verdict = "mixed -- weight recent, pool with shrinkage"
            else:
                verdict = "SITUATIONAL -- recent only, reset on role change"
            result["dimensions"][label]["by_position"][pos] = dict(
                r=r, lo=lo, hi=hi, n=n, verdict=verdict)
            print(f"{label:22s} {hyp:12s} {pos:4s} {r:+9.3f} [{lo:+8.3f},{hi:+8.3f}] "
                  f"{n:6d}  {verdict}")

    # ---- 2. does pooling MORE history help or hurt? Direct test of the founder's rule.
    print("\n=== 2. Does more history help? r(mean of all prior seasons -> season N) "
          "vs r(season N-1 -> season N) ===")
    print(f"{'dimension':22s} {'pos':4s} {'r(prev only)':>13s} {'r(career mean)':>15s} "
          f"{'delta':>8s}  reading")
    hist: Dict = {}
    for label, hyp, positions in DIMENSIONS:
        for pos in positions:
            prev_pairs, career_pairs = [], []
            for (pid, season), rec in data.items():
                if rec["position"] != pos or rec.get(label) is None:
                    continue
                nxt = data.get((pid, season + 1))
                if not (nxt and nxt["position"] == pos and nxt.get(label) is not None):
                    continue
                prev_pairs.append((pid, float(rec[label]), float(nxt[label])))
                past = [float(data[(pid, s)][label])
                        for s in range(USAGE_FIRST_SEASON, season + 1)
                        if (pid, s) in data and data[(pid, s)].get(label) is not None]
                if len(past) >= 2:
                    career_pairs.append((pid, statistics.fmean(past), float(nxt[label])))
            if len(prev_pairs) < 60 or len(career_pairs) < 60:
                continue
            # restrict BOTH to the same rows -- players with >=2 prior seasons --
            # or the comparison is confounded with who has a career at all
            ids = {(p, a, b) for p, a, b in career_pairs}
            keys = {p for p, _, _ in career_pairs}
            prev_r = player_bootstrap_corr([x for x in prev_pairs if x[0] in keys])
            car_r = player_bootstrap_corr(career_pairs)
            n_tests += 2
            d = car_r[0] - prev_r[0]
            reading = ("career pooling HELPS" if d > 0.03 else
                       ("career pooling HURTS" if d < -0.03 else "no difference"))
            hist[f"{label}:{pos}"] = dict(prev_only=prev_r[0], career_mean=car_r[0],
                                          delta=d, n=car_r[3], reading=reading)
            print(f"{label:22s} {pos:4s} {prev_r[0]:+13.3f} {car_r[0]:+15.3f} "
                  f"{d:+8.3f}  {reading}")
    result["career_vs_recent"] = hist

    # ---- 3. the survivorship confound
    print("\n=== 3. Confound check -- is 'more history' partly just 'better player'? ===")
    career_games: Dict[str, int] = defaultdict(int)
    for (pid, _s), rec in data.items():
        career_games[pid] += rec["games"]
    seasons_seen: Dict[str, int] = defaultdict(int)
    for (pid, _s) in data:
        seasons_seen[pid] += 1
    conf = {}
    for pos in POSITIONS:
        xs, ys = [], []
        for (pid, season), rec in data.items():
            if rec["position"] != pos:
                continue
            xs.append(float(seasons_seen[pid]))
            ys.append(float(rec["ppg"]))
        if len(xs) < 100:
            continue
        r = pearson(xs, ys)
        n_tests += 1
        # how much of a PPG gap is it worth?
        long_ = [y for x, y in zip(xs, ys) if x >= 5]
        short = [y for x, y in zip(xs, ys) if x <= 2]
        conf[pos] = dict(r_seasons_vs_ppg=r,
                         ppg_long_career=statistics.fmean(long_) if long_ else float("nan"),
                         ppg_short_career=statistics.fmean(short) if short else float("nan"),
                         n_long=len(long_), n_short=len(short))
        print(f"  {pos}: corr(seasons observed, PPG) = {r:+.3f}   "
              f"PPG of players seen >=5 seasons {conf[pos]['ppg_long_career']:.2f} "
              f"(n={len(long_)}) vs <=2 seasons {conf[pos]['ppg_short_career']:.2f} "
              f"(n={len(short)})")
    result["survivorship_confound"] = conf

    result["n_interval_tests"] = n_tests
    print(f"\n==== {n_tests} interval/correlation tests; at 5% that is "
          f"~{0.05 * n_tests:.1f} false results by chance. ====")
    dest = REPO / "data" / "qa" / "fr095-dimension-stability-2026-07-30.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, default=str))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
