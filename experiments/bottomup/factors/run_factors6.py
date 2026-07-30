#!/usr/bin/env python
"""Factor batch 6 -- run every arm declared in the pre-commitment.

    .venv/bin/python -m experiments.bottomup.factors.run_factors6

Design: `docs/ranking/factor-batch-6-precommit.md`, committed BEFORE any arm was
fitted (f6e09da). 23 registered tests in one batch, registered into the SHARED
campaign family `docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`.

  E1a  full-universe component MAE, 11 seasons -- THE CAMPAIGN FDR ENDPOINT.
  E1b  the same MAE on the ADP board, 7 seasons -- a REQUIRED DIRECTION CHECK.
  E2   ADP-board Spearman, 7 seasons, the bar. NOT in the FDR family.

BH is computed at the CAMPAIGN denominator (sum of every `m` in the manifest),
not at the batch's own m -- four factor batches ran concurrently against the same
harness on the same day, and correcting inside each while ignoring the others is
the multiplicity failure CLAUDE.md 6.3 names. Because batches 4 and 5 could not
be seen at the moment this ran, every surviving arm also reports its BREAKING M:
the largest campaign denominator at which it would still clear BH at q=0.10.

NO ARM HERE READS SEASON N. Every arm runs `allow_preseason_proxy=False`, so a
zero proxy-read count is enforced by the harness rather than asserted in prose.
"""

from __future__ import annotations

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

from experiments.bottomup.components import pos_eval as E             # noqa: E402
from experiments.bottomup.components import pos_model as M            # noqa: E402
from experiments.bottomup.components.pos_data import build_panel      # noqa: E402
from experiments.bottomup.factors.factor_features6 import (           # noqa: E402
    QBEFF_K0, build_factor6_features, source,
)
from experiments.bottomup.factors.run_factors import (                # noqa: E402
    benjamini_hochberg, paired,
)

OUT = _REPO / "experiments" / "bottomup" / "results"
MANIFEST = _REPO / "docs" / "preregistration" / "families" / \
    "F-FACTOR-CAMPAIGN-2026-07-30.yaml"
FIRST, LAST = 2014, 2024
BATCH_M = 23                     # §4 of the pre-commitment, fixed in advance
Q_MAIN, Q_TIGHT = 0.10, 0.05
COVERAGE_GATE = 0.80             # §5, fixed before the coverage was measured
VOID_RATIO = 0.50                # §5 leak trigger, fixed in advance
LEAK_PCT = 2.0                   # §5 escalation threshold, % of primary error

FEAT_BASE = partial(build_factor6_features, blocks=())
FEAT_QB = partial(build_factor6_features, blocks=("qbeff",))
FEAT_XF = partial(build_factor6_features, blocks=("xfp",))

E1_COMPONENT = {"QB": "attempts", "RB": "carries", "WR": "targets", "TE": "targets"}
#: the volume spec that produces each position's declared E1 component
E1_SPEC = {"QB": "att_pg", "RB": "carries_pg", "WR": "tpg", "TE": "tpg"}
BASE_SPEC = {"QB": list(M._QB_ATT_VOLUME), "RB": list(M._RB_CARRY_VOLUME),
             "WR": list(M._RECEIVER_VOLUME), "TE": list(M._RECEIVER_VOLUME)}


def _spec_add(pos: str, *cols: str) -> Dict:
    base = BASE_SPEC[pos]
    return {"model_kwargs": {"volume_cols": {
        E1_SPEC[pos]: base + [c for c in cols if c not in base]}}}


def _spec_replace(pos: str, old: str, new: str) -> Dict:
    base = [new if c == old else c for c in BASE_SPEC[pos]]
    if old not in BASE_SPEC[pos]:
        raise KeyError(f"{pos}: {old!r} is not in the primary spec to replace")
    return {"model_kwargs": {"volume_cols": {E1_SPEC[pos]: base}}}


@dataclass
class Arm:
    idx: int
    factor: str
    arm: str
    position: str
    block: str                       # "qbeff" | "xfp"
    kwargs: Dict = field(default_factory=dict)
    control_for: Optional[str] = None   # the flag column this arm gates on
    is_control: bool = False
    gate_flag: Optional[str] = None     # coverage flag this arm's cell needs


ARMS: List[Arm] = []
_i = 0


def _add(factor, arm, pos, block, kwargs, *, is_control=False, gate=None,
         control_for=None) -> None:
    global _i
    _i += 1
    ARMS.append(Arm(_i, factor, arm, pos, block, kwargs, is_control=is_control,
                    gate_flag=gate, control_for=control_for))


# ---- Family P: passing efficiency over volume (N10), QB only
for _id, _col, _label in (
        ("P1", "epa_db_w", "P1 EPA per dropback"),
        ("P2", "anya_w", "P2 ANY/A"),
        ("P3", "pratg_w", "P3 passer rating"),
        ("P4", "cpoe_w", "P4 CPOE")):
    _add("N10 passing efficiency", _label, "QB", "qbeff", _spec_add("QB", _col),
         gate="cpoe_known" if _id == "P4" else "qbeff_known",
         control_for="P4c" if _id == "P4" else "Pc")
_add("N10 passing efficiency", "P4c CPOE coverage CONTROL", "QB", "qbeff",
     _spec_add("QB", "cpoe_known"), is_control=True)
_add("N10 passing efficiency", "Pc QB-efficiency coverage CONTROL", "QB", "qbeff",
     _spec_add("QB", "qbeff_known"), is_control=True)

# ---- Family K: sack avoidance (N11), QB only. Shares Pc as its control.
_add("N11 sack avoidance", "K1 sack rate per dropback", "QB", "qbeff",
     _spec_add("QB", "sackrate_w"), gate="qbeff_known", control_for="Pc")

# ---- Family X: expected fantasy points (#18), all four positions
for pos in ("QB", "RB", "WR", "TE"):
    _add("#18 expected fantasy points", "X1 add xFP per game", pos, "xfp",
         _spec_add(pos, "xfp_pg_w"), gate="xfp_known", control_for="X4c")
for pos in ("QB", "RB", "WR", "TE"):
    _add("#18 expected fantasy points", "X2 REPLACE ppg_w with xFP per game", pos,
         "xfp", _spec_replace(pos, "ppg_w", "xfp_pg_w"), gate="xfp_known",
         control_for="X4c")
for pos in ("QB", "RB", "WR", "TE"):
    _add("#18 expected fantasy points", "X3 luck residual (actual - expected)", pos,
         "xfp", _spec_add(pos, "xfp_resid_pg_w"), gate="xfp_known",
         control_for="X4c")
for pos in ("QB", "RB", "WR", "TE"):
    _add("#18 expected fantasy points", "X4c xFP coverage CONTROL", pos, "xfp",
         _spec_add(pos, "xfp_known"), is_control=True)

assert len(ARMS) == BATCH_M, f"declared m={BATCH_M}, built {len(ARMS)}"


# ------------------------------------------------------------------ campaign m
def campaign_m() -> Tuple[int, str]:
    """Sum of every `m` registered in the shared manifest.

    Parsed with a two-line reader rather than a YAML dependency: the file is
    append-only and the only thing needed from it is the integer next to `m:`.
    If it cannot be read the batch REFUSES to fall back to its own m silently --
    a batch-local denominator masquerading as a campaign one is exactly what the
    manifest exists to prevent.
    """
    if not MANIFEST.exists():
        raise FileNotFoundError(f"campaign manifest missing: {MANIFEST}")
    ms, batches = [], []
    for line in MANIFEST.read_text().splitlines():
        s = line.strip()
        if s.startswith("- batch:"):
            batches.append(s.split(":", 1)[1].strip())
        elif s.startswith("m:") and batches:
            ms.append(int(s.split(":", 1)[1].strip()))
    if not ms:
        raise ValueError("campaign manifest declares no m")
    return int(sum(ms)), ", ".join(f"batch {b}: m={m}" for b, m in zip(batches, ms))


def breaking_m(pvals: List[float], i: int, q: float, m_hi: int = 4000) -> int:
    """Largest campaign denominator at which arm `i` still clears BH at `q`.

    Batches 4 and 5 were running concurrently and their m could not be read at
    run time. Rather than assert a denominator this batch cannot verify, each
    surviving arm carries the number that lets any later reader check it against
    the finished manifest without rerunning anything.
    """
    lo, hi = 0, 0
    for m in range(len(pvals), m_hi + 1):
        pad = pvals + [1.0] * (m - len(pvals))
        if benjamini_hochberg(pad, q)[i]:
            hi = m
        else:
            break
    return hi if hi else lo


# ------------------------------------------------------------------ diagnostics
def overlap_diagnostic(panel) -> pd.DataFrame:
    """MANDATORY under §5, regardless of result, and it is not a test.

    xFP is a model output whose inputs overlap ours. If `xfp_pg_w` is essentially
    `ppg_w` renamed, X1/X2 are a restatement whatever their p-values say.
    """
    rows = []
    for pos in ("QB", "RB", "WR", "TE"):
        vol = {"QB": "att_pg_w", "RB": "carries_pg_w",
               "WR": "tgt_pg_w", "TE": "tgt_pg_w"}[pos]
        for s in range(FIRST, LAST + 1):
            u = E.universe_for(panel, s, pos)
            f = FEAT_XF(panel, u, s)
            k = f["xfp_known"] > 0
            if k.sum() < 20:
                continue
            sub = f.loc[k, ["xfp_pg_w", "ppg_w", vol, "xfp_resid_pg_w"]].fillna(0.0)
            rows.append(dict(
                position=pos, season=s, n=int(k.sum()),
                corr_xfp_ppg=float(sub["xfp_pg_w"].corr(sub["ppg_w"])),
                corr_xfp_vol=float(sub["xfp_pg_w"].corr(sub[vol])),
                corr_resid_ppg=float(sub["xfp_resid_pg_w"].corr(sub["ppg_w"])),
            ))
    d = pd.DataFrame(rows)
    return d.groupby("position", as_index=False).agg(
        seasons=("season", "size"), n=("n", "mean"),
        corr_xfp_ppg=("corr_xfp_ppg", "mean"),
        corr_xfp_vol=("corr_xfp_vol", "mean"),
        corr_resid_ppg=("corr_resid_ppg", "mean"))


_QB_METRICS = ["epa_db_w", "anya_w", "pratg_w", "cpoe_w", "sackrate_w"]


def qb_descriptives(panel) -> pd.DataFrame:
    """§7 descriptive secondaries. OUTSIDE THE FAMILY, CARRYING NO CLAIM.

    Three numbers per metric, all Spearman, busts retained:
      persist   lagged metric at season N vs the same metric measured on N itself
      to_points lagged metric vs realised season-N fantasy points, THIS league
      resid_adp lagged metric vs the residual of realised points on consensus ADP
                -- i.e. what the market has not already priced. n = 7 seasons.
    """
    rows = []
    for s in range(FIRST, LAST + 1):
        board = E.adp.load_adp(s, position="QB")
        extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                 if len(board) else None)
        u = E.universe_for(panel, s, "QB", extra_ids=extra)
        f = FEAT_QB(panel, u, s)
        o = E.outcome_components(panel, u, s)
        d = f.merge(o[["player_id", "points", "attempts"]], on="player_id")
        if len(board):
            b = board.loc[~board["unmatched"], ["player_id", "average_pick"]]
            d = d.merge(b.drop_duplicates("player_id"), on="player_id", how="left")
        else:
            d["average_pick"] = np.nan
        known = d["qbeff_known"] > 0
        sub = d[known]
        if len(sub) < 12:
            continue
        adp_ok = sub["average_pick"].notna()
        resid = None
        if adp_ok.sum() >= 10:
            x = -sub.loc[adp_ok, "average_pick"].to_numpy(dtype=float)
            y = sub.loc[adp_ok, "points"].to_numpy(dtype=float)
            xr = pd.Series(x).rank().to_numpy()
            yr = pd.Series(y).rank().to_numpy()
            beta = np.polyfit(xr, yr, 1)
            resid = yr - np.polyval(beta, xr)
        for mcol in _QB_METRICS:
            r = dict(season=s, metric=mcol, n=len(sub))
            r["to_points"] = E.spearman(sub[mcol].to_numpy(dtype=float),
                                        sub["points"].to_numpy(dtype=float))
            if resid is not None:
                r["resid_adp"] = E.spearman(
                    sub.loc[adp_ok, mcol].to_numpy(dtype=float), resid)
                r["n_adp"] = int(adp_ok.sum())
            rows.append(r)
    d = pd.DataFrame(rows)
    for c in ("resid_adp", "n_adp"):
        if c not in d.columns:
            d[c] = np.nan
    return d.groupby("metric", as_index=False).agg(
        seasons=("season", "size"), n=("n", "mean"),
        to_points=("to_points", "mean"),
        resid_adp=("resid_adp", "mean"), n_adp=("n_adp", "mean"))


def qb_persistence(panel) -> pd.DataFrame:
    """YoY persistence of each raw QB efficiency metric, on our own data with
    busts retained -- the direct check on SumerSports' r~0.60 / r~0.50, which
    were measured on survivors and are upper bounds under CLAUDE.md §6.2."""
    qb, _ = source().before(panel, LAST)
    q = qb[qb["dropbacks"] >= 100].copy()
    q["epa_db"] = q["epa"] / q["dropbacks"]
    q["anya"] = q["anya_num"] / q["dropbacks"]
    q["sackrate"] = q["sacks"] / q["dropbacks"]
    q["cpoe"] = np.where(q["cpoe_den"] > 0, q["cpoe_num"] / q["cpoe_den"].replace(0, np.nan),
                         np.nan)
    q["cmp_rate"] = q["cmp"] / q["att"]
    q["ypa"] = q["pass_yards"] / q["att"]
    q["tdpa"] = q["pass_tds"] / q["att"]
    q["intpa"] = q["ints"] / q["att"]
    from experiments.bottomup.factors.factor_features6 import _passer_rating
    q["pratg"] = _passer_rating(q["cmp_rate"].to_numpy(), q["ypa"].to_numpy(),
                                q["tdpa"].to_numpy(), q["intpa"].to_numpy())
    nxt = q.copy()
    nxt["season"] = nxt["season"] - 1
    j = q.merge(nxt, on=["player_id", "season"], suffixes=("", "_n"))
    rows = []
    for mcol in ("epa_db", "anya", "pratg", "cpoe", "sackrate"):
        sub = j[["season", mcol, f"{mcol}_n"]].dropna()
        if len(sub) < 50:
            continue
        rows.append(dict(metric=mcol, n_pairs=len(sub),
                         first=int(sub["season"].min()), last=int(sub["season"].max()),
                         yoy_pearson=float(sub[mcol].corr(sub[f"{mcol}_n"])),
                         yoy_spearman=float(sub[mcol].corr(sub[f"{mcol}_n"],
                                                           method="spearman"))))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------ main
def main() -> None:
    panel = build_panel()
    src = source()
    print(f"panel: {len(panel.seasons)} seasons, {panel.seasons[0]}-"
          f"{panel.seasons[-1]} (2025 sealed)")
    print(f"QB-efficiency rows: {len(src.qbeff)} "
          f"{src.qbeff['season'].min()}-{src.qbeff['season'].max()}")
    print(f"xFP rows (REG only): {len(src.xfp)} "
          f"{src.xfp['season'].min()}-{src.xfp['season'].max()}")

    m_campaign, m_detail = campaign_m()
    print(f"\ncampaign family: {m_detail}  ->  CAMPAIGN m = {m_campaign}")
    print(f"batch-local m = {BATCH_M} (reported as SECONDARY only)")

    # ---- primaries, one per position, on the SAME builder as the arms
    prim: Dict[str, pd.DataFrame] = {}
    for pos in ("QB", "RB", "WR", "TE"):
        wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                           last_target=LAST, avail_arm="A", feature_fn=FEAT_BASE)
        pl, mt = wf.run()
        prim[pos] = mt
        px = sum(a["n_preseason_proxy_reads"] for a in wf.audit)
        print(f"primary {pos}: {len(pl)} player-seasons, {len(mt)} seasons, "
              f"proxy reads {px}")
        if px:
            raise RuntimeError(f"primary {pos} touched a season-N read")

    # ---- coverage gates, evaluated ON THE ADP BOARD before any result is read
    cov: Dict[Tuple[str, str], float] = {}
    for pos in ("QB", "RB", "WR", "TE"):
        vals: Dict[str, List[float]] = {"qbeff_known": [], "cpoe_known": [],
                                        "xfp_known": []}
        for s in range(FIRST, LAST + 1):
            board = E.adp.load_adp(s, position=pos)
            extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                     if len(board) else None)
            if not extra:
                continue
            u = E.universe_for(panel, s, pos, extra_ids=extra)
            f = build_factor6_features(panel, u, s, blocks=("qbeff", "xfp"))
            on = f["player_id"].isin(extra)
            if not on.any():
                continue
            for flag in vals:
                vals[flag].append(float(f.loc[on, flag].mean()))
        for flag, v in vals.items():
            cov[(pos, flag)] = float(np.mean(v)) if v else float("nan")
    print("\ncoverage ON THE ADP BOARD (gate = %.2f):" % COVERAGE_GATE)
    for pos in ("QB", "RB", "WR", "TE"):
        print("  %-3s " % pos + "  ".join(
            f"{f} {cov[(pos, f)]:.3f}" for f in
            ("qbeff_known", "cpoe_known", "xfp_known")))

    # ------------------------------------------------------------------ run
    rows = []
    for a in ARMS:
        gated = (a.gate_flag is not None
                 and not (cov[(a.position, a.gate_flag)] >= COVERAGE_GATE))
        if gated:
            rows.append(dict(idx=a.idx, factor=a.factor, arm=a.arm,
                             position=a.position, e1_comp=E1_COMPONENT[a.position],
                             is_control=a.is_control, grade="NO DATA",
                             coverage=cov[(a.position, a.gate_flag)]))
            print(f"[{a.idx:2d}/{BATCH_M}] {a.position:3s} {a.arm:38s} NO DATA "
                  f"({a.gate_flag} {cov[(a.position, a.gate_flag)]:.3f})")
            continue
        feat = FEAT_QB if a.block == "qbeff" else FEAT_XF
        wf = E.WalkForward(panel=panel, position=a.position, first_target=FIRST,
                           last_target=LAST, avail_arm="A", feature_fn=feat,
                           allow_preseason_proxy=False, **a.kwargs)
        pl, mt = wf.run()
        px = sum(x["n_preseason_proxy_reads"] for x in wf.audit)
        comp = E1_COMPONENT[a.position]
        e1a = paired(mt, prim[a.position], f"mae_{comp}")
        e1b = paired(mt, prim[a.position], f"adpsub_mae_{comp}")
        e2 = paired(mt, prim[a.position], "adpsub_rho_model")
        rho = paired(mt, prim[a.position], "rho_model")
        pyd = paired(mt, prim[a.position], "mae_pass_yards")
        base = float(prim[a.position][f"mae_{comp}"].mean())
        base_b = float(prim[a.position][f"adpsub_mae_{comp}"].mean())
        rows.append(dict(
            idx=a.idx, factor=a.factor, arm=a.arm, position=a.position,
            e1_comp=comp, is_control=a.is_control, control_for=a.control_for,
            e1a_d=e1a[0], e1a_lo=e1a[1], e1a_hi=e1a[2], e1a_p=e1a[3], e1a_n=e1a[4],
            e1a_pct=100.0 * e1a[0] / base if base else np.nan,
            e1b_d=e1b[0], e1b_lo=e1b[1], e1b_hi=e1b[2], e1b_n=e1b[4],
            e2_d=e2[0], e2_lo=e2[1], e2_hi=e2[2], e2_n=e2[4],
            rho_d=rho[0], rho_lo=rho[1], rho_hi=rho[2],
            passyds_d=pyd[0], proxy_reads=px, n_players=len(pl),
            primary_mae=base, primary_adpsub_mae=base_b,
            coverage=cov[(a.position, a.gate_flag)] if a.gate_flag else np.nan))
        print(f"[{a.idx:2d}/{BATCH_M}] {a.position:3s} {a.arm:38s} "
              f"E1a {e1a[0]:+9.4f} ({rows[-1]['e1a_pct']:+6.2f}%) p={e1a[3]:.4f} "
              f"n={e1a[4]}  E1b {e1b[0]:+9.4f}  E2 {e2[0]:+.4f}  proxy={px}")

    res = pd.DataFrame(rows)
    for c in ("grade", "e1a_d", "e1a_lo", "e1a_hi", "e1a_p", "e1b_d", "e2_d"):
        if c not in res.columns:
            res[c] = np.nan

    # ---- BH at the CAMPAIGN denominator (§4), batch-local reported as secondary
    live = res["grade"].isna()
    pv = res.loc[live, "e1a_p"].fillna(1.0).tolist()
    pv_full = pv + [1.0] * (BATCH_M - len(pv))
    for tag, m_den, q in (("camp10", m_campaign, Q_MAIN),
                          ("camp05", m_campaign, Q_TIGHT),
                          ("batch10", BATCH_M, Q_MAIN)):
        pad = pv_full + [1.0] * max(0, m_den - BATCH_M)
        res[f"bh_{tag}"] = False
        res.loc[live, f"bh_{tag}"] = benjamini_hochberg(pad, q)[:int(live.sum())]
    res["breaking_m"] = np.nan
    for j, (i, _) in enumerate(res.loc[live].iterrows()):
        if res.loc[i, "bh_camp10"]:
            res.loc[i, "breaking_m"] = breaking_m(pv_full, j, Q_MAIN)

    # ---- the VOID rule (§5): a control arm >= 50% of its treatment kills the
    # treatment's INTERPRETATION, regardless of the treatment's own p-value.
    ctrl_abs = {}
    for r in res.itertuples():
        if r.is_control:
            key = ("Pc" if r.arm.startswith("Pc") else
                   "P4c" if r.arm.startswith("P4c") else "X4c")
            ctrl_abs[(key, r.position)] = abs(r.e1a_d) if np.isfinite(r.e1a_d) else 0.0

    def voided(r) -> bool:
        if r.is_control or not isinstance(r.control_for, str):
            return False
        c = ctrl_abs.get((r.control_for, r.position))
        return bool(c is not None and np.isfinite(r.e1a_d) and abs(r.e1a_d) > 0
                    and c >= VOID_RATIO * abs(r.e1a_d))

    def grade(r) -> str:
        if isinstance(getattr(r, "grade", None), str):
            return r.grade
        if not np.isfinite(r.e1a_d):
            return "NO DATA"
        better = r.e1a_d < 0
        sig = bool(r.bh_camp10)
        if sig and better:
            g = ("BOARD-NEUTRAL" if not (np.isfinite(r.e1b_d) and r.e1b_d < 0)
                 else ("SURVIVES" if (np.isfinite(r.e2_d) and r.e2_d > 0)
                       else "PROJECTION-ONLY"))
            return f"VOID-COVERAGE ({g})" if voided(r) else g
        if sig and not better:
            return "HARMFUL"
        if r.e1a_lo < 0 and r.e1a_hi < 0:
            return "MARGINAL"
        if r.e1a_lo > 0 and r.e1a_hi > 0:
            return "MARGINAL-HARMFUL"
        return "NULL"

    res["grade"] = [grade(r) for r in res.itertuples()]
    res["leak_trigger"] = (res["e1a_pct"] <= -LEAK_PCT)

    print("\n" + "=" * 104)
    print(f"RESULTS -- E1a = full-universe component MAE (negative = better). "
          f"BH q=0.10 at CAMPAIGN m={m_campaign}")
    print("=" * 104)
    for f_, g in res.groupby("factor", sort=False):
        print(f"\n{f_}")
        for r in g.itertuples():
            if r.grade == "NO DATA":
                print(f"  {r.position:3s} {r.arm:38s} NO DATA")
                continue
            bm = "" if not np.isfinite(r.breaking_m) else f" breakM={int(r.breaking_m)}"
            print(f"  {r.position:3s} {r.arm:38s} "
                  f"E1a {r.e1a_d:+9.4f} [{r.e1a_lo:+9.4f},{r.e1a_hi:+9.4f}] "
                  f"({r.e1a_pct:+6.2f}%) p={r.e1a_p:.4f}  "
                  f"E1b {r.e1b_d:+9.4f}  E2 {r.e2_d:+.4f}  {r.grade}{bm}")

    print("\ngrade counts:")
    print(res["grade"].value_counts().to_string())
    trig = res[res["leak_trigger"] & ~res["is_control"]]
    print(f"\nleak/overlap trigger (E1a better than {LEAK_PCT}% of primary error): "
          f"{len(trig)} arm(s)" + ("" if not len(trig) else
                                   " -- ESCALATE BEFORE WRITE-UP"))
    for r in trig.itertuples():
        print(f"    {r.position} {r.arm}  {r.e1a_pct:+.2f}%")

    OUT.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / "factor_batch6_results.csv", index=False)

    print("\n" + "=" * 104)
    print("MANDATORY xFP OVERLAP DIAGNOSTIC (§5) -- a description, not a test")
    print("=" * 104)
    ov = overlap_diagnostic(panel)
    print(ov.round(4).to_string(index=False))
    ov.to_csv(OUT / "factor_batch6_xfp_overlap.csv", index=False)

    print("\n" + "=" * 104)
    print("DESCRIPTIVE SECONDARIES (§7) -- OUTSIDE THE FAMILY, NO CLAIM ATTACHED")
    print("=" * 104)
    per = qb_persistence(panel)
    print("\nYoY persistence of each raw QB metric, >=100 dropbacks both years:")
    print(per.round(4).to_string(index=False))
    per.to_csv(OUT / "factor_batch6_qb_persistence.csv", index=False)
    desc = qb_descriptives(panel)
    print("\nLagged metric vs season-N QB points (this league), and vs the "
          "residual on consensus ADP:")
    print(desc.round(4).to_string(index=False))
    desc.to_csv(OUT / "factor_batch6_qb_descriptives.csv", index=False)

    print(f"\nQBEFF_K0 = {QBEFF_K0} dropbacks (fixed a priori, never tuned)")
    print(f"wrote {OUT/'factor_batch6_results.csv'} and three companions")


if __name__ == "__main__":
    main()
