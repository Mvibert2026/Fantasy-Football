"""
Era and regime analysis over the full 1999-2025 league-level window (Task 3).

METHOD NOTE -- why not a Chow test. A Chow test requires the break date to be
specified in advance; using it to "find" breaks means quietly assuming the
answer (e.g. testing only at known rule-change years). This module instead uses
a **supremum-Wald (Quandt-Andrews) test for an unknown breakpoint**: compute the
Chow F statistic at every admissible break and take the maximum. Multiple breaks
are found by binary segmentation, the greedy form of Bai-Perron.

STATISTICAL HONESTY -- the sup-F statistic does not have an F distribution
(maximising over candidate breaks inflates it), so asymptotic F p-values would
be badly anti-conservative. p-values here come from a moving-block residual
bootstrap under the null of no break, seeded and recorded.

POWER WARNING. The series are ANNUAL: n = 27 observations. This is a small
sample for structural break detection. Treat detected breaks as suggestive
boundaries for deciding how far back to pool data, not as established facts.
A non-detection is weak evidence of no break, not evidence of stability.

TWO TREND QUESTIONS, KEPT SEPARATE. A regime's fitted slope answers "what has
this metric done across this whole regime". It does NOT answer "where is this
trend in its cycle right now" -- a metric that rose for a decade and has fallen
for five years still fits a positive line overall. `recent_trends` reports
trailing-window slopes for the cycle-position question. Read both.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

import db as dbmod

# Parameters per segment in the trend model: intercept + slope.
N_PARAMS = 2
DEFAULT_TRIM = 0.15
DEFAULT_MIN_SEGMENT = 5
DEFAULT_N_BOOTSTRAP = 2000
DEFAULT_ALPHA = 0.05
# Regimes are short, so the within-regime slope test uses a more permissive
# threshold than the break test. Stated explicitly rather than buried.
TREND_ALPHA = 0.10
RECENT_WINDOWS = (5, 10)
# Era similarity excludes the immediately preceding seasons: "2025 most
# resembles 2024" is trivially true and answers nothing.
DEFAULT_SIMILARITY_MIN_GAP = 5

METRICS = [
    "pass_rate",
    "neutral_pass_rate",
    "plays_per_game",
    "points_per_team_game",
    "qb_point_share",
    "rb_point_share",
    "wr_point_share",
    "te_point_share",
    "rb_carry_top30_share",
    "wr_target_top45_share",
]


@dataclass(frozen=True)
class BreakPoint:
    """A detected structural break. `season` is the LAST season of the earlier
    regime, i.e. the break falls between `season` and the next observation."""

    season: int
    sup_f: float
    p_value: float
    n_bootstrap: int


@dataclass(frozen=True)
class Regime:
    start_season: int
    end_season: int
    n_seasons: int
    mean: float
    slope_per_season: float
    slope_p_value: float
    trend: str  # "rising" | "declining" | "plateaued"


@dataclass(frozen=True)
class TrendWindow:
    window: int
    n_used: int
    slope_per_season: float
    p_value: float
    trend: str


@dataclass(frozen=True)
class MetricAnalysis:
    metric: str
    seasons: List[int]
    values: List[float]
    breaks: List[BreakPoint]
    regimes: List[Regime]
    recent_trends: Dict[int, TrendWindow]
    residual_autocorr_lag1: float
    has_season_gaps: bool
    seed: int
    n_bootstrap: int

    @property
    def current_regime(self) -> Optional[Regime]:
        return self.regimes[-1] if self.regimes else None


# --------------------------------------------------------------------------
# Numeric core. The time regressor is the ACTUAL season, not the row index, so
# that a series with excluded seasons (e.g. the 2003-2008 receiver-attribution
# gap) is not silently treated as contiguous -- otherwise "slope per season"
# would be wrong by the width of the gap.
# --------------------------------------------------------------------------


def _design(x: np.ndarray) -> np.ndarray:
    xc = x - x.mean()  # centred for numerical stability
    return np.column_stack([np.ones(len(x)), xc])


def _ols(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return beta, float(resid @ resid)


def chow_f(x: np.ndarray, y: np.ndarray, k: int) -> float:
    """Chow F for a break immediately before index k (segments [0:k], [k:n])."""
    n = len(y)
    if k < N_PARAMS or (n - k) < N_PARAMS:
        return 0.0
    _, rss_r = _ols(_design(x), y)
    _, rss1 = _ols(_design(x[:k]), y[:k])
    _, rss2 = _ols(_design(x[k:]), y[k:])
    rss_u = rss1 + rss2
    df_denom = n - 2 * N_PARAMS
    if df_denom <= 0 or rss_u <= 0:
        return 0.0
    return float(((rss_r - rss_u) / N_PARAMS) / (rss_u / df_denom))


def sup_wald(
    x: np.ndarray,
    y: np.ndarray,
    trim: float = DEFAULT_TRIM,
    min_segment: int = DEFAULT_MIN_SEGMENT,
) -> Tuple[Optional[int], float]:
    """(best_k, sup_F) over admissible break points."""
    n = len(y)
    lo = max(min_segment, int(np.floor(trim * n)), N_PARAMS)
    hi = min(n - min_segment, int(np.ceil((1 - trim) * n)), n - N_PARAMS)
    best_k, best_f = None, 0.0
    for k in range(lo, hi + 1):
        f = chow_f(x, y, k)
        if f > best_f:
            best_k, best_f = k, f
    return best_k, best_f


def _bootstrap_p_value(
    x: np.ndarray,
    y: np.ndarray,
    observed_f: float,
    seed: int,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    trim: float = DEFAULT_TRIM,
    min_segment: int = DEFAULT_MIN_SEGMENT,
    block_size: int = 3,
) -> float:
    """p-value under H0: no break, via a moving-block residual bootstrap.

    Blocks rather than iid draws because annual league series are plausibly
    autocorrelated; an iid bootstrap understates the null spread and makes the
    test anti-conservative. With n=27 neither block size is clearly correct,
    which is itself a reason to treat these p-values as approximate.
    """
    n = len(y)
    X = _design(x)
    beta, _ = _ols(X, y)
    fitted = X @ beta
    resid = y - fitted
    rng = np.random.default_rng(seed)

    n_blocks = int(np.ceil(n / block_size))
    max_start = max(1, n - block_size + 1)
    exceed = 0
    for _ in range(n_bootstrap):
        starts = rng.integers(0, max_start, size=n_blocks)
        boot = np.concatenate([resid[s : s + block_size] for s in starts])
        boot = boot[:n]
        if len(boot) < n:
            boot = np.concatenate([boot, resid[: n - len(boot)]])
        _, f_star = sup_wald(x, fitted + boot, trim=trim, min_segment=min_segment)
        if f_star >= observed_f:
            exceed += 1
    return (exceed + 1) / (n_bootstrap + 1)


def _lag1_autocorr(x: np.ndarray, y: np.ndarray) -> float:
    n = len(y)
    if n < 3:
        return 0.0
    X = _design(x)
    beta, _ = _ols(X, y)
    r = y - X @ beta
    den = float(r @ r)
    if den == 0:
        return 0.0
    return float(r[:-1] @ r[1:]) / den


def _slope_with_p(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """OLS slope PER SEASON and its two-sided p-value."""
    n = len(y)
    if n < 3:
        return 0.0, 1.0
    X = _design(x)
    beta, rss = _ols(X, y)
    df = n - N_PARAMS
    if df <= 0 or rss <= 0:
        return float(beta[1]), 1.0
    sigma2 = rss / df
    try:
        xtx_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        return float(beta[1]), 1.0
    se = float(np.sqrt(sigma2 * xtx_inv[1, 1]))
    if se == 0:
        return float(beta[1]), 1.0
    t = float(beta[1]) / se
    return float(beta[1]), float(2 * (1 - stats.t.cdf(abs(t), df)))


def _classify_trend(slope: float, p_value: float) -> str:
    if p_value >= TREND_ALPHA:
        return "plateaued"
    return "rising" if slope > 0 else "declining"


def detect_breaks(
    seasons: Sequence[int],
    values: Sequence[float],
    seed: int,
    alpha: float = DEFAULT_ALPHA,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    min_segment: int = DEFAULT_MIN_SEGMENT,
    _depth: int = 0,
) -> List[BreakPoint]:
    """Binary segmentation: find the strongest break; if significant, recurse
    into each side. Greedy form of Bai-Perron multiple-break search."""
    x = np.asarray(seasons, dtype=float)
    y = np.asarray(values, dtype=float)
    n = len(y)
    if n < 2 * min_segment or _depth > 3:
        return []
    k, f = sup_wald(x, y, min_segment=min_segment)
    if k is None or f <= 0:
        return []
    p = _bootstrap_p_value(
        x, y, f, seed=seed + _depth * 7919, n_bootstrap=n_bootstrap, min_segment=min_segment
    )
    if p > alpha:
        return []
    bp = BreakPoint(season=int(seasons[k - 1]), sup_f=f, p_value=p, n_bootstrap=n_bootstrap)
    left = detect_breaks(seasons[:k], values[:k], seed, alpha, n_bootstrap, min_segment, _depth + 1)
    right = detect_breaks(seasons[k:], values[k:], seed, alpha, n_bootstrap, min_segment, _depth + 1)
    return sorted(left + [bp] + right, key=lambda b: b.season)


def _recent_trends(seasons: np.ndarray, values: np.ndarray) -> Dict[int, TrendWindow]:
    out: Dict[int, TrendWindow] = {}
    for w in RECENT_WINDOWS:
        if len(values) < 3:
            continue
        xs, ys = seasons[-w:], values[-w:]
        if len(ys) < 3:
            continue
        slope, p = _slope_with_p(xs, ys)
        out[w] = TrendWindow(
            window=w,
            n_used=len(ys),
            slope_per_season=slope,
            p_value=p,
            trend=_classify_trend(slope, p),
        )
    return out


def analyze_metric(
    metric: str,
    seasons: Sequence[int],
    values: Sequence[Optional[float]],
    seed: int,
    alpha: float = DEFAULT_ALPHA,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
) -> MetricAnalysis:
    pairs = [
        (s, v) for s, v in zip(seasons, values)
        if v is not None and not (isinstance(v, float) and np.isnan(v))
    ]
    ss = [int(p[0]) for p in pairs]
    vv = np.array([float(p[1]) for p in pairs], dtype=float)
    xs = np.array(ss, dtype=float)

    has_gaps = bool(len(ss) > 1 and (np.diff(xs) != 1).any())

    breaks = detect_breaks(ss, list(vv), seed=seed, alpha=alpha, n_bootstrap=n_bootstrap)

    boundaries = [0] + [ss.index(b.season) + 1 for b in breaks] + [len(ss)]
    regimes: List[Regime] = []
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        seg_y, seg_x = vv[a:b], xs[a:b]
        if len(seg_y) == 0:
            continue
        slope, p = _slope_with_p(seg_x, seg_y)
        regimes.append(
            Regime(
                start_season=ss[a],
                end_season=ss[b - 1],
                n_seasons=len(seg_y),
                mean=float(seg_y.mean()),
                slope_per_season=slope,
                slope_p_value=p,
                trend=_classify_trend(slope, p),
            )
        )

    return MetricAnalysis(
        metric=metric,
        seasons=ss,
        values=[float(v) for v in vv],
        breaks=breaks,
        regimes=regimes,
        recent_trends=_recent_trends(xs, vv),
        residual_autocorr_lag1=_lag1_autocorr(xs, vv),
        has_season_gaps=has_gaps,
        seed=seed,
        n_bootstrap=n_bootstrap,
    )


def load_league_metrics(conn: sqlite3.Connection) -> Dict[str, object]:
    cur = conn.execute(
        f"SELECT season, {', '.join(METRICS)} FROM {dbmod.LEAGUE_METRICS_TABLE} ORDER BY season"
    )
    rows = cur.fetchall()
    seasons = [r[0] for r in rows]
    data = {m: [r[i + 1] for r in rows] for i, m in enumerate(METRICS)}
    return {"seasons": seasons, "data": data}


def most_similar_prior_season(
    seasons: Sequence[int],
    data: Dict[str, Sequence[Optional[float]]],
    target_season: int,
    min_gap: int = DEFAULT_SIMILARITY_MIN_GAP,
) -> Tuple[Optional[int], List[str], List[Tuple[int, float]]]:
    """Which earlier season does `target_season` most resemble?

    Excludes the `min_gap` seasons immediately prior: adjacent seasons are
    trivially the nearest neighbours and answer nothing about which *era*
    current conditions resemble. Uses z-scored metrics so units don't dominate.
    Returns (best_season, metrics_used, ranked_distances).
    """
    usable = [
        m for m, vals in data.items()
        if all(v is not None and not (isinstance(v, float) and np.isnan(v)) for v in vals)
    ]
    if not usable or target_season not in seasons:
        return None, usable, []

    idx = {s: i for i, s in enumerate(seasons)}
    z = {}
    for m in usable:
        arr = np.array([float(v) for v in data[m]], dtype=float)
        sd = arr.std()
        z[m] = (arr - arr.mean()) / sd if sd > 0 else arr * 0.0

    ti = idx[target_season]
    target_vec = np.array([z[m][ti] for m in usable])
    ranked: List[Tuple[int, float]] = []
    for s, i in idx.items():
        if s > target_season - min_gap:
            continue
        d = float(np.linalg.norm(np.array([z[m][i] for m in usable]) - target_vec))
        ranked.append((s, d))
    ranked.sort(key=lambda t: t[1])
    return (ranked[0][0] if ranked else None), usable, ranked


def analyze_all(
    conn: sqlite3.Connection,
    seed: int,
    alpha: float = DEFAULT_ALPHA,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
) -> Dict[str, MetricAnalysis]:
    payload = load_league_metrics(conn)
    seasons, data = payload["seasons"], payload["data"]
    return {
        m: analyze_metric(m, seasons, data[m], seed=seed, alpha=alpha, n_bootstrap=n_bootstrap)
        for m in METRICS
    }


def format_report(results: Dict[str, MetricAnalysis], conn: sqlite3.Connection) -> str:
    payload = load_league_metrics(conn)
    seasons, data = payload["seasons"], payload["data"]
    current = max(seasons)

    lines: List[str] = []
    lines.append("LEAGUE REGIME ANALYSIS (1999-2025)")
    lines.append("=" * 78)
    lines.append("Method: sup-Wald (Quandt-Andrews) unknown-breakpoint test;")
    lines.append("        binary segmentation for multiple breaks.")
    first = next(iter(results.values()))
    lines.append(
        f"p-values: moving-block residual bootstrap, {first.n_bootstrap} reps, seed={first.seed}."
    )
    lines.append(f"n = {len(seasons)} annual observations -- LOW POWER. Breaks are suggestive.")
    lines.append("Regime slope = whole-regime direction. 'recent' = where the trend is NOW.")
    lines.append("")

    for m, res in results.items():
        if not res.seasons:
            lines.append(f"{m}: no data\n")
            continue
        lines.append(f"--- {m}  [{res.seasons[0]}-{res.seasons[-1]}, n={len(res.seasons)}] ---")
        if res.has_season_gaps:
            missing = sorted(set(range(res.seasons[0], res.seasons[-1] + 1)) - set(res.seasons))
            lines.append(
                f"  EXCLUDED seasons (data unavailable, not zero-filled): "
                f"{missing[0]}-{missing[-1]}"
            )
        if res.breaks:
            for b in res.breaks:
                lines.append(f"  BREAK after {b.season}: sup-F={b.sup_f:.2f}, p={b.p_value:.4f}")
        else:
            lines.append("  no significant break detected")
        for r in res.regimes:
            lines.append(
                f"  regime {r.start_season}-{r.end_season} (n={r.n_seasons}): "
                f"mean={r.mean:.4f}, slope={r.slope_per_season:+.5f}/season "
                f"(p={r.slope_p_value:.3f}) -> {r.trend.upper()}"
            )
        for w in sorted(res.recent_trends):
            tw = res.recent_trends[w]
            lines.append(
                f"  recent last-{tw.window} (n={tw.n_used}): "
                f"slope={tw.slope_per_season:+.5f}/season (p={tw.p_value:.3f}) "
                f"-> {tw.trend.upper()}"
            )
        cur_regime = res.current_regime
        last5 = res.recent_trends.get(5)
        if cur_regime and last5 and cur_regime.trend != last5.trend:
            lines.append(
                f"  ** CYCLE FLAG: regime direction ({cur_regime.trend}) disagrees with "
                f"last-5 direction ({last5.trend}). The long-run average hides the turn."
            )
        if abs(res.residual_autocorr_lag1) > 0.4:
            lines.append(
                f"  NOTE: lag-1 residual autocorrelation {res.residual_autocorr_lag1:+.2f} "
                "is high; bootstrap p-value is approximate."
            )
        lines.append("")

    sim, usable, ranked = most_similar_prior_season(seasons, data, current)
    lines.append("--- ERA SIMILARITY ---")
    lines.append(
        f"  (seasons within {DEFAULT_SIMILARITY_MIN_GAP} years of {current} excluded -- "
        "adjacent seasons are trivially nearest)"
    )
    if sim is not None:
        lines.append(f"  {current} most resembles {sim} across {len(usable)} shared metrics.")
        top = ", ".join(f"{s} (d={d:.2f})" for s, d in ranked[:5])
        lines.append(f"  nearest: {top}")
        lines.append(f"  metrics used: {', '.join(usable)}")
    else:
        lines.append("  insufficient complete metrics for similarity comparison")
    lines.append("")

    lines.append("--- POOLABILITY ---")
    latest_break = max((b.season for r in results.values() for b in r.breaks), default=None)
    if latest_break is not None:
        lines.append(f"  Most recent detected break across all metrics: after {latest_break}.")
        lines.append(
            f"  Player-level factor models pooling seasons <= {latest_break} with seasons "
            f"> {latest_break} cross a detected regime boundary; per-regime coefficients "
            "are required (statistical-guardrails.md §4)."
        )
    else:
        lines.append("  No breaks detected in any metric; no evidence against pooling.")
        lines.append("  With n=27 this is weak evidence -- non-detection is not stability.")
    return "\n".join(lines)


def main() -> None:
    import argparse

    from config import DEFAULT_CONFIG

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=dbmod.DB_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_CONFIG.random_seed)
    parser.add_argument("--bootstrap", type=int, default=DEFAULT_N_BOOTSTRAP)
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    args = parser.parse_args()

    conn = dbmod.connect(args.db)
    try:
        results = analyze_all(conn, seed=args.seed, alpha=args.alpha, n_bootstrap=args.bootstrap)
        print(format_report(results, conn))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
