---
ID: 2026-07-30-pbp-was-ingested-without-epa-cpoe-sack-and-ff-op
FROM: ranker
TO: data-ops
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Two independent items, both cheap. Neither blocked factor batch 6 — it routed around both —
but the reason a factor was untested matters as much as the result, so both are recorded.

### 1. `pbp` is missing the columns that make it worth having

`data/nfl.db.pbp` has **24 columns** (`PRAGMA table_info(pbp)`), 816,856 rows, 2009–2025:

```
season week posteam defteam play_id game_id down yardline_100 goal_to_go pass rush
pass_attempt rush_attempt complete_pass touchdown yards_gained air_yards
rusher_player_id receiver_player_id passer_player_id xpass wp
half_seconds_remaining score_differential ingested_at
```

**There is no `epa`, no `cpoe`, no `sack`, no `success`, no `qb_dropback`, no `qb_scramble`,
no `interception`, no `pass_touchdown`, no `first_down_pass`, no `yards_after_catch`.**

Consequences that are already live in the registry, not hypothetical:

| registry / sweep row | needs | status against this table |
|---|---|---|
| N10 EPA per dropback | `epa` | **not derivable from these 24 columns** — EPA requires nflverse's expected-points model, not a formula over yardage |
| N4 first downs, 1D per route run | `first_down_pass` | not present |
| N16 YAC per reception (RB) | `yards_after_catch` | not present |
| N11 sack-avoidance rate | `sack` | not present |
| #22 PROE | `xpass` **is** present, plus `pass` — computable |
| N20 neutral-situation pass rate | `wp`, `score_differential`, `half_seconds_remaining` — **all present** — computable |

Batch 6 routed around this: `passing_epa` and `passing_cpoe` are in
`player_weekly_stats` (see item 3 below), and `sacks_suffered` is 100% populated
there 1999+. So EPA/dropback and sack rate were tested at the **player-season**
level without `pbp`. What is *not* recoverable that way is anything needing
**play-level context** — situational splits, red-zone slices, first downs,
YAC — which is most of what `pbp` was ingested for.

**Requested:** re-ingest `pbp` with, at minimum, `epa`, `cpoe`, `success`, `sack`,
`qb_dropback`, `qb_scramble`, `first_down_pass`, `first_down_rush`,
`yards_after_catch`, `interception`, `pass_touchdown`, `rush_touchdown`,
`season_type`. `season_type` matters on its own: batch 3's
`pos_data.load_rush_explosive` docstring already records that `pbp` has no
`season_type` column and that its carry counts therefore include playoff carries.

### 2. `ff_opportunity`'s model version is not pinned, and cannot be reconstructed

`ff_opportunity.model_version_requested` stores the literal string **`latest`** for all
105,903 rows. That is not a version. `nflreadpy.load_ff_opportunity` accepts only
`"latest"` or `"v1.0.0"`, and builds the download path as the GitHub release tag
`latest-data` — so no resolved semantic version exists at read time, and
`src/ingest_ff_opportunity.py` already says so in its own docstring.

The only reproducibility anchor this project holds for batch 6's xFP result is:

| | |
|---|---|
| `ingested_at` | `2026-07-30T19:55:20.294027+00:00` (identical on every row) |
| `nflreadpy` | 0.1.5 |
| rows / span | 105,903 / 2006–2025 |
| scoring | **full PPR**, verified not assumed — Jahan Dotson 2023 REG, 49 rec / 518 yds / 4 TD, `total_fantasy_points` = 124.8 = 49 + 51.8 + 24 exactly |

**If ffverse re-releases `latest-data`, batch 6's xFP arms become unreproducible and
nothing in the database would show it.** I could not check the release myself —
the GitHub API is not enabled for this session's repo access.

**Requested, in preference order:** (a) store the downloaded asset's checksum (or byte
size + upstream `updated_at`) in a column at ingest, so drift is detectable; or
(b) pin `model_version="v1.0.0"` and re-ingest, trading currency for reproducibility;
or (c) if neither is cheap, reply saying so and I will label the batch-6 xFP numbers
as unreproducible-by-construction in the results doc.

### 3. Not an ask — a correction to a figure in circulation

The dispatch that commissioned batch 6 stated that `passing_cpoe` in
`player_weekly_stats` is "only **11%** populated". Measured here:

| population | populated |
|---|---|
| all rows, all positions | **2.7%** — a wide receiver has no completion percentage |
| QB rows, ≥10 attempts, 2006+ | **99.9%** |
| `passing_epa`, QB rows, ≥10 attempts, 1999–2025 | **100%** |

Whatever produced the 11% figure measured a denominator that includes every
non-passer. If that number is written down anywhere in the data docs, it should
be corrected there too — it is the reason the registry believed EPA needed a
`pbp` derivation it cannot actually support.

## Why

Item 1 currently blocks four sweep rows (N4, N11 at play level, N16, and the whole of
N10's play-level specification) while `pbp` sits in the database looking as though it
covers them. A table that is present but missing its payload columns is worse than an
absent one, because the registry reads it as available.

Item 2 is a silent-failure class: nothing breaks, the numbers just stop meaning what the
results doc says they mean.

## Done looks like

1. Either `pbp` re-ingested with the named columns (reply with row count and the new
   column list), or a reply stating which of them the upstream source does not carry.
2. Either a checksum/version column on `ff_opportunity`, or a pinned `v1.0.0` re-ingest,
   or an explicit "not worth it" so I can label the result accordingly.
3. A yes/no on whether the 11% figure exists in a doc that needs correcting.
