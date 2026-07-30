# Factor batch 5 — pass-catcher opportunity — pre-commitment

**Ranker, 2026-07-30. Written and committed BEFORE any arm was fitted.** Same discipline as
`factor-batch-1-precommit.md` (`d546cff`), `factor-batch-2-precommit.md` (`851a6bb`) and
`factor-batch-3-precommit.md` (`1c452a1`). If a number in the results document is not predicted by
an endpoint declared here, it is post-hoc and must be labelled so.

**Scope.** The four pass-catcher rows of `docs/research/analyst-factor-sweep-2026-07-30.md` §2a —
N1 first-read target share, N2 catchable target share and rate, N3 targets per route run, N4
receiving first downs and first downs per route run — plus §3's contested result, the direct
numerical contradiction between Heath's **0.79** and Hoopes's measured ceiling of **0.68**.

**Exploratory, not confirmatory of a shipped change.** The sealed 2025 holdout is not touched and
no holdout spend is requested. Promotion of any arm into the shipped model is a `strategist`
registration plus a `backend` handoff, not a decision this pass may make.

**Multiplicity is corrected at the CAMPAIGN level, not inside this batch.** Registration:
`docs/ranking/factor-campaign-manifest/batch-5.md`; rule and denominator:
`docs/ranking/factor-campaign-manifest/README.md`. **m_5 = 17; the correction denominator is
`M_campaign = max(Σ_b m_b, 80)`.**

---

## 1. What batch 5 exists to answer, stated before the answer is known

The sweep's own §0 says the thing that should govern the expectation here: **every headline
correlation in the public literature is measured on survivors**, and **not one of eleven shops
publishes a comparison against market ADP**. So the honest prior is that these factors look
strong in public because they are measured on qualified populations against no baseline, and that
on a bust-retaining universe measured against the incumbent projection they will mostly be null.
Batch 2 ended 12-of-12 null-or-worse. Batch 3 was written expecting mostly null. This one is
written the same way, and that sentence is here so a null cannot afterwards be re-described as
"underpowered" and a hit cannot afterwards be re-described as "expected."

Four things are specific to this batch and each is stated now so none can later be claimed as a
discovery:

1. **The dispatch's own registry correction is load-bearing and it is right.** Registry #16/#17
   were tagged `nflverse:FTN`, which cannot supply per-player routes at all — FTN charting is
   play-level with no receiver id. `participation.offense_players` is the real source. Verified
   in this database: **2016–2025, 10 seasons, every pass play carrying a full 11-man offensive
   personnel list** (measured, §5). The mis-tag has been suppressing a ten-season test as though
   it were a four-season one.
2. **Two of the four dispatched arms cannot be graded here, and that is a finding, not a
   shortfall.** §2.
3. **Route participation has never been in this project's feature space.** `CLAUDE.md` §5 lists
   it as a known gap and it is the input the founder's own coordinator example is about ("we
   expect routes run to increase"). Batch 2 §7 had to refuse the directional wording precisely
   because *"nothing in batch 2 measures routes — route participation is not in `nfl.db` at
   all."* **That sentence is now wrong**: it is derivable, as a labelled proxy, from a table that
   has been sitting in the database unused.
4. **Coverage differs by a factor of 1.6 between the two blocks in this batch** — the route arms
   get 7 target seasons, the first-down arms get 11. Effects across those two blocks are **not**
   comparable and every table must carry the season count in the row.

---

## 2. The two arms that cannot be graded, and why — settled before fitting

**N1 (first-read target share) and N2 (catchable target share / rate) are not registered as model
arms.** The reason is arithmetic on the harness, not a judgment about the football.

FTN charting begins in **2022**. It is fetchable — verified this session,
`nflreadpy.load_ftn_charting`, 29 columns, and it joins to our `pbp` on
`(season, nflverse_game_id, nflverse_play_id)` at **99.5%** of pass plays that carry a receiver
id (98.4% in 2022, 100.0% in 2023 and 2024). So the data is real and the proxy is computable.

What is not computable is a **graded** result. `pos_eval.WalkForward` builds a training pair for
season *s* from features in *s−1* and outcomes in *s*, and projects target season *N* from
training pairs whose outcome season is ≤ *N−1*:

| requirement | consequence |
|---|---|
| feature season ≥ 2022 | target season N ≥ 2023 |
| at least one **training** pair carrying the feature | training season s ≥ 2023, so N ≥ 2024 |
| 2025 sealed (`pos_data.HOLDOUT_SEASON`) | N ≤ 2024 |

**Exactly one target season: 2024.** The endpoint is a season-paired difference with a
season-block bootstrap; at n = 1 it has no sampling distribution. An arm registered here would
consume campaign m to buy a guaranteed NULL and would then be misread as evidence against the
factor. It is therefore declared **NOT REGISTERED — UNGRADEABLE, n_seasons = 1**, which is a
different statement from "tested and null" and must not be collapsed into one.

**What is done with N1/N2 instead:** they go into family **F3** (§6), the descriptive replication
that settles the 0.79-vs-0.68 contradiction. That question does not need the walk-forward — it is
a cross-sectional correlation of a season-Y statistic against season-Y+1 scoring, which is exactly
what both shops published. It gets **two** season pairs (2022→2023, 2023→2024) and that limit is
stated on every number rather than discovered afterwards.

**The proxy caveat travels with every N1/N2 number, on screen and in the write-up.** Ours is
`read_thrown == '1'` from FTN joined to the pbp receiver id. **It is not Heath's charted
definition**, whose filters are unstated, and it is a per-play flag we did not chart. Under
`docs/research/analyst-factor-sweep-2026-07-30.md` §4's licensing note, anything proxied off a
paid definition is labelled a proxy and never presented as the named metric.

---

## 3. Harness — unchanged, deliberately

`experiments/bottomup/components`, the walk-forward from `component-model-multipos-precommit.md`,
reused exactly as batches 2 and 3 reused it.

| | |
|---|---|
| Target seasons | **2014–2024 (11)** for the first-down block; **2018–2024 (7)** for the route block — see §4 |
| Features | seasons ≤ N−1 only. **No batch-5 block reads season N at all** |
| Training | (features, outcome) pairs whose OUTCOME season is ≤ N−1; `first_feature_season` unchanged |
| Universe | frozen from pre-N information; busts retained, scoring zero |
| Holdout | 2025 sealed at the SQL gate (`pos_data.HOLDOUT_SEASON`). **Not opened** |
| Uncertainty | season-block bootstrap, 4,000 reps, **seasons** the resampling unit |

**Every arm differs from its position's primary by exactly the feature block it declares.** No arm
changes the availability sub-model, the bonus machinery, the universe or the scoring.

**Batch 5 does not touch `pos_data.py`.** Three other factor agents are working the same checkout;
adding fields to the shared `SeasonPanel` dataclass is how two agents silently overwrite each
other. The two new sources are loaded and gated inside
`experiments/bottomup/factors/factor_features5.py`, by a gate that reproduces `SeasonPanel`'s
semantics exactly — refuses any cutoff ≥ 2025, asserts `max(season) <= cutoff` on the way out, and
appends to the panel's own `access_log` under the **`feature`** tag. Consequence, and it is a
strong one: **every batch-5 arm can be proven to have made zero season-N proxy reads**, because
`allow_preseason_proxy=False` is left at its default and the audit assertion in `WalkForward.run`
fires on any violation.

---

## 4. The two blocks, their sources, and the season floors — fixed before fitting

### Block R — routes, from `participation`

A **route** here is: *the player's gsis id appears in `participation.offense_players` on a play
`pbp` marks `pass = 1`.* Labelled a proxy, with three named departures from a charted route count,
none of them discovered afterwards:

1. **On the field ≠ ran a route.** A back kept in to block, or a tight end chipping, is counted.
   The error is largest at RB and smallest at WR, which is exactly the direction that would make
   an RB result look better than it is. The RB cells are read with that in mind.
2. **The denominator is inflated ~10–20%.** `pass = 1` includes sacks, scrambles and plays wiped
   by penalty, and our `pbp` table has no `season_type` column, so postseason plays are in — the
   same known and stated condition batch 3 accepted for `expl10`. Measured: 22,463 joined pass
   plays in 2022 against roughly 20,900 league dropbacks. This affects the **level** of a rate,
   not its look-ahead status and not the within-season ordering of players, and every player in a
   season is inflated by the same mechanism.
3. **No position filter is available on the participation row** (`offense_positions` is NULL
   throughout), so position comes from `player_weekly_stats`. Only universe positions are ever
   computed.

**Season floor, fixed now by the same rule batch 3 fixed for NGS.** Participation starts 2016, so
a target season needs its *training window* to contain at least one season with real route
coverage: training season s ≥ 2017, hence **first target season 2018**. **7 target seasons,
2018–2024, and that is fewer than the first-down block's 11 — stated here so the two blocks are
never compared without it.**

### Block D — receiving first downs, from `ff_opportunity`

`ff_opportunity` (ffverse `ffopportunity`, xgboost over nflverse pbp, versioned, already ingested)
carries `rec_first_down` per player-week. The dispatch pointed at `pbp.first_down_pass`; **that
column does not exist in this database's `pbp` table** (25 columns, no `ydstogo` either, so it
cannot be derived), and `ff_opportunity` is the working source. Effective coverage in the panel's
own window is **2009+**, because that is when `player_weekly_stats` targets begin.

**Coverage measured before any arm was fitted**, players with ≥15 targets in a season (the WR/TE
universe bar), 2009–2024: **missing rate 0.0000 at WR (n=2,294), TE (n=1,037) and RB (n=1,102),
in every season.** Target counts agree with the box score at r = 0.9985, mean absolute difference
0.69 targets.

**Consequence, committed in advance: block D gets no control arm, and the reason is a
measurement.** Batch 3's rule is that a coverage flag ships as its own registered control because
"has a row" can be 95–97% of an apparent effect. Here "has a row" is constant at 1.000 on the
graded population, so a control arm would be a zero-variance column — it cannot carry an effect
and it would consume campaign m for nothing. **The route block, whose flag is not constant, keeps
its controls (three of them).** If measured `fd_known` on the ADP board comes in below **0.95**,
the D arms are graded **NO DATA** and still count in m.

### The features, defined before fitting

All use the existing `LAG_WEIGHTS = (0.55, 0.30, 0.15)` over three prior seasons, weighted by
games share, exactly as `pos_features.build_features` does — **not** re-tuned, and no new decay
parameter is introduced.

| feature | definition | shrinkage |
|---|---|---|
| `tprr_w` | targets ÷ routes, empirical-Bayes shrunk to the pooled league rate | `TPRR_K0 = 100` routes |
| `rpg_w` | routes ÷ games played | none |
| `fdrr_w` | receiving first downs ÷ routes, EB shrunk to pooled | `TPRR_K0 = 100` routes |
| `routes_known` | 1 if the player has ≥1 route in any of the three prior seasons | — |
| `fd_pg_w` | receiving first downs ÷ games played | none |
| `fdpt_w` | receiving first downs ÷ targets, EB shrunk to pooled | `FDPT_K0 = 20` targets |
| `fd_known` | 1 if an `ff_opportunity` row exists in N−1, or the player had 0 targets in N−1 | — |

**`TPRR_K0 = 100` and `FDPT_K0 = 20` are fixed a priori and never tuned against a result** —
100 routes is a few games of a rotational receiver, 20 targets is just above the universe's own
15-target bar. Same discipline as batch 3's `EXPL_K0 = 50`.

Unknowns are filled with the same-season **median of what is known**, never 0 — batch 3's rule,
restated: a zero is a claim about the player, a median is an admission that we do not know.

---

## 5. Endpoints, fixed now

**E1a — THE FDR ENDPOINT. Out-of-sample MAE of the one declared component, full universe.**
Arm − primary, paired by season, season-block bootstrap, 4,000 reps. **Negative = better.** Every
arm in this batch projects the `targets` component, so all 17 numbers are on one scale — but
**not on one season count**, and the season count is printed in every row.

**E1b — A REQUIRED DIRECTION CHECK, NOT THE SIGNIFICANCE TEST.** The same MAE restricted to
players on the consensus ADP board, `adpsub_mae_targets`, **7 seasons (2018–2024)**. Batch 2's
reasoning stands unchanged: a family this size on 7 seasons returns all-NULL regardless of the
truth, so E1b is a **necessary condition** and not the test. An arm significant on E1a but not
better on E1b is graded **BOARD-NEUTRAL** and is explicitly not an edge.

**E2 — the bar that matters, NOT in the FDR family. ADP-board Spearman, arm − primary**, 7
seasons. `CLAUDE.md` §6.5. **Known underpowered before it is run** at WR and TE
(`component-model-rb-qb-te-pass-1.md` §1). Stated here so it cannot be produced afterwards as a
caveat.

**Exactly one E1 component per cell.** Reporting the best of several components per cell would be
selection on the outcome, which is what this document exists to stop.

**§6.5 discipline, restated because this batch is unusually tempting on it:** the headline is the
comparison against the incumbent, never a raw correlation. That applies to F3 as much as to F1 —
an r of 0.79 for a factor is not a result; **0.79 against prior FPG's number on the same
population** is the result.

---

## 6. Family F3 — the contested 0.79-vs-0.68 result. Descriptive, outside the FDR family

The sweep §3 records a direct numerical contradiction: Heath puts first-read target share at
**0.79** to next-season PPR FPG; Hoopes's systematic sweep of 23 rate stats puts the ceiling at
**prior FPG itself, 0.68**, with the best rate stat at 0.59. 0.79 exceeds Hoopes's entire list.
Either the samples differ materially or first-read share is the single best public WR input.

**Both numbers are on survivor-filtered populations, so both are upper bounds, not our expected
effect.** That is why the design measures *the same predictors, on the same season pairs, under
both a survivor filter and our own bust-retaining universe.* The contradiction is resolved by
whether it survives being put on one population — not by whether we can reproduce either number.

**Endpoint E4:** cross-sectional correlation of a season-Y predictor against season-Y+1 fantasy
points per game **under this league's scoring** (half-PPR with the stacking yardage bonuses, as
the panel computes it). Both Spearman and Pearson are reported, because neither shop states which
it used and the answer can differ. WR is the primary position (the literature is WR-centric); TE
and RB are reported alongside and labelled thinner.

**Populations, both run for every predictor:**

| id | filter | why |
|---|---|---|
| **S** | qualified in **both** Y and Y+1 — ≥30 targets each year for target-based predictors, ≥235 routes each year for route-based ones | reproduces the shops' stated filters, which is the only way their numbers mean anything |
| **U** | the frozen pre-season universe for Y+1, busts retained and scored 0 | `CLAUDE.md` §6.2. This is the population a draft actually faces |

**Predictors, all measured in season Y:**

| predictor | source | season pairs |
|---|---|---|
| **prior FPG** — the incumbent, Hoopes's 0.68 | panel | 2009→2010 … 2023→2024 (15) |
| target share | panel | 15 |
| targets per game | panel | 15 |
| **first-read target share (PROXY)** | FTN `read_thrown == '1'` × pbp receiver | **2022→2023, 2023→2024 (2)** |
| **catchable target share (PROXY)** | FTN `is_catchable_ball` | **2** |
| **catchable rate (PROXY)** | FTN | **2** |
| TPRR | participation | 2016→2017 … 2023→2024 (8) |
| YPRR | participation | 8 |
| 1D per route run | participation × ff_opportunity | 8 |
| 1D per game | ff_opportunity | 15 |
| 1D per target | ff_opportunity | 15 |

**The reported quantity is `r(predictor) − r(prior FPG)` on the same population and the same
season pairs**, with a season-block bootstrap CI where the pair count is ≥ 5 and per-season point
estimates plus a **player bootstrap** where it is 2. **With two season pairs the season-level
uncertainty is unbounded and no interval over seasons is quoted for the FTN predictors.** That
sentence is written before the numbers exist.

**F3 is not in the FDR family and carries no BH claim.** It refits nothing, it changes nothing in
the model, and it cannot promote a factor. It answers a question about the published literature.

---

## 7. Decision rules, fixed now

| grade | rule |
|---|---|
| **SURVIVES** | BH-significant on E1a at q=0.10 (campaign `M_campaign`), direction better, **and** E1b < 0, **and** E2 > 0 |
| **PROJECTION-ONLY** | BH-significant better on E1a, **and** E1b < 0, but E2 ≤ 0 |
| **BOARD-NEUTRAL** | BH-significant better on E1a, but **E1b ≥ 0** |
| **HARMFUL** | BH-significant on E1a, direction worse |
| **MARGINAL / MARGINAL-HARMFUL** | E1a 95% CI excludes zero but not BH-significant |
| **NULL** | otherwise |
| **NO DATA** | coverage gate failed. Still counts in m |
| **VOID — COVERAGE ARTIFACT** | see the leak trigger below |

### The leak trigger, armed in advance with a number — batch 2's lesson, batch 3's rule

Batch 2 lost three arms because a companion "we know his club" flag turned out to be **95–97% of
the effect**. The rule is imported unchanged and its scope is stated explicitly:

> **If a control arm's |E1a| is ≥ 50% of a treatment arm's |E1a| at the same position and block,
> that treatment arm is graded VOID — COVERAGE ARTIFACT**, regardless of its own p-value, and may
> not be quoted without that sentence. The treatment keeps its recorded numbers; it loses its
> interpretation.

**`R1c` is the control for R1, R2 and R3 at its position** — all three treatments are built off
the same `routes_known` support, so one flag controls all three. Block D has no control **and the
justification is the measured 1.000 coverage in §4, not convenience**; if the ADP-board
measurement disagrees the D arms go NO DATA.

**The too-good escape hatch is re-armed unchanged:** any E1a improvement exceeding **2% of the
primary's own error** is treated as a suspected leak and escalated before write-up, per
`CLAUDE.md` §8. A result that looks too good is a finding to escalate, not to celebrate. The
specific leak to fear in this batch is that routes and first downs are both **downstream of
targets**, which is the component being projected — a first-down count is a function of receptions
which is a function of targets. That is a collinearity, not a look-ahead, and it is why the
declared feature set is dominated by **rates** (`tprr`, `fdrr`, `fdpt`) rather than counts. The
two count features that are registered, `rpg_w` and `fd_pg_w`, are registered **because** they are
the volume-flavoured versions and their behaviour against the rate versions is informative.

### Coverage gates, measured on the ADP board — the population the gate protects

| block | flag | gate | below it |
|---|---|---|---|
| routes | `routes_known` | ≥ **0.80** | cell **NO DATA**, reported as a data finding, still counts in m = 17 |
| firstdown | `fd_known` | ≥ **0.95** | same |

### Stopping condition

All 17 tests run **once**. No arm is re-specified, re-parameterised or re-scoped after any result
is seen. Anything discovered afterwards is labelled post-hoc and carries a lower evidential
standard, as in batch 1 §4.

**Stated before measurement:** if R1 (TPRR) is null at WR and TE, then registry #16/#17 are
measured-and-dead on their ten-season sample and must not be re-specified a third time on the
grounds that the sample was short. Ten seasons is the sample the corrected tag buys; that is the
test.

---

## 8. Guardrails (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§6.1) | `SeasonPanel.before()` plus batch-5's own `routes_before()` / `fd_before()` gates, which refuse any cutoff ≥ 2025 and assert `max(season) <= cutoff`; per-target-season audit asserting max feature cutoff and max outcome season strictly < target and zero outcome reads at target |
| **Zero season-N reads** | no batch-5 block reads season N. `allow_preseason_proxy` is left **False** on every arm, so `WalkForward.run` raises on any proxy read. This is a proof, not a convention |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0. F3 additionally runs both the survivor filter **and** the frozen universe, side by side, because that contrast is the whole point of F3 |
| **Multiple comparisons** (§6.3) | BH across the **campaign**, `M_campaign = max(Σ_b m_b, 80)`, q = 0.10 and 0.05, denominator fixed regardless of outcome. Batch-local m = 17 reported as a labelled secondary only |
| **Holdout** (§6.3) | 2025 sealed at the SQL gate and at batch-5's own gates. Not opened. FTN is fetched for 2022–2024 only |
| **Effect size** | every E1a reported as a % of the primary's own error, and every candidate re-checked on the ADP board via E1b |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n, never player-seasons |
| **Unequal support** | every row prints its season count; route arms (7) and first-down arms (11) are never compared without it |
| **Coverage-flag confound** | three registered control arms on block R, the 50% VOID rule, and a measured justification for block D having none |
| **Reproduction** | batches 1–3 must reproduce **bit-for-bit** under the extended feature builder; asserted in code, not assumed |
| **Proxy labelling** | routes, TPRR, 1D/RR, first-read share and catchable share are all labelled proxies wherever they appear, per the sweep's §4 licensing note |

---

## 9. Who checks this, because I do not check my own work

| claim | independent check |
|---|---|
| this design, the campaign family definition and the decision rules | **`strategist`** — thread opened this session, before results are read |
| the result once it exists, and specifically whether the route proxy's blocking-snap contamination invalidates the RB cells | **`fable`**, at maximum effort, separate budget |
| **FTN charting is not in `nfl.db` and is fetched ad hoc by this batch** — whether it should be ingested and versioned like every other source | **`data-ops`** — thread opened this session |
| the F3 conclusion about the published literature | **`researcher`** — thread opened this session, since the contradiction is between two of its own cited sources |
| shipping anything that grades | **`backend`** — a handoff, never a self-merge |
