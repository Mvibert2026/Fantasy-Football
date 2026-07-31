# Suggested-pick decision rule (`qg_rule`) — pre-commitment

**Written 2026-07-30 by `strategist`, before any measurement in it has been run.**
Answers `docs/founder-requests/FR-2026-07-30-recommendation-logic-is-inverted-it-prefers-the.md`.
Companion to `docs/adr-drafts/ADR-DRAFT-suggested-pick-opportunity-cost-rule.md`, which states the
rule; this file states what will be measured and what each outcome licenses.

This is the `full_design` document. A `PR-0NN` registration file referencing it, with a checked id
and a computed `content_hash`, must exist **before** any of H1–H3 executes —
`src/preregistration.require_confirmatory` will refuse otherwise, which is the point. I have no
shell and cannot compute the hash, so the registration file is deliberately not written here.

Everything below was written with **no database access**. The only data consulted are
`data/export/availability.json` (committed) and the source files cited by `file:line`.

---

## 0. The decision being pre-committed

`frontend/ui/data/recommendation.ts:64-72` orders candidates by `vbd + 8 + 18 − 25`. Availability
is not an argument to the function. The proposal is to replace the ordering with

$$\arg\max_X \; q_X \, g_X, \qquad q_X = 1 - \Pr(X \text{ survives to } t'), \qquad g_X = u_X - u_{f_X}$$

where $u_{f_X}$ is the expected best marginal value obtainable at the user's next pick $t'$ in the
branch where $X$ was not taken. Full derivation and term glossary: ADR-draft §3.

Three separable parts, registered separately so a null on one does not drag the others:

| Part | Change |
|---|---|
| **A** | Static per-position replacement level → dynamic fallback $u_{f}$ evaluated at $t'$ |
| **B** | Survival discount $q_X$ multiplying the gap (Part A alone sets $q \equiv 1$) |
| **C** | The three stopgap constants are **out of scope** — that is PR-007, thread 093, never run |

Part **C** is named only to fix the boundary: `qg_rule` is defined against `vbd_plain`, never
against `vbd_all4`. Testing a new rule on top of three unvalidated constants confounds the two.

---

## 1. Family and multiple-comparisons denominator

- **Family id:** `F-OPPORTUNITY-COST-RULE`
- **Declared m (confirmatory): 3** — H1, H2, H3 below.
- **Exploratory, never in the denominator:** D1 (the single-board pick-18 decomposition), A1 (an
  acceptance check on an approximation, not a hypothesis about rosters), the pick-flip diagnostic,
  and any per-position breakdown.
- The run log `docs/preregistration/test_run_log.jsonl` is appended for **every** run including
  nulls. A test run and not recorded shrinks every future denominator.

**Adding a fourth confirmatory test reopens the family and requires the whole §5 accounting to be
redone.** Declared here so that is a visible cost.

**Benjamini–Hochberg is not applied, and the reason is not convenience.** At n = 3–4 seasons the
exact two-sided sign test's minimum attainable p is 0.125 (n=3) / 0.0625 (n=4), and
`draft_sim.paired_season_bootstrap` deliberately returns no p-value because a 3–4-unit bootstrap's
tail is an artefact of the resampling grid rather than evidence (`draft_sim.py:436-447`). **There is
no admissible p-value at the registered resampling unit, so there is nothing for BH to correct.**
Producing one by resampling simulated drafts instead of seasons would inflate n roughly
thousandfold using a unit that is not the argument, and is refused. This is PR-007 §5's ruling,
inherited rather than re-derived.

**What replaces it, all structural and stated in advance:**

1. m fixed at 3 before any arm runs; all three reported including failures.
2. **Explicit false-ADOPT bound.** Criterion (b) requires every season positive. Under the global
   null with the season as the independent unit, P(all positive) = 0.125 at n=3 / 0.0625 at n=4 per
   comparison, so **the expected number of false ADOPTs across m=3 is ≤ 0.375 (n=3) / ≤ 0.19 (n=4),
   before the +20 materiality floor is applied at all.**
3. Conjunctive criteria (§3 (d)–(f)) can only reduce ADOPTs, never increase them, and are therefore
   outside the denominator by construction.
4. Exploratory artifacts carry no CI, no p-value, no significance flag
   (`preregistration.validate_exploratory_artifact`), and may never promote an arm.

---

## 2. Resampling unit, seeds, noise floor

- **Resampling unit: the season.** Not the simulated draft, not the pick. Seasons are the argument.
- **Common random numbers, mandatory.** Every arm within a (season, σ) cell uses the identical seed
  so `simulate_one`'s per-draft `rng.normal(0, σ, n)` board realisation is byte-identical across
  arms and the paired difference isolates the rule rather than the room. Seed formula recorded in
  the runner; **`run_draft_sim.py:68`'s `stable_offset(name)` must NOT be copied** — it gives each
  arm a different room and destroys the pairing.
- **CRN identity assertion, blocking:** record `zlib.crc32` of the first draft's `effective_rank`
  bytes per (arm, season, σ) and assert equality across all arms in the cell. **A mismatch voids the
  run**; it is not a caveat.
- **No arm may consume the RNG.** Ties break on lowest player index, deterministically.
- **Seeds never from builtin `hash()`** (guardrails §11.1). Determinism proved by running twice in
  **separate processes** and comparing byte-for-byte.
- **Noise floor before any point estimate.** Report the measured simulation SE at the chosen sims
  count (thread 111 measured ≈8.5 pts at 300 sims/cell for this simulator) alongside every margin,
  separately from the season-level bootstrap, never combined. If the seed-induced range is
  comparable to the effect claimed, the effect is reported as not measurable at that resolution.

---

## 3. H1 / H2 / H3 — the three confirmatory comparisons

**Arms.** All share one underlying value array $u$ (the same VBD board every arm uses; whichever
board PR-007's census fixes, so the two runs are comparable).

| Arm | Definition |
|---|---|
| `vbd_plain` | $\arg\max_X u_X - \text{repl}(pos_X)$ — plain VBD, no constants. The comparator. |
| `vbd_all4` | `vbd_plain` + the three shipped constants (+8 / +18 / −25). **What ships today.** |
| `vona_q1` | $\arg\max_X u_X - u_{f_X}$ with $q \equiv 1$ — Part A alone. Thread 111's formulation, re-run here on this design's fallback estimator so H2 isolates $q$ and nothing else. |
| `qg_rule` | $\arg\max_X q_X (u_X - u_{f_X})$ — Parts A **and** B. |

| id | Comparison | The question it answers |
|---|---|---|
| **H1** | `qg_rule − vbd_plain` | Does the rule build better rosters than the researched quantity? |
| **H2** | `qg_rule − vona_q1` | **Does the survival factor earn its place?** The founder's actual claim, isolated. |
| **H3** | `qg_rule − vbd_all4` | Does the rule beat what the founder is looking at today? The founder-facing headline. |

**Metric.** Paired mean roster points: season total under a weekly-optimal legal lineup scored
against **actual** historical weekly outcomes under this league's real scoring rules
(`draft_sim.weekly_optimal_points`). Season statistic is the unweighted mean of per-season margins.
**Secondary, sign-gated only:** paired change in $P(\text{user roster finishes top-4 of 10 by total
points})$ — the league's real objective under a 4-team playoff (`CLAUDE.md` §7). Rank correlation
is **not** used: two of the four arms are functions of live draft state and roster composition, so
no static ordered list exists to correlate (PR-007 §3, same reasoning, same instrument).

**Materiality floor M = +20 roster points, INHERITED VERBATIM from PR-003/PR-007, not chosen for
this test.** Re-deriving a floor is the exact move by which a bar gets quietly lowered.

**Decision rule, per comparison:**

| | Criterion | In the denominator? |
|---|---|---|
| (a) | mean margin at σ=10 **≥ +20 points** | yes |
| (b) | margin **> 0 in every** season×σ cell | yes |
| (c) | season-level bootstrap 95% CI at σ=10 **excludes 0** | yes |
| (d) | **sign agreement** on ΔP(top-4) at σ=10 | no — conjunction |
| (e) | **regime gate** — per-season margins at σ=10 not strictly decreasing across the fold set with the most recent season below +20 | no — conjunction, one-way |
| (f) | cross-process determinism **and** the CRN identity assertion both pass | no — conjunction |

**ADOPT** iff all six. **REJECT** in every other case, including every null.

**Honest note on (b) and (c):** at n = 3–4 they are near-collinear — a bootstrap CI excluding zero
essentially requires every season positive. They are **not two independent pieces of evidence** and
nobody may later count them as two. Both are listed because they fail differently under the σ sweep.

**σ sweep** is `draft_sim.SIGMA_SWEEP` verbatim, {5, 10, 20}, combined as a **conjunction, not an
average**. Absolute roster totals are never compared across σ. σ=0 runs as a deterministic
descriptive diagnostic: **if an arm's pick-flip rate is 0 at σ=0 but positive at σ=20, its entire
measured effect is an artefact of opponent noise and must be reported that way.**

**Power, stated honestly.** n = 3–4 seasons. No admissible p-value exists (§1). This design is
**powered to reject and underpowered to adopt**, deliberately — that is what "every added parameter
must earn its place" means when the burden of proof is on the parameter (`CLAUDE.md` §6.3). **Any
ADOPT is PROVISIONAL** and licenses "not rejected this pass," never "validated."

**Registered expectation, so the run can contradict me.** Applying my standing calibration prior to
my own reasoning: "opportunity cost is obviously the right frame" is a *story*, and it goes in at
half weight. **I predict H1 and H3 land positive but under the +20 floor, and REJECT; H2 positive
and the largest of the three, because it is the only one isolating a term the prior arm had
hardcoded, and still likely under the floor.** If all three ADOPT on 3–4 seasons, read
`guardrails` §8 item 7 first: an unusually strong result is evidence of a bug — most likely broken
CRN pairing or a fallback estimator that peeked at the realised draft — more often than evidence of
a good model.

---

## 4. D1 — the pick-18 decomposition. **Exploratory. Never in any denominator.**

Reproduce the founder's observed board state (pick 18, `USER_SLOT` per his live config, the players
he had rostered). Report, for Allen, McBride and the next four candidates by each rule:

$u_X$, $p_X$ at $t'=23$ (σ=5/10/20), $q_X$, $u_{f_X}$, $g_X$, $q_X g_X$ — and three orderings:

| Ordering | Setting |
|---|---|
| shipped | `vbd_all4` |
| Part A only | dynamic $u_f$, $q$ forced to 1 |
| Part A + B | `qg_rule` |

**Registered directional prediction, before the run:** *the Part-A-only ordering already reverses
Allen/McBride, and a $q$-only variant (static $u_f$, real $q$) does not.* i.e. the dominant error at
pick 18 is the static replacement level, not the missing survival term. Basis, arithmetic not
narrative: VBD prices Allen against QB10 in a 1-QB league (ADR-029 levels; ADR-016 QB1 slot value
114.1), and QB10 is not the QB available at pick 23.

**This is one board state with no resampling unit. It can never be reported as an edge, and it
cannot promote or demote any arm.** Its only job is to tell the founder *which* term was missing,
in his own screenshot, in a form he can check.

---

## 4b. D2 — does `qg_rule` make the `−25` QB constant redundant? **Exploratory.**

The ADR draft §3.4b argues that a correct opportunity-cost rule should discover early-QB cost
endogenously — $g_{\text{QB}}$ is small whenever QB is deep — and therefore that a hand-picked QB
penalty is a patch for a missing term, not a finding being encoded.

That is checkable. **Report, descriptively, no CI, outside every denominator:**

| Quantity | Read as |
|---|---|
| QB selection rate in rounds 1–3, `qg_rule` vs `vbd_plain` vs `vbd_all4` | Does `qg_rule` alone already under-select early QBs relative to plain VBD? |
| Paired margin `qg_rule` vs `qg_rule + (−25 QB, round < 6)` | If near zero, the constant is redundant **given** the rule — the ADR's claim. If materially positive, the rule does *not* subsume it and the ADR §3.4b argument is wrong. |
| Mean $g_{\text{QB1}}$ at each user pick in rounds 1–3, against mean $g$ for the best RB/WR available | The mechanism, if there is one |

**Registered prediction:** `qg_rule` under-selects early QBs relative to `vbd_plain` **without** any
QB term, and adding the −25 on top moves the margin by less than the +20 floor. **If instead the
−25 still helps materially on top of `qg_rule`, ADR §3.4b is wrong and must be corrected in place,
not quietly dropped.**

This is descriptive on one instrument at n = 3–4 seasons and can never promote or demote an arm. It
does not adjudicate the −25; **PR-007 does that**, and this is not a substitute for running it.

## 5. A1 — acceptance check on the fallback estimator. **Not a hypothesis.**

$u_{f_X} = \mathbb{E}[\max_{Y \in \mathcal{A}_{t'}, Y\neq X} u(Y)]$ is an expectation of a maximum
over a **joint** survival distribution. `availability.json` ships per-player marginals (`by_player`)
and P(≥1 of a tier survives) (`by_tier`, `docs/data-contract.md:153`). Neither is the required
statistic.

| Estimator | Method |
|---|---|
| **(ii) independent marginals** | over the position's board order, $\sum_j u_{(j)}\, p_{(j)} \prod_{i<j}(1-p_{(i)})$ from `by_player[·][t']`. Closed form, browser-side, shipped fields only. |
| **(iii) simulator-exact** | `simulate_availability` conditioned on live draft state; empirical mean of $\max_Y u(Y)$ over simulated continuations. |

**(iii) is used for every arm in §3.** (ii) is a *shipping* question only.

**A1 pass criterion, pre-committed and blocking on (ii) shipping:** report mean and max
$|u_f^{(ii)} - u_f^{(iii)}|$ in VBD points, broken out by position and by intervening-pick gap (this
league alternates 14 and 4 — `USER_SLOT=3`, `N_TEAMS=10`). **Pass iff mean ≤ 5 and max ≤ 20**
(the 20 is M, inherited). Fail ⇒ (ii) does not ship, and the client reads (iii)'s exported values.

**Report the sign of the bias, not just its size.** Within-position survivals are positively
correlated through a positional run and negatively correlated through fixed pick supply; the net
sign is not knowable a priori and I am explicitly declining to predict it. Measuring it is the
point of this check.

**Jensen guard, pre-committed.** $\mathbb{E}[\max] \neq \max \mathbb{E}$. Any implementation that
computes the fallback as "the value of the player most likely to be there" rather than the
expectation of the maximum is **wrong and must be rejected in review, not caveated in the report.**
`findLikelyThereCandidate` (`DraftRoom.tsx:134-153`) is exactly that wrong form and is display-only
today; it must not become the estimator.

---

## 6. Look-ahead, survivorship, universe — the standing guards

- **Look-ahead (guardrails §1).** No outcome data may enter any board or any $p$. Outcomes enter
  **only** through `weekly_optimal_points`. Backend asserts programmatically and prints
  `max(training_seasons) < N` for every fitted rank curve, per season, per arm. Every season read
  routes through `holdout.load_season_registered`.
  **The specific new leak this design creates and must be checked for:** $u_f$ is an expectation
  over *who will still be available*. An implementation that computes it from the realised draft
  order of the historical season, rather than from the opponent model, leaks the answer into the
  decision. **Required assertion: the fallback estimator's inputs are the board and the opponent
  model only, never `data.pts` and never the realised pick sequence.** State it as an executed
  assertion, not a claim.
- **Survivorship (guardrails §2).** Universe is the entire pre-season consensus list; players who
  never scored get 0 and are retained by construction. Assert the zeros are present.
- **Holdout.** **2025 stays sealed. This registration does not authorise an unseal and no agent may
  perform one under it.** n=1 cannot resolve a +20 margin, an unseal is irreversible, and the
  expected outcome here (reject) needs no holdout because nothing is fitted to these seasons.
- **Fold set** is inherited from PR-007 §6's formula, not re-chosen: seasons with a usable
  pre-draft board and a fittable rank curve, excluding 2025. Expected {2022, 2023, 2024}. If the
  census yields fewer than 3, **STOP and reply — do not run.**

---

## 7. STOP conditions — do not run, reply on the thread

1. Fold set < 3 seasons.
2. The CRN identity assertion fails in any cell.
3. The look-ahead assertion in §6 fails, or the fallback estimator's input set cannot be shown to
   exclude realised outcomes.
4. `qg_rule`'s pick-flip rate versus `vbd_plain` is **< 1% of user picks** at σ=0 → report
   **UNEXERCISED** rather than as evidence of harmlessness, and stop. A rule that never changes a
   pick cannot be evaluated on roster points.
5. `qg_rule` and `vona_q1` choose an identical roster in ≥ 99% of paired drafts → H2 has no signal
   to measure at this sample; report that, do not report a margin.

---

## 8. Pre-mortem (guardrails §8), answered before the run

1. **Look-ahead?** The live risk is §6's fallback-estimator leak. Named, with a required executed
   assertion.
2. **Universe defined before outcomes?** Yes — pre-season consensus list, zeros retained.
3. **Holdout untouched?** Yes. 2025 sealed, explicitly not unsealed by this registration.
4. **Multiple comparisons?** m = 3 fixed before the run; BH inapplicable and the structural
   replacement stated (§1).
5. **Confidence intervals?** Season-level bootstrap 95% CI required on every margin, reported
   separately from the simulation SE, never combined.
6. **All three baselines?** `vbd_plain` is guardrails §5 baseline 1 (BPA by our VBD/replacement
   levels); `bpa_consensus` carries baseline 3 (expert consensus) as a descriptive arm. **Baseline
   2 (consensus market ADP) is structurally unavailable for 2022–2024** — no historical ADP for
   those seasons exists in this repo at a pre-draft date usable for the simulator's board (ADR-018;
   thread 055's FFC backfill is a *season-level* ADP source, and whether it can serve as a
   simulator board for those seasons is an open question, not an assumption). Stated as a
   limitation, not omitted.
7. **If the result looks unusually good, what is the leakage explanation?** Two, ranked: (1) the
   fallback estimator seeing realised outcomes (§6); (2) broken CRN pairing making the comparison
   between different rooms rather than different rules. Both have executed assertions attached.

---

## 9. Refusals, in writing

1. **Shipping `qg_rule` before H1–H3 report.** Thread 111 measured its nearest relative at −106
   [−182,−54] / −126 [−215,−69] points against plain BPA. The derivation in the ADR draft explains
   *why* that arm was mis-specified ($q \equiv 1$); it is not evidence that the corrected version
   wins.
2. **A grid search over the rule's shape** — a $q$ exponent, a blend weight against VBD, a
   truncation horizon. At n = 3–4 seasons a search returns a fitted object with no out-of-sample
   support that then carries false authority: strictly worse than the status quo. Same refusal as
   PR-007 §13.1.
3. **Amending PR-007 to add these arms.** An amendment after seeing data irreversibly demotes a
   registration to exploratory. Separate family, separate registration, same batch, same CRN seeds.
4. **Reporting D1 as evidence about the rule.** One board state, exploratory forever.
5. **Manufacturing a p-value** by moving the resampling unit to the simulated draft.
6. **Reading a null on H1/H3 as licence to keep the three constants.** That is PR-007's question.
   If everything here is null, the recommender falls back to plain VBD and says so.
