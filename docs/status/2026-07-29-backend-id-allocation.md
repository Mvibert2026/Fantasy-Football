# 2026-07-29 — backend — ID allocation widened + duplicate backstop (ADR-056)

## Task
Fix the recurring ID-collision defect (threads 043/049/053, ADR-048, thread 079/081, and three
more today: FR-020 double-allocated, ADR-054 colliding across `main` and an unmerged branch).
Root cause: every allocator scans the local working tree only, so a parallel branch is invisible.

## What shipped
1. **Widened allocation** (`tools/handoffs.py::next_free_id`, `::adr_next`,
   `tools/founder_requests.py::next_free_id`): now also scans `docs/handoffs/`,
   `docs/decisions.md`, `docs/adr-drafts/`, `docs/founder-requests/` as committed on every
   local + remote-tracking git ref, via `git for-each-ref` / `git ls-tree` / `git show`.
   Degrades loudly to working-tree-only scanning on any git failure (stderr warning, never
   silent).
2. **Hard duplicate-collision backstop** (the part that actually can't be bypassed):
   `find_adr_collisions()`, `find_thread_id_collisions()` in `tools/handoffs.py`;
   `find_fr_collisions()` in `tools/founder_requests.py`. Wired into `tools/handoffs.py check`
   (now hard-fails, not warns) and a new `tools/founder_requests.py check` subcommand.
   Detection only — nothing is renumbered automatically.

## What the new check found on this tree (real, not simulated)
`python3 tools/handoffs.py check` now fails with two genuine collisions in addition to the
pre-existing 078 issue:
- **ADR-054**: `main` = FFC ingester; `origin/backend/mock-calibration-kickers` = mock-draft
  batch ingestion snapshot work.
- **ADR-055**: `main` = kicker consensus-only export artifact; `origin/backend/mock-calibration-kickers`
  = `live_availability.py` LeagueConfig threading (my own ADR-055 from earlier this session).

Neither was renumbered, per explicit instruction. Whoever merges
`backend/mock-calibration-kickers` needs to renumber one side's ADRs before merge, or `check`
will keep failing after merge too.

`FR-020`'s reported double-allocation was not reproducible from the one branch fetched in this
session (`origin/backend/mock-calibration-kickers` has no second `FR-020-*.md`); the fix is
validated by fixture tests and will catch the real case once that branch is available here.

## Files touched
- `tools/handoffs.py` — `_git_ref_names`, `_git_tree_filenames`, `_git_show`, widened
  `next_free_id`/`adr_next`, `find_adr_collisions`, `find_thread_id_collisions`, wired into
  `cmd_check`.
- `tools/founder_requests.py` — same shape: `_git_ref_names`, `_git_tree_filenames`, widened
  `next_free_id`, `find_fr_collisions`, new `cmd_check` + `check` subcommand.
- `tests/test_handoffs.py` — 6 new tests (widening + both collision detectors, mocked git
  helpers so they don't depend on this session's actual fetched branches).
- `tests/test_founder_requests.py` — 3 new tests (same shape).
- `docs/decisions.md` — ADR-056.
- `docs/ideas-inbox.md` — the live collision finding, logged.

## Evidence
`python3 -m pytest tests/test_handoffs.py tests/test_founder_requests.py -q` → 27 passed, 1
pre-existing failure (`test_mailbox_health`; now failing for three true-positive reasons instead
of one — 078's missing reply, plus the two ADR collisions this session's own check newly
surfaces). Confirmed via `git stash` that `test_mailbox_health` was already red before this
session's changes (078 alone).

ADR number `056` from `python tools/handoffs.py adr next`; verified free (not present in
`docs/decisions.md`, `docs/adr-drafts/`, or the one fetched remote branch).

## Not done / out of scope
- Did not touch `src/`, `frontend/`, `docs/CURRENT-STATE.md` (file boundary).
- Did not renumber the live ADR-054/055 collision — detection only, as instructed.
- Did not widen the older unused `next_id()` back-compat helper in `tools/handoffs.py` — no
  current caller.
- Did not resolve thread 078's missing-reply issue — out of scope for this task.
