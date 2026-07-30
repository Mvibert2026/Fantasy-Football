"""Walk-forward evaluation for the multi-position component model.

Protocol, fixed in `component-model-multipos-precommit.md` before any number was
looked at:

  for each target season N:
      universe   <- pre-N information only
      features   <- seasons <= N-1
      training   <- (features, outcomes) pairs whose OUTCOME season is <= N-1
      fit        <- on training only
      predict    <- season N
      score      <- against realised season N

No season is ever in its own training set. 2025 is sealed and never opened.

Baselines (CLAUDE.md §6.5), all three required, per position:
  B1  consensus ADP        -- FFC half-PPR 12-team, pre-kickoff dated
  B2  prior-season points  -- season N-1 total, ranked
  B3  positional heuristic -- recency-weighted prior points per game

THE HEADLINE IS THE COMPARISON, NEVER THE RAW CORRELATION.

Uncertainty is a season-block bootstrap: seasons are the independent unit, not
players -- the same players recur every year and treating them as independent
would shrink every interval by roughly the square root of that autocorrelation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from . import adp_baseline as adp
from .pos_data import SeasonPanel, universe_for
from .pos_features import build_features, outcome_components
from .pos_model import MODELS, RBComponentModel, ReceiverComponentModel

FIRST_FEATURE_SEASON = 2012      # 2009 usage data + three lag seasons
DEEP_FIRST_FEATURE_SEASON = 2002  # QB only: passing volume is complete from 1999


# ------------------------------------------------------------------ metrics
def spearman(a: np.ndarray, b: np.ndarray) -> float:
    a = pd.Series(a).rank().to_numpy()
    b = pd.Series(b).rank().to_numpy()
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def top_k_capture(pred: np.ndarray, actual: np.ndarray, k: int) -> float:
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


def season_block_bootstrap(metrics: pd.DataFrame, col_a: str, col_b: str,
                           reps: int = 4000, seed: int = 20260730
                           ) -> Tuple[float, float, float, int]:
    """Paired difference col_a - col_b, resampling SEASONS with replacement."""
    if col_a not in metrics.columns or col_b not in metrics.columns:
        return np.nan, np.nan, np.nan, 0
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


def fmt(label: str, d: float, lo: float, hi: float, n: int, width: int = 40) -> str:
    if not np.isfinite(d):
        return f"  {label:<{width}} (no data)"
    verdict = "CLEARS 0" if (lo > 0 or hi < 0) else "does NOT clear 0"
    return f"  {label:<{width}} {d:+.4f} [{lo:+.4f}, {hi:+.4f}]  n={n}  {verdict}"


# ---- per-position component ledger for the naive-persistence comparison ----
# (projection column, realised column, lag-1 feature column that is the honest
#  zero-work baseline for that component)
COMPONENT_LEDGER: Dict[str, List[Tuple[str, str, str]]] = {
    "WR": [("proj_games", "games", "games_1"), ("proj_targets", "targets", "tgt_1"),
           ("proj_receptions", "receptions", "rec_1"),
           ("proj_rec_yards", "rec_yards", "recyds_1"),
           ("proj_rec_tds", "rec_tds", "rectd_1")],
    "TE": [("proj_games", "games", "games_1"), ("proj_targets", "targets", "tgt_1"),
           ("proj_receptions", "receptions", "rec_1"),
           ("proj_rec_yards", "rec_yards", "recyds_1"),
           ("proj_rec_tds", "rec_tds", "rectd_1")],
    "RB": [("proj_games", "games", "games_1"), ("proj_carries", "carries", "carries_1"),
           ("proj_rush_yards", "rush_yards", "rushyds_1"),
           ("proj_rush_tds", "rush_tds", "rushtd_1"),
           ("proj_targets", "targets", "tgt_1"),
           ("proj_receptions", "receptions", "rec_1"),
           ("proj_rec_yards", "rec_yards", "recyds_1")],
    "QB": [("proj_games", "games", "games_1"), ("proj_attempts", "attempts", "att_1"),
           ("proj_pass_yards", "pass_yards", "passyds_1"),
           ("proj_pass_tds", "pass_tds", "passtd_1"),
           ("proj_interceptions", "interceptions", "ints_1"),
           ("proj_carries", "carries", "carries_1"),
           ("proj_rush_yards", "rush_yards", "rushyds_1")],
}

# feature columns carried through to the output frame for diagnostics
_CARRY = ["pts_1", "ppg_w", "gshare_w", "gshare_1", "age", "evidence", "present_1",
          "gshare_max3", "inj_missed_share_1", "unexp_missed_share_1",
          "rostered_absent_share_1", "offroster_share_1", "depth_first_share_1",
          "inj_out_wks_1", "missed_wks_1", "games_1", "tgt_1", "rec_1", "recyds_1",
          "rectd_1", "carries_1", "rushyds_1", "rushtd_1", "att_1", "passyds_1",
          "passtd_1", "ints_1"]


@dataclass
class WalkForward:
    panel: SeasonPanel
    position: str
    first_target: int = 2014
    last_target: int = 2024
    min_train_seasons: int = 2
    avail_arm: str = "A"
    calibrate_bonus: bool = True
    model_kwargs: Dict = field(default_factory=dict)
    first_feature_season: int = FIRST_FEATURE_SEASON
    pool_position: Optional[str] = None       # TE secondary: borrow WR rate rows
    audit: List[Dict] = field(default_factory=list)
    _cache: Dict = field(default_factory=dict, repr=False)

    def _make_model(self):
        cls = MODELS[self.position]
        return cls(position=self.position, avail_arm=self.avail_arm,
                   **self.model_kwargs)

    def _season_pair(self, position: str, s: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """One training season's (features, outcomes), memoised.

        The cache REPLAYS the panel access-log entries it would have generated,
        so the look-ahead audit sees exactly the same reads as an uncached run.
        A cache that silently suppressed audit entries would weaken the one check
        that makes this whole harness trustworthy.
        """
        key = (position, s)
        hit = self._cache.get(key)
        if hit is None:
            u = universe_for(self.panel, s, position)
            hit = (build_features(self.panel, u, s),
                   outcome_components(self.panel, u, s))
            self._cache[key] = hit
        else:
            self.panel.access_log.extend(
                [("feature", s - 1)] * 4 + [("outcome", s)])
        return hit

    def _pairs(self, position: str, upto: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        fs, os_ = [], []
        for s in range(self.first_feature_season, upto):
            a, b = self._season_pair(position, s)
            fs.append(a)
            os_.append(b)
        return pd.concat(fs, ignore_index=True), pd.concat(os_, ignore_index=True)

    def _oos_training_projections(self, tf, to, pool) -> Optional[pd.DataFrame]:
        """Expanding-window projections INSIDE the training window: for each
        training season s, fit on seasons strictly before s and project s.
        Nothing in these projections has seen its own season. Used only to
        calibrate the bonus curves."""
        out = []
        for s in sorted(to["season"].unique())[1:]:
            sub_f, sub_o = tf[tf["season"] < s], to[to["season"] < s]
            if sub_o["season"].nunique() < 1:
                continue
            m = self._make_model()
            pl = None
            if pool is not None:
                pf, po = pool
                pl = (pf[pf["season"] < s], po[po["season"] < s])
            m.fit(sub_f, sub_o, rate_pool=pl)
            out.append(m.predict(tf[tf["season"] == s]))
        return pd.concat(out, ignore_index=True) if out else None

    def run(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        rows, metrics = [], []
        self.audit = []
        for target in range(self.first_target, self.last_target + 1):
            self.panel.reset_audit()
            tf, to = self._pairs(self.position, target)
            n_train = to["season"].nunique()
            if n_train < self.min_train_seasons:
                continue
            pool = self._pairs(self.pool_position, target) if self.pool_position else None

            board = adp.load_adp(target, position=self.position)
            extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                     if len(board) else None)
            u = universe_for(self.panel, target, self.position, extra_ids=extra)
            f = build_features(self.panel, u, target)

            model = self._make_model()
            model.fit(tf, to, rate_pool=pool)
            if self.calibrate_bonus:
                oos = self._oos_training_projections(tf, to, pool)
                if oos is not None and len(oos) > 150:
                    model.refit_bonus_on_projections(oos, to)

            # AUDIT: everything above must have stayed strictly before `target`.
            a = self.panel.audit(target)
            a.update(season=target, phase="pre_outcome")
            self.audit.append(a)
            if a["max_feature_cutoff"] >= target or a["max_outcome_season"] >= target:
                raise RuntimeError(f"look-ahead: target {target} saw {a}")

            proj = model.predict(f)
            o = outcome_components(self.panel, u, target)   # evaluation only

            d = proj.merge(o, on=["player_id", "season"], suffixes=("", "_act"))
            carry = [c for c in _CARRY if c in f.columns]
            d = d.merge(f[["player_id"] + carry], on="player_id", how="left")
            if len(board):
                b = board.loc[~board["unmatched"], ["player_id", "average_pick"]]
                d = d.merge(b.drop_duplicates("player_id"), on="player_id", how="left")
            else:
                d["average_pick"] = np.nan
            d["n_train_seasons"] = n_train
            rows.append(d)
            metrics.append(_season_metrics(d, target, self.position))
        if not rows:
            return pd.DataFrame(), pd.DataFrame()
        return pd.concat(rows, ignore_index=True), pd.DataFrame(metrics)


def _baseline_columns(d: pd.DataFrame) -> Dict[str, np.ndarray]:
    """All four rankers in the same orientation: higher = better."""
    return {
        "model": d["proj_points"].to_numpy(dtype=float),
        "model_no_bonus": d["proj_points_base"].to_numpy(dtype=float),
        "b2_prior_points": d["pts_1"].fillna(0.0).to_numpy(dtype=float),
        "b3_wavg_ppg": (d["ppg_w"].fillna(0.0) * d["gshare_w"].fillna(0.0)
                        ).to_numpy(dtype=float),
        "b1_adp": -d["average_pick"].to_numpy(dtype=float),
    }


def _season_metrics(d: pd.DataFrame, season: int, position: str) -> Dict:
    act = d["points"].to_numpy(dtype=float)
    out = {"season": season, "n": len(d), "position": position}
    cols = _baseline_columns(d)
    has_adp = np.isfinite(cols["b1_adp"])
    out["n_adp"] = int(has_adp.sum())
    # top-k sized to what this league actually starts at the position, so the
    # decision-relevant metric is not a generic 24 at every position.
    k = {"QB": 10, "TE": 10, "RB": 20, "WR": 30}.get(position, 24)
    out["k"] = k
    for name, pred in cols.items():
        ok = np.isfinite(pred)
        if ok.sum() < 5:
            out[f"rho_{name}"] = np.nan
            continue
        out[f"rho_{name}"] = spearman(pred[ok], act[ok])
        out[f"top_{name}"] = top_k_capture(pred[ok], act[ok], k)
        out[f"pts_top_{name}"] = mean_actual_of_top_k(pred[ok], act[ok], k)
    # head-to-head on the ADP-covered subset only (apples to apples)
    if has_adp.sum() >= 10:
        a = act[has_adp]
        for name, pred in cols.items():
            p = pred[has_adp]
            if not np.isfinite(p).all():
                continue
            out[f"adpsub_rho_{name}"] = spearman(p, a)
            out[f"adpsub_top_{name}"] = top_k_capture(p, a, k)
            out[f"adpsub_pts_top_{name}"] = mean_actual_of_top_k(p, a, k)
    # component accuracy against naive persistence -- last season's own total,
    # the honest zero-work baseline for a component projection
    for pcol, acol, ncol in COMPONENT_LEDGER[position]:
        if pcol not in d.columns:
            continue
        e = d[pcol].to_numpy(dtype=float) - d[acol].to_numpy(dtype=float)
        out[f"mae_{acol}"] = float(np.mean(np.abs(e)))
        out[f"bias_{acol}"] = float(np.mean(e))
        if ncol in d.columns:
            en = d[ncol].fillna(0.0).to_numpy(dtype=float) - d[acol].to_numpy(dtype=float)
            out[f"mae_naive_{acol}"] = float(np.mean(np.abs(en)))
    # bonus calibration, per family
    for fam, actual_col in [("rec", "rec_bonus"), ("rush", "rush_bonus"),
                            ("pass", "pass_bonus")]:
        if actual_col in d.columns:
            out[f"bonus_actual_{fam}"] = float(d[actual_col].sum())
    out["bonus_pred_total"] = float(d["proj_bonus_points"].sum())
    out["bonus_actual_total"] = float(d["total_bonus"].sum())
    return out


# ------------------------------------------------- availability diagnostics
def returning_absent(d: pd.DataFrame, max_gshare: float = 0.35) -> pd.Series:
    """Players entering season N off a season N-1 in which they played at most
    `max_gshare` of the games. This is the WR pass 1 §7 error class, isolated."""
    return (d["gshare_1"].fillna(0.0) <= max_gshare) & (d["entry"] == "veteran") \
        & (d["evidence"].fillna(0.0) > 0)


def availability_metrics(d: pd.DataFrame, season: int) -> Dict:
    """How well the availability sub-model does, overall and on the error class."""
    e = (d["proj_games"] - d["games"]).to_numpy(dtype=float)
    row = {"season": season, "mae_games": float(np.mean(np.abs(e))),
           "bias_games": float(np.mean(e))}
    sub = d[returning_absent(d)]
    row["n_returning"] = len(sub)
    if len(sub) >= 5:
        es = (sub["proj_games"] - sub["games"]).to_numpy(dtype=float)
        row["mae_games_returning"] = float(np.mean(np.abs(es)))
        row["bias_games_returning"] = float(np.mean(es))
        row["rho_returning"] = spearman(sub["proj_points"].to_numpy(dtype=float),
                                        sub["points"].to_numpy(dtype=float))
    return row


def per_season_availability(players: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([availability_metrics(g, s)
                         for s, g in players.groupby("season")])
