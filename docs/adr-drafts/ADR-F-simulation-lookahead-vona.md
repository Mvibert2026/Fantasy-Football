# ADR-F — Simulation-based lookahead (VONA) for the recommendation

**Path:** `docs/adr/ADR-F-simulation-lookahead-vona.md`
**Status:** Proposed — draft for `backend` feasibility and latency review
**Date:** 2026-07-27
**Owner:** Strategist (spec) / Backend (feasibility + execution)
**Thread:** 045. Consumer: thread 044 (roster-aware recommendation).
**Depends on:** `src/draft_sim.py`, `src/live_availability.py` (ADR-045), ADR-C (pre-registration), ADR-A (the "do not fit an unidentifiable magnitude" precedent)

---

## Context

Today the recommendation answers *"who has the most value over replacement right now."* The founder
asked it to answer *"which pick leaves me with the better roster two picks from now."* That is VONA,
and P3-1's schema prerequisite (`rankings.spread_sd` / `rank_best` / `rank_worst` per source per
`as_of_date`) is already satisfied. Only the algorithm is missing.

The machinery is also largely present. `draft_sim.py` runs full 10-team, 16-round snake drafts with an
opponent model (consensus ECR + Gaussian rank noise `sigma`, drawn once per draft, plus an additive
positional-need penalty), scores rosters with the real scoring engine, and already carries
season-level paired bootstrap and an exact sign test with `min_achievable_p` printed. `live_availability.py`
supplies the per-pick hazard model with `lambda = 0.352` (measured, clustered SE 0.070, n=160 picks /
10 clusters, one draft) and `delta = 0.10` (unvalidated prior).

At the founder's slot (`USER_SLOT = 3`) the pick gaps alternate **15 and 5**. A 15-pick gap is exactly
the regime where lookahead could matter and exactly the regime where opponent-model error accumulates.
Both things are true at once, which is why this ADR is mostly about deciding *whether* the answer is
usable, not about computing it.

---

## Decision

### 1. The decision object, defined before anything is computed

At the user's pick, with board state `S` and candidate set `C`:

```
V(c) = E[ starter-lineup value of the roster at end of draft
          | take c now, then follow continuation policy pi at every later own pick,
            opponents drawn from opponent model M(lambda, sigma, delta) ]
```

Three components of that definition are choices, and each is a claim the output inherits.

**1.1 The continuation policy `pi` is declared and fixed.** `pi` = the current shipping recommender
(`strategy_balanced`: need-weighted VBD). Lookahead compares candidates *under a fixed downstream
policy*; it does not recurse. Recursive lookahead ("and at the next pick I would also look ahead")
multiplies cost by the branching factor for a second-order effect and makes the result impossible to
explain in a card. **Consequence the output must disclose:** every VONA number is conditional on "and
then you draft need-weighted best value at every remaining pick." A user who intends to do something
else is being shown the wrong comparison, and the card says so.

**1.2 Roster value is defined only at end of draft.** Valuing a partial roster requires a terminal
value function for unfilled slots, and that function is an unconstrained judgement call that would
dominate the answer while being invisible in it. Simulating to completion under `pi` avoids inventing
one. Cost is addressed in §5.

**1.3 The candidate set `C` is the top 8 by current need-weighted VBD**, plus any player the user has
explicitly pinned. Fixed before the pick, logged. §5's degraded ladder can shrink it, and shrinking it
changes what the answer means (§5.3).

### 2. Horizon — three different claims, three different costs

| Horizon | The claim it supports | Marginal cost | Assumption load |
|---|---|---|---|
| **H1 — to next own pick** | "which candidate leaves the better *pair* of picks" | Cheapest: simulate the intervening 15 (or 5) opponent picks only | Lowest. Needs the opponent model over one gap. Availability error over 15 picks is the only compounding term. |
| **H2 — to next two own picks** | "…better trio" | ~2× H1 | Moderate. Two gaps of opponent behaviour, plus one more application of `pi`. |
| **H3 — end of draft** | "which candidate leaves the better *roster*" | Full 160-pick sim per candidate per replicate | Highest. Opponent-model error and `pi` error compound over 16 rounds; roster value at the end is also where `draft_sim`'s known biases bite hardest (§7). |

**Decision:** the **confirmatory metric is H3**, because roster value is only well-defined there
(§1.2). **H1 is computed and reported as a separate, cheap diagnostic** — "candidate c survives to your
next pick in N% of simulations" — because it is directly interpretable, is the quantity users actually
reason about, and does not depend on `pi` at all. H2 is not built; it has H3's assumption load without
H3's clean definition.

These are not interchangeable and must not be reported under one label. H1 is a statement about
*availability*; H3 is a statement about *roster value*. Collapsing them into "the simulation says" is
the reporting failure this ADR exists to prevent.

### 3. Simulation count, and what the interval around it does and does not mean

**3.1 Paired estimation with common random numbers.** For candidates `c1, c2`, estimate

```
Delta(c1, c2) = V(c1) - V(c2)
```

as a **paired** difference: replicate `i` uses the *same* seed, therefore the same board-noise
realisation `effective_rank`, for both branches. `draft_sim.simulate_one` already draws one board
realisation per draft and the strategy functions consume no RNG, so CRN is available essentially for
free — but it must be made explicit (seed per replicate index, not one sequential generator shared
across arms) so that a future refactor cannot silently break the pairing.

CRN is not a performance trick here. It is the statistical substance of §6: it is what makes the shared
opponent-model error cancel in the difference.

**3.2 Fixed N, not sequential stopping.** Pre-committed: `N` is **fixed per pick**, calibrated offline
from a pilot variance estimate so that the Monte Carlo standard error on the paired difference meets a
declared tolerance:

```
SE_MC(Delta) = sd(Delta_i) / sqrt(N)        target: SE_MC <= 0.5 projected starter points
```

Backend measures `sd(Delta_i)` in a pilot (§9, item 2) and `N` follows from it; it is not guessed here.

Sequential "run until the interval excludes zero" is **rejected**. Optional stopping on a significance
criterion inflates the error rate, and the inflation is worst exactly when the true difference is near
zero — which is the case this whole ADR is trying to detect. Sequential batching survives only inside
the degraded ladder (§5.2), and when it fires the card must not report a percentage as if it were exact.

**3.3 The distinction that must never be blurred.** Two independent uncertainties:

| | What it measures | Behaviour as N grows | Reported as |
|---|---|---|---|
| **Monte Carlo error** | How precisely we have estimated **our own model's** expectation | Shrinks as `1/sqrt(N)` | `SE_MC`, and the ordering-hold percentage's binomial SE |
| **Model error** | Whether our opponent model resembles the real draft room | **Does not shrink at all.** N=10,000 is exactly as wrong as N=100. | The `(lambda, sigma, delta)` sweep range in §4 — the only honest error bar available |

A tight interval around our model's answer is not a tight interval around the truth. Reporting the
first alone is the false-precision failure mode named in thread 045, and it is prohibited: **any
artifact quoting `SE_MC` must quote the sweep range in the same view.** The sweep is not an appendix;
it is the uncertainty statement.

### 4. Sensitivity sweep — and why sweeping `lambda` alone would be the least informative choice available

Thread 045 asks for a `lambda` sweep. Taken literally that would be a reassuring and misleading
exercise, and the reason is worth stating plainly:

**`lambda` is the best-characterised of the three opponent-model parameters.** It has a point estimate
and a clustered SE from a real draft. `sigma` — described in `draft_sim.py`'s own assumption 1 as
"THE DOMINANT ASSUMPTION AND IS NOT CALIBRATED" — has no estimate at all; its default 10.0 is a guess.
`delta = 0.10` is an unvalidated prior with a standing rule (ADR-045 / D-004) to zero it if it fails
validation. Sweeping only the parameter we measured, and holding fixed the two we did not, would
produce a stability result that is an artifact of what we chose to vary.

**The sweep grid, fixed in advance:**

| Parameter | Values | Basis |
|---|---|---|
| `lambda` | 0.212, 0.282, **0.352**, 0.422, 0.492 | point estimate ± 1 and ± 2 clustered SE (0.070) |
| `sigma` | 5.0, **10.0**, 20.0 | `draft_sim.SIGMA_SWEEP`, already the project's declared uncalibrated range |
| `delta` | **0.10**, 0.0 | the prior and its pre-committed fallback |

30 cells. Central cell in bold. CRN across cells (same replicate seeds everywhere) so cell-to-cell
differences are parameter effects, not sampling noise. Additionally run `lambda = 0` and `lambda = 0.5`
as boundary probes — reported, not counted in the adopt/shelve arithmetic.

**Stability statistics, declared before running:**

1. **Top-1 agreement rate** — fraction of sweep cells whose `argmax_c V(c)` equals the central cell's.
2. **Top-1 vs top-2 sign stability** — fraction of cells where `sign(Delta(c_1, c_2))` matches the
   central cell's. This is the decision-relevant one; a flip between ranks 4 and 5 changes nothing.
3. **Smallest perturbation that flips top-1**, reported in units of `lambda`-SE and in `sigma` units.
4. All three computed **per draft state**, then summarised across the registered state set (§8.1).

**If the ordering flips inside `lambda`'s own measured uncertainty, that is the finding.** It would mean
the lookahead is not decision-relevant at current parameter knowledge — reported as a result, in those
words, not as a disappointing run to be re-tuned. §8.3 pre-commits the consequence so the conclusion
cannot be renegotiated after seeing it.

### 5. Cost, latency, and the degraded ladder

**5.1 Budget.** The recommendation must refresh within **2.0 s p95** on the founder's machine, measured
end-to-end from "opponent's pick entered" to "card updated." The pick clock is longer than that, but
the binding constraint is not the clock — it is that a user reading a card will not wait, and a stale
card during a live draft is worse than a simpler one. Per-simulation cost is a backend measurement
(§9), not a guess made here.

**The sweep does not run live.** All 30 cells are an **offline** robustness study, run before the
draft, over the registered state set. Live inference runs the central cell only. This is precisely why
the adopt threshold in §8.2 is gated on the offline sweep: the live answer is trustworthy only in the
regime where the offline sweep showed the ordering does not depend on the parameters we cannot pin
down.

**5.2 Degraded ladder, in firing order.** Each rung states what it costs.

| Rung | Change | What is lost |
|---|---|---|
| 0 — Full | `\|C\|` = 8, `N` = `N_full`, H3 + H1 | nothing (within the offline sweep's validity) |
| 1 — Reduced N | `N` = `N_min` (SE_MC target relaxed to 1.0 pt) | Precision. Rule: report an ordering only if `\|Delta\| > 2 × SE_MC`; otherwise the card says **"too close to call under our model"** — which is a legitimate output, not a failure to answer. |
| 2 — Reduced candidates | `\|C\|` = 5, top-5 by VBD | Lookahead becomes a **re-ranker of VBD's shortlist**, not an independent search. It can no longer surface a candidate VBD ranked 6th. Say so in the card's mode line. |
| 3 — H1 only | Drop the H3 roster simulation; show survival-to-next-pick only | The roster-value claim entirely. The card must switch to availability language and drop every VONA phrase. |
| 4 — Cached | Reuse the previous pick's result | Freshness. **Valid only if** no member of `C` was drafted since and ≤ 2 picks have elapsed. Otherwise recompute or fall to rung 5. |
| 5 — Floor | Plain need-weighted VBD + marginal availability | Lookahead entirely. Card states "lookahead unavailable this pick." |

**Hard requirement: no silent degradation.** The card names the mode that produced the number, every
time, including at rung 0. A product whose central claim is rigour cannot have an invisible quality
switch — a user comparing a rung-2 number to a rung-0 number from the previous round is comparing two
different quantities without knowing it.

**5.3 Speculative precomputation (offered to backend, not mandated).** Start the simulation when the
user's pick is two away, using the then-current board, and refresh incrementally as picks land. Most of
the H3 cost is opponent picks that will be simulated regardless of what the user chooses. Whether this
is worth the complexity is a feasibility call.

### 6. Why the relative framing is defensible here, and exactly where the defence stops

The objection is live: simulated drafts come from **our** opponent model, whose `lambda` was fitted on
a single real draft with 10 clusters and whose `sigma` is uncalibrated. Any claim resting on them
partly measures our model rather than the world.

**Why it bites less here than for calibration.** A calibration claim is *absolute* — "when we say 33%,
it happens a third of the time" — so model error passes straight through into the number. A
recommendation is *relative*: both branches are simulated under the same opponent model, the same
`sigma` draw (CRN, §3.1), the same `delta`, and the same continuation policy. Only the initial action
differs. Errors common to both branches shift `V(c1)` and `V(c2)` in the same direction and cancel in
`Delta`.

**Where the cancellation stops — stated because "largely cancels" is where over-claiming would enter.**
Cancellation is exact only for model error that is *independent of the choice*. It fails wherever the
error **interacts with the branch**:

- **Cross-positional comparisons are the weak case.** If real managers run on TE harder than the model
  says, the branch that takes the TE now and the branch that waits are affected differently. The error
  does not cancel; it has a sign that favours one branch.
- **Same-position comparisons are the strong case.** "Bowers or Kittle" shares nearly all of the
  positional dynamics, so the residual interaction is small.
- **`draft_sim` assumption 3 (opponents never adapt) is a directional, non-cancelling bias.** Its own
  docstring states it "makes reaching look cheaper than it is, because no one punishes you for it."
  In VONA terms it systematically flatters the *wait* branch — the model believes a player will come
  back to you more often than a real, adapting room would allow. This bias is in the direction that
  makes lookahead look valuable, and it is not removed by CRN, larger N, or the parameter sweep.

**Operational rule following from that:** for **cross-positional** comparisons, the adopt threshold
(§8.2) requires agreement across the **full** 30-cell sweep. For **same-position** comparisons, the
central cell plus the `sigma` sweep suffices. Different robustness requirements for different claim
types, decided in advance rather than after seeing which comparisons were awkward.

**Unchanged by this ADR:** the availability percentages on the board remain absolute claims, still
governed by the existing calibration caveat (1 of ~30 mocks logged; ADR-D contamination control must
land before collection). Nothing in this ADR improves them, and the lookahead's relative-framing
defence does not extend to them.

### 7. Known biases carried in from the simulator, and what each does to a VONA number

Listed so a reviewer can check them rather than rediscover them.

| `draft_sim` assumption | Effect on VONA |
|---|---|
| 1 — `sigma` uncalibrated | Sets how much players slide; drives every survival probability. Swept (§4), never fixed silently. |
| 2 — noise drawn once per draft | Correct modelling choice for "the room valued him a round high this year." Keep; it is also what makes CRN meaningful. |
| 3 — opponents do not adapt | **Directional, non-cancelling.** Flatters waiting. See §6. |
| 4 — need is an additive rank penalty | The opponent-side need model is a judgement call (`NEED_TARGETS`), distinct from the `lambda`-based hazard need model. Two different need models are live in this codebase; the ADR requires the VONA path to state which it used. |
| 5 — DEF is a constant | Cancels in `Delta`. Absolute roster totals understate by one starter. |
| 6 — lineups set with perfect hindsight | **Live inference is unaffected** (no actuals exist at draft time; scoring uses projections). **The backtest validation arm is affected** — hindsight flatters deep rosters, which biases toward whichever branch builds depth. Validation therefore uses a **no-hindsight lineup rule**: set the lineup from projections, score with actuals. If both are reported, the no-hindsight number is the headline. |
| 7 — no in-season management | Bounds the whole claim to the draft in isolation. Stated on the card's methodology link, not buried. |

### 8. Pre-committed thresholds — both, written before anything runs

Registered under ADR-C as family `F-VONA`, with `m` fixed at registration.

**8.1 The evaluation state set, frozen first.** ≥ 200 draft states sampled from seeded simulated drafts
at `USER_SLOT`, stratified across rounds 1–10 (both the 15-gap and 5-gap positions), **plus** every
user-facing state from the one real 2025 draft on file. Frozen and hashed before any threshold is
evaluated, so the state set cannot be reshaped once results are visible.

**8.2 ADOPT — lookahead replaces plain VBD in the recommendation — iff all four hold:**

1. **Sweep robustness.** Top-1 agreement across the applicable sweep (full 30 cells for cross-positional
   comparisons, central + `sigma` for same-position) is **≥ 90%** of states, and top-1-vs-top-2 sign
   stability is **≥ 90%**.
2. **Material and real under the model.** In states where lookahead's top-1 differs from greedy VBD's,
   the paired `Delta` in end-of-draft starter points is positive with a **draft-level** bootstrap 95% CI
   excluding 0, and the median `|Delta|` exceeds **1.0 projected starter point over the season**. The
   substantive floor is deliberate: a statistically clean 0.2-point difference over 16 weeks is not a
   decision.
3. **Precision and latency.** `SE_MC ≤ 0.5` points at the adopted `N`, within the 2.0 s p95 budget at
   rung 0 or 1.
4. **Determinism.** Two runs in separate processes from the recorded seed produce identical orderings
   (guardrails §11 — this project has already shipped a "seeded" result that was not).

**Note on resampling unit in criterion 2, and why it is draft-level.** "Which policy wins *under our
model*" resamples at the **draft** level, and drafts can be simulated without limit, so it is
answerable to tight intervals today — this is precisely the FR-005 distinction that reopened this class
of question. "Which policy wins **in the real world**" resamples at the **season** level, n=4, where
`draft_sim.sign_test` already reports `min_achievable_p = 0.125`: no strategy comparison can reach
conventional significance there regardless of effect size. The adopt decision therefore rests on the
draft-level question, and **the real-world phrasing is forbidden in every artifact** (§10). The
historical-season arm is run and reported as descriptive, n=4, with the sign test's power ceiling
printed next to it.

**8.3 SHELVE — judged not decision-relevant — if any of:**

- Top-1 agreement across the applicable sweep is **< 75%** of states; **or**
- The ordering flips within **± 1 clustered SE of `lambda`** (0.282 → 0.422) in **> 10%** of states; **or**
- Median `|Delta|` in disagreement states is **< 1.0 projected starter point** or below the `SE_MC`
  achievable inside the latency budget.

**Consequence, pre-committed:** ship plain need-weighted VBD, keep the lookahead as an offline analysis
tool, and state the finding in those words — *"at the current uncertainty in the opponent model, the
lookahead does not change the recommendation often enough, or by enough, to be worth showing."* That is
a legitimate, useful, publishable result about the opponent model's precision. Registering it here in
advance is what stops it being reframed later as a failed sprint, and what stops the alternative
failure mode: adopting the lookahead because the output looks sophisticated.

**8.4 The middle band (75–90% agreement): disclose, do not override.** Show the lookahead's
ordering-hold rate as information *beside* the VBD recommendation; do not reorder the card. This is the
same shape thread 044 already chose for roster awareness — a constraint and a disclosure, not a hidden
scoring weight — and it is the honest treatment of a signal that is real but not robust.

### 9. Measurements needed from `backend` (I cannot run these)

Specified to be executable without a round trip.

1. **Per-simulation wall clock** for one full 160-pick `simulate_one` at the current board size, on the
   founder's machine, single-threaded and vectorised-batch, reported separately.
2. **Pilot `sd(Delta_i)`** over 500 CRN replicates on 20 sampled states, for a representative
   cross-positional pair and a representative same-position pair. This sets `N` via §3.2; do not pick
   `N` first.
3. **Feasible `N` inside 2.0 s p95** for `|C|` = 8 and `|C|` = 5, which fixes where rung 1 and rung 2
   sit.
4. **Which need model the VONA path uses** — `draft_sim.NEED_TARGETS` (opponent-side judgement call) or
   `live_availability`'s `lambda` hazard need. They are different objects; running one while reporting
   the other would be a silent inconsistency.
5. **Confirmation that CRN survives the call path** — same replicate seed, both branches, identical
   `effective_rank`; verified by asserting equality of the drawn board across branches, not by
   inspection.

### 10. Output language — the exact constraint

**Required form:**

> *"Under our opponent model (λ=0.352, σ=10, δ=0.10, and assuming you then draft need-weighted best
> value at every later pick), taking Bowers here ranked ahead of Olave in **78%** of 2,000 simulated
> continuations (Monte Carlo SE 0.9 pp). This ordering held in all 30 parameter cells we swept."*

Every element is load-bearing: the model qualifier, the named parameters, the continuation-policy
disclosure, the simulation count, the Monte Carlo SE, and the sweep result as the model-uncertainty
statement.

**Forbidden, anywhere — card, tooltip, export, assistant, ADR, status entry:**

- "Bowers is the better pick."
- "There is a 78% chance Bowers is the right choice." *(The 78% is a property of our simulations, not a
  probability about the world.)*
- "This will leave you 4 points better off."
- Any sentence that drops "under our opponent model."
- Any presentation of the H1 survival diagnostic as a roster-value claim, or vice versa (§2).
- Any use of the phrase "beats consensus" or "edge" derived from these simulations. Simulations
  measure our model; they cannot measure the market.

### 11. Standing refusals, restated

- **No per-manager opponent parameters, and no inference of an opponent's strategy from their picks.**
  n=1 league. The mechanical arithmetic of what roster slots a team still needs is observable and is
  already used (`live_availability` need shares). The latent intent behind their picks is not
  identifiable at this sample size, and a hedged version of that inference is not an acceptable
  compromise — it is the same claim with a softer verb.
- **No fitting `sigma` to the simulations themselves.** It is uncalibrated because no observed
  draft-position data exists (ADR-018). Sweeping an unknown is honest; fitting it to the thing it
  generates is circular. This is the ADR-A precedent: an unidentifiable magnitude gets bounded, not
  fitted.
- **No adoption on qualitative impression.** §8.2 or §8.3; there is no third path.

---

## Consequences

- The offline sweep must run before the draft, not after adoption. It is the load-bearing artifact —
  live inference is only as trustworthy as the sweep that licensed it.
- The recommendation card gains a mode line and a methodology disclosure. Frontend work, gated on the
  adopt decision, so it should not start before §8 resolves.
- A shelve outcome is a realistic result — arguably the modal one given `sigma` is uncalibrated and
  assumption 3 biases in the flattering direction. Plan the sprint so that a shelve leaves a usable
  offline analysis tool rather than nothing.
- One founder decision goes to `decisions-needed.md` as **D-024**: the live latency budget and the
  real pick-clock length.

## What would falsify this ADR

- **`sigma` becoming calibrated** (ADP snapshots, or logged mock drafts with per-pick state). The
  dominant uncertainty would shrink, the sweep would narrow, and the shelve threshold might no longer
  bind. This is the single highest-value input to the whole question, which is another argument for the
  standing top open items — ADP snapshot capture and per-pick draft-state logging.
- **The continuation policy mattering more than the first pick.** If `Delta` is dominated by `pi`'s
  behaviour rather than by the candidate, the framing is wrong and the right question is about the
  policy, not the pick. Detectable: rerun with `pi` = `strategy_bpa` and see whether the ordering
  moves more than the parameter sweep moves it. Worth running early — it is cheap and it could
  invalidate the framing before the expensive work.
- **H1 and H3 disagreeing systematically.** If the candidate that survives less often is routinely the
  one with higher end-of-draft roster value, one of the two is measuring something other than what its
  label says, and both should be withheld until that is understood.
