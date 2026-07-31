# Ranking version v1 — pre-commitment

**Ranker, 2026-07-31. Written and committed BEFORE any v1 number was computed.**

This is a **pre-commitment, not a registration.** `strategist` has not registered it, the sealed
2025 holdout is not touched, and nothing here is confirmatory. It is committed in advance so that
the bar cannot be chosen after seeing the result. The confirmatory version, if v1 earns one, is
`strategist`'s to register.

**Why this exists.** Across ~90 registered factor tests, batches 1–7, **a ranking version has never
been assembled or tested.** Every arm was a single feature inside one component of an unshipped
model. `ADR-DRAFT-edge-vs-absolute-quality.md` Ruling 3.4(3) states the consequence plainly: *"the
proposition 'our model does not beat consensus' has never been tested with a model."* This pass
tests it with a model.

**Why the head-to-head loss does not pre-empt it.** `component-model-vs-incumbent-headtohead.md`
found the component models lose to the incumbent on **projection MAE** at all four positions. Per
`ADR-DRAFT-primary-evaluation-metric.md` §3(2) and Ruling 1.1(a), **raw MAE is minimised by the
conditional median and can be improved by shrinking toward the positional mean, which strictly
degrades ordering.** Projection error and ranking quality are different objects. This pass measures
the second one.

---

## 1. What v1 is

**`bottom-up-v1`.** Config blob: `experiments/bottomup/ranking_versions/v1.json`, immutable once
run, SHA-256 recorded in the results doc. No weight is hardcoded in the runner.

| Element | Choice | Why this and not something else |
|---|---|---|
| **Engine** | `experiments.bottomup.components.pos_eval.WalkForward`, `avail_arm="A"`, `calibrate_bonus=True`, unmodified | The pre-committed primary arm of `component-model-multipos-precommit.md`. Building a second model would be the over-engineering finding this project treats as a defect |
| **Output** | `proj_points` — full season points, this league's ruleset incl. stacking bonuses, via `pos_model.score_components()` | Already in the league's own units |
| **Positions** | QB, RB, WR, TE | — |
| **DEF** | **blank, with a note** | Zero coverage in `nfl.db`. No fabricated number |
| **Rookies** | **fall back to consensus and are labelled** | **Rank-space pinning** (amended below). `entry == "rookie"` rows stay at exactly their consensus positional slot; the remaining slots are filled by veterans re-ordered by `proj_points`. The model's internal rookie sub-model (draft capital) is **overridden** — draft capital is an already-eliminated edge channel |

> **Amendment, 2026-07-31, made BEFORE the first run — git history is the proof.** The rookie
> fallback was originally specified as a walk-forward curve `a + b·ln(consensus positional rank)`
> fitted on strictly prior seasons. It is replaced by **rank-space pinning**, for three reasons all
> available without seeing a result: (1) pinning *is* the stated intent — "on rookie rows v1 equals
> the crowd it is compared against" — where the curve only approximated it; (2) it deletes a fitted
> object and therefore a look-ahead surface; (3) the curve is unfittable for the first Panel M season
> (2018 has no prior FFC season), which would have forced a special case invented after seeing which
> seasons broke. Recorded rather than silently applied.
| **Cross-positional revaluation** | in the config, **not measured by this design** | The endpoint is per-position rank correlation (ADR-B forbids a cross-position aggregate). v1's positional-tilt channel is untested here and must not be claimed |

### 1.1 Table stakes — what is in, what is out, and why

Four Tier-0 table stakes are genuinely wired inside the components (`fr136-q1-bottom-up-assessment.md`
§6a.1). **v1's inclusion rule is stated as a rule, not per-feature:** *only pre-committed feature
blocks enter v1.*

| Tier 0 row | feature block | in v1? | reason |
|---|---|---|---|
| **#7 Age** | `age`, `age2` (arm A + every volume spec) | **YES** | pre-committed base |
| **#8 Prior-year target / touch share** | `tshare_w`, `cshare_w` (volume specs) | **YES** | pre-committed base; arm-independent |
| **#6 Injury designations** | `inj_missed_share_1`, `unexp_missed_share_1` (arm **B**) | **secondary arm `v1b` only** | pre-committed arm, but **measured NULL on ranking at all four positions**. Reported as a declared secondary so "adding it changed nothing" is a measurement, not an assumption |
| **#5 Depth-chart role** | `rostered_absent_share_1`, `offroster_share_1`, `depth_first_share_1` (arms **D/E**) | **NO** | arms D and E are **post-hoc** by their own source comment (`pos_features.py:37-41`) and measured NULL. Shipping a post-hoc configuration is the failure this dispatch names |

**Lagged-YPC → RB volume: EXCLUDED.** It was the one row of `factor-batch-6-results.md` with a large
`C2` movement (−0.72) and it is **post-hoc, unregistered and never run confirmatorily** (Ruling
1.2). I checked `docs/preregistration/families/*.yaml` and the whole of `docs/preregistration/`:
**no registration for it exists.** Per the dispatch it is out, and this sentence is the record of why.

---

## 2. Evaluation design

**Fixed before running. Nothing below is chosen after seeing a number.**

### 2.1 Two panels, because §6.5 as amended 2026-07-31 requires both crowds

| | **Panel M — market crowd** | **Panel E — expert crowd** |
|---|---|---|
| universe | that season's FFC half-PPR 12-team ADP board | that season's FantasyPros ECR preseason-final board |
| seasons | **2018–2024 (7)** | **2021–2024 (4)** |
| status | **primary** | required by §6.5; **pre-declared as likely non-resolving at n=4** |
| look-ahead gate | `adp_baseline.load_adp` re-asserts strictly-pre-kickoff (`:88-92`) | `is_preseason_final = 1`, `as_of_date` in late August of the target season, asserted in the runner |

Both universes are **frozen before the season** (§6.2): board membership is a pre-kickoff fact.
**Busts are retained at realised 0 points. No games-played filter. No survivor filtering.**

The ECR board is a 10-team-agnostic analyst ranking; FFC ADP is **12-team**, and the league is
**10-team**. That confound travels with every Panel M number and is not corrected.

### 2.2 The four baselines (`CLAUDE.md` §6.5 as amended)

| | baseline | construction | orientation |
|---|---|---|---|
| **B1** | **Market ADP** | `−average_pick`, FFC half-PPR 12-team | higher = better |
| **B2** | **Expert consensus** | `−` within-position rank of `rankings.adp_rank`, `source='fantasypros_ecr'`, `is_preseason_final=1` | higher = better |
| **B3** | Prior-season fantasy points, ranked | `pts_1`, missing → 0 | higher = better |
| **B4** | Simple positional-tier heuristic | tier by prior-season positional finish on `pts_1` (1–5 / 6–12 / 13–24 / 25–48 / 49+ / none), ties broken by prior-season games played. Score `−100·tier + games_1` | higher = better |
| B3w | *(informational fifth)* recency-weighted prior PPG × games share | `ppg_w · gshare_w`, the project's existing B3 | higher = better |

B3w is retained because it is the reference contrast the power check is built on (§2.5), not because
§6.5 asks for it.

### 2.3 Endpoint

**Primary: Spearman ρ(ranker score, realised season fantasy points), per position, per season, on
the panel's board-restricted universe.** Strategist's Ruling 1 item 5 makes **`C2` — the
draft-relevant universe — the FDR endpoint from batch 8**; here the entire evaluation is on the
board universe, so the endpoint *is* `C2`'s population by construction.

**Secondary, decision-relevant (§6.6):** top-k capture and mean realised points of the drafted
top-k, k = QB 10 · RB 20 · WR 30 · TE 10 (what this league starts, flex-adjusted). Descriptive only.

**Uncertainty:** season-block bootstrap on the paired per-season difference, 4,000 reps, seasons as
the independent unit, **integer seed 20260731** (never builtin `hash()`). Every figure reports a 95%
interval. A point estimate without one is not a result.

### 2.4 Multiplicity

**Primary family `F-RANKING-V1`: 8 tests** — 4 positions × 2 crowds (B1, B2), Panel M for B1 and
Panel E for B2. Benjamini–Hochberg, **q = 0.10**, applied within the family. Bootstrap two-sided
p-values from the season-block distribution.

B3, B4 and B3w contrasts are **descriptive context, not in the family** — `fr136` §1.4 already
established the component models beat them at all four positions, so they carry no decision weight
and adding them to the family would only dilute the correction.

### 2.5 The power rule — declared before running, because this is the failure mode most likely to recur

Batch 2's FDR family was underpowered and it was caught only after the fact. Pre-registering the
detection rule here.

**Minimum detectable effect (MDE)** at a position = half-width of the 95% season-block bootstrap CI
on a **baseline-vs-baseline** paired contrast — **B1 − B3w** in Panel M, **B2 − B3w** in Panel E.
This contrast contains no v1 quantity, so computing it is not peeking.

> **If MDE > 0.10 ρ at a position, that position is declared *the design cannot answer the
> question*, not *null*.**

**Why 0.10.** `fr136` §4's oracle ladder bounds the *total* room between consensus and perfect
per-game-rate knowledge at **+0.35 to +0.44 ρ**. A model capturing a quarter of that room — which
would be a very good model — moves ρ by ~0.09–0.11. A design that cannot resolve 0.10 cannot see
even an implausibly good bottom-up model, and reporting its null as evidence would be false.

`fr136` §1.4's published intervals imply QB and TE will fail this rule and RB and WR will pass.
**Stating that expectation in advance** so it reads as a prediction, not as an excuse discovered
afterwards.

### 2.6 What "competitive" means, numerically, decided now

| outcome | rule | reading |
|---|---|---|
| **EDGE** | Δρ 95% CI lower bound **> 0 against both B1 and B2** at a position | §6.5 satisfied. First real evidence an independent ranking is viable |
| **SPLIT** | clears zero against one crowd, not the other | **reported exactly as that, never the flattering half** (§6.5, founder's ruling 2026-07-31) |
| **PARITY** | CI contains 0 **and** Δρ ≥ **−0.02** against both crowds | v1 matches the crowd from scratch. **This is NOT edge and may not be reported as one.** It is evidence the approach is worth further investment, nothing more. −0.02 ≈ a quarter of the tightest expected MDE and ~5% of the oracle room |
| **LOSES** | CI upper bound < 0, **or** Δρ < −0.02 with the CI containing 0 | say so plainly |
| **CANNOT ANSWER** | MDE > 0.10 at that position (§2.5) | the design, not the model, is what failed |

**Headline rule:** the project-level verdict is taken from **RB and WR only** if QB and TE trip §2.5,
because a verdict cannot be read off positions the design cannot resolve.

### 2.7 Guardrails accounting

- **Look-ahead §6.1** — `WalkForward` raises on any feature/outcome read at or after the target
  season, per target, and the audit frame is asserted in the runner. The rookie-fallback curve is fit
  on strictly prior seasons of the same consensus source. ECR rows are asserted `is_preseason_final=1`
  with `as_of_date` before that season's Week 1 kickoff (kickoff measured, not assumed).
- **Survivorship §6.2** — universes frozen pre-season from board membership; zero-game seasons
  retained at 0 points; the count of retained zero-game player-seasons is reported.
- **Overfitting §6.3** — no v1 parameter is tuned on the evaluation seasons; arm A and the config are
  fixed before the run; BH q=0.10 on the declared family.
- **Non-stationarity §6.4** — v1 pools seasons with the components' own fixed a-priori lag weights
  (0.55/0.30/0.15), **not tuned**. Per-season ρ is reported so a regime turn is visible.
- **Baselines §6.5** — all four, both crowds.
- **Metrics §6.6** — rank correlation is the primary and it is a proxy for roster quality; top-k
  capture is reported alongside and the gap is stated.
- **Holdout** — **2025 is sealed and is not touched.** `HOLDOUT_SEASON = 2025` asserted in the runner.
  See §2.7a: it is a hard gate with a named condition, not a judgement call.

### 2.7a The holdout gate — founder's ruling, 2026-07-31, now `CLAUDE.md` §6.3

> *"We won't unlock the holdout until after fable has a chance to run."*

**Fable has never run.** Until it has, 2025 does not open — not for a decisive result, not as a
tie-breaker, not to settle whether v1 is competitive. This pre-commitment therefore adds a rule that
would otherwise be tempting to break at exactly the moment the result comes back ambiguous:

> **If v1's answer on the training seasons is ambiguous, the report says "ambiguous on the available
> evidence." It does not say "needs the holdout to settle it."** What the holdout *would* settle is
> stated; the holdout stays sealed.

The reasoning, recorded so it is applied rather than merely obeyed. Adversarial review overturned
three things today that would otherwise have been carried into a holdout test:

| overturned today | what it was |
|---|---|
| the 12-of-12-zeros framing | one algebraic identity printed twelve times |
| four arms read as consensus-suppressed improvements | `E1b`/`E2` never touched consensus, and two of the four were **degradations** |
| the oracle-ladder headline | the games-played oracle shares its zero set with the outcome |

Any of those could have justified opening 2025 a day ago. **All three were wrong by today.** The
holdout is spendable once; a day of review is cheaper than the thing it protects.

### 2.8 Independent checks — named now, per claim

| claim | who checks it |
|---|---|
| the design is sound and the bar is not self-serving | **`strategist`** — a ranker choosing the bar that scores the ranker is the failure the structure exists to prevent |
| leakage, survivorship, and whether any result is too good | **`fable`**, at maximum effort |
| anything that ships | **`backend`** — the export contract is not mine to merge |

**A result that looks too good is escalated, not celebrated.**
