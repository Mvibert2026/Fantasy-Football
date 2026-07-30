#!/usr/bin/env python
"""Factor batch 1 -- run every arm declared in the pre-commitment.

    .venv/bin/python -m experiments.bottomup.factors.run_factors

Design: `docs/ranking/factor-batch-1-precommit.md`, committed d546cff BEFORE any
arm was fitted. 23 E1 tests, BH at q=0.10. E2 (ADP-board rho) is the bar and is
NOT in the FDR family -- it has 7 seasons and is known-underpowered at three of
four positions, which was stated in advance.
"""

from __future__ import annotations

import json
import sys
import warnings
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E            # noqa: E402
from experiments.bottomup.components import pos_model as M           # noqa: E402
from experiments.bottomup.components.pos_data import build_panel     # noqa: E402
from experiments.bottomup.factors.factor_features import (           # noqa: E402
    build_factor_features,
)

OUT = _REPO / "experiments" / "bottomup" / "results"
FIRST, LAST = 2014, 2024
BOOT_REPS = 4000

FEAT = partial(build_factor_features, use_proxy=False)
FEAT_PROXY = partial(build_factor_features, use_proxy=True)

# ---------------------------------------------------------------- designs
REC_V = list(M._RECEIVER_VOLUME)      # tpg_w tshare_w gshare_w evidence age age2 ppg_w experience
RB_C = list(M._RB_CARRY_VOLUME)
RB_T = list(M._RB_TARGET_VOLUME)


def _drop(cols, *names):
    return [c for c in cols if c not in names]


def _add(cols, *names):
    return list(cols) + [n for n in names if n not in cols]


# factor #19 -- the TD rates each position owns
TD_RATES = {"WR": ("tdpt", "tdpc"), "TE": ("tdpt", "tdpc"),
            "RB": ("tdpc", "tdpt"), "QB": ("tdpa", "tdpc")}
T1_KW = {"volume_prior": True}
# k -> effectively infinity AND recalibration off. Off is not a second change: a
# linear recalibration of an almost-constant regressor is scale-invariant and
# would mechanically undo the shrinkage, recovering the unshrunk rate. The pooled
# prior is already the training-level-calibrated rate, so there is nothing left
# for the recalibration to correct.
T2_KW = {"k_grid": (1e9,), "recalibrate": False}


def _td_over(pos: str, kw: Dict) -> Dict:
    return {"rate_overrides": {r: dict(kw) for r in TD_RATES[pos]}}


@dataclass
class Arm:
    factor: str
    arm: str
    position: str
    e1: str                       # the ONE component MAE declared in advance
    kwargs: Dict = field(default_factory=dict)
    proxy: bool = False
    in_family: bool = True


def _vol(pos: str, **cols) -> Dict:
    return {"model_kwargs": {"volume_cols": cols}}


ARMS: List[Arm] = []

# ---- factor #19, TD-rate regression -- 8 cells
for pos in ("WR", "TE", "RB", "QB"):
    e1 = {"WR": "rec_tds", "TE": "rec_tds", "RB": "rush_tds", "QB": "pass_tds"}[pos]
    ARMS.append(Arm("#19 TD-rate regression", "T1 volume-conditional prior",
                    pos, e1, {"model_kwargs": _td_over(pos, T1_KW)}))
    ARMS.append(Arm("#19 TD-rate regression", "T2 full regression to the mean",
                    pos, e1, {"model_kwargs": _td_over(pos, T2_KW)}))

# ---- factor #20, opportunity share -- 6 cells
for pos in ("WR", "TE"):
    ARMS.append(Arm("#20 opportunity share", "O1 share x pace reparameterisation",
                    pos, "targets",
                    _vol(pos, tpg=_add(_drop(REC_V, "tpg_w"),
                                       "team_tpg_w", "tshare_x_pace"))))
    ARMS.append(Arm("#20 opportunity share", "O2 share ablation",
                    pos, "targets", _vol(pos, tpg=_drop(REC_V, "tshare_w"))))
ARMS.append(Arm("#20 opportunity share", "O1 share x pace reparameterisation",
                "RB", "carries",
                _vol("RB",
                     carries_pg=_add(_drop(RB_C, "carries_pg_w"),
                                     "team_cpg_w", "cshare_x_pace"),
                     tpg=_add(_drop(RB_T, "tgt_pg_w"),
                              "team_tpg_w", "tshare_x_pace"))))
ARMS.append(Arm("#20 opportunity share", "O2 share ablation", "RB", "carries",
                _vol("RB", carries_pg=_drop(RB_C, "cshare_w"),
                     tpg=_drop(RB_T, "tshare_w"))))

# ---- factor #28, vacated opportunity -- 6 cells (V1 declares the proxy)
for pos in ("WR", "TE"):
    ARMS.append(Arm("#28 vacated opportunity", "V1 vacated share (PROXY)",
                    pos, "targets", _vol(pos, tpg=_add(REC_V, "vac_tshare")),
                    proxy=True))
    ARMS.append(Arm("#28 vacated opportunity", "V0c free control: team volume",
                    pos, "targets", _vol(pos, tpg=_add(REC_V, "team_tpg_w"))))
ARMS.append(Arm("#28 vacated opportunity", "V1 vacated share (PROXY)", "RB",
                "carries",
                _vol("RB", carries_pg=_add(RB_C, "vac_cshare"),
                     tpg=_add(RB_T, "vac_tshare")), proxy=True))
ARMS.append(Arm("#28 vacated opportunity", "V0c free control: team volume", "RB",
                "carries",
                _vol("RB", carries_pg=_add(RB_C, "team_cpg_w"),
                     tpg=_add(RB_T, "team_tpg_w"))))

# ---- factor #13, target-share stability -- 3 cells
for pos in ("WR", "TE"):
    ARMS.append(Arm("#13 target-share stability", "S1 stability-weighted share",
                    pos, "targets",
                    _vol(pos, tpg=_add(REC_V, "tshare_sd3", "tshare_n3"))))
ARMS.append(Arm("#13 target-share stability", "S1 stability-weighted share", "RB",
                "targets",
                _vol("RB", tpg=_add(RB_T, "tshare_sd3", "tshare_n3"))))


# ------------------------------------------------------------------ stats
def paired(metrics_a: pd.DataFrame, metrics_p: pd.DataFrame, col: str
           ) -> Tuple[float, float, float, float, int]:
    """arm - primary on `col`, paired by season. Bootstrap CI + paired t p-value."""
    if col not in metrics_a.columns or col not in metrics_p.columns:
        return (np.nan,) * 4 + (0,)
    j = metrics_a[["season", col]].merge(metrics_p[["season", col]], on="season",
                                         suffixes=("_a", "_p")).dropna()
    d = (j[f"{col}_a"] - j[f"{col}_p"]).to_numpy(dtype=float)
    n = len(d)
    if n < 3:
        return (np.nan,) * 4 + (n,)
    rng = np.random.default_rng(20260730)
    boot = np.array([np.mean(rng.choice(d, size=n, replace=True))
                     for _ in range(BOOT_REPS)])
    sd = float(np.std(d, ddof=1))
    if sd < 1e-15:
        p = 1.0
    else:
        t = float(np.mean(d)) / (sd / np.sqrt(n))
        try:
            from scipy import stats as _st
            p = float(2 * _st.t.sf(abs(t), df=n - 1))
        except Exception:                     # no scipy: normal approximation
            p = float(2 * 0.5 * np.exp(-0.717 * abs(t) - 0.416 * t * t))
    return (float(np.mean(d)), float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)), p, n)


def benjamini_hochberg(pvals: List[float], q: float) -> List[bool]:
    m = len(pvals)
    order = np.argsort(pvals)
    keep = np.zeros(m, dtype=bool)
    thresh = -1
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= q * rank / m:
            thresh = rank
    if thresh > 0:
        keep[order[:thresh]] = True
    return keep.tolist()


# --------------------------------------------------- factor #13 descriptive
def target_share_persistence(panel) -> pd.DataFrame:
    """Lag-1 -> lag-0 correlation of target share, per position. Descriptive,
    outside the FDR family. Reported on the same scale as the archetype
    persistence numbers (snap share r=+0.707) so the comparison is direct."""
    hist = panel.before(2024)
    team = panel.team_before(2024)
    h = hist.merge(team, on=["team", "season"], how="left")
    h = h[(h["season"] >= 2009) & (h["team_targets"] > 0)].copy()
    h["tshare"] = h["targets"] / h["team_targets"]
    h["cshare"] = h["carries"] / h["team_carries"].replace(0, np.nan)
    rows = []
    for pos, col, minv in [("WR", "tshare", 15), ("TE", "tshare", 15),
                           ("RB", "tshare", 10), ("RB", "cshare", 25)]:
        sub = h[h["position"] == pos]
        nxt = sub.copy()
        nxt["season"] = nxt["season"] - 1
        pair = sub.merge(nxt[["player_id", "season", col]], on=["player_id", "season"],
                         suffixes=("", "_next"))
        qual = "targets" if col == "tshare" else "carries"
        pair = pair[pair[qual] >= minv]
        if len(pair) < 30:
            continue
        x = pair[col].to_numpy(float)
        y = pair[f"{col}_next"].to_numpy(float)
        seasons = pair["season"].to_numpy()
        r = float(np.corrcoef(x, y)[0, 1])
        rho = E.spearman(x, y)
        uniq = np.unique(seasons)
        rng = np.random.default_rng(20260730)
        boot = []
        for _ in range(2000):
            pick = rng.choice(uniq, size=len(uniq), replace=True)
            idx = np.concatenate([np.where(seasons == s)[0] for s in pick])
            if len(idx) > 10:
                boot.append(np.corrcoef(x[idx], y[idx])[0, 1])
        rows.append(dict(position=pos, metric=col, n_pairs=len(pair),
                         n_seasons=len(uniq), pearson_r=r, spearman=rho,
                         lo=float(np.percentile(boot, 2.5)),
                         hi=float(np.percentile(boot, 97.5))))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- main
def main() -> None:
    panel = build_panel()
    print(f"panel: {len(panel.seasons)} seasons, "
          f"{panel.seasons[0]}-{panel.seasons[-1]} (2025 sealed)")

    print("\n" + "=" * 86)
    print("FACTOR #13 DESCRIPTIVE -- year-over-year persistence of usage share")
    print("=" * 86)
    pers = target_share_persistence(panel)
    print(pers.round(3).to_string(index=False))

    # --- primaries, one per position, on the same feature builder as the arms
    prim: Dict[str, pd.DataFrame] = {}
    prim_players: Dict[str, pd.DataFrame] = {}
    for pos in ("WR", "TE", "RB", "QB"):
        wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                           last_target=LAST, avail_arm="A", feature_fn=FEAT)
        pl, m = wf.run()
        prim[pos], prim_players[pos] = m, pl
        print(f"primary {pos}: {len(pl)} player-seasons, {len(m)} seasons, "
              f"proxy reads {sum(a['n_preseason_proxy_reads'] for a in wf.audit)}")

    rows = []
    for i, a in enumerate(ARMS, start=1):
        wf = E.WalkForward(panel=panel, position=a.position, first_target=FIRST,
                           last_target=LAST, avail_arm="A",
                           feature_fn=FEAT_PROXY if a.proxy else FEAT,
                           allow_preseason_proxy=a.proxy, **a.kwargs)
        pl, m = wf.run()
        proxy_reads = sum(x["n_preseason_proxy_reads"] for x in wf.audit)
        e1 = paired(m, prim[a.position], f"mae_{a.e1}")
        e2 = paired(m, prim[a.position], "adpsub_rho_model")
        e2f = paired(m, prim[a.position], "rho_model")
        rows.append(dict(
            idx=i, factor=a.factor, arm=a.arm, position=a.position, e1_comp=a.e1,
            e1_d=e1[0], e1_lo=e1[1], e1_hi=e1[2], e1_p=e1[3], e1_n=e1[4],
            e2_d=e2[0], e2_lo=e2[1], e2_hi=e2[2], e2_n=e2[4],
            full_d=e2f[0], full_lo=e2f[1], full_hi=e2f[2],
            proxy_reads=proxy_reads, n_players=len(pl)))
        print(f"[{i:2d}/{len(ARMS)}] {a.position:3s} {a.arm:38s} "
              f"E1 {e1[0]:+9.4f} p={e1[3]:.3f}   E2 {e2[0]:+.4f}  "
              f"proxy={proxy_reads}")

    res = pd.DataFrame(rows)
    fam = res["e1_p"].fillna(1.0).tolist()
    for q in (0.10, 0.05):
        res[f"bh_{int(q*100):02d}"] = benjamini_hochberg(fam, q)

    def grade(r) -> str:
        if not np.isfinite(r.e1_d):
            return "NO DATA"
        better = r.e1_d < 0
        if r.bh_10 and better:
            return "SURVIVES" if (np.isfinite(r.e2_d) and r.e2_d > 0) \
                else "PROJECTION-ONLY"
        if r.bh_10 and not better:
            return "HARMFUL"
        if (r.e1_lo < 0 and r.e1_hi < 0):
            return "MARGINAL"
        if (r.e1_lo > 0 and r.e1_hi > 0):
            return "MARGINAL-HARMFUL"
        return "NULL"

    res["grade"] = [grade(r) for r in res.itertuples()]

    print("\n" + "=" * 86)
    print(f"RESULTS -- E1 = out-of-sample MAE of the declared component "
          f"(negative = better), m={len(res)}, BH q=0.10")
    print("=" * 86)
    for f_, g in res.groupby("factor", sort=False):
        print(f"\n{f_}")
        for r in g.itertuples():
            print(f"  {r.position:3s} {r.arm:38s} "
                  f"E1 {r.e1_d:+8.4f} [{r.e1_lo:+8.4f},{r.e1_hi:+8.4f}] "
                  f"p={r.e1_p:.4f} bh10={'Y' if r.bh_10 else 'n'}  "
                  f"E2 {r.e2_d:+.4f} [{r.e2_lo:+.4f},{r.e2_hi:+.4f}]  {r.grade}")

    print("\ngrade counts:")
    print(res["grade"].value_counts().to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / "factor_batch1_results.csv", index=False)
    pers.to_csv(OUT / "factor_batch1_share_persistence.csv", index=False)
    print(f"\nwrote {OUT/'factor_batch1_results.csv'}")


if __name__ == "__main__":
    main()
