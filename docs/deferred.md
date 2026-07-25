# Deferred Decisions

## Normalized `players` dimension table

`CLAUDE.md` §4's core-tables sketch lists both `players` and `player_weekly_stats`. Only
`player_weekly_stats` was built (2026-07-25). A separate `players` table would require making
identity-resolution judgment calls (current team/position when they change mid-season or
year-to-year, name changes, etc.) with no current consumer — the raw fact table already carries
`player_name`, `position`, and `team` per row, which is sufficient for Step 1. Build it when the
scoring engine (Step 2) or ranking algorithm (Step 4) actually needs a stable per-player entity
to join against, not before.

## `player_season_stats` table

Also in `CLAUDE.md`'s sketch, not built. Season-level aggregates are a derived view over
`player_weekly_stats` (sum/avg by player+season) with no independent source data — better as a
SQL view or computed at read time once there's a real consumer, rather than a second cached copy
that can drift out of sync with the weekly table.

## Coaching staff, odds, ADP ingestion

Explicitly out of scope for this pass — the task was weekly player stats only. `coach_id`,
`odds_snapshots`, and `adp_snapshots` remain unbuilt. Per `CLAUDE.md`'s own flag: ADP snapshot
capture with `as_of_date` should start "immediately regardless of sequence" since it can't be
backfilled later — this is the next highest-priority ingestion gap, not weekly stats.
