# 2026-07-30 — data-ops — re-landing lost ADP ingest

## Task
A prior worktree session's ADP capture wrote CSVs but ingested into a worktree copy of
`data/nfl.db`, which is gitignored and did not survive a container reset. Instructed to land it
for real, in the main checkout (`/home/user/Fantasy-Football`, branch `claude/pm-agent-setup-gobxa0`),
not a worktree.

## Before
`python3 tools/data_freshness_check.py` exited 1 with four CAPTURE-WITHOUT-INGEST gaps:

- `data/adp-snapshots/*.csv -> adp_snapshots(mfl_proxy)` file=2026-07-30 db=2026-07-29
- `data/adp-snapshots-ffc/*_non_ppr.csv -> ffc_adp_snapshots(ffc_non_ppr_10team)` file=2026-07-30 db=2026-07-29
- `data/adp-snapshots-ffc/*_half_ppr.csv -> ffc_adp_snapshots(ffc_half_ppr_10team)` file=2026-07-30 db=2026-07-29
- `data/adp-snapshots-ffc/*_ppr.csv -> ffc_adp_snapshots(ffc_ppr_10team)` file=2026-07-30 db=2026-07-29

Row counts before ingest (adp_source, count, max retrieved_at):
- `adp_snapshots` / `mfl_proxy`: 703 rows, max `2026-07-29T15:38:52`
- `ffc_adp_snapshots` / `ffc_non_ppr_10team`: 171 rows, max `2026-07-29T16:43:50`
- `ffc_adp_snapshots` / `ffc_half_ppr_10team`: 180 rows, max `2026-07-29T16:44:18`
- `ffc_adp_snapshots` / `ffc_ppr_10team`: 213 rows, max `2026-07-29T16:44:01`

## What I did
Used the project's existing import path — no new ingestion code:

```
python3 src/ingest_mfl_adp.py --db data/nfl.db --import-csv-dir data/adp-snapshots
python3 src/ingest_ffc_adp.py --db data/nfl.db --import-csv-dir data/adp-snapshots-ffc
```

Both are idempotent (`INSERT OR REPLACE` on the existing primary key), so re-running them is safe.

## Rows ingested
- MFL: 939 rows imported across 4 CSVs (2026-07-26: 232, 2026-07-28: 246, 2026-07-29: 225,
  2026-07-30: 236). `adp_snapshots(mfl_proxy)` `as_of`/`retrieved_at` now 2026-07-30.
- FFC: 4,967 rows imported across 37 CSVs — the three daily 10-team formats
  (`2026-07-29_{non_ppr,half_ppr,ppr}.csv`, `2026-07-30_{non_ppr,half_ppr,ppr}.csv`) plus the
  already-on-disk thread-055/thread-087 12-team historical backfill CSVs (2013-2024, non_ppr/
  half_ppr/ppr) that were sitting in the same directory. `ffc_adp_snapshots(ffc_{non_ppr,half_ppr,
  ppr}_10team)` `as_of`/`retrieved_at` now 2026-07-30.

No rows quarantined by this session — both scripts' `import_snapshot_csv`/`import_all_snapshot_csvs`
paths replay CSV rows verbatim (no re-resolution, no new quarantine decisions); any quarantine
already happened at original capture time, upstream of these files.

## Sources attempted and status
| Source | Status |
|---|---|
| `data/adp-snapshots/*.csv` -> `adp_snapshots(mfl_proxy)` | Ingested, gap closed |
| `data/adp-snapshots-ffc/*_{non_ppr,half_ppr,ppr}.csv` -> `ffc_adp_snapshots(ffc_*_10team)` | Ingested, gap closed |
| `rankings:fantasypros_csv_2026draft` | WARN, unchanged — needs founder browser export, not this task |
| `rankings:fantasypros_ecr` | WARN, unchanged — DynastyProcess mirror returns HTTP 403 from this environment, blocked 2026-07-30, not this task |

## After
`python3 tools/data_freshness_check.py` exits 0, all four gaps show `[ok]`.

## Exports regenerated
`python3 src/export_contract.py` — writes `board.json`, `availability.json`, `league.json`,
`rosters.json`, `weekly_finishes.json`, `season_stats.json` to `data/export/`.
`availability.json`'s figures are read from a pre-computed CSV inside `build_availability_json`
(`_load_availability_csv`) — **the availability model itself was NOT re-run**, per the hard stop on
this task (blocked pending strategist thread 119). Diffed the non-ADP artifacts (`league.json`,
`rosters.json`) — only `generated_utc` changed, confirming no formula/weight touched.

`player_descriptions.json` was already `OK` (age 0) in the freshness check before this session and
was not regenerated — it does not depend on the ADP tables.

## Not done (explicitly out of scope per task)
- Did not re-run the availability model for any of the 25 leagues (thread 119 hard stop).
- Did not change any formula, weight, or statistical constant.
- Did not touch FantasyPros ingestion (founder-export-only / 403-blocked, pre-existing).

## Tests
`python3 -m pytest tests/test_backfill_ffc_adp_history.py tests/test_freshness.py
tests/test_ingest_ffc_adp.py tests/test_ingest_mfl_adp.py tests/test_export_contract.py -q`:
**111 passed, 3 failed.** The 3 failures (`test_store_adp_called_twice_same_day_overwrites_not_appends`,
`test_export_snapshot_csv_after_repeated_store_has_no_duplicate_rows`,
`test_three_formats_export_to_distinct_csv_filenames`) are pre-existing, date-dependent test bugs —
each hardcodes `"2026-07-29"` as "today" while `export_snapshot_csv` filters by the real current UTC
date (now 2026-07-30), and each uses an isolated `tmp_path` DB never touched by this session's
changes. Not caused by this ingest.

## Commit
`fd8f063` — "Re-land lost ADP ingest: import 2026-07-30 MFL/FFC CSVs into data/nfl.db"
(6 files changed in `data/export/`; `data/nfl.db` itself is gitignored per project convention, so
the ingested rows live only in the local DB file, matching how every prior ADP ingest in this
project has been committed).
