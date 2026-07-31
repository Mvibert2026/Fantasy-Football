# data-ops · 2026-07-30 · six-loader nflverse ingest

Task: ingest the six free, previously-unfetched nflverse loaders named in
`docs/research/analyst-factor-sweep-2026-07-30.md` §1. Ingestion only, no
formula/statistical work.

## What was ingested

| Loader | Table(s) | Seasons | Rows | Time |
|---|---|---|---|---|
| `load_participation()` | `participation` | 2016–2025 | 478,989 | 14.0s |
| `load_ff_opportunity()` | `ff_opportunity` | 2006–2025 | 105,905 | 15.3s |
| `load_pfr_advstats()` | `pfr_advstats_pass/rush/rec/def` | 2018–2025 | 5,424 / 18,461 / 35,724 / 62,345 (121,954 total) | 19.0s |
| `load_contracts()` | `contracts` | present-day snapshot | 51,772 | 2.4s |
| `load_combine()` | `combine` | draft classes 2000–2026 | 8,968 | 1.1s |
| `load_trades()` | `trades` | 2002–2026 | 4,975 | 1.5s |
| `load_officials()` | `officials` | 2015–2025 | 21,900 | 1.8s |

All figures measured this session (`.venv/bin/python`, Linux, main checkout,
no worktree). Total: ~793,463 rows, ~56s wall across all fetches.

## Time keys — which are defensible, which are not

- **Defensible, native season/week grain, no invented date**: `participation`
  (season/week parsed from `nflverse_game_id`, no native column), `ff_opportunity`,
  `pfr_advstats_*`, `officials`.
- **Defensible, fixed historical fact**: `combine` (season = draft class year).
- **Defensible, fixed historical fact but source doesn't filter by season**:
  `trades` (native `season`/`trade_date`, full-history pull, no seasons arg exists).
- **NOT a time series — present-day snapshot only**: `contracts`. `is_active`
  reflects status as of fetch date, not any historical season. Flagged heavily
  in `src/ingest_contracts.py`'s docstring as the same class of trap as the
  Wikipedia-navbox coaching-staff issue named in the task brief. `year_signed`
  contains at least one `0` value in the raw source — recorded as-is, not
  fabricated or silently dropped.

## Sealed 2025 holdout

`participation`, `ff_opportunity`, and all four `pfr_advstats_*` tables carry
season-2025 rows (in-progress season). Ingesting them is not spending the
holdout, but any future backtest touching season 2025 from these tables
outside pre-registered holdout context raises `HoldoutViolation` per
`CLAUDE.md` §2/§6.3. `contracts`/`combine`/`trades`/`officials` are not
season-partitioned the same way and carry no comparable risk.

## Freshness check

`tools/data_freshness_check.py` extended with 8 new rows: season-grain checks
for `participation`/`ff_opportunity`/`pfr_advstats_*` (matching the existing
`pbp`/`rosters_weekly` pattern), and `ingested_at`-grain checks for
`contracts`/`trades`/`officials`/`combine` (wide thresholds — these are
static/backfill/rolling-snapshot sources, not daily feeds).

- Exit code before extension: **0**
- Exit code after extension: **0**

## Not done

- No formula changes, no feature computation (e.g. no YPRR/route-participation
  computed from `participation.offense_players`; no ALY computed from PBP for
  registry #23). That is a Backend/Statistician-owned step per `CLAUDE.md` §9.
- No re-run of the availability model (still gated on M0, per task instruction).
- `load_ff_opportunity()`'s `pbp_pass`/`pbp_rush` stat_types not fetched — no
  named registry consumer yet, left for a future ingest if one appears.
- Mock draft logging and ADP `as_of_date` snapshots were not touched this
  session; the task scope was explicitly the six named loaders.

## Evidence

- Commits: `65facca` (ff_opportunity), `503809c` (pfr_advstats), `8306780`
  (contracts), `a1b29ee` (combine), `0000102` (trades + officials), `12dcb92`
  (freshness check). `participation`'s script landed under commit `3201daa`
  (coordinator-committed, verified `git diff HEAD -- src/ingest_participation.py`
  empty — byte-for-byte the file as written this session, nothing to reconcile).
- Test count: `pytest tests/ -k freshness` — 14 passed. Full suite not re-run
  this session (out of scope; no code outside ingestion/freshness-check touched).
- `data/nfl.db` is gitignored per `CLAUDE.md` §10; not committed, as expected.

## Sources attempted and status

All six loaders: **fetched successfully**, no blocks encountered. No FFC/
ESPN/Yahoo endpoints touched this session (out of scope for this task).
