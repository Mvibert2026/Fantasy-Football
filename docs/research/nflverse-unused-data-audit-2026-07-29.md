# nflverse unused-data audit — 2026-07-29

**Method:** enumerated every `load_*` function actually exported by `nflreadpy==0.1.5` (the pinned
version in `requirements.txt`), called each one that a documentation-only pass would not have
caught, and inspected real columns/row counts. Not a documentation summary — every number below
was measured against a live loader call or a query against `data/nfl.db` in this worktree
(copied in from the main checkout per `docs/environment.md` §4; original in this worktree was a
0-byte stub).

## Conclusion first

**Three things worth pulling, in priority order:**

1. **`load_schedules()` — `home_coach` / `away_coach` columns.** Head-coach name per game,
   1999–2026 (2026 preseason schedule already populated), 7,548 rows, **zero nulls** in every
   season checked. This is real coach identity, resolved at game granularity (so a mid-season
   firing shows up correctly, unlike a season-level table). **Partially closes the coaching
   gap** — see caveat below.
2. **`load_participation()` — the `route` column plus `offense_players`.** Play-level data,
   2016–2025 (`participation` files don't exist before 2016), ~46–48K plays/season. `route` names
   the route type run by the targeted receiver on each pass play; `offense_players` lists all 11
   offensive players on the field for every play. Counting plays-with-a-route-tag against
   plays-on-field-during-dropbacks per player, per game, is a legitimate proxy for **route
   participation rate** (test-registry #17) and, combined with receiving yards, **yards per route
   run** (test-registry #16). This is a real, if effortful, close of a chunk of the route gap.
3. **`load_ff_opportunity()`** — pre-computed expected-fantasy-points model (target share,
   air-yards share, completion/TD probability vs. actual), 2006–2025, 159 columns, ~5,200–6,100
   rows/season. Not raw data — it is itself somebody else's fitted model (`ffopportunity`
   package), so feeding it into a proprietary ranking model risks stacking one model's priors
   inside another's (worth a Statistician call, not a Data Ops one). Flagging it because the
   *actual vs. expected* delta it carries is exactly the "luck vs. skill" signal §6 cares about,
   and it is free and already licensed.

**Does anything here reduce the coaching gap?** Partially, not fully. `home_coach`/`away_coach`
gives verified, dated **head-coach** identity only. It does **not** give offensive/defensive
coordinator or actual **play-caller** identity — the exact gap `src/ingest_play_callers.py`
exists for (HC often is not the play-caller; see that file's own Cleveland 2025 example,
Stefanski→Rees). That file remains correctly parked: nothing in nflreadpy supplies play-calling
duty, so the ESPN-roundup completion trigger it already names is still the right plan. Head-coach
identity is still useful on its own (coaching tenure/system continuity, `coaches` /
`coaching_staff_seasons` in the target schema, CLAUDE.md §4), just not sufficient by itself.

**Does anything here reduce the route gap?** Yes, materially. CLAUDE.md §5 says route data
"needs NGS or a documented proxy calculation. Flag clearly if proxied." `load_participation`
*is* that documented proxy — nflverse ships it, we simply never ingested it. The three
already-ingested NGS tables (`ngs_receiving`/`ngs_rushing`/`ngs_passing`, verified by schema
below) carry **no route or route-participation column at all** — `avg_cushion`,
`avg_separation`, `avg_intended_air_yards`, target/reception counts, YAC — so the project's
existing claim that routes are "not directly in nflverse" for the NGS tables specifically is
still accurate; the miss was not checking `load_participation`.

---

## 1. Full nflreadpy loader inventory (0.1.5)

```
load_combine            load_draft_picks        load_ff_rankings         load_officials
load_contracts          load_ff_opportunity      load_ffverse             load_participation
load_depth_charts       load_ff_playerids        load_injuries            load_pbp
load_pfr_advstats       load_player_stats        load_players             load_rosters
load_rosters_weekly     load_schedules           load_snap_counts         load_stats
load_team_stats         load_teams               load_trades
```
23 loaders total.

## 2. Currently ingested (measured against `data/nfl.db`, 22 tables)

`src/ingest_reference.py` pulls: `injuries`, `depth_charts_snapshots`/`depth_charts_weekly`
(both formats of `load_depth_charts`), `snap_counts`, `ngs_receiving`/`ngs_rushing`/`ngs_passing`
(three calls to `load_nextgen_stats`), `draft_picks`, `combine`, `contracts`, `ff_playerids`.
`src/ingest_weekly_stats.py` pulls `load_player_stats(summary_level="week")` →
`player_weekly_stats`.

Row counts / coverage measured directly:

| Table | Rows | Seasons |
|---|---|---|
| `ngs_receiving` | 14,731 | 2016–2025 |
| `ngs_rushing` | 6,059 | 2016–2025 |
| `ngs_passing` | 5,933 | 2016–2025 |
| `snap_counts` | 324,611 | 2013–2025 |
| `draft_picks` | 12,927 | 1980–2026 |
| `combine` | 8,968 | 2000–2026 |

`ngs_receiving` schema (checked column-by-column): `avg_cushion`, `avg_separation`,
`avg_intended_air_yards`, `percent_share_of_intended_air_yards`, `receptions`, `targets`,
`catch_percentage`, `yards`, `rec_touchdowns`, `avg_yac`, `avg_expected_yac`,
`avg_yac_above_expectation` — no route field. Confirms CLAUDE.md's route-data note is accurate
for the tables actually held today.

`src/ingest_play_callers.py` — **parked, zero rows, no table exists in `data/nfl.db`** (queried
directly: `no such table: play_callers`). It is a hand-fed CSV validator with a documented
completion trigger (ESPN's annual 32-team play-caller roundup, late August), not an nflverse
loader — confirms it does not touch nflreadpy at all and does not close any part of the gap on
its own; it is waiting on an external source, same as before this audit.

## 3. Loaders never called by this repo — findings

| Loader | Seasons checked | Rows (sample) | Columns of note | Verdict |
|---|---|---|---|---|
| `load_schedules` | 1999–2026, full pull | 7,548 total; 285 (2023) | `home_coach`, `away_coach`, `stadium`, `stadium_id`, div/game-type flags | **Pull.** Real, dated HC identity, free, zero nulls checked. |
| `load_participation` | 2016, 2017, 2020, 2023–2025 | 45–48K plays/season | `route`, `offense_players`, `defense_players`, `n_offense`, `time_to_throw`, `was_pressure`, `defense_coverage_type` | **Pull.** Play-level; needs aggregation work (Backend, not Data Ops) to become a per-player route-participation metric. Not available before 2016. |
| `load_ff_opportunity` | 2006, 2016, 2020, 2025 | ~5,200–6,100/season | Actual vs. expected for every scoring category, team-level splits too | **Worth having, needs Statistician sign-off** before use as a ranking input — it's a fitted model's output, not raw counts. |
| `load_rosters_weekly` | 2023 | 45,655 | `status`, `week`, `status_description_abbr`, full player-ID crosswalk | Marginal. `status`/`week` gives a genuine as-of-date active-roster flag (helps §6.2 survivorship universe construction) but overlaps heavily with `injuries`/`depth_charts_weekly` already held. Not top-3, but cheap if ever needed. |
| `load_ftn_charting` | 2023 | 48,225 | Formation, personnel, motion/play-action/RPO/screen flags, pressure/coverage charting | No route-participation or routes-run field despite test-registry #16/#17 naming FTN as the place to check — **that pointer in the test registry is stale/wrong**; the real proxy is `load_participation`, not FTN. FTN itself may still be useful later for play-calling-tendency factors (motion rate, PA rate), out of scope for this audit. |
| `load_pfr_advstats` | 2023, week level | 700 | Drop rate, bad-throw rate, pressure/blitz/hurry counts | Passing/pressure efficiency detail, thin coverage, not obviously additive over existing NGS/PBP data. Low priority. |
| `load_team_stats` | 2023, week level | 570 | 133 team-level aggregate columns | Team-level, not player-level; plausible future input for the opponent model, out of scope for a player-ranking gap-closer. |
| `load_officials` | full pull | 21,900 | Referee assignments per game | No plausible player-ranking use. Skip. |
| `load_trades` | full pull | 4,975 | Trade transactions | Roster-context, not ranking-relevant on its own. Skip. |
| `load_ff_rankings` | attempted | — | — | **Blocked, not skipped**: `403 Forbidden` fetching `github.com/dynastyprocess/data` through the proxy. Recorded as blocked per source-terms discipline; not retried with any workaround. If pulled later it is expert consensus (`ranking_source=expert`), judge-only, never a training input. |
| `load_players`, `load_rosters` | not deep-checked | — | Static player/roster attribute tables | Overlaps `ff_playerids`/`load_rosters_weekly` already assessed; no distinct new signal identified. |
| `load_combine`, `load_contracts`, `load_draft_picks`, `load_injuries`, `load_depth_charts`, `load_snap_counts`, `load_player_stats`, `load_nextgen_stats` | — | — | Already ingested (§2). |
| `load_pbp`, `load_stats`, `load_ffverse` | — | — | `load_pbp` is the raw play-by-play the other tables are already derived from — no new signal beyond what's aggregated; `load_stats` is a generic dispatcher over already-ingested sources; `load_ffverse` is a manifest/meta helper, not a dataset. |

## 4. What this does not do

This audit does not ingest anything. No new tables were written to `data/nfl.db`. The three
recommended pulls (`load_schedules` coach columns, `load_participation`, `load_ff_opportunity`)
are each a deliberate follow-up decision for whoever owns that backlog item next — Data Ops for
the mechanical ingest of `load_schedules`/`load_participation`, Backend/Statistician for whether
`load_ff_opportunity` is safe to feed into a ranking model without violating the "one model
inside another" concern above.
