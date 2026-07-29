---
id: PR-004
test_registry_id: ADR-E-§9
family: F-BOTTOMUP-CORE
mode: confirmatory
question: Does the frozen V5 bottom-up projection order draft-relevant veterans better,
  out of sample, than ranking them by prior-season fantasy points — by a margin large enough
  to change one real draft decision — at QB, RB, WR and TE independently?
metric: Mean paired Kendall tau-b difference over embargoed-LOSO folds, dtau_f =
  tau_b(model_f, actual_f) - tau_b(B1_f, actual_f), computed within position on the fold's
  pre-season-frozen universe; point estimate is the mean over folds. Co-primary gate for
  projected_points adoption only, ADR-E §9(i), season-points R-squared: dR2_f = R2(model_f) -
  R2(B1_f) against the TEST fold's own mean. Artefact guard, ADR-E §9(ii): the same statistic
  recomputed on points per game played. Uncertainty on every reported figure is a season-level
  bootstrap 95 percent CI over the fold-level paired differences.
threshold: ADOPT-OVERLAY at a position iff ALL SIX hold — (a) mean dtau_b >= +0.04;
  (b) dtau_f > 0 in >= 75 percent of folds (>= 10 of 13 usage-arm folds); (c) the season-level
  bootstrap 95 percent percentile CI on mean dtau_b excludes 0 AND the bootstrap two-sided
  p survives Benjamini-Hochberg at alpha=0.05 across the declared m=4; (d) the ppg variant
  agrees in sign; (e) no ADR-E §8 audit trigger outstanding; (f) cross-process determinism
  verified from the recorded seed. ADOPT-PROJECTED-POINTS additionally requires mean dR2 > 0
  with >= 10 of 13 folds positive. STOP if neither RB nor WR reaches ADOPT-OVERLAY.
data_scope: {seasons: [2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013,
  2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024], evaluation_folds_usage_arm:
  [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
  holdout_unsealed: false}
frozen: {model: V5, model_commit: experiments/bottomup as carried out of session 4,
  registered_at: 2026-07-29, registered_by: strategist, seed: 20260729, bootstrap_draws: 10000,
  content_hash: PENDING-FREEZE}
secondary: Long arm (box-score-only features, folds 2002-2024) reported as point estimates and
  fold-sign counts ONLY — no p-value, no CI, outside the FDR denominator, and pre-committed as
  unable to promote a position that failed the usage arm. Consensus ECR (2021-2024, n=4,
  veterans-only common universe) likewise descriptive-only, same restriction, per ADR-B.
resampling_unit: season
power_note: 13 usage-arm folds. The season-level bootstrap is the mandated instrument
  (guardrails §7); the exact sign test is reported as a disclosed diagnostic and may never
  rescue a failed criterion, only caveat a passed one.
amendments:
---

# PR-004 — F-BOTTOMUP-CORE: the confirmatory bottom-up run

**Registered 2026-07-29 by `strategist`, before any run, before any V5 re-execution.**
Nothing in `experiments/bottomup/` may be re-run against this id until this file is committed
and its `content_hash` frozen (procedure in §9).

This is the run ADR-E §9 and `docs/reviews/fable-bottomup-next-tests-2026-07-28.md` §1 (F-A)
both name as the falsification event for bottom-up as a 2026 product input. It has never been
run. Every number quoted in `experiments/bottomup/REPORT.md` is exploratory: walk-forward
expanding window rather than embargoed LOSO, no BH correction, no fixed family denominator,
and — the point the founder's brief makes correctly — **no confidence interval has ever been
computed under a pre-registered rule that could fail.**

---

## 1. Premise correction, stated before the protocol

The brief that commissioned this registration says *"the baseline that matters is consensus,
not last-season rank."* **That is right in principle and unachievable here, and this
registration says so rather than producing a hedged version of it.**

| Baseline | Status for this test | Why |
|---|---|---|
| **B1 — prior-season fantasy points, ranked** | **Confirmatory.** The rule above is written against it. | 13 usage folds / 23 long-arm folds. Enough seasons for a season-level bootstrap that can actually exclude zero. |
| **B3 — volume-only** | Reported, descriptive | Already measured; diagnostic for *what* is doing the work. |
| **Consensus ECR / market ADP** | **Descriptive only. Cannot be confirmatory.** | Coverage is 2021–2025; 2025 is the sealed holdout, leaving **n=4 seasons**. The exact two-sided sign-test floor at n=4 is **p=0.125** — unreachable at alpha=0.05 *before* any correction. This is the same wall PR-003 hit and reported. Additionally the comparison is only definable on a veterans-only common universe, which deletes exactly the rows where consensus has an information advantage. |

**What that weakens — plainly.** `CLAUDE.md` §6.5 makes the consensus comparison *the headline
result*. We cannot produce that headline. Therefore **no outcome of PR-004 can be reported as
an edge, as beating the market, or as evidence that our rankings are better than consensus.**
The maximum claim a full pass licenses is:

> *"Out of sample (embargoed LOSO, 13 folds, 2012–2024), the bottom-up projection orders
> draft-relevant veteran <position>s better than ranking them by prior-season fantasy points,
> dtau_b = [value] [CI], under this league's scoring."*

And the descriptive evidence already on file points the other way on the question that
matters: consensus beats the V5 model at **every** position (RB −0.110, QB −0.241, WR −0.046,
TE −0.016; `REPORT.md` session-3 appendix). A PASS here therefore licenses a **labelled,
non-binding overlay at the passing position** and nothing more. It does not license replacing
the consensus-anchored board, and `CLAUDE.md` §4's never-blend rule still forbids averaging
the two.

I considered refusing this test outright on the §6.5 grounds and decided against it: an
accuracy claim against a stated naive baseline, scope-limited as above, is defensible with the
data in hand. What would be indefensible is running it and calling the result an edge. The
scope limit is registered here so that it cannot be relaxed after the number is seen.

## 2. What is frozen, and why V5 is frozen *unconditionally*

**Frozen candidate: V5 exactly as carried out of session 4** — the two-stage S1×S2 pipeline
plus the self-excluded vacated/arrived-opportunity feature group. No re-tuning, no `k`-grid
change, no cap change, no feature added or removed.

**Deviation from F-A §2, recorded with reasoning.** F-A ordered N-1 (direct-projection
collapse control) and N-2 (rookie-universe sensitivity) *before* the freeze, so their results
could inform what gets frozen. That ordering is unsafe under this project's own convention:
choosing the confirmatory candidate after seeing N-1/N-2 results is a `data_seen` selection
step, and amending PR-004 on the back of it would irreversibly demote it to exploratory
(ADR-C, `record_amendment`). So the order is inverted: **PR-004 runs first on the already-
frozen carry candidate.** N-1 and N-2 remain worth running as *exploratory* registrations
afterwards; neither may amend this file, and neither may change this verdict. If N-1 later
shows the two-stage split is decoration, that is a new confirmatory id and a new increment to
`m`, not a rescue of a failed PR-004.

**Deviation from F-A §2.3 on QB, recorded with reasoning.** F-A said QB is not run
confirmatorily. This registration runs it, keeping ADR-E §9's declared **m=4**. Dropping the
one position we already know loses would shrink the BH denominator by exactly the test we
expect to fail — the cherry-picking pattern `src/preregistration.py`'s whole docstring exists
to prevent. Including it is strictly more conservative and costs nothing.

## 3. Protocol

**Scheme.** Embargoed leave-one-season-out, ADR-E §3.1 verbatim: when season N is the test
fold, seasons **N−1 and N+1 are excluded from training**. Everything fitted — ridge
coefficients, S2 shrinkage constants `k`, standardisation means, any break detection — is
fitted **inside the training fold**, never hoisted. Break detection for fold N uses seasons
≤ N−2 only (ADR-E §5).

**Universe.** Frozen per fold using pre-season information only: players with a prior-season
positional finish inside draft-relevant depth. Rookies excluded (the registered prototype
universe). Rookie inclusion is N-2's question and is **out of scope here** — the headline claim
is scoped to veterans regardless of what N-2 later shows, per F-A §2.2's pre-committed rule.
No filtering on games played, on "qualified" status, or on any post-season-N quantity.

**Positions.** QB, RB, WR, TE — four confirmatory tests, one per position, m=4.

**Arms.** Usage arm (folds 2012–2024, n=13) is the confirmatory arm. Long arm (2002–2024) is
reported per `secondary` above: point estimates and fold-sign counts only, no CI, no p-value,
outside the denominator, and pre-committed as unable to promote a failing position.

**Uncertainty.** Season-level bootstrap over the 13 fold-level paired differences, B=10,000,
percentile method, seed **20260729** (a literal integer — never builtin `hash()`, guardrails
§11). Two-sided bootstrap p = 2 × min(prop(replicate mean ≤ 0), prop(≥ 0)), with the standard
(k+1)/(B+1) correction and a floor of 1/(B+1). If the bootstrap distribution is degenerate,
surface the existing `degenerate=True` flag rather than a decimal.

**Multiple comparisons.** BH at alpha=0.05 **within F-BOTTOMUP-CORE, across the declared
m=4**, applied to the four bootstrap p-values (one per position, from the primary dtau_b).
The dR2 and ppg criteria are **conjunctive gates, not additional tests** — a conjunction can
only reduce rejections, so it does not enter the denominator. Descriptive arms (long arm,
consensus, B3) never enter it. Every executed run, including a failed or abandoned one, is
appended to `test_run_log.jsonl`.

**Holdout.** 2025 stays sealed. `data_scope.holdout_unsealed: false`. **This registration does
not authorise an unseal and no agent may perform one under it.** Unsealing is irreversible,
permanently closes the family (`FAMILY_STATUS_CLOSED_UNSEALED`), and requires a signed
`UNSEAL_LOG.md` entry with a **named human approver** — a founder decision, escalated, never
made by an agent mid-run.

**Structural enforcement, hard prerequisite.** Every season read in `experiments/bottomup/`
must route through `holdout.load_season_registered(year, "PR-004")` before the run. The
registration's value as a confirmatory instrument is the structural refusal, not the promise.
This is F-A's "H3" item and it is one call site.

## 4. The decision rule (this is the point of the document)

Per position, independently. All criteria are evaluated **once**, on the numbers the run
produces, with no re-run permitted at a different floor, universe, fold scheme, or seed.

**ADOPT-OVERLAY(pos)** iff all six:

| | Criterion |
|---|---|
| (a) | mean dtau_b (model − B1) over the 13 usage folds **>= +0.04** |
| (b) | dtau_f > 0 in **>= 10 of 13** folds (ADR-E §9's 75 percent rule) |
| (c) | season-level bootstrap 95 percent CI on mean dtau_b **excludes 0**, AND its two-sided bootstrap p **survives BH** at alpha=0.05 across m=4 |
| (d) | the points-per-game-played variant agrees in **sign** (ADR-E §9(ii)) |
| (e) | **no ADR-E §8 audit trigger outstanding** — in particular any season-points R² > 0.40 halts reporting and escalates to the founder as suspected leakage before any number leaves the run |
| (f) | cross-process determinism: two runs in **separate processes** from seed 20260729 produce byte-identical output (guardrails §11) |

**ADOPT-PROJECTED-POINTS(pos)** = ADOPT-OVERLAY(pos) AND mean dR2 (season points, vs B1) > 0
with >= 10 of 13 folds positive. This is the stricter decision because it is the one ADR-E §9
actually governs — replacing the board's `projected_points` source. TE is predicted to fail it
outright (season-points R² −0.85 exploratory).

**STOP — the stopping condition, committed in advance:**

> **If neither RB nor WR reaches ADOPT-OVERLAY, bottom-up is dead as a 2026 product input.**
> The 2026 board ships consensus-only at every position, with no bottom-up overlay. No further
> bottom-up configuration is run before the 2026 draft. `F-BOTTOMUP-CORE` is set to `closed`.
> The finding is written in the form ADR-E §9 already pre-committed: *"a bottom-up projection
> built from usage features is not measurably more accurate out-of-sample than the existing
> rank-derived curve on N seasons."* Only P-2026 (the free prospective registration) continues.

Three exits are closed in advance, by name, because each is the argument someone will reach
for at 11pm on 2026-08-21:

1. **"It clears if we drop the +0.04 floor."** The floor is not fitted to anything. It comes
   from decision-relevance arithmetic that predates this registration: over a ~48-player
   draft-relevant universe (1,128 pairs), dtau = +0.04 corrects roughly 23 pairwise
   inversions — about **one improved pick per draft**. Below that the overlay cannot change a
   real decision, and shipping it would be shipping a number, not a benefit. Note that this
   floor sits **above WR's exploratory point estimate under V5 (+0.036)**. WR is therefore
   predicted to FAIL on materiality even if it clears significance, and that is deliberate:
   a threshold set beneath every estimate we have already seen is not a threshold.
2. **"The long arm / the consensus arm / TE's VBD-capture number looks better."** All are
   pre-declared descriptive, cannot carry a CI or a p-value (`validate_exploratory_artifact`
   enforces this), and cannot promote a position.
3. **"Re-run it with the rookie-inclusive universe / un-embargoed folds / a different seed."**
   Each is a different test and requires a new PR id, which increments `m` and re-triggers BH
   across the whole family — every prior adjusted p in F-BOTTOMUP-CORE must then be recomputed
   and republished.

**Auxiliary stops, same outcome (F-A §1, restated so they bind here):** the gated run has not
completed by **2026-08-22**; or the 20-config LOSO budget is exhausted (8 spent; this is the
9th).

## 5. Predictions, registered before the run

The calibration prior is applied as a rule, not a mood: four of five registered prediction
sets across sessions 3–4 were materially wrong, **every miss over-crediting a situation
story**. V5's carry advantage over V1 comes precisely from a situation feature family. So
these predictions are deliberately pessimistic relative to the exploratory table.

| Position | Prediction |
|---|---|
| **RB** | The only genuine candidate. Exploratory V5 +0.057 [+0.018, +0.095], 10/13. **Predicted: clears (b) and (c), ~55/45 on (a).** The +0.04 floor and the LOSO-vs-walk-forward switch are both expected to shave the estimate; embargo removes two folds of training data from every fold. |
| **WR** | **Predicted: FAILS (a).** V5 point estimate +0.036 is below the floor. Tightest CI of any position, so it may well clear (c) and still stop — which is the correct behaviour, not a bug in the rule. |
| **TE** | **Predicted: fails.** Either (b) (8/13 exploratory) or (d)/the dR2 gate (season R² −0.85). |
| **QB** | **Predicted: fails, hard and negatively.** Six configurations already failed. Run only to keep the denominator honest. |
| **Overall** | **Modal outcome is STOP.** I expect at most RB to clear, and I would not be surprised by a clean sweep of failures. Under the calibration prior, the exploratory table should be read as an upper bound. |

Anyone reading a PASS should first read this table and note that it predicted otherwise.

## 6. What would falsify this — and what would falsify the registration itself

**What falsifies the hypothesis:** any position failing any one of (a)–(f). Concretely, the
most likely falsifiers, in order: the mean dtau_b landing in (0, +0.04) — real but too small
to act on; fold-positivity dropping below 10/13 once the embargo removes adjacent-season
training data; the bootstrap CI crossing zero at RB where the exploratory lower bound was
already +0.018 under a *less* conservative fold scheme; the ppg variant flipping sign at TE.

**What falsifies the whole registration, i.e. would make even a PASS uninterpretable, stated
because it is the paragraph most likely to be skipped:**

- **Selection contamination, the honest limitation.** V5 was chosen from eight configurations
  evaluated on **these same folds, 2012–2024**. PR-004 therefore does *not* measure V5 against
  data unseen by the selection process. It measures, correctly and for the first time, what
  the effect looks like under a pre-registered rule with an honest CI, a fixed denominator,
  the embargo, and a threshold that could fail. **It cannot establish out-of-sample skill for
  the V5 configuration choice.** A PASS must be reported with this sentence attached. The only
  instruments that could establish that are the sealed 2025 unseal (n=1, one shot, founder
  approval, not authorised here) and P-2026 (n=1, prospective, cannot leak). If this caveat is
  dropped from any downstream summary, the summary is wrong.
- **An ADR-E §8 audit trigger firing** — a season-points R² above 0.40 makes every number in
  the run suspect, not just that cell. Halt, audit in ADR-E §8's order (target contamination,
  cutoff violation, fold contamination first), escalate per `CLAUDE.md` §8.
- **Determinism failing** — if two processes disagree, both numbers are void, per ADR-028.
- **The embargo proving inert or the reverse** — report both embargoed and un-embargoed LOSO.
  Un-embargoed R² exceeding embargoed by more than 0.03 at any position is a leakage signal:
  audit before reporting either number (ADR-E §3.1).
- **Universe drift** — if the frozen universe for any fold turns out to have been filtered on
  a post-season-N quantity, the run is void, not caveated. Guardrails §2.

---

## 7. Reporting

One results section appended to this file (not a new document), stating for every position:
mean dtau_b with season-level bootstrap 95% CI, folds positive out of 13, raw and BH-adjusted
bootstrap p across m=4, mean dR2 with CI, the ppg-variant sign, the embargoed/un-embargoed
gap, the seed, the determinism check outcome, and the verdict against each of (a)–(f)
individually — not a summary judgement. Descriptive arms in a separate table, visibly marked,
with no p-values or CIs. Then update `status:` to `RUN`, append to `test_run_log.jsonl`
(all four positions, including failures), and set the family `status` per §4.

## 8. Checks applied (guardrails accounting, filled at registration time)

Look-ahead §1: embargoed LOSO, everything fitted in-fold, break detection truncated at N−2,
season reads routed through the prereg gate. Survivorship §2: universe frozen pre-season, no
outcome-conditioned filter, busts retained. Multiple comparisons §3: m=4 fixed before the run,
BH within family, descriptive arms excluded, every run logged. Non-stationarity §4: two arms
of different depth reported; the long arm cannot promote. Baselines §5: B1 confirmatory, B3
and consensus descriptive — the §6.5 gap is stated in §1 above rather than papered over.
Metrics §6: tau-b primary, R² and ppg as gates, the list-vs-roster gap acknowledged (this is a
list metric and licenses no roster claim). Uncertainty §7: season-level bootstrap on every
figure. Reproducibility §11: integer seed 20260729, cross-process determinism is criterion (f).

## 9. Freeze procedure (do this before the run, not after)

`frozen.content_hash` currently reads `PENDING-FREEZE` because the registering agent has no
shell. `compute_content_hash()` redacts the `content_hash` value before hashing, so writing
the real hash in afterwards does not change it. Backend's **first** action, before any model
code runs:

1. `python -c "import sys; sys.path.insert(0,'src'); import preregistration as p; from pathlib import Path; print(p.compute_content_hash(Path('docs/preregistration/PR-004-bottomup-core-confirmatory.md')))"`
2. Replace `PENDING-FREEZE` with that value. Commit. That commit is the freeze.
3. `p.check_registration("PR-004")` must return `[]`. If it does not, stop and reply on the
   thread — do not run.
4. Only then execute. Any edit to this file after step 2 without an `amendments:` entry is
   detectable and voids the registration.

## 10. Exactly what Backend must run

Ordered. Do not reorder, do not skip, do not substitute. If any step is impossible as written,
stop and reply on the thread — do **not** run a modified version.

1. **Freeze.** §9 steps 1–3. `check_registration("PR-004")` returns `[]`.
2. **Wire the gate.** Route every season read in `experiments/bottomup/data.py` through
   `holdout.load_season_registered(year, "PR-004")`. Add one test asserting that a read of
   2025 under `PR-004` raises `HoldoutViolation`. This is the H3 item; it is a prerequisite,
   not a follow-up.
3. **Switch the fold scheme** from the prototype's walk-forward expanding window to
   **embargoed LOSO** (ADR-E §3.1): test fold N trains on all in-scope seasons except
   {N−1, N, N+1}. Usage arm folds 2012–2024. Assert per fold that `max(season touched)` in
   training ≤ N−2 and that N+1 is absent — an assertion, not an inspection (guardrails §1).
4. **Run V5 unmodified**, both arms, four positions, seed `20260729`, `B=10000` percentile
   bootstrap over fold-level paired differences. Compute per position: mean dtau_b vs B1,
   folds positive/13, bootstrap 95% CI, two-sided bootstrap p; mean dR2 (season points, vs the
   test fold's own mean) with folds positive; the ppg-variant sign; B3 and consensus arms as
   descriptive point estimates only.
5. **Also run un-embargoed LOSO** on the same folds and report the R² gap per position
   (ADR-E §3.1 diagnostic). Gap > 0.03 at any position ⇒ halt and audit before reporting
   anything.
6. **BH** the four primary bootstrap p-values with
   `benjamini_hochberg(p_values, alpha=0.05, n_total=4)`. Not `correct_against_full_log` — the
   denominator for this family is the manifest's `m=4`, fixed at
   `docs/preregistration/families/F-BOTTOMUP-CORE.yaml`.
7. **Determinism.** Re-run step 4 in a **separate process** from the same seed; diff the
   output byte-for-byte. Same-process re-runs do not count (ADR-028).
8. **Audit gate.** If any season-points R² > 0.40, stop, run ADR-E §8's audit in its stated
   order, and escalate to the founder before any number is reported anywhere.
9. **Report** per §7 into this file, set `status: RUN`, append all four positions to
   `test_run_log.jsonl` (including failures), set the family `status` per §4, and reply on the
   thread with the verdict per position against criteria (a)–(f) individually.
10. **Do not unseal 2025.** Not under any result. Not "just to check."
