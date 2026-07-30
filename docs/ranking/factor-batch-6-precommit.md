# Factor batch 6 — pre-commitment

**Ranker, 2026-07-30. Written and committed BEFORE any arm was fitted.** Same discipline as
`factor-batch-1-precommit.md` (`d546cff`), `factor-batch-2-precommit.md` (`851a6bb`) and
`factor-batch-3-precommit.md` (`1c452a1`). If a number in the results document is not predicted by
an endpoint declared here, it is post-hoc and must be labelled so.

**Scope.** Three rows: `analyst-factor-sweep-2026-07-30.md` §2b **N10** (passing efficiency over
volume) and **N11** (sack-avoidance rate), plus `docs/test-registry.md` **#18** (expected fantasy
points), which the sweep re-costed from effort H to a download.

**Exploratory, not confirmatory of a shipped change.** The sealed 2025 holdout is not touched and no
holdout spend is requested. Promotion of any arm into the shipped model is a `strategist`
registration plus a `backend` handoff, not a decision this pass may make.

**Batch 3 is concurrently testing QB rushing attempts (arms A1/A2). No arm here touches the rushing
volume spec.** Batch 6 changes the *passing* spec only, so the two batches are separable by
construction rather than by agreement.

---

## 0. A measured correction to the dispatch, made before any arm was fitted

The dispatch that commissioned this batch states that `passing_cpoe` in `player_weekly_stats` is
"only **11%** populated" and instructs that EPA be derived from `pbp` instead. **Both halves are
wrong on this database, and the correction makes the batch stronger rather than weaker.**

| claim | measured here |
|---|---|
| `passing_cpoe` ~11% populated | **2.7%** across all rows — because a wide receiver has no completion percentage. On the rows that can have one (QB, ≥10 attempts, 2006+): **99.9%** |
| EPA must come from `pbp` | **`passing_epa` is 100% populated** for QB weeks with ≥10 attempts, **1999–2025**, in `player_weekly_stats` |
| `pbp` can supply EPA | **`pbp` as ingested has no `epa`, `cpoe`, `sack` or `success` column at all** — 24 columns, `PRAGMA table_info(pbp)`. Deriving EPA from it is impossible, not merely unnecessary |

Scale check against published values, 2023, EPA per dropback: Purdy **0.305**, Tua **0.207**, Dak
**0.192**, Allen **0.152**. These are the right numbers.

**Consequence:** the strongest external QB claim in the whole sweep — EPA/dropback, "stickiest QB
stat since 2021, r≈0.60" — is testable here on the **deep sample, eleven target seasons**, not
blocked and not proxied. Sack rate likewise: `sacks_suffered` is 100% populated 1999+, so N11 needs
neither `pbp` nor `pfr_advstats_pass`.

---

## 1. What batch 6 exists to answer, stated before the answer is known

**The registry contains zero QB-specific factors, and all twelve of the shipped board's largest
top-100 disagreements with consensus are QBs or TEs** — produced by a positional tilt with no
QB-specific input behind it. The board is making its biggest bets at QB blind. Batch 3 is testing QB
*rushing*; batch 6 tests everything about QB *passing*.

The honest prior, written down now: **batch 2 ended 12-of-12 null-or-worse and batch 3's own
pre-commitment recorded that most of these will be null.** Four of five registered prediction sets in
this project were materially wrong and every miss over-credited a situation story. Nothing below is
expected to survive. This document exists so that a null cannot be re-described afterwards as
"underpowered" and a hit cannot be re-described afterwards as "expected."

Three things are stated now so they cannot be claimed later as discoveries:

1. **These arms test efficiency as a predictor of future OPPORTUNITY, not of future efficiency.** See
   §4a. That is a real limitation of the harness and it is registered, not discovered.
2. **ANY/A and passer rating are re-weightings of quantities the model already holds** (`ypa`,
   `tdpa`, `intpa` are already shrunk own-rates). The genuinely new information in this batch is
   **CPOE** (needs an expected-completion model), **EPA** (needs an expected-points model) and
   **sacks** (which this league does not score at all, and which the QB model's rate ledger does not
   contain in any form).
3. **xFP is a model output, not a measurement, and it overlaps our own inputs.** §6 states what it is
   built from, in what scoring, and which of its effects would be a repackaging. A large xFP effect
   is a suspected overlap first and a finding second.

---

## 2. Harness — unchanged, deliberately

`experiments/bottomup/components`, the walk-forward from `component-model-multipos-precommit.md`,
reused exactly as batches 2 and 3 reused it.

| | |
|---|---|
| Target seasons | **2014–2024 (11)** for every arm in the batch. No arm has a shorter window |
| Features | seasons ≤ N−1 only |
| Training | (features, outcome) pairs whose OUTCOME season is ≤ N−1; `first_feature_season = 2012` at every position |
| Universe | frozen from pre-N information; busts retained, scoring zero |
| Holdout | 2025 sealed at the SQL gate (`pos_data.HOLDOUT_SEASON`). **Not opened** |
| Uncertainty | season-block bootstrap, 4,000 reps, **seasons** the resampling unit |

**Every arm differs from its position's primary by exactly the feature block it declares.** No arm
changes the availability sub-model, the bonus machinery, the universe or the scoring.

**No arm in this batch reads season N.** Batches 1–3 each carried a `proxy`-tagged season-N read
(Week-1 depth chart, pre-season roster, pre-season coordinators). Batch 6 has none: every source is
seasons ≤ N−1. So **every arm runs with `allow_preseason_proxy=False` and the harness PROVES
`n_preseason_proxy_reads == 0`** rather than the write-up asserting it.

**The two new sources are loaded behind batch 6's own cutoff gate, in batch 6's own module, and
append the same `("feature", cutoff)` entry to `panel.access_log` that `panel.before()` would** — so
the existing look-ahead audit covers them without `pos_data.py` being edited while three factor
batches are running against it.

---

## 3. Endpoints, fixed now

Identical to batches 2 and 3, so every batch-6 number is directly comparable to their tables.

**E1a — THE CAMPAIGN FDR ENDPOINT. Out-of-sample MAE of the one declared component, full universe.**
Arm − primary, paired by season, 11 seasons, season-block bootstrap, 4,000 reps. **Negative =
better.**

**E1b — A REQUIRED DIRECTION CHECK, NOT THE SIGNIFICANCE TEST.** The same MAE restricted to players
on the consensus ADP board, **7 seasons (2018–2024)**, metric `adpsub_mae_*`. A 23-arm BH family on 7
seasons returns all-NULL regardless of the truth, so E1b is a necessary condition and not the test.
An arm significant on E1a but **not** better on E1b is graded **BOARD-NEUTRAL** and is explicitly not
an edge.

**E2 — the bar that matters, NOT in the FDR family. ADP-board Spearman, arm − primary**, 7 seasons.
`CLAUDE.md` §6.5. **Known underpowered before it is run at QB, WR and TE**
(`component-model-rb-qb-te-pass-1.md` §1); only RB resolves anything. Stated here so it cannot be
produced afterwards as a caveat.

**Declared secondaries, reported for every arm, carrying no significance claim and not in the family:**
`mae_pass_yards` (QB) — because the passing arms change attempts and attempts drive projected yards —
and full-universe `rho_model`.

**Exactly one E1 component per cell**, declared in §4. Reporting the best of several components per
cell would be selection on the outcome, which is what this document exists to stop.

| position | E1 component | volume spec the arm modifies |
|---|---|---|
| QB | `attempts` | `att_pg` |
| RB | `carries` | `carries_pg` |
| WR | `targets` | `tpg` |
| TE | `targets` | `tpg` |

**The arm modifies only the volume spec that produces its declared E1 component.** Batch 2 modified
both RB specs; this batch does not, because "the one thing that changed" should be one thing.

---

## 4. The arms — declared in full. Batch m = 23

### Family P — passing efficiency over volume (N10), QB only

| # | id | the ONE thing that changes | external claim being tested |
|---|---|---|---|
| 1 | **P1** | add `epa_db_w` to `att_pg` | Bruchhaus, SumerSports: EPA/dropback **stickiest QB stat since 2021, r≈0.60** |
| 2 | **P2** | add `anya_w` to `att_pg` | Heath: efficiency beats total attempts |
| 3 | **P3** | add `pratg_w` to `att_pg` | Heath: passer rating beats total pass attempts; completion % near bottom at 0.154 |
| 4 | **P4** | add `cpoe_w` to `att_pg` | the only efficiency metric here requiring a model the box score cannot produce |
| 5 | **P4c** | add `cpoe_known` **only** — CONTROL | — |
| 6 | **Pc** | add `qbeff_known` **only** — CONTROL | — |

### Family K — sack avoidance (N11), QB only

| # | id | the ONE thing that changes | external claim |
|---|---|---|---|
| 7 | **K1** | add `sackrate_w` to `att_pg` | SumerSports: r≈**0.50** YoY, second-stickiest QB metric |

`Pc` is K1's coverage control as well as P1/P2/P3's — same flag, same population, and registering it
twice would inflate m with a duplicate rather than protect anything.

**`pfr_advstats_pass` (pressure rate, pressure-to-sack conversion) is deliberately NOT an arm.** It
starts in 2018, which is five target seasons — a window this project has already measured as unable
to resolve anything at any position. Deferred with the reason stated in advance rather than run and
then explained away.

### Family X — expected fantasy points (registry #18), all four positions

| # | id | the ONE thing that changes | positions |
|---|---|---|---|
| 8–11 | **X1** | **add** `xfp_pg_w` to the E1 volume spec | QB, RB, WR, TE |
| 12–15 | **X2** | **replace** `ppg_w` with `xfp_pg_w` in the E1 volume spec | QB, RB, WR, TE |
| 16–19 | **X3** | **add** `xfp_resid_pg_w` — realised minus expected, the luck term | QB, RB, WR, TE |
| 20–23 | **X4c** | add `xfp_known` **only** — CONTROL | QB, RB, WR, TE |

**X2 is the registry's actual claim, and it is the interesting one.** The volume specs already carry
`ppg_w`, realised prior points per game. X2 swaps it for *expected* prior points per game. If
isolating luck from skill is real, the expected version is better; if xFP is a repackaging of the
usage the model already holds, it is a wash. X1 (both) and X3 (the residual alone) bracket it.

**Registered directional prediction for X3, stated before fitting:** if the luck story is right,
`xfp_resid_pg_w` should carry a **negative** coefficient — over-performance regresses. A positive
fitted coefficient would mean the residual is measuring persistent skill the expectation model
misses, which is a different finding and must be reported as one.

### 4a. What these arms do NOT test, registered as a limitation rather than discovered as one

Every arm enters through a **volume** spec, so what is measured is *"does last season's efficiency
predict this season's opportunity?"* — the benching channel, which is the dominant fantasy risk at
quarterback. What is **not** measured is *"does last season's efficiency predict this season's
efficiency beyond the player's own shrunk lagged rate?"*

That second question needs a covariate on a `ShrunkRate`, and `pos_model.ShrunkRate` has no covariate
mechanism. Adding one means editing shared model code that three concurrent factor batches depend on
and that batches 1–3 must keep reproducing bit-for-bit. **Deferred on those grounds, named here, and
handed to `strategist` as the specification question it is.** The declared secondary
`mae_pass_yards` partly observes the gap; it does not close it.

### Multiplicity

**The family is the campaign, not the batch.** Batch 6 registers **m = 23** into
`docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`, the shared manifest all concurrent
factor batches register into. Benjamini–Hochberg at **q = 0.10 across the campaign denominator** =
the sum of every `m` in that file. Also reported at q = 0.05, and — clearly labelled as secondary —
at the batch-local m = 23.

**Concurrency, handled rather than hoped about.** Batches 4 and 5 run at the same time and their m is
not knowable at the moment this batch computes BH. So for **every arm that survives, the results
document must report its BREAKING m** — the largest campaign denominator at which it would still
clear BH at q = 0.10. An arm whose breaking m falls below the final campaign total loses its claim,
and any reader can check that against the manifest without rerunning anything.

Control arms count in m. They are expected to be uninformative and including them costs the treatment
arms power; that is the conservative direction and it is taken on purpose.

---

## 5. Decision rules, fixed now

| grade | rule |
|---|---|
| **SURVIVES** | BH-significant on E1a at q=0.10 (campaign m), direction better, **and** E1b < 0, **and** E2 > 0 |
| **PROJECTION-ONLY** | BH-significant better on E1a, **and** E1b < 0, but E2 ≤ 0 |
| **BOARD-NEUTRAL** | BH-significant better on E1a, but **E1b ≥ 0** |
| **HARMFUL** | BH-significant on E1a, direction worse |
| **MARGINAL / MARGINAL-HARMFUL** | E1a 95% CI excludes zero but not BH-significant |
| **NULL** | otherwise |

### The leak trigger, armed in advance with a number — batch 2's, unchanged

Batch 2 lost three arms because a companion "we know his club" flag turned out to be **95–97% of the
effect**. Every batch-6 block ships its coverage flag as its own registered control arm (Pc, P4c,
X4c), and:

> **If a control arm's |E1a| is ≥ 50% of its paired treatment arm's |E1a|, the treatment arm is
> graded VOID — COVERAGE ARTIFACT**, regardless of its own p-value, and may not be quoted without
> that sentence. The treatment keeps its recorded numbers; it loses its interpretation.

Pairings, fixed now: **Pc** → P1, P2, P3, K1. **P4c** → P4. **X4c at position p** → X1, X2, X3 at
that same position.

Additionally: **any E1a improvement exceeding 2% of the primary's own error is treated as a suspected
leak and escalated before write-up**, per `CLAUDE.md` §8.

### The xFP-specific trigger, which is stricter and separate

xFP is a *model output* whose inputs overlap ours, so the usual leak trigger is not sufficient.

> **Any X arm exceeding the 2% threshold is escalated as a SUSPECTED OVERLAP, not published as a
> finding**, until the overlap diagnostic below rules it out.

**The overlap diagnostic is required regardless of result** — it is a description, not a test, and it
costs nothing: per position, the correlation of `xfp_pg_w` with `ppg_w` and with the E1 volume
spec's own lagged volume column. If `corr(xfp_pg_w, ppg_w) > 0.95`, X1/X2 are reported as **a
restatement of `ppg_w`** whatever their p-values say.

### Coverage gates, committed before the coverage is known on the graded population

Measured **on the ADP board**, the population the gate exists to protect, averaged across the arm's
eleven target seasons:

| flag | gate | below it |
|---|---|---|
| `qbeff_known` (QB) | ≥ **0.80** | P1, P2, P3, K1 cells marked **NO DATA**, reported as a data finding, **still counting in m = 23** |
| `cpoe_known` (QB) | ≥ **0.80** | P4 same |
| `xfp_known` (per position) | ≥ **0.80** | X1, X2, X3 at that position same |

### Stopping condition

All 23 tests run **once**. No arm is re-specified, re-parameterised or re-scoped after any result is
seen. Anything discovered afterwards is labelled post-hoc and carries a lower evidential standard.

**Stated before measurement:** if P1–P4 and K1 are all null, then **passing efficiency does not
predict quarterback opportunity in this model on eleven seasons**, N10 and N11 are measured-and-dead
on this specification, and the correct next move is the rate-channel specification of §4a — **not a
third re-specification of the same volume arms.**

---

## 6. What xFP actually is, before it is used

`ff_opportunity` is the ffverse `ffopportunity` package's output: prebuilt **xgboost models over
nflverse play-by-play** predicting, per play, expected completions / yards / touchdowns / first downs
/ two-point conversions / interceptions from **play context** — down, distance, yardline, air yards,
pass location. It prices the **opportunity, not the player**: two receivers running the same route
from the same spot on the same down get the same expected value. Those per-play expectations are
summed and converted to fantasy points.

**Three consequences, none optional to state.**

1. **It is full PPR, not this league.** Verified rather than assumed: Jahan Dotson, 2023 REG, 49
   receptions / 518 yards / 4 TD, and `total_fantasy_points` = **124.8** = 49×1.0 + 51.8 + 24.0
   exactly. No yardage bonuses. So `total_fantasy_points_exp` is **not** "expected points in our
   league" and is used here only as a **usage-quality index**. Anything on screen calling it expected
   points would be a false claim about our own product.

2. **It overlaps what the model already holds.** Expected receiving points are close to a nonlinear
   function of targets and air-yards context, and the volume specs already carry `tpg_w`, `tshare_w`,
   `adot` and `ppg_w`. The genuinely new content is the removal of realised-TD noise — and registry
   **#19 already measured that the model's existing empirical-Bayes TD shrinkage extracts most of
   it** (discarding own TD rate was HARMFUL at all four positions, up to +4.0% of QB error). That is
   the specific reason this batch registers a *small or null* expectation for X1/X2 in advance.

3. **The model was fitted on all seasons, including the target season.** The published artifact is
   one global play-context map trained on 2006–current and cannot be refitted per season from here.
   It puts no player-specific season-N information into an N−1 feature — the map has no player
   identity in it — but it is a real, non-zero, non-player-specific contamination. Named, bounded,
   not hidden. It is a second reason a large X effect is escalated rather than celebrated.

**Reproducibility, and it is a gap.** `ff_opportunity.model_version_requested` records the literal
**`latest`** and nothing else, because `nflreadpy.load_ff_opportunity` accepts only `"latest"` or
`"v1.0.0"` and the source exposes no resolved semantic version at read time (the release tag is
literally `latest-data`). The only real anchor this project holds is the ingest timestamp,
**`2026-07-30T19:55:20Z`**, `nflreadpy 0.1.5`, 105,903 rows, 2006–2025. **If upstream re-releases
`latest-data`, this result becomes unreproducible and nothing in the data would show it.** Flagged to
`data-ops` as a thread: pinning `v1.0.0` — or storing the asset checksum — is the fix, and it is
cheap.

**REG-season filter.** `ff_opportunity` has no `season_type` column and does carry playoff weeks (max
week 21 pre-2021, 22 after). Rows are filtered to `week <= season_length(season) + 1`. Without it a
player's per-game xFP would silently include January.

**Convention shared with `ppg_w`, chosen so an arm is one change and not two.** `xfp_pg_w` uses the
identical weighting `pos_features` uses for `ppg_w` — weight `LAG_WEIGHTS[k] × min(gshare_k, 1)`, a
lag with no source row contributing 0 to the numerator and its full weight to the denominator.
Median-imputing missing lags instead would have made X2 differ by two things. The coverage difference
that convention creates is exactly what `xfp_known` (X4c) exists to detect.

---

## 7. Descriptive secondaries — outside the family, carrying no claim

Reported because the founder's question is "does QB now have any input the board can use", and a
component MAE does not answer it on its own. **None of these is a test, none enters m, and none may
be quoted as a finding.**

1. **YoY persistence of each QB efficiency metric on our own data**, busts retained — the direct
   check on SumerSports' r≈0.60 (EPA/dropback) and r≈0.50 (sack rate), which were measured on
   survivors and are therefore upper bounds under `CLAUDE.md` §6.2.
2. **Spearman of each lagged metric against next-season QB fantasy points under this league's rules.**
3. **The same, against the residual of realised points on consensus ADP** — i.e. does the metric carry
   anything the market has not already priced. This is the decision-relevant descriptive number and
   it is the one most likely to be misread as a finding, so: **n = 7 seasons, it is descriptive, and
   `CLAUDE.md` §6.5 says a beats-consensus claim cannot reach significance on this sample.**
4. **The xFP overlap diagnostic** required by §5.

---

## 8. Guardrails (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§6.1) | `SeasonPanel.before()` gate plus batch 6's own gate, which appends the same `("feature", cutoff)` audit entry; per-target-season audit asserting max feature cutoff and max outcome season strictly < target and zero outcome reads at target |
| **Season-N reads** | **there are none.** Every arm runs `allow_preseason_proxy=False`, so `n_preseason_proxy_reads == 0` is a `RuntimeError` if violated, not a claim |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0 |
| **Multiple comparisons** (§6.3) | BH across the **campaign**, denominator from the shared manifest, q = 0.10 and 0.05, plus a breaking-m per survivor for the batches still running |
| **Holdout** (§6.3) | 2025 sealed at the SQL gate. Not opened |
| **Effect size** | every E1a reported as a % of the primary's own error, and every candidate re-checked on the ADP board via E1b |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n, never player-seasons |
| **Coverage-flag confound** | three registered control arms (Pc, P4c, X4c) plus the 50% VOID rule |
| **Model-output overlap** | §6 states what xFP is built from and in what scoring; the overlap diagnostic is mandatory regardless of result |
| **Reproduction** | batches 1–3 must reproduce **bit-for-bit** under the extended feature builder; asserted, not assumed — `blocks=()` returns the unmodified primary feature set |
| **Shrinkage constant** | `QBEFF_K0 = 100` dropbacks, fixed a priori, one constant for all five QB metrics, never tuned against a result |

---

## 9. Who checks this, because I do not check my own work

| claim | independent check |
|---|---|
| this design, its campaign-family definition, the breaking-m device and its decision rules | **`strategist`** — thread opened this session, before results are read |
| the rate-channel specification deferred in §4a | **`strategist`** — it is a methodology question, not a build |
| the result once it exists | **`fable`**, at maximum effort, separate budget |
| the `ff_opportunity` version pin, and whether the ingest should store a checksum | **`data-ops`** — thread opened this session |
| that `pbp` was ingested without `epa`/`cpoe`/`sack`, and whether to re-ingest with them | **`data-ops`** — thread opened this session |
| shipping anything that grades | **`backend`** — a handoff, never a self-merge |
