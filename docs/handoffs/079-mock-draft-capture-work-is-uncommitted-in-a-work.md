---
ID: 079
FROM: pm
TO: backend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask

The 2026-07-29 overnight integration run was told to merge four branches. Three existed. The
fourth — "mock draft capture" — **is not a branch and has never been committed.** Its work is
sitting as eleven uncommitted files in a worktree:

`.claude/worktrees/backend-mock-calibration` (branch `backend/mock-calibration-kickers`)

```
 M docs/CURRENT-STATE.md
 M docs/decisions.md
 M docs/status.md
 M src/export_contract.py
 M src/freshness.py
 M src/ingest_mock_drafts.py
 M tests/test_rosters_export.py
?? src/mock_prediction.py
?? tests/test_kickers_export.py
?? tests/test_mock_calibration_snapshot.py
?? tests/test_mock_prediction.py
```

The branch itself points at `f1d51d0`, which is already an ancestor of `main` — zero commits
ahead. Last file write was 2026-07-28 23:25 local; `main` took its next commit at 23:46, so the
session that produced this ended, or stopped, without committing.

**The integration run deliberately did not commit or merge it.** Reasons in
`docs/status/2026-07-29-integration.md`. Nothing was lost: the files are untouched where they lie.

Whoever picks this up needs to answer, in this order:

1. **Is it finished?** No commit, no test evidence, and no handoff reply declares it done. If a
   session was interrupted mid-edit, some of these files may be half-written.
2. **Does the suite pass in that worktree?** Copy `data/nfl.db` into the worktree first or roughly
   21 tests fail for reasons unrelated to the work — this is a known, recorded trap.
3. **Does `tests/test_kickers_export.py` still have a reason to exist?**
   `docs/fable-mandate-M-2026-07-29.md` records a founder constraint dated 2026-07-29: *"Kickers:
   consensus-only list, excluded from the combined board. The model need not represent them."* and
   *"No kicker"* in the Westwood roster shape. That may or may not invalidate the kicker export
   work. **Confirm with the founder before deleting anything** — this thread is not authority to
   discard it.
4. **`docs/status.md` is modified in that worktree, and `docs/status.md` is now frozen.** The
   sharding branch landed on `main` in `5901b6b`. That edit must be replayed as a new file under
   `docs/status/` instead, or it will conflict.

## Why

The work is invisible to everything: not on a branch, not in a thread until now, not in any index.
A worktree that nobody remembers gets deleted eventually, and this one contains four new source and
test files that exist nowhere else in the repo. The cost of leaving it undeclared is losing it
silently; the cost of merging it blind is landing a half-finished export contract change on `main`.

## Done looks like

Either a commit hash on a branch merged into `main` with a test count, or an explicit reply on this
thread saying the work is superseded/abandoned and the worktree can be removed — naming who decided
that. "No action taken, because X" closes this thread; silence does not.
