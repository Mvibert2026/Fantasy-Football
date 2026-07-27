# Tier 1 usage/opportunity source inventory — 2026-07-27

Scope: thread 046, Tier 1 only (volume and opportunity features for a bottom-up projection
model). Tier 2/3 out of scope this round; noted briefly at the end per the ask.

All figures pulled live from `data/nfl.db` and from `nflreadpy==0.1.5` loader calls
(`update_config(cache_mode="filesystem")`), 2026-07-27. Interpreter used throughout:
`C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe`.

**Headline finding: most of Tier 1 is already ingested and fresh.** Prior sessions (thread
018/024 and others, via `src/ingest_weekly_stats.py` and `src/ingest_reference.py`) already
pulled the core volume/opportunity tables. All Tier-1-relevant tables in `data/nfl.db` carry
`ingested_at` timestamps of 2026-07-25/26 — within the last two days as of this session. No stale
re-pull was needed for this round.

## 1. Snap counts and snap share

| | |
|---|---|
| Table | `snap_counts` (`src/ingest_reference.py`, loader `nfl.load_snap_counts`) |
| Coverage in DB | 2013–2025, 324,611 rows |
| Source floor | nflverse rejects `season < 2012` outright (`ValueError: Season must be between 2012 and 2025`); `season=2012` returns 0 rows when queried directly. **2013 is the true first populated season**, not an ingestion gap. |
| Columns | `offense_snaps`/`offense_pct`, `defense_snaps`/`defense_pct`, `st_snaps`/`st_pct`, keyed `(game_id, pfr_player_id)` |
| Reliability | No known unreliable-but-present window (unlike targets/air yards below). Verified populated at both ends of the range spot-checked. |

## 2. Target share, carry share, route participation

| Feature | Status |
|---|---|
| Target share | `player_weekly_stats.target_share` (also `air_yards_share`, `wopr`) — present 1999–2025, **unreliable 2003–2008** (see §5). Source: `nfl.load_player_stats(summary_level="week")`. |
| Carry share | Not a precomputed column. `carries` is present and reliable across the full 1999–2025 window (rushing counting stats did not suffer the 2003–2008 charting gap that targets did — verified: `SUM(carries)` for those seasons is in normal per-season range, only `targets`/`receiving_air_yards` collapse). Carry share must be derived downstream as `carries / team_carries`; that's a Backend feature-engineering task, not an ingestion gap. |
| Route participation | **No per-player nflverse table gives this directly.** `nfl.load_participation` (2016–2025 only; rejects earlier seasons) is play-level, not per-player: it carries a play-level `route` field (whether the play was a route-running play) plus `offense_players`/`offense_positions` list columns. A per-player route-participation rate could in principle be derived by exploding those list columns and joining player identity, but that is a nontrivial derivation, not a ready column, and would only cover 2016 forward. Not attempted this round — flagged as a Tier 1 gap requiring either (a) a derivation task from `load_participation`, or (b) accepting NGS `avg_intended_air_yards`/target-share proxies in its place pre-2016. `load_ftn_charting` (2022–2025 only, CC-BY-SA, attribution required) is also play-level (formation/personnel/pressure booleans), not a per-player route charting source — checked its column list directly, no per-player route field present. |

## 3. Red-zone and goal-line usage

**Not present as a ready column or table anywhere in the current pipeline.** No nflverse loader
returns a precomputed red-zone-share stat; the only path is aggregating `nfl.load_pbp` by
`yardline_100 <= 20` (red zone) / `<= 10` or `<= 5` (goal-line), grouped by player and season. `load_pbp`
is not currently ingested into `data/nfl.db` at all (no `pbp` or `plays` table exists). Full historical
play-by-play (1999–2025) is a multi-gigabyte pull and a nontrivial per-play-to-per-player attribution
job — explicitly out of scope for a low-effort ingestion pass, and risky to attempt against the shared
853 MB `data/nfl.db` while three backend sessions are concurrently writing to it this round. **Flagged
as the one genuine Tier 1 gap requiring a real ingestion decision**, not attempted this session.

`nfl.load_ff_opportunity` (2006–2025, checked live: `season < 2006` rejected) is the closest existing
proxy — per-player-per-week expected vs. actual points/yards/TDs/first-downs split by pass/rush/rec,
which implicitly captures high-value (red-zone-adjacent) opportunity via the `_exp` columns, without
being a literal red-zone share. Not yet ingested into `data/nfl.db`; noted as a cheaper near-term
alternative to a full pbp red-zone build if Backend/Strategist decide the `_exp` framing is an adequate
substitute.

## 4. Air yards and aDOT

| | |
|---|---|
| Air yards | `player_weekly_stats.receiving_air_yards` / `.passing_air_yards`, 1999–2025, **unreliable 2003–2008** (see §5) |
| aDOT (receiver) | Not a direct column pre-2016. `ngs_receiving.avg_intended_air_yards` (table already ingested, 2016–2025, 14,731 rows) gives a real per-player-per-week aDOT independent of the `receiving_air_yards`/`targets` division, and is **not** affected by the 2003–2008 charting gap since it doesn't exist for those seasons anyway. For 2009–2015, aDOT must be derived as `receiving_air_yards / targets` from `player_weekly_stats` (reliable window, per §5). |
| aDOT (passer) | `ngs_passing.avg_intended_air_yards` (table ingested, 2016–2025, 5,933 rows), same caveats. |

## 5. The known 2003–2008 hole — reconfirmed, not assumed

Re-ran the league-wide sum check directly against `player_weekly_stats` this session:

| season | SUM(targets) | SUM(receiving_air_yards) | row count |
|---|---|---|---|
| 2002 | 17,686 | 7,889 | 17,460 |
| 2003 | 3 | 55 | 17,211 |
| 2004 | 5 | 0 | 17,251 |
| 2005 | 0 | 0 | 17,334 |
| 2006 | 67 | 483 | 17,193 |
| 2007 | 14 | 76 | 17,244 |
| 2008 | 17 | 54 | 17,191 |
| 2009 | 17,546 | 144,842 | 17,669 |

Confirms the CLAUDE.md/thread-046 precedent exactly: row counts are normal all the way through
(no missing games), but `targets`/`receiving_air_yards` collapse to single digits for six straight
seasons then jump back to normal in 2009. This is present-but-effectively-zero, not absent — any
Tier 1 feature keyed on targets, target share, air-yards share, WOPR, or air-yards-derived aDOT
**must explicitly refuse 2003–2008** (`target_data_unavailable`-style flag, per the
`weekly_finishes.json` precedent in `src/export_history.py`) rather than compute a real-looking
zero. `carries` and `snap_counts`-derived features are unaffected — the hole is target/air-yards
specific, not a general charting gap for those seasons.

## 6. Tier 2 / Tier 3 — out of scope this round, noted only

- **Tier 2** (pace, PROE, O-line/D-line quality, Vegas lines): not investigated this session.
  `nfl.load_team_stats`/`load_pbp` are the likely nflverse paths for pace/PROE; Vegas lines are
  not an nflverse source and need the odds source CLAUDE.md §5 flags as still unevaluated.
- **Tier 3 — depth-chart role, the specific ask to re-check the "ends at 2024" blocker:**
  **That framing is now stale — a current-data path exists and is already ingested.**
  `src/ingest_reference.py` splits `nfl.load_depth_charts` into two tables because the source
  itself changed format mid-2025: `depth_charts_weekly` (season/week-labelled, 2001–2024, the
  table the "ends at 2024" claim refers to) and `depth_charts_snapshots` (dt-timestamped, no
  season/week, **2025-08-03 through 2026-07-26 — 349 distinct daily snapshots, already in
  `data/nfl.db`, most recent snapshot ingested yesterday**). The new format is not a proxy or a
  workaround; it's the current form of the same nflverse source, and it covers the present day,
  which is what a 2026 depth-chart role feature actually needs. No other alternative source
  (PFR depth charts, ESPN) was found or needed — this one resolves the blocker as stated.
  Tier 3 volatility/age-curve features not investigated this session.

## Ingestion status this round

No new ingestion script was written. All Tier 1 tables named above (`snap_counts`,
`player_weekly_stats`, `ngs_receiving`, `ngs_passing`, `depth_charts_weekly`,
`depth_charts_snapshots`) were already present, current (`ingested_at` within the last ~48h), and
verified against source loaders directly (not assumed from table presence). The one action item
that is genuinely new ingestion work — red-zone/goal-line usage — requires a pbp ingestion
decision (full pbp table, or the cheaper `load_ff_opportunity` proxy) that is a scope/cost call,
not a mechanical pull; flagged in the reply to thread 046 rather than started unilaterally given
the shared-DB constraint this round.
