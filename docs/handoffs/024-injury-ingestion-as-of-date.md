---
ID: 024
FROM: pm
TO: data-ops
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: P3-2 (date-parametrised board refresh)
---

## Ask
Ingest injury status via nflverse `load_injuries`, which covers 2009–2025, and capture it **with an
`as_of_date` on every row**.

## Why
This is logged as `deferred.md` item P3-2 and the reason it matters is subtle: without `as_of_date`,
any historical rebuild of the board uses final-season injury knowledge, which is look-ahead
contamination and violates the project's own §6.1. The ranking side of P3-2 already works today; this
is the missing half.

**This is not the same as building the injury pipeline.** The real-time injury/news feature is
deliberately deferred over hallucination risk, with that reasoning stated in the code. Do not build
prose generation, do not build alerting. Ingest historical injury facts with dates. Nothing more.

## Constraints
Dates are the entire point. A row without an `as_of_date` is worse than no row, because it looks
usable. Reject rather than default them.

## Done looks like
Injury data ingested 2009–2025 with `as_of_date` on every row, row counts per season reported, a test
asserting no row can be inserted without a date. Commit hash and test count.

---

### data-ops · 2026-07-26

**Found existing infra, fixed it rather than duplicating it.** `src/ingest_reference.py` was
already pulling `load_injuries(seasons=True)` into an `injuries` table (90,752 raw rows), with an
`as_of_column="date_modified"` field already declared on its `SourceSpec` — but that field was
pure metadata, never read anywhere. No row was rejected for lacking a date, and the column had no
`NOT NULL`. That's exactly this thread's gap. Rather than stand up a second, competing `injuries`
table (which would have created two disagreeing sources of truth), I made `as_of_column`
structural in the shared pipeline:

- `prepare()` now drops any row whose `as_of_column` value is null, before it ever reaches the
  DB, and reports the drop count.
- `build_create_table_sql()` now emits `NOT NULL` on that column, so even a direct INSERT
  bypassing `prepare()` is refused by the table itself.
- This applies to both tables that declare `as_of_column` (`injuries` → `date_modified`,
  `depth_charts_snapshots` → `dt`), not just injuries. Re-ran `depth_charts_snapshots` after the
  change: 926,335 rows, zero dropped (its `dt` was already fully populated) — confirms the fix
  didn't regress an unrelated table.

**Row counts per season, real pull (`--only injuries`):**

| Season | Rows kept | Notes |
|---|---|---|
| 2009 | 17 | 4,804 of 4,821 source rows had no `date_modified` — rejected, not defaulted |
| 2010 | 4,429 | 62 undated rows rejected |
| 2011 | 4,971 | fully dated |
| 2012 | 5,533 | fully dated |
| 2013 | 5,070 | fully dated |
| 2014 | 5,078 | fully dated |
| 2015 | 5,232 | fully dated |
| 2016 | 5,115 | fully dated |
| 2017 | 5,104 | fully dated |
| 2018 | 5,133 | fully dated |
| 2019 | 5,392 | fully dated |
| 2020 | 5,661 | fully dated |
| 2021 | 5,587 | fully dated |
| 2022 | 5,682 | fully dated |
| 2023 | 5,599 | fully dated |
| 2024 | 6,213 | fully dated |
| 2025 | 0 | nflverse has not published a `date_modified` column for the current season yet — entire season dropped, not defaulted. Re-check later; the ask said "covers 2009-2025" but the live schema doesn't currently support 2025 |

Total kept: 79,816 of 90,752 loaded (10,934 dropped for missing `as_of_date`, 2 dropped as
duplicate keys). Verified post-write: `SELECT COUNT(*) FROM injuries WHERE date_modified IS NULL`
→ 0.

**No prose/alerting built** — confirmed out of scope, not touched.

**Rows ingested:** 79,816 (table `injuries`, full 2009–2024 rebuild; 2025 not yet available from
source).
**Rows quarantined/dropped:** 10,934 for missing `as_of_date` (see per-season table above) + 2 for
duplicate primary key.
**Tests:** `tests/test_ingest_reference.py`, 8 new — covers the null-drop in `prepare()`, the
`NOT NULL` in generated DDL, a raw-SQL insert attempt asserting `sqlite3.IntegrityError` on a null
`as_of_date`, and an end-to-end prepare→write path with zero nulls surviving.
**Commit:** see session commit in `docs/status.md`.

STATUS: RESOLVED.
