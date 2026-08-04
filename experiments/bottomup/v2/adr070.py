"""ADR-070 — the factor inclusion decision instrument. Pure functions, no DB.

Implements, from `docs/adr-drafts/ADR-070-factor-inclusion-decision-rule.md`:

  §4.1  matched per-cell null ensembles           (the runner is ensemble070.py;
                                                   this module consumes its draws)
  §4.3  Besag–Clifford sequential Monte Carlo p   — two-sided, hard floor
        2/(L+1), NO parametric tail of any kind
  §4.4  the verdict taxonomy, incl. the RE-SPECIFY / EXCLUDE (variance) split
  §4.4a calibrated sign-consistency C = W⁺ − W⁻, scored against the ensemble,
        never against a binomial — a REQUIRED CONDITION, never a second
        discovery route (it can only remove rejections)
  §4.5  BH on top, at the cumulative campaign M
  §4.6  the reporting fields every graded cell must carry
  §4.7  the derived per-season snap tolerance 6/(n³−n), replacing global 1e-9
  §4.8  the four-part provenance key, enforced by a raise — cross-universe or
        cross-span deltas are impossible to compute here, not discouraged

One resolution the ADR's §4.4 table leaves implicit, fixed here so it cannot be
chosen after seeing a result: a BH-robust cell that fails CONSISTENT is graded
FRAGILE when the effect is carried by one or two seasons (dropping the two most
favourable seasons flips or kills Δ̄); a BH-robust HARM that fails CONSISTENT and
is NOT so carried is EXCLUDE (variance). A BH-robust WIN that fails CONSISTENT
is FRAGILE either way — there is no other WIN category and INCLUDE requires
CONSISTENT.

Direction convention: every delta entering this module is CANONICAL — positive
means the arm is BETTER. Endpoints where lower is better (MAE) are multiplied by
−1 at ingestion by the caller, which records the raw sign alongside.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

Q_FDR = 0.10

#: campaign M as of 2026-08-02: 130 (through C1) + 88 (D1) + 12 (D1 Amendment 1)
#: = 230. Any new registered batch ADDS its m_b here; never shrink (§4.5).
M_CAMPAIGN_BASE = 230

#: sequential-test exceedance target (§4.3)
H_EXCEED = 20


def draws_needed(m_campaign: int, q: float = Q_FDR) -> int:
    """L = ceil(2M/q) − 1. At M=230, q=0.10 -> 4,599. The p floor 2/(L+1) then
    equals the BH rank-1 threshold q/M exactly, so a zero-exceedance cell is
    BH-reachable and nothing finer is purchasable at this M."""
    return int(math.ceil(2.0 * m_campaign / q)) - 1


# ------------------------------------------------------------------ §4.8 keys
class KeyMismatchError(RuntimeError):
    """Raised when asked to difference or pool cells whose provenance keys
    differ. CLAUDE.md §6.1 requires a layer that refuses; a warning is not one."""


VALID_UNIVERSES = ("m_panel_halfppr12", "m_panel_ppr12", "m_panel_nonppr12",
                   "full_veteran_roster")


@dataclass(frozen=True)
class ProvKey:
    """The four-part provenance key (§4.8). A number without one is UNLABELLED
    and not citable."""
    universe: str
    targets: str                  # "YYYY-YYYY" as REGISTERED for the run
    S: int                        # registered span length
    first_feature_season: int

    def __post_init__(self):
        if self.universe not in VALID_UNIVERSES:
            raise KeyMismatchError(f"unknown universe {self.universe!r}; "
                                   f"valid: {VALID_UNIVERSES}")

    def as_dict(self) -> Dict:
        return {"universe": self.universe, "targets": self.targets,
                "S": self.S, "first_feature_season": self.first_feature_season}


def assert_joinable(a: ProvKey, b: ProvKey, what: str = "cells") -> None:
    """An arm differences only against a control carrying an IDENTICAL key."""
    if a != b:
        raise KeyMismatchError(
            f"refusing to join {what} with different provenance keys:\n"
            f"  a = {a}\n  b = {b}\n"
            f"No cross-universe or cross-span delta may ever be computed "
            f"(ADR-070 §4.8 rule 1).")


# ------------------------------------------------------- §4.7 snap tolerance
def snap_tolerance(n_graded: int) -> float:
    """Half of Spearman's smallest attainable non-zero change on n players,
    12/(n³−n). Anything below it is definitionally arithmetic noise."""
    n = int(n_graded)
    if n < 3:
        return np.inf
    return 6.0 / (n ** 3 - n)


def snap_deltas(deltas: np.ndarray, n_graded: Sequence[int],
                continuous: bool = False) -> np.ndarray:
    """Per-season snap. For the discrete rank endpoint the tolerance is derived
    (§4.7); for a continuous endpoint (MAE) only float-representation noise is
    snapped."""
    d = np.array(deltas, dtype=float, copy=True)
    if continuous:
        d[np.abs(d) < 1e-12] = 0.0
        return d
    for i, n in enumerate(n_graded):
        if np.isfinite(d[i]) and abs(d[i]) < snap_tolerance(n):
            d[i] = 0.0
    return d


def tolerances(n_graded: Sequence[int], continuous: bool = False) -> np.ndarray:
    if continuous:
        return np.full(len(n_graded), 1e-12)
    return np.array([snap_tolerance(n) for n in n_graded], dtype=float)


# ------------------------------------------------ §4.3 sequential Monte Carlo
@dataclass
class SeqResult:
    p_one: float
    p_two: float
    p_floor: float
    n_draws_used: int
    n_exceed: int
    stop_reason: str              # "h_reached" | "L_exhausted" | "insufficient"
    direction: str                # "WIN" | "HARM" | "ZERO"


def bc_sequential_p(obs_delta_bar: float, draw_delta_bars: Sequence[float],
                    h: int = H_EXCEED, L: int = 4599) -> SeqResult:
    """Besag–Clifford (1991) sequential MC test on a deterministic draw order.

    `draw_delta_bars` are the ensemble Δ̄ values in registered order k=1..n
    (n ≤ L). Exceedance = at least as extreme as the observation in the observed
    direction (ties count — conservative). NO parametric tail: if the sequence
    is exhausted before h exceedances, p_one = (l+1)/(L+1); no p below 2/(L+1)
    may exist and none is ever extrapolated.

    If fewer draws than needed were supplied (neither h reached nor L
    exhausted), the result is `insufficient` and carries the p the evidence so
    far supports at its own resolution — the caller must either supply more
    draws or grade HYPOTHESIS at best (§5: there is no reduced-L inclusion).
    """
    floor = 2.0 / (L + 1)
    if not np.isfinite(obs_delta_bar):
        return SeqResult(np.nan, np.nan, floor, 0, 0, "insufficient", "ZERO")
    if obs_delta_bar == 0.0:
        return SeqResult(1.0, 1.0, floor, 0, 0, "h_reached", "ZERO")
    direction = "WIN" if obs_delta_bar > 0 else "HARM"
    count = 0
    n = 0
    for k, v in enumerate(draw_delta_bars, start=1):
        n = k
        if not np.isfinite(v):
            continue
        if (obs_delta_bar > 0 and v >= obs_delta_bar) or \
           (obs_delta_bar < 0 and v <= obs_delta_bar):
            count += 1
            if count >= h:
                p1 = count / k
                return SeqResult(p1, min(1.0, 2.0 * p1), floor, k, count,
                                 "h_reached", direction)
        if k >= L:
            break
    if n >= L:
        p1 = (count + 1) / (L + 1)
        return SeqResult(p1, min(1.0, 2.0 * p1), floor, n, count,
                         "L_exhausted", direction)
    # not enough draws yet: report at the resolution the draws support
    p1 = (count + 1) / (n + 1) if n else np.nan
    return SeqResult(p1, min(1.0, 2.0 * p1) if n else np.nan, floor, n, count,
                     "insufficient", direction)


# ------------------------------------------------------- §4.4a consistency C
@dataclass
class Consistency:
    w_plus: int
    w_minus: int
    c: int                        # oriented toward the claim direction
    c_q95_null: float
    consistent: bool
    binom_p_half: float           # descriptive only, never a decision input
    pi0_hat: float                # ensemble's own measured null sign prob
    zero_mass: float              # ensemble fraction of |Δ_s| <= tol


def _wpm(deltas: np.ndarray, tols: np.ndarray) -> Tuple[int, int]:
    ok = np.isfinite(deltas)
    wp = int(np.sum(deltas[ok] > tols[ok]))
    wm = int(np.sum(deltas[ok] < -tols[ok]))
    return wp, wm


def _binom_two_sided_half(k: int, n: int) -> float:
    """Exact two-sided binomial p at π=0.5 (descriptive honesty line, §4.4a)."""
    if n == 0:
        return np.nan
    probs = np.array([math.comb(n, i) for i in range(n + 1)], dtype=float) \
        / 2.0 ** n
    return float(min(1.0, probs[probs <= probs[k] + 1e-15].sum()))


def consistency(obs_deltas: np.ndarray, draw_deltas: np.ndarray,
                tols: np.ndarray, direction: str) -> Consistency:
    """C for the cell, calibrated against the SAME null ensemble (§4.4a).

    `draw_deltas` is (n_draws, S) per-season deltas per draw — which is why
    M-1(B) requires them stored, not summarised. CONSISTENT iff the cell's
    oriented C strictly exceeds the ensemble's q95 of oriented C. No binomial
    assumption anywhere in the decision path.
    """
    wp, wm = _wpm(obs_deltas, tols)
    c_obs = (wp - wm) if direction == "WIN" else (wm - wp)

    cs = []
    zero_ct = 0
    tot_ct = 0
    win_ct = 0
    for row in np.atleast_2d(draw_deltas):
        p, m = _wpm(np.asarray(row, dtype=float), tols)
        cs.append((p - m) if direction == "WIN" else (m - p))
        okr = np.isfinite(np.asarray(row, dtype=float))
        vals = np.asarray(row, dtype=float)[okr]
        t = tols[okr]
        zero_ct += int(np.sum(np.abs(vals) <= t))
        win_ct += int(np.sum(vals > t))
        tot_ct += int(okr.sum())
    cs_arr = np.array(cs, dtype=float)
    q95 = float(np.quantile(cs_arr, 0.95)) if len(cs_arr) else np.nan
    ok = np.isfinite(obs_deltas)
    n_signed = int(np.sum(np.abs(obs_deltas[ok]) > tols[ok]))
    k_dir = wp if direction == "WIN" else wm
    return Consistency(
        w_plus=wp, w_minus=wm, c=int(c_obs), c_q95_null=q95,
        consistent=bool(np.isfinite(q95) and c_obs > q95),
        binom_p_half=_binom_two_sided_half(k_dir, n_signed) if n_signed else np.nan,
        pi0_hat=(win_ct / tot_ct) if tot_ct else np.nan,
        zero_mass=(zero_ct / tot_ct) if tot_ct else np.nan)


# ----------------------------------------------------------- ensemble stats
def ensemble_stats(delta_bars: Sequence[float]) -> Dict[str, float]:
    """§4.6 item 2 — BOTH tails, always. C1 published the upper tail only,
    which left every HARM cell ungradeable against its own null."""
    v = np.asarray([x for x in delta_bars if np.isfinite(x)], dtype=float)
    if not len(v):
        return {k: np.nan for k in
                ("n_draws", "mean", "sd", "min", "q025", "q05", "q25",
                 "median", "q75", "q95", "q975", "max")}
    return {
        "n_draws": int(len(v)), "mean": float(v.mean()),
        "sd": float(v.std(ddof=1)) if len(v) > 1 else np.nan,
        "min": float(v.min()), "q025": float(np.quantile(v, 0.025)),
        "q05": float(np.quantile(v, 0.05)), "q25": float(np.quantile(v, 0.25)),
        "median": float(np.quantile(v, 0.5)), "q75": float(np.quantile(v, 0.75)),
        "q95": float(np.quantile(v, 0.95)), "q975": float(np.quantile(v, 0.975)),
        "max": float(v.max()),
    }


# ------------------------------------------------------------------ §4.5 BH
def bh_reject(pvals: Sequence[float], m_campaign: int,
              q: float = Q_FDR) -> np.ndarray:
    """This batch's p-values ranked among themselves against the CUMULATIVE
    campaign denominator — the existing convention (run_c1.grade), conservative
    by construction. BH, not BY, logged as an assumption in the ADR."""
    ps = np.asarray(pvals, dtype=float)
    ok = np.isfinite(ps)
    keep = np.zeros(len(ps), dtype=bool)
    if not ok.any():
        return keep
    idx = np.where(ok)[0]
    order = idx[np.argsort(ps[idx])]
    thresh = 0
    for rank, i in enumerate(order, start=1):
        if ps[i] <= q * rank / m_campaign:
            thresh = rank
    keep[order[:thresh]] = True
    return keep


# ------------------------------------------------------------- §4.4 verdicts
COVERAGE_FLOOR = 0.80


def carried_by_one_or_two(deltas: np.ndarray, direction: str) -> bool:
    """True when dropping the two seasons most favourable to the claim flips
    or zeroes the mean — the FRAGILE geometry."""
    d = np.asarray(deltas, dtype=float)
    d = d[np.isfinite(d)]
    if len(d) <= 2:
        return True
    sgn = 1.0 if direction == "WIN" else -1.0
    keep = np.sort(sgn * d)[:-2]          # drop the 2 most favourable
    return bool(keep.mean() <= 0.0)


def verdict(p_two: float, bh_robust: bool, direction: str, consistent: bool,
            voided: bool, coverage: float, stop_reason: str,
            deltas: Optional[np.ndarray] = None) -> str:
    """§4.4, resolved as documented in the module docstring. `C` is a required
    condition only — it can remove a rejection, never grant one."""
    if not np.isfinite(p_two):
        return "NO DATA"
    if np.isfinite(coverage) and coverage < COVERAGE_FLOOR:
        return "NO DATA"
    if direction == "ZERO":
        return "NULL (calibrated)"
    if stop_reason == "insufficient":
        # §5: no reduced-L inclusion, no parametric shortcut. And an ensemble
        # that did not run to its stopping rule cannot support a CALIBRATED
        # null either (§4.4's NULL row requires it) — the honest state is
        # "no complete ensemble", which is NO DATA.
        return "HYPOTHESIS" if p_two <= 0.05 else "NO DATA"
    if bh_robust:
        if direction == "WIN":
            if voided:
                return "WIN (VOID: control wins)"
            if consistent:
                return "INCLUDE"
            return "FRAGILE"
        # HARM
        if consistent:
            return "RE-SPECIFY"
        if deltas is not None and carried_by_one_or_two(deltas, direction):
            return "FRAGILE"
        return "EXCLUDE (variance)"
    if p_two <= 0.05:
        return "HYPOTHESIS"
    return "NULL (calibrated)"


# --------------------------------------------------------- §4.6 cell report
@dataclass
class CellReport:
    """Everything §4.6 requires a graded cell to carry. Assembled by the
    runner; this class exists so nothing can be silently dropped."""
    batch: str
    arm: str
    position: str
    key: ProvKey
    s_pos: int                          # realised per-position span
    endpoint: str                       # "rho_points" | "mae_games" | ...
    better: str                         # "higher" | "lower" (raw orientation)
    delta_bar: float                    # canonical (positive = better)
    deltas: List[float]                 # per-season, canonical, snapped
    seasons: List[int]
    n_graded: List[int]
    seq: SeqResult
    cons: Optional[Consistency]
    stats: Dict[str, float]
    coverage: float
    voided: bool
    verdict: str
    bh_robust: bool
    pearson_delta_bar: float            # §4.6 item 5, diagnostic only
    descriptive_spread: Tuple[float, float]  # old bootstrap CI, relabelled
    seed_scheme: str
    h: int
    L: int

    def flat(self) -> Dict:
        d = {"batch": self.batch, "arm": self.arm, "position": self.position,
             **self.key.as_dict(), "S_pos": self.s_pos,
             "endpoint": self.endpoint, "better": self.better,
             "delta_bar": self.delta_bar,
             "deltas": ";".join(f"{x:+.6f}" for x in self.deltas),
             "seasons": ";".join(str(s) for s in self.seasons),
             "n_graded": ";".join(str(n) for n in self.n_graded),
             "p": self.seq.p_two, "p_one": self.seq.p_one,
             "p_floor": self.seq.p_floor, "n_draws_used": self.seq.n_draws_used,
             "n_exceed": self.seq.n_exceed, "stop_reason": self.seq.stop_reason,
             "direction": self.seq.direction,
             "coverage": self.coverage, "voided": self.voided,
             "verdict": self.verdict, "bh_robust": self.bh_robust,
             "pearson_delta_bar": self.pearson_delta_bar,
             "descriptive_spread_lo": self.descriptive_spread[0],
             "descriptive_spread_hi": self.descriptive_spread[1],
             "seed_scheme": self.seed_scheme, "h": self.h, "L": self.L}
        for k, v in self.stats.items():
            d[f"null_{k}"] = v
        if self.cons is not None:
            d.update({"w_plus": self.cons.w_plus, "w_minus": self.cons.w_minus,
                      "C": self.cons.c, "C_q95_null": self.cons.c_q95_null,
                      "consistent": self.cons.consistent,
                      "binom_p_half": self.cons.binom_p_half,
                      "pi0_hat": self.cons.pi0_hat,
                      "zero_mass": self.cons.zero_mass})
        return d


def descriptive_spread(deltas: np.ndarray, reps: int = 4000,
                       seed: int = 20260801) -> Tuple[float, float]:
    """The season-block bootstrap, retained ONLY as `descriptive_spread`
    (§4.6 item 6). It is not a decision instrument for this endpoint and must
    never again appear as lo/hi next to a verdict."""
    d = np.asarray(deltas, dtype=float)
    d = d[np.isfinite(d)]
    if not len(d):
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    boot = np.array([np.mean(rng.choice(d, size=len(d), replace=True))
                     for _ in range(reps)])
    return (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))
