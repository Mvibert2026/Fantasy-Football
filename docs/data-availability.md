# Data Availability Map

**Every figure in this document was verified by querying the data, not by reading
documentation.** Probe scripts and raw outputs are reproducible from the queries described
in each section.

**Standing rule: every factor test must cite its true effective sample from this document.**
"nflverse goes back to 1999" is true of *outcomes* and false of nearly every *opportunity
metric*. A factor test that claims 27 seasons when its inputs start in 2009 is misreporting
its own statistical power.

Last verified: 2026-07-25.

---

## 0. The trap this document exists to prevent

Three columns in `player_weekly_stats` are **100% non-null back to 1999** and still unusable
before 2009:

| Season | `targets` (season sum) | `receiving_air_yards` (season sum) |
|---|---|---|
| 2002 | 16,853 | 7,464 |
| 2003 | **3** | 55 |
| 2004 | **5** | 0 |
| 2005 | **0** | 0 |
| 2006 | **67** | 483 |
| 2007 | **14** | 76 |
| 2008 | **17** | 54 |
| 2009 | 16,809 | 138,815 |

These are not nulls — they are **zeros**. A null check passes. A "column exists" check passes.
A feature computing prior-year target share for 2004–2009 would silently return 0.0 for every
receiver in the league and train a model on the belief that nobody was targeted.

**Root cause (inferred from the pattern, consistent across sources):** receiver *identification*
on plays is unreliable in the 2003–2008 window. Metrics requiring the intended receiver
(`targets`, `receiving_air_yards`, and everything derived from them) fail. Passing-side metrics
that need no receiver attribution (`passing_air_yards`, `cpoe`) are fine from 2006.

**Required handling:** the feature pipeline must **refuse** to serve these seasons for affected
features and raise, rather than return zeros. Imputation is not appropriate here — the data is
absent, not noisy.

---

## 1. Source-level availability

Verified via `seasons=True` on each loader, taking min/max of the season column.

| Source | First | Last | Rows | Notes |
|---|---|---|---|---|
| `load_player_stats` (weekly) | 1999 | 2025 | 476,156 | 145 columns. Column-level caveats in §2 |
| `load_pbp` | 1999 | 2025 | ~46–49k plays/season | Field-level caveats in §3 |
| `load_ff_opportunity` | 2006 | 2025 | — | **Component-level** expected values (`*_exp`). Basis for xFP (test-registry #18) |
| `load_snap_counts` | 2013 | 2025 | 324,611 | Snap share unavailable before 2013 |
| `load_participation` | 2016 | 2025 | 478,989 | Personnel packages, formation, box count |
| `load_nextgen_stats` (pass/rec/rush) | 2016 | 2025 | 5,933 / 14,731 / 6,059 | Season-aggregated, not play-level |
| `load_pfr_advstats` (rec/rush) | 2018 | 2025 | 35,724 / 18,461 | |
| `load_ftn_charting` | 2022 | 2025 | 185,215 | **4 seasons.** CC-BY-SA, attribution required |
| `load_injuries` | 2009 | 2025 | 90,752 | |
| `load_depth_charts` | 2001 | **2026** | 1,792,347 | ~~Ends at 2024~~ **CORRECTED 2026-07-25** — two stacked formats; 2025/2026 data exists but is `dt`-keyed with NULL season. See §7.2 |
| `load_rosters_weekly` | 2002 | 2025 | 906,378 | |
| `load_rosters` | 1920 | 2026 | 142,615 | 2026 present |
| `load_draft_picks` | 1980 | 2026 | 12,927 | Includes 2026 class → draft capital usable for 2026 rookies |
| `load_schedules` | 1999 | 2026 | 7,548 | 2026 schedule present → bye weeks known |
| `load_combine` | 2000 | 2026 | 8,968 | |
| `load_players` | 1974 | 2025 | 25,035 | Season col is `draft_year`; birthdate → age |
| `load_contracts` | 1983 | 2026 | 51,734 | Season col is `draft_year` |
| `load_ff_rankings` | 2020-10 | 2026-07 | — | Consensus. Preseason coverage is narrower — see §5 |

---

## 2. Column-level availability inside `player_weekly_stats`

The distinction that matters. Verified by per-season sums and non-zero rates.

| Column family | Usable seasons | Effective N | Notes |
|---|---|---|---|
| **Outcomes**: `receptions`, `receiving_yards`, `rushing_yards`, `passing_yards`, all TDs, `carries` | **1999–2025** | 27 | Fully populated. Fantasy scoring works across the whole window |
| `fumbles_lost_total`, 2pt conversions, `special_teams_tds` | 1999–2025 | 27 | |
| **`targets`**, `target_share`, opportunity share | **1999–2002, 2009–2025** | 21 (with a 6-season hole) | **2003–2008 unusable.** Do not pool across the gap without excluding it |
| **`receiving_air_yards`**, `air_yards_share`, `wopr`, `racr`, aDOT | **2009–2025** | 17 | 1999–2002 present but ~5% of modern volume — treat as unreliable, not usable |
| `passing_air_yards`, `passing_cpoe`, `pacr` | **2006–2025** | 20 | No receiver attribution needed, so unaffected by the 2003–2008 gap |
| `receiving_yards_after_catch` | **2006–2025** | 20 | Zero 2000–2005 |
| `passing_epa`, `rushing_epa`, `receiving_epa` | 1999–2025 | 27 | Populated throughout |

`racr` and `pacr` are ratios and are legitimately null when the denominator is zero (~20–25%
non-null in all seasons). That nullness is expected and is not a coverage problem.

---

## 3. PBP field availability (for derived factors)

| Field | First reliable | Enables | Notes |
|---|---|---|---|
| `yardline_100`, `down`, `ydstogo`, `pass`, `rush` | **1999** | Red-zone usage, goal-line usage, team pace, plays/game | ~93–100% populated throughout |
| `epa` | 1999 | Efficiency metrics | 99% |
| `xpass`, `pass_oe` | **2006** | **PROE** (test-registry #22) | 0% in 1999; 74–76% from 2006 |
| `air_yards`, `cp`, `cpoe` | **2006** | Play-level air yards | 34–40% (pass plays only) |

**PROE is not computable before 2006.** test-registry.md lists #22 as `nflverse`-sourced without
a date bound; its true effective sample is 20 seasons, not 27.

---

## 4. Gaps that affect the 2026 draft specifically

| Issue | Impact |
|---|---|
| ~~`load_depth_charts` ends at 2024~~ **RETRACTED 2026-07-25** | This was wrong. Depth charts **are** available for 2025 and 2026 — 348 dated snapshots from 2025-08-03 to 2026-07-25 — in a second, `dt`-keyed format with NULL season/week that the earlier `min/max(season)` check could not see. test-registry Tier 0 #5 is buildable. See §7.2 |
| FantasyPros preseason snapshots for 2026 not yet published | Latest 2026 snapshot is 2026-07-24 (in-window, usable now); August snapshots will appear closer to the draft. Re-pull before finalizing the board |
| FTN charting = 4 seasons | Any FTN-derived factor (#16, #17, #31, #32) carries a 4-season sample. Per statistical-guardrails.md §4, must not be weighted equally against a 17- or 27-season factor |

---

## 5. Consensus data coverage (bounds the ALPHA track)

`load_ff_rankings(type="all")`, `page_type == "redraft-overall"`. Preseason means an August
snapshot — the last board before Week 1.

| Season | Preseason (Aug) snapshot available? |
|---|---|
| 2020 | **No** — earliest 2020 snapshot is 2020-10-16 (in-season) |
| 2021 | Yes — 2021-08-06, -13, -20, -27 |
| 2022 | Yes — 2022-08-05, -12, -19, -26 |
| 2023 | Yes — 2023-08-04, -11, -17, -18, -22, -25 |
| 2024 | Yes — 2024-08-02, -09, -16, -23, -30 |
| 2025 | Yes — 2025-08-01, -08, -15, -22, -29 |
| 2026 | Not yet (latest 2026-07-24); expected during August |

**The alpha track has an effective sample of 5 seasons (2021–2025).** This is the binding
constraint on every alpha claim in the project:

- Per-regime alpha coefficients are **not estimable** — all five seasons sit inside a single
  modern regime (see `src/regimes.py` output).
- Season-level bootstrap (statistical-guardrails.md §7) resamples 5 units. Confidence intervals
  will be very wide, and that width is the honest result, not a defect to engineer away.
- Reserving a holdout leaves 4 development seasons.

The **accuracy track** is not bounded this way — it extends as far back as each feature's own
availability in §2/§3 allows.

---

## 6. How to cite this document in a factor test

Every factor test must state, in its result:

1. First available season for its *most restrictive* input (not its least restrictive).
2. Whether the 2003–2008 receiver-attribution gap falls inside its window, and if so that those
   seasons were **excluded**, not zero-filled.
3. Whether the test is ACCURACY_ONLY (outside consensus coverage) or eligible for an alpha claim
   (2021–2025 only).

---

# 7. Reference sources (verified 2026-07-25)

Ingested by `src/ingest_reference.py` into 11 tables, 2,320,528 rows. Every figure below was
produced by querying the ingested data. Nothing here is inferred from documentation, and
nothing is accepted on the basis of a column merely existing.

**Method note.** For each source: season span, interior gaps, non-null rate, and a
plausibility check on the *distribution* of non-null values. The last of these is the one
that matters — the 2003-2008 targets hole (§0) was 100% non-null and 100% wrong.

## 7.0 Key design, and why two tables have surrogate keys

Primary keys were verified for nullability and uniqueness before being chosen. Results:

| Table | Key | Verdict |
|---|---|---|
| `injuries` | `(season, game_type, team, week, gsis_id)` | Clean: 0 nulls, 2 duplicate groups (deduped on latest `date_modified`) |
| `snap_counts` | `(game_id, pfr_player_id)` | Clean: 0 nulls, 0 duplicates |
| `ngs_receiving/rushing/passing` | `(season, season_type, week, player_gsis_id)` | Clean: 0 nulls, 0 duplicates |
| `draft_picks` | `(season, round, pick)` | Clean: 0 nulls, 0 duplicates |
| `combine` | `(season, player_name, pos)` | Clean. **`pfr_id` cannot be used — 1,531 nulls** |
| `ff_playerids` | `(mfl_id)` | Clean: 0 nulls, 0 duplicates |
| `depth_charts_weekly` | **surrogate `row_hash`** | No natural key exists: `week` has 5,736 nulls and the best candidate still duplicates 5,346 times |
| `depth_charts_snapshots` | **surrogate `row_hash`** | No natural key exists: `gsis_id` has 8,038 nulls |
| `contracts` | **surrogate `row_hash`** | No natural key exists: multiple contracts per player-year, 9,809 duplicate `(otc_id, year_signed)` groups |

The surrogate is a SHA-1 of the row's content, so re-ingestion is idempotent. A side effect
worth recording: it collapses **exactly duplicated source rows** — 3,330 in `contracts` and
3,856 in `depth_charts_weekly`. Those are genuine duplicates in the upstream data, not a
processing artifact.

## 7.1 Injuries — practice participation vs game designation

**This was the specific question, and the two fields have opposite availability profiles.**

| Field | What it is | Usable from |
|---|---|---|
| `practice_status` | DNP / Limited / Full participation | **2009 — effectively complete throughout** |
| `report_status` | Out / Doubtful / Questionable (/ Probable pre-2016) | 2009, but see the collapse below |

Non-null-and-non-blank rate by season:

| Season | practice_status | report_status | `Probable` count |
|---|---|---|---|
| 2009-2015 | 100% | 93.9-97.3% | 1,874-2,963 per season |
| 2016 | 100% | **60.2%** | **0** |
| 2017 | 100% | **50.6%** | 0 |
| 2018-2024 | 99.2-100% | 44.8-48.6% | 0 |
| 2025 | 99.3% | 45.9% | 0 |

**The mechanism, and why it is a trap.** The `Probable` designation appears 17,400 times
through 2015 and **exactly zero times from 2016 onward** — the NFL abolished it after the
2015 season. Players who would have been listed Probable now appear on the report with a
practice status and **no game designation at all**. That is the entire cause of the
`report_status` collapse from ~95% to ~46%.

So a NULL `report_status` means two different things either side of 2016:

- **Pre-2016 (~5% of rows):** genuinely not designated.
- **Post-2016 (~55% of rows):** on the injury report, practised in some capacity, healthy
  enough that no designation was required — roughly the old `Probable`.

A health model that reads NULL as "not injured" will misclassify **over half** of all
post-2016 injury-report rows, and one trained across the boundary will see a step change in
"designation rate" that is purely administrative. **Use `practice_status` as the primary
health signal**: it is complete across the entire 2009-2025 window and its meaning did not
change.

**Value-set contamination** (non-null but meaningless — the §0 lesson):

- `practice_status` contains 213 whitespace-only (`'\n    '`) values and 1 literal `'Note'`.
- `report_status` contains 6 `'Note'` values.
- `practice_status` includes `'Out (Definitely Will Not Play)'` (974 rows), which is a *game*
  outcome appearing in a *practice* field. It does not occur after 2019.

Filter on `TRIM(practice_status) NOT IN ('', 'Note')` rather than `IS NOT NULL`.

**Coverage:** 2009-2025, no interior gaps, 90,750 rows. Includes postseason (`game_type` in
REG/WC/DIV/CON/SB); REG covers weeks 1-18. `date_modified` is a genuine timestamp and is
retained as the `as_of_date` for this table.

## 7.2 Depth charts — two stacked formats (corrects §4)

`load_depth_charts` returns **two incompatible datasets in one frame**, split on ingest:

| Table | Rows | Coverage | Key columns populated |
|---|---|---|---|
| `depth_charts_weekly` | 865,329 | **2001-2024**, season/week labelled, no interior gaps | `club_code`, `depth_team`, `formation`, `depth_position`, `position`, `full_name`, `elias_id`, `jersey_number` — all 100% |
| `depth_charts_snapshots` | 923,162 | **2025-08-03 → 2026-07-25**, `dt`-timestamped, season/week NULL | `team`, `player_name`, `pos_rank`, `pos_slot`, `pos_abb`, `pos_grp`, `espn_id`, `dt` |

The two formats share almost no columns: every "new format" column is **0.0% populated in
every season 2001-2024**, and every "old format" column is NULL in the snapshot rows. Stacking
them would have produced a table that is half-null in every row.

**This corrects the earlier claim that depth charts end at 2024.** They do not. The 2025/2026
data exists as **348 distinct dated snapshots**, roughly 25-31 per month, all 32 teams present
in every month. That earlier conclusion came from `min/max(season)`, which cannot see rows
whose season is NULL — the same failure mode as §0, in a different disguise.

For the draft this is *better* than the old format: dated snapshots are exactly what a
date-parametrised board needs (`docs/deferred.md` P3-2), because a snapshot's `dt` is a true
`as_of_date` rather than an inferred week boundary.

Caveats: 8,038 snapshot rows have a NULL `gsis_id` (unmatched players); `depth_charts_weekly`
has 5,736 NULL-week rows, ~220-270 per season plus 1,593 in 2001.

## 7.3 Snap counts

**2013-2025, no interior gaps, 324,611 rows.** Plausibility: `offense_pct` ranges exactly
[0.0, 1.0] in every season — it is a **fraction, not a percentage**, which is an easy
off-by-100x error. Season mean is stable at 0.236-0.247. `offense_snaps` maxima are 90-100 per
game, which is right for a team's offensive play count. No degradation or regime shift.

## 7.4 Next Gen Stats — and an interior gap inside a column

**All three tables: 2016-2025, no interior season gaps.** Volumes are small — 14,731 receiving
/ 6,059 rushing / 5,933 passing rows — because these are weekly aggregates over qualifying
players only, not full rosters.

Plausibility checks all pass:

| Metric | Observed range | Plausible? |
|---|---|---|
| `avg_separation` (rec) | season means 2.70-3.12 yd | Yes |
| `avg_cushion` (rec) | season means 5.71-6.24 yd | Yes |
| `avg_time_to_throw` (pass) | season means 2.65-2.85 s | Yes |
| `efficiency` (rush) | season means 4.15-4.64 | Yes |

**Interior gap inside a column:** `rush_yards_over_expected` (and the `_per_att` and
`rush_pct_over_expected` variants) are **100% NULL for 2016 and 2017**, then fully populated
from 2018. The column exists for the table's whole span; the data starts two years later.
**RYOE-based features have an effective sample of 2018-2025 (8 seasons), not 2016-2025.**

Note also a real trend rather than an artifact: `avg_separation` rises steadily from 2.70
(2016) to 3.12 (2024). Worth a factor test, not a data-quality concern.

## 7.5 Contracts

**48,404 rows after collapsing 3,330 exact duplicates.** `year_signed` spans 1980-2026 with no
interior gaps in that range — **but 1,106 rows carry `year_signed = 0`**, a sentinel for
unknown. Non-null, numeric, and meaningless: exactly the §0 pattern. Filter
`year_signed > 0`.

`apy` plausibility by signing year: mean $1.0-2.6M, maximum rising 18.0 (2010) → 64.0 (2026),
which tracks real cap growth. Only 0-28 zero/null `apy` values per year.

`gsis_id` is NULL for 4,194 rows, so contracts cannot be joined to player stats for those.
The nested `cols` column (per-year cap detail) is **JSON-encoded on ingest** and needs a parse
on read — recorded here so it isn't later mistaken for a plain string.

## 7.6 Combine

**2000-2026, no interior gaps, 8,968 rows.** `forty` times span [4.21, 6.00] with season means
4.67-4.81 — plausible throughout.

**Coverage declines materially over time**, which matters more than the span: ~99% of
attendees have a `forty` through 2016 (e.g. 331/332 in 2016), falling to 201/329 in 2025 and
**189/319 in 2026 (59%)**. Prospects increasingly skip the 40 at the combine. Any
combine-athleticism feature must handle a missingness rate that is both large and trending,
and missingness is unlikely to be random — it plausibly correlates with draft stock.

## 7.7 Draft picks

**1980-2026, no interior gaps, 12,927 rows.** Structure matches real draft history and is a
good plausibility signal: 12 rounds and ~333 picks per year through 1992, 8 rounds in 1993,
then 7 rounds and 222-262 picks from 1994 onward.

`gsis_id` coverage rises from ~60-65% in the 1980s to essentially 100% from 2018. For 2026 it
is 230/257 (89%) — IDs are still propagating for the most recent class. Draft-capital features
for rookies are safe from ~2000 onward; earlier seasons will silently lose the players whose
IDs are missing.

## 7.8 ff_playerids (cross-source ID map)

**12,468 rows, keyed on `mfl_id` (unique, no nulls).** Coverage of each foreign key:

| ID | Coverage |
|---|---|
| `pfr_id` | 76.8% |
| `espn_id` | 65.3% |
| **`gsis_id`** | **62.1%** |
| `sportradar_id` | 59.6% |
| `sleeper_id` | 50.9% |
| `yahoo_id` | 44.0% |
| `fantasypros_id` | 38.3% |

**`gsis_id` is not unique here: 10 values map to more than one `mfl_id`.** Inspection shows
these are genuinely different players sharing an ID — e.g. `00-0029435` is attached to both
"Damaris Johnson" (WR) and "Dennis Johnson" (DE). Any join on `gsis_id` must be checked for
row multiplication, and these ten will produce wrong matches. Since `gsis_id` is the join key
between this crosswalk and `player_weekly_stats`, **38% of the crosswalk cannot be joined to
NFL stats at all**, and a handful of the remainder join incorrectly.

## 7.9 Coaching staff — BLOCKED, reported and not worked around

`coach_id` (test-registry #29 coordinator continuity, #30 first-time play-callers) needs
coordinator-level data. Status:

**Pro Football Reference is not cleanly obtainable.** Both `https://www.pro-football-reference.com/robots.txt`
and their terms page return **HTTP 403 Forbidden** to programmatic requests. The site actively
blocks automated access, and I could not even read the crawl policy to determine what it
permits. Building a scraper would mean circumventing an active block. Per CLAUDE.md §10
("check terms before building the scraper, not after") and the explicit instruction not to
work around it: **not attempted, and this gates the coordinator dimension.**

**Partial win found instead.** `nflreadpy.load_schedules()` carries `home_coach` and
`away_coach`: **1999-2026, 15,096 team-games, 100% populated, zero nulls, 177 distinct
coaches.** Structurally sound — 850 team-seasons have exactly one coach, 43 have two
(in-season changes), and none have three or more.

This gives a clean, licensed **head coach** dimension for the full modern era. It does **not**
give offensive or defensive coordinators, which is what #29/#30 actually require, since the
whole point of those tests is that coordinators move between teams. Head-coach continuity is a
weaker proxy but is buildable today at zero licensing risk.

**Unverifiable from the pipeline:** the 2026 coach assignments in this data (e.g. Jesse Minter
at BAL, Robert Saleh at TEN, John Harbaugh at NYG) cannot be checked against anything in the
repo, and I have no reliable way to confirm current NFL hires. **Spot-check them before any
2026 coach-based feature is trusted.**

## 7.10 Summary — what changed for downstream work

1. **Use `practice_status`, not `report_status`, as the health signal.** The latter's meaning
   changes at 2016 and it is ~46% populated after that.
2. **Depth charts are available for 2026** (§7.2 corrects §4). Use `depth_charts_snapshots`
   and its `dt` as a true `as_of_date`.
3. **RYOE starts in 2018**, not 2016 — 8 seasons, not 10.
4. **Combine `forty` missingness is ~41% for 2026** and trending upward, probably not at random.
5. **`gsis_id` joins are lossy (62%) and slightly wrong (10 collisions).**
6. **Coordinator data remains blocked**; head coach is available 1999-2026 as a partial substitute.

---

# 8. Two targeted verifications (2026-07-25)

Both were run because a downstream decision rested on an unmeasured assumption.

## 8.1 Does the season-labelled depth chart carry a real `week`?

**Yes — it is a genuine weekly snapshot, not a retroactive season roll-up.** This was the
specific concern (guardrails §1 names retroactively-assigned starter flags as a disguised form
of look-ahead), and the data clears it:

| Check | Result |
|---|---|
| Distinct weeks per season | **21–22** (17 in 2005) |
| Week range | 1–22, covering REG through SB |
| Players whose `depth_team` changes across weeks, 2023 | **753 of 2,007 (37.5%)** |
| Players whose `depth_position` changes across weeks, 2023 | 486 |
| Rows with NULL `week` | 5,736 — **all of them `game_type = 'SBBYE'`** (Super Bowl bye, which has no week). Not corruption. |

Depth position genuinely moves during a season, so a week-N chart reflects week-N belief.
**Registry #5 is buildable for in-season use across 2001–2024.**

### But it is NOT buildable for a DRAFT feature, for two separate reasons

**1. There is no preseason chart.** `game_type` takes only REG / WC / DIV / CON / SB / SBBYE.
The earliest available chart is REG week 1, published days before week-1 games — i.e. *after*
a late-August draft. Using it as a pre-draft feature is look-ahead, marginal but real.

**2. The dated snapshot format has ZERO development-set coverage.** Snapshots carry a true
`dt` and would be ideal for a pre-draft feature, but:

```
rows with dt < 2025-01-01 : 0
earliest snapshot         : 2025-08-03
```

Development seasons are 2021–2024. The snapshot series begins inside the **locked holdout
season** and continues into 2026. So the format that *could* support a look-ahead-safe
pre-draft depth-chart feature cannot be validated on any development season.

**Net: registry #5 is usable live for the 2026 draft (via snapshots) but cannot be validated
before use.** Any 2026 depth-chart feature is an untested assumption, and should be labelled
that way rather than treated as a backtested factor.

## 8.2 Join coverage per leg

The 98.9% figure recorded earlier is for `fantasypros_id → gsis_id` **only**. The other legs
were unmeasured; at least one proposed factor (snap share) rests entirely on the second.

### Leg A — `depth_charts_weekly.gsis_id → player_weekly_stats.player_id`

| Season | Distinct ids | Non-null | Matched to stats | Coverage |
|---|---|---|---|---|
| 2021 | 2,154 | 2,154 | 1,982 | **92.0%** |
| 2022 | 2,073 | 2,073 | 1,915 | **92.4%** |
| 2023 | 2,007 | 2,007 | 1,850 | **92.2%** |
| 2024 | 2,054 | 2,054 | 1,895 | **92.3%** |

`gsis_id` is non-null on **all 865,329 rows** (0.00%). The ~8% shortfall is players on a depth
chart who record no stat line in that season — mostly backups who never took a snap, which is
a real absence rather than a join failure.

### Leg B — `snap_counts.pfr_player_id → ff_playerids.pfr_id → gsis_id`

This is the leg snap-share features depend on entirely, and it is the weakest.

| Season | Snap ids | Resolve to gsis_id | Reach stats |
|---|---|---|---|
| 2021 | 2,301 | 1,889 (82.1%) | 1,798 (**78.1%**) |
| 2022 | 2,196 | 1,792 (81.6%) | 1,720 (**78.3%**) |
| 2023 | 2,145 | 1,739 (81.1%) | 1,653 (**77.1%**) |
| 2024 | 2,192 | 1,782 (81.3%) | 1,706 (**77.8%**) |

**Restricted to the positions actually modelled (QB/RB/WR/TE), it is much better:**

| Season | Skill snap ids | Reach stats |
|---|---|---|
| 2021 | 677 | 631 (**93.2%**) |
| 2022 | 634 | 604 (**95.3%**) |
| 2023 | 621 | 572 (**92.1%**) |
| 2024 | 620 | 586 (**94.5%**) |

The headline 78% is dragged down by linemen and defensive players, who are irrelevant here.
The number that matters for a snap-share factor is **92–95%**, with 5–8% of skill players
still unjoinable in any given season.

### Summary of measured legs

| Join | Coverage | Status |
|---|---|---|
| `fantasypros_id → gsis_id` | 98.9% | previously measured |
| `depth_chart gsis_id → stats` | 92.0–92.4% | **measured 2026-07-25** |
| `pfr_player_id → gsis_id → stats` (all positions) | 77.1–78.3% | **measured 2026-07-25** |
| `pfr_player_id → gsis_id → stats` (QB/RB/WR/TE) | 92.1–95.3% | **measured 2026-07-25** |

**Any feature built on leg B must state 92–95% coverage and refuse the unresolved rows rather
than dropping them silently** — a silent drop is non-random, since unjoinable players skew
toward fringe roster spots, which is exactly where role changes happen.
