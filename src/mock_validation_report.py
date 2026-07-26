"""
Mock draft validation report, implementing mock_validation_protocol.md's
Level 1, Level 2, Tertiary (ADR-042/043).

PREDICTIONS COME FROM THE SHIPPED data/availability_2026.csv, not a fresh
simulation, for Levels 1-2 -- that CSV already contains `player_available`
probabilities per (player, pick, sigma) from the last run_availability.py
pass, and reusing it is what a report checking "did the shipped model's
predictions hold up" should compare against. Tertiary (dispersion) DOES run a
fresh simulation, at reduced n_sims, because the shipped CSV stores only
percentile SUMMARIES of the best-available distribution, not the raw samples
needed for an exact SD.

DEPLETION PICKS are the primary league's own first 7 user picks
(`ds.user_pick_numbers()[:7]`) -- which happen to equal the protocol's
literal [3, 18, 23, 38, 43, 58, 63], computed rather than hardcoded so this
does not silently go stale if the league config changes.

BOT-SEAT GATE (ADR-043): `mock_drafts.bot_seat_status` is 'unknown' (no
drafter_type data supplied for that mock -- INCLUDED here with a caveat, not
silently excluded, since excluding all of them would make the report
permanently report zero usable mocks), 'conforms' (checked, <=3 bot seats),
or 'excluded_too_many_bots' (checked, >3 -- HARD EXCLUDED here, same
treatment as a format-mismatch failure).
"""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

import draft_sim as ds

AVAIL_CSV = Path(__file__).resolve().parent.parent / "data" / "availability_2026.csv"
DEFAULT_SIGMA = 10.0
BUCKET_EDGES = (0.0, 0.4, 0.75, 1.0)  # protocol SS2: 3 buckets, not 5
DISPERSION_BAND = (0.5, 2.0)  # protocol SS5 criterion 4: [0.5x, 2.0x] of implied SD


def depletion_picks() -> List[int]:
    return ds.user_pick_numbers()[:7]


def _load_predicted_available(csv_path: Path = AVAIL_CSV, sigma: float = DEFAULT_SIGMA):
    """{player: {pick: predicted_survival_prob}} at the given sigma, from the
    shipped CSV. Returns ({}, {}) if the file does not exist yet."""
    by_player: Dict[str, Dict[int, float]] = {}
    positions: Dict[str, str] = {}
    if not csv_path.exists():
        return by_player, positions
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["record_type"] != "player_available":
                continue
            if abs(float(row["sigma"]) - sigma) > 1e-9:
                continue
            by_player.setdefault(row["player"], {})[int(row["pick"])] = float(row["value"])
            positions[row["player"]] = row["position"]
    return by_player, positions


def conforming_mock_ids(conn: sqlite3.Connection, league_config_id: str = "primary") -> List[str]:
    """format_conforms=1 AND bot_seat_status != 'excluded_too_many_bots' --
    both are protocol HARD gates (SS4). 'unknown' bot_seat_status is INCLUDED
    (see module docstring); its presence is surfaced via unknown_bot_seat_mock_ids().
    """
    rows = conn.execute(
        "SELECT mock_id FROM mock_drafts WHERE league_config_id=? AND format_conforms=1 "
        "AND bot_seat_status != 'excluded_too_many_bots'",
        (league_config_id,),
    ).fetchall()
    return [r[0] for r in rows]


def unknown_bot_seat_mock_ids(conn: sqlite3.Connection, league_config_id: str = "primary") -> List[str]:
    """Which conforming mocks have bot_seat_status='unknown' -- so a report
    caveat can say how many of the mocks it used could not actually be
    checked against the bot-seat gate, not just that the gate exists."""
    rows = conn.execute(
        "SELECT mock_id FROM mock_drafts WHERE league_config_id=? AND format_conforms=1 "
        "AND bot_seat_status='unknown'",
        (league_config_id,),
    ).fetchall()
    return [r[0] for r in rows]


def _picks_for_mock(conn: sqlite3.Connection, mock_id: str) -> List[Tuple[int, str]]:
    """[(overall_pick, mfl_id), ...] ordered, RESOLVED picks only -- a
    quarantined pick is neither present nor absent in a principled way, so it
    is excluded rather than guessed at."""
    return conn.execute(
        "SELECT overall_pick, mfl_id FROM mock_picks WHERE mock_id=? ORDER BY overall_pick",
        (mock_id,),
    ).fetchall()


@dataclass
class DepletionCell:
    pick: int
    position: str
    predicted_gone: Optional[float]
    observed_gone_mean: Optional[float]
    observed_gone_sd: Optional[float]
    n_mocks: int
    signed_error: Optional[float]


def level1_depletion_report(conn: sqlite3.Connection) -> Dict[str, object]:
    """Protocol SS3 Level 1: positional depletion counts at each of the first
    7 user picks, observed vs predicted, signed error."""
    mock_ids = conforming_mock_ids(conn)
    picks = depletion_picks()
    positions = list(ds.POSITIONS)

    # Predicted "N gone" per (position, pick) = mean best-available positional
    # rank minus 1, from the shipped best_available_dist summary.
    predicted: Dict[Tuple[str, int], float] = {}
    means: Dict[Tuple[str, int], float] = {}
    if AVAIL_CSV.exists():
        with AVAIL_CSV.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["record_type"] != "best_available_dist":
                    continue
                if abs(float(row["sigma"]) - DEFAULT_SIGMA) > 1e-9:
                    continue
                if not row["note"].startswith("mean of"):
                    continue
                means[(row["position"], int(row["pick"]))] = float(row["value"])
    for pos in positions:
        for pk in picks:
            m = means.get((pos, pk))
            if m is not None:
                predicted[(pos, pk)] = m - 1.0  # rank K available => K-1 already gone

    mfl_to_pos: Dict[str, str] = {}
    for mfl_id, pos in conn.execute(
        "SELECT DISTINCT mfl_id, position FROM players_canonical WHERE mfl_id IS NOT NULL"
    ).fetchall():
        mfl_to_pos[mfl_id] = pos

    cells: List[DepletionCell] = []
    for pos in positions:
        for pk in picks:
            observed_counts = []
            for mid in mock_ids:
                picks_in_mock = _picks_for_mock(conn, mid)
                n_gone = sum(
                    1 for opick, mfl_id in picks_in_mock
                    if opick < pk and mfl_to_pos.get(mfl_id) == pos
                )
                observed_counts.append(n_gone)
            pred = predicted.get((pos, pk))
            if observed_counts:
                mean_obs = sum(observed_counts) / len(observed_counts)
                if len(observed_counts) > 1:
                    var = sum((x - mean_obs) ** 2 for x in observed_counts) / (len(observed_counts) - 1)
                    sd_obs = var ** 0.5
                else:
                    sd_obs = None
            else:
                mean_obs = None
                sd_obs = None
            signed_error = (mean_obs - pred) if (mean_obs is not None and pred is not None) else None
            cells.append(DepletionCell(
                pick=pk, position=pos, predicted_gone=pred, observed_gone_mean=mean_obs,
                observed_gone_sd=sd_obs, n_mocks=len(observed_counts), signed_error=signed_error,
            ))

    return {
        "n_conforming_mocks": len(mock_ids),
        "depletion_picks": picks,
        "cells": cells,
        "power_note": _power_note(len(mock_ids)),
    }


@dataclass
class DispersionCell:
    pick: int
    position: str
    observed_sd: Optional[float]
    implied_sd_at_10: Optional[float]
    implied_sd_at_5: Optional[float]
    implied_sd_at_20: Optional[float]
    band_lo: Optional[float]
    band_hi: Optional[float]
    verdict: str  # "pass" | "fail" | "no_data" | "no_model_sd"


def implied_depletion_sd(
    conn: sqlite3.Connection, season: int = 2026, n_sims: int = 500, seed: int = 20260726,
) -> Dict[Tuple[float, str, int], float]:
    """The MODEL side of the dispersion test: {(sigma, position, pick): SD of
    simulated 'N gone'}, computed by actually re-running the opponent model at
    each of the three sigmas -- NOT approximated from the shipped CSV's
    percentile summary (SD from an IQR approximation would assume
    near-normality, which is exactly the kind of unverified assumption this
    project's guardrails warn against). n_sims is reduced from
    run_availability.py's production 3000-4000 (this is a diagnostic re-run,
    not a shipped artifact) -- 500 keeps three-sigma runtime to roughly the
    same order as one production availability pass.
    """
    import availability as av

    try:
        data = ds.load_season(conn, season)
    except sqlite3.OperationalError:
        # No `rankings` table (a DB without season data ingested, or a
        # lightweight test fixture) -- report no implied SD rather than
        # crashing the whole validation report over one section.
        return {}
    sources = av.default_ranking_sources(data)
    picks = depletion_picks()
    out: Dict[Tuple[float, str, int], float] = {}
    for sigma in ds.SIGMA_SWEEP:
        res = av.simulate_availability(data, sigma, n_sims, seed + int(sigma * 100), sources=sources)
        for pos in ds.POSITIONS:
            for pk in picks:
                vals = res.best_avail_dist.get(pos, {}).get(pk, [])
                vals = [v for v in vals if v < 999]  # 999 sentinel: position exhausted
                if len(vals) > 1:
                    out[(sigma, pos, pk)] = float(np.std(vals, ddof=1))
    return out


def level3_dispersion_report(
    conn: sqlite3.Connection, n_sims: int = 500,
) -> Dict[str, object]:
    """Protocol SS3 Tertiary / SS5 criterion 4: observed SD of positional
    depletion vs the sigma schedule's implied SD. 'The direct test of the
    sigma prior... the highest-value output of the whole exercise, because
    sigma scales every simulator result.'

    Runs REGARDLESS of mock count -- the model side (implied SD) is a
    property of the model alone and is always computable; only the observed
    side needs mock data. At 0 mocks this still reports the implied SD
    numbers, which is useful on its own (states what the model currently
    predicts dispersion to be) even with no observed comparison yet.
    """
    mock_ids = conforming_mock_ids(conn)
    picks = depletion_picks()
    depletion = level1_depletion_report(conn)  # reuse for observed_gone_sd
    observed_sd_by_cell = {
        (c.position, c.pick): c.observed_gone_sd for c in depletion["cells"]
    }
    implied = implied_depletion_sd(conn, n_sims=n_sims)

    cells: List[DispersionCell] = []
    for pos in ds.POSITIONS:
        for pk in picks:
            sd10 = implied.get((10.0, pos, pk))
            sd5 = implied.get((5.0, pos, pk))
            sd20 = implied.get((20.0, pos, pk))
            obs = observed_sd_by_cell.get((pos, pk))
            band_lo = sd10 * DISPERSION_BAND[0] if sd10 is not None else None
            band_hi = sd10 * DISPERSION_BAND[1] if sd10 is not None else None
            if sd10 is None:
                verdict = "no_model_sd"
            elif obs is None:
                verdict = "no_data"
            else:
                verdict = "pass" if band_lo <= obs <= band_hi else "fail"
            cells.append(DispersionCell(
                pick=pk, position=pos, observed_sd=obs, implied_sd_at_10=sd10,
                implied_sd_at_5=sd5, implied_sd_at_20=sd20, band_lo=band_lo, band_hi=band_hi,
                verdict=verdict,
            ))

    n_fail = sum(1 for c in cells if c.verdict == "fail")
    n_checked = sum(1 for c in cells if c.verdict in ("pass", "fail"))
    return {
        "n_conforming_mocks": len(mock_ids),
        "n_sims_per_sigma": n_sims,
        "cells": cells,
        "n_checked": n_checked,
        "n_fail": n_fail,
        "criterion_4_status": (
            "NOT_EVALUATED_NO_MOCKS" if n_checked == 0 else
            ("FAIL" if n_fail > 0 else "PASS")
        ),
        "power_note": _power_note(len(mock_ids)),
    }


def _power_note(n: int) -> str:
    if n == 0:
        return (
            "0 conforming mocks logged. No comparison is possible -- this is not a null "
            "result, it is the absence of any measurement. Do not read any number in this "
            "report as evidence of calibration or miscalibration."
        )
    if n < 10:
        return (
            f"{n} conforming mock(s) logged. Per mock_validation_protocol.md SS2, ~10 mocks "
            f"catches only gross miscalibration; ~30 is needed to detect a one-player bias "
            f"at pick 18, which is roughly the decision threshold. Treat every number below "
            f"as a rough, unreliable early read, not a conclusion."
        )
    if n < 30:
        return (
            f"{n} conforming mock(s) logged -- above the ~10-mock floor for detecting gross "
            f"miscalibration, but below the ~30-mock point the protocol calls decision-"
            f"useful. Treat direction as informative, magnitude as uncertain."
        )
    return f"{n} conforming mock(s) logged -- at or above the protocol's 30-mock decision-useful threshold."


@dataclass
class CalibrationBucket:
    lo: float
    hi: float
    n_pairs: int
    mean_predicted: Optional[float]
    mean_observed: Optional[float]


def level2_calibration_report(conn: sqlite3.Connection) -> Dict[str, object]:
    """Protocol SS3 Level 2 / SS2: per-player survival calibration, 3 buckets
    (not 5 -- with ~40 decision-relevant players, 5 buckets is 8 players per
    bin, which the protocol calls noise). Reports bucket means, not a fitted
    curve -- "there is not enough resolution for a shape" (protocol SS2).
    """
    mock_ids = conforming_mock_ids(conn)
    picks = depletion_picks()
    predicted_avail, _positions = _load_predicted_available()

    mfl_to_name: Dict[str, str] = {}
    for mfl_id, name in conn.execute(
        "SELECT DISTINCT mfl_id, display_name FROM players_canonical WHERE mfl_id IS NOT NULL"
    ).fetchall():
        mfl_to_name[mfl_id] = name

    pairs: List[Tuple[float, float]] = []  # (predicted, observed) per (player, pick)
    if mock_ids and predicted_avail:
        mocks_picks = {mid: _picks_for_mock(conn, mid) for mid in mock_ids}
        for player, per_pick in predicted_avail.items():
            for pk, pred_p in per_pick.items():
                if pk not in picks:
                    continue
                observed = []
                for mid in mock_ids:
                    taken_by = {mfl for opick, mfl in mocks_picks[mid] if opick < pk}
                    # match by NAME against the CSV (predictions are keyed by
                    # player name, mock_picks by mfl_id) -- resolve via
                    # players_canonical the same normalized way ingestion did.
                    taken_names = {mfl_to_name.get(mfl) for mfl in taken_by}
                    observed.append(0.0 if player in taken_names else 1.0)
                if observed:
                    pairs.append((pred_p, sum(observed) / len(observed)))

    buckets = []
    for lo, hi in zip(BUCKET_EDGES[:-1], BUCKET_EDGES[1:]):
        in_bucket = [(p, o) for p, o in pairs if lo <= p < hi or (hi == 1.0 and p == 1.0)]
        if in_bucket:
            mean_pred = sum(p for p, _ in in_bucket) / len(in_bucket)
            mean_obs = sum(o for _, o in in_bucket) / len(in_bucket)
        else:
            mean_pred = None
            mean_obs = None
        buckets.append(CalibrationBucket(lo=lo, hi=hi, n_pairs=len(in_bucket),
                                          mean_predicted=mean_pred, mean_observed=mean_obs))

    return {
        "n_conforming_mocks": len(mock_ids),
        "n_player_pick_pairs": len(pairs),
        "buckets": buckets,
        "power_note": _power_note(len(mock_ids)) + (
            " Additionally: per the protocol's own ceiling argument (SS2), the board is fixed "
            "across mocks, so more mocks narrow the noise on each player's observed rate but "
            "add NO new independent calibration points -- effective N for this report is "
            "bounded by the number of distinct decision-relevant players (~40), not by "
            "player x mock. Level 2 is expected to stay underpowered at any feasible mock count."
        ),
    }


def _load_predicted_available_with_rank(csv_path: Path = AVAIL_CSV, sigma: float = DEFAULT_SIGMA):
    """{player: {pick: predicted_p}}, {player: consensus_rank} -- same source
    as _load_predicted_available, extended with consensus_rank (already a
    column in the shipped CSV) for the rank-logistic baseline's feature."""
    by_player: Dict[str, Dict[int, float]] = {}
    rank: Dict[str, float] = {}
    if not csv_path.exists():
        return by_player, rank
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["record_type"] != "player_available":
                continue
            if abs(float(row["sigma"]) - sigma) > 1e-9:
                continue
            by_player.setdefault(row["player"], {})[int(row["pick"])] = float(row["value"])
            if row["consensus_rank"]:
                rank[row["player"]] = float(row["consensus_rank"])
    return by_player, rank


def _survival_pairs(
    conn: sqlite3.Connection,
) -> List[Tuple[int, float, float, float]]:
    """[(pick, consensus_rank, observed_survived, predicted_p), ...] across
    every (decision-relevant player, depletion pick) cell and every
    conforming mock -- the shared dataset both the full model's Brier score
    and the rank-logistic baseline's fit and Brier score are computed on."""
    mock_ids = conforming_mock_ids(conn)
    picks = depletion_picks()
    predicted_avail, rank_by_player = _load_predicted_available_with_rank()
    if not mock_ids or not predicted_avail:
        return []

    mfl_to_name: Dict[str, str] = {}
    for mfl_id, name in conn.execute(
        "SELECT DISTINCT mfl_id, display_name FROM players_canonical WHERE mfl_id IS NOT NULL"
    ).fetchall():
        mfl_to_name[mfl_id] = name

    mocks_picks = {mid: _picks_for_mock(conn, mid) for mid in mock_ids}
    pairs: List[Tuple[int, float, float, float]] = []
    for player, per_pick in predicted_avail.items():
        rank = rank_by_player.get(player)
        if rank is None:
            continue
        for pk in picks:
            pred_p = per_pick.get(pk)
            if pred_p is None:
                continue
            observed = []
            for mid in mock_ids:
                taken_names = {mfl_to_name.get(mfl) for opick, mfl in mocks_picks[mid] if opick < pk}
                observed.append(0.0 if player in taken_names else 1.0)
            if observed:
                pairs.append((pk, rank, sum(observed) / len(observed), pred_p))
    return pairs


def _fit_rank_logistic(
    pairs: List[Tuple[int, float, float, float]],
) -> Optional[Tuple[float, float]]:
    """MLE fit of P(survive to pick N) = sigmoid(a + b*(N - rank)) on
    (pick, rank, observed) -- protocol SS1's baseline. 'Observed' here is
    each cell's ACROSS-MOCK survival RATE (0..1, not strictly 0/1, since a
    (player, pick) cell is already averaged over conforming mocks in
    _survival_pairs) -- fit by weighted log-likelihood treating each rate as
    a Bernoulli mean, the standard way to fit a binomial-family GLM to
    proportion data. Requires scipy (already a project dependency).

    NOT a train/test split: the baseline is fit on the SAME pairs its Brier
    score is then computed on, matching how backtest.py's own baseline arms
    are computed directly from the same season being scored (see
    backtest.py's BPA baseline). Reconsider if mock volume ever grows enough
    to support a genuine holdout split -- with a handful of mocks, splitting
    further would leave nothing to fit on.
    """
    if len(pairs) < 10:
        return None
    from scipy.optimize import minimize

    x = np.array([pk - rank for pk, rank, _obs, _pred in pairs])
    y = np.array([obs for _pk, _rank, obs, _pred in pairs])

    def neg_log_lik(params):
        a, b = params
        z = a + b * x
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        eps = 1e-9
        p = np.clip(p, eps, 1 - eps)
        return -np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))

    result = minimize(neg_log_lik, x0=np.array([0.0, 0.05]), method="BFGS")
    if not result.success:
        return None
    return float(result.x[0]), float(result.x[1])


def brier_vs_baseline_report(conn: sqlite3.Connection) -> Dict[str, object]:
    """Protocol SS1 / SS5 criterion 2 -- the actual pass/fail gate: 'If the
    full opponent model... does not beat [the rank-logistic baseline] on
    Brier score, the complexity is unjustified and should be stripped.'
    """
    mock_ids = conforming_mock_ids(conn)
    pairs = _survival_pairs(conn)
    fit = _fit_rank_logistic(pairs)

    brier_full = None
    brier_baseline = None
    baseline_params = None
    if pairs:
        brier_full = float(np.mean([(pred - obs) ** 2 for _pk, _rank, obs, pred in pairs]))
    if fit is not None:
        a, b = fit
        baseline_params = {"a": a, "b": b}
        preds = 1.0 / (1.0 + np.exp(-np.clip(a + b * np.array(
            [pk - rank for pk, rank, _obs, _pred in pairs]
        ), -30, 30)))
        obs_arr = np.array([obs for _pk, _rank, obs, _pred in pairs])
        brier_baseline = float(np.mean((preds - obs_arr) ** 2))

    if not pairs:
        verdict = "NOT_EVALUATED_NO_DATA"
    elif fit is None:
        verdict = "NOT_EVALUATED_INSUFFICIENT_DATA_FOR_BASELINE_FIT"
    elif brier_full < brier_baseline:
        verdict = "MODEL_BEATS_BASELINE"
    else:
        verdict = "FAIL_MODEL_DOES_NOT_BEAT_BASELINE"

    return {
        "n_conforming_mocks": len(mock_ids),
        "n_pairs": len(pairs),
        "brier_full_model": brier_full,
        "brier_baseline_logistic": brier_baseline,
        "baseline_params": baseline_params,
        "verdict": verdict,
        "power_note": _power_note(len(mock_ids)) + (
            " The baseline needs >=10 (player, pick) cells with mock coverage to fit at all; "
            "fewer than that and this test cannot run regardless of mock count."
        ),
    }


def render_report(conn: sqlite3.Connection) -> str:
    lvl1 = level1_depletion_report(conn)
    lvl2 = level2_calibration_report(conn)
    lvl3 = level3_dispersion_report(conn)
    brier = brier_vs_baseline_report(conn)
    unknown_bot = unknown_bot_seat_mock_ids(conn)
    lines = []
    A = lines.append
    A("=" * 78)
    A("MOCK DRAFT VALIDATION REPORT")
    A("=" * 78)
    A(f"Conforming mocks: {lvl1['n_conforming_mocks']}")
    A(lvl1["power_note"])
    if unknown_bot:
        A(f"CAVEAT: {len(unknown_bot)} of {lvl1['n_conforming_mocks']} conforming mock(s) have "
          f"bot_seat_status='unknown' (no drafter_type data supplied) -- the >3-bot-seats gate "
          f"could NOT be checked for them; they are included anyway rather than discarded "
          f"(ADR-043). If the room was bot-heavy, these numbers understate sigma.")
    A("")
    A("-" * 78)
    A("LEVEL 1 -- POSITIONAL DEPLETION (observed vs predicted 'N gone')")
    A("-" * 78)
    for cell in lvl1["cells"]:
        pred = f"{cell.predicted_gone:5.1f}" if cell.predicted_gone is not None else "  n/a"
        obs = f"{cell.observed_gone_mean:5.1f}" if cell.observed_gone_mean is not None else "  n/a"
        err = f"{cell.signed_error:+5.1f}" if cell.signed_error is not None else "  n/a"
        A(f"  pick {cell.pick:>3}  {cell.position:<3}  predicted={pred}  observed={obs}  "
          f"signed_error={err}  n_mocks={cell.n_mocks}")
    A("")
    A("-" * 78)
    A("LEVEL 2 -- PER-PLAYER SURVIVAL CALIBRATION (3 buckets)")
    A("-" * 78)
    A(lvl2["power_note"])
    for b in lvl2["buckets"]:
        mp = f"{b.mean_predicted:.3f}" if b.mean_predicted is not None else "n/a"
        mo = f"{b.mean_observed:.3f}" if b.mean_observed is not None else "n/a"
        A(f"  [{b.lo:.2f}, {b.hi:.2f})  n={b.n_pairs:>4}  mean_predicted={mp}  mean_observed={mo}")
    A("")
    A("-" * 78)
    A("TERTIARY -- DISPERSION: observed SD vs sigma-schedule-implied SD (the direct")
    A("test of the sigma prior; protocol calls this the highest-value output)")
    A("-" * 78)
    A(f"criterion_4_status: {lvl3['criterion_4_status']}  "
      f"({lvl3['n_fail']} of {lvl3['n_checked']} checked cells failed the "
      f"[0.5x, 2.0x] band)")
    for cell in lvl3["cells"]:
        obs = f"{cell.observed_sd:5.2f}" if cell.observed_sd is not None else "  n/a"
        implied10 = f"{cell.implied_sd_at_10:5.2f}" if cell.implied_sd_at_10 is not None else "  n/a"
        band = (f"[{cell.band_lo:5.2f},{cell.band_hi:5.2f}]"
                if cell.band_lo is not None else "        n/a")
        A(f"  pick {cell.pick:>3}  {cell.position:<3}  observed_sd={obs}  "
          f"implied_sd@10={implied10}  band={band}  {cell.verdict}")
    A("")
    A("-" * 78)
    A("BRIER SCORE -- full model vs. one-parameter rank-logistic baseline")
    A("(protocol SS1/SS5 criterion 2: the ACTUAL pass/fail gate)")
    A("-" * 78)
    bf = f"{brier['brier_full_model']:.4f}" if brier["brier_full_model"] is not None else "n/a"
    bb = (f"{brier['brier_baseline_logistic']:.4f}"
          if brier["brier_baseline_logistic"] is not None else "n/a")
    A(f"  brier_full_model={bf}  brier_baseline={bb}  verdict={brier['verdict']}")
    if brier["baseline_params"]:
        A(f"  baseline fit: a={brier['baseline_params']['a']:.4f} "
          f"b={brier['baseline_params']['b']:.4f}  (n_pairs={brier['n_pairs']})")
    A(brier["power_note"])
    return "\n".join(lines)


def main() -> None:
    import db as dbmod

    conn = dbmod.connect()
    try:
        import ingest_mock_drafts as imd

        imd.ensure_tables(conn)
        print(render_report(conn))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
