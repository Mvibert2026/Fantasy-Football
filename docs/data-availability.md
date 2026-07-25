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
| `load_depth_charts` | 2001 | **2024** | 1,792,347 | **Ends at 2024 — no 2025 or 2026 data.** See §4 |
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
| `load_depth_charts` ends at **2024** | No depth-chart feature is available for the 2026 draft. test-registry Tier 0 #5 ("Depth chart / role") is **not buildable** for the live objective unless another source is found |
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
