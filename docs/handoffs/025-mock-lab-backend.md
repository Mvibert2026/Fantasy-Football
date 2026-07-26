---
ID: 025
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: Mock Lab UI, mock collection, calibration validation
---

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
