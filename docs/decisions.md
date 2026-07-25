# Architecture Decision Log

## 2026-07-25 — Data ingestion (Phase 1, Step 1)

**Single wide `player_weekly_stats` table, schema generated from the source, not hand-typed.**
`src/ingest_weekly_stats.py` builds the SQLite `CREATE TABLE` from the polars DataFrame that
`nflreadpy.load_player_stats()` returns, mapping dtypes programmatically instead of hardcoding
~145 column definitions. This avoids silent drift if nflverse adds/renames columns upstream.

**No `user_id` / `league_id` on this table**, despite `CLAUDE.md` §4's multi-user-from-day-one
principle. Reasoning: this table is shared reference data (what actually happened in the NFL) —
identical for every user/league, not owned by one. The multi-user principle applies to tables
holding user- or league-specific state (rosters, rankings, ADP snapshots, outcome feedback), not
to the raw stats fact table. Revisit only if a future requirement makes per-user *overrides* of
raw stats a real thing (currently inconceivable).

**No `as_of_date` on this table.** `CLAUDE.md` §6.1 requires `as_of_date` for time-sensitive
records (ADP, injuries, depth charts, odds) because their *meaning* depends on when they were
observed. Weekly stats are the opposite: they are final, already-realized outcomes for a game
that already happened, not a snapshot of a belief. The look-ahead-bias risk this table poses is
structural (a season-N ranking model must not be handed season-N rows) and belongs to the
backtest harness (Step 3), not to this cache. Flagging so Step 3's harness design accounts for it
explicitly rather than assuming `as_of_date` filtering will handle it.

**No `season_weight` on this table.** That's a ranking-algorithm-time concept (how much a given
season should count toward a projection), applied by the model, not a static property of a
historical row. Belongs in `ranking_versions` config (Step 4).

**Filtered out rows with `player_id IS NULL` before writing.** Verified via direct inspection:
~22 rows/season in the nflreadpy output are team-level aggregates (only `def_safeties`,
`penalties`, `penalty_yards` are ever non-zero on them) with no player attribution. None of
those stat categories are in this league's scoring rules (`CLAUDE.md` §7) anyway. Left in, they
would also break upsert idempotency: SQLite does not treat `NULL` as equal to `NULL` in a
composite primary key, so these rows would duplicate on every re-ingestion run. Caught by a
failing idempotency test before it reached `data/nfl.db`.

**Primary key: `(player_id, season, season_type, week)`.** Verified empirically (no duplicate
key groups in any pulled season) rather than assumed. `INSERT OR REPLACE` on this key makes
re-running ingestion for a season safe — it updates corrected stats in place instead of
duplicating rows.

**Provenance column `ingested_at`** added (not present in the source) so we can tell when a row
was last (re)written — cheap, useful for debugging cache staleness, not a modeling field.
