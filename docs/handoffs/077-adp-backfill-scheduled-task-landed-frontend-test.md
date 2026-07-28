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

---

## Reply — data-ops, 2026-07-27, founder amendment (CSV archive + date correction)

Founder amendment landed on top of the above, same worktree/branch. Two things backend needs to
know before step 1.2:

**1. Correction to the row above — the "2026-07-27" backfill was actually dated 2026-07-28 UTC.**
When I re-checked `adp_snapshots` while implementing the CSV export, the machine's UTC clock had
already rolled past midnight by the time the `--force` run executed: `retrieved_at` for that write
is `2026-07-28`, not `2026-07-27`. `adp_snapshots` now shows rows for UTC 2026-07-26 (232) and
2026-07-28 (246) with **zero rows for UTC 2026-07-27** — a real, permanent gap; MFL only serves
current ADP, so that day cannot be recovered. Not fabricated, not backfilled with a placeholder —
recorded as absent, per the honest-nulls rule. Flagging in case anything downstream assumed a
07-27 row exists.

**2. CSV archive added, per founder instruction.** `src/ingest_mfl_adp.py` now also writes
`data/adp-snapshots/YYYY-MM-DD.csv` (UTC date) on every run, one row per player, same columns as
`adp_snapshots`. Docstring states plainly: **the CSV is the canonical archive, the DB is a
queryable cache of it — if they disagree, the CSV wins.** `.gitignore` checked directly (not
assumed): no exception was needed, `data/adp-snapshots/` was never covered by the existing
`data/*.db` / `data/raw/` / `data/user pulled fantasy data/` patterns. Backfilled and committed
CSVs for both dates that actually have data: `data/adp-snapshots/2026-07-26.csv` (232 rows) and
`data/adp-snapshots/2026-07-28.csv` (246 rows) — written from the rows already in the DB, no
re-fetch. New tests `test_export_snapshot_csv_writes_one_row_per_player` and
`test_export_snapshot_csv_returns_none_and_writes_nothing_when_no_rows` (never writes an empty
file for a date with no rows). File total: 12/12 passed.

**3. Scheduled task re-pointed at a commit/push wrapper.** Added
`tools/run_adp_snapshot_task.bat` **in the main checkout** (not this worktree — required so the
task keeps working once this worktree is merged/deleted). It runs the ingest script, then
`git add data\adp-snapshots\*.csv`, commits, and pushes from the main checkout. Re-pointed
`FantasyFootball_MFL_ADP_Daily` at it via `schtasks /Change /TN "FantasyFootball_MFL_ADP_Daily"
/TR "\"...\tools\run_adp_snapshot_task.bat\""` — succeeded. **Caveat surfaced by `schtasks /Query
/V`**: `Logon Mode: Interactive only` (no run-as password was stored at creation or change time,
and I did not attempt to supply one — that would mean storing a Windows account password in a
script, which is exactly the credential-liability pattern CLAUDE.md §10 rules out as a last
resort). This means the task will only fire while an interactive session is logged in at 09:00
UTC-local, not from a locked screen or logged-out state — not truly unattended. Nobody has
verified an actual scheduled fire yet (can't fast-forward time). Flagging as a known limitation,
not silently claiming full unattended reliability.

**4. Worktree-isolation note**: `tools/run_adp_snapshot_task.bat` is the one file this session
added directly to the main checkout rather than this worktree. It's new/untracked there (added,
not modifying any existing tracked file, no git operations run against main by me) — left
uncommitted since committing app-adjacent files into main isn't mine to do per the isolation rule.
Whoever next touches main should either commit it or say if a different location/mechanism is
preferred.

Commit `8eb6276` on `backend/phase3-chain1-adp-and-exports`, pushed. `git stash list` empty.
Test count: `tests/test_ingest_mfl_adp.py` 12/12 passed.
