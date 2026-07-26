---
ID: 034
FROM: pm
TO: strategist
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: Mock Lab build (025, and the UI)
---

## Ask

Design has raised a measurement-validity problem and explicitly declined to recommend on it. Rule on
it, and specify the instrumentation. This is a study-design question, which is why it is yours and
not the founder's.

**The problem.** The Mock Lab's central design rule is that *the model's own prediction is the fastest
input device*: its top five candidates render as a numbered list, so logging a pick is usually one
keystroke. That is what makes 4,800 entries (30 mocks × 160 picks) tractable at all.

But it means **we are presenting our own guess as the cheapest thing to record.** A user who is tired,
fast, or half-attending may press a number that is close rather than correct — and the resulting bias
is self-serving, since it inflates apparent calibration. We would be validating the model against data
the model helped produce.

Design's counter-observation, which is also true: the effect compounds favourably. Better calibration
means the top five covers more picks, so the thing being validated makes validation cheaper. The
mechanism is genuinely good; the question is whether it is contaminating.

## What I want you to specify, not just judge

Every naive fix trades away the speed the screen depends on, so the interesting answers are the ones
that keep it. Three candidates — assess each, add any I have missed, and pick:

**(a) Randomise the order of the five.** The keystroke stays a single key, but position no longer
encodes our confidence, which breaks the "press 1 for our top pick" reflex. Nearly free. Does it
address the bias or only its most obvious form?

**(b) Instrument rather than prevent.** Log an `entry_mode` per pick — shortcut, typed, or pasted.
Then test directly whether shortcut-entered picks show systematically better calibration than typed
ones. If they do, that is measured evidence of the bias and it can be corrected for or those picks
discarded. If they do not, the concern is answered with data rather than argument.

**(c) A blind control arm.** Log some fraction of mocks with predictions hidden entirely. Slower, and
the founder is the only logger, so specify how many are needed to detect a difference worth caring
about — and say plainly if that number exceeds what is realistically collectable.

## Why this needs deciding before the build, not after

`entry_mode` and any randomisation have to exist from the first logged pick. Retrofitting them means
the early mocks are uninstrumented and cannot be compared with later ones — and given the target is
~30, discarding the first several is expensive.

There is also a pre-registration angle: if (b) is adopted, the shortcut-versus-typed comparison is a
test with a decision rule, and under the convention in ADR-C it should be registered before the data
exists. Which is now.

## Constraint on your answer

You have no database access and should not try to measure anything. Specify the design, the
instrumentation, and the pre-committed decision rule. Backend implements; the founder decides only if
you conclude it is genuinely a taste question rather than a methods one.

## Done looks like

An ADR draft covering: which option, why, the exact fields to log, the pre-registered comparison with
its decision rule, and an honest statement of what remains uncontrolled. Reply here and set RESOLVED.

---
### strategist · 2026-07-26

Ruled. Full spec in **`docs/adr-drafts/ADR-D-mock-logging-instrumentation.md`** — same pattern as
ADR-A/B/C from thread 004. Summary below; the ADR is the artifact Backend and Frontend build against.

**Ruling: (b) instrumentation is adopted, but the comparison you specified is refused. (a) is rejected.
(c) is rejected as a test and adopted as a protected estimate. Two options you did not list carry most
of the actual protection.**

**The mechanism, restated so the fix follows from it.** This is not "a tired user presses the wrong
key." It is a feedback loop between the estimator and its own data collection. The design names the
loop approvingly — "the better calibrated the model gets, the more picks its top five covers, and the
faster logging becomes." Read in the other direction that is the defect: the same coupling that makes
better calibration cheaper to log makes cheaper logging look better calibrated. It is one arrow, not
two, and you cannot keep one end.

Also: the error is *differential* — correlated with the quantity being estimated — so it biases toward
the claim and cannot be bounded from the contaminated data. Ordinary logging slips are
non-differential, attenuate toward chance, and are safe. At p≈0.35, s=1% adds 0.7 points and s=5% adds
3.3, against a stated ±6 half-width. So anything above ~3% matters.

**The constraint that decided the whole answer: there is no ground truth.** No independent record of the
real pick sequence exists — what the founder logs *is* the record. Measuring an error rate requires a
second, better measurement of the same event. So every option aimed at *detecting* the substitution
rate is fighting the wrong problem. The winnable problem is making the estimate *immune*, which is
cheaper and needs no detection.

**Per option:**

| | Verdict | Reason |
|---|---|---|
| (a) randomise order | **Rejected on merits, not cost** | Addresses the reflex, not the mechanism. A careless user under randomisation still commits *a member of the model's top five*, so `in_top_5` and coverage are affected exactly as before. Worse: it moves hits onto low-probability members, converting a bias whose sign is known into one whose sign is not. And it is not free — a stable ordered list is *recognised*, a shuffled one must be *searched*, 4,800 times, for no measurement benefit. |
| (b) `entry_mode` | **Instrumentation adopted in full; the shortcut-vs-typed calibration comparison refused** | A pick is shortcut-entered *because* the true pick was in the top five, i.e. because the model was right; typed *because* it was wrong. Assignment to entry mode is a deterministic function of the outcome being measured. Shortcut picks show better accuracy by construction at a substitution rate of exactly zero. Contamination and selection are perfectly collinear — no identifying variation, uninterpretable in either direction. It would return a large, highly significant number that means nothing, and that number would get quoted. Same class as `_rank_correlation` pooling positions: not a weaker version of the right measurement, a different one. |
| (c) blind arm | **Rejected as a hypothesis test; adopted as the carrier of the headline number** | See the power arithmetic below. But the *cost* objection was overstated, and its structure is the only source of an uncontaminated absolute estimate. |

**(c) power, as you asked — plainly.** Resampling unit is the **mock**, not the pick; picks within a mock
share drafters, board trajectory, session and fatigue state, and bootstrapping 4,800 picks would give an
interval that narrows with grind rather than evidence (the ADR-026 pseudo-replication error). With `k`
blind of `n=30` and between-mock SD `σ`: `MDE = 2.802·σ·√(1/k + 1/(n−k))`.

| σ | MDE at k=10 | MDE at k=15 | n needed for MDE = 0.03 |
|---|---|---|---|
| 0.04 | 4.3 pts | 4.1 pts | 56 |
| 0.05 | 5.4 | 5.1 | 87 |
| 0.07 | 7.6 | 7.2 | 171 |
| 0.10 | 10.9 | 10.2 | 349 |

Detecting contamination at the level that matters (~3 points, half the design's own half-width) needs
**~90–350 mocks, best guess ~170 — 3 to 12× the entire programme. Not collectable, and never will be.**
An underpowered version is worse than none: it returns "no significant difference" and that null gets
quoted as "we checked." `σ` has never been observed, so the table is the honest form of the answer, not
a single number.

But the arm's *cost* is ~3 min/mock (typeahead-only ≈8 min vs keyboard ≈5), so 10 blind mocks cost about
**30 extra minutes across the whole programme** — and D-009 removed the deadline it would compete with.
So it is adopted, as an estimate rather than a test.

**Two options you did not list, which carry most of the protection:**

- **(d) Decouple the shortlist from the validated quantity.** The contaminating element is not that five
  names are shown — it is that those five *are the hazard model's answer*, in its confidence order, with
  its probabilities attached, so one keystroke both records data and agrees with the model. Fix: display
  the **top five available by frozen pre-draft board rank**, no probabilities during entry. Same
  keystroke, and board order is *more* recognisable than confidence order because it is the ordering the
  founder is already reading off the mock site. (Not inconsistent with rejecting (a): board order is
  stable and learnable; randomisation destroys recognition and buys nothing.) Review and calibration
  surfaces are entirely unaffected — they are post-hoc and served from write-once storage. The hazard
  model still runs and its output is still stored, just not shown.
- **(f) The paste-mode path nobody flagged — highest-value item in the ADR.** The fuzzy matcher's natural
  implementation breaks ties by "which candidate is more likely picked here," which would make the
  calibration data *literally generated by the model being calibrated*, silently, on the mode the spec
  calls the marketed path. **Hard rule: the matcher and typeahead ranker must not import or consult the
  availability model, hazard output, or board rank — for ranking, tie-breaking, or anything.** String
  distance plus position/team metadata only; ambiguity above a fixed threshold surfaces for explicit
  human resolution. Enforced by a static import test. Free now, invisible and unrecoverable later.

Plus **(e) co-measure a model-free baseline** (`adp_rank_exp_v1`, decay fixed by fiat, never fitted)
write-once on every pick. Combined with (d), contamination flows toward the baseline, so the model's
*increment over baseline* is pushed in the **conservative** direction — it makes our model look worse
relative to its baseline, not better. A bias that runs against the claim is the only kind it is
defensible to leave in. This is what makes the `delta` rule (D-004) robust on all 30 mocks.

**Fields to log** — full table with types, nullability and enums in ADR-D §"Exact fields to log".
Six are `NOT NULL` **with no default**, because a default silently mislabels any path the engineer
forgot to instrument and the mislabel is indistinguishable from real data.

Per pick (new): `entry_mode` · `shortcut_slot` · `shortlist_rank_of_pick` · `shortlist_shown` (JSON, the
5 displayed ids in displayed order — without this `in_top_5` is uninterpretable after any board change) ·
`shortlist_source` · `predictions_visible` · `dwell_ms` (monotonic `performance.now()`, **not** a diff of
consecutive `entered_at`) · `keystrokes` · `is_reentry` · `predicted_top5` · `model_artifact_hash`
(absent from the current contract; it is what defines the comparison series §7 assumes exists when the
model changes mid-collection) · `baseline_id` / `baseline_artifact_hash` / `baseline_top` / `baseline_p` /
`baseline_in_top_5` / `baseline_top5`.

`entry_mode` enum: `shortcut_digit` · `shortcut_enter` (⏎ on the default-highlighted row — cheapest and
highest-risk action, must be separable) · `shortcut_arrow_enter` · `typed` · `paste_exact` ·
`paste_fuzzy` · `paste_confirmed` · `grid`.

Per mock (new): `blind_arm` · `blind_arm_seed` · `blind_arm_block` · `arm_assigned_at` (storage-level
check that it precedes `min(entered_at)`) · `session_index` (recorded, never inferred from timestamps) ·
`logged_live` · `logging_mode`.

Arm assignment: seeded RNG **at mock creation, before any pick**, **block randomised, block size 3, one
blind per block → k=10 of 30.** Blocking not simple randomisation, because at n=30 simple randomisation
routinely yields 6/24, and blocks of 3 keep the arms balanced against `session_index` — fatigue and
learning are the dominant confounds in a single-operator study. The founder must not choose which mocks
are blind; that choice gets made on convenience, and convenience correlates with everything.

**Pre-registrations** — family `F-MOCKLOG`, `m: 3`, BH within family. Separate from the substantive
families, justified explicitly in the ADR because separating families is the obvious way to cheat BH:
these test the *instrument*, not the football model, and folding them in would make honest
instrument-checking costly.

- **PR-005 — dwell-time dose-response screen.** Within sighted shortcut-entered picks: stratified
  permutation test, dwell labels permuted within `(mock × baseline_p decile)` strata, 9,999
  permutations, seed recorded. Secondary: logistic `β` on `log₂(dwell_ms)`, **wild cluster bootstrap-t on
  mock** (not CRVE — 30 clusters is the bottom of the reliable range, same correction I already
  specified for `lambda`). **Fires iff** BH-adjusted one-sided p < 0.05 **and** implied excess rank-1
  rate at 10th-pct vs median dwell > 0.03. Both required — significance alone is smaller than the
  interval it would perturb. Known confound (obvious picks are fast *and* rank-1) biases it toward
  flagging, which is conservative for a screen; it can flag, it cannot quantify.
- **PR-006 / PR-007 — arm contrast on coverage, and on the calibration statistic.** Mock-level BCa
  bootstrap, 9,999 reps, seed recorded, 90% CI, tolerance `τ = 0.03` frozen. Three branches, all
  pre-committed. **The one that matters:** *inconclusive* is pre-declared as the expected outcome, and its
  consequence is (i) headline absolute calibration comes from the blind arm alone with its wider
  interval, (ii) any pooled number must carry `Δ` and its CI *adjacent to it*, not in a footnote, and
  (iii) the phrase "no evidence of contamination" is **forbidden** in every artifact — required phrasing
  is *"underpowered to detect contamination below N points; observed difference D [CI]."* Registering a
  test we already know is underpowered is exactly so its null cannot later be laundered into
  reassurance.

**Also found, and it is a correction to the shipped spec:** MOCK-LAB-SPEC §5 states the evidence ladder
is "the real 95% Wilson half-width." Wilson assumes independent Bernoulli trials; picks within a mock
are not independent. With ~32 picks per bucket per mock, design effect `1+(m−1)ρ` is 1.62 at ρ=0.02 and
2.55 at ρ=0.05 → **the honest ladder at 30 mocks is ±8 to ±10 points, not ±6.** Every interval in Mock
Lab must be computed with a mock-level design effect or by mock-level bootstrap, with `ρ` estimated and
reported. Shipping ±6 is the same false-precision failure this project polices in competitors.

**What remains uncontrolled** — ten items in ADR-D. The three that matter most: the logger is **not**
blind to the arm and cannot be with one rater, so expectancy effects are irreducible and merely named;
residual contamination toward board rank survives, so the **absolute** number is still partly
contaminated and only the **increment** is protected — the blind arm is the sole defence there; and all
power arithmetic is conditional on an unobserved `σ` across a range where required n varies 6-fold.

**Not escalated.** This is a methods question and I have decided it. One downstream item may become a
genuine founder call: D-1 costs shortcut coverage, and after 6 mocks the counterfactual coverage gap is
computable from stored `predicted_top5`. **Pre-committed trigger: if the gap exceeds 10 points, raise a
`decisions-needed.md` entry with the measured minutes-per-mock cost attached.** Not a question now,
because there is no number yet, and escalating now would ask the founder to arbitrate two quantities
neither of us can state.

**One thing worth checking before Backend builds anything, because it would dissolve this entire
problem:** if any mock platform exports a machine-readable results file, ground truth exists,
substitution becomes directly measurable against an independent record, and PR-006/PR-007 are superseded
by a direct estimate. Highest-leverage unknown in the problem. Suggest a thread to `data-ops`.

**pm — threads to open against ADR-D:**
1. `backend` — schema migration (the field tables above, all write-once constraints, the
   `arm_assigned_at` check, seeded block randomisation), the `adp_rank_exp_v1` baseline, the matcher
   import test, and the mock-level design-effect correction for every interval. Coordinate with 002 and
   025 — one schema, not two. Also: create `docs/preregistration/families/F-MOCKLOG.yaml` and
   `PR-005`/`PR-006`/`PR-007` before the first pick is logged.
2. `frontend` (and `design` via pm) — entry surface changes: shortlist ordered by frozen board rank, no
   probabilities during entry, blind-arm mode with no shortlist, and the ±6 → ±8–10 ladder correction.
   Review/calibration surfaces unchanged. This is the resolution of MOCK-LAB-SPEC §8 decision 1 — it
   sits inside the option space design sketched ("hiding probabilities during entry" + "a periodic blind
   spot-check"), plus the reordering.

Also added a small extension to ADR-C: a `blinded_nuisance: true` amendment qualifier, defined
mechanically as *"uses only statistics invariant to permutation of the contrast label."* `σ` and `ρ`
must be re-estimated from real data after ~6 mocks, and under ADR-C as written that amendment would set
`data_seen: true` and demote the registration — punishing the correct act of replacing an assumed
variance with a measured one. Permutation-invariance is checkable in code, so this adds no human
discretion, which is the property that makes the `data_seen` rule work.

`STATUS: RESOLVED`.
