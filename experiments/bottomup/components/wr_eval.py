"""Walk-forward evaluation of the WR component model.

Protocol, fixed before any number was looked at:

  for each target season N:
      universe   <- pre-N information only
      features   <- seasons <= N-1
      training   <- (features, outcomes) pairs whose OUTCOME season is <= N-1
      fit        <- on training only
      predict    <- season N
      score      <- against realised season N

No season is ever in its own training set. 2025 is sealed and never opened.

Baselines (CLAUDE.md 6.5), all three required:
  B1  consensus ADP           -- FFC half-PPR 12-team, pre-kickoff dated
  B2  prior-season points     -- season N-1 total, ranked
  B3  positional heuristic    -- recency-weighted prior points per game

The headline is the COMPARISON, never the raw correlation.

Uncertainty is a season-block bootstrap: seasons are the independent unit here,
not players -- the same ~200 players recur every year and treating them as
independent would shrink every interval by roughly the square root of that
autocorrelation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from . import adp_baseline as adp
from .wr_data import SeasonPanel, universe_for
from .wr_features import build_features, outcome_components
from .wr_model import WRComponentModel


# ------------------------------------------------------------------ metrics
def _rank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(np.argsort(-np.asarray(x, dtype=float)))
    return order.astype(float)


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    a = pd.Series(a).rank().to_numpy()
    b = pd.Series(b).rank().to_numpy()
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def kendall_tau_b(a: np.ndarray, b: np.ndarray) -> float:
    from itertools import combinations
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = len(a)
    if n < 3:
        return np.nan
    # O(n^2) is fine at n ~ 200
    da = np.sign(a[:, None] - a[None, :])
    db = np.sign(b[:, None] - b[None, :])
    iu = np.triu_indices(n, 1)
    sa, sb = da[iu], db[iu]
    conc = float(np.sum(sa * sb))
    n0 = len(sa)
    n1 = float(np.sum(sa == 0))
    n2 = float(np.sum(sb == 0))
    denom = np.sqrt((n0 - n1) * (n0 - n2))
    return conc / denom if denom > 0 else np.nan


def top_k_capture(pred: np.ndarray, actual: np.ndarray, k: int) -> float:
    """Share of the true top-k actually captured by the predicted top-k."""
    if len(pred) < k:
        return np.nan
    pi = set(np.argsort(-np.asarray(pred, dtype=float))[:k])
    ai = set(np.argsort(-np.asarray(actual, dtype=float))[:k])
    return len(pi & ai) / k


def mean_actual_of_top_k(pred: np.ndarray, actual: np.ndarray, k: int) -> float:
    if len(pred) < k:
        return np.nan
    pi = np.argsort(-np.asarray(pred, dtype=float))[:k]
    return float(np.mean(np.asarray(actual, dtype=float)[pi]))


# --------------------------------------------------------------- the runner
FIRST_FEATURE_SEASON = 2012   # 2009 usage data + three lag seasons


@dataclass
class WalkForward:
    panel: SeasonPanel
    first_target: int = 2014
    last_target: int = 2024
    min_train_seasons: int = 2
    use_adp_universe: bool = True
    calibrate_bonus: bool = True
    model_kwargs: Optional[Dict] = None
    audit: List[Dict] = None

    def _training_pairs(self, target: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        fs, os_ = [], []
        for s in range(FIRST_FEATURE_SEASON, target):
            u = universe_for(self.panel, s)
            fs.append(build_features(self.panel, u, s))
            os_.append(outcome_components(self.panel, u, s))
        return pd.concat(fs, ignore_index=True), pd.concat(os_, ignore_index=True)

    def _oos_training_projections(self, tf: pd.DataFrame, to: pd.DataFrame
                                  ) -> Optional[pd.DataFrame]:
        """Expanding-window projections INSIDE the training window.

        For each training season s, fit on training seasons strictly before s
        and project s. Nothing in these projections has seen its own season.
        Used only to calibrate the bonus curve.
        """
        seasons = sorted(to["season"].unique())
        out = []
        for s in seasons[1:]:
            sub_f = tf[tf["season"] < s]
            sub_o = to[to["season"] < s]
            if sub_o["season"].nunique() < 1:
                continue
            m = WRComponentModel(**(self.model_kwargs or {}))
            m.fit(sub_f, sub_o)
            out.append(m.predict(tf[tf["season"] == s]))
        return pd.concat(out, ignore_index=True) if out else None

    def run(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Returns (per-player projections+actuals, per-season metric rows)."""
        rows, metrics = [], []
        self.audit = []
        for target in range(self.first_target, self.last_target + 1):
            self.panel.reset_audit()
            tf, to = self._training_pairs(target)
            n_train_seasons = to["season"].nunique()
            if n_train_seasons < self.min_train_seasons:
                continue

            board = adp.load_adp(target) if self.use_adp_universe else pd.DataFrame()
            extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                     if len(board) else None)
            u = universe_for(self.panel, target, extra_ids=extra)
            f = build_features(self.panel, u, target)

            model = WRComponentModel(**(self.model_kwargs or {}))
            model.fit(tf, to)
            if self.calibrate_bonus:
                oos = self._oos_training_projections(tf, to)
                if oos is not None and len(oos) > 200:
                    model.refit_bonus_on_projections(oos, tf, to)

            # AUDIT: everything above must have stayed strictly before `target`.
            a = self.panel.audit(target)
            a.update(season=target, phase="pre_outcome")
            self.audit.append(a)
            if a["max_feature_cutoff"] >= target or a["max_outcome_season"] >= target:
                raise RuntimeError(
                    f"look-ahead: target {target} saw {a}")

            proj = model.predict(f)
            o = outcome_components(self.panel, u, target)   # evaluation only

            d = proj.merge(o, on=["player_id", "season"], suffixes=("", "_act"))
            d = d.merge(f[["player_id", "pts_1", "ppg_w", "gshare_w", "age",
                           "evidence", "tpg_w", "rec_1", "recyds_1", "rectd_1",
                           "tgt_1", "games_1"]], on="player_id", how="left")
            if len(board):
                b = board.loc[~board["unmatched"], ["player_id", "average_pick"]]
                d = d.merge(b, on="player_id", how="left")
            else:
                d["average_pick"] = np.nan
            d["n_train_seasons"] = n_train_seasons
            rows.append(d)
            metrics.append(_season_metrics(d, target))
        return pd.concat(rows, ignore_index=True), pd.DataFrame(metrics)


# B2 / B3 in the same shape as the model's output: higher = better.
def _baseline_columns(d: pd.DataFrame) -> Dict[str, np.ndarray]:
    return {
        "model": d["proj_points"].to_numpy(dtype=float),
        "model_no_bonus": d["proj_points_base"].to_numpy(dtype=float),
        "b2_prior_points": d["pts_1"].fillna(0.0).to_numpy(dtype=float),
        "b3_wavg_ppg": (d["ppg_w"].fillna(0.0) * d["gshare_w"].fillna(0.0)
                        ).to_numpy(dtype=float),
        "b1_adp": -d["average_pick"].to_numpy(dtype=float),
    }


def _season_metrics(d: pd.DataFrame, season: int) -> Dict:
    act = d["points"].to_numpy(dtype=float)
    out = {"season": season, "n": len(d)}
    cols = _baseline_columns(d)
    has_adp = np.isfinite(cols["b1_adp"])
    out["n_adp"] = int(has_adp.sum())
    for name, pred in cols.items():
        ok = np.isfinite(pred)
        if ok.sum() < 5:
            out[f"rho_{name}"] = np.nan
            continue
        out[f"rho_{name}"] = spearman(pred[ok], act[ok])
        out[f"top24_{name}"] = top_k_capture(pred[ok], act[ok], 24)
        out[f"pts_top24_{name}"] = mean_actual_of_top_k(pred[ok], act[ok], 24)
    # head-to-head on the ADP-covered subset only (apples to apples)
    if has_adp.sum() >= 20:
        a = act[has_adp]
        for name, pred in cols.items():
            p = pred[has_adp]
            if not np.isfinite(p).all():
                continue
            out[f"adpsub_rho_{name}"] = spearman(p, a)
            out[f"adpsub_top24_{name}"] = top_k_capture(p, a, 24)
            out[f"adpsub_pts_top24_{name}"] = mean_actual_of_top_k(p, a, 24)
    # component accuracy (the FR-054 deliverable), against naive persistence:
    # last season's own component total, which is the honest zero-work baseline
    # for a component projection.
    naive = {"receptions": "rec_1", "rec_yards": "recyds_1", "rec_tds": "rectd_1",
             "targets": "tgt_1", "games": "games_1"}
    for comp, actual_col in [("proj_receptions", "receptions"),
                             ("proj_rec_yards", "rec_yards"),
                             ("proj_rec_tds", "rec_tds"),
                             ("proj_games", "games"),
                             ("proj_targets", "targets")]:
        e = d[comp].to_numpy(dtype=float) - d[actual_col].to_numpy(dtype=float)
        out[f"mae_{actual_col}"] = float(np.mean(np.abs(e)))
        out[f"bias_{actual_col}"] = float(np.mean(e))
        nc = naive.get(actual_col)
        if nc and nc in d.columns:
            en = d[nc].fillna(0.0).to_numpy(dtype=float) - d[actual_col].to_numpy(dtype=float)
            out[f"mae_naive_{actual_col}"] = float(np.mean(np.abs(en)))
    # bonus calibration -- predicted vs realised stacking-bonus points
    out["bonus_pred_total"] = float(d["proj_bonus_points"].sum())
    out["bonus_actual_total"] = float(d["rec_bonus"].sum())
    return out


# ------------------------------------------------------------- uncertainty
def season_block_bootstrap(metrics: pd.DataFrame, col_a: str, col_b: str,
                           reps: int = 4000, seed: int = 20260729
                           ) -> Tuple[float, float, float, int]:
    """Paired difference col_a - col_b, resampling SEASONS with replacement."""
    sub = metrics[[col_a, col_b]].dropna()
    diffs = (sub[col_a] - sub[col_b]).to_numpy(dtype=float)
    n = len(diffs)
    if n == 0:
        return np.nan, np.nan, np.nan, 0
    rng = np.random.default_rng(seed)
    boot = np.array([np.mean(rng.choice(diffs, size=n, replace=True))
                     for _ in range(reps)])
    return float(diffs.mean()), float(np.percentile(boot, 2.5)), \
        float(np.percentile(boot, 97.5)), n
