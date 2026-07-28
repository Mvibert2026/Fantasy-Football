---
ID: 077
FROM: data-ops
TO: backend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-27
---

## Ask
Chain 1 step 1.1 (RUN-2026-07-27-overnight.md, Phase 3) is done. Summary for backend to pick
up on step 1.2 in the same worktree (`.claude/worktrees/phase3-chain1`, branch
`backend/phase3-chain1-adp-and-exports`, pushed):

1. **Root cause of the missed 2026-07-27 snapshot**: not investigable directly — no scheduled-task
   config or transcript existed anywhere (platform scheduler and cron both checked, both empty)
   for the run that failed. `src/ingest_mfl_adp.py` (ADR-035) itself was already correct: plain
   `urllib.request`, honest User-Agent, 429 backoff, once-per-UTC-day cache. No other ADP source
   (FFC/Yahoo/ESPN/FantasyPros-ADP-specific) was ever live per `docs/deferred.md` — confirmed MFL
   is the only in-scope mechanism, so no new scraper was needed.
2. **Backfill**: ran `src/ingest_mfl_adp.py --force` against the worktree's `data/nfl.db`. Landed
   246 rows, `adp_source='mfl_proxy'`, `retrieved_at` 2026-07-27, `total_drafts_in_sample=47`
   (thin-sample CAUTION printed by the script itself, as designed).
3. **Scheduled task registered** (Windows Scheduled Task, current-user scope, no admin needed):
   `schtasks /Create /TN "FantasyFootball_MFL_ADP_Daily" /TR "\"C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe\" \"C:\Users\matth\Documents\Personal\Fantasy Football\src\ingest_mfl_adp.py\"" /SC DAILY /ST 09:00 /F`
   — succeeded, verified via `schtasks /Query /TN ... /V /FO LIST` (Status: Ready, Scheduled Task
   State: Enabled, Run As User: matth). Points at the **main checkout** path
   (`C:\Users\matth\Documents\Personal\Fantasy Football\src\...` and `...\data\nfl.db`), not this
   worktree, so it will keep landing rows in the canonical db regardless of worktree lifecycle.
4. **Consumer check**: `src/availability.py::load_mfl_adp_source` / `default_ranking_sources`
   already keep `mfl_proxy` out of the default ranking-source set (single-source default is
   `fantasypros_ecr`; test `test_default_ranking_sources_does_not_include_mfl` already enforces
   this) and never write it as `league_adp`. No change needed there.
5. **Test added**: `tests/test_ingest_mfl_adp.py::test_network_failure_raises_loudly_and_writes_no_row`
   — stubs `urlopen` to raise, asserts the exception propagates and the row count stays 0. Full
   file: 10/10 passed.
6. **Flagged, not fixed**: `frontend/tests/test_ingest_mfl_adp.py` is a byte-identical duplicate of
   `tests/test_ingest_mfl_adp.py`, introduced by the "Merge frontend-prep branch into frontend/
   subdirectory, preserving history" merge (commit 2df3716). Root `pytest.ini` has
   `testpaths = tests` and `frontend/pytest.ini` has `testpaths = tests` (relative to frontend/),
   so both run independently and both currently pass — it's redundant, not broken, but it will
   silently drift out of sync with the canonical copy (I only patched `tests/test_ingest_mfl_adp.py`).
   Left untouched per my scope; flagging for backend/PM to decide whether to delete the frontend
   copy or symlink/import it.

## Why
Step 1.2 of this chain lands next in the same worktree. Backend needs today's row count, the
scheduled-task registration state, and the frontend-test-duplicate finding before building on top
of this, per the run playbook's "stop on red" / sequential-landing discipline.

## Done looks like
Backend acknowledges (reply appended here, STATUS updated) before starting step 1.2, and separately
decides whether to act on the `frontend/tests/test_ingest_mfl_adp.py` duplicate finding (own thread
if it needs its own tracking). Commit `a9291f1` on `backend/phase3-chain1-adp-and-exports`
(pushed to origin) is the artifact for this session's work.
