"""
Mock draft validation report (ADR-042), implementing
mock_validation_protocol.md SS3 (Level 1, Level 2) against logged mock_picks.

SCOPE CUT, NAMED. This implements Level 1 (positional depletion) and Level 2
(per-player calibration, 3 buckets). The protocol's Tertiary section
(observed SD of depletion vs the sigma schedule's implied SD -- "the highest-
value output of the whole exercise" per the protocol itself) and SS1's
Brier-score-vs-rank-logistic-baseline test are NOT implemented here. Both are
real, well-specified pieces of remaining work, cut for time -- see
docs/status.md's handoff. Do not read their absence as "not needed."

PREDICTIONS COME FROM THE SHIPPED data/availability_2026.csv, not a fresh
simulation. That CSV already contains `player_available` probabilities per
(player, pick, sigma) from the last run_availability.py pass -- reusing it is
faster and, more importantly, is what a report checking "did the shipped
model's predictions hold up" should compare against, not a re-simulation that
could differ from what was actually shipped.

DEPLETION PICKS are the primary league's own first 7 user picks
(`ds.user_pick_numbers()[:7]`) -- which happen to equal the protocol's
literal [3, 18, 23, 38, 43, 58, 63], computed rather than hardcoded so this
does not silently go stale if the league config changes.

BOT-SEAT GATE: cannot be enforced (ingest_mock_drafts.py's docstring explains
why -- the schema carries no drafter_type). Every mock currently has
bot_seat_status='unknown'. This report INCLUDES unknown-status mocks (the
alternative -- excluding all of them -- would make the report permanently
report zero usable mocks forever, which defeats the point) but states this
loudly in the caveats, not as a footnote.
"""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import draft_sim as ds

AVAIL_CSV = Path(__file__).resolve().parent.parent / "data" / "availability_2026.csv"
DEFAULT_SIGMA = 10.0
BUCKET_EDGES = (0.0, 0.4, 0.75, 1.0)  # protocol SS2: 3 buckets, not 5


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
    """format_conforms=1 only -- the protocol's HARD gate. bot_seat_status is
    NOT filtered on (see module docstring)."""
    rows = conn.execute(
        "SELECT mock_id FROM mock_drafts WHERE league_config_id=? AND format_conforms=1",
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


def render_report(conn: sqlite3.Connection) -> str:
    lvl1 = level1_depletion_report(conn)
    lvl2 = level2_calibration_report(conn)
    lines = []
    A = lines.append
    A("=" * 78)
    A("MOCK DRAFT VALIDATION REPORT")
    A("=" * 78)
    A(f"Conforming mocks: {lvl1['n_conforming_mocks']}")
    A(lvl1["power_note"])
    A("")
    A("NOT COMPUTED IN THIS REPORT (scope cut, see mock_validation_report.py docstring):")
    A("  - Tertiary: observed dispersion (SD) vs the sigma schedule's implied SD")
    A("  - Brier score vs. the one-parameter rank-logistic baseline (protocol SS1)")
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
