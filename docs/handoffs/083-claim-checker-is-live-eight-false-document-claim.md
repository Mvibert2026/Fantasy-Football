---
ID: 083
FROM: backend
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask

Three things, all small.

1. **Add `docs/pm/CHARTER.md` and `docs/pm/MEMORY.md` to `[scope].live_docs` in
   `docs/state-claims.toml`, and fix whatever the checker then reports.** They are the two
   richest sources of live factual claims in the repo and they are currently *not* scanned —
   not because they are trusted, but because they are outside the backend role's write
   boundary, and a checker that flags a document the failing session may not edit produces a
   red suite with no available fix. It is a one-line change. Run
   `python tools/state_claims.py` first to see what it finds before committing the change.

2. **Thread 078's open founder decision is already answered, and CURRENT-STATE.md was still
   saying otherwise until today.** 078 asks for "an actual FFC ToS answer, or accept the block
   indefinitely." The founder got that answer on 2026-07-29 ("we have no blocks from FFC, we
   can use as needed" — `docs/founder-requests/FR-023-ffc-is-unblocked-founder-confirmed-no-restrictio.md`,
   `docs/pm/MEMORY.md` §0/§4, `docs/research/source-audit-2026-07.md`). `docs/CURRENT-STATE.md`
   still described FFC as robots.txt-blocked in two places; both corrected in this session's
   commit. Pick-level ADP-velocity capture is now a *scoping and build* question, not a
   permission question. 078 should be re-scoped or closed on that basis — that is the PM's call,
   not mine, which is why this is an ask and not a done.

3. **Note the one thing the checker cannot verify**, because it is the failure that would have
   cost the most. "The automated ADP capture has been observed to succeed, so the local Windows
   Scheduled Task is now redundant" was false — no run with `event: schedule` had ever fired.
   Whether a GitHub Actions *schedule* has fired is not readable from a checkout, so no truth can
   be registered for it. The claim is registered truth-less: the checker will flag it if two live
   documents disagree about it, but **a single document asserting the false version alone still
   passes.** If the PM wants that closed properly it needs a step that queries the Actions API
   (`event` field, never the commit author — the author is `github-actions[bot]` for a manual
   dispatch too, and that is exactly how this was got wrong) and writes the result to a file the
   checker can read. That is a data-ops or PM task, not a backend one.

## Why

The project's measured blindness is that documents assert things the repo contradicts, and the
founder is the one who finds them — roughly 6:1 in his favour on 2026-07-29 and not improving.
`docs/pm/CHARTER.md` names the threshold for him stepping back as "zero interruptions plus a
detector that has caught planted faults." The detector now exists and has caught planted faults
(six fixtures, both directions) and eight live ones. Leaving the PM's own two files outside its
scope leaves the largest surface unguarded, and item 3 is the gap that a future session must not
mistake for coverage.

## Done looks like

1. `docs/state-claims.toml` `live_docs` contains both PM files and
   `python tools/state_claims.py` exits 0.
2. Thread 078 re-scoped or closed with a stated reason.
3. A yes/no on whether the Actions-schedule check is wanted, and if yes, which role owns it.
