"""
SS5(a) lambda estimation, live_availability_adjustment.md: "the 2025 draft
alone can estimate lambda, in the correct population, with no mocks needed."
Run BEFORE writing live_availability.py's N_t(p) into anything load-bearing,
per the spec's own instruction.

DATA: the one real draft this project has -- 160 picks, 10 teams, ingested
via ingest_mock_drafts.py as mock_id='2025_league_draft_real' (is_mock=0).
This module reads `data/real_drafts/2025_league_draft.json` DIRECTLY rather
than the ingested `mock_picks` table, because 9 of the 160 picks are team
defenses with no player identity to resolve (ADR-039 -- no DST data ingested
at all) and correctly quarantine during ingestion. `mock_picks` has no
`position` column (it stores identity, not position), so the quarantined
picks' positions -- exactly the QB/DEF near-hard-cap behaviour this test
exists to check -- would silently vanish if this read through that table
instead of the source file.

MODEL: a conditional logit (McFadden), single shared covariate
x_p = log(share_t(p) / share_bar(p)), NO alternative-specific intercepts:

    P(position taken = p) = exp(beta * x_p) / sum_q exp(beta * x_q)

This is exactly the functional form live_availability.py's
N_t(p) = (share_t(p)/share_bar(p))^lambda implies for pick CHOICE under the
need mechanism alone (ADP/rank preference is not in this regression at all --
a real, stated limitation, not an oversight). The fitted beta IS the SS5(a)
estimate of lambda.

LIMITS, stated plainly (spec's own words): 160 picks, 10 clusters, one
season, and deficits are mechanically correlated with round (everyone has
deficits early). Cluster SEs by team. Treat the result as A PRIOR WITH A WIDE
INTERVAL, not a measurement -- these numbers do not clear the bar for
anything in CLAUDE.md SS6.3 on their own.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.optimize import minimize

from live_availability import POSITIONS, SHARE_BAR, need_share

DRAFT_LOG_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "real_drafts" / "2025_league_draft.json"
)


def load_picks(path: Path = DRAFT_LOG_PATH) -> List[dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return sorted(raw["picks"], key=lambda p: p["overall_pick"])


def build_regression_rows(
    picks: List[dict],
) -> Tuple[List[object], List[np.ndarray], List[int]]:
    """For each pick (in draft order), the drafting team's
    log(share_t(p)/share_bar(p)) vector over POSITIONS, evaluated on that
    team's counts BEFORE this pick, plus the index of the position actually
    taken. Team counts start at zero and accumulate strictly in pick order --
    this is what makes a team's FIRST pick always produce an all-zero x
    vector (share_t == share_bar with no picks made yet), which is the
    correct 'no information yet' behaviour, not a bug.

    Picks at a position outside POSITIONS (e.g. K, which this league does not
    roster) are skipped -- none exist in the 2025 draft, but a future league's
    log should not crash on one.
    """
    counts: Dict[object, Dict[str, int]] = {}
    teams: List[object] = []
    x_rows: List[np.ndarray] = []
    y_idx: List[int] = []
    for pick in picks:
        team = pick["team_slot"]
        pos = pick["position"]
        if pos not in POSITIONS:
            continue
        drafted = counts.setdefault(team, {p: 0 for p in POSITIONS})
        share = need_share(drafted)
        x = np.array([math.log(share[p] / SHARE_BAR[p]) for p in POSITIONS])
        teams.append(team)
        x_rows.append(x)
        y_idx.append(POSITIONS.index(pos))
        drafted[pos] = drafted.get(pos, 0) + 1
    return teams, x_rows, y_idx


def _softmax_rows(z: np.ndarray) -> np.ndarray:
    m = z.max(axis=1, keepdims=True)
    e = np.exp(z - m)
    return e / e.sum(axis=1, keepdims=True)


def fit_conditional_logit(
    x_rows: List[np.ndarray], y_idx: List[int], teams: List[object]
) -> Dict[str, object]:
    """MLE of the single shared coefficient beta (= lambda under this
    regression's own reasoning), plus a cluster-robust (by team) SE.

    Cluster-robust variance for a scalar M-estimator: Var(beta_hat) =
    (sum_c S_c^2) / H^2, where S_c is the CLUSTER-SUMMED per-observation
    score (d log-lik_i / d beta) at beta_hat, and H is the (positive) Hessian
    of the NEGATIVE log-likelihood at beta_hat -- for a conditional logit
    with one covariate, H_i = Var_p[x_i] under the fitted softmax, a standard
    result (no numeric differentiation needed).
    """
    x = np.array(x_rows)  # (n, k)
    y = np.array(y_idx)
    n = len(y)

    def neg_ll(beta_arr: np.ndarray) -> float:
        beta = beta_arr[0]
        z = beta * x
        m = z.max(axis=1, keepdims=True)
        lse = m[:, 0] + np.log(np.exp(z - m).sum(axis=1))
        chosen = z[np.arange(n), y]
        return float(-np.sum(chosen - lse))

    result = minimize(neg_ll, x0=np.array([0.5]), method="BFGS")
    beta_hat = float(result.x[0])

    z = beta_hat * x
    p = _softmax_rows(z)
    e_x = np.sum(p * x, axis=1)
    e_x2 = np.sum(p * x**2, axis=1)
    var_x = np.clip(e_x2 - e_x**2, 0.0, None)
    score_i = x[np.arange(n), y] - e_x

    H = float(np.sum(var_x))
    cluster_scores: Dict[object, float] = {}
    for t, s in zip(teams, score_i):
        cluster_scores[t] = cluster_scores.get(t, 0.0) + float(s)
    B = sum(s * s for s in cluster_scores.values())
    if H > 0:
        var_beta = B / (H * H)
        se = math.sqrt(var_beta) if var_beta >= 0 else float("nan")
    else:
        se = float("nan")
    z_stat = beta_hat / se if se == se and se > 0 else float("nan")

    return {
        "lambda_hat": beta_hat,
        "se_clustered": se,
        "z": z_stat,
        "n_obs": n,
        "n_teams": len(cluster_scores),
        "converged": bool(result.success),
    }


def estimate_lambda_from_2025_draft(path: Path = DRAFT_LOG_PATH) -> Dict[str, object]:
    picks = load_picks(path)
    teams, x_rows, y_idx = build_regression_rows(picks)
    fit = fit_conditional_logit(x_rows, y_idx, teams)
    fit["prior"] = 0.5
    fit["source"] = str(path)
    return fit


def main() -> None:
    report = estimate_lambda_from_2025_draft()
    print(
        f"lambda_hat={report['lambda_hat']:.4f}  se_clustered={report['se_clustered']:.4f}  "
        f"z={report['z']:.3f}  n_obs={report['n_obs']}  n_teams={report['n_teams']}  "
        f"converged={report['converged']}  (prior was {report['prior']})"
    )


if __name__ == "__main__":
    main()
