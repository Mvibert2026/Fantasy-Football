---
ID: FR-020
STATUS: NEW
SOURCE: claude code session (cloud-path rehearsal)
RAISED: 2026-07-29
---

## Request
Clean-clone cloud rehearsal is the gate for moving off the local Windows box

Founder's own words:

> "Rehearse the cloud path. In a scratch directory outside the repo, do a clean clone from
> origin - nothing copied across, no data folder - then rebuild the database from scratch and
> run both test suites against it. [...] This is the gate for moving to cloud. If a clean clone
> cannot produce a working project, say exactly what is missing."

## Why it matters

Standing constraint, not a one-off task: the founder has named a concrete, testable condition
for the cloud migration rather than a judgement call. Anything that breaks a clean clone's path
to green is now a release blocker by the founder's own definition, and the rehearsal is
repeatable — it should be re-run after any change to `requirements.txt`, the ingest scripts, or
the rebuild order.

## Initial read

Rehearsal run 2026-07-29 (`docs/status/2026-07-29-cloud-path-rehearsal.md`). Verdict: the gate
**passes** — 641 backend + 202 frontend tests green from a clean clone in ~9 minutes, no
credentials — but only after four hand-fixes that a fresh machine would hit. Two are one-line
repo fixes (`pandas` missing from `requirements.txt`; no Python version declared, and the
pin needs >=3.12). Two are ordering/coverage gaps (`identity.py` exits non-zero on a fresh DB;
no loader for the committed ADP snapshot CSVs). None is architectural.

Sequencing: fix the two one-liners first — they are what actually stops a fresh machine dead.
`tools/state.py`'s hardcoded Windows interpreter blocks the mandated write-back workflow in
cloud and should go with them.
