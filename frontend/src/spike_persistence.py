"""
PR-002 / test-registry #38b: is spike-week-ness a persistent player trait?

THE QUESTION. This league's stacking bonuses reward distribution SHAPE. The
project has treated that as its primary structural edge. The edge exists only if
"clears thresholds more often than volume alone implies" is a stable property of
a player. If the volume-adjusted residual does not persist year over year, then
bonus clearance is fully implied by projected yardage and carries no independent
information.

THE VOLUME ADJUSTMENT IS THE TEST, NOT A NUISANCE. A player averaging 90 yards a
game clears 100 far more often than one averaging 40. That is arithmetic and any
yardage projection already contains it. So the mechanical baseline IS the null
hypothesis: only the residual above it could be a tradeable trait.

Method, fixed in advance by docs/preregistration/PR-002-spike-week-persistence.md:
  1. player-season aggregates, receiving / rushing / passing separately
  2. expected clearance rate as a smooth games-weighted function of yards/game
  3. residual = observed clearance - expected(yards per game)
  4. YoY correlation of the residual, per position, CIs from a bootstrap that
     RESAMPLES PLAYERS so repeated appearances are not treated as independent

Uses weekly stats only. No cross-source joins, so neither the 2003-2008
receiver-attribution gap (which affects targets, not yards) nor the gsis_id
collision problem touches this test.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

import db as dbmod
import holdout as holdout_mod
from config import DEFAULT_CONFIG

# Pre-registered qualifying rules (PR-002). Changing any of these requires a new
# pre-registration id; they are constants here so they cannot drift silently.
MIN_GAMES = 8
MIN_YPG_SCRIMMAGE = 25.0
MIN_YPG_PASSING = 150.0

THRESHOLDS = {
    "receiving": (100, 150, 200),
    "rushing": (100, 150, 200),
    "passing": (300, 350, 400),
}
YARD_COLUMN = {
    "receiving": "receiving_yards",
    "rushing": "rushing_yards",
    "passing": "passing_yards",
}
# Positions tested per stat family. Declared up front so the set cannot be
# expanded after seeing which ones look interesting.
POSITIONS = {
    "receiving": ("WR", "RB", "TE"),
    "rushing": ("RB", "QB"),
    "passing": ("QB",),
}

# Regime boundaries detected by src/regimes.py (breaks after 2011 and 2019).
REGIMES = (("1999-2011", 1999, 2011), ("2012-2019", 2012, 2019), ("2020-2024", 2020, 2024))


@dataclass
class PlayerSeason:
    player_id: str
    season: int
    position: str
    games: int
    yards_per_game: float
    clearances: Dict[int, int]  # threshold -> games clearing it


@dataclass
class CorrelationResult:
    family: str
    position: str
    threshold: int
    n_pairs: int
    n_players: int
    pearson: float
    spearman: float
    ci_lo: float
    ci_hi: float
    p_value: float
    residual_sd: float
    degenerate_reason: Optional[str] = None


def load_player_seasons(
    conn: sqlite3.Connection, family: str, seasons: Sequence[int]
) -> List[PlayerSeason]:
    """Per player-season: games, yards/game, and clearance counts per threshold."""
    col = YARD_COLUMN[family]
    ths = THRESHOLDS[family]
    clear_sql = ", ".join(
        f"SUM(CASE WHEN COALESCE({col},0) >= {t} THEN 1 ELSE 0 END) AS c{t}" for t in ths
    )
    placeholders = ",".join("?" for _ in seasons)
    sql = f"""
        SELECT player_id, season, position,
               COUNT(*) AS games,
               SUM(COALESCE({col},0)) AS yards,
               {clear_sql}
        FROM player_weekly_stats
        WHERE season_type = 'REG' AND season IN ({placeholders})
              AND player_id IS NOT NULL AND position IS NOT NULL
        GROUP BY player_id, season, position
    """
    out: List[PlayerSeason] = []
    for row in conn.execute(sql, list(seasons)).fetchall():
        games = row["games"]
        if games <= 0:
            continue
        out.append(
            PlayerSeason(
                player_id=row["player_id"],
                season=row["season"],
                position=row["position"],
                games=games,
                yards_per_game=row["yards"] / games,
                clearances={t: row[f"c{t}"] for t in ths},
            )
        )
    return out


def qualifies(ps: PlayerSeason, family: str) -> bool:
    floor = MIN_YPG_PASSING if family == "passing" else MIN_YPG_SCRIMMAGE
    return ps.games >= MIN_GAMES and ps.yards_per_game >= floor


def fit_expected_curve(
    rows: Sequence[PlayerSeason], threshold: int, bin_width: float = 2.5
) -> Tuple[np.ndarray, np.ndarray]:
    """Games-weighted P(clear) as a function of yards/game.

    Binned rather than parametric: clearance-vs-volume is a smooth monotone
    relationship with no reason to assume a particular functional form, and with
    thousands of player-seasons the bins are well populated. The estimator is
    sum(clearances)/sum(games) within a bin, which is the correct
    games-weighted proportion -- an unweighted mean of per-season rates would
    over-count short seasons.
    """
    if not rows:
        return np.array([]), np.array([])
    ypg = np.array([r.yards_per_game for r in rows])
    games = np.array([r.games for r in rows], dtype=float)
    clears = np.array([r.clearances[threshold] for r in rows], dtype=float)

    lo, hi = ypg.min(), ypg.max()
    edges = np.arange(lo, hi + bin_width, bin_width)
    idx = np.clip(np.digitize(ypg, edges) - 1, 0, len(edges) - 2)

    centers, rates = [], []
    for b in range(len(edges) - 1):
        m = idx == b
        g = games[m].sum()
        if g < 50:  # too thin to estimate a rate from
            continue
        centers.append((edges[b] + edges[b + 1]) / 2.0)
        rates.append(clears[m].sum() / g)
    if len(centers) < 2:
        return np.array([]), np.array([])

    centers = np.array(centers)
    rates = np.array(rates)
    # light 3-point smoothing to damp bin-to-bin sampling noise
    if len(rates) >= 3:
        smooth = np.convolve(rates, np.ones(3) / 3.0, mode="same")
        smooth[0], smooth[-1] = rates[0], rates[-1]
        rates = smooth
    return centers, rates


def residuals(
    rows: Sequence[PlayerSeason], threshold: int, centers: np.ndarray, rates: np.ndarray
) -> Dict[Tuple[str, int], float]:
    if centers.size == 0:
        return {}
    out = {}
    for r in rows:
        expected = float(np.interp(r.yards_per_game, centers, rates))
        observed = r.clearances[threshold] / r.games
        out[(r.player_id, r.season)] = observed - expected
    return out


def build_pairs(res: Dict[Tuple[str, int], float]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Consecutive-season residual pairs. Returns (x, y, player_ids)."""
    xs, ys, pids = [], [], []
    for (pid, season), val in res.items():
        nxt = res.get((pid, season + 1))
        if nxt is None:
            continue
        xs.append(val)
        ys.append(nxt)
        pids.append(pid)
    return np.array(xs), np.array(ys), np.array(pids)


def player_clustered_bootstrap(
    x: np.ndarray, y: np.ndarray, pids: np.ndarray, seed: int, n_boot: int = 2000
) -> Tuple[float, float, float]:
    """(ci_lo, ci_hi, two-sided bootstrap p) resampling PLAYERS, not pairs.

    The same player contributes many consecutive-season pairs. Resampling pairs
    would treat those as independent evidence and produce an interval far too
    narrow -- the exact error statistical-guardrails.md §3 warns about.
    """
    unique = np.unique(pids)
    by_player = {p: np.where(pids == p)[0] for p in unique}
    rng = np.random.default_rng(seed)
    stats_out = []
    for _ in range(n_boot):
        picks = rng.choice(unique, size=len(unique), replace=True)
        idx = np.concatenate([by_player[p] for p in picks])
        bx, by = x[idx], y[idx]
        if bx.std() == 0 or by.std() == 0:
            continue
        stats_out.append(float(np.corrcoef(bx, by)[0, 1]))
    if not stats_out:
        return float("nan"), float("nan"), float("nan")
    arr = np.array(stats_out)
    lo, hi = float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))
    frac_le = float((arr <= 0).mean())
    p = 2.0 * min(frac_le, 1.0 - frac_le)
    return lo, hi, min(1.0, max(p, 1.0 / (len(arr) + 1)))


def analyse(
    conn: sqlite3.Connection,
    family: str,
    seasons: Sequence[int],
    seed: int,
    n_boot: int = 2000,
    season_filter: Optional[Tuple[int, int]] = None,
) -> List[CorrelationResult]:
    all_rows = load_player_seasons(conn, family, seasons)
    results: List[CorrelationResult] = []

    for position in POSITIONS[family]:
        pos_rows = [r for r in all_rows if r.position == position and qualifies(r, family)]
        if season_filter:
            lo, hi = season_filter
            pos_rows = [r for r in pos_rows if lo <= r.season <= hi]
        for threshold in THRESHOLDS[family]:
            centers, rates = fit_expected_curve(pos_rows, threshold)
            res = residuals(pos_rows, threshold, centers, rates)
            x, y, pids = build_pairs(res)

            reason = None
            if len(x) < 30:
                reason = f"only {len(x)} consecutive-season pairs"
            elif x.std() == 0 or y.std() == 0:
                reason = "residual has zero variance (threshold effectively never cleared)"
            elif float(np.mean([r.clearances[threshold] for r in pos_rows])) < 0.15:
                reason = (
                    "threshold cleared in <0.15 games per player-season on average; "
                    "residual is almost entirely structural zeros"
                )

            if reason:
                results.append(
                    CorrelationResult(
                        family, position, threshold, len(x), len(np.unique(pids)) if len(x) else 0,
                        float("nan"), float("nan"), float("nan"), float("nan"), float("nan"),
                        float(np.std(x)) if len(x) else float("nan"), reason,
                    )
                )
                continue

            pearson = float(np.corrcoef(x, y)[0, 1])
            spearman = float(stats.spearmanr(x, y).statistic)
            lo, hi, p = player_clustered_bootstrap(x, y, pids, seed=seed, n_boot=n_boot)
            results.append(
                CorrelationResult(
                    family, position, threshold, len(x), len(np.unique(pids)),
                    pearson, spearman, lo, hi, p, float(np.std(x)),
                )
            )
    return results


def format_results(results: Sequence[CorrelationResult], title: str) -> str:
    lines = [title, "-" * len(title)]
    lines.append(
        f"{'family':<10} {'pos':<4} {'thr':>4} {'pairs':>6} {'players':>8} "
        f"{'pearson':>8} {'spearman':>9} {'95% CI':>18} {'p':>8}"
    )
    for r in results:
        if r.degenerate_reason:
            lines.append(
                f"{r.family:<10} {r.position:<4} {r.threshold:>4} {r.n_pairs:>6} "
                f"{r.n_players:>8}   -- NOT TESTABLE: {r.degenerate_reason}"
            )
            continue
        ci = f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]"
        lines.append(
            f"{r.family:<10} {r.position:<4} {r.threshold:>4} {r.n_pairs:>6} {r.n_players:>8} "
            f"{r.pearson:>+8.3f} {r.spearman:>+9.3f} {ci:>18} {r.p_value:>8.4f}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=dbmod.DB_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_CONFIG.random_seed)
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()

    # Development seasons only. 2025 is the locked holdout.
    seasons = [s for s in range(1999, 2025)]
    holdout_mod.DEFAULT_LOCK.guard(seasons, purpose="PR-002 spike-week persistence")

    conn = dbmod.connect(args.db)
    try:
        print(f"PR-002: spike-week persistence")
        print(f"seasons: {seasons[0]}-{seasons[-1]} ({len(seasons)}), holdout "
              f"{holdout_mod.HOLDOUT_SEASON} excluded")
        print(f"seed={args.seed}  bootstrap={args.bootstrap}  "
              f"qualifying: games>={MIN_GAMES}, ypg>={MIN_YPG_SCRIMMAGE} "
              f"(passing {MIN_YPG_PASSING})")
        print()

        pooled: List[CorrelationResult] = []
        for family in ("receiving", "rushing", "passing"):
            pooled.extend(analyse(conn, family, seasons, args.seed, args.bootstrap))
        print(format_results(pooled, "POOLED 1999-2024"))
        print()

        for label, lo, hi in REGIMES:
            per_regime: List[CorrelationResult] = []
            for family in ("receiving", "rushing", "passing"):
                per_regime.extend(
                    analyse(conn, family, seasons, args.seed, max(500, args.bootstrap // 4),
                            season_filter=(lo, hi))
                )
            keep = [r for r in per_regime if r.threshold == 100 or r.threshold == 300]
            print(format_results(keep, f"REGIME {label} (primary thresholds only)"))
            print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
