# 2026-07-29 — librarian: backlog triage + Fable still-live pass

**Role:** librarian. Read-only analysis session; no code changed, no thread STATUS changed (not my
role for any of them). Two documents written, both for the founder, plus this log.

## What was asked

Two founder questions, verbatim: (1) "do we have other things on our lists or bugs to clean up... can
we start knocking them out?" and (2) "is there relevant stuff left on Fable's last recommendations
(we've changed a lot since it ran)."

## What was done

**Task A.** Read all 47 open threads in `docs/handoffs/` in full, against `docs/pm/MEMORY.md`,
`docs/CURRENT-STATE.md`, and `docs/status/2026-07-29-pm-cloud-migration-and-deploy.md`. Sorted each
into DONE ALREADY / STILL LIVE / OBSOLETE / BLOCKED. Spot-checked two claims directly in the repo
rather than trusting a session narrative: whether ADP fields actually render on any frontend screen
(grepped `frontend/ui` for `adp_source`/`adp_as_of_date` — zero matches, so **no**, despite a status
log saying ADP is "now on the board"), and whether `data/export/strategies.json` is still stale
(**yes** — `contract_version: 1.7.0` on disk against a live contract of `1.14.0`). Both surfaced as
real, cheap bugs and are called out first in the output, ahead of the full 47-thread sort.

Output: `docs/backlog-triage-2026-07-29.md`. Two real bugs, ~19 STILL LIVE items (summarized, several
already substantially done with one piece remaining), ~10 BLOCKED (mostly the shared screenshot-pane
limitation and the design-fidelity pause), 5 DONE-ALREADY-but-never-closed threads, zero OBSOLETE
(nothing found with a cleanly falsified premise — the closest candidates were already corrected in
place by later replies on the same thread rather than left to rot).

**Task B.** Read all 18 files in `docs/reviews/` in full (fable-* review docs plus the
`ACTION-PLAN-2026-08.md` consolidation). Extracted what still applies given today's changes (cloud
migration, FFC unblocked and half-PPR ADP now daily, ADP reached the board data layer, the app live
on the internet, one-command DB rebuild, ESPN-league deferral reversed per FR-027). Spot-checked two
things directly: whether the thread-ID allocator fix Fable recommended was actually built (yes,
`docs/pm-outbox/` and `NEW-*.md` handling exist in `tools/handoffs.py`) and whether λ (the one
measured model parameter) reaches the shipped recommendation card (per Fable's own G-A session, no —
confirmed nothing since claims otherwise).

Output: `docs/fable-still-live-2026-07-29.md`. Eight still-live items, four dead (their premises
were falsified by today's work — notably the FFC/ADP data-source gap Fable worried about no longer
exists), two items flagged as *more* urgent now than when Fable wrote them (the model's need-math
being hardcoded to the Westwood league specifically, now a direct blocker for the founder's new
generic-tier request; and the ticket/decision-numbering collision problem, which recurred three more
times today in forms the shipped fix doesn't cover).

## Contradictions flagged, not resolved

- A session status log claims ADP is "now on the board." Verified false by direct grep. Not fixed
  here — flagged in the triage doc per this role's standing instruction to report, not silently
  correct, another session's narrative.
- `docs/decisions.md`'s live ADR-054 (FFC ingester) and `docs/CURRENT-STATE.md`'s note that an
  unmerged branch also claims ADR-054 will collide the moment that branch merges. Already known to
  the PM (per `docs/pm/MEMORY.md`); restated in the triage doc rather than acted on.

## What I did not reach

Every open thread and every review file was read in full — nothing was skipped for time. Given the
token budget, the two output documents report what the threads/reviews themselves say rather than
independently re-verifying every code claim inside them; only the handful of claims cheap to check
and central to a DONE/STILL-LIVE/OBSOLETE call were spot-checked directly (see above).

## Handoffs opened

None. No new gap was found that warranted a fresh thread — the two real bugs (ADP display, stale
`strategies.json`) are already covered by existing open threads (082, 042) named in the triage doc.

## Files

- `/home/user/Fantasy-Football/docs/backlog-triage-2026-07-29.md`
- `/home/user/Fantasy-Football/docs/fable-still-live-2026-07-29.md`
- `/home/user/Fantasy-Football/docs/status/2026-07-29-librarian-triage.md` (this file)

## Same-day correction: BLOCKED bucket re-tested

The founder flagged that this same document's original BLOCKED bucket had carried the
screenshot-compositing limitation forward from earlier sessions without re-testing it against
today's environment — a document asserting something nobody re-checked, this project's recorded
failure mode, happening again in a document I wrote hours earlier the same day.

Went back through every thread in the BLOCKED bucket and re-read each one's own reply chain rather
than trusting the bucket label. Result: **027, 028, 029, 041** were each blocked solely on the same
screenshot-compositing gap ("the Browser pane is not displayed, so the page is not compositing
frames") — verified by reading each thread's own text, not inferred. That gap is fixed today per
`docs/frontend-cloud-runbook.md` (real Chromium via `executablePath`,
`frontend/e2e/cloud-board-screenshot.mjs`, dated captures in `frontend/e2e/artifacts/`). Moved all
four to STILL LIVE with a note that the remaining work is running the capture and attaching it, not
re-building anything.

Checked the rest of the BLOCKED bucket too, not just the ones that looked suspicious: 003, 006, 007,
012, 030, 031, 035, 050 are blocked on a deliberate, on-record design-fidelity pause (confirmed in
`docs/handoffs/035-frontend-catchup-runbook.md:77-81`, not a stale artifact). 076 and 081 are blocked
on a genuinely unresolved thread-ID/ADR-allocator design question, unrelated to screenshots, FFC, or
the database — confirmed by reading 081's latest reply, which explicitly says the problem is broader
than worktrees and still needs a design owner. Also checked for the other two classes the founder
named (FFC-blocked and database-unavailable-in-cloud-blocked items in the open BLOCKED bucket): none
found — FFC's unblocking was already reflected correctly in STILL LIVE (thread 054/055), and the one
thread about DB rebuild-in-cloud (080) was already closed, not sitting in BLOCKED.

Edited `docs/backlog-triage-2026-07-29.md` in place (correction note at top, BLOCKED section trimmed,
four items added to STILL LIVE with unblock reasons). No thread STATUS changed — that belongs to
`frontend`/`pm`, not this role.
