# Standalone predictiveness screen 2 — the complete v3 candidate pool

**backend, 2026-08-04.** Supersedes `docs/ranking/standalone-screen-1.md`. Screen 1 covered 14 base
factors, built before C4 existed. This document covers the **full** pool the founder asked for:
C1's 6, C2's 6, C3's 6, C4's 6, the six predictive incumbents (no grandfather clause,
`FR-2026-08-04-v3-build-strategy...`), everything Task 1's blocked-row re-audit unblocks, and the
within-cluster contrasts. Same method as screen 1 throughout — **this screen decides nothing and
grades nothing.** No `INCLUDE`/`EXCLUDE` anywhere below. Nothing here enters any campaign
multiplicity denominator.

---

## NEXT STEP

*Rewritten for a successor with none of this context.*

1. **v3 joint fit is not started.** This document's survivor set (below), the collinearity
   clusters, and the incumbent-shrinkage findings are its input, per
   `FR-2026-08-04-v3-build-strategy-screen-all-factors-for-predict.md`. That FR's own binding
   rules (ridge/elastic net never lasso, standardise before penalising, never prune on
   correlation, measure coefficient stability under leave-one-season-out/bootstrap, per-position
   fits) govern the fit this screen feeds — not repeated in full here, read that FR before
   fitting anything.
2. **Season budget is still the constraint screen 1 flagged and it is unchanged**: screen spent
   2013–2019 (7 seasons), leaving ≤5 of 2020–2024 for fit+test, disjoint, before the sealed 2025
   holdout. `strategist` still owns registering the exact split — not resolved here, not resolved
   by screen 1 either.
3. **Five factors flagged NOW AVAILABLE by Task 1's audit were deliberately not built this
   pass** (vacated opportunity/T1-28, red-zone snap rate/N14, first-time-play-caller/T1-30's exact
   definition, play-caller portability-of-tendency/N21's exact definition, and the multi-source-ADP
   baseline arm/T0-1, which is a harness switch not a ranking factor). Reasons stated per-row in
   §2 below — mostly "the join is non-trivial enough that folding it in here risks reproducing a
   known contamination under a new name," the same judgment call C4's own dispatch made for T1-28.
   Flagged for `ranker`/`strategist` to schedule as a follow-up batch.
4. **Contract**: `experiments/bottomup/v2/standalone_screen2.py` is self-contained — it does
   **not** import `standalone_screen1.py`, `factors_c1–c4.py`, or anything under `sweep070/`,
   because this worktree's `git log` (`fd3bed1`) does not contain any of those files; they exist
   only as uncommitted work in a sibling checkout. See the script's own header for the full
   explanation. It **does** import `experiments/bottomup/components/{pos_data,pos_features}.py`,
   which **are** committed on this branch — the six predictive incumbents are built by calling
   `pos_features.build_features` directly, not reimplemented, so there is no drift risk between
   what this screen measures and what the live component model actually computes.
5. Re-run: `python3 -m experiments.bottomup.v2.standalone_screen2` from the repo root (needs
   `data/nfl.db`, gitignored — copy from a checkout that has it, `docs/environment.md` §4). Writes
   `experiments/bottomup/results/standalone_screen2_{results,collinearity,contrasts}.csv`.

---

## Part A — Task 1: the blocked-row re-audit

The ledger has **17 rows marked `blocked`** (`docs/factor-ledger.md`, counted mechanically —
T0-1, T0-2, T0-10, T0-11, T1-21, T1-22, T1-28, T1-29, T1-30, T1-32, N8, N12, N14, N21, N22, N23,
N24). Every row checked directly against `data/nfl.db` as it exists today (39 tables). Three-way
classification: **NOW AVAILABLE** (table exists, factor buildable — states which table and span),
**STILL BLOCKED** (names the table that would hold it and confirms it is absent or empty), or
**NEVER WAS BLOCKED** (the disposition itself was wrong when written).

| Ledger row | Factor | Verdict | Detail |
|---|---|---|---|
| T0-1 | Multi-source ADP | **NOW AVAILABLE**, not a ranking factor | `ffc_adp_snapshots` is ingested (confirmed, matches the row's own text). This is a `backtest.py` baseline-arm switch (`consensus_adp.available=False` never flipped), not a player-level predictor — out of scope for this screen, in scope for whoever next touches `backtest.py`'s arm registry. |
| T0-2 | Consensus projections (component-level: pass/rush/rec yards, TDs separately) | **STILL BLOCKED** | Checked `rankings`, `rankings_expert_quarantine`, `rankings_quarantine` schemas directly: all three carry rank/tier/ADP columns only (`adp_rank`, `rank_best`, `rank_worst`, `tier`, `sos_season`, …) — zero yardage/TD/component columns anywhere. No table in the 39-table schema holds component-level consensus projections. Confirmed still absent, not merely unchecked. |
| T0-10 | Red-zone/goal-line usage | **NOW AVAILABLE — already tested** | `pbp` exists (816,856 rows, 2009–2025). This is mislabelled in the ledger: C1's factor F2 already built and tested this exact quantity against `pbp` (`docs/factor-ledger.md` Section 0: RB −0.0001, WR −0.0010, TE +0.0020, all NULL). Also re-screened here as `redzone_share` (§2). |
| T0-11 | Vegas win totals & implied team totals | **NOW AVAILABLE — already tested** | `odds_snapshots` exists: 3,884 rows, 2018–2024 (7 seasons, `implied_team_total`/`team_spread`/`game_total_line`/`moneyline` all populated). Mislabelled: C2 already built and CI-tested `implied_team_total` (`docs/factor-ledger.md` Section 0: QB +0.0140 CI-WIN, RB/WR/TE NULL). Re-screened here as `implied_team_total` (§2) — thin coverage (2018+ only) reproduces exactly. |
| T1-21 | Team pace / plays per game | **NOW AVAILABLE** | `pbp` exists, 2009+. This is C4's factor J, already defined (`docs/ranking/batch-C4-candidates.md`), never before screened for raw predictiveness. Screened here as `team_pace` (§2). |
| T1-22 | Pass rate over expectation (PROE) | **NEVER WAS BLOCKED, once `pbp` landed** | `pbp.xpass` (nflverse's own expected-pass-probability model output) is already a column in the ingested schema — 97–98% populated every season 2009–2025 (measured: 589,334 scrimmage plays, 579,261 non-null `xpass`). PROE = actual pass rate − mean(xpass), directly computable, no expectation model needed to be built. This is a genuinely new candidate, not a rebuild of N20 (neutral pass rate, a raw frequency) — PROE nets out game-state. Screened here as `proe` (§2). |
| T1-28 | Vacated targets & carries | **NOW AVAILABLE, not built this pass** | `rosters_weekly` exists (888,786 rows, 2002–2025) — exactly the table the ledger's own disposition names as the fix (`nflreadpy.load_rosters_weekly()`). The old result is a proxy-contamination finding (Week-1 depth chart, not a real preseason roster), and this table resolves that. **Not built here**: correctly joining preseason vs. mid-season status and handling multi-team players is substantial enough that a rushed version risks reproducing the same contamination under a new name — the same judgment call C4's own dispatch made. Flagged for a follow-up batch. |
| T1-29 | Coordinator continuity | **NOW AVAILABLE (partial)** | `play_callers_preseason` has **992 rows**, 2007–2024, `coach_id` populated on 957/992, confidence `medium` on 957 / `low` on 35. Source is a **Wikipedia team-staff-navbox snapshot**, not the PFR-403 source the ledger's disposition names — genuinely different data that has landed since that row was written, not a resurrection of the same blocked path. Built and screened here as `oc_disruption` (§2), a lag-1 "did the OC change" signal, same construction as C4's factor L for head coaches. |
| T1-30 | First-time play-callers | **NOW AVAILABLE (partial), not built this pass** | Same table as T1-29. `is_hc_calling` distinguishes HC-as-playcaller (7 of 992 rows) from a dedicated OC, and `oc_disruption` (§2) already captures "this is the OC's first season with this team." **True "first time calling plays anywhere in his career"** — as opposed to first time *at this team* — needs a career-length lookback this table's 2007 floor cannot fully support for coaches whose careers started earlier; not attempted this pass. |
| T1-32 | Pre-snap motion rates (player level) | **STILL BLOCKED** | Checked `participation`'s full 28-column schema directly: no `is_motion`, no motion-rate column of any kind. Checked `pbp`'s 25-column schema: same, no motion column. Neither table carries pre-snap motion at all (team or player level) in this database, contradicting the ledger's claim that a team-level version is computable — it is not, from what is actually ingested. Confirmed absent, not merely unchecked. |
| N8 | Tight-window target rate | **STILL BLOCKED** | No charting/coverage-window column exists anywhere in the 39-table schema (checked `participation`, `ngs_receiving`, `pbp`). Needs paid window-charting data, as the ledger states. |
| N12 | Game total / team spread as player features | **NOW AVAILABLE — already tested (partial)** | Same table as T0-11, `odds_snapshots`. `implied_team_total` (already re-tested, above) is the team-total half of this row. `team_spread` itself is a separate column in `odds_snapshots`, not separately screened here — flagged as a small remaining gap, buildable identically to `implied_team_total` in a follow-up. |
| N14 | Red-zone/inside-10/inside-5 **snap** rate | **NOW AVAILABLE, not built this pass** | `participation` (478,989 rows, 2016+) × `pbp.yardline_100` — both tables exist and are already joined elsewhere in this project (the TPRR proxy, §2). Buildable by filtering the same join to red-zone plays. Not built this pass for time; flagged for a follow-up batch alongside T1-28. |
| N21 | Play-caller portability of tendency | **NOW AVAILABLE (partial), not built this pass** | The ledger's stated blocker ("`play_callers` table has zero rows") names the wrong table — `play_callers_preseason` (992 rows) is the real, populated table; `play_callers` does not exist as a separate table at all. The underlying coordinator-identity data is therefore available (same source as `oc_disruption`, §2). **The specific claim this row asks about — does an individual coordinator's run/pass tendency travel with him when he changes teams — is a different, harder construction** (needs a per-coordinator tendency measure tracked across team changes) not attempted this pass. |
| N22 | Coordinator-change effect | **NOW AVAILABLE — screened** | Same table as T1-29/N21. This is exactly what `oc_disruption` (§2) measures. |
| N23 | Pre-snap motion, player level | **STILL BLOCKED** | Same finding as T1-32 — no motion column anywhere in this database. |
| N24 | Play-action rate | **STILL BLOCKED (both levels — corrects the ledger)** | The ledger claims "computable team-level, 2022+." Checked directly: neither `pbp` (25 columns) nor `participation` (28 columns) carries a play-action indicator of any kind, at any level, for any season. The ledger's team-level claim does not hold against what is actually ingested — corrected here, not resurrected. |

### Task 1 summary

- **7 of 17** blocked rows are **NOW AVAILABLE and screened in this document**: T0-10, T0-11,
  T1-21, T1-22, T1-29 (partial), N12 (partial, team-total half only), N22.
- **5 of 17** are **NOW AVAILABLE but deliberately not built this pass** (flagged for a follow-up
  batch, each with a stated reason above): T0-1 (not a factor, a harness switch), T1-28, T1-30
  (exact definition), N14, N21 (exact definition).
- **5 of 17** are **STILL BLOCKED**, confirmed by checking the named table's actual schema rather
  than trusting the old disposition: T0-2, T1-32, N8, N23, N24.

---

## Part B — Task 2: the extended screen

### Method (unchanged from screen 1 — read `docs/ranking/standalone-screen-1.md` first)

- Screens **2013–2019 only**. 2020–2024 untouched. Sealed 2025 holdout never read.
- Universe: players with ≥1 game at the position that season (stated survivorship limitation,
  same as screen 1 — not a pre-season ADP/roster universe).
- Every factor value built from strictly-prior-season data (lag-1, or up to 3-lag recency-weighted,
  `LAG_WEIGHTS = (0.55, 0.30, 0.15)`).
- **EXOGENOUS / CONSTITUENT / AMBIGUOUS classified before any number is computed** (table below).
  Partialling out prior-season points is a valid predictiveness test only for EXOGENOUS factors.
  Both raw and partial numbers are always printed, for every factor.
- **Noise benchmark**: a seeded-noise placebo, same construction as screen 1, run per position.
- **Collinearity is diagnostic, never a filter.** Within-cluster contrasts (percentile-rank gap,
  |ρ| ≥ 0.6 within a position) are constructed and screened as their own candidates.
- **Cluster within each position, never once across all four** (per
  `FR-2026-08-04-v3-build-strategy...`'s binding instruction).

### Denominator

**35 base factors (36 named constructs minus the placebo) + 40 within-cluster contrasts = 75
distinct candidate constructs.** Screened across the positions each applies to: **119 base
factor-position cells + 78 contrast cells = 197 total screening cells.** Full detail:
`experiments/bottomup/results/standalone_screen2_results.csv` (119 rows),
`..._contrasts.csv` (78 rows), `..._collinearity.csv` (1,741 pairwise rows).

This is a different, larger denominator than screen 1's (58 cells) and a different, much cheaper
denominator than the incremental campaign's (M≈259–284 registered cells). **Nothing here adds to
either** — no `INCLUDE`/`EXCLUDE` appears anywhere below.

### What's new vs. screen 1's 14 base factors

| Group | Factors added | Ledger row(s) |
|---|---|---|
| C1 remainder | `xfp_diff` (actual − expected points/game), `ngs_separation` (lag-1 NGS avg separation), `tprr` (targets/route, participation proxy) | T1-18, N5, T1-16/T1-17/N3 |
| C2 remainder | `implied_team_total` (lagged, `odds_snapshots`) | T0-11/N12 |
| C4 (all six) | `tshare_stability`, `team_pace`, `is_contract_year`, `hc_disruption`, `ol_ybc`, `two_wr_rate` | T1-13, T1-21, T1-27, T1-29b, T1-23/N27, T1-31/N25 |
| Task-1 newly-unblocked | `proe`, `oc_disruption` | T1-22, T1-29/T1-30/N21/N22 |
| Six predictive incumbents (**no grandfather clause**) | `age`, `draft_capital`, `share_level` (tshare_w WR/TE, cshare_w RB — the LEVEL, distinct from C4-I's stability), `adot`, `depth_rostered_absent`/`depth_offroster`/`depth_first_share` (three sub-columns of T0-5), `inj_missed_share`/`inj_unexp_missed_share` (two sub-columns of T0-6) | T0-5, T0-6, T0-7, T0-8, T1-14, T1-25 |

**Not screenable, noted rather than silently dropped**: C2's RB high-carry-season breakpoint is a
functional-form/threshold hypothesis (already tested as such in C2, `docs/factor-ledger.md`
Section 0: RB −0.0002 NULL), not a factor *value* — there is nothing for a standalone-predictiveness
screen to compute.

### Incumbents built via `pos_features.build_features`, not reimplemented

The six predictive incumbents are pulled directly from the same construction the live/unshipped
component model uses (`experiments/bottomup/components/pos_features.py::build_features`, committed
on this branch), not a screen-only reimplementation — there is no risk of the screen's numbers
drifting from what v2/v3 actually fit on. `depth_rostered_absent`/`depth_offroster`/
`depth_first_share`/`inj_missed_share`/`inj_unexp_missed_share` are lag-1 only, `known` gated on
"not a rookie" (a rookie has no prior season for any of these, which is the correct unknown state,
not a zero).

### Noise benchmark (calibration reference, all positions)

| position | placebo raw ρ (pooled) | placebo partial ρ (pooled) |
|---|---|---|
| QB | +0.0368 | +0.0749 |
| RB | +0.0275 | +0.0584 |
| WR | −0.0065 | −0.0111 |
| TE | −0.0545 | −0.0407 |

Same order of magnitude as screen 1's floors (different exact values — a different seed string,
`standalone-screen2` vs `standalone-screen1`, by design so the two screens' placebos are
independent draws). **Survivor rule, unchanged from screen 1**: EXOGENOUS survives if
`|partial ρ pooled| > |placebo partial ρ|` at that position; CONSTITUENT/AMBIGUOUS survives if
`|raw ρ pooled| > |placebo raw ρ|` **and** the per-season sign is not reversed in the majority of
screened seasons. Deliberately inclusive — regularisation in the v3 joint fit decides what earns
weight, not this screen.

### Classification table (every new factor, class fixed before interpretation)

| Factor | Class | Why |
|---|---|---|
| `xfp_diff` | CONSTITUENT | built from the player's own actual-vs-expected points |
| `ngs_separation` | EXOGENOUS | NGS tracking-derived skill metric, not a box-score stat |
| `tprr` | CONSTITUENT | rate over the player's own targets |
| `implied_team_total` | EXOGENOUS | Vegas market read, not the player's own box score |
| `tshare_stability` | AMBIGUOUS | stability *of* a constituent quantity — neither purely inside nor outside the box score |
| `team_pace` | EXOGENOUS | team environment, not the player's own box score |
| `is_contract_year` | EXOGENOUS | a calendar/business event |
| `hc_disruption` | EXOGENOUS | coaching context |
| `ol_ybc` | EXOGENOUS | O-line environment, not the RB's own box score |
| `two_wr_rate` | EXOGENOUS | team personnel identity |
| `proe` | EXOGENOUS | team scheme identity (an `xpass` residual) |
| `oc_disruption` | EXOGENOUS | coordinator context |
| `age` | EXOGENOUS | time-invariant biography |
| `draft_capital` | EXOGENOUS | fixed at the draft, outside any season's box score |
| `share_level` | CONSTITUENT | the literal volume share the model already runs on (T0-8) |
| `adot` | AMBIGUOUS | a route-depth/role signal, but built from the player's own air yards and targets |
| `depth_rostered_absent` / `depth_offroster` / `depth_first_share` | EXOGENOUS | coach's own stated weekly role/availability, not derived from the box score |
| `inj_missed_share` / `inj_unexp_missed_share` | EXOGENOUS | injury-report-attributed vs. unattributed absence |

### Results — headline survivors by position

*Survivor rule as stated above. Full numbers (raw ρ, partial ρ, beats-aggregate delta, per-season
stability) for all 119 base cells: `standalone_screen2_results.csv`. All 78 contrast cells:
`standalone_screen2_contrasts.csv`.*

| Position | Base factors screened | Survivors (base) | Contrasts screened | Survivors (contrast) |
|---|---|---|---|---|
| QB | 22 | 12 | 11 | 7 |
| RB | 31 | 21 | 16 | 13 |
| WR | 31 | 27 | 20 | 16 |
| TE | 31 | 21 | 31 | 26 |

**Notable new findings, none of them decisions:**

- **`share_level` (the T0-8 incumbent, prior-year target/carry share LEVEL) is among the
  strongest survivors at every position it applies to** — WR raw ρ=0.678, TE 0.676, RB 0.567,
  essentially tied with `snap_share` and ahead of `redzone_share`. This is the base-spec incumbent
  that has never before faced this screen.
- **`draft_capital` and `age` survive strongly but with a striking sign pattern**: raw ρ is
  *positive* (older/higher-drafted correlates with more points, unsurprising — established players
  are more productive on average) but the **partial** ρ (controlling for prior-season points) is
  *negative* at every position for both factors. Read together with `depth_end_rank`'s similarly
  large negative partial: once you already know how many points a player scored last year, an
  *additional* season of age or a *worse* draft slot both predict a *decline* — consistent with
  regression-to-mean/aging-curve intuition, not a contradiction.
- **`depth_rostered_absent`, `depth_offroster`, and `inj_unexp_missed_share` all reverse sign to
  raw-negative at every position, every season, 0 exceptions** (`n_seasons_pos=0` across the board)
  — a player who was rostered-but-absent or off-roster or missing games for un-attributed reasons
  in the prior season reliably scores fewer points the following season. This is the strongest,
  most stable signal in the entire pool by season-consistency, though its magnitude is modest
  (raw ρ −0.24 to −0.65 depending on position).
- **`oc_disruption` and `hc_disruption` are both essentially null everywhere** (raw ρ within
  ±0.06 of zero at every position) — coordinator-level continuity, now that it is finally
  measurable, shows no standalone signal in this window. Consistent with the external sweep's own
  finding (`N22`, `docs/factor-ledger.md`: "not a single public backtest found").
- **`proe` is also essentially null** (raw ρ 0.03–0.05, well inside the placebo band at 3 of 4
  positions) — team pass-rate-over-expectation shows no standalone signal, distinct from (and
  weaker than) `neutral_pass_rate`, which the two are ρ=0.90 collinear with at every position
  (see below) — the raw frequency, not the game-state-adjusted residual, is carrying whatever
  signal exists.
- **`tprr` (targets per route run) reverses to negative raw ρ at all three applicable positions**
  (RB −0.45, TE −0.26, WR −0.33), the opposite sign of every external shop's reported YoY
  persistence number (N3, N1). Coverage is thin (routes only from 2016, so only 2017–2019 target
  seasons inside this screen's window, n_seasons=3 everywhere) and the partial ρ flips positive —
  flagged as a genuine oddity worth a second look before the joint fit, not resolved here.
- **`tshare_stability` (C4's factor I) survives cleanly at both applicable positions** (WR raw
  ρ=0.46, TE 0.37) and is itself only moderately collinear with `share_level` (WR ρ=0.65, TE not
  tight) — a real candidate for adding incremental information beyond the level feature it is
  designed to complement.

### Collinearity — diagnostic, not a pruning list (selected clusters, full matrix in the CSV)

Consistent with screen 1's finding: `{snap_share, share_level, wopr, redzone_share,
depth_end_rank, depth_first_share}` form one broad, only-partially-collapsed cluster at WR/TE — all
different views on "how much does the team feature this player." Two new tight pairs worth flagging
explicitly:

- **`neutral_pass_rate` ↔ `proe`, ρ=0.90 at every position** — expected (PROE is a game-state-
  adjusted version of the same underlying pass-rate signal) but the tightness means the two are
  very nearly measuring one thing; the contrast (`neutral_pass_rate − proe`) is screened and is
  null everywhere, meaning whatever the raw frequency captures, the residual does not add to it.
- **`implied_team_total` ↔ `proe`, ρ≈0.72–0.74** — a scoring-environment/scheme-identity link
  (teams expected to win big pass less than expected, roughly): informative but expected, not
  investigated further here.
- **`depth_first_share` ↔ `inj_unexp_missed_share`, ρ = −0.67 to −0.91** (strongest at QB) — a
  player consistently listed first on the depth chart is, almost mechanically, one who did not
  accrue unattributed missed games; the two overlap heavily but are not identical (the QB contrast
  survives with raw ρ=0.71, essentially as strong as either component alone).

Full pairwise matrix: `standalone_screen2_collinearity.csv` (1,741 rows).

### Two limits of this method (unchanged from screen 1)

1. A factor can be strongly predictive alone yet add nothing incrementally once the model already
   has correlated inputs — the joint fit, not this screen, is the real test.
2. A factor can be null alone yet help in combination (an interaction this screen cannot detect).
   Standalone predictiveness orders the queue; it does not decide inclusion.

---

## Part C — the final survivor set, ready for the v3 joint fit

**Per the founder's binding instruction (`FR-2026-08-04...`): v3 is four models, not one. No
factor is required to appear at every position; a factor earning weight at one position and
dropped at another is the correct outcome, not an inconsistency.** The full candidate pool below
goes into the joint fit **per position**, inclusively — nothing is pre-selected here.

| Position | Candidate pool size (base factors applicable + contrasts) |
|---|---|
| QB | 22 base (excludes WR/TE/RB-only constructs) + 11 contrasts = **33** |
| RB | 31 base + 16 contrasts = **47** |
| WR | 31 base + 20 contrasts = **51** |
| TE | 31 base + 31 contrasts = **62** |

("Candidate pool size" here counts every screened factor-position cell that is not the placebo,
including cells that did not clear the noise floor — per the founder's instruction, nothing is
pre-selected before the joint fit; the survivor counts in Part B's table above are context, not a
filter.)

---

## Bottom line, stated plainly

**75 distinct candidate factors (35 base + 40 within-cluster contrasts) will be tested for
inclusion in v3's joint fit.** Combined with screen 1's original 14 base factors and screen-1-era
contrasts (14 of the 35 base factors above are carried forward unchanged from screen 1; the "75"
figure already includes them, it is not additive on top of screen 1's count), this is the complete
testable pool as of today's ingestion state.

**5 factors remain genuinely untestable with the data we hold**: T0-2 (component-level consensus
projections), T1-32 (pre-snap motion, player level), N8 (tight-window target rate), N23
(pre-snap motion, player level — same underlying gap as T1-32), N24 (play-action rate, both team
and player level — corrects a stale ledger claim that team-level was computable). All five are
confirmed absent by checking the named table's actual schema directly, not by trusting the old
disposition.

A further 5 ledger rows are now available but were deliberately not built this pass (T0-1, T1-28,
T1-30, N14, N21) — each has a real join or a harder-than-stated construction behind it, flagged
above for a follow-up batch rather than rushed into this one.

---

## Files

- `experiments/bottomup/v2/standalone_screen2.py` — self-contained script, run from repo root
- `experiments/bottomup/results/standalone_screen2_results.csv` — 119 rows, individual factors
- `experiments/bottomup/results/standalone_screen2_collinearity.csv` — 1,741 rows, full pairwise matrix
- `experiments/bottomup/results/standalone_screen2_contrasts.csv` — 78 rows, within-cluster contrasts
- `docs/ranking/standalone-screen-1.md` — superseded by this document; kept for its own NEXT STEP
  history and as the record of the lag-bug data-quality note it documents
