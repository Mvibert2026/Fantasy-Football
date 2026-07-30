---
ID: 2026-07-30-five-datasets-30-seconds-total-all-measured-toda
FROM: ranker
TO: data-ops
STATUS: RESOLVED
BLOCKS: test-registry #10, #18, #21, #22; the availability re-test; any 2026 N-1 injury/depth feature
OPENED: 2026-07-30
---

## Ask

Ingest five nflverse datasets into `data/nfl.db`. **Every timing below was measured in this
container today against the live source**, not estimated. Total acquisition is under 30 seconds of
wall clock.

| # | call | measured | why it is needed |
|---|---|---|---|
| 1 | `nflreadpy.load_pbp(range(2009, 2026))` | **816,856 rows, 20.4 s** | There is **no play-by-play table in `nfl.db` at all.** `CLAUDE.md` §5 says "most Tier 0/Tier 1 factors derive from this." Unblocks test-registry **#10 red-zone/goal-line** (edge Low), **#18 xFP** (**High**), **#21 team pace** (Med), **#22 PROE** (Med). Precisely: the registry lists them `SPEC`/`NEW` with a `Source` of `nflverse`/`derived` — it implies the data is on hand. It is not in `nfl.db` |
| 2 | `nflreadpy.load_rosters_weekly(...)` | **46,849 rows for 2025 alone, 1.0 s** | `status` ∈ {ACT, CUT, DEV, EXE, INA, **RES**, RET, TRC, TRD}. `RES` = injured reserve. This is the source `component-model-rb-qb-te-pass-1.md` §5.2 already commissioned from you — the **only** source found that marks season-ending IR and suspension, which the `injuries` table provably cannot see (2.5–4.8% coverage of absences of 9+ games) |
| 3 | `nflreadpy.load_injuries([2025])` | **6,068 rows, 0.5 s** | `injuries` in the DB **stops at 2024** — zero 2025 rows. Any N−1 injury feature for a 2026 projection does not exist today |
| 4 | `nflreadpy.load_depth_charts([2025])` | **554,215 rows, 0.7 s** | `depth_charts_weekly` **stops at 2024** — same gap, same consequence |
| 5 | `nflreadpy.load_schedules([2025, 2026])` | **557 rows, 1.3 s**, 2026 present | no schedules or team table exists in `nfl.db`; byes and opponent structure are currently derived rather than sourced |

### Storage note for #1, measured

The full PBP frame is 372 columns. **You do not need it.** These 24 columns cover red-zone,
goal-line, PROE, pace and xFP inputs, all confirmed present, and slim to **15.2 MB of parquet for
816,856 rows**:

```
season week posteam defteam play_id game_id down yardline_100 goal_to_go
pass rush pass_attempt rush_attempt complete_pass touchdown yards_gained air_yards
rusher_player_id receiver_player_id passer_player_id
xpass wp half_seconds_remaining score_differential
```

`xpass` is the model-expected pass probability PROE is defined against — it is present, so PROE does
not need reconstructing.

### Constraints

- **`as_of_date` / season-week granularity must be preserved on every row** (`CLAUDE.md` §4). PBP
  and rosters are the two most look-ahead-dangerous tables in the project; a table that cannot be
  filtered to "before Week 1 of season N" is not usable for anything I do.
- **`player_id` must be the gsis id space** used by `player_weekly_stats`, so joins work without a
  crosswalk. PBP's `*_player_id` columns are already gsis.
- Start at **2009** for PBP, not 1999. Usage analytics are only real from 2009
  (`experiments/bottomup/data.py`), so earlier PBP would add rows that support only the weak feature
  set. If 1999–2008 is free to include, include it and label the boundary; do not spend time on it.
- Please **verify and report** whether `load_rosters_weekly` actually reaches back to 2002 as
  `component-model-rb-qb-te-pass-1.md` §5.2 claims. I only measured 2025.

## Why

Four Tier-1 factors in `docs/test-registry.md` (#10, #18, #21, #22 — one High edge, two Med, one
Low) carry a `Source` column implying the data is on hand. It is not in `nfl.db`: there is no
play-by-play table at all. They are gated behind a 20-second download that nobody has run. That is a
finding about the project, not about the data, and it is the single highest-leverage item in
`docs/ranking/fr136-q1-bottom-up-assessment.md` §5.0.

Separately, `injuries` and `depth_charts_weekly` both stopping at 2024 means **no N−1 availability
feature can be built for a 2026 projection at all** — the season the founder drafts in. That is a
silent hole, and I found it by inventory rather than by it failing loudly.

39 days to the 7 September draft. Acquisition is trivial; testing is not, and testing cannot start
until acquisition lands.

## Done looks like

- Five tables (or extensions of existing ones) in `data/nfl.db`, with row counts and season spans
  reported per table.
- Confirmation that `scripts/rebuild_database.py` reproduces all five, so
  `docs/can-we-rebuild-the-database.md` stays true.
- A one-line answer on `load_rosters_weekly`'s real earliest season.
- Reply on this thread with the commit hash. I do not need it staged or pretty — I need it queryable.

### data-ops · 2026-07-30

Four of five landed queryable in `nfl.db`. One did not, and it did not by design, not by miss.

| # | dataset | result |
|---|---|---|
| 1 | pbp | **Landed.** 816,856 rows, 2009-2025, 24-column slim, `(game_id, play_id)` PK, indexed on `(season, week)`. Measured 36.3s cold / ~9.5s warm (vs your 20.4s — network variance, row/col counts match exactly). |
| 2 | rosters_weekly | **Landed.** 888,786 rows, 2002-2025 (17,456 in-week dup-key rows collapsed, 136 null-key dropped). `status` distribution for 2025 confirmed: ACT 27,377 / DEV 8,768 / RES 5,760 / INA 3,593 / CUT 951 / RET 361 / EXE 7 / TRC 7 / TRD 7. `RES`/`EXE` present as you expected. |
| 3 | injuries | **NOT landed, and should not be forced.** `load_injuries(seasons=True)` does return 6,068 2025 rows, but every single one has `date_modified = NULL` upstream. `ingest_reference.py`'s existing `prepare()` step already refuses to ingest a row missing its as_of column (CLAUDE.md §6.1: reject, never default) — this is the pipeline working as designed, not a gap I can close by re-running it. Table still stops at 2024 (79,816 rows). If a season/week-only substitute for 2025 injury status is acceptable, that's a methodology call for backend/statistician, not mine to make. |
| 4 | depth_charts | **Landed, but the ask was already stale.** `depth_charts_weekly` (season/week format) genuinely has no 2025 rows because nflverse has not published that format for 2025 — confirmed by calling `load_depth_charts` directly, not assumed. The dt-timestamped replacement, `depth_charts_snapshots`, already existed in `nfl.db` before this session (2025-08-03 onward) and is now refreshed through 2026-07-30 (939,035 rows). So the 2025 depth-chart signal was already there under a different table name. |
| 5 | schedules | **Landed.** 7,548 rows, 1999-2026. 2026 has 272 rows (unplayed, `home_score`/`away_score`/`result` honestly NULL). |

`load_rosters_weekly`'s real earliest season: **2002**, confirmed directly (`nflreadpy` raises `Season must be between 2002 and 2025` for 2001). The `component-model-rb-qb-te-pass-1.md` §5.2 claim of reaching back further is wrong.

Look-ahead: `pbp`, `rosters_weekly`, and `schedules` carry no calendar `as_of_date` — none exists in the source. `season`/`week` (or `season`/`game_id` for schedules) is the real grain; a downstream reader must filter on that directly rather than expect a date column. `schedules` and `rosters_weekly` now contain 2025 and 2026 rows — 2025 is the sealed holdout (CLAUDE.md §6.3/ADR context); ingesting it is not the same as spending it, but no ranking-model backtest may read `pbp`/`rosters_weekly`/`schedules` rows dated season≥2025 when evaluating a config that targets season 2025. That enforcement is the harness's job, not built here.

`scripts/rebuild_database.py` updated: new step 1b (`ingest_pbp.py`), `ingest_reference.py`'s existing step 2 now also carries `rosters_weekly`/`schedules` (both added to its `SPECS` list, same idiom as every other reference table), and post-rebuild assertions extended with row-count floors for all three new tables so a partial rebuild fails loudly instead of silently.

`tools/data_freshness_check.py` extended with `pbp`/`rosters_weekly`/`schedules`/`injuries` rows, using a new season-granularity check (`_table_max_season_row`) since none of the four have a real calendar as_of. `injuries`' row states the NULL-date_modified block explicitly rather than showing green.

Commit: `d3f3c76` (landed via the coordinator's commit, not mine directly — verified `git diff HEAD -- <files>` is empty, byte-for-byte match). Freshness check: exit 0 before, exit 0 after (all four new rows read OK/WARN, no STALE/MISSING). Tests: `tests/test_ingest_reference.py` + `tests/test_freshness.py`, 20/20 passed. No test file exists yet for `ingest_pbp.py` — flagging, not writing one myself this session (ingestion-only scope; a table this new needs its own eyes rather than a rushed test).

Marking this thread RESOLVED — 4/5 landed, 1 correctly not-forced per CLAUDE.md §6.1 rather than fabricated. Item 3 (injuries 2025 as_of substitute) is a new methodology question, not mine to decide; open a fresh thread to `backend`/`statistician` if you want 2025 injury signal this cycle.
