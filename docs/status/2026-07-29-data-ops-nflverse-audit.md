# 2026-07-29 — data-ops — nflverse unused-data audit

**Task:** audit only, no ingestion. Enumerate every `nflreadpy` loader (23 total, pinned
`nflreadpy==0.1.5`) against what `data/nfl.db` and `src/ingest_reference.py` /
`src/ingest_weekly_stats.py` already pull, and identify what's free, licensed, and unused that
would plausibly matter to a player-level ranking model — specifically checking whether it closes
any of the coaching or route-participation gaps.

**Worktree setup note:** `data/nfl.db` in this worktree was a 0-byte stub (per
`docs/environment.md` §4 — sqlite silently creates one on first touch). Copied the real 854.7MB
file from the main checkout before querying.

**Method:** called every loader not already used by this repo directly against the network
(nflverse's public GitHub-release mirrors), inspected real `.columns`/`.shape`, cross-checked
against `sqlite3` queries on the copied `data/nfl.db` (22 tables, matches CURRENT-STATE).

**Findings (full detail in `docs/research/nflverse-unused-data-audit-2026-07-29.md`):**

- 10 of 23 loaders already called by this repo; 13 never called.
- `load_schedules()` carries `home_coach`/`away_coach` per game, 1999–2026, 7,548 rows total,
  zero nulls in every season sampled (1999/2010/2020/2025/2026). Not currently ingested.
  **Partially** closes the coaching gap — head-coach identity only, not coordinator/play-caller
  duty, so `src/ingest_play_callers.py` (confirmed still parked, zero rows, no table in
  `data/nfl.db`) remains the right approach for that piece.
- `load_participation()` carries a `route` column (route type run by the targeted receiver) and
  `offense_players` (all 11 on-field players) per pass play, 2016–2025, ~45–48K plays/season.
  This is the "documented proxy calculation" CLAUDE.md §5 anticipates for route data — not
  currently ingested. Confirmed the three already-ingested NGS tables
  (`ngs_receiving`/`rushing`/`passing`, 14,731/6,059/5,933 rows, 2016–2025) carry no route field
  at all — so the existing route-gap claim was accurate for those tables, the miss was never
  checking `load_participation`.
- `load_ff_opportunity()` (2006–2025, ~5,200–6,100 rows/season, 159 columns) is a pre-fitted xFP
  model, not raw data — flagged for a Statistician call before use as a ranking input, not
  something Data Ops should decide alone.
- `load_ff_rankings()` attempted, got `403 Forbidden` from the proxy fetching
  `github.com/dynastyprocess/data` — recorded as blocked, not retried, not worked around.
- Other unused loaders checked and deprioritized: `load_rosters_weekly` (marginal overlap with
  `injuries`/`depth_charts_weekly`), `load_ftn_charting` (test-registry #16/#17 pointed here —
  checked, **no route-participation column exists in it**, that pointer was stale), `load_pfr_advstats`,
  `load_team_stats`, `load_officials`, `load_trades`, `load_players`/`load_rosters` (no distinct
  signal over what's already held), `load_pbp`/`load_stats`/`load_ffverse` (raw source or
  dispatcher/meta, nothing new).

**Rows ingested:** 0 (audit only, per task constraint).
**Rows quarantined:** 0.
**Sources attempted:** nflreadpy loaders — all succeeded except `load_ff_rankings` (403 via
proxy, blocked, recorded).
**Commit:** see `git log` in this worktree, branch pushed, not merged.
**Test count:** no code changed; no new/changed tests this session.

**Docs touched:** `docs/research/nflverse-unused-data-audit-2026-07-29.md` (new),
`docs/CURRENT-STATE.md` (item 10 added, in place), this file.
