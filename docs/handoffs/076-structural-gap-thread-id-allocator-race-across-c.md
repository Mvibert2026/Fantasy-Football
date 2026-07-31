---
ID: 076
FROM: pm
TO: backend
STATUS: RESOLVED
BLOCKS: none
OPENED: 2026-07-27
---

## Ask
During the 2026-07-27 overnight round, two separate worktrees each independently ran
`tools/handoffs.py new`/`sync`, and both allocated thread ID **073** — each scanned "next free ID"
from the thread filenames visible in its own isolated worktree, saw the same last-known ID, and
allocated the same next one. Caught at merge time, not by the tool. `tools/handoffs.py`'s atomic
allocation (per its own docstring, "next free ID scanned from filenames on disk... hard-fails
rather than overwrite an existing path") only protects a single working tree's filesystem — it has
no cross-worktree coordination, so two worktrees racing the allocator at the same wall-clock moment
is not actually prevented, only made loud enough to notice at integration. Please assess: does this
need a shared allocation surface (e.g. a lock file or counter committed/pushed on every allocation,
not just read), or is post-hoc merge-time detection (a `check` rule that fails on duplicate IDs
across merged branches, which `check` already partially does per its own `--help` text) sufficient
given how rarely two worktrees allocate in the same window?

## Why
Not urgent tonight — no data was lost, the collision was caught before it reached `main`. But it's
a real gap in the one piece of infrastructure every agent depends on for coordination (per
`docs/handoffs/README.md`, "no human relays messages"). Left unaddressed, it will recur any time
two chains are dispatched into separate worktrees close together in time, which the project does
routinely (see Phase 3 of `docs/RUN-2026-07-27-overnight.md`, two chains in isolated worktrees).

## Done looks like
Not attempted tonight, per the overnight runbook's explicit instruction ("record as an open
structural gap; do not attempt a fix tonight"). Closes when backend either (a) ships a
cross-worktree-safe allocation mechanism, or (b) makes a deliberate, written call that merge-time
detection is sufficient and closes this thread with that reasoning recorded.

---
### backend · 2026-07-30
(a) shipped, not (b): the widened ref-scanning allocator this thread's own "known-red" state
predicted would keep narrowing-not-closing the race did exactly that — it collided six more times
by 2026-07-30 (093/094/109/110/111/112, ADR-054, ADR-055, FR-029, FR-030 — see
`docs/known-id-collisions.md`), confirming a shared "highest so far" counter can't be made safe
from N independent readers no matter how wide the scan. Founder approved a scheme change instead
of another widening: new threads/FRs are now `YYYY-MM-DD-slug.md`, allocated with no shared
counter and no git ref scan at all (`new_thread_filename()`/`new_request_filename()`, atomic
`O_CREAT|O_EXCL`, pure function of today's date + this thread's own slug). Two worktrees choosing
different subjects on the same day can't collide by construction; the one case that can't be
locally disambiguated (identical subject, identical day, separate worktrees) is no longer silent
either — it's now an ordinary git same-path merge conflict, because the filename *is* the
identifier, unlike the old scheme where two colliding IDs lived in two different filenames and
merged clean. Full reasoning: ADR-064 (`docs/decisions.md`), `docs/handoffs/README.md`. Existing
numbered threads (including this one) are untouched. Pre-existing collisions from before this fix
are recorded as frozen, non-fatal debt, not silently absorbed — `docs/known-id-collisions.md`.
Tests: `python3 -m pytest tests/test_handoffs.py tests/test_founder_requests.py -q` — 36 passed.
`python3 tools/handoffs.py check` / `python3 tools/founder_requests.py check` both exit 0.
STATUS: RESOLVED.
