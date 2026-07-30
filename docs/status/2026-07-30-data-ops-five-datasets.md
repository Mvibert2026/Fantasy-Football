# 2026-07-30 — data-ops — five nflverse datasets, ranker's thread

Worked in the main checkout, not a worktree (per task instructions — a worktree DB write was
explicitly called out as the mistake to avoid). Answers thread
`docs/handoffs/2026-07-30-five-datasets-30-seconds-total-all-measured-toda.md` (ranker → data-ops).

## What landed

| dataset | status | rows | span | key |
|---|---|---|---|---|
| `pbp` | new table | 816,856 | 2009-2025 | `(game_id, play_id)`, indexed `(season, week)` |
| `rosters_weekly` | new table (`ingest_reference.py` SPECS) | 888,786 | 2002-2025 | `(season, team, week, gsis_id)` |
| `schedules` | new table (`ingest_reference.py` SPECS) | 7,548 | 1999-2026 (2026 unplayed) | `(game_id)` |
| `depth_charts_snapshots` | refreshed (already existed) | 939,035 | 2025-08-03 to 2026-07-30 | `row_hash`, `as_of_column=dt` |
| `injuries` | **not landed for 2025** | 79,816 (unchanged) | 2009-2024 | `(season, game_type, team, week, gsis_id)`, `as_of_column=date_modified` |

## Why injuries didn't land for 2025

`load_injuries(seasons=True)` returns 6,068 2025 rows, but every one has `date_modified = NULL`
upstream. `ingest_reference.py`'s existing `prepare()` step (CLAUDE.md §6.1: reject an undated
row, never default it) correctly drops all 6,068. This is the guardrail working, not a bug I
should route around. Flagged loudly in `tools/data_freshness_check.py`'s new `injuries` row and
in the handoff reply; the fix (if any) is a methodology call for backend/statistician about
whether season/week is an acceptable as_of substitute for this table, not an ingestion decision.

## Look-ahead / holdout notes

- `pbp`, `rosters_weekly`, `schedules` carry no calendar `as_of_date` — none exists upstream.
  `season`/`week` (or `season`/`game_id` for schedules) is the real grain a downstream reader
  must filter on.
- `rosters_weekly` and `schedules` now contain season-2025 and season-2026 rows. 2025 is the
  sealed ranking-model holdout. Ingesting it is not the same as spending it, but any backtest
  harness evaluating a season-2025 config must not read season≥2025 rows from these three tables
  — that enforcement belongs to the harness, not built here.

## Measured vs ranker's numbers

| call | ranker measured | measured this session |
|---|---|---|
| `load_pbp(2009…2025)`, 24 cols | 816,856 rows, 20.4s | 816,856 rows, 36.3s cold / ~9.5s warm (row/col counts match exactly; timing variance is network, not data) |
| `load_rosters_weekly(2025)` | 46,849 rows, 1.0s | 46,849 rows, 1.7s |
| `load_injuries([2025])` | 6,068 rows, 0.5s | 6,068 rows, 1.2s |
| `load_schedules([2025,2026])` | 557 rows, 1.3s | 557 rows, 0.7s |
| `load_depth_charts([2025])` | 554,215 rows, 0.7s | not independently re-measured; ran via `ingest_reference.py`'s full historical pull instead (see below) |

## Also confirmed

- `load_rosters_weekly`'s real earliest valid season is **2002**, not earlier — `nflreadpy`
  raises `Season must be between 2002 and 2025` for 2001. The `component-model-rb-qb-te-pass-1.md`
  §5.2 claim of reaching further back is wrong.
- `depth_charts_weekly` (season/week format) has zero 2025 rows because nflverse has not
  published that format for 2025 at all — not an ingestion gap. The 2025 depth-chart signal
  already existed under `depth_charts_snapshots` (dt-timestamped) before this session; it is now
  refreshed through 2026-07-30.

## Code changes

- `src/ingest_pbp.py` — new script, 24-column slim PBP ingester.
- `src/ingest_reference.py` — two new `SourceSpec` entries: `rosters_weekly`, `schedules`.
- `scripts/rebuild_database.py` — new step 1b (`ingest_pbp.py`); post-rebuild assertions extended
  with row-count floors for `pbp`, `rosters_weekly`, `schedules`.
- `tools/data_freshness_check.py` — new `_table_max_season_row` helper (season-granularity
  freshness for tables with no calendar as_of); rows added for `pbp`, `rosters_weekly`,
  `schedules`, `injuries`.
- `docs/CURRENT-STATE.md` — items 9/9a updated in place from "missing" to landed, with the
  injuries caveat stated explicitly.
- Handoff thread replied and marked `STATUS: RESOLVED` (I am the `TO:` role).

## Commit

Landed via the coordinator's bundling commit `d3f3c76` ("FR-136 Q1 block 4..."), not a commit I
made directly — verified `git diff HEAD -- <my files>` is empty (byte-for-byte match), per the
"work appears in a commit you did not make" protocol. No conflict, nothing to reconcile.

## Tests

`tests/test_ingest_reference.py` + `tests/test_freshness.py`: 20/20 passed. No dedicated test
file exists yet for `ingest_pbp.py` — flagged, not written this session (a table this new
deserves its own review, not a rushed test under ingestion-only scope). Four pre-existing,
unrelated failures observed in `tests/test_ingest_ffc_adp.py` / `tests/test_ingest_sleeper_
projections.py` — not touched by this work, not investigated (out of scope).

## Freshness check

Exit 0 before this session's changes. Exit 0 after, with `pbp`/`rosters_weekly`/`schedules`
reporting OK and `injuries` reporting OK-but-explicitly-flagged (its `owner` field states the
NULL-`date_modified` block in full rather than showing a bare status).

## Rows ingested / quarantined

- Ingested: 816,856 (pbp) + 888,786 (rosters_weekly, full 2002-2025 pull) + 7,548 (schedules,
  full 1999-2026 pull) + 939,035 (depth_charts_snapshots refresh) = 2,652,225 rows written across
  four tables.
- Quarantined/dropped, all reported not silent: `rosters_weekly` 136 null-key + 17,456
  duplicate-key (multi-entry weeks, expected); `injuries` 6,068 rows never written (NULL as_of,
  see above) — not a quarantine table, a structural refusal.
