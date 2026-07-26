# ADR-D — Contamination control in Mock Lab logging

**Path:** `docs/adr/ADR-D-mock-logging-instrumentation.md`
**Status:** Proposed
**Date:** 2026-07-26
**Owner:** Strategist (spec) / Backend (execution) / Frontend (entry surface)
**Thread:** [034](../handoffs/034-shortcut-bias-in-mock-logging.md)
**Test-registry family:** `F-MOCKLOG`
**Pre-registrations created:** `PR-005`, `PR-006`, `PR-007`

## Context

Mock Lab exists to make the product's central claim — calibrated availability — true. Doing that needs
~30 mocks × ~160 picks ≈ 4,800 logged entries, so entry cost decides whether the claim ever gets
tested. The design's answer (`docs/design-handoff/mock-lab/MOCK-LAB-SPEC.md` §1) is to make the
model's own prediction the fastest input device: the hazard model's five most-likely-next players
render in confidence order with probabilities attached, and a digit commits one.

Thread 034 asks whether that contaminates the measurement. It does, and the reason is worth stating
precisely rather than as a worry about a tired user.

**The mechanism is a feedback loop between the estimator and its own data collection.** The design
names the loop approvingly: "the better calibrated the model gets, the more picks its top five covers,
and the faster logging becomes." Read that sentence in the other direction and it is the defect. The
same coupling that makes better calibration cheaper to log makes cheaper logging look better
calibrated. There is no way to keep one direction and discard the other; they are the same arrow.

**Why the error is the bad kind.** A logging error that is independent of the model's prediction is
non-differential measurement error: it attenuates, biasing calibration *toward* chance. That is a loss
of power, and it is safe, because it works against the claim. An error that substitutes the model's own
candidate for the true pick is *differential* — correlated with the quantity being estimated — and it
biases toward the claim. Differential misclassification cannot be bounded from the contaminated data
alone and does not shrink with more data. 4,800 entries at a 1% substitution rate is 48 manufactured
hits; at 5% it is 240.

**Rough magnitude.** If the true hit rate in a bucket is `p` and a fraction `s` of picks that should
have been logged as something outside the shortlist are instead logged as a shortlist member, observed
rate ≈ `p + s(1 − p)`. At `p = 0.35`: `s = 0.01` adds 0.7 points, `s = 0.05` adds 3.3 points. The
design's own evidence ladder claims ±6 points at 30 mocks. So contamination anywhere above roughly
`s = 0.03` moves the estimate by a material fraction of its own stated interval.

**The constraint that determines the whole answer: there is no ground truth.** No independent record of
the real pick sequence exists — what the founder logs *is* the record. Measuring an error rate requires
a second, more accurate measurement of the same event, and we have none. Every option that tries to
*detect* the substitution rate is therefore fighting the wrong problem. The winnable problem is to make
the estimate *immune* to substitution, which is cheaper and needs no detection at all.

Two other facts shape the cost side. D-009 has removed the draft-deadline constraint, so entry-time
cost is no longer competing with a date. And D-015's rigorous default (per-configuration targeting)
means the 30 is per league config, so any design that discards mocks is more expensive than it looks.

## Assessment of the three candidates

### (a) Randomise the order of the five — **rejected**

It addresses the reflex (`press 1`), not the mechanism (commit from the presented set without
verifying). A careless user under randomisation still selects *a member of the model's top five*, so:

- `in_top_5` and top-5 coverage — the quantities the shortcut most directly inflates — are affected
  exactly as before. Randomisation does nothing to them.
- Per-player probability calibration gets *worse*, not better. Substitution now lands on a random
  member, moving hits from the high-probability candidate onto low-probability ones. That scrambles the
  calibration curve in a direction that depends on which member was mis-pressed, converting a bias
  whose sign is known into one whose sign is not. A signable bias you can reason about is strictly
  better than an unsignable one.
- It is not free. A stable, confidence-ordered list is *recognised*; a shuffled one must be *searched*.
  That is a per-pick read of five names instead of a glance, on a 4,800-pick budget, purchased for no
  measurement benefit.

Rejected on the merits, not on cost. Note this is not inconsistent with the reordering adopted in D-1
below: board-rank order is stable, learnable, and matches the ordering the founder is already reading
off the mock site, so it preserves recognition. Randomisation destroys recognition and buys nothing.

### (b) Instrument with `entry_mode`, then compare calibration shortcut-vs-typed — **instrumentation adopted, the proposed comparison refused**

The instrumentation is right and is adopted in full. **The comparison as specified in thread 034 cannot
be run, and I will not produce a hedged version of it.**

A pick is shortcut-entered *because* the true pick appeared in the model's top five — that is, because
the model was right. A pick is typed *because* it did not — because the model was wrong. Assignment to
entry mode is a deterministic function of the outcome being measured. Shortcut-entered picks will show
better model accuracy than typed ones by construction, at a substitution rate of exactly zero. The
contamination effect and the selection effect are perfectly collinear; the comparison has no
identifying variation and its result is uninterpretable in either direction. Running it would produce a
large, highly significant number that means nothing, and that number would then be quoted.

This is the same class of error as `_rank_correlation` pooling positions (ADR-B): not a weaker version
of the right measurement, a different measurement.

What *can* be tested from the instrumentation is behavioural, not calibrational, and it survives
because it holds entry mode fixed: **within shortcut-entered picks only, does faster entry predict
slot-1 selection, conditional on how obvious the pick was?** That is `PR-005` below. It has a residual
confound (obvious picks are both fast and genuinely slot-1, and stated probability is an imperfect
proxy for subjective obviousness) which biases it *toward* flagging contamination — the correct
direction for a screen, and stated rather than hidden.

### (c) A blind control arm — **rejected as an inferential test, adopted as a protected estimate**

As a hypothesis test of "is there contamination," the arithmetic kills it. Per-mock rate is the
resampling unit — picks within a mock share drafters, board-state trajectory, session, config, and
fatigue state, and bootstrapping over 4,800 picks would produce an interval that narrows with grind
rather than with evidence. That is the pseudo-replication error that closed the alpha-detection track
(ADR-026) and it must not reappear here.

With `k` blind and `n − k` sighted mocks and between-mock SD `σ` of the per-mock rate,
`MDE = 2.802 · σ · √(1/k + 1/(n−k))` at 80% power, two-sided α = 0.05.

| σ (assumed) | MDE at n=30, k=10 | MDE at n=30, k=15 | n needed for MDE = 0.03, balanced |
|---|---|---|---|
| 0.04 | 4.3 pts | 4.1 pts | **56** |
| 0.05 | 5.4 pts | 5.1 pts | **87** |
| 0.07 | 7.6 pts | 7.2 pts | **171** |
| 0.10 | 10.9 pts | 10.2 pts | **349** |

`σ` has never been observed and every figure here is conditional on it; the table is the honest form of
the answer, and Backend must recompute it from the blinded pooled variance after 6 mocks (see §Blinded
nuisance amendments).

**Plainly, as thread 034 asked:** detecting a contamination difference at the level that actually
matters — around 3 percentage points, half the design's own stated half-width — needs on the order of
**90 to 350 mocks**, best guess ~170. Against a target of 30 that is 3–12× the entire collection
programme. **It is not collectable, and it will not be collectable.** An underpowered version is worse
than none, because it returns "no significant difference" and that null gets quoted as "we checked."

But the *structure* of (c) is still the only thing that yields an uncontaminated absolute estimate, and
its cost has been overstated. Keyboard entry is ~2s/pick ≈ 5 min per mock; typeahead-only entry with no
shortlist is realistically ~3s/pick ≈ 8 min. Ten blind mocks cost roughly **30 extra minutes across the
whole programme**, and D-009 removed the deadline they would have competed with. So the blind arm is
adopted — not as a test, as the carrier of the headline number.

### Options thread 034 did not list

**(d) Decouple the shortlist from the quantity under validation.** The contaminating element is not
that five names are shown; it is that those five names *are the hazard model's answer*, in its
confidence order, with its probabilities attached, so one keystroke both records data and agrees with
the model. A shortlist generated by something that is not the object of validation costs the same
keystroke and breaks the loop. Adopted (D-1).

**(e) Co-measure a model-free baseline on identical picks.** Store, write-once at entry, what a
zero-fitted-parameter baseline predictor would have said. Contamination toward the displayed shortlist
inflates both the model and the baseline; the *difference* is protected. Combined with (d) — where the
displayed shortlist *is* the baseline — the contamination pushes the model's increment over baseline in
the **conservative** direction: it makes our model look worse relative to its baseline, not better. A
bias that runs against the claim is the only kind it is defensible to leave in. Adopted (D-3).

**(f) The paste-mode contamination path nobody has flagged.** Paste mode resolves names by fuzzy match.
The natural implementation breaks ties by "which of these candidates is more likely to be picked here"
— which would make the calibration data *literally generated by the model being calibrated*, silently,
on the mode the spec calls the marketed path. This is the highest-value single item in this ADR: it is
invisible once shipped, free to prevent now, and would be unrecoverable after 30 mocks. Adopted as a
hard structural rule (D-4).

## Decision

### D-1 — The entry shortlist is not the hazard model, and no probabilities appear during entry

For all sighted logging:

- The displayed five are the **top five available players by frozen pre-draft board rank**
  (`shortlist_source = board_rank_frozen`), in board order. Stable, learnable, and the same ordering
  the founder is reading off the mock site.
- **No probabilities are rendered during entry.** The `39%` / `26%` column in MOCK-LAB-SPEC §2 comes
  off the entry surface.
- Nothing on the review or calibration surfaces changes. `WE SAID`, `OUR TOP CALL`, `VERDICT`,
  `SURPRISE`, the frozen-prediction banner and the calibration dots are all post-hoc, all served from
  write-once stored predictions, and are unaffected. The founder loses no information they need at
  entry time — availability at decision time is the *Draft* screen's job, not the logging tool's.
- The board artifact is a legitimate source: it is frozen pre-draft, is not fitted to mock data, and
  mocks are judge-only by guardrail (ADR-C's `MockDataViolation` loader guard). Its hash is recorded per
  pick.
- **The hazard model still runs and its output is still stored** (`predicted_top`, `predicted_p`,
  `predicted_top5`, `model_artifact_hash`) — write-once, at entry, exactly as before. It is simply not
  displayed. This keeps calibration fully computable and makes the coverage cost of D-1 measurable
  after the fact rather than debated in advance.

Reverting `shortlist_source` to `hazard_model` requires a new ADR, not a config change.

### D-2 — A randomised blind arm carries the absolute calibration claim

- `blind_arm` is assigned at **mock creation, before any pick is entered**, by seeded RNG. Seed and
  assignment timestamp recorded; a storage-level check enforces `arm_assigned_at < min(entered_at)`.
  The founder must not choose which mocks are blind — that choice would be made on convenience, and
  convenience correlates with everything.
- **Block randomisation, block size 3, one blind per block** → `k = 10` of `n = 30`. Blocking rather
  than simple randomisation because at n=30 simple randomisation routinely yields 6/24 or 14/16, and
  because blocks of 3 keep the arms balanced against `session_index` at every point in the programme.
  Fatigue and learning are the dominant confounds in a single-operator study, and `session_index` is
  the only handle on them.
- A blind-arm mock shows **no shortlist at all** — typeahead only, `shortlist_source = none`,
  `predictions_visible = 0`. Undo, tempo readout and every other affordance are unchanged.
- **What k = 10 buys, stated honestly.** Roughly the design's own "10 mocks" rung — about ±10 points
  before the design effect below, so realistically **±13 to ±16 points** on the largest bucket. That is
  **not enough to certify calibration.** It is enough to refute gross miscalibration and to give the
  headline number a provenance that does not depend on the model that produced it. An honest ±14 is
  worth more than a contaminated ±6, because the width is measured and the contamination is not.

### D-3 — A model-free baseline is co-measured on every pick

Store, write-once at entry alongside `predicted_*`: `baseline_id`, `baseline_artifact_hash`,
`baseline_top`, `baseline_p`, `baseline_in_top_5`, `baseline_top5`.

`baseline_id = adp_rank_exp_v1`: "the next pick is the highest-frozen-board-rank available player,"
with per-player probabilities from a rank-exponential rule whose decay is **fixed by fiat and frozen in
this ADR, never fitted** — a fitted baseline is a second model and inherits the same problem. Zero free
parameters estimated from mock data.

This is guardrails §5 (the baseline rule) applied to a measurement-error problem, and it is what makes
the *relative* claims — hazard vs baseline, and need+run vs marginal-only, the `delta` decision in
D-004 — robust to contamination even in the sighted arm.

### D-4 — Matcher independence (structural, no data required)

**The typeahead ranker and the paste/bulk fuzzy matcher must not consult the availability model, the
hazard output, board rank, or any prediction — for ranking, for tie-breaking, or for anything else.**
Candidate ranking is string distance plus position/team metadata only. Ambiguity above a fixed,
pre-declared distance threshold surfaces for explicit human resolution (`paste_confirmed`) rather than
auto-resolving.

Enforced by a static test: the matcher module may not import the availability, hazard, or board
modules. If violated after mocks exist, the affected picks are **excluded from calibration entirely,
not corrected** — a contaminated resolution cannot be undone from the stored row.

### D-5 — The on-screen evidence ladder overstates precision

MOCK-LAB-SPEC §5 states the ladder is "the real 95% Wilson half-width at that sample size." Wilson
assumes independent Bernoulli trials. Picks within a mock are not independent, so with `m` picks per
bucket per mock and intra-mock correlation `ρ`, the design effect is `1 + (m − 1)ρ` and the true
half-width is `√DEFF` times wider. At `m ≈ 32` and `ρ = 0.02`, `DEFF = 1.62` (1.27× wider); at
`ρ = 0.05`, `DEFF = 2.55` (1.60× wider).

**The honest ladder at 30 mocks is roughly ±8 to ±10 points, not ±6.** Every interval in Mock Lab —
ladder, Wilson bars, bucket bands — must be computed with a mock-level design effect or by mock-level
bootstrap, and `ρ` must be estimated and reported rather than assumed. Shipping ±6 would be the exact
false-precision failure this project polices in competitors' composites.

## Exact fields to log

Write-once means write-once: reject an update, do not overwrite. Six fields are `NOT NULL` **with no
default** — a default would silently mislabel any code path the engineer forgot to instrument, and the
mislabel would be indistinguishable from real data.

### Per pick — new columns on `mock_picks`

| Field | Type | Null | Default | Meaning |
|---|---|---|---|---|
| `entry_mode` | TEXT, CHECK in enum | NOT NULL | **none** | how this pick was committed (enum below) |
| `shortcut_slot` | INTEGER 1–5 | NULL ok | — | which displayed row was committed; NULL if not a shortcut |
| `shortlist_rank_of_pick` | INTEGER 1–5 | NULL ok | — | where the logged player sat in the *displayed* shortlist, populated even for typed picks; NULL if not on it |
| `shortlist_shown` | TEXT (JSON array of 5 ids, displayed order) | NOT NULL | **none** | write-once record of what was on screen. Without this, `in_top_5` is uninterpretable after any board or model change |
| `shortlist_source` | TEXT: `board_rank_frozen` \| `hazard_model` \| `none` | NOT NULL | **none** | which generator produced the displayed five; defines the arm at pick granularity |
| `predictions_visible` | INTEGER 0/1 | NOT NULL | **none** | whether probabilities were rendered during entry for this pick |
| `dwell_ms` | INTEGER | NULL ok | — | monotonic-clock ms from shortlist-rendered-and-focused to commit. `performance.now()`, **not** `Date.now()`, and **not** a diff of consecutive `entered_at` (that includes render and idle time). NULL for bulk paste |
| `keystrokes` | INTEGER | NULL ok | — | key events in the field before commit. Independent of the mode label, so it catches mode-labelling bugs |
| `is_reentry` | INTEGER 0/1 | NOT NULL | **none** | re-entered after an undo. The superseded attempt keeps its own audit row |
| `predicted_top` | INTEGER | NOT NULL | — | existing; hazard model's top call. Write-once |
| `predicted_p` | REAL | NOT NULL | — | existing. Write-once |
| `predicted_top5` | TEXT (JSON array of 5) | NOT NULL | **none** | **new** — the hazard model's five, stored whether or not displayed. Makes calibration and the D-1 coverage cost computable |
| `in_top_5` | INTEGER 0/1 | NOT NULL | — | existing; must be defined against `predicted_top5`, not `shortlist_shown` — they now differ |
| `model_artifact_hash` | TEXT | NOT NULL | **none** | **new** — hash of the hazard model + board artifact that produced `predicted_*`. Required to define the comparison series MOCK-LAB-SPEC §7 assumes exists when the model changes mid-collection |
| `baseline_id` | TEXT | NOT NULL | — | `adp_rank_exp_v1` |
| `baseline_artifact_hash` | TEXT | NOT NULL | — | |
| `baseline_top` | INTEGER | NOT NULL | — | write-once |
| `baseline_p` | REAL | NOT NULL | — | write-once |
| `baseline_in_top_5` | INTEGER 0/1 | NOT NULL | — | write-once |
| `baseline_top5` | TEXT (JSON array of 5) | NOT NULL | — | write-once |

`entry_mode` enum, closed set: `shortcut_digit` · `shortcut_enter` (⏎ on the default-highlighted row,
no arrow movement — the cheapest possible action and the highest-risk one, so it must be separable) ·
`shortcut_arrow_enter` (↑↓ then ⏎ — evidence of deliberation) · `typed` · `paste_exact` ·
`paste_fuzzy` (auto-resolved, no human confirmation) · `paste_confirmed` (ambiguous, human chose) ·
`grid`.

Off-board picks are not an `entry_mode`; they remain `player_id = unknown` with `raw_text` retained,
and are excluded from calibration rather than dropped, per MOCK-LAB-SPEC §2.

### Per mock — new columns on `mock_drafts`

| Field | Type | Null | Meaning |
|---|---|---|---|
| `blind_arm` | INTEGER 0/1 | NOT NULL, no default | assigned at creation, before any pick |
| `blind_arm_seed` | INTEGER | NOT NULL | recorded seed |
| `blind_arm_block` | INTEGER | NOT NULL | block index (size 3) |
| `arm_assigned_at` | TEXT ISO-8601 | NOT NULL | must precede `min(picks.entered_at)`; enforce at the storage layer |
| `session_index` | INTEGER | NOT NULL | ordinal within the collection programme, **per `league_settings_hash`**. Recorded, never inferred from timestamps — backfill breaks inference |
| `logged_live` | INTEGER 0/1 | NOT NULL | concurrent with the mock vs from a results screen; different error mechanisms |
| `logging_mode` | TEXT | derived at close | `keyboard_sighted` \| `keyboard_blind` \| `paste` \| `grid` \| `mixed` |

Existing mock-level fields from the staleness retrofit (`league_settings_hash`, `config_summary`,
`rounds_logged`) are unchanged and remain required.

## Pre-registered tests

Family `docs/preregistration/families/F-MOCKLOG.yaml`, `m: 3`, `status: open`. BH within family over
m = 3.

**Why this is a separate family and not gerrymandering.** F-MOCKLOG tests hypotheses about the
*instrument* — whether the logging surface corrupts the record. The substantive families (the `delta`
Brier rule in D-004, `F-NEEDSCALE`) test hypotheses about the *football model*. A false positive in one
buys nothing in the other, and folding instrument checks into a substantive family would inflate that
family's denominator and make honest instrument-checking costly — the opposite of the incentive we
want. Stated explicitly because separating families is the obvious way to cheat BH, and the
justification has to be on the record before the tests run.

### PR-005 — Dwell-time dose-response screen (confirmatory)

- **Question.** Within sighted-arm shortcut-entered picks, conditional on how obvious the pick was, does
  faster entry predict selection of the shortlist's rank-1 row?
- **Population.** `shortlist_source = board_rank_frozen`, `entry_mode ∈ {shortcut_digit,
  shortcut_enter, shortcut_arrow_enter}`, `is_reentry = 0`, `dwell_ms IS NOT NULL`.
- **Primary metric.** Difference in rank-1 selection rate between the fastest and slowest dwell terciles,
  from a **stratified permutation test**: dwell labels permuted within `(mock × baseline_p decile)`
  strata, 9,999 permutations, seed recorded. Stratifying by mock absorbs every mock-level confound
  (fatigue, site, config, model version) without modelling it; stratifying by `baseline_p` decile
  conditions on obviousness. Assumption-light by construction.
- **Secondary metric.** Coefficient `β` on `log₂(dwell_ms)` in a logistic regression of
  `shortcut_slot == 1` on `log₂(dwell_ms)` with a `baseline_p` spline, SEs by **wild cluster
  bootstrap-t clustered on mock**, 9,999 replicates, seed recorded. Not CRVE: 30 clusters sits at the
  bottom of the reliable range, and this is the same correction already required for `lambda = 0.352`.
- **Decision rule — both conditions required.** Fires iff BH-adjusted one-sided p < 0.05 **and** the
  implied excess rank-1 rate at the 10th-percentile dwell versus the median dwell exceeds **0.03**.
  Significance alone does not fire it: an effect below 3 points is smaller than the interval it would
  perturb, and acting on it would be acting on noise.
- **If it fires.** Headline absolute calibration switches to blind-arm only; sighted picks below the
  10th-percentile dwell threshold are excluded from all calibration, and the excluded count is displayed
  on screen, not buried.
- **If it does not fire.** Report the estimate with CI and the observed MDE. The required phrasing is
  *"underpowered to detect contamination below N points; observed difference D [CI]."* The phrase
  *"no evidence of contamination"* is forbidden in every artifact — CI enforces it by the same grep
  machinery ADR-C already specifies.
- **Known confound, stated up front.** `baseline_p` is an imperfect proxy for subjective obviousness, so
  a genuinely obvious pick the baseline under-rates produces fast entry *and* rank-1 selection with no
  contamination present. This biases the test toward flagging a problem — conservative for a screen,
  which is why this is a screen and not an estimate. It can flag; it cannot quantify.

### PR-006 — Arm contrast on top-5 coverage (confirmatory, and known underpowered)

- **Question.** Does per-mock coverage of the hazard model's `predicted_top5` differ between sighted
  and blind arms?
- **Estimand.** `Δ_cov` = mean per-mock coverage (sighted) − (blind). **Resampling unit: the mock.**
  BCa bootstrap over mocks, 9,999 replicates, seed recorded, 90% CI (the concern is one-sided).
- **Tolerance `τ = 0.03`,** frozen here: the largest bias that could be ignored without invalidating
  the design's own stated half-width, i.e. half of it.
- **Decision rule, three branches, all pre-committed:**
  - **Fires (contamination demonstrated)** iff the 90% CI lower bound > 0 **and** the point estimate >
    τ. Consequence: headline absolute calibration = blind arm only; the sighted arm is reported
    separately and labelled "shortcut-assisted," never pooled into the headline.
  - **Bounds (contamination below tolerance)** iff the 90% CI upper bound < τ. Consequence: pooling
    permitted for absolute calibration.
  - **Inconclusive — pre-declared as the expected outcome, given the power table above.** Consequence,
    and this is the clause that matters most in this ADR: (i) the headline absolute calibration number
    is reported from the **blind arm alone**, with its wider interval; (ii) a pooled number may be
    shown but must carry `Δ_cov` and its CI *adjacent to it*, not in a footnote; (iii) the inconclusive
    branch is **never** described as reassurance. Pre-committing the inconclusive consequence is the
    entire point of registering a test we already know is underpowered: it makes the null
    unquotable-as-clean before anyone has an incentive to quote it that way.
- **Power note (required, on the record now).** MDE at n=30, k=10 is `1.085 σ`, and `σ` is unobserved.
  See the table above. Reaching MDE = τ requires ~90–350 mocks. This test cannot succeed and is
  registered so that its failure is interpreted correctly rather than favourably.

### PR-007 — Arm contrast on the headline calibration statistic (confirmatory, same structure)

Identical design to PR-006 with `Δ_cal` = mean per-mock calibration-slope deviation from 1 (primary)
and per-mock Brier (secondary). `τ_cal` = the Brier / slope value corresponding to a 3-point shift in
the largest bucket, computed and **frozen in the registration before any run**. Same three-branch rule,
same forbidden phrasing, same power note.

### Exploratory registrations (mandatory, free, and not in the FDR denominator)

`shortcut_slot` distribution · `keystrokes` and `dwell_ms` distributions by mode · per-mock coverage
trajectory against `session_index` · counterfactual coverage of `predicted_top5` versus
`shortlist_shown`. Point estimates and plots only. No p-value, no CI, no threshold comparison — per
ADR-C, CI rejects artifacts from exploratory runs containing `p_value` / `ci_lower` / `ci_upper` /
`significant`.

### Blinded nuisance amendments — a small extension to ADR-C

`σ` and `ρ` must be re-estimated from real data after ~6 mocks, and every power and interval statement
here depends on them. Under ADR-C as written, amending a registration after touching data sets
`data_seen: true` and irreversibly demotes it to exploratory — which would punish the correct act of
replacing an assumed variance with a measured one.

ADR-C's own falsification section anticipates this and proposes the right pattern. Adopt the analogue:
a `blinded_nuisance: true` amendment qualifier, defined **mechanically, not by judgment**: the
amendment may use only statistics that are **invariant to permutation of the contrast label**. Pooled
variance and intra-cluster correlation qualify; anything computed on the arm difference does not.
Permutation-invariance is checkable in code, so this adds no human discretion — which is the property
that makes the `data_seen` rule work and must not be eroded.

### Structural rules — no inference, enforced by tests

| Rule | Enforcement | On violation |
|---|---|---|
| Matcher independence (D-4) | static import test on the matcher module | affected picks excluded from calibration, not corrected |
| `shortlist_source = board_rank_frozen` for sighted entry (D-1) | schema CHECK + UI test | build fails |
| No probabilities rendered at entry (D-1) | frontend assertion in the fidelity harness | build fails |
| Arm assigned before first pick (D-2) | storage-layer check `arm_assigned_at < min(entered_at)` | insert rejected |
| Write-once on all `predicted_*`, `baseline_*`, `shortlist_shown` | no update path exists (per thread 025) | insert rejected |
| Mock-level resampling on every reported interval | analysis-entrypoint assertion | run refused |

### Deferred trigger — the one thing that may become a founder call

D-1 costs shortcut coverage: the hazard model's top five should cover more picks than board rank's,
otherwise the model has no value. The cost is measurable retrospectively because `predicted_top5` is
stored even when not displayed.

**Pre-committed trigger.** After 6 mocks, compute counterfactual coverage of `predicted_top5` versus
realised coverage of `shortlist_shown`. If the gap exceeds **10 percentage points**, raise a
`decisions-needed.md` entry with the measured minutes-per-mock cost attached. That, and only that, is a
genuine taste question — measured founder time against measured rigour. It is not a question now,
because there is no number yet, and escalating it now would be asking the founder to arbitrate between
two quantities neither of us can state.

## What remains uncontrolled — read this before quoting any calibration number

1. **No ground truth, and the blind arm does not create one.** Blind logging is uncontaminated by the
   *model*; it is not error-free. A mistyped name still resolves to a real player. That error is
   non-differential and therefore attenuating — it biases toward chance, against the claim — but its
   rate is unmeasured and unmeasurable from this data.
2. **The logger is not blind to the arm.** The founder knows which mocks are blind and why. Expectancy
   effects — more care on blind mocks, or drawing blind mocks from easier sources — are uncontrolled and
   unmeasurable with a single rater. Irreducible in a one-person study. Naming it is the whole of what
   can be done.
3. **Arm assignment is randomised; mock *selection* is not.** Which site, which lobby, which time of
   day, which config are all chosen after the arm is known.
4. **Residual contamination toward board rank.** Removing the hazard model from the display does not
   remove the correlation between board rank and hazard output. The **absolute** calibration number
   remains contaminated to the extent the two agree. Only the **increment over baseline** is protected
   — and that protection runs in the conservative direction. The product's headline claim ("when it
   says 33%, it happens a third of the time") is the absolute number, so this is the largest surviving
   threat in the design and the blind arm is the only thing standing against it.
5. **All power arithmetic is conditional on an assumed `σ`** that has never been observed, across a
   range where the required n varies 6-fold.
6. **`ρ` is assumed too,** and the shipped evidence ladder currently ignores it (D-5).
7. **PR-005 conflates contamination with obviousness-residual.** A flag is not a measurement.
8. **Fatigue and learning are balanced against arm but not against model version.** `model_artifact_hash`
   changes whenever the model does, and blocking cannot balance something that changes on its own
   schedule.
9. **Config fragility.** Under D-015's per-configuration default, a scoring change resets the count —
   and resets the blind arm with it. At `k = 10` of 30, the blind arm is the most fragile part of the
   programme; losing it loses the only uncontaminated estimate. Freeze scoring for the duration of the
   collection programme, or accept restarting it.
10. **Nothing here addresses whether 30 mocks of *any* purity suffice.** That is D-015's question and it
    is not reopened by this ADR.

## Consequences

- Entry stays one keystroke. The loop between the estimator and its own data collection is cut, and
  the property design praised — better calibration making logging cheaper — is deliberately given up,
  because it is the same arrow as the defect.
- The headline absolute calibration number becomes **wider and honest** (blind arm, ~±14) rather than
  narrower and contaminated (~±6, before the design-effect correction that makes even that ±8–10).
- The relative claims — hazard vs baseline, and the binding `delta` rule in D-004 — become robust to
  contamination in the conservative direction, on all 30 mocks.
- One contamination path that would have been shipped invisibly (D-4, matcher tie-breaking on model
  output) is closed before the first pick.
- The comparison thread 034 proposed is refused, in writing, rather than run in a hedged form. It would
  have produced a large significant number with no identifying variation.
- Cost: ~30 extra minutes of founder time across the programme, ~14 new columns, one fewer number on
  the entry screen, and the on-screen evidence ladder must be recomputed wider.

## What would falsify this

- **Falsifies D-1:** the board-rank shortlist covers materially fewer picks (>10 pts) than the hazard
  shortlist, making entry slow enough that mocks stop getting logged. Then the trigger above fires and
  the trade goes to the founder with a measured number. Data volume beats purity if purity costs the
  data.
- **Falsifies D-2:** `k = 10` blind mocks turn out to produce an interval so wide it supports no claim
  at all — in which case the blind arm should be *larger*, not abandoned, and the sighted arm's only
  remaining role is the relative contrast.
- **Falsifies the "no ground truth" premise:** a mock platform exports a machine-readable results file.
  Then substitution becomes directly measurable against an independent record, PR-006 and PR-007 are
  superseded by a direct estimate, and this ADR's central constraint dissolves. Worth checking before
  building — it is the single highest-leverage fact in the whole problem.
- **Falsifies the separate-family justification:** an instrument test result is used to argue a
  substantive claim. Then the families were not independent and the denominators must merge.
- **Falsifies `blinded_nuisance`:** a permutation-invariant statistic is found that nonetheless leaks
  the contrast. Then tighten the invariance definition — do **not** add a human-judgment override,
  which would restore exactly the discretion the `data_seen` rule exists to remove.
