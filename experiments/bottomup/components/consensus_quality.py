"""PR-009: consensus quality, season by season -- run against BOTH baselines.

Design: docs/preregistration/PR-009-consensus-quality-by-season.md (strategist,
registered 2026-07-31, run rule fixed before any value was read).
Founder's ruling extending it: docs/founder-requests/FR-2026-07-31-both-baselines
(CLAUDE.md 6.5, amended 2026-07-31) -- "I'd measure against both": market ADP
(FFC half-PPR 12-team) AND expert consensus (FantasyPros ECR), reported side by
side, never the flattering half.

    .venv/bin/python -m experiments.bottomup.components.consensus_quality

WHAT THIS DOES NOT DO. It does not touch 2025 (sealed; excluded structurally --
neither ADP archive nor the `fantasypros_ecr` rankings table contains it). It
does not fit, tune, or refit anything -- B2/B3 are the SAME lag-1/recency
features `pos_eval`'s own committed walk-forward already computes
(`build_features`), reused unmodified so this script cannot drift from the
already-published per-season numbers. Market-ADP-pass B1/B2/B3 rho levels are
cross-checked against the already-committed
`experiments/bottomup/results/{pos}_components_metrics.csv` (verified
byte-identical for RB before this script was trusted, PR-009 run log).

THE NULL BAND (PR-009 SS4), operationalised. The PR specifies bootstrapping
`rho_ADP` within season (player resample, 4000 reps) to get "the width rho
would have if consensus quality were constant across seasons" and then asking
whether the season's gap vs B3 falls outside that band. The PR does not spell
out the exact band construction, so it is fixed HERE, before any table is
printed: normal-approximate 95% band centred on zero,
+/-1.96 * SE(rho_ADP boot), i.e. the amount a single season's own rho could
plausibly wobble by sampling alone. A season is POOR only if BOTH the
directional condition (rho_ADP < rho_B3) AND |gap| exceeds this band. Recorded
here, not adjusted after a number was seen.

THE ECR EXTENSION TO SS6 (prediction test), also fixed here before any value is
read. PR-009 SS6 registers S1/S2/S3 against the ADP label only (12 CONFIRMATORY
tests, m=12, its own BH correction). The founder's both-baselines ruling did not
re-open SS6, so running S1/S3 (S2 is ADP-specific by construction -- FFC's own
std_dev has no ECR analogue in this schema) against the ECR-POOR label is an
EXPLORATORY EXTENSION, reported separately, NOT pooled into SS6's m=12, and NOT
itself confirmatory of anything.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import adp_baseline as adp          # noqa: E402
from experiments.bottomup.components import pos_eval as E                # noqa: E402
from experiments.bottomup.components.pos_data import (                   # noqa: E402
    HOLDOUT_SEASON, build_panel, universe_for,
)
from experiments.bottomup.components.pos_features import (               # noqa: E402
    build_features, outcome_components,
)

DB_PATH = _REPO / "data" / "nfl.db"
RESULTS_DIR = _REPO / "experiments" / "bottomup" / "results"
PREREG_DIR = _REPO / "docs" / "preregistration"
RUN_LOG = PREREG_DIR / "test_run_log.jsonl"

FIRST_SEASON, LAST_SEASON = 2013, 2024   # PR-009 SS1 -- 2025 stays sealed
POSITIONS = ["QB", "RB", "WR", "TE"]

SEED = 20260731            # recorded per guardrails SS11 -- never builtin hash()
NULL_REPS = 4000            # PR-009 SS4
STRONG_MARGIN = 0.134       # PR-009 SS5 -- the RB point estimate already on file
PRED_MAGNITUDE_GATE = 0.134 # PR-009 SS6(b)
MIN_ADP_N = 10               # matches pos_eval's own adpsub_* gate


# --------------------------------------------------------------- market ADP
def market_pass_players(panel, position: str) -> pd.DataFrame:
    """One row per (season 2013-2024, player) in that position's frozen
    universe, with average_pick / std_dev (market crowd) and pts_1/ppg_w/gshare_w
    (B2/B3 features) and realised points -- same construction pos_eval.WalkForward
    uses, minus the model fit itself (B1/B2/B3 never touch the fitted model)."""
    rows = []
    for target in range(FIRST_SEASON, LAST_SEASON + 1):
        try:
            board = adp.load_adp(target, position=position)
        except ValueError as e:
            print(f"  [market {position} {target}] ADP gate: {e}")
            continue
        extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                 if len(board) else None)
        try:
            u = universe_for(panel, target, position, extra_ids=extra)
        except Exception as e:  # holdout / cutoff guard, or too little history
            print(f"  [market {position} {target}] universe: {e}")
            continue
        f = build_features(panel, u, target)
        o = outcome_components(panel, u, target)
        d = f.merge(o[["player_id", "points"]], on="player_id", how="left")
        if len(board):
            b = board.loc[~board["unmatched"], ["player_id", "average_pick", "std_dev"]]
            d = d.merge(b.drop_duplicates("player_id"), on="player_id", how="left")
        else:
            d["average_pick"] = np.nan
            d["std_dev"] = np.nan
        d["season"] = target
        rows.append(d)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


# ------------------------------------------------------------------- ECR
_ECR_SQL = """
SELECT season, player_id, position, adp_rank AS ecr_rank, adp_value AS ecr_value,
       spread_sd AS ecr_spread_sd, as_of_date
FROM rankings
WHERE source = 'fantasypros_ecr' AND season = ? AND position = ?
"""


def load_ecr(season: int, position: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    """Pre-season FantasyPros ECR for (season, position). Structurally cannot
    reach the sealed holdout: the table's own MAX(season)=2026 draft-cycle row
    aside, per-position PRESEASON snapshots only exist 2021-2025, and this
    caller is never given 2025 by `main()`'s season range check.

    KNOWN PROXY, not this league's own crowd: `src/ingest_rankings.py` states
    plainly that this source (DynastyProcess mirror, redraft-overall) has NO
    half-PPR variant -- `scoring_format` is NULL on every row. It is the
    EXPERT-OPINION baseline CLAUDE.md 6.5 names, but it is a standard/non-PPR
    scoring proxy for it, same caveat class as the ADP pass's 12-team-for-10-team
    substitution. Labelled at every use below, never silently treated as exact.
    """
    if season >= HOLDOUT_SEASON:
        raise ValueError(f"season {season} is sealed, refusing to load ECR")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(_ECR_SQL, conn, params=(season, position))
    finally:
        conn.close()
    return df


def ecr_pass_players(panel, position: str) -> pd.DataFrame:
    rows = []
    for target in range(FIRST_SEASON, LAST_SEASON + 1):
        ecr = load_ecr(target, position)
        extra = ecr["player_id"].dropna().unique().tolist() if len(ecr) else None
        try:
            u = universe_for(panel, target, position, extra_ids=extra)
        except Exception as e:
            print(f"  [ecr {position} {target}] universe: {e}")
            continue
        f = build_features(panel, u, target)
        o = outcome_components(panel, u, target)
        d = f.merge(o[["player_id", "points"]], on="player_id", how="left")
        if len(ecr):
            e2 = ecr[["player_id", "ecr_rank", "ecr_value", "ecr_spread_sd"]].drop_duplicates("player_id")
            d = d.merge(e2, on="player_id", how="left")
        else:
            d["ecr_rank"] = np.nan
            d["ecr_value"] = np.nan
            d["ecr_spread_sd"] = np.nan
        d["season"] = target
        rows.append(d)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


# ------------------------------------------------------------- season metrics
def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    return E.spearman(a, b)


def season_cell(d: pd.DataFrame, predictor_col: str, min_n: int = MIN_ADP_N) -> Dict:
    """One (season, position) row: rho of the crowd (higher predictor = better,
    so pass NEGATIVE rank / NEGATIVE average_pick in) vs B2/B3, plus B4 context.
    Busts retained at 0 (already true of `points`, filled upstream); no
    games-played filter (none applied here)."""
    ok = d[predictor_col].notna()
    n = int(ok.sum())
    out = {"n_universe": len(d), "n_covered": n}
    if n < min_n:
        out.update(rho_crowd=np.nan, rho_b2=np.nan, rho_b3=np.nan,
                    top12_pts=np.nan, rank13_24_pts=np.nan)
        return out
    sub = d[ok]
    act = sub["points"].to_numpy(float)
    pred = -sub[predictor_col].to_numpy(float)   # lower rank/pick = better
    out["rho_crowd"] = _spearman(pred, act)
    b2 = sub["pts_1"].fillna(0.0).to_numpy(float)
    b3 = (sub["ppg_w"].fillna(0.0) * sub["gshare_w"].fillna(0.0)).to_numpy(float)
    out["rho_b2"] = _spearman(b2, act) if n >= 5 else np.nan
    out["rho_b3"] = _spearman(b3, act) if n >= 5 else np.nan
    # B4: is there anything to predict at all in this season's covered subset?
    order = sub[predictor_col].to_numpy(float).argsort()  # ascending pick/rank = better
    ranked_pts = act[order]
    out["top12_pts"] = float(np.mean(ranked_pts[:12])) if n >= 12 else np.nan
    out["rank13_24_pts"] = (float(np.mean(ranked_pts[12:24]))
                             if n >= 24 else (float(np.mean(ranked_pts[12:n])) if n > 12 else np.nan))
    return out


def null_band(d: pd.DataFrame, predictor_col: str, seed: int,
               reps: int = NULL_REPS) -> Tuple[float, float]:
    """Bootstrap SE of THIS season's own rho_crowd by resampling players with
    replacement (player-level, by design -- PR-009 SS4/SS8). Returns
    (se, half_width_95) where half_width_95 = 1.96 * se: the amount a single
    season's rho could plausibly wobble by sampling alone if quality were
    constant across seasons."""
    ok = d[predictor_col].notna()
    sub = d[ok]
    n = len(sub)
    if n < MIN_ADP_N:
        return np.nan, np.nan
    act = sub["points"].to_numpy(float)
    pred = -sub[predictor_col].to_numpy(float)
    rng = np.random.default_rng(seed)
    boots = np.empty(reps)
    idx = np.arange(n)
    for i in range(reps):
        s = rng.choice(idx, size=n, replace=True)
        boots[i] = _spearman(pred[s], act[s])
    boots = boots[np.isfinite(boots)]
    if len(boots) < reps // 2:
        return np.nan, np.nan
    se = float(np.std(boots, ddof=1))
    return se, 1.96 * se


def build_table(players: pd.DataFrame, predictor_col: str, seed_base: int) -> pd.DataFrame:
    rows = []
    for season, g in players.groupby("season"):
        cell = season_cell(g, predictor_col)
        se, half_width = null_band(g, predictor_col, seed=seed_base + season)
        cell["season"] = season
        cell["null_se"] = se
        cell["null_half_width_95"] = half_width
        rows.append(cell)
    t = pd.DataFrame(rows).sort_values("season").reset_index(drop=True)
    t["gap_vs_b3"] = t["rho_crowd"] - t["rho_b3"]
    t["outside_null_band"] = t["gap_vs_b3"].abs() > t["null_half_width_95"]
    t["poor"] = (t["rho_crowd"] < t["rho_b3"]) & t["outside_null_band"].fillna(False)
    t["strong"] = t["gap_vs_b3"] >= STRONG_MARGIN
    return t


# ------------------------------------------------------- prediction test (SS6)
def rookie_share_top36(d: pd.DataFrame, predictor_col: str) -> float:
    ok = d[predictor_col].notna()
    sub = d[ok].sort_values(predictor_col, ascending=True).head(36)
    if len(sub) < 5:
        return np.nan
    return float((sub["entry"] == "rookie").mean())


def dispersion_top36(d: pd.DataFrame, disp_col: str, predictor_col: str) -> float:
    ok = d[predictor_col].notna() & d[disp_col].notna()
    sub = d[ok].sort_values(predictor_col, ascending=True).head(36)
    if len(sub) < 5:
        return np.nan
    return float(sub[disp_col].mean())


def auc_and_ci(score: np.ndarray, label: np.ndarray, seed: int,
                reps: int = NULL_REPS) -> Tuple[float, float, float, int]:
    """Mann-Whitney AUC (score ranks POOR above not-POOR) + season-level
    bootstrap CI. NaN-safe; returns (auc, lo, hi, n) with auc=nan if either
    class is empty or all scores tie."""
    ok = np.isfinite(score) & np.isfinite(label)
    s, y = score[ok], label[ok].astype(bool)
    n = len(s)
    if n < 4 or y.sum() == 0 or y.sum() == n:
        return np.nan, np.nan, np.nan, n

    def _auc(s_, y_):
        pos, neg = s_[y_], s_[~y_]
        if len(pos) == 0 or len(neg) == 0:
            return np.nan
        # rank-based Mann-Whitney U -> AUC
        allv = np.concatenate([pos, neg])
        ranks = pd.Series(allv).rank().to_numpy()
        r_pos = ranks[:len(pos)].sum()
        u = r_pos - len(pos) * (len(pos) + 1) / 2
        return u / (len(pos) * len(neg))

    point = _auc(s, y)
    rng = np.random.default_rng(seed)
    boots = []
    idx = np.arange(n)
    for _ in range(reps):
        b = rng.choice(idx, size=n, replace=True)
        v = _auc(s[b], y[b])
        if np.isfinite(v):
            boots.append(v)
    if len(boots) < reps // 4:
        return point, np.nan, np.nan, n
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return point, float(lo), float(hi), n


def prediction_test(table: pd.DataFrame, players: pd.DataFrame, position: str,
                     predictor_col: str, disp_col: Optional[str], seed_base: int,
                     label: str) -> List[Dict]:
    """SS6: does S1 (rookie share top36) / S2 (dispersion top36, ADP only) /
    S3 (prior season's own gap) predict this season's POOR label?

    Simplification stated openly: each signal is a raw pre-existing value with
    no parameters fit to prior seasons (S1/S2 are this season's own pre-Week-1
    numbers; S3 is last season's already-realised gap) -- there is nothing to
    "train" that could leak future information, so "walk-forward AUC" reduces
    to computing AUC directly over the labelled seasons, each of whose signal
    value only ever used information dated before that season's own Week 1.
    """
    labelled = table.dropna(subset=["poor"])
    out = []
    seasons_by_g = {s: g for s, g in players.groupby("season")}

    s1 = np.array([rookie_share_top36(seasons_by_g[s], predictor_col)
                    if s in seasons_by_g else np.nan for s in labelled["season"]])
    sigs = {"S1_rookie_share_top36": s1}
    if disp_col is not None:
        s2 = np.array([dispersion_top36(seasons_by_g[s], disp_col, predictor_col)
                        if s in seasons_by_g else np.nan for s in labelled["season"]])
        sigs["S2_dispersion_top36"] = s2
    gap_by_season = dict(zip(table["season"], table["gap_vs_b3"]))
    s3 = np.array([gap_by_season.get(s - 1, np.nan) for s in labelled["season"]])
    sigs["S3_prior_season_gap"] = s3

    y = labelled["poor"].to_numpy(dtype=float)
    for i, (name, sig) in enumerate(sigs.items()):
        auc_, lo, hi, n = auc_and_ci(sig, y, seed=seed_base + i)
        poor_mean = np.nanmean(sig[y.astype(bool)]) if y.sum() else np.nan
        notpoor_mean = np.nanmean(sig[~y.astype(bool)]) if (~y.astype(bool)).sum() else np.nan
        gap_mag = (poor_mean - notpoor_mean) if np.isfinite(poor_mean) and np.isfinite(notpoor_mean) else np.nan
        out.append(dict(baseline=label, position=position, signal=name, auc=auc_,
                         auc_lo=lo, auc_hi=hi, n=n,
                         mean_signal_predicted_poor=poor_mean,
                         mean_signal_predicted_notpoor=notpoor_mean,
                         magnitude_gap=gap_mag))
    return out


# ------------------------------------------------------------------ driver
def run_log_append(entries: List[Dict]) -> None:
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    with open(RUN_LOG, "a") as fh:
        for e in entries:
            row = {"timestamp_utc": ts, **e}
            fh.write(json.dumps(row) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RESULTS_DIR / "pr009_consensus_quality.csv"))
    args = ap.parse_args()

    print(f"seed={SEED}  reps={NULL_REPS}  seasons={FIRST_SEASON}-{LAST_SEASON}  "
          f"(2025 sealed, excluded by range and by source coverage)")
    panel = build_panel()

    all_tables = {}
    all_players = {}
    for baseline, predictor_col, disp_col, pass_fn in [
            ("market_adp", "average_pick", "std_dev", market_pass_players),
            ("expert_ecr", "ecr_rank", None, ecr_pass_players)]:
        for pos in POSITIONS:
            print(f"\n=== {baseline} {pos} ===")
            players = pass_fn(panel, pos)
            if not len(players):
                print("  no data at all")
                continue
            table = build_table(players, predictor_col, seed_base=SEED)
            table["baseline"] = baseline
            table["position"] = pos
            all_tables[(baseline, pos)] = table
            all_players[(baseline, pos)] = players
            cols = ["season", "n_universe", "n_covered", "rho_crowd", "rho_b2",
                    "rho_b3", "gap_vs_b3", "null_half_width_95", "poor", "strong",
                    "top12_pts", "rank13_24_pts"]
            print(table[cols].round(4).to_string(index=False))

    combined = pd.concat(all_tables.values(), ignore_index=True) if all_tables else pd.DataFrame()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")

    # ---------------------------------------------------------------- SS6
    print("\n\n" + "=" * 78)
    print("SS6 PREDICTION TEST -- confirmatory for market_adp (12 tests, m=12); "
          "EXPLORATORY EXTENSION for expert_ecr (not pooled into m=12)")
    print("=" * 78)
    pred_rows = []
    for baseline, predictor_col, disp_col in [
            ("market_adp", "average_pick", "std_dev"),
            ("expert_ecr", "ecr_rank", None)]:
        for pos in POSITIONS:
            key = (baseline, pos)
            if key not in all_tables:
                continue
            rows = prediction_test(all_tables[key], all_players[key], pos,
                                    predictor_col, disp_col,
                                    seed_base=SEED + 1000, label=baseline)
            pred_rows.extend(rows)
    pred_df = pd.DataFrame(pred_rows)
    if len(pred_df):
        print(pred_df.round(4).to_string(index=False))
    pred_out = str(RESULTS_DIR / "pr009_prediction_test.csv")
    pred_df.to_csv(pred_out, index=False)
    print(f"\nwrote {pred_out}")

    # ---------------------------------------------------------------- run log
    log_entries = []
    for (baseline, pos), t in all_tables.items():
        for _, r in t.dropna(subset=["gap_vs_b3"]).iterrows():
            log_entries.append({
                "test_id": f"PR-009:{baseline}:{pos}:{int(r['season'])}",
                "metric": "rho_crowd_minus_rho_b3",
                "effect_size": float(r["gap_vs_b3"]),
                "p_value": None,
                "seasons_used": [int(r["season"])],
                "notes": f"n_covered={int(r['n_covered'])} poor={bool(r['poor'])} "
                         f"strong={bool(r['strong'])} seed={SEED} reps={NULL_REPS}",
            })
    confirmatory_m12 = pred_df[pred_df.baseline == "market_adp"] if len(pred_df) else pred_df
    for _, r in confirmatory_m12.iterrows():
        log_entries.append({
            "test_id": f"PR-009:SS6:{r['baseline']}:{r['position']}:{r['signal']}",
            "metric": "walkforward_auc_poor_prediction",
            "effect_size": float(r["auc"]) if np.isfinite(r["auc"]) else None,
            "p_value": None,
            "seasons_used": None,
            "notes": f"ci=[{r['auc_lo']},{r['auc_hi']}] n={r['n']} "
                     f"magnitude_gap={r['magnitude_gap']} seed={SEED+1000} reps={NULL_REPS}",
        })
    run_log_append(log_entries)
    print(f"\nappended {len(log_entries)} rows to {RUN_LOG}")


if __name__ == "__main__":
    main()
