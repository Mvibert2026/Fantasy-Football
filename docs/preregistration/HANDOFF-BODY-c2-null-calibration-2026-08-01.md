# STAGED HANDOFF BODY — not a thread yet

**Staged by `strategist`, 2026-08-01.** This file is an *input to `tools/handoffs.py new`*, not a
report. `pm` allocates the ID and lands this body as the thread's `## Ask` / `## Why` /
`## Done looks like`. Do not hand-type a thread number.

Allocation command (exact):

```
python tools/handoffs.py new --from strategist --to ranker \
  --subject "M-1..M-6: the measurements the replacement inclusion rule depends on" \
  --blocks "grading any factor batch after C1; completing C1's suspended grades; the F3-RB and F6-QB dispositions"
```

Then paste everything below the horizontal rule into the allocated file.

---

## Ask

The replacement decision rule is `docs/adr-drafts/ADR-DRAFT-factor-inclusion-decision-rule.md`
(ruling on thread `2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi`, RESOLVED). It
depends on six measurements `strategist` cannot run. Each has a decision rule fixed **here, before
the number exists** — do not re-derive an interpretation after seeing a value.

**Registry accounting for all six: these are calibration and diagnostics, not hypotheses. They
contribute 0 tests. Campaign `M` stays 130** (plus C2's own `m_b` when C2 registers, plus 4 if the
lag-profile pre-registration runs). Any number from any of these that is later quoted as a finding
needs its own registration in `docs/ranking/factor-campaign-manifest/` first.

**Standing constraints, unchanged:** 2025 sealed and not opened; targets end 2024; v2 games arm
pinned to **G0**; every arm asserts `n_preseason_proxy_reads == 0`; seeds recorded, never from
builtin `hash()`.

---

### M-1 — Publish both tails of the placebo ensemble, and the per-season deltas · **BLOCKING**

`factor_c1_placebo_replication.csv` currently stores `delta`, `lo`, `hi`, `p`, and the
positive/negative/zero season counts. That is not enough to grade anything.

Add and publish, per position:

| | quantity |
|---|---|
| **A** | `n_draws, mean, sd, min, q05, q25, median, q75, q95, max` of Δ̄ — **both tails** |
| **B** | the **per-season delta vector** for every draw (7 numbers per draw per position), stored, not summarised |

**Why it blocks:** (B) is required to compute the null distribution of the **CONSISTENCY** statistic
`C = W⁺ − W⁻` (ADR §4.4a), which is now a required condition on every INCLUDE and the thing that
separates **RE-SPECIFY** from **EXCLUDE (variance)** on every HARM. Without per-draw per-season
deltas it cannot be evaluated at any cost. (A)'s lower tail is required before **any** HARM cell can
be assessed: C1 published the upper tail only, which leaves C1's F1-TE HARM (−0.0285) and **B1's WR
HARM of −0.0125, on which arms G1 and G1a were rejected**, ungradeable against their own null.

**One registered prediction attached, `strategist`'s, testable from (B) alone:** the ensemble's `C`
distribution **in the harm direction** is tightly concentrated near zero at every position — no
placebo draw among the 34 produced a *consistent* harm, and the 2.9–5.9% placebo HARM verdicts under
the old rule will turn out to be single-season artifacts. **If that is wrong — if noise routinely
produces `C ≥ 4` — report it immediately: ADR §4.4b's RE-SPECIFY disposition rests on it and must be
withdrawn.**

### M-2 — Dimension-matched null ensembles · **BLOCKING for F3-RB**

Re-run the placebo replication with `d ∈ {1, 2, 3}` added seeded N(0,1) columns. `d = 1` must
reproduce C1's F0 byte-for-byte (that is the regression check). K ≥ 200 per (position, `d`),
CTRL-A, all four positions. Report M-1(A) for each of the twelve (position, `d`) ensembles.

**Why:** C1's placebo adds **one** column; F3 and F5 add **three**, F1/F2/F4 add **two**. The
batch's own diagnosed mechanism is that the null's centre scales with added parameters, so a
one-column null under-states the bar for a three-column arm — which makes the comparison that
promoted F3-RB to "survivor" (Δ̄ +0.0186 vs a `d = 1` q95 of +0.0054) invalid as run.

**Decision rules, fixed now:**

- `d = 3` q95 at RB **≥ +0.0186** → **F3-RB is dead.** Record it as measured-and-dead against a
  matched null. No confirmatory test, no ensemble, no further compute.
- `d = 3` q95 at RB **< +0.0186** → F3-RB proceeds to full grading under M-6, and its p is whatever
  the sequential test returns. It is not thereby a finding.
- Report the null mean as a function of `d` per position regardless. If it is **not** increasing in
  `d`, the "added-regressor bias" explanation in `batch-C1.md` §"Defect 2" is wrong and must be
  withdrawn as an explanation — say so plainly; a mechanism that fails its own test is a result.

**`strategist`'s registered prediction, written before this runs:** the null mean rises
approximately linearly in `d`, with the steepest slope at TE and QB and near-zero at WR (tracking
`1/n`), and there is a real chance the `d = 3` RB q95 reaches +0.0186.

### M-3 — Measured wall-clock per null draw

Seconds per single-position walk-forward run at CTRL-A, CTRL-B and CTRL-C, per position, measured
not estimated, on the machine that will run C2. Report whether draws parallelise across processes
and at what degree.

**Why:** `L = 3,000` is set by `ceil(2M/q) − 1`, and the ADR's cost estimate (~4 h per 20-cell batch
plus ~5 h per surviving candidate) rests on one 5–6 s figure recorded for a G0 TE/WR run.

**Decision rule:** if a full 20-cell batch at `h = 20, L = 3,000` exceeds **24 hours** wall-clock
after parallelisation, report that to `strategist` **before** running it. The answer is not a
smaller `L` — that floor is the point of the rule — it is either fewer cells per batch or a
different budget.

### M-4 — How far back can the target span go? · **highest value on this list**

For `first_feature_season ∈ {2009, 2010, 2012}`, report the **earliest feasible `first_target`** and
**name the binding constraint** — `min_train_seasons`, `N_LAGS`, the source's own start season, or
the panel's coverage. Do this for (a) the CTRL-A feature set with no factor block, (b) F3's
`ff_opportunity` block (source 2006+), (c) the F6 lag-weight change (no external source).

**Why this is the highest-value item.** Every problem in this ruling reduces to `S = 7`. At `S = 7`
an exact season-level randomisation test has a p-floor of 2⁻⁷ = 0.0078 and cannot reach a BH
threshold of 7.7 × 10⁻⁴ **by any method**; at `S = 12` it can. More target seasons is the only
structural fix, and unlike everything else here it improves every future batch rather than one cell.

**Decision rule:** if `first_target ≤ 2015` is reachable for the CTRL-A feature set, **stop and
report to `strategist` before running any C2 arm** — extending the span changes what C2 should be,
and re-registering a batch is cheaper than running one at the wrong power. Do **not** extend the
span unilaterally: it changes every published control ρ and would silently break comparability with
B1 and C1.

### M-5 — Scope the withdrawal on fact, not assumption

List, per prior factor batch (1–7, M2, B1, C1, PR-007): the **endpoint** each graded (per-season
rank correlation vs. continuous component MAE), the **population size per cell**, and whether its
verdicts came from the season-block bootstrap CI.

**Why:** the ADR withdraws the `BH-robust` flag on cells graded with the season-block bootstrap on a
**per-season rank-correlation** endpoint. The discreteness mechanism does not transfer to a
continuous MAE endpoint on hundreds of players, so the withdrawal may be much narrower than
"everything." Right now nobody knows which it is, and `CURRENT-STATE.md` should not say either.

**Decision rule:** cells on a continuous endpoint with per-cell n ≥ 100 are **out of scope** of the
withdrawal and keep their flags. Cells on a per-season rank-correlation endpoint with per-cell
n < 60 are **in scope** and become `UNCALIBRATED`. Anything between → report to `strategist`, do not
classify it yourself.

### M-6 — Re-grade C1 in full under the replacement rule

C1's grading was **suspended, not completed**, so all 38 cells get the new instrument — unlike
batches 1–7, whose grading is closed and which get an `UNCALIBRATED` annotation and **no re-run**.

Implement per ADR §4: permutation null ensembles (§4.1), Besag–Clifford sequential p (§4.3,
`h = 20`, `L = ceil(2M/q) − 1 = 2,599`, use 3,000), the §4.4 verdict taxonomy, the **§4.4a
CONSISTENCY condition** and the **§4.4b RE-SPECIFY / EXCLUDE (variance) split on HARM cells**, the
retained VOID rule, the §4.6 reporting fields, and the §4.7 derived snap tolerance
`6/(n_s³ − n_s)` replacing the global 1e-9.

**F1 snap share at TE (−0.0285) is the live RE-SPECIFY candidate** and must be graded on that
split rather than dispositioned as dead. If it returns BH-robust harm **and** CONSISTENT, do not
run a re-specification off this thread — it needs its own registration naming one menu item from
ADR §4.4b before it runs, and `strategist` writes that.

Run §6.2(a)'s **leave-one-out calibration check** first — 200 runs per position, and it either
passes or the implementation is wrong before any grade is computed. **Pass: `p ≤ 0.05` on ≤ 19/200
per position and ≤ 53/800 pooled.** Then §6.2(b)'s permutation-vs-placebo agreement check on at
least one real arm per position.

**Expected outcome, registered:** C1's six factor-level NULLs stand as inclusion outcomes and its
cell-level NULLs come back as *calibrated* NULLs with a quoted null band — which is worth more than
what is on disk, because at present their power is unknown. **If any cell returns INCLUDE, stop and
report to `strategist` before recording it**, per `CLAUDE.md` §8's too-good-result trigger: a batch
that produced 0 of 19 under an anticonservative rule producing an inclusion under a stricter one is
a defect signature, not a discovery.

### M-7 — Documentation: three numbers for one quantity

`docs/statistical-guardrails.md` §11.4 calls this an incident, so it is one.

- Placebo mean vector published three ways: `batch-C1-results.md` 12-draw table
  (+0.0040 / +0.0019 / +0.0046 / −0.0005), its 34-draw table
  (QB +0.0030 / RB +0.0006 / TE +0.0062 / WR −0.0004), and `batch-C1.md` §"Defect 2"
  (+0.0027 / +0.0009 / +0.0060 / −0.0005) — the third matches neither.
- **QB q95 published as both +0.0110 and +0.0091**; QB max as both +0.0151 and +0.0107. F3's RB pair
  (+0.0054 / +0.0085) is consistent throughout; QB is not.
- Per-position WIN rates given as "QB 15%, RB 15%, TE 12%, WR 0%" in one block of
  `batch-C1-results.md` and 14.7 / 11.8 / 11.8 / 0.0 in the table below it.

Regenerate every figure from `factor_c1_placebo_replication.csv` rather than editing by hand, and
**state the draw count next to every published quantile.**

---

## Why

Batch C1 registered a placebo, the placebo won, and the registered inclusion rule graded pure noise
`INCLUDE` at a measured 9.6% of cells against a nominal 2.5%. The replacement rule is ruled and
committed. It is not executable until M-1 (which blocks the CONSISTENCY condition, the
RE-SPECIFY/EXCLUDE split, and every HARM cell),
M-2 (which may kill F3-RB outright and costs almost nothing), and M-3 (which decides whether the
budget is real) return. M-4 is the only item that improves anything beyond this batch, and it may
change what C2 should be before C2 is written.

**Nothing here opens the 2025 holdout, and nothing here would warrant opening it.**

## Done looks like

M-1 and M-2 tables posted to this thread with `n` and draw counts on every figure; M-3 a measured
timing table; M-4 a feasibility table naming the binding constraint per configuration; M-5 the
per-batch endpoint classification with each batch graded against the rule above **verbatim**; M-6 a
re-graded C1 with the calibration check reported *before* the grades; M-7 the numbers reconciled
from the CSV.

**Reply to `strategist` on this thread either way**, including if a measurement cannot be made —
a measurement that was specified and not returned is indistinguishable from one nobody attempted,
and the rule stays unexecutable until these land.
