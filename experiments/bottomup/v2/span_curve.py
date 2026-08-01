#!/usr/bin/env python
"""M-4 — how far back the panel CAN go, and how far back it SHOULD go.

    .venv/bin/python -m experiments.bottomup.v2.span_curve --feasibility
    .venv/bin/python -m experiments.bottomup.v2.span_curve --spans 2002,2006,2010,2012,2015,2018
    .venv/bin/python -m experiments.bottomup.v2.span_curve --spans 2002,2012 --ctx

TWO SEPARATE QUESTIONS, deliberately not merged (founder's framing, 2026-08-01):

  CAN   a data fact -- per feature family, the first usable season, the gaps, and
        the binding constraint on first_feature_season / first_target.
  SHOULD a measured result -- vary first_feature_season, hold the target seasons
        fixed at 2018-2024 so every span is scored on the identical evaluation
        set, and report the curve per position.

Holding the targets fixed is what makes the curve a curve. Extending the target
window as well would change the evaluation set and the training set at the same
time, and the two effects would be inseparable.

NOTHING HERE ADOPTS ANYTHING. `first_feature_season` stays at its committed
default; every value is passed per-run. Changing the default would silently move
every published control rho in B1, C1 and D1 (M-4's own instruction).

REGIME (CLAUDE.md 6.4, founder 2026-08-01 "regime change is real, we should take
it into account"). Two variants per span:

  raw  features as the model builds them today
  ctx  the era-sensitive features divided by that season's own league-season
       norm from `league_season_metrics` (1999-2025, 27 rows, read by no model
       until now), so a 2003 target share and a 2023 target share are in the
       same units.

What is ALREADY neutralised and must not be fixed twice: the evaluation metric
is a WITHIN-SEASON rank correlation, so pure scoring-level inflation is handled.
What is not handled is STRUCTURAL change -- positional point shares and workload
concentration -- which is exactly what this table measures. `ctx` therefore
normalises structure, not level.

No decay profile is fitted here. Recency weighting is strategist's live
pre-registration (`docs/preregistration/PR-DRAFT-lag-weight-decay-profile.md`)
and is deliberately untouched.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import adp_baseline as adp        # noqa: E402
from experiments.bottomup.components import pos_eval as E              # noqa: E402
from experiments.bottomup.components.pos_data import DEFAULT_DB        # noqa: E402
from experiments.bottomup.components.pos_eval import WalkForward       # noqa: E402
from experiments.bottomup.components.pos_features import LAG_WEIGHTS   # noqa: E402
from experiments.bottomup.v2.availability_data import build_avail_panel  # noqa: E402
from experiments.bottomup.v2.availability_features import build_features_d1  # noqa: E402

OUT = _REPO / "experiments" / "bottomup" / "results"
CELLS = OUT / "span_curve_cells.csv"
FEAS = OUT / "span_feasibility.csv"

HOLDOUT_SEASON = 2025
FIRST_TARGET, LAST_TARGET = 2018, 2024      # held fixed across every span
POSITIONS = ("QB", "RB", "WR", "TE")
BOOT_REPS, BOOT_SEED = 4000, 20260801
N_LAGS = 3
MIN_TRAIN_SEASONS = 2


# ------------------------------------------------------------- CAN: the facts
_COVERAGE_SQL = """
SELECT season,
       SUM(COALESCE(targets,0))              AS targets,
       SUM(COALESCE(receiving_air_yards,0))  AS air_yards,
       SUM(COALESCE(carries,0))              AS carries,
       SUM(COALESCE(attempts,0))             AS attempts,
       SUM(COALESCE(receptions,0))           AS receptions,
       SUM(COALESCE(receiving_yards,0))      AS rec_yards,
       SUM(COALESCE(rushing_yards,0))        AS rush_yards,
       SUM(COALESCE(passing_yards,0))        AS pass_yards,
       COUNT(*)                              AS rows
FROM player_weekly_stats
WHERE season_type='REG' AND position IN ('QB','RB','WR','TE','FB')
GROUP BY season ORDER BY season
"""

#: a source is "usable" in a season when its volume is at least this fraction of
#: that column's own median across seasons. Catches the 2003-2008 targets hole
#: without hand-listing it.
USABLE_FRAC = 0.25


def feasibility(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cov = pd.read_sql_query(_COVERAGE_SQL, conn)
        tables = {}
        for t in ("depth_charts_weekly", "rosters_weekly", "injuries",
                  "snap_counts", "participation", "ngs_receiving", "pbp",
                  "ff_opportunity", "league_season_metrics"):
            try:
                r = conn.execute(
                    f"SELECT MIN(CAST(season AS INT)), MAX(CAST(season AS INT)), "
                    f"COUNT(*) FROM {t}").fetchone()
                tables[t] = r
            except sqlite3.OperationalError:
                tables[t] = (None, None, 0)
    finally:
        conn.close()

    rows: List[Dict] = []
    for col in ("targets", "air_yards", "carries", "attempts", "receptions",
                "rec_yards", "rush_yards", "pass_yards"):
        med = cov[col].median()
        ok = cov.loc[cov[col] >= USABLE_FRAC * med, "season"]
        gaps = sorted(set(range(int(cov.season.min()), int(cov.season.max()) + 1))
                      - set(ok.astype(int)))
        first_clean = int(ok.min())
        # earliest feature season with N_LAGS clean lags and no gap inside them
        feasible = [s for s in range(first_clean + N_LAGS, int(cov.season.max()) + 1)
                    if not any(g in gaps for g in range(s - N_LAGS, s))]
        ff = min(feasible) if feasible else None
        rows.append(dict(family=f"player_weekly_stats.{col}",
                         first_season=first_clean,
                         gap_seasons=",".join(str(g) for g in gaps) or "none",
                         earliest_first_feature_season=ff,
                         earliest_first_target=(ff + MIN_TRAIN_SEASONS) if ff else None,
                         binding="N_LAGS=3 + gap" if gaps else "N_LAGS=3"))
    for t, (a, b, n) in tables.items():
        if not n:
            rows.append(dict(family=t, first_season=None, gap_seasons="TABLE ABSENT",
                             earliest_first_feature_season=None,
                             earliest_first_target=None, binding="absent"))
            continue
        ff = int(a) + 1          # a lagged feature needs one prior season
        rows.append(dict(family=t, first_season=int(a), gap_seasons=f"through {int(b)}",
                         earliest_first_feature_season=ff,
                         earliest_first_target=ff + MIN_TRAIN_SEASONS,
                         binding="source start season"))
    for fmt in ("half_ppr_12team", "ppr_12team", "non_ppr_12team"):
        seasons = adp.adp_seasons(fmt)
        rows.append(dict(family=f"ADP {fmt} (evaluation universe definer)",
                         first_season=min(seasons) if seasons else None,
                         gap_seasons=f"{len(seasons)} seasons",
                         earliest_first_feature_season=None,
                         earliest_first_target=min(seasons) if seasons else None,
                         binding="ADP archive"))
    rows.append(dict(family="NO ADP (full-veteran-universe endpoint)",
                     first_season=1999, gap_seasons="none",
                     earliest_first_feature_season=2002,
                     earliest_first_target=2004,
                     binding="N_LAGS=3 + min_train_seasons=2"))
    return pd.DataFrame(rows)


# ------------------------------------------------- SHOULD: the measured curve
_CTX_SQL = "SELECT * FROM league_season_metrics ORDER BY season"

#: feature column -> league-season metric it is normalised by. Only metrics
#: populated on every season 1999-2025 are used; `rb_carry_top30_share` and
#: `wr_target_top45_share` are NULL across the 2003-2008 targets hole and are
#: deliberately NOT used, because a normaliser with the same gap as the feature
#: would reintroduce the gap as a time dummy (batch 7 D2).
CTX_MAP: Dict[str, str] = {
    "ppg_w": "points_per_team_game",
    "pts_pg_w": "points_per_team_game",
    "pts_1": "points_per_team_game", "pts_2": "points_per_team_game",
    "pts_3": "points_per_team_game",
    "tgt_pg_w": "plays_per_game", "carries_pg_w": "plays_per_game",
    "att_pg_w": "plays_per_game", "opp_pg_w": "plays_per_game",
    "passyds_pg_w": "plays_per_game", "recyds_pg_w": "plays_per_game",
    "rushyds_pg_w": "plays_per_game",
}
#: position -> the point-share column that measures that position's structural
#: weight in the league. Applied to the points columns on top of CTX_MAP.
POS_SHARE = {"QB": "qb_point_share", "RB": "rb_point_share",
             "WR": "wr_point_share", "TE": "te_point_share"}
#: reference season all normalisers are expressed relative to, so `ctx` features
#: keep the same scale as `raw` and nothing else in the model has to change.
CTX_REF_SEASON = 2024


def load_ctx(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        m = pd.read_sql_query(_CTX_SQL, conn)
    finally:
        conn.close()
    return m.set_index("season")


def _lagged_norm(metric: pd.Series, target_season: int) -> float:
    """The lag-weighted league norm behind a recency-weighted feature.

    `build_features` collapses lags 1-3 with LAG_WEIGHTS, so the matching
    normaliser is those weights applied to the same three seasons' metrics.
    Transparent and parameter-free; it is arithmetic on a published table, not
    a fit."""
    num = den = 0.0
    for k in range(1, N_LAGS + 1):
        s = target_season - k
        if s in metric.index and np.isfinite(metric.loc[s]):
            num += LAG_WEIGHTS[k - 1] * float(metric.loc[s])
            den += LAG_WEIGHTS[k - 1]
    if den <= 0:
        return np.nan
    return num / den


def contextualise(f: pd.DataFrame, target_season: int, position: str,
                  ctx: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    for col, metric_col in CTX_MAP.items():
        if col not in f.columns or metric_col not in ctx.columns:
            continue
        norm = _lagged_norm(ctx[metric_col], target_season)
        ref = float(ctx[metric_col].loc[CTX_REF_SEASON])
        if not np.isfinite(norm) or norm <= 0:
            continue
        f[col] = pd.to_numeric(f[col], errors="coerce") * (ref / norm)
    share_col = POS_SHARE.get(position)
    if share_col and share_col in ctx.columns:
        norm = _lagged_norm(ctx[share_col], target_season)
        ref = float(ctx[share_col].loc[CTX_REF_SEASON])
        if np.isfinite(norm) and norm > 0:
            for col in ("ppg_w", "pts_pg_w", "pts_1", "pts_2", "pts_3"):
                if col in f.columns:
                    f[col] = pd.to_numeric(f[col], errors="coerce") * (ref / norm)
    return f


def _feature_fn(variant: str, position: str, ctx: pd.DataFrame):
    def fn(panel, universe, target_season):
        f = build_features_d1(panel, universe, target_season, blocks=())
        if variant == "ctx":
            f = contextualise(f, target_season, position, ctx)
        return f
    return fn


def run_span(panel, ctx: pd.DataFrame, first_feature: int, variant: str,
             positions=POSITIONS) -> pd.DataFrame:
    rows: List[Dict] = []
    # A span starting at S cannot produce a training pair for target S or S+1:
    # `_pairs` iterates range(first_feature_season, target) and needs
    # MIN_TRAIN_SEASONS entries. Clamping here rather than letting pandas raise
    # "No objects to concatenate" -- and `curve_report` joins on season, so a
    # clamped span is compared only on the seasons it actually covers, with its
    # own n_seasons reported rather than silently borrowed from the baseline.
    ft = max(FIRST_TARGET, first_feature + MIN_TRAIN_SEASONS)
    for pos in positions:
        wf = WalkForward(
            panel=panel, position=pos, first_target=ft,
            last_target=LAST_TARGET, min_train_seasons=MIN_TRAIN_SEASONS,
            avail_arm="A", calibrate_bonus=True,
            first_feature_season=first_feature,
            feature_fn=_feature_fn(variant, pos, ctx),
            allow_preseason_proxy=False)
        players, _ = wf.run()
        aud = pd.DataFrame(wf.audit)
        assert (aud.max_feature_cutoff < aud.season).all(), "feature leak"
        assert (aud.max_outcome_season < aud.season).all(), "outcome leak"
        assert (aud.n_outcome_reads_at_target == 0).all(), "target read"
        assert (aud.n_preseason_proxy_reads == 0).all(), "proxy read"
        assert players["season"].max() < HOLDOUT_SEASON, "HOLDOUT TOUCHED"
        for season, g in players.groupby("season"):
            vet = g[g["entry"] == "veteran"]
            sub = vet[vet["average_pick"].notna()]
            row = dict(span=first_feature, variant=variant, position=pos,
                       season=int(season), n_train=int(season - first_feature),
                       n_board_vet=len(sub), n_vet=len(vet))
            if len(sub) >= 10:
                row["rho_points"] = E.spearman(
                    sub["proj_points"].to_numpy(dtype=float),
                    sub["points"].to_numpy(dtype=float))
                row["rho_games"] = E.spearman(
                    sub["proj_games"].to_numpy(dtype=float),
                    sub["games"].to_numpy(dtype=float))
                row["mae_games"] = float(np.mean(np.abs(
                    sub["proj_games"] - sub["games"])))
            if len(vet) >= 10:
                row["rho_points_fullvet"] = E.spearman(
                    vet["proj_points"].to_numpy(dtype=float),
                    vet["points"].to_numpy(dtype=float))
            rows.append(row)
    return pd.DataFrame(rows)


def boot_diff(diffs: np.ndarray) -> Tuple[float, float, float, int, float]:
    d = np.asarray(diffs, dtype=float)
    d = d[np.isfinite(d)]
    if not len(d):
        return np.nan, np.nan, np.nan, 0, np.nan
    rng = np.random.default_rng(BOOT_SEED)
    boot = np.array([np.mean(rng.choice(d, size=len(d), replace=True))
                     for _ in range(BOOT_REPS)])
    p = 2.0 * min(float((boot <= 0).mean()), float((boot >= 0).mean()))
    return (float(d.mean()), float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)), len(d),
            min(1.0, max(p, 1.0 / BOOT_REPS)))


def curve_report(cells: pd.DataFrame, baseline_span: int = 2012) -> pd.DataFrame:
    """Every span against the committed default, paired by season. Positive =
    the longer (or shorter) span is BETTER than the incumbent 2012."""
    rows: List[Dict] = []
    for (variant, pos, span), g in cells.groupby(["variant", "position", "span"]):
        b = cells[(cells.variant == variant) & (cells.position == pos)
                  & (cells.span == baseline_span)]
        for metric in ("rho_points", "rho_points_fullvet", "rho_games"):
            if metric not in g.columns:
                continue
            j = g.set_index("season")[[metric]].join(
                b.set_index("season")[[metric]], how="inner", rsuffix="_b").dropna()
            if not len(j):
                continue
            d, lo, hi, n, p = boot_diff(
                (j[metric] - j[f"{metric}_b"]).to_numpy())
            rows.append(dict(variant=variant, position=pos, span=span,
                             metric=metric, mean=float(j[metric].mean()),
                             baseline=float(j[f"{metric}_b"].mean()),
                             delta=d, lo=lo, hi=hi, n_seasons=n, p=p))
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feasibility", action="store_true")
    ap.add_argument("--spans", default="")
    ap.add_argument("--ctx", action="store_true",
                    help="also run the context-normalised variant")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    if args.feasibility:
        f = feasibility()
        f.to_csv(FEAS, index=False)
        pd.set_option("display.width", 220)
        print(f.to_string(index=False))
        return

    if args.report:
        cells = pd.read_csv(CELLS)
        pd.set_option("display.width", 220)
        pd.set_option("display.max_rows", 400)
        print(curve_report(cells).round(4).to_string(index=False))
        return

    spans = [int(s) for s in args.spans.split(",") if s]
    variants = ["raw"] + (["ctx"] if args.ctx else [])
    print(f"HOLDOUT {HOLDOUT_SEASON}: sealed. Targets held at "
          f"{FIRST_TARGET}-{LAST_TARGET} for every span.", flush=True)
    panel = build_avail_panel()
    ctx = load_ctx()
    print(f"panel {panel.seasons[0]}-{panel.seasons[-1]}; "
          f"league_season_metrics {ctx.index.min()}-{ctx.index.max()}", flush=True)

    cells = pd.read_csv(CELLS) if CELLS.exists() else pd.DataFrame()
    for variant in variants:
        for span in spans:
            print(f"\n### span first_feature_season={span} variant={variant}",
                  flush=True)
            new = run_span(panel, ctx, span, variant)
            cells = pd.concat([cells, new], ignore_index=True).drop_duplicates(
                subset=["span", "variant", "position", "season"], keep="last")
            cells.to_csv(CELLS, index=False)
            print(new.groupby("position")[
                [c for c in ("rho_points", "rho_points_fullvet", "rho_games",
                             "mae_games") if c in new.columns]]
                  .mean().round(4).to_string(), flush=True)
    print("\n" + "=" * 100)
    print(curve_report(cells).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
