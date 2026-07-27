"""Registered metrics for the prototype (frozen before fitting).

- Primary: Kendall tau_b within position (repo convention, ADR-B).
- Co-primary: draft-weighted VBD capture at replacement depth K
  (QB10/RB30/WR40/TE10 — ReplacementLevels().baselines()).
- Secondary: R^2 triplet (season points / ppg / games), computed against the
  TEST fold's own mean (ADR-E §8 item 6).
- Season-level percentile bootstrap CIs; paired deltas resample seasons.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import kendalltau

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scoring import ReplacementLevels  # noqa: E402

REPLACEMENT_K = ReplacementLevels().baselines()  # {'QB':10,'RB':30,'WR':40,'TE':10}
N_BOOTSTRAP = 2000
SEED = 20260727


def tau_b(pred_value: Dict[str, float], actual_points: Dict[str, float],
          pids: Sequence[str]) -> float:
    """tau_b between predicted value and actual points over the universe."""
    common = [p for p in pids if p in pred_value]
    if len(common) < 8:
        return float("nan")
    pv = [pred_value[p] for p in common]
    ap = [actual_points.get(p, 0.0) for p in common]
    t, _ = kendalltau(pv, ap, variant="b")
    return float(t)


def vbd_capture(pred_value: Dict[str, float], actual_points: Dict[str, float],
                pids: Sequence[str], position: str) -> float:
    """Sum of actual VBD of the model's top-K vs the oracle top-K.
    Replacement = points of the K-th actual finisher within the universe."""
    k = REPLACEMENT_K[position]
    pts = sorted((actual_points.get(p, 0.0) for p in pids), reverse=True)
    if len(pts) < k:
        return float("nan")
    repl = pts[k - 1]
    vbd = {p: max(0.0, actual_points.get(p, 0.0) - repl) for p in pids}
    oracle = sum(sorted(vbd.values(), reverse=True)[:k])
    if oracle <= 0:
        return float("nan")
    ranked = sorted((p for p in pids if p in pred_value),
                    key=lambda p: -pred_value[p])[:k]
    return sum(vbd[p] for p in ranked) / oracle


def r2(pred: Dict[str, float], actual: Dict[str, float],
       pids: Sequence[str]) -> float:
    common = [p for p in pids if p in pred and p in actual]
    if len(common) < 8:
        return float("nan")
    a = np.array([actual[p] for p in common])
    y = np.array([pred[p] for p in common])
    ss_res = float(((a - y) ** 2).sum())
    ss_tot = float(((a - a.mean()) ** 2).sum())
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def season_bootstrap_ci(values: Sequence[float], seed: int = SEED,
                        n: int = N_BOOTSTRAP) -> Tuple[float, float, float]:
    """(point, lo, hi): mean of per-season values, percentile bootstrap over
    seasons. Degenerate at tiny n by construction — the caller reports n."""
    vals = np.array([v for v in values if not np.isnan(v)])
    if len(vals) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(n, len(vals)))
    means = vals[idx].mean(axis=1)
    return float(vals.mean()), float(np.percentile(means, 2.5)), \
        float(np.percentile(means, 97.5))


def paired_delta_ci(a: Sequence[float], b: Sequence[float], seed: int = SEED,
                    n: int = N_BOOTSTRAP) -> Tuple[float, float, float, float]:
    """Paired per-season deltas a-b: (mean, lo, hi, frac_positive)."""
    deltas = np.array([x - y for x, y in zip(a, b)
                       if not (np.isnan(x) or np.isnan(y))])
    if len(deltas) == 0:
        return (float("nan"),) * 4
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(deltas), size=(n, len(deltas)))
    means = deltas[idx].mean(axis=1)
    return float(deltas.mean()), float(np.percentile(means, 2.5)), \
        float(np.percentile(means, 97.5)), float((deltas > 0).mean())
