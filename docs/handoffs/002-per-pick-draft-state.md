---
ID: 002
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: 007 (mock collection, not yet opened)
---

## Ask

Add per-pick draft-state capture to the mock-draft schema, using the non-destructive
`ALTER TABLE ADD COLUMN` pattern established by ADR-043's `drafter_type`.

You own the shape decision — `deferred.md` names two candidates:
(a) drafted-counts-per-team at each pick, or (b) the raw ordered pick list with team attribution.
Pick one, justify it in an ADR, and state explicitly whether existing logged mock data survives
the migration.

## Why

This is a sequencing trap, and it is the reason this thread outranks the mock collection it blocks.

`live_availability.py` ships `delta = 0.10` as an explicitly unvalidated prior. The binding,
pre-registered rule is that if the need+run model does not beat marginal-only on Brier across ≥30
conforming mocks, `delta` goes to zero. Validating the run term `R(p)` requires the draft state at
**every** pick, because `obs(p)` and `exp(p)` are computed over a trailing 10-pick window.

The current `mock_drafts` / `mock_picks` tables store only the final pick sequence. So if mock
collection starts before this lands, you collect 30 mocks that **cannot test the thing they were
collected to test**, and you cannot go back and re-derive per-pick state from a final ordering
once the drafts are over.

`deferred.md` already calls this "cheap to add now and unrecoverable later." It is blocked on a
decision, not on a technical obstacle.

## Done looks like

- Migration applied, ADR written, existing mock data preserved (or explicitly stated as not)
- Tests covering the new column
- One line appended to `docs/CURRENT-STATE.md` confirming mock collection is now unblocked
- Reply with commit hash + test count + the shape you chose and why
