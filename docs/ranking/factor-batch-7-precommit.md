# Factor batch 7 — pre-commitment

**Ranker, 2026-07-30. Written and committed BEFORE any arm was fitted.** Same discipline as
`factor-batch-1-precommit.md` (`d546cff`), `factor-batch-2-precommit.md` (`851a6bb`) and
`factor-batch-3-precommit.md` (`1c452a1`). If a number in the results document is not predicted by
an endpoint declared here, it is post-hoc and must be labelled so.

**Scope.** The six running-back rows of the external analyst sweep,
`docs/research/analyst-factor-sweep-2026-07-30.md` §2c — **N14, N15, N16, N17, N18, N19**. Every arm
is at RB and no other position is touched.

**Not in this batch, and named so the omission is not mistaken for an oversight:** N13 explosive
rush rate is batch 3's registered arm X1 and is already graded; high-carry workload thresholds are
batch 4's. Neither is re-run here.

**Exploratory, not confirmatory of a shipped change.** The sealed 2025 holdout is not touched and no
holdout spend is requested. Promotion of any arm into the shipped model is a `strategist`
registration plus a `backend` handoff, not a decision this pass may make.

---

## 1. Why RB, and what "success" would have to look like

RB is the only position where this project's own experiment has **demonstrated statistical power**
and where the component model has a **measured deficit**:

| measurement | value | source |
|---|---|---|
| ADP − positional heuristic, RB | **+0.134 [+0.043, +0.223]** | the experiment resolves at RB and at no other position |
| component model − ADP, RB board Spearman | **−0.0523**, 7 seasons (2018–2024) | `experiments/bottomup/results/rb_components_metrics.csv`, recomputed in §3 as E4 |

Power plus a measured deficit is the best place in this project to spend a test. **The honest prior
is still that most of these are null** — batch 1 produced one rejected factor and two false passes it
had to disown, batch 2 ended 12-of-12 null-or-worse, and batch 3's only real find was a missing wire
inside our own model rather than any factor from the sweep. This document exists so that a null
cannot be re-described afterwards as "underpowered" and a hit cannot be re-described afterwards as
"expected".

**Stated before measurement:** closing −0.0523 requires an arm to move E4 to at least zero. No single
usage feature in this batch is expected to do that, and **an arm that improves E1a without moving E4
has not closed the RB deficit** — that sentence is written here so it cannot be softened later.

---

## 2. Harness — unchanged, deliberately

`experiments/bottomup/components`, the walk-forward from `component-model-multipos-precommit.md`,
reused exactly as batches 2 and 3 reused it.

| | |
|---|---|
| Position | **RB only** |
| Target seasons | **2014–2024 (11)**, except the participation and snap-count arms — §4 |
| Features | seasons ≤ N−1 **only**. Batch 7 makes **no season-N read of any kind** |
| Training | (features, outcome) pairs whose OUTCOME season is ≤ N−1; `first_feature_season = 2012` |
| Universe | frozen from pre-N information; busts retained, scoring zero |
| Holdout | 2025 sealed at the SQL gate (`pos_data.HOLDOUT_SEASON`). **Not opened** |
| Uncertainty | season-block bootstrap, 4,000 reps, **seasons** the resampling unit |

**Every arm differs from the primary by exactly the one feature column it declares.** No arm changes
the availability sub-model, the bonus machinery, the universe or the scoring.

**No shared module is edited.** Four factor batches are running concurrently against one checkout.
Batch 7's six new sources load through a batch-local `Batch7Sources` object
(`experiments/bottomup/factors/factor_features7.py`) that carries its own holdout gate and its own
cutoff assertion, and pushes every read onto `panel.access_log` under the existing `feature` tag — so
`WalkForward`'s look-ahead audit covers them unchanged. `pos_data.py`, `pos_model.py` and `pos_eval.py`
are read-only to this batch.

### Two insertion mechanisms, and why there are two

Batches 1–3 inserted every arm as a column added to a **volume spec** (`carries_pg`, `tpg`). Two of
batch 7's factors are **efficiency** claims whose hypotheses live in a shrunk **rate**, not in a
volume spec:

| factor | the claim | where it lives |
|---|---|---|
| N15 inside-5 TD conversion | a back converts goal-line carries above/below the base rate | `tdpc` → `proj_rush_tds` |
| N16 YAC per reception | a back gains more after the catch than his peers | `ypr` → `proj_rec_yards` |

Adding either to `carries_pg` would test a proposition nobody made — that goal-line conversion
predicts how many carries a back is given. So a **batch-local subclass** adds **one linear covariate
to one declared rate**: after the ordinary fit, the residual of the realised rate against the model's
own shrunk prediction is regressed on the centred covariate by weighted least squares, weights = the
rate's own denominator, veterans only. **One extra parameter.** It is a subclass and an overridden
`_make_model`, not a monkeypatch of `MODELS`, and `pos_model.py` is untouched.

---

## 3. Endpoints, fixed now

**E1a — THE FDR ENDPOINT. Out-of-sample MAE of the one declared component, full universe.**
Arm − primary, paired by season, season-block bootstrap, 4,000 reps. **Negative = better.** Same
endpoint as batches 1–3, so every batch-7 number is directly comparable to their tables.

**E1b — A REQUIRED DIRECTION CHECK, NOT THE SIGNIFICANCE TEST.** The same MAE restricted to players
on the consensus ADP board, **7 seasons (2018–2024)**, metric `adpsub_mae_*`. Batch 2's reasoning
stands unchanged: a large BH family on 7 seasons returns all-NULL regardless of the truth, so E1b is
a *necessary condition* and not the test. An arm significant on E1a but **not** better on E1b is
graded **BOARD-NEUTRAL** and is explicitly not an edge.

**E2 — the bar that matters, NOT in the FDR family. ADP-board Spearman, arm − primary**, 7 seasons.
`CLAUDE.md` §6.5. At RB this endpoint **does** resolve — that is precisely why this batch is at RB.

**E4 — THE DEFICIT ITSELF, reported for every arm, not a significance test.** Mean over the arm's
board seasons of `adpsub_rho_model − adpsub_rho_b1_adp`. The primary's value is **−0.0523**. This is
the number the dispatch asks about and it is an absolute level, not a delta: an arm can improve E2
and still leave E4 negative, and that outcome is **"did not close the deficit"**, not a win.

**Exactly one E1 component per arm**, declared in §4. Reporting the best of several components per
arm would be selection on the outcome, which is what this document exists to stop.

---

## 4. The arms — declared in full. Batch m = 16, campaign m = 80

| # | id | factor | the ONE thing that changes | insertion | E1 comp | first target |
|---|---|---|---|---|---|---|
| 1 | **Z1** | N14 red-zone **snap** rate | `rz20_snap_w` | `carries_pg` | carries | **2018** |
| 2 | **Z2** | N14 **inside-5** snap rate | `i5_snap_w` | `carries_pg` | carries | **2018** |
| 3 | **Z3** | N14 red-zone snap rate → receiving | `rz20_snap_w` | `tpg` | targets | **2018** |
| 4 | **Z1c** | **CONTROL** coverage flag | `rzsnap_known` | `carries_pg` | carries | **2018** |
| 5 | **G1** | N15 inside-5 conversion vs base rate | `i5_conv_w` | **rate cov on `tdpc`** | rush_tds | 2014 |
| 6 | **G1p** | **CONTROL** binomial placebo | `i5_conv_placebo_w` | rate cov on `tdpc` | rush_tds | 2014 |
| 7 | **G1c** | **CONTROL** coverage flag | `i5_known` | rate cov on `tdpc` | rush_tds | 2014 |
| 8 | **Y1** | N16 YAC per reception | `yac_per_rec_w` | **rate cov on `ypr`** | rec_yards | 2014 |
| 9 | **Y1c** | **CONTROL** coverage flag | `yac_known` | rate cov on `ypr` | rec_yards | 2014 |
| 10 | **S1** | N17 receiving share of own points | `recpts_share_w` | `tpg` | targets | 2014 |
| 11 | **S2** | N17 **≥40% bin**, McFarland's own cut | `recpts_ge40` | `tpg` | targets | 2014 |
| 12 | **P1** | N18 prior snap share | `snapshare_w` | `carries_pg` | carries | **2015** |
| 13 | **P2** | N18 **≥60% gate**, McFarland's own cut | `snap_ge60_w` | `carries_pg` | carries | **2015** |
| 14 | **P1c** | **CONTROL** coverage flag | `snap_known` | `carries_pg` | carries | **2015** |
| 15 | **L1** | N19 his **OWN** late/early opportunity ratio | `late_ratio_w` | `carries_pg` | carries | 2014 |
| 16 | **L2** | N19 **GROUP** lift, draft round × career year | `late_lift_grp` | `carries_pg` | carries | 2014 |

**Target-season floors are set by one mechanical rule applied to every source, not per arm:** the
first target season whose *training* window contains a season with real lag-1 coverage, i.e.
(source first season) + 2. Batch 3 registered this rule for NGS separation (2016 → 2018); it is
reused verbatim. Participation 2016 → **2018 (7 target seasons)**. `snap_counts` 2013 → **2015 (10)**.
`pbp` 2009 and weekly YAC 2006 → no binding floor, so 2014 (11). **The participation arms are known
underpowered relative to the 11-season arms before they are run.**

### Multiplicity — campaign level, m = 80

**Benjamini–Hochberg at q = 0.10 across a campaign denominator of m = 80, fixed here and not moved
afterwards.** Also reported at q = 0.05, and — as a **clearly-labelled secondary that is not the
headline** — within-batch BH at m = 16.

*Why 80 and how it can be honest without knowing the other batches' counts.* Batches 4, 5, 6 and 7
are running concurrently against the same model and the same 11 seasons. Correcting inside each while
ignoring the others is the exact failure `CLAUDE.md` §6.3 names, and no shared count exists at the
moment this document is written. **80 = four batches × 20 registered tests**, declared in advance as
a planning figure and registered in `docs/ranking/factor-campaign-manifest.md`. The rule attached to
it is one-directional and is committed now:

> **If the realised campaign total exceeds 80, every batch-7 grade is recomputed at the realised
> total. If it comes in under 80, nothing is relaxed** — 80 was registered, and a denominator that
> shrinks after the results are seen is not a pre-registration.

Control arms count in m. They are expected to be uninformative and including them costs the
treatment arms power; that is the conservative direction and it is taken on purpose.

---

## 5. Decision rules, fixed now

| grade | rule |
|---|---|
| **SURVIVES** | BH-significant on E1a at q = 0.10 (**campaign m = 80**), direction better, **and** E1b < 0, **and** E2 > 0 |
| **PROJECTION-ONLY** | BH-significant better on E1a, **and** E1b < 0, but E2 ≤ 0 |
| **BOARD-NEUTRAL** | BH-significant better on E1a, but **E1b ≥ 0** |
| **RESTATEMENT** | independence gate below fails, **regardless of p-value** |
| **VOID — COVERAGE ARTIFACT** | control-arm rule below fires, **regardless of p-value** |
| **HARMFUL** | BH-significant on E1a, direction worse |
| **MARGINAL / MARGINAL-HARMFUL** | E1a 95% CI excludes zero but not BH-significant |
| **NULL** | otherwise |

**No grade in this table is "closes the RB deficit."** That is E4, it is reported as a level for
every arm against the primary's −0.0523, and it is stated in prose rather than folded into a verdict
word.

### The independence gate — the dispatch's own requirement, made mechanical

The dispatch flags **N17 and N19** as at risk of being restatements of things already measured:
receiving share overlaps the archetype work, late-season trajectory overlaps age. That is turned into
a rule rather than a caveat, and it is applied to **every** arm so N17 and N19 are not singled out
after the fact:

> Each arm's declared column is regressed on **the model's own existing RB feature set**
> (`_RB_CARRY_VOLUME ∪ _RB_TARGET_VOLUME` = `carries_pg_w, cshare_w, gshare_w, evidence, age, age2,
> ppg_w, experience, tgt_pg_w, tshare_w`), measured **on the ADP board** across the arm's target
> seasons. **R² ≥ 0.90 ⇒ RESTATEMENT**, and the arm may not be quoted as a new effect whatever its
> p-value. A second R² against `{age, age2, experience}` alone is reported for every arm, because
> that is the specific confound N19 is accused of.

Both R² values are printed **before any arm's result is computed**, in the same run.

### The leak trigger, armed in advance with a number

Batch 2 lost three arms because a companion "we know this about him" flag turned out to be **95–97%
of the effect** (`move_known`). Every batch-7 block with a coverage flag ships that flag as **its own
registered control arm** (Z1c, G1c, Y1c, P1c), and:

> **If a control arm's |E1a| is ≥ 50% of its paired treatment arm's |E1a|, the treatment arm is
> graded VOID — COVERAGE ARTIFACT**, regardless of its own p-value, and may not be quoted without
> that sentence. The treatment keeps its recorded numbers; it loses its interpretation.

**G1p is a second, sharper control on the same block**, registered because an empirical-Bayes shrunk
rate is pulled toward the prior in proportion to its denominator, so `|conversion − prior|` is a
monotone function of goal-line *volume*. G1p has identical shrinkage geometry and **zero
player-specific signal** (numerator replaced by a `Binomial(den, prior)` draw). If G1p also helps,
G1 is the geometry and not the football. This is batch 3's D1a instrument, promoted from post-hoc
diagnostic to registered arm.

Batch 2's escape hatch is re-armed unchanged: **any E1a improvement exceeding 2% of the primary's own
error is treated as a suspected leak and escalated before write-up**, per `CLAUDE.md` §8. A result
that looks too good is a finding to escalate, not to celebrate.

### Coverage gates, committed before the coverage is known on the graded population

Measured **on the ADP board**, the population the gate exists to protect, averaged across the arm's
target seasons. Below the gate the cell is marked **NO DATA**, reported as a data finding rather than
a test, and **still counts in m**.

| block | flag | gate |
|---|---|---|
| red-zone snaps | `rzsnap_known` | ≥ 0.80 |
| inside-5 | `i5_known` | ≥ 0.80 |
| YAC | `yac_known` | ≥ 0.80 |
| snap share | `snap_known` | ≥ 0.80 |
| late-season | `late_known` | ≥ 0.80 |
| receiving share | `recpts_known` | ≥ 0.80 |

### Stopping condition

All 16 tests run **once**. No arm is re-specified, re-parameterised or re-scoped after any result is
seen. Anything discovered afterwards is labelled post-hoc and carries a lower evidential standard, as
in batches 1 and 3.

**Fixed a priori and never tuned against a result:** `I5_K0 = 10` inside-5 attempts, `YAC_K0 = 25`
receptions, `LATE_WEEK = 13`, the ≥40% and ≥60% cuts (McFarland's own, used verbatim rather than
re-derived on our data), the group-cell minimum of 30 player-seasons, and `LAG_WEIGHTS = (0.55, 0.30,
0.15)` inherited from `pos_features`.

---

## 6. What the data actually is, including three corrections the dispatch's own source needs

**Measured this session, before any arm was fitted.**

| dispatch says | what is actually true | consequence |
|---|---|---|
| N16 from `pbp` `yards_after_catch`, **1999+** | **`pbp` in this database has no `yards_after_catch` column at all** — 24 columns, and the table starts in **2009**, not 1999 | the real source is `player_weekly_stats.receiving_yards_after_catch` |
| the same, 1999+ | that column is **identically zero for 2000–2005** and non-zero from **2006** (1999 holds a token 378 yards league-wide against 1,957 RB receptions) | YAC is a **2006+** feature. No binding constraint here, since features begin in 2012 — but "1999+" is wrong and would matter to any deep-sample design |
| N14 from `participation` `offense_players` × `pbp` `yardline_100`, 2016+ | correct. `participation` is **2016–2025, 478,989 rows**. `offense_players` is empty on ~8.5% of rows in 2016–2022 — **all of them non-scrimmage plays**; on rush/pass plays the missingness is **0.0000** | usable, with the arms floored at target season 2018 by the §4 rule |
| N18 `snap_counts` 2013–2025, 324,611 rows, unused by any model | correct, **and it is keyed on PFR ids, not gsis** | joined through `player_ids` (mfl pivot). **99.34% of RB player-seasons match, 99.55% snap-weighted** |

**N14 is presence, not touches, and that is the whole point.** Registry #10 is red-zone *touches* —
carries and targets inside the 20. A snap rate counts the plays the coach chose to have him on the
field for, including the ones where the ball went elsewhere. The denominator is **team red-zone plays
in the games he appeared in**, not the team's season total: a season-total denominator multiplies
role by availability, and `gshare_w` is already in every spec, so the feature would be re-encoding a
column the model already holds.

**N15's overlap with `ff_opportunity` is declared, not claimed away.** ffverse's xFP construction
models expected touchdowns from field position and is being tested concurrently by batch 6. Inside-5
conversion is a component of the same mechanism. **No independence from that arm is claimed here and
none has been established.** N15 is also **not** registry #19, which was TD-rate *shrinkage* (a change
to how `tdpc` is pooled across all carries) and measured HARMFUL; this is a covariate built from a
different denominator — goal-line attempts only.

**Every pooled prior is the modelled position's own.** RB yards-after-catch per reception runs far
above the all-position mean and inside-5 conversion is dominated by quarterback sneaks; shrinking a
lightly-used back toward an all-position constant would bias exactly the players the shrinkage exists
to protect, in a known direction.

**N19 is a late-season-weighting factor and the registry has nothing like it.** This league's playoffs
are weeks 16–17 with no reseeding, so late-season role is worth more here than in a league that ends
in week 14 — which is why it is worth a slot despite the restatement risk §5 gates.

---

## 7. Guardrails (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§6.1) | `SeasonPanel.before()` plus batch-7's own `rz_before/i5_before/yac_before/snaps_before/half_before`, each asserting `max(season) ≤ cutoff` and each logging to the same audit; per-target-season assertion that max feature cutoff < target and zero outcome reads at target |
| **Zero season-N reads** | **no batch-7 block reads season N at all.** Every arm asserts `n_preseason_proxy_reads == 0` as a `RuntimeError`, so it is proven rather than believed |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0 |
| **Multiple comparisons** (§6.3) | BH at the **campaign** level, m = 80, q = 0.10 and 0.05, denominator fixed regardless of outcome; batch-level m = 16 reported as secondary only |
| **Holdout** (§6.3) | 2025 sealed at the SQL gate and excluded at load time in every batch-7 source. Not opened |
| **Effect size** | every E1a reported as a % of the primary's own error; every candidate re-checked on the ADP board via E1b; **E4 reported as an absolute level against −0.0523** |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n, never player-seasons |
| **Coverage-flag confound** | four registered control arms plus the 50% VOID rule |
| **Shrinkage geometry confound** | one registered binomial placebo arm (G1p) |
| **Restatement confound** | the independence gate, R² ≥ 0.90 ⇒ RESTATEMENT, computed before any result |
| **Reproduction** | the batch-7 primary must reproduce **batch 3's RB primary `mae_carries` to numerical zero**; asserted in the run and printed, not assumed |

---

## 8. Who checks this, because I do not check my own work

| claim | independent check |
|---|---|
| this design, its campaign-family definition, the m = 80 denominator and its decision rules | **`strategist`** — thread opened this session |
| the result once it exists | **`fable`**, at maximum effort, separate budget |
| whether `participation` red-zone snaps and the PFR→gsis crosswalk belong in the rebuild path | **`data-ops`** |
| shipping anything that grades | **`backend`** — a handoff, never a self-merge |
