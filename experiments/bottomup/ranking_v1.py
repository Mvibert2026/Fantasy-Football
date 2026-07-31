#!/usr/bin/env python
"""Ranking version **v1** -- assembled and tested end to end.

    .venv/bin/python -m experiments.bottomup.ranking_v1

Pre-commitment: `docs/ranking/ranking-v1-precommit.md`, committed BEFORE this ran.
Config blob:    `experiments/bottomup/ranking_versions/v1.json` -- every knob is
                read from there, nothing is hardcoded here (`CLAUDE.md` §4).

WHY THIS EXISTS. Across ~90 registered factor tests in batches 1-7, a *ranking
version* has never been assembled or tested; every arm was a single feature
inside one component of an unshipped model. `ADR-DRAFT-edge-vs-absolute-quality.md`
Ruling 3.4(3): "the proposition 'our model does not beat consensus' has never been
tested with a model."

WHAT IT MEASURES. Spearman rank correlation with realised season fantasy points,
per position, walk-forward, busts retained at zero, universe frozen pre-season,
against all four `CLAUDE.md` §6.5 baselines including BOTH crowds (market ADP and
expert consensus) per the founder's ruling of 2026-07-31.

HOLDOUT. 2025 is sealed and is never read. `CLAUDE.md` §6.3, founder's ruling
2026-07-31: the holdout does not open until `fable` has run, and `fable` has not
run. An ambiguous result is reported as ambiguous, not as needing the holdout.
"""

from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import adp_baseline as adp     # noqa: E402
from experiments.bottomup.components import ecr_baseline as ecr     # noqa: E402
from experiments.bottomup.components import pos_eval as E           # noqa: E402
from experiments.bottomup.components.pos_data import build_panel     # noqa: E402

CONFIG_PATH = _REPO / "experiments" / "bottomup" / "ranking_versions" / "v1.json"
OUT = _REPO / "experiments" / "bottomup" / "results"
HOLDOUT_SEASON = 2025


def load_config() -> Dict:
    raw = CONFIG_PATH.read_bytes()
    cfg = json.loads(raw)
    cfg["_sha256"] = hashlib.sha256(raw).hexdigest()
    return cfg


# --------------------------------------------------------------- v1 assembly
def v1_scores(d: pd.DataFrame, rank_col: str) -> np.ndarray:
    """v1's ordering on one (season, position, panel) block.

    RANK-SPACE ASSEMBLY. Start from the panel's own consensus ordering
    (`rank_col`, lower = better). Rookies -- players with no prior NFL season in
    the panel -- stay pinned at exactly their consensus slot. The remaining slots
    are filled by the veterans re-ordered by the component model's `proj_points`.

    So on rookie rows v1 IS the crowd it is being compared against, contributing
    zero differential information in either direction, which is precisely the
    honest position: rookie draft capital is an already-eliminated edge channel
    and this model holds no opinion on rookies. Returns a score where higher =
    better, i.e. the negated final slot.
    """
    r = d[rank_col].to_numpy(dtype=float)
    order = np.argsort(r, kind="stable")            # consensus order, best first
    is_rookie = (d["entry"].to_numpy() == "rookie")[order]
    proj = d["proj_points"].to_numpy(dtype=float)[order]

    slots = np.arange(len(order), dtype=float)
    out_slot = np.empty(len(order), dtype=float)
    out_slot[is_rookie] = slots[is_rookie]           # rookies pinned to consensus
    vet_slots = slots[~is_rookie]
    vet_idx = np.argsort(-np.nan_to_num(proj[~is_rookie], nan=-1e18), kind="stable")
    filled = np.empty(int((~is_rookie).sum()), dtype=float)
    filled[vet_idx] = vet_slots
    out_slot[~is_rookie] = filled

    score = np.empty(len(d), dtype=float)
    score[order] = -out_slot
    return score


def tier_heuristic(d: pd.DataFrame) -> np.ndarray:
    """§6.5 baseline #4 -- a simple positional-tier heuristic, deliberately crude.

    Tier by prior-season positional finish on `pts_1` (1-5 / 6-12 / 13-24 /
    25-48 / 49+ / no prior season), ties broken by prior-season games played.
    """
    pts1 = d["pts_1"].fillna(0.0).to_numpy(dtype=float)
    had_prior = d["pts_1"].notna().to_numpy() & (pts1 > 0)
    finish = pd.Series(-pts1).rank(method="first").to_numpy()
    tier = np.full(len(d), 6.0)
    for cut, t in [(48, 5.0), (24, 4.0), (12, 3.0), (5, 2.0)]:
        tier[had_prior & (finish <= cut)] = t
    tier[had_prior & (finish <= 5)] = 1.0
    games1 = d["games_1"].fillna(0.0).to_numpy(dtype=float) if "games_1" in d else np.zeros(len(d))
    return -(100.0 * tier) + games1


def ranker_columns(d: pd.DataFrame, panel: str) -> Dict[str, np.ndarray]:
    """Every ranker on one block, all oriented higher = better."""
    rank_col = "ffc_pos_rank" if panel == "M" else "ecr_pos_rank"
    cols: Dict[str, np.ndarray] = {
        "v1": v1_scores(d, rank_col),
        "b3_prior_points": d["pts_1"].fillna(0.0).to_numpy(dtype=float),
        "b4_tier_heuristic": tier_heuristic(d),
        "b3w_wavg_ppg": (d["ppg_w"].fillna(0.0) * d["gshare_w"].fillna(0.0)
                         ).to_numpy(dtype=float),
    }
    cols["b1_market_adp"] = -d["ffc_pos_rank"].to_numpy(dtype=float)
    cols["b2_expert_ecr"] = -d["ecr_pos_rank"].to_numpy(dtype=float)
    return cols


# ------------------------------------------------------------------ metrics
def block_metrics(d: pd.DataFrame, panel: str, position: str, season: int,
                  k: int) -> Dict:
    act = d["points"].to_numpy(dtype=float)
    row = {"panel": panel, "position": position, "season": season, "n": len(d),
           "n_rookie": int((d["entry"] == "rookie").sum()),
           "n_zero_game": int((d["games"] == 0).sum()),
           "mean_actual": float(np.mean(act)), "k": k}
    for name, pred in ranker_columns(d, panel).items():
        # a ranker that cannot score EVERY row of the block is not comparable on
        # that block. NaN, never a silently-scored subset -- scoring a subset
        # would change the universe per ranker, which is survivorship by the
        # back door.
        if (~np.isfinite(pred)).any() or len(d) < 5:
            row[f"rho_{name}"] = np.nan
            continue
        row[f"rho_{name}"] = E.spearman(pred, act)
        row[f"top_{name}"] = E.top_k_capture(pred, act, k)
        row[f"pts_top_{name}"] = E.mean_actual_of_top_k(pred, act, k)
    return row


def boot_diff(m: pd.DataFrame, a: str, b: str, reps: int, seed: int):
    """Paired difference a - b, resampling SEASONS. Returns mean, lo, hi, n, p."""
    if a not in m.columns or b not in m.columns:
        return np.nan, np.nan, np.nan, 0, np.nan
    sub = m[[a, b]].dropna()
    diffs = (sub[a] - sub[b]).to_numpy(dtype=float)
    n = len(diffs)
    if n == 0:
        return np.nan, np.nan, np.nan, 0, np.nan
    rng = np.random.default_rng(seed)
    boot = np.array([np.mean(rng.choice(diffs, size=n, replace=True))
                     for _ in range(reps)])
    p = 2.0 * min(float((boot <= 0).mean()), float((boot >= 0).mean()))
    return (float(diffs.mean()), float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)), n, min(1.0, max(p, 1.0 / reps)))


def bh(pvals: List[float], q: float) -> List[bool]:
    idx = np.argsort(pvals)
    m_ = len(pvals)
    keep = np.zeros(m_, dtype=bool)
    thresh = -1
    for rank, i in enumerate(idx, start=1):
        if pvals[i] <= q * rank / m_:
            thresh = rank
    if thresh > 0:
        keep[idx[:thresh]] = True
    return keep.tolist()


# --------------------------------------------------------------------- main
def build_frames(cfg: Dict, arm: str) -> pd.DataFrame:
    eng = cfg["engine"]
    panel = build_panel()

    def extra_ecr(target: int, position: str) -> Sequence[str]:
        b = ecr.load_ecr(target, position)
        return b["player_id"].dropna().tolist() if len(b) else []

    frames = []
    for pos in cfg["positions"]:
        wf = E.WalkForward(panel=panel, position=pos,
                           first_target=eng["first_target"],
                           last_target=eng["last_target"],
                           min_train_seasons=eng["min_train_seasons"],
                           avail_arm=arm,
                           calibrate_bonus=eng["calibrate_bonus"],
                           extra_universe_fn=extra_ecr)
        players, _ = wf.run()
        aud = pd.DataFrame(wf.audit)
        assert (aud.max_feature_cutoff < aud.season).all(), f"{pos} look-ahead (features)"
        assert (aud.max_outcome_season < aud.season).all(), f"{pos} look-ahead (outcomes)"
        assert (aud.n_outcome_reads_at_target == 0).all(), f"{pos} outcome read at target"
        assert players["season"].max() < HOLDOUT_SEASON, "HOLDOUT TOUCHED"

        # market rank: within-position rank of FFC ADP, per season
        players["ffc_pos_rank"] = players.groupby("season")["average_pick"].rank(
            method="first")
        # expert rank
        eb = pd.concat([ecr.load_ecr(s, pos) for s in
                        sorted(players["season"].unique())], ignore_index=True)
        players = players.merge(
            eb[["player_id", "season", "ecr_pos_rank"]],
            on=["player_id", "season"], how="left")
        players["position"] = pos
        frames.append(players)
    return pd.concat(frames, ignore_index=True)


def evaluate(full: pd.DataFrame, cfg: Dict, tag: str) -> pd.DataFrame:
    ev = cfg["evaluation"]
    rows = []
    for panel, rank_col, span in [("M", "ffc_pos_rank", ev["panels"]["M"]["seasons"]),
                                  ("E", "ecr_pos_rank", ev["panels"]["E"]["seasons"])]:
        for pos in cfg["positions"]:
            k = ev["topk"][pos]
            sub = full[(full.position == pos)
                       & full[rank_col].notna()
                       & full.season.between(span[0], span[1])]
            for season, g in sub.groupby("season"):
                if len(g) < 10:
                    continue
                rows.append(block_metrics(g, panel, pos, int(season), k))
    m = pd.DataFrame(rows)
    m.to_csv(OUT / f"ranking_v1_{tag}_season_metrics.csv", index=False)
    return m


def report(m: pd.DataFrame, cfg: Dict, tag: str) -> None:
    ev = cfg["evaluation"]
    reps, seed = ev["bootstrap"]["reps"], ev["bootstrap"]["seed"]
    q = ev["fdr"]["q"]
    mde_thresh = ev["mde_rule"]["threshold_rho"]
    parity = ev["decision_thresholds"]["parity_floor_rho"]

    print(f"\n{'='*90}\n{tag}  0. UNIVERSE -- frozen pre-season, busts retained\n{'='*90}")
    u = m.groupby(["panel", "position"]).agg(
        seasons=("season", "nunique"), n_mean=("n", "mean"),
        rookies=("n_rookie", "sum"), zero_game=("n_zero_game", "sum"),
        mean_actual=("mean_actual", "mean"))
    print(u.round(1).to_string())

    # ---- power first, before any v1 number is read -------------------------
    print(f"\n{'='*90}\n{tag}  1. POWER -- MDE from a BASELINE-vs-BASELINE contrast "
          f"(no v1 quantity)\n{'='*90}")
    mde: Dict = {}
    for panel, crowd in [("M", "b1_market_adp"), ("E", "b2_expert_ecr")]:
        for pos in cfg["positions"]:
            sub = m[(m.panel == panel) & (m.position == pos)]
            d, lo, hi, n, _p = boot_diff(sub, f"rho_{crowd}", "rho_b3w_wavg_ppg",
                                         reps, seed)
            hw = (hi - lo) / 2 if np.isfinite(hi) else np.nan
            mde[(panel, pos)] = hw
            verdict = ("CANNOT ANSWER" if (not np.isfinite(hw) or hw > mde_thresh)
                       else "resolvable")
            print(f"  panel {panel} {pos:3s}  {crowd:14s} - b3w:  {d:+.4f} "
                  f"[{lo:+.4f}, {hi:+.4f}]  n={n}  MDE={hw:.4f}  -> {verdict}")

    # ---- primary family ----------------------------------------------------
    print(f"\n{'='*90}\n{tag}  2. PRIMARY -- v1 vs BOTH CROWDS (§6.5), "
          f"family F-RANKING-V1, BH q={q}\n{'='*90}")
    fam = []
    for panel, crowd in [("M", "b1_market_adp"), ("E", "b2_expert_ecr")]:
        for pos in cfg["positions"]:
            sub = m[(m.panel == panel) & (m.position == pos)]
            d, lo, hi, n, p = boot_diff(sub, "rho_v1", f"rho_{crowd}", reps, seed)
            fam.append(dict(panel=panel, crowd=crowd, position=pos, delta=d,
                            lo=lo, hi=hi, n=n, p=p, mde=mde[(panel, pos)]))
    fam_df = pd.DataFrame(fam)
    ok = fam_df["p"].notna()
    fam_df["bh_reject"] = False
    if ok.any():
        fam_df.loc[ok, "bh_reject"] = bh(fam_df.loc[ok, "p"].tolist(), q)

    def verdict(r) -> str:
        if not np.isfinite(r["mde"]) or r["mde"] > mde_thresh:
            return "CANNOT ANSWER (design)"
        if r["lo"] > 0:
            return "BEATS"
        if r["hi"] < 0:
            return "LOSES"
        if r["delta"] < parity:
            return "LOSES (pt est below parity floor)"
        return "PARITY (not edge)"

    fam_df["verdict"] = fam_df.apply(verdict, axis=1)
    print(fam_df[["panel", "crowd", "position", "delta", "lo", "hi", "n", "p",
                  "mde", "bh_reject", "verdict"]].round(4).to_string(index=False))
    fam_df.to_csv(OUT / f"ranking_v1_{tag}_primary_family.csv", index=False)

    # ---- context baselines -------------------------------------------------
    print(f"\n{'='*90}\n{tag}  3. CONTEXT -- v1 vs the two non-crowd §6.5 baselines "
          f"(descriptive, NOT in the FDR family)\n{'='*90}")
    ctx = []
    for panel in ["M", "E"]:
        for pos in cfg["positions"]:
            sub = m[(m.panel == panel) & (m.position == pos)]
            for b in ["b3_prior_points", "b4_tier_heuristic", "b3w_wavg_ppg"]:
                d, lo, hi, n, p = boot_diff(sub, "rho_v1", f"rho_{b}", reps, seed)
                ctx.append(dict(panel=panel, position=pos, baseline=b, delta=d,
                                lo=lo, hi=hi, n=n))
    ctx_df = pd.DataFrame(ctx)
    print(ctx_df.round(4).to_string(index=False))
    ctx_df.to_csv(OUT / f"ranking_v1_{tag}_context.csv", index=False)

    # ---- levels ------------------------------------------------------------
    print(f"\n{'='*90}\n{tag}  4. LEVELS -- mean rho per ranker "
          f"(the comparison is the headline, not these)\n{'='*90}")
    lv = m.groupby(["panel", "position"])[
        [c for c in m.columns if c.startswith("rho_")]].mean()
    print(lv.round(3).to_string())

    # ---- decision-relevant -------------------------------------------------
    print(f"\n{'='*90}\n{tag}  5. DECISION-RELEVANT (§6.6) -- top-k capture and "
          f"mean actual points of the drafted top-k\n{'='*90}")
    for panel, crowd in [("M", "b1_market_adp"), ("E", "b2_expert_ecr")]:
        for pos in cfg["positions"]:
            sub = m[(m.panel == panel) & (m.position == pos)]
            for lab, a, b in [("top-k capture", "top_v1", f"top_{crowd}"),
                              ("pts of top-k", "pts_top_v1", f"pts_top_{crowd}")]:
                d, lo, hi, n, _p = boot_diff(sub, a, b, reps, seed)
                if np.isfinite(d):
                    print(f"  panel {panel} {pos:3s} {lab:14s} v1 - {crowd:14s}: "
                          f"{d:+.4f} [{lo:+.4f}, {hi:+.4f}]  n={n}")


def main() -> None:
    cfg = load_config()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"config {CONFIG_PATH.relative_to(_REPO)}  sha256={cfg['_sha256'][:16]}")
    print(f"precommit: {cfg['precommit']}")
    print(f"HOLDOUT {HOLDOUT_SEASON}: sealed, never read "
          f"(CLAUDE.md §6.3 -- does not open until fable has run)")

    for tag, arm in [("v1", cfg["engine"]["avail_arm"]),
                     ("v1b", cfg["secondary_versions"]["v1b"]["avail_arm"])]:
        print(f"\n\n{'#'*90}\n# {tag}  (availability arm {arm})\n{'#'*90}")
        full = build_frames(cfg, arm)
        full.to_csv(OUT / f"ranking_v1_{tag}_players.csv", index=False)
        m = evaluate(full, cfg, tag)
        report(m, cfg, tag)


if __name__ == "__main__":
    main()
