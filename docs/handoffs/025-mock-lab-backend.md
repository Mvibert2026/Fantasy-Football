---
ID: 025
FROM: pm
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: Mock Lab UI, mock collection, calibration validation
---

## Reply — backend, 2026-07-27

Read thread 040's AMENDMENT first, as instructed. It supersedes this thread's own "immutable,
write-once prediction" premise (see amendment for the reasoning) -- built accordingly, not as
originally specced.

**Built:** `src/mock_lab_store.py`, new tables `mocklab_drafts`/`mocklab_picks`. Separate from the
existing batch `mock_drafts`/`mock_picks` (`ingest_mock_drafts.py`) -- that path stays file-based,
after-the-fact ingestion of a completed mock; this is the pick-at-a-time LIVE logging path (create
→ append → undo → close, survives a dropped connection) this thread actually asked for.

- **Create/append/undo/close**, pick-at-a-time, per item 1.
- **Predictions**: DERIVED, not stored -- `predict_next_pick`/`replay_predictions`, pure function
  of board state at pick N, guarded by a `model_version` pin at creation. `replay_predictions`
  raises `ModelVersionMismatch` and refuses outright once the live `MODEL_VERSION` has moved past
  what a mock was pinned to. This satisfies the amendment's corrected requirement ("reproducible
  under the model that made the claim"), not this thread's original "write-once" text.
- **Brier scoring + calibration bucketing**, per item 3 -- `brier_score`, `calibration_buckets`,
  the latter skipping (and reporting the count of) mocks whose pinned version no longer matches
  current, rather than erroring or silently pooling.

**Gap, stated rather than hidden**: the prediction function shipped is ADR-D's D-3 model-free
baseline (`adp_rank_exp_v1`, unfitted rank-exponential decay over frozen board rank), not the
reviewed hazard model (`live_availability.py`). Wiring the real hazard model needs a general-purpose
prep-mode Monte-Carlo marginal for arbitrary slots that does not exist yet (today it's only computed
for the founder's primary league's own pick sequence) -- that's real modelling work, flagged in
ADR-046, not done this session. The version-pin mechanism means this is a safe thing to defer: when
that follow-up lands, `MODEL_VERSION` bumps and every mock logged under the baseline stays correctly
frozen at its own pinned version rather than getting silently regraded.

**Also out of scope, on purpose**: ADR-D's dwell/entry-mode/blind-arm instrumentation (thread 034)
is frontend entry-surface + strategist statistical design, not storage. This store's schema doesn't
preclude adding those columns to `mocklab_picks` later.

**Tests written first**: `tests/test_mock_lab_store.py`, 20 tests, covering slot validation,
duplicate-mock/duplicate-pick rejection, closed-mock rejection, undo-truncates-not-voids,
undo-then-reentry pick-number reuse, absence of any undo counter (the retracted design), the
model-version-mismatch refusal and its converse (permitted when unchanged), Brier bounds plus a
zero-Brier degenerate case, and calibration-bucket skip-counting. All 20 pass in isolation
(`pytest tests/test_mock_lab_store.py`) -- full suite not re-run this session per instruction, to
avoid DB contention with concurrent agents.

Commit: see session commit for `src/mock_lab_store.py` + `tests/test_mock_lab_store.py` +
`docs/decisions.md` (ADR-046). Full detail in ADR-046, `docs/decisions.md`.

No export-contract change -- no export artifact exists yet for Mock Lab data, so no version bump
and no thread to frontend this session. That follows whenever the UI/export wiring is built.

## Ask
Build the Mock Lab backend. It does not exist at all — `/api/mocks`, prediction storage, and Brier
scoring are all listed as unbuilt in the confirmed gap list.

Needed:
1. **Endpoints to create, append picks to, and close a mock draft.** Pick-at-a-time append, not
   bulk-only — a user logging live enters one pick at a time and the connection may drop.
2. **Prediction storage, written at the moment the prediction is made.** Before each pick, store what
   the model predicted: survival probability per available player at the relevant horizon. Stored
   immutably, timestamped, never recomputed afterwards.
3. **Brier scoring and calibration bucketing** over stored predictions versus outcomes, per mock and
   aggregate across mocks.

Coordinate with thread 002 — per-pick draft state must be captured by the same schema. Do not design
two overlapping structures.

## Why this is the highest-priority thread on the board

The product's central claim is calibrated availability. Validating it needs ~30 logged mocks. There
is **1**, and there is currently **nowhere to log the other 29** — no endpoint, no storage, no
scoring. Design is speccing the UI right now, and it will arrive with nothing to talk to.

Five weeks to the draft. The chain is: thread 002 (per-pick state) → this (storage and scoring) →
Mock Lab UI → the founder actually running mocks. Every day this is not built is a day of mock
collection that cannot happen, and mocks cannot be collected retroactively.

## The immutability constraint — non-negotiable

A prediction is written once and never updated. Not corrected, not recomputed with a better model,
not backfilled. If the model improves mid-collection, old predictions stay as they were and the new
model starts a fresh comparison series.

The reason is that calibration measures what the model *actually claimed at the time*. Recomputing
predictions with hindsight produces a calibration curve that is guaranteed to look good and means
nothing at all. Enforce it at the storage layer — an update path that does not exist cannot be used
by accident.

## Done looks like
Endpoints working, an append-only prediction store with a test proving predictions cannot be updated,
Brier and calibration-bucket computation with tests, and a thread to `frontend` describing the
contract. Commit hash and test count.
