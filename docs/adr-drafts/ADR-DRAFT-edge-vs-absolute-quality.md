# ADR-DRAFT — Separating edge over consensus from absolute ranking quality

**Status:** Proposed (rulings issued; number to be allocated by `tools/handoffs.py adr next` at landing)
**Date:** 2026-07-31
**Owner:** Strategist (ruling) / Ranker + Backend (execution)
**Answers:** `docs/founder-requests/FR-2026-07-31-separate-edge-over-consensus-from-absolute-ranki.md`
**Amends:** the factor campaign's endpoint vocabulary (batches 1–7 legends; every future pre-commit)
**Amends `CLAUDE.md`:** **NO.** §6.5 stands unamended — see Ruling 2. One contradiction between
`CLAUDE.md` §6.5 and `docs/statistical-guardrails.md` §5 is **escalated to the founder**, not resolved here.
**Companion:** `docs/preregistration/PR-DRAFT-consensus-quality-by-season.md` (Ruling 4)

---

## 0. The four rulings in one table

| # | Question | Ruling | Founder decision needed? |
|---|---|---|---|
| 1 | Are edge and absolute quality adequately separated in the current grading? | **No — only apparently, and the mislabelling runs the opposite way from the FR's diagnosis.** `E1a` is not absolute ranking quality; `E1b`/`E2` are not edge over consensus. Rename, and require a derivation | No — mine |
| 2 | Should `CLAUDE.md` §6.5 be amended? | **No. Declined.** §6.5 governs *ranking versions*; it was never binding on component arms. The defect is misapplication, not the rule | **One escalation** — §6.5 vs guardrails §5 disagree on the baseline list |
| 3 | Is "no edge over consensus" the expected outcome? | **Yes in the weak form, and the campaign has misreported it. No in the strong form** — "consensus is unbeatable" is unsupported here and is refused | No — mine |
| 4 | How good is consensus year by year? | Specified in full, pre-registered, with a null model. See the companion PR | No — mine, pending the Ruling 2 escalation, which changes which crowd is measured |

---

## Ruling 1 — The separation is apparent, not real, and it is mislabelled in the opposite direction

### 1.1 The FR's premise is wrong on both halves, and this is checkable

The FR states: *absolute quality is measured by `E1a`; edge over consensus by `E1b` and `E2`.*
Against the pre-commits and results docs, neither half holds.

**(a) `E1a` is not "absolute ranking quality."** Every pre-commit defines it identically
(`factor-batch-{2,3,5,6,7}-precommit.md` §3/§5): *"out-of-sample MAE of the **one declared
component**, full universe."* A component is `carries`, `targets`, `rec_yards`, `pass_attempts`,
`rush_tds` — not points, not a rank. Three gaps sit between it and "the ranking is better":

1. **It is one channel of about seven.** A ranking falls out of composing every component through
   the scoring engine and a per-game distribution. No batch has ever derived a rank change from a
   component-MAE change, in either direction.
2. **It is measured on an unshipped model.** The live board's only player-level input is consensus
   positional rank (`fr136-q1-bottom-up-assessment.md` §1.1; `factor-ledger.md`'s standing
   shipped-vs-experimental note). Nothing in batches 1–7 has been measured on the object the founder
   looks at.
3. **MAE has a known ordering pathology, already ruled on in this project and never applied here.**
   `ADR-DRAFT-primary-evaluation-metric.md` §3(2): MAE is minimised by the conditional median, so it
   **can be improved by shrinking toward the positional mean, which strictly degrades ordering.**
   That ruling was issued for the projection metric. `E1a` — the campaign's FDR endpoint through
   seven batches — is raw MAE and inherits the pathology untouched.

An `E1a` improvement is therefore not "an improvement that might not aggregate." It is a movement in
a quantity whose optimum is reachable by destroying the thing the product sells.

**(b) `E1b` and `E2` are not edge-over-consensus metrics.** The pre-commits are explicit:

| endpoint | pre-commit text | what it actually compares |
|---|---|---|
| `E1b` | *"the same MAE **restricted to players on the consensus ADP board**"* | arm vs **primary model**, on a restricted universe. A population filter, not a comparator |
| `E2` | *"ADP-board Spearman, **arm − primary**"* | arm vs **primary model**. "ADP" names the population, not the benchmark |
| `E4` | *"mean of `adpsub_rho_model − adpsub_rho_b1_adp`"* | **model vs market.** The only §6.5-shaped number in the campaign — and it appears in **one batch of seven** |

`E2` is labelled in five consecutive pre-commits as *"the bar that matters ... `CLAUDE.md` §6.5."*
**That label is attached to the wrong object.** §6.5's bar is the comparison against consensus ADP.
`E2` does not contain consensus ADP.

### 1.2 The correction inverts three of the FR's own four rows

The FR reads its table as *"real improvements to the rankings, graded as failures by the consensus
bar."* Checked against `factor-batch-6-results.md` §3:

| arm | `E2` (arm − **primary model**) | what actually happened |
|---|---|---|
| ANY/A at QB | **−0.0118** | the arm's ranking is **worse than the incumbent model's own ranking** |
| Passer rating at QB | **−0.0180 [−0.0350, −0.0005]** | worse, **interval excludes zero on the harmful side** |
| Explosive rush rate | ≈ 0 (`E1b` −0.03, also better) | component error fell on both universes, ordering unchanged |
| Lagged YPC → RB volume | `E1b` −0.72 | post-hoc, unregistered, unrun confirmatorily |

**Consensus never entered any of these grades.** ANY/A and passer rating are not suppressed wins —
they are **measured ranking degradations**, recorded correctly. The FR has re-read them as wins the
consensus bar denied. That sentence must not be allowed to stand; it is the exact shape of the error
this ruling exists to stop.

Explosive rush rate is the one row where the FR's *shape* is right, and what it describes is already
what `PROJECTION-ONLY` means.

### 1.3 The founder's question, answered directly

> *If a factor improves component MAE and does nothing to the board, has the ranking improved in any
> sense the founder would recognise?*

**No.** He looks at an ordered list of players. If the order does not change, nothing he can see
improved. If the order changes and rank correlation does not improve, the list is not better.

The honest content of `PROJECTION-ONLY` is: *"the number printed beside a player's name is closer to
what he scored; the order of the names is unchanged."* That is worth something — it is display
honesty and it has its own product surface (`ADR-DRAFT-component-projection-display.md`) — but it is
**not a ranking improvement** and may not be renarrated as one.

### 1.4 Failure mode: **metric laundering**

Take an endpoint that measures A (one component's error, unshipped model, metric with a known
ordering pathology), attach a label meaning B ("absolute ranking quality"), and recover the wins the
edge bar denied. The FR is a sincere early instance. The fix is renaming plus a derivation
requirement — **not** re-grading anything.

### 1.5 What is ordered

1. **Rename, campaign-wide.** In every future pre-commit, and as a one-line legend correction in the
   batch 1–7 *results* headers (**no grade changes, no number changes**):

   | old | new | meaning |
   |---|---|---|
   | `E1a` | **`C1`** | component error, full universe |
   | `E1b` | **`C2`** | component error, draft-relevant universe |
   | `E2` | **`R1`** | within-model ordering delta (arm − primary) |
   | `E4` | **`M1`** | **margin over market** (model − consensus ADP), a level, not a delta |

   Delete the phrase *"the bar that matters, `CLAUDE.md` §6.5"* from `E2`/`R1`'s description entirely.

2. **`M1` becomes mandatory in every batch**, for every arm, at every position with market coverage,
   reported as a **level with a season-level bootstrap CI**. It is the only §6.5-compliant figure the
   campaign produces and it currently exists in one batch.

3. **`PROJECTION-ONLY` gets the definition it lacks**, written verbatim into the next pre-commit:
   > *"Component error fell on both universes and the ordering did not change beyond noise. This is a
   > display claim, not a ranking claim, and it may not be reported as an improvement to the rankings."*

4. **A `PROJECTION-ONLY` arm may not be shipped to the board.** It may ship to the projection display
   only, and only after clearing `ADR-DRAFT-primary-evaluation-metric.md` §3's skill score `SS`
   against the frozen constant-predictor floor — **which no batch has computed for any arm.** Until
   that is computed, `PROJECTION-ONLY` is an unshipped intermediate, not a deliverable.

5. **Batch 7's own question is answered in the affirmative.** Its §1(3) asks whether `E1a` should
   remain the FDR endpoint, having found across three batches, three positions and four sources that
   *every arm improving the full universe degraded the draft board*. It should not remain the sole
   endpoint. **`C2` (draft-relevant universe) becomes the FDR endpoint from batch 8**, with `C1`
   retained and reported. The population a ten-team draft actually chooses between is the population
   the correction should protect.

---

## Ruling 2 — `CLAUDE.md` §6.5 stands unamended. Declined.

### 2.1 The rule is correct and was never binding on what was graded

§6.5 opens: *"Any **ranking version** must be measured against baselines."* A ranking version is a
complete candidate ordering. **A component-projection arm is not a ranking version.** Batches 1–7
tested single features inside one component of an unshipped model. §6.5 never governed them. `E2`'s
pre-commit text asserted that it did, and **that assertion is the defect** — not the rule.

The second sentence — *"if a version does not beat consensus ADP on a holdout season, it has no
edge"* — says *no edge*. It does not say no value, does not say do not build, does not say do not
ship. Everything the founder is worried about is already outside what §6.5 claims.

### 2.2 Why amending it would be the wrong move specifically now

§6.5 is the project's only structural defence against a favourable number buying an exception. It has
already caught two live instances: the yardage-bonus variance claim (retired in `CLAUDE.md` §7 after
four independent nulls) and the calibration prior's four-of-five misses. **Loosening it in response to
one day of nulls is bar-moving under null pressure**, and the correct response to nulls is a better
instrument or a better factor, never a softer rule. Recording that I felt the pull and refused it.

### 2.3 What is added instead — in the campaign's documents, not in `CLAUDE.md`

> §6.5 governs ranking versions. It does not govern component-projection arms. An arm that improves a
> component's error is graded on the projection metric (`ADR-DRAFT-primary-evaluation-metric.md` §3,
> skill score against a frozen constant floor), reports `M1` for information, and is never described
> as beating or failing to beat consensus.

### 2.4 ESCALATION — a contradiction between two documents, which I do not resolve

`CLAUDE.md` §6.5 and `docs/statistical-guardrails.md` §5 state **different required baseline sets**:

| | `CLAUDE.md` §6.5 | `statistical-guardrails.md` §5 |
|---|---|---|
| 1 | Consensus **market** ADP | Best Player Available (VBD) |
| 2 | Prior-season fantasy points, ranked | Consensus **market** ADP |
| 3 | Simple positional-tier heuristic | **FantasyPros / expert consensus** preseason ranking |

Per my operating rules a contradiction between two documents is escalated, never resolved by whichever
session next needs it. **It is load-bearing here, not cosmetic:**

- The founder's sentence is about **analysts** — expert consensus, which is what `fantasypros_ecr`
  is, and what the **shipped board** runs off (`draft_sim.py:120`).
- Every measured "consensus" figure in the entire factor campaign is **market** ADP — FFC half-PPR
  12-team mock-draft ADP (`experiments/bottomup/components/adp_baseline.py:1-14`).

**Those are different crowds** (a crowd of drafters vs a crowd of analysts), and which one is "the
bar" is a founder call. It changes Ruling 4's design directly. **Founder decision required.**

### 2.5 Failure mode: **bar-moving under null pressure**

A day of nulls creates the strongest possible incentive to discover the bar was unfair. Named here so
that if §6.5 is ever amended, the amendment has to explain why it is not this.

---

## Ruling 3 — Expected in the weak form; refused in the strong form

### 3.1 The FR's supporting evidence does not support its claim

The FR cites batch 5's **ρ = +0.668** as showing consensus is the ceiling. It does not. That figure is
**prior points per game** — §6.5 baseline **#2** — inside a descriptive family (F3) comparing ten
*rate statistics* on survivor-filtered WR pairs. **Consensus ADP is not in that table at all.**

"Prior FPG is the ceiling among pass-catcher rate stats" and "consensus is the ceiling" are different
claims with different evidence, and the second does not follow from the first.

### 3.2 The evidence that does bear on it is better — and partly cuts the other way

`component-model-rb-qb-te-pass-1.md` §1's power-check column is the most informative number in the
repo on this question. Market ADP minus a three-line heuristic (`weighted prior PPG × games share`),
seven seasons:

| position | ADP − heuristic | reading |
|---|---|---|
| **RB** | **+0.134 [+0.043, +0.223]** | consensus is measurably better than a trivial baseline |
| TE | +0.058 [−0.055, +0.224] | cannot distinguish |
| WR | +0.043 [−0.032, +0.126] | cannot distinguish |
| QB | +0.038 [−0.039, +0.137] | cannot distinguish |

At **three of four positions, seven seasons cannot show market ADP beating a three-line heuristic.**
That is not "consensus is a formidable, well-calibrated aggregate."

It carries a consequence the FR misses: at WR/QB/TE, **"we did not beat consensus" and "we did not
beat a three-line heuristic" are the same statement.** Framing the nulls as failure against a
formidable crowd flatters both sides. The honest framing: at three positions the experiment resolves
nothing; at the fourth — RB, where it does resolve — we are behind by **−0.052**, and sixteen
registered arms moved it by **±0.005**.

### 3.3 The weak form — adopted, and the campaign has been misreporting it

An individual predictor drawn from the pool that forms a consensus should not be expected to beat the
consensus, because the consensus is a variance-reduced average of that pool. Batches 5, 6 and 7 tested
published metrics from eleven analytics shops — **drawn from exactly that pool.** Expecting each to
beat the aggregate of all of them is expecting each analyst to beat their own average. It should not
have surprised anyone, and reporting each null as a failure did misrepresent what was learned. **The
founder is right about this and the reporting changes.**

### 3.4 The strong form — refused. Three reasons.

*"Consensus is unbeatable, therefore no edge exists, therefore the nulls are the final answer."*

1. **Wisdom of crowds requires independence, and fantasy ADP has almost none.** The mechanism that
   makes an average beat its members is *uncorrelated* individual error. FFC ADP comes from mock
   drafters reading the same shops; FantasyPros ECR is a literal average of those shops. The sweep's
   own effective-independence estimate across 11 shops is **~6** (`factor-ledger.md` §5 header). A
   crowd with correlated errors averages away little and **retains its shared biases in full.** That
   is the textbook failure condition of the result, and it is present here by construction.
2. **The crowd's errors are known to be structured, and one is already measured.** The 2026-07-30
   ADP-vs-production analysis found early-round RB underperforming same-round peers at every other
   position by roughly **3×** (−54.1 VBD vs −15.9 to −18.9, rounds 1–3, train seasons), surviving an
   era split. A perfectly wise crowd does not have a systematic, directional, era-robust error.
3. **We have never tested a ranking version.** Every arm in batches 1–7 was a single feature inside
   one component of an unshipped model; the shipped board has **one** player-level input. The
   proposition "our model does not beat consensus" **has never been tested with a model.** Concluding
   market efficiency from seven batches of component ablations is concluding a race is unwinnable from
   the warm-up.

### 3.5 Failure mode: **the efficient-market lullaby**

"Nobody beats the market" is unfalsifiable in the direction that ends the project, requires no further
work, exonerates every null, and is — on the evidence currently held — **indistinguishable from "we
have not built a model yet."** Adopting it would let a day of component ablations retire the product's
core premise. The distinguishing test is Ruling 4.

---

## 4. What would falsify these rulings

- **Falsifies Ruling 1:** someone derives, on real data, that a `C1` improvement of the observed size
  (0.1–2% of component error) produces a measurable rank-correlation improvement on the shipped board.
  Then component MAE *is* a ranking metric and the rename is cosmetic. Nobody has attempted this
  derivation; it is item 2 of the companion handoff.
- **Falsifies Ruling 2:** the founder rules that the product's goal is absolute projection quality and
  edge over consensus is secondary. That is his call to make, and it would make §6.5's headline rule
  wrong for this product — a `CLAUDE.md` change, which would then go through him, not around him.
- **Falsifies Ruling 3's refusal:** Ruling 4 returns outcome (i) — consensus quality stable across
  seasons and materially above the heuristic at all four positions — **and** a real ranking version,
  once built, fails against it at n ≥ 6 seasons. Both, not either.

---

## 5. Guardrails accounting

Look-ahead §6.1: nothing here reads data; the companion PR's predictor is gated strictly pre-kickoff
by `adp_baseline.py:88-92` and re-asserted rather than trusted. Survivorship §6.2: busts retained at
realised 0 points, no games filter. Multiple comparisons §6.3: Ruling 1 item 5 moves the FDR endpoint
but **does not change `M_campaign = 80`**; no grade in batches 1–7 is altered by anything in this
document. Non-stationarity §6.4: Ruling 4 is a direct test of whether the *baseline itself* is
non-stationary, which the campaign has assumed away. Baselines §6.5: unamended, and its scope stated.
Metrics §6.6: Ruling 1 item 5 moves the endpoint toward the decision-relevant population. Uncertainty
§7: season-level bootstrap required on `M1` and on every figure in the companion PR. Reproducibility
§11: integer seeds recorded, never builtin `hash()`.
