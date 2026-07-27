"""
Mock Lab live-logging store (thread 025), event-sourced per the thread 040
AMENDMENT (2026-07-27).

WHY THIS EXISTS. `ingest_mock_drafts.py` is file-based, batch, after-the-fact
ingestion of a completed mock's final pick sequence. Thread 025 asks for the
thing that does not exist yet: pick-at-a-time LIVE logging while a mock is in
progress (the connection may drop mid-mock), plus prediction storage and
Brier/calibration scoring. This module is that live store. It is deliberately
separate from `ingest_mock_drafts.py` / `mock_drafts` / `mock_picks` -- this
is a new capability, not a rework of the existing batch path, and the two are
expected to be reconciled (a closed mocklab draft exported into the batch
ingester's JSON shape) in a later session, not silently merged now.

THE ARCHITECTURE CHANGE THAT MATTERS -- read before touching this file.
Thread 025 originally specified predictions "written at the moment the
prediction is made... stored immutably... never recomputed." Thread 040's
AMENDMENT (docs/handoffs/040-multi-league-slot-and-undo.md) overturned that:
an availability prediction is a pure function of board state at pick N, so
replaying it after an undo with the SAME model version reproduces exactly
what would have been produced live -- that is not hindsight contamination.
So:

  - `mocklab_picks` is an append-only, truncatable LOG. It is the only
    source of truth. There is no `predicted_*` column on it and no
    `voided_by_undo` flag -- both belonged to the superseded design.
  - Predictions are DERIVED on demand by replaying the log through
    `predict_next_pick`, board state at each pick built from the picks
    that preceded it in the (possibly-truncated) log.
  - `mocklab_drafts.model_version` is PINNED at creation. Replay is
    refused if the module's current `MODEL_VERSION` has moved past the
    pinned value -- that comparison is the entire safeguard the amendment
    describes. It is not undo that is dangerous; it is grading an old
    mock's predictions under a model that did not exist when the mock was
    logged (hindsight improvement, "calibration gets better for free
    without the model getting better at anything").
  - Undo (`undo_to`) is a plain DELETE of log rows after a point, nothing
    more. No undo counter, no user-visible "this costs you N predictions"
    warning -- the amendment explicitly retracts that bookkeeping as
    solving a problem that does not exist in this case.

PREDICTION SOURCE -- STATED HONESTLY, NOT PAPERED OVER. The reviewed hazard
model (`live_availability.py`, ADR-045) predicts SURVIVAL TO A FUTURE PICK
given a prep-mode Monte-Carlo marginal (P0) that today is only computed for
the founder's own primary-league pick sequence
(`data/availability_2026.csv`). Thread 040 item 2 requires Mock Lab to accept
ANY slot with a derived pick sequence, which means P0 must exist for
arbitrary slots/configs too -- and building that general Monte-Carlo P0
source is real modelling work, not a wiring exercise, and is NOT done here.
Silently approximating it would be exactly the kind of guess CLAUDE.md
prohibits for a statistical constant.

What ships here instead is ADR-D's own model-free baseline, D-3:
`baseline_id = adp_rank_exp_v1` -- probability of being the next pick decays
by fixed, UNFITTED exponential in the player's frozen pre-draft consensus
board rank among the currently-undrafted pool. `DECAY_K` below is chosen by
fiat (ADR-D: "fixed by fiat and frozen ... never fitted"), not measured, and
is labelled as such -- it estimates zero parameters from mock data, so it
carries no false precision and needs no standard error. It is the same
quantity ADR-D specifies co-measuring alongside the real hazard model once
that model is wired for arbitrary slots; until then it is what this module
predicts, not a stand-in pretending to be the hazard model.

**Follow-up needed, logged rather than silently deferred**: wire the real
hazard model here once a general-purpose P0 source for arbitrary
slot/config exists. Until then `MODEL_VERSION == "adp_rank_exp_v1"` and
every mock created under it is validly comparable against every other --
the version pin exists precisely so that day's cutover doesn't
retroactively contaminate mocks logged before it.
"""

from __future__ import annotations

import math
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Bump this constant, and only this constant, when the prediction function
# changes in any way that alters its output. Mocks pin whatever value was
# current at creation; replay compares against the CURRENT value, not a
# stored copy of old logic.
MODEL_VERSION = "adp_rank_exp_v1"

# Fixed by fiat (ADR-D D-3). Not fitted, not measured -- an unfitted baseline
# has no free parameters to overfit, so no SE is owed for this number.
DECAY_K = 0.15

_CREATE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS mocklab_drafts (
        mock_id TEXT PRIMARY KEY,
        league_config_id TEXT NOT NULL,
        slot INTEGER NOT NULL,
        model_version TEXT NOT NULL,
        rng_seed INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        closed_at TEXT,
        status TEXT NOT NULL DEFAULT 'open'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mocklab_picks (
        mock_id TEXT NOT NULL REFERENCES mocklab_drafts(mock_id),
        pick_no INTEGER NOT NULL,
        mfl_id TEXT NOT NULL,
        team_slot INTEGER,
        entered_at TEXT NOT NULL,
        PRIMARY KEY (mock_id, pick_no)
    )
    """,
]


class MockLabError(Exception):
    pass


class MockNotFoundError(MockLabError):
    pass


class DuplicateMockError(MockLabError):
    pass


class InvalidSlotError(MockLabError):
    pass


class MockClosedError(MockLabError):
    pass


class DuplicatePickError(MockLabError):
    pass


class ModelVersionMismatch(MockLabError):
    """Raised when replay is attempted against a mock whose pinned
    model_version no longer matches the module's current MODEL_VERSION.
    This is the entire safeguard the thread 040 amendment describes -- do
    not add a bypass or an override flag."""


def ensure_tables(conn: sqlite3.Connection) -> None:
    for stmt in _CREATE_SQL:
        conn.execute(stmt)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_mock(row) -> dict:
    keys = ("mock_id", "league_config_id", "slot", "model_version", "rng_seed",
            "created_at", "closed_at", "status")
    return dict(zip(keys, row))


def get_mock(conn: sqlite3.Connection, mock_id: str) -> dict:
    ensure_tables(conn)
    row = conn.execute(
        "SELECT mock_id, league_config_id, slot, model_version, rng_seed, "
        "created_at, closed_at, status FROM mocklab_drafts WHERE mock_id=?",
        (mock_id,),
    ).fetchone()
    if row is None:
        raise MockNotFoundError(mock_id)
    return _row_to_mock(row)


def create_mock(
    conn: sqlite3.Connection,
    mock_id: str,
    league_config_id: str,
    slot: int,
    teams: Optional[int] = None,
    rng_seed: Optional[int] = None,
    model_version: Optional[str] = None,
) -> dict:
    """Thread 040 item 2: any slot is valid, not just the founder's own
    league slot -- `teams` is passed by the caller (from that league's
    config) purely to validate range, never assumed."""
    ensure_tables(conn)
    if teams is not None and not (1 <= slot <= teams):
        raise InvalidSlotError(f"slot {slot} outside [1, {teams}]")
    if slot < 1:
        raise InvalidSlotError(f"slot {slot} must be >= 1")
    existing = conn.execute(
        "SELECT 1 FROM mocklab_drafts WHERE mock_id=?", (mock_id,)
    ).fetchone()
    if existing is not None:
        raise DuplicateMockError(mock_id)

    seed = rng_seed if rng_seed is not None else int(time.time() * 1000) % (2 ** 31)
    version = model_version if model_version is not None else MODEL_VERSION
    now = _now()
    conn.execute(
        "INSERT INTO mocklab_drafts "
        "(mock_id, league_config_id, slot, model_version, rng_seed, created_at, "
        " closed_at, status) VALUES (?, ?, ?, ?, ?, ?, NULL, 'open')",
        (mock_id, league_config_id, slot, version, seed, now),
    )
    conn.commit()
    return get_mock(conn, mock_id)


def close_mock(conn: sqlite3.Connection, mock_id: str) -> None:
    mock = get_mock(conn, mock_id)
    if mock["status"] == "closed":
        return
    conn.execute(
        "UPDATE mocklab_drafts SET status='closed', closed_at=? WHERE mock_id=?",
        (_now(), mock_id),
    )
    conn.commit()


def reopen_mock(conn: sqlite3.Connection, mock_id: str) -> None:
    get_mock(conn, mock_id)  # raises MockNotFoundError if absent
    conn.execute(
        "UPDATE mocklab_drafts SET status='open', closed_at=NULL WHERE mock_id=?",
        (mock_id,),
    )
    conn.commit()


def list_picks(conn: sqlite3.Connection, mock_id: str) -> List[dict]:
    ensure_tables(conn)
    rows = conn.execute(
        "SELECT pick_no, mfl_id, team_slot, entered_at FROM mocklab_picks "
        "WHERE mock_id=? ORDER BY pick_no ASC",
        (mock_id,),
    ).fetchall()
    return [
        {"pick_no": r[0], "mfl_id": r[1], "team_slot": r[2], "entered_at": r[3]}
        for r in rows
    ]


def append_pick(
    conn: sqlite3.Connection,
    mock_id: str,
    mfl_id: str,
    team_slot: Optional[int] = None,
    entered_at: Optional[str] = None,
) -> int:
    """Pick-at-a-time append -- a user logging live enters one pick at a
    time and the connection may drop (thread 025's stated requirement).
    Idempotent it is NOT: re-appending the same player raises
    DuplicatePickError rather than silently no-opping, because a genuine
    duplicate pick in a real draft is impossible and almost always signals
    a double-submit that the caller must handle, not swallow."""
    mock = get_mock(conn, mock_id)
    if mock["status"] == "closed":
        raise MockClosedError(f"{mock_id} is closed; reopen_mock() first")

    already = conn.execute(
        "SELECT 1 FROM mocklab_picks WHERE mock_id=? AND mfl_id=?",
        (mock_id, mfl_id),
    ).fetchone()
    if already is not None:
        raise DuplicatePickError(f"{mfl_id} already drafted in {mock_id}")

    next_pick_no = conn.execute(
        "SELECT COALESCE(MAX(pick_no), 0) + 1 FROM mocklab_picks WHERE mock_id=?",
        (mock_id,),
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO mocklab_picks (mock_id, pick_no, mfl_id, team_slot, entered_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (mock_id, next_pick_no, mfl_id, team_slot, entered_at or _now()),
    )
    conn.commit()
    return next_pick_no


def undo_to(conn: sqlite3.Connection, mock_id: str, keep_through: int) -> None:
    """Truncate the log after `keep_through` and stop -- no replay is
    forced here, because callers may want to inspect state before deciding
    what (if anything) to recompute. `keep_through=0` empties the mock.
    Per the 040 amendment: this is a plain delete, not a void/mark
    operation, and nothing is counted or surfaced as a cost."""
    mock = get_mock(conn, mock_id)
    if mock["status"] == "closed":
        raise MockClosedError(f"{mock_id} is closed; reopen_mock() first")
    conn.execute(
        "DELETE FROM mocklab_picks WHERE mock_id=? AND pick_no > ?",
        (mock_id, keep_through),
    )
    conn.commit()


# --------------------------------------------------------------- prediction (derived, D-3 baseline)

@dataclass
class Prediction:
    predicted_top: Optional[str]
    predicted_p: float
    predicted_top5: List[str]
    all_probs: Dict[str, float] = field(default_factory=dict)
    baseline_id: str = MODEL_VERSION


def predict_next_pick(available_ranks: Dict[str, int], decay_k: float = DECAY_K) -> Prediction:
    """ADR-D D-3 model-free baseline: P(picked next) decays exponentially in
    frozen consensus board rank among currently-undrafted players. Zero
    parameters fitted to any mock data -- `decay_k` is fixed by fiat.
    `available_ranks`: mfl_id -> consensus_rank, UNDRAFTED players only; the
    caller is responsible for excluding already-picked ids (see
    `replay_predictions`, which does this from the log automatically)."""
    if not available_ranks:
        return Prediction(predicted_top=None, predicted_p=0.0, predicted_top5=[], all_probs={})

    weights = {pid: math.exp(-decay_k * (rank - 1)) for pid, rank in available_ranks.items()}
    total = sum(weights.values())
    probs = {pid: w / total for pid, w in weights.items()}
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    top5 = [pid for pid, _ in ranked[:5]]
    predicted_top, predicted_p = ranked[0]
    return Prediction(
        predicted_top=predicted_top,
        predicted_p=predicted_p,
        predicted_top5=top5,
        all_probs=probs,
    )


@dataclass
class ReplayedPick:
    pick_no: int
    actual_mfl_id: str
    prediction: Prediction
    hit: bool


def replay_predictions(
    conn: sqlite3.Connection, mock_id: str, board_ranks: Dict[str, int]
) -> List[ReplayedPick]:
    """Recompute predictions for every logged pick, board state at pick N
    built from picks 1..N-1 only (never later picks -- that would be the
    same look-ahead bug guardrails SS6.1 polices elsewhere). Refuses if the
    mock's pinned model_version no longer matches MODEL_VERSION."""
    mock = get_mock(conn, mock_id)
    if mock["model_version"] != MODEL_VERSION:
        raise ModelVersionMismatch(
            f"{mock_id} was pinned to model_version={mock['model_version']!r}, "
            f"current is {MODEL_VERSION!r}; replay refused"
        )

    picks = list_picks(conn, mock_id)
    out: List[ReplayedPick] = []
    drafted: set = set()
    for p in picks:
        available = {pid: r for pid, r in board_ranks.items() if pid not in drafted}
        prediction = predict_next_pick(available)
        out.append(ReplayedPick(
            pick_no=p["pick_no"],
            actual_mfl_id=p["mfl_id"],
            prediction=prediction,
            hit=(prediction.predicted_top == p["mfl_id"]),
        ))
        drafted.add(p["mfl_id"])
    return out


# --------------------------------------------------------------- scoring

def brier_score(conn: sqlite3.Connection, mock_id: str, board_ranks: Dict[str, int]) -> float:
    """Mean squared error of predicted_p against the hit indicator (was the
    model's top call actually taken), over every logged pick. Bounded
    [0, 1] since predicted_p in [0,1] and hit in {0,1}."""
    replay = replay_predictions(conn, mock_id, board_ranks)
    if not replay:
        return 0.0
    errors = [(r.prediction.predicted_p - (1.0 if r.hit else 0.0)) ** 2 for r in replay]
    return sum(errors) / len(errors)


def calibration_buckets(
    conn: sqlite3.Connection,
    mock_ids: List[str],
    board_ranks_by_mock: Dict[str, Dict[str, int]],
    edges=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
) -> dict:
    """Aggregate calibration across mocks: for each predicted_p bucket,
    observed hit rate vs. mean predicted p. Mocks whose pinned
    model_version no longer matches MODEL_VERSION are SKIPPED, not errored
    on and not silently pooled -- the skip count is returned so a caller
    can see coverage was reduced instead of discovering it later."""
    buckets = [
        {"lo": edges[i], "hi": edges[i + 1], "n": 0, "hits": 0, "sum_p": 0.0}
        for i in range(len(edges) - 1)
    ]
    n_scored = 0
    n_skipped = 0
    for mock_id in mock_ids:
        try:
            replay = replay_predictions(conn, mock_id, board_ranks_by_mock[mock_id])
        except ModelVersionMismatch:
            n_skipped += 1
            continue
        for r in replay:
            p = r.prediction.predicted_p
            for b in buckets:
                hi_inclusive = b["hi"] == edges[-1]
                if (p >= b["lo"] and p < b["hi"]) or (hi_inclusive and p == b["hi"]):
                    b["n"] += 1
                    b["sum_p"] += p
                    if r.hit:
                        b["hits"] += 1
                    break
            n_scored += 1

    for b in buckets:
        b["observed_rate"] = (b["hits"] / b["n"]) if b["n"] else None
        b["mean_predicted_p"] = (b["sum_p"] / b["n"]) if b["n"] else None

    return {
        "buckets": buckets,
        "n_scored": n_scored,
        "n_skipped_version_mismatch": n_skipped,
    }
