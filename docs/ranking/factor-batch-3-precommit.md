# Factor batch 3 — pre-commitment

**Ranker, 2026-07-30. Written and committed BEFORE any arm was fitted.** Same discipline as
`factor-batch-1-precommit.md` (`d546cff`) and `factor-batch-2-precommit.md` (`851a6bb`). If a number
in the results document is not predicted by an endpoint declared here, it is post-hoc and must be
labelled so.

**Scope.** The researcher's ranked five
(`docs/research/analyst-factor-sweep-2026-07-30.md` §5), plus the founder's correction that
coordinator continuity should be specified as *tenure* and that **QB was never tested at all** in
batch 2's coordinator arms.

| sweep rank | factor | data | status here |
|---|---|---|---|
| 1 | QB rushing attempts per game (N9) | `player_weekly_stats`, zero ingest | arms **A1, A2** |
| 2 | NGS average separation (N5) | `ngs_receiving`, 2016–2025 | arms **S1, S1c** |
| 4 | Explosive rush rate (N13) | `pbp`, 2009–2025 | arms **X1, X2, X1c** |
| 5 | Prior points **per game played** vs season total | `player_weekly_stats` | **family F2** |
| — | Coordinator continuity as **tenure**, incl. QB | `play_callers_preseason` | arms **T1, T1c, C1Q** |

Sweep rank 3 (first-read target share) is **not** in this batch: it needs FTN charting, which is 4
seasons and a proxy for a paid definition. Deferred with a reason, not forgotten.

**Exploratory, not confirmatory of a shipped change.** The sealed 2025 holdout is not touched and no
holdout spend is requested. Promotion of any arm into the shipped model is a `strategist`
registration plus a `backend` handoff, not a decision this pass may make.

---

## 1. What batch 3 exists to answer, stated before the answer is known

Batch 2 ended **12 NULL-or-worse out of 12** once its one mis-specified arm was decomposed. Batch 1
ended with one factor rejected-with-evidence and two false passes it had to name and disown. The
honest prior going into batch 3 is therefore **that most of these will be null**, and this document
exists so that a null cannot be re-described afterwards as "underpowered" and a hit cannot be
re-described afterwards as "expected."

Three things are new in this batch and each is stated now so it cannot be claimed later as a
discovery:

1. **QB has never been touched by any factor arm in this project.** Batch 1 ran QB only on the TD-rate
   arms; batch 2 ran WR/TE/RB and skipped QB entirely. Meanwhile all twelve of the shipped board's
   largest top-100 disagreements with consensus are QBs or TEs, with no QB-specific input behind them.
2. **Separation is the only in-database signal that is not a rearrangement of box-score volume.** If
   consensus prices volume — and it visibly does — then a factor built out of volume is the least
   likely place for an edge and this is the most likely.
3. **F2 is not a factor.** It changes the *reference* every future factor is measured against. That is
   why it is in this batch rather than a later one.

---

## 2. Harness — unchanged, deliberately

`experiments/bottomup/components`, the walk-forward from `component-model-multipos-precommit.md`,
reused exactly as batch 2 reused it.

| | |
|---|---|
| Target seasons | **2014–2024 (11)** for every arm except the two NGS separation arms — see §4 |
| Features | seasons ≤ N−1, plus the declared season-N `proxy`-tagged reads |
| Training | (features, outcome) pairs whose OUTCOME season is ≤ N−1; `first_feature_season = 2012` at every position, QB included |
| Universe | frozen from pre-N information; busts retained, scoring zero |
| Holdout | 2025 sealed at the SQL gate (`pos_data.HOLDOUT_SEASON`). **Not opened** |
| Uncertainty | season-block bootstrap, 4,000 reps, **seasons** the resampling unit |

**Every arm differs from its position's primary by exactly the feature block it declares.** No arm
changes the availability sub-model, the bonus machinery, the universe or the scoring.

**Two new data sources enter the panel and neither is a season-N read.** `ngs_receiving` (season-level,
`week = 0`, REG) and `pbp` rushing counts are ordinary history: they go through `before()`-style
cutoff gates and log as `feature`, not as `proxy`. Only the coordinator block reads season N.

---

## 3. Endpoints, fixed now

**E1a — THE FDR ENDPOINT FOR FAMILY F1. Out-of-sample MAE of the one declared component, full
universe.** Arm − primary, paired by season, season-block bootstrap, 4,000 reps. **Negative = better**
for addition arms; the sign convention for the one ablation arm is inverted and stated at §5.

**E1b — A REQUIRED DIRECTION CHECK, NOT THE SIGNIFICANCE TEST.** The same MAE restricted to players on
the consensus ADP board, **7 seasons (2018–2024)**, metric `adpsub_mae_*`. Batch 2's reasoning stands
unchanged: a 24-arm BH family on 7 seasons returns all-NULL regardless of the truth, so E1b is a
necessary condition and not the test. An arm significant on E1a but **not** better on E1b is graded
**BOARD-NEUTRAL** and is explicitly not an edge.

**E2 — the bar that matters, NOT in the FDR family. ADP-board Spearman, arm − primary**, 7 seasons.
`CLAUDE.md` §6.5. **Known underpowered before it is run** at WR, TE and QB
(`component-model-rb-qb-te-pass-1.md` §1); only RB resolves anything. Stated here so it cannot be
produced afterwards as a caveat.

**E3 — the endpoint for family F2 only. Full-universe Spearman of a candidate BASELINE against
realised season-N points, candidate − incumbent**, paired by season, 11 seasons, same bootstrap. F2
compares reference rankers, not model arms, so a component MAE is not defined for it. Its ADP-board
Spearman is reported as a direction check.

**Exactly one E1 component per cell**, declared in §4. Reporting the best of several components per
cell would be selection on the outcome, which is what this document exists to stop.

---

## 4. The arms — declared in full. Campaign m = 24, in two families

### Family F1 — model arms, 16

| # | id | factor | pos | the ONE thing that changes | E1 comp | target seasons |
|---|---|---|---|---|---|---|
| 1 | **A1** | QB rushing volume, **ABLATION** | QB | drop `carries_pg_w`, `rushyds_pg_w` from the `carries_pg` volume spec | `carries` | 11 |
| 2 | **A2** | QB rushing → **passing** volume | QB | add `carries_pg_w` to the `att_pg` volume spec | `attempts` | 11 |
| 3 | **S1** | NGS average separation | WR | add `sep_1` to `tpg` | `targets` | **7** (2018–2024) |
| 4 | **S1** | NGS average separation | TE | add `sep_1` to `tpg` | `targets` | **7** |
| 5 | **S1c** | NGS **coverage control** | WR | add `sep_known_1` **only** | `targets` | **7** |
| 6 | **S1c** | NGS **coverage control** | TE | add `sep_known_1` **only** | `targets` | **7** |
| 7 | **X1** | explosive rush rate, own | RB | add `expl_w` to `carries_pg` | `carries` | 11 |
| 8 | **X2** | explosive rush rate, **club-relative** | RB | add `expl_rel_w` to `carries_pg` | `carries` | 11 |
| 9 | **X1c** | explosive **coverage control** | RB | add `expl_known` **only** | `carries` | 11 |
| 10 | **T1** | OC **tenure** | QB | add `oc_tenure` to `att_pg` | `attempts` | 11 |
| 11 | **T1** | OC **tenure** | WR | add `oc_tenure` to `tpg` | `targets` | 11 |
| 12 | **T1** | OC **tenure** | TE | add `oc_tenure` to `tpg` | `targets` | 11 |
| 13 | **T1** | OC **tenure** | RB | add `oc_tenure` to `carries_pg` | `carries` | 11 |
| 14 | **T1c** | OC **coverage control** | QB | add `oc_tenure_known` **only** | `attempts` | 11 |
| 15 | **T1c** | OC **coverage control** | WR | add `oc_tenure_known` **only** | `targets` | 11 |
| 16 | **C1Q** | **`new_oc`, batch 2's own C1 block, at the position batch 2 never ran** | QB | add `new_oc` to `att_pg` | `attempts` | 11 |

### Family F2 — baseline respecification, 8

`CLAUDE.md` §6.5 baseline #2 is *prior-season fantasy points, ranked* — implemented as `pts_1`, a
season **total**, which silently multiplies a rate by an availability. F2 splits them. Endpoint E3.

| # | id | candidate | positions |
|---|---|---|---|
| 17–20 | **B2r** | prior points **per game played** (`pts_1 / games_1`, 0 when `games_1 = 0`) | QB, RB, WR, TE |
| 21–24 | **B2ra** | prior points per game played **× prior games share** (`ppg_1 × gshare_1`) | QB, RB, WR, TE |

Reported alongside, **outside the family and carrying no new claim**: the incumbent `b3_wavg_ppg`
(recency-weighted ppg × recency-weighted games share), which already exists in `pos_eval` and is the
three-lag version of B2ra.

### Multiplicity

**The campaign family is all 24 tests. Benjamini–Hochberg at q = 0.10 across all 24 E1a/E3 p-values,
denominator fixed at 24 regardless of how many arms turn out to be computable.** Also reported at
q = 0.05, and — as a clearly-labelled secondary — within-family BH (m = 16, m = 8).

Control arms count in m. They are expected to be uninformative and including them costs the treatment
arms power; that is the conservative direction and it is taken on purpose.

### Why the NGS arms get 7 seasons and not 11

NGS begins in 2016, so `sep_1` is structurally missing for target seasons 2014–2016 and the arm would
be *identical* to the primary in those years. **2018 is the first target season whose training window
contains a season with real separation coverage** (training season 2017, whose lag-1 is 2016). That
rule is fixed here, before fitting, and it produces 7 target seasons — the same n as E1b, and
**known underpowered relative to the 11-season arms before it is run.**

---

## 5. Decision rules, fixed now

### Addition arms (all except A1)

| grade | rule |
|---|---|
| **SURVIVES** | BH-significant on E1a at q=0.10 (campaign m=24), direction better, **and** E1b < 0, **and** E2 > 0 |
| **PROJECTION-ONLY** | BH-significant better on E1a, **and** E1b < 0, but E2 ≤ 0 |
| **BOARD-NEUTRAL** | BH-significant better on E1a, but **E1b ≥ 0** |
| **HARMFUL** | BH-significant on E1a, direction worse |
| **MARGINAL / MARGINAL-HARMFUL** | E1a 95% CI excludes zero but not BH-significant |
| **NULL** | otherwise |

### The one ablation arm, A1 — sign convention inverted, stated now

A1 removes a block that is already in the primary, so **a positive E1a means the block was doing real
work.**

| grade | rule |
|---|---|
| **EARNS-ITS-PLACE** | BH-significant, E1a > 0 |
| **NO-MEASURABLE-CONTRIBUTION** | not significant |
| **HARMFUL-TO-KEEP** | BH-significant, E1a < 0 — the model is better without it |

### The leak trigger, armed in advance with a number

Batch 2 lost three arms because a companion "we know his club" flag turned out to be **95–97% of the
effect**. Every batch-3 block that has a coverage flag ships that flag as **its own registered control
arm** (S1c, X1c, T1c), and:

> **If a control arm's |E1a| is ≥ 50% of its paired treatment arm's |E1a|, the treatment arm is graded
> VOID — COVERAGE ARTIFACT**, regardless of its own p-value, and may not be quoted without that
> sentence. The treatment keeps its recorded numbers; it loses its interpretation.

Additionally, batch 2's escape hatch is re-armed unchanged: **any E1a improvement exceeding 2% of the
primary's own error is treated as a suspected leak and escalated before write-up**, per `CLAUDE.md`
§8. A result that looks too good is a finding to escalate, not to celebrate.

### Coverage gates, committed before the coverage is known on the graded population

Measured **on the ADP board**, the population the gate exists to protect, averaged across the arm's
target seasons:

| block | gate | below it |
|---|---|---|
| `oc_tenure` | mean `oc_tenure_known` ≥ **0.80** | cell marked **NO DATA**, reported as a data finding, **still counts in m = 24** |
| `sep_1` | mean `sep_known_1` ≥ **0.60** | same |
| `expl_w` | mean `expl_known` ≥ **0.80** | same |

### Stopping condition

All 24 tests run **once**. No arm is re-specified, re-parameterised or re-scoped after any result is
seen. Anything discovered afterwards is labelled post-hoc and carries a lower evidential standard.

**Stated before measurement, at the founder's request:** batch 2 graded coordinator change NULL at WR,
TE and RB. **If T1/C1Q are also null at QB, registry #29 is dead on both specifications — change and
tenure — and must not be re-specified a third time.**

---

## 6. What the coordinator data is, where it is censored, and what a backfill actually returned

`play_callers_preseason` is the pre-Week-1 Wikipedia staff-navbox read built for batch 2
(`experiments/bottomup/factors/coord_preseason.py`), **not** the end-of-season `{{NFL final staff}}`
rows, which name the mid-season replacement and would manufacture signal in the direction of the
hypothesis. Batch 2 §3 establishes that; it is not re-derived here.

**A tenure variable computed off a source that starts in year Y understates every spell that began
before Y**, in one direction, for exactly the longest-serving coordinators. So a backfill was run
before this document was written.

**The backfill failed, for a documented source reason, and the failure is the finding.** Running
`coord_preseason --start-season 2004 --end-season 2009` returned **96 of 192 team-seasons as
`no_revision_before_kickoff`**: the club staff **navbox template pages did not exist on Wikipedia**
before roughly 2010. What landed was 5 clubs in 2007, 4 in 2008 and 12 in 2009 — partial, and partial
*by club*, so a chain reaching a covered club would look longer than an identical chain at an
uncovered one. **That is worse than a clean floor**, so those rows are deliberately not used.

**Choice made, and stated as the dispatch requires: restrict, with the floor at 2010.** The chain is
walked back to 2010 and no further; any spell still alive at 2010 is flagged
`oc_tenure_known = 0`, imputed to the median of known tenures, and **not reported as tenure.**

**Censoring under that floor, measured before any arm was fitted** (32 clubs per season):

| target seasons 2014–2023 | 2024 |
|---|---|
| **exactly 1 censored club-season per year — 3.1%** | **0** |

One club. The censoring does not bite, and that is a measurement rather than a hope.

Coverage of `play_callers_preseason` after the batch-2 build plus this batch's attempted backfill:
**2010–2024, 30–32 clubs per season, 496 OC rows.** The 2007–2009 partial rows are present in the
table and unused by the feature code.

---

## 7. Guardrails (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§6.1) | `SeasonPanel.before()` / `ngs_before()` / `rush_before()` gates; separate `outcomes()` accessor; per-target-season audit asserting max feature cutoff and max outcome season strictly < target and zero outcome reads at target |
| **The season-N reads, isolated** | only the `oc` block reads season N. `sep` and `expl` are built by a feature function that computes **only the blocks an arm declares**, so a separation arm can be PROVEN to have made zero proxy reads rather than merely believed to have |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0 |
| **Multiple comparisons** (§6.3) | BH across the campaign, m = 24, q = 0.10 and 0.05, denominator fixed regardless of outcome |
| **Holdout** (§6.3) | 2025 sealed at the SQL gate. Not opened |
| **Effect size** | every E1a reported as a % of the primary's own error, and every candidate re-checked on the ADP board via E1b |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n, never player-seasons |
| **Coverage-flag confound** | three registered control arms plus the 50% VOID rule above |
| **Reproduction** | batch 1 and batch 2 must both reproduce **bit-for-bit** under the extended feature builder; asserted, not assumed |
| **Shrinkage constant** | `EXPL_K0 = 50` carries, fixed a priori, never tuned against a result |

---

## 8. Who checks this, because I do not check my own work

| claim | independent check |
|---|---|
| this design, its family definition and its decision rules | **`strategist`** — thread opened this session, before results are read |
| the result once it exists | **`fable`**, at maximum effort, separate budget |
| the coordinator source's 2010 floor, and whether `pbp` / `ngs_receiving` belong in the rebuild path | **`data-ops`** |
| shipping anything that grades | **`backend`** — a handoff, never a self-merge |
