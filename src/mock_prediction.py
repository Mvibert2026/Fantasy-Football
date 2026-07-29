"""
Ingest-time prediction-snapshot computation for the BATCH mock-draft path
(ADR-054), closing the gap CURRENT-STATE flagged: `mock_picks.predicted_top`/
`predicted_p` existed but were populated ONLY when the source JSON happened
to supply them -- nothing computed them at ingest time, so a logged mock
carried no board-survival prediction to validate the availability model
against.

WHICH MODEL PRODUCES THE SNAPSHOT -- evidence, not a guess (per this
session's instruction not to trust mock_lab_store.py's docstring claim
uncritically). Read directly:

  - `live_availability.py` (ADR-045) is fully parameterized (p0, positions,
    gap are all function arguments, nothing about a specific slot or league
    is hardcoded in the hazard math itself) -- so the HAZARD MODEL's re-
    weighting step could in principle run for any slot/config.
  - But the hazard model needs a prep-mode marginal P0 to re-weight, and P0
    is NOT produced on demand: `run_availability.py` generates it via a
    Monte-Carlo simulation (`availability.simulate_availability`, thousands
    of simulated drafts) that writes a CSV file per league config
    (`_out_paths`), keyed to that config's own hardcoded `user_draft_slot`
    (see `league_config.LeagueConfig.user_draft_slot` and
    `draft_sim.DraftEngine`). There is no function anywhere in this codebase
    that returns a P0 for an arbitrary (config, slot, as-of-date) triple on
    demand -- it is a batch script producing a dated artifact, not a callable
    prediction source. Confirmed by reading `run_availability.py` end to end,
    not by trusting `mock_lab_store.py`'s docstring, which happens to be
    correct here but was verified independently.
  - Building a general-purpose on-demand P0 source is real modelling work
    (a fresh Monte-Carlo run per historical mock, potentially per pick) and
    is explicitly out of scope for this session (mock_lab_store.py's own
    "Follow-up needed" note says the same).

CONCLUSION: ingest-time snapshots use the same D-3 model-free baseline
`mock_lab_store.predict_next_pick` already uses for live logging
(`MODEL_VERSION = "adp_rank_exp_v1"`), imported and reused here rather than
re-derived, so batch and live mocks stay comparable under one model_version
pin. When a general-purpose hazard-model P0 source exists, this module is
the one place that needs to change.

LOOK-AHEAD BIAS (CLAUDE.md SS6.1). A pick's prediction must be built from
the board snapshot that was ACTUALLY ON FILE before that mock's
`drafted_at` date -- never the current/latest board, which for a backfilled
mock would silently use rankings information that did not exist yet.
`historical_board_ranks_as_of` reuses `freshness.historical_snapshot_date`
(the existing as_of_date infrastructure, not a parallel invention) to find
the most recent snapshot <= drafted_at; if none exists, that is an honest,
surfaced gap -- the mock is marked prediction-incomplete, never silently
filled from the live board.
"""

from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional, Tuple

import freshness as fr
import identity as idn
import mock_lab_store as mls

# The two sources make_board.py itself distinguishes: the live, format-aware
# 2026 pull (SOURCE) and the older multi-season mirror (TRAINING_SOURCE),
# which is the only source with history for seasons before 2026. Tried in
# this order so a 2026 mock prefers the format-aware source and an older/
# historical mock (e.g. the real 2025 draft) still finds a match.
_CANDIDATE_SOURCES = ("fantasypros_csv_2026draft", "fantasypros_ecr")

PREDICTION_MODEL_VERSION = mls.MODEL_VERSION  # reused, not duplicated


def historical_board_ranks_as_of(
    conn: sqlite3.Connection,
    season: int,
    on_or_before: str,
    sources: Tuple[str, ...] = _CANDIDATE_SOURCES,
) -> Tuple[Optional[str], Optional[str], Dict[str, int]]:
    """Find the most recent rankings snapshot <= `on_or_before` for `season`,
    trying `sources` in order, and return it as {mfl_id: consensus_adp_rank}.

    Returns (source_used, snapshot_date_used, ranks). (None, None, {}) if no
    candidate source has ANY snapshot on or before `on_or_before` for this
    season -- an honest gap, never a fallback to a later/current snapshot.

    `rankings.player_id` is a gsis_id, not the `mfl_id` mock_picks keys on
    (identity.py: mfl_id is the hub, gsis is a spoke) -- resolved per-row via
    `identity.resolve`. A gsis id with no mfl_id mapping is dropped from the
    ranks dict (not guessed), same discipline `ingest_mock_drafts.py` already
    applies to name resolution.
    """
    for source in sources:
        try:
            snapshot_date = fr.historical_snapshot_date(conn, season, source, on_or_before)
        except sqlite3.OperationalError:
            # No `rankings` table at all in this connection (e.g. a minimal
            # test fixture, or a DB that predates the rankings ingester) --
            # treated the same as "no snapshot found", never a hard crash of
            # the whole ingest path over a table that legitimately isn't
            # there yet.
            snapshot_date = None
        if snapshot_date is None:
            continue
        rows = conn.execute(
            "SELECT player_id, adp_rank FROM rankings "
            "WHERE source = ? AND season = ? AND as_of_date = ? AND adp_rank IS NOT NULL",
            (source, season, snapshot_date),
        ).fetchall()
        ranks: Dict[str, int] = {}
        for gsis_id, adp_rank in rows:
            mfl_id = idn.resolve(conn, "gsis", gsis_id)
            if mfl_id is not None:
                ranks[mfl_id] = int(adp_rank)
        # A snapshot date was found for this source -- stop here even if
        # every row in it failed identity resolution (surfaced as an empty
        # ranks dict, not silently papered over by trying the next source,
        # which could be a DIFFERENT snapshot date and reintroduce
        # look-ahead risk in the caller's mental model of "the snapshot used").
        return source, snapshot_date, ranks
    return None, None, {}


def compute_pick_predictions(
    conn: sqlite3.Connection,
    ordered_mfl_ids: List[Optional[str]],
    season: int,
    drafted_at: str,
) -> Tuple[Optional[str], Optional[str], List[Optional[dict]]]:
    """Replay one mock's picks (in `overall_pick` order) through the D-3
    baseline, board state at each pick built ONLY from picks preceding it --
    the same rule `mock_lab_store.replay_predictions` follows, restated here
    because this is the batch path replaying from a completed file rather
    than a live log.

    `ordered_mfl_ids[i]` is the resolved mfl_id for pick i+1, or None if that
    pick could not be resolved (quarantined). A None anywhere in the
    sequence means the undrafted pool from that point on cannot be trusted
    (we do not know which player actually left the pool), so this function
    refuses to compute predictions at all past that point and the caller
    must treat the whole mock as prediction-incomplete -- see
    `ingest_mock_drafts.calibration_usable`.

    Returns (source_used, snapshot_date_used, [prediction_dict_or_None, ...]),
    one entry per input pick, same length and order as `ordered_mfl_ids`.
    """
    source, snapshot_date, ranks = historical_board_ranks_as_of(conn, season, drafted_at)
    if snapshot_date is None or not ranks:
        return source, snapshot_date, [None for _ in ordered_mfl_ids]
    if any(m is None for m in ordered_mfl_ids):
        # An unresolved pick breaks the undrafted-pool bookkeeping from that
        # point forward -- refuse rather than silently mis-track the pool.
        return source, snapshot_date, [None for _ in ordered_mfl_ids]

    out: List[Optional[dict]] = []
    drafted: set = set()
    for mfl_id in ordered_mfl_ids:
        available = {pid: r for pid, r in ranks.items() if pid not in drafted}
        pred = mls.predict_next_pick(available)
        out.append({
            "predicted_top": pred.predicted_top,
            "predicted_p": pred.predicted_p,
            "predicted_top5": pred.predicted_top5,
            "model_version": mls.MODEL_VERSION,
            "board_source": source,
            "board_as_of_date": snapshot_date,
        })
        drafted.add(mfl_id)
    return source, snapshot_date, out
