# Batch C2 — more factors, plus the RB high-carry breakpoint, against ranking v2

**Registered by `backend`, 2026-08-01, before any arm was fitted and before any evaluative number
was computed.** Continues the C1 inclusion test (`batch-C1.md`, results
`docs/ranking/batch-C1-results.md`) against v2 (ADR-069: absolute quality against realised
outcomes; consensus is neither an input nor a development signal).

## Grading is SUSPENDED for this batch

C1's registered inclusion rule (paired season-block bootstrap 95% CI excluding zero, BH at the
campaign M) handed a BH-robust `INCLUDE` to **seeded noise that provably cannot carry signal**
(F0 at TE, +0.0303, p = 0.0002); replication measured the harness's false-positive rate at
**9.6% of cells against a nominal 2.5%**. `strategist` owns the replacement rule
(`docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi.md`, BLOCKED-ON-YOU).

**This batch builds, runs, and records. No factor here is graded INCLUDE or EXCLUDE.** Every cell
gets a CI-level verdict (WIN/HARM/NULL, estimator-independent) and is compared against this
batch's own placebo instrument, but the factor-level status is fixed in advance as
**`PENDING-RULE`** regardless of outcome. Re-grading once the replacement rule lands is mechanical
(`--regrade`, no refits) — see `docs/ranking/batch-C2-results.md`'s NEXT STEP block.

## Why C2 exists and what it adds over C1

C1 tested six factors, all NULL: snap share, red-zone usage, xFP, NGS separation, route
participation, steeper recency. Per the ledger's Section 0 note (`docs/factor-ledger.md`), rows
`rejected-with-evidence` under the **old consensus-derived frame** are untested for v2 and are fair
game; rows excluded for data availability or licensing still stand. C2 covers two things:

- **Part A — more untested-for-v2 factors**, prioritising data already in `nfl.db`, including
  `odds_snapshots` (3,884 rows, 2018–2024, ingested since C1 and never used by any model).
- **Part B — the threshold/breakpoint test class**, registered by the founder 2026-07-31 and never
  run: his own worked example is running backs coming off high-carry seasons (350/375/400 carries).

## The pinned primary (control)

**v2 with the G0 games arm — pinned**, unchanged from C1 (the G2a ruling's conditions C1–C5 remain
unsatisfied; `docs/ranking/factor-campaign-manifest/batch-C1.md` §"pinned primary"). Every cell
records `games_arm = G0`. No C2 arm reads week-1 roster status, asserted via
`n_preseason_proxy_reads == 0` per position per season, exactly as C1.

### Matched controls — one per feature window

| control | `first_feature_season` | targets | why |
|---|---|---|---|
| **CTRL-A2** | 2012 | 2018–2024 (7) | same parameters as C1's CTRL-A, for continuity. Used by every Part A/B factor whose source predates 2012 |
| **CTRL-D** | 2018 | 2021–2024 (4) | `odds_snapshots` starts 2018; a lag-3 feature at the earliest target (2021) needs 2018 data, so this is the widest window fully inside odds coverage. Used by A5 (implied team total) only |

## Part A — the factors, m_b = 21 (16 treatment/control cells + F0/F0D placebo not yet counted)

Every arm differs from its matched control by **exactly one thing** — one factor's column block
added to the position's volume feature spec — per the C1 arm discipline (one arm, one change, no
stacking).

| arm | factor | ledger row | source | positions | cells | reused code |
|---|---|---|---|---|---|---|
| **A1** | WOPR (weighted opportunity rating), recency-weighted | T1-15 | `player_weekly_stats.wopr`, full 2009+ | WR TE | 2 | new block (data already computed as a stored column) |
| **A2** | YAC per reception (empirical-Bayes shrunk vs. own-position prior) | N16 | `player_weekly_stats.receiving_yards_after_catch`, real 2006+ | RB | 1 | **reused verbatim**: `factor_features7._yac` (batch 7) |
| **A3** | Receiving share of an RB's own points, scored under this league's rules | N17 | panel's own `rec_pts`/`rush_pts`, computed from stat lines already in every panel row | RB | 1 | **reused verbatim**: `factor_features7._rec_points_share` (batch 7) |
| **A4** | Late-season role trajectory (own ratio + round×career-year group lift) | N19 | `player_weekly_stats` + `draft_picks`, weeks 13+ split | RB WR TE | 3 | **reused verbatim**: `factor_features7._late_season` (batch 7) |
| **A5** | Implied team total, lagged (team offensive environment) | T0-11 / N12 | `odds_snapshots` 2018+, joined to each player's own team by (season, week, team) | QB RB WR TE | 4 | new block |

**Why these four are reused rather than reimplemented**: `_yac`, `_rec_points_share`, and
`_late_season` were built and gated for batch 7 (`docs/ranking/factor-batch-7-results.md`), tested
only against the **old consensus-derived primary**, and never run against v2. Per the ledger's
Section 0 rule they are untested-for-v2 and fair game; importing the same gated code (rather than
rewriting it) is the same discipline C1 used for snap share / xFP / NGS separation / routes — a
second implementation of a feature is a second chance to get its cutoff wrong.

### Positions deliberately excluded, with the reason, before measurement

- **A1 at RB/QB** — WOPR is a receiving-usage composite (target share + air-yards share); RBs and
  QBs are not the population it is defined for.
- **A2/A3 at WR/TE/QB** — YAC-per-reception and receiving-share-of-own-points are RB-specific
  claims in the source material (McFarland); batch 7 built and scoped them to RB only, and C2 does
  not widen that scope without a registered reason.
- **A4 at QB** — a starting quarterback's role does not fluctuate across a season the way a
  committee back's or a WR2/3's does; career-year bucketing is a poor descriptor of a stable QB1
  job. A priori judgment, stated before measurement.

### Coverage-indicator paired controls (C1 Amendment 1's VOID-rule discipline, carried forward)

Every factor above except A1 carries a `*_known` presence/join indicator, and batch 7 measured one
such indicator at **215% of its own treatment's effect** (`rzsnap_known`). C1's Amendment 1 fix —
one paired control arm per factor, appending **only** the `*_known` column, same control, same
positions — is repeated here rather than re-discovered:

| arm | pairs | column | positions | cells |
|---|---|---|---|---|
| **A2k** | A2 | `yac_known` | RB | 1 |
| **A3k** | A3 | `recpts_known` | RB | 1 |
| **A4k** | A4 | `late_known` | RB WR TE | 3 |
| **A5k** | A5 | `itt_known` (odds join resolved) | QB RB WR TE | 4 |

**A1 has no paired control**: `wopr` is a dense scoring column (100% populated 2009+ at WR/TE, no
join/presence gate), so there is no presence indicator to void against.

**The VOID rule, unchanged from C1**: a treatment cell's WIN is void if its paired `*k` cell wins at
the CI level. Recorded per cell; not acted on until the replacement inclusion rule lands, since
grading is suspended this batch regardless.

**Part A total: A1(2) + A2(1) + A2k(1) + A3(1) + A3k(1) + A4(3) + A4k(3) + A5(4) + A5k(4) = 20 cells.**

## Part B — the RB high-carry-season breakpoint, m_b = 1

**The founder's registered hypothesis, 2026-07-31**: running backs coming off high-carry seasons —
350 / 375 / 400 carries — may see a non-linear effect (a "workload cliff") that a linear volume
term cannot express. **His three numbers are his hypotheses, not established thresholds.**

**Design choice, made before computing anything**: the dispatch prefers "a single test for
non-linearity ... over a sweep of hard cutoffs," because sweeping candidate thresholds and
reporting the best is exactly how a multiple-comparisons finding gets manufactured. **One arm**,
not three: a piecewise-linear (hinge) basis with the founder's three values used as **fixed,
pre-registered knots** — `max(0, carries_1 − 350)`, `max(0, carries_1 − 375)`,
`max(0, carries_1 − 400)` — added together to the RB `carries_pg` and `tpg` volume specs. This is
one non-linearity test (one bootstrap comparison against the linear control that already holds
`carries_1` implicitly through `carries_pg_w`), not three separate cutoff sweeps; the three knots
are not searched, selected, or compared against each other — only the joint hinge block is
compared to the no-hinge control.

**`carries_1` already exists in every v2 feature frame** (`pos_features.build_features`'s own
lag-1 raw carries column) — zero new ingest, zero new source, zero new gate. Feature-season carries
are already bounded by the existing walk-forward cutoff; no additional look-ahead risk is
introduced.

**Power, stated before running, not discovered after**: within CTRL-A2's feature-season range
(2011–2023, the lag-1 seasons feeding targets 2018–2024 across the three lags used elsewhere),
**exactly 3 RB player-seasons have carries_1 ≥ 350, 2 have ≥ 375, and 0 have ≥ 400** (measured
directly against `player_weekly_stats`, `SELECT ... WHERE position='RB' AND season BETWEEN 2011
AND 2023 GROUP BY player_id, season`). Batch 3/4 found the same order of scarcity in the old
frame (≥350 carries: 26 player-seasons since 1999 league-wide; ≥400: zero) and registered but did
not run this test for exactly that reason. **This batch runs it anyway**, because the dispatch
asks for build-run-record rather than a stop, but the expected finding is that the arm is
**underpowered to the point of near-certain NULL**, not evidence the workload-cliff hypothesis is
false. No coverage floor is applied to this arm (it is a rare-event indicator, not a
presence/join condition) — the sparsity itself is reported directly instead.

| arm | positions | cells |
|---|---|---|
| **B1** | RB | 1 |

## The placebo — carried again, as the batch's own calibration instrument

C1's placebo is the reason C1's NULLs are trustworthy rather than merely unreflected-upon. C2
reuses the **identical instrument** — `factors_c1._placebo`, the same seeded-hash generator, same
salt (`""`, i.e. byte-for-byte the registered C1 draw) — run fresh against **this batch's own
controls**, because C1's 34-draw replication calibrated CTRL-A/B/C, not CTRL-A2/CTRL-D. One draw
per control (not a 34-draw replication study — that is C1's already-published instrument; this is a
same-batch sanity check, reported as such, not oversold as a fresh calibration study).

| arm | control | positions | cells |
|---|---|---|---|
| **F0** | CTRL-A2 | QB RB WR TE | 4 |
| **F0D** | CTRL-D | QB RB WR TE | 4 |

## m_b = 20 (Part A) + 1 (Part B) + 8 (placebo) = **29**

**Campaign denominator, for whenever the replacement rule lands and grading resumes:**
`M_campaign = max(Σ_b m_b, FLOOR=80) = max(130 + 29, 80) = 159` (130 = batches 5/6/7 [56] + M2 [16]
+ B1 [20] + C1 [38]; PR-007's 4 stay in their own family). **Not applied in this batch** — no BH is
computed here, since the WIN rule it would feed is suspended. Recorded so the next batch to
register does not under-count, and so a future regrade knows the correct denominator.

## Endpoint, population, statistics — identical to C1

- **Endpoint:** Spearman(v2 `proj_points` order, realised season points), per (position, season).
- **Population:** M-panel veterans (FFC-ADP membership defines the evaluation subset only).
- **Look-ahead:** `feature_gate`/`outcome_gate` + `WalkForward` audit assertions, no hand-rolled
  cutoffs. Every arm asserts `n_preseason_proxy_reads == 0`.
- **Holdout:** 2025 sealed, never read. Targets end at 2024.
- **Statistics:** paired season-block bootstrap on the per-season deltas, 4,000 reps, seed
  20260801 (same as C1 — same estimator, not a second one). CI verdict (WIN/HARM/NULL) recorded per
  cell, estimator-independent and safe to re-grade later. **No BH, no INCLUDE/EXCLUDE call, this
  batch.**

## Registered predictions, so the result can surprise

- **A1 WOPR:** possible WIN at WR (WOPR is a composite of target share and air-yards share, both
  of which the model already holds as `tshare_w`/`adot`-adjacent terms; registered downside is
  collinearity, same mechanism C1 predicted for red-zone usage). NULL at TE (thin sample, WOPR
  built for high-target WRs).
- **A2 YAC per reception:** NULL. The old-frame measurement was ~0 relative to a published r=0.421
  external correlation (`docs/ranking/factor-batch-7-results.md`); nothing about moving to v2's
  primary changes the mechanism (an efficiency trait fed to a volume-oriented spec).
- **A3 receiving share of own points:** NULL to marginal WIN at RB — it is closer to a role
  descriptor than most efficiency traits, but the model already holds `tshare_w`/`cshare_w`
  separately, so the combined-share ratio may be collinear.
- **A4 late-season trajectory:** possible WIN at RB (committee-back roles are the least stable),
  NULL at WR/TE (roles more fixed within a season for pass catchers).
- **A5 implied team total:** NULL to marginal WIN, all four positions — externally, the whole
  team-environment channel is oracle-bounded at ≤ +0.055 τ_b (`fr136-q1-bottom-up-assessment.md`
  §6.6); registered expectation is a small, possibly undetectable effect at this n.
- **B1 RB carry-hinge:** **NULL, and expected to be exactly-zero-delta or a wide, uninformative
  CI** — 3 feature-season instances at ≥350 carries in the entire training window is not enough
  evidence for OLS to fit a stable coefficient. Reported as **measured-underpowered**, not as
  evidence against the workload-cliff hypothesis.
- **F0/F0D placebo:** registered prediction is 0 WIN, 0 HARM, same as C1 — any WIN here is a
  finding about the harness at these specific controls, not a factor result, and it is reported
  alongside the Part A/B cells for direct comparison rather than graded.

## Scope notes

No arm reads consensus, ADP, or ECR in its ordering path. No arm reads a season-N proxy. No
weights are tuned. No factors are stacked. The 2025 holdout is not opened, and nothing in this
batch would warrant opening it — a result that appears to warrant it stops and escalates to the
founder per `CLAUDE.md` §6.3.
