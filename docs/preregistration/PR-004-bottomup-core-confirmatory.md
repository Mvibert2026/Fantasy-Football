---
id: PR-004
test_registry_id: ADR-E-§9
family: F-BOTTOMUP-CORE
mode: confirmatory
question: Over the full usable historical record — not the four seasons of consensus coverage —
  does the bottom-up box-score projection order draft-relevant veterans better than ranking them
  by prior-season fantasy points, and better than a three-season weighted average, by a margin
  large enough to change one real draft decision, at QB, RB, WR and TE independently?
metric: Mean paired Kendall tau-b difference over embargoed-LOSO folds, dtau_f =
  tau_b(model_f, actual_f) - tau_b(B1_f, actual_f), computed within position on the fold's
  pre-season-frozen universe; point estimate is the mean over folds. Secondary comparator B2
  (three-season equal-weight average of prior fantasy points, ranked). Co-primary gate for
  projected_points adoption only, ADR-E §9(i), season-points R-squared against the TEST fold's
  own mean. Artefact guard, ADR-E §9(ii): the same statistic on points per game played.
  Uncertainty on every reported figure is a season-level bootstrap 95 percent CI over the
  fold-level paired differences.
threshold: ADOPT-OVERLAY at a position iff ALL EIGHT of (a)-(h) in §4 hold — headline bar is
  mean dtau_b vs B1 >= +0.04, positive in >= 75 percent of folds, season-level bootstrap 95
  percent CI excluding 0, bootstrap p surviving Benjamini-Hochberg at alpha=0.05 across the
  declared m=4, sign agreement on points per game, no ADR-E §8 audit trigger, cross-process
  determinism, era-split sign agreement, and mean dtau_b vs B2 > 0. ADOPT-PROJECTED-POINTS
  additionally requires mean dR2 > 0 with >= 75 percent of folds positive. STOP if neither RB
  nor WR reaches ADOPT-OVERLAY.
data_scope: {seasons: [1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
  2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
  evaluation_folds: MEASURED-BY-CENSUS-SEE-SECTION-3, holdout_unsealed: false}
frozen: {model: long-arm box-score configuration as implemented in experiments/bottomup,
  registered_at: 2026-07-29, revised_at: 2026-07-29, registered_by: strategist, seed: 20260729,
  bootstrap_draws: 10000, content_hash: PENDING-FREEZE}
secondary: Consensus ECR (2021-2024, n=4, veterans-only common universe) and the three-way
  bottom-up / consensus / consensus-adjusted-by-bottom-up comparison in section 11 are
  DESCRIPTIVE ONLY — no p-value, no CI, no significance flag, outside the FDR denominator, and
  may never be reported as an edge. Long-arm B3 (volume-only) likewise descriptive.
resampling_unit: season
power_note: Fold count is measured by the section-3 census, not assumed. The registration is
  valid only for n >= 15 folds; below that, STOP without running. At n >= 15 the >= 75 percent
  fold-majority rule is at least as strict as an uncorrected two-sided sign test at
  alpha=0.05, which is why 15 is the floor.
amendments:
---

# PR-004 — F-BOTTOMUP-CORE: the deep-sample confirmatory bottom-up run

**Registered 2026-07-29 by `strategist`. Revised the same day, before freeze, before any run.**

**This is a pre-freeze revision, not an ADR-C amendment.** `content_hash` was never frozen and
no data was seen, so there is nothing to amend and no demotion is triggered. The revision is
recorded here for audit rather than in `amendments:`, which would misrepresent a never-frozen
file as a peeked-at one.

## 0. What the revision changed, and why the founder was right

The first draft let the **weaker question's sample size cap the stronger one.** It registered
the confirmatory test on the 13 usage-arm folds and treated n=4 consensus coverage as the
binding constraint on everything. Two founder corrections, both correct:

1. **"Market ADP is not consensus rankings — people use consensus rankings, not ADP."**
   Accepted without qualification. ADP is realised draft behaviour; consensus is stated expert
   opinion; drafters read the rankings. **The baseline is not swapped to ADP**, not even to buy
   FFC's deeper history. Depth bought by measuring a different quantity is not depth.
2. **"We have 25 years of data to build our bottom-up rankings from, independent of
   consensus."** Correct and structural. Bottom-up needs *player stats* to build and *actual
   finishes* to score. Both go back decades. Consensus history is required for exactly one
   question — did we beat the experts — and that question does not get to cap the others.

So the questions are now separated, with separate fixed denominators:

| Question | Instrument | Power |
|---|---|---|
| **Is bottom-up any good?** | **PR-004, this file.** Deep sample, box-score model, vs B1 and B2. | High — see §3 |
| Is the *shipping* model (V5, usage features) any good? | **PR-005**, family `F-BOTTOMUP-USAGE`, m=4 | n=13, capped by target-data availability |
| Does bottom-up beat the experts? | §11 here. Descriptive only. | n=4, permanently |

## 1. The constraint that actually binds — and it is not consensus

`experiments/bottomup/data.py:60` is the governing line:

```
TARGET_RELIABLE = lambda s: (1999 <= s <= 2002) or (s >= 2009)   # air yards real 2009+ only
```

**Targets are missing 2003–2008 and air yards do not exist before 2009.** The usage features
that `REPORT.md` identifies as the entire source of the model's edge — target share, air yards,
WOPR, and V5's vacated-opportunity group — **cannot be built across the deep record at all.**

This is the material fact the revision surfaces, and it must reach the founder before the run:

> **The deep sample buys power. The deep model is the weak one.** Over 23 box-score folds the
> model is already measured at roughly parity with prior-season rank (RB +0.023, WR +0.010).
> The model that shows a real edge is the shallow one, and it is shallow because of target
> data, not because of consensus. Twenty-five years of stats does not rescue the strong model;
> it gives a powerful test of the weak one.

That trade is not a reason to skip this test — a powerful test of the architecture on the
deepest available sample is exactly what has never been run, and a clean negative is publishable
under ADR-E §9's pre-committed shelving language. It *is* a reason to predict failure (§5) and
to register PR-005 separately so the shipping candidate is not judged by this run's result.

## 2. Baselines — what is achievable, what is not, and the one that turns out to be degenerate

| Baseline (CLAUDE.md §6.5) | Status | Note |
|---|---|---|
| **B1 — prior-season fantasy points, ranked** (§6.5 baseline 2) | **Confirmatory primary comparator** | Available every fold. |
| **B2 — three-season equal-weight average of prior fantasy points, ranked** (§6.5 baseline 3, made concrete) | **Confirmatory gate, criterion (h)** | The heuristic a human actually uses. Distinct from B1. |
| **A replacement-level / positional-tier heuristic** | **Structurally impossible as a separate baseline here** | Subtracting a position's replacement level is a **monotone transform within position**. Kendall tau-b is invariant under monotone transforms, so its tau is *identical* to B1's by construction. Reporting it as a third baseline would be reporting B1 twice. Stated here so it is not later mistaken for an omission. |
| **Consensus ECR** | **Descriptive only, n=4, permanently** | §11. |
| **Market ADP** | **Not used as a consensus substitute** | Founder correction 1. |

**What the consensus limitation weakens — unchanged from the first draft and not relaxed.**
`CLAUDE.md` §6.5 makes the consensus comparison the headline result. We cannot produce that
headline at any n available before 2027. **No outcome of PR-004 may be reported as an edge, as
beating the market, or as evidence our rankings beat consensus.** A full pass licenses exactly
one sentence:

> *"Out of sample (embargoed LOSO, N folds, seasons S–2024), the bottom-up projection orders
> draft-relevant veteran <position>s better than ranking them by prior-season fantasy points
> and better than a three-season average, dtau_b = [value] [CI], under this league's scoring."*

## 3. How many seasons are actually usable — measured, not assumed

**I do not have database access and will not assert a number I cannot verify.** The census below
is a **coverage count, not a look at any effect**, so it may precede the freeze without
demoting this registration; that distinction is the reason it is safe to run first.

**Backend runs this census and reports it on the thread before freezing:**

1. `SELECT season, COUNT(*) FROM player_weekly_stats GROUP BY season ORDER BY season` — earliest
   and latest season, row counts per season.
2. Per season, the non-null fraction, restricted to QB/RB/WR/TE player-weeks, of every field
   `src/scoring.py`'s `LEAGUE` consumes: passing yards / TD / INT, rushing yards / TD,
   receptions, receiving yards / TD, fumbles lost, two-point conversions, return TDs. Report
   **`S_min` = the earliest season where every one of those is present for ≥99% of those
   player-weeks.** Two-point conversions and return TDs are the expected binding fields, not
   receptions — check them explicitly rather than assuming the pbp floor.
3. `L` = the feature lookback the frozen long-arm configuration actually requires, read from
   `experiments/bottomup/model.py`, **not from memory**.
4. Emit the resulting fold list and `n`.

**The fold set, pre-committed as a formula rather than a list:**

> `FOLDS = { s : S_min + L ≤ s ≤ 2024, s ≠ 2025 }`

**Expected answer, stated in advance so the census can contradict me.** Data begins 1999.
`run.py:10` gives the current start as 2002 because **walk-forward** needed ">=2 training
pairs" of warm-up. **Embargoed LOSO does not have a warm-up cost** — fold 2000 trains on
2002–2024, which is ~23 pairs. So I expect the switch to LOSO to *recover* the two or three
folds walk-forward spent, landing near **folds 2000–2024, n≈25**, rather than `REPORT.md`'s 23.
If that holds, the founder's "25 years" is close to exactly right and the current 23 was an
artifact of the fold scheme, not a data limit. If `S_min` is later than 1999 — most likely
because two-point conversions or return TDs are thin early — `n` drops and **the reason must be
named in the reply**, not absorbed silently.

**Pre-committed rule on the census result:** run as written if `n ≥ 15`. **If `n < 15`, STOP and
reply — do not run.** The criteria below are calibrated for a deep sample, and 15 is the point
at which the ≥75% fold rule becomes at least as strict as an uncorrected two-sided sign test at
α=0.05 (at n=15, 12/15 gives sign p≈0.035).

## 4. The decision rule

Per position, independently. Evaluated **once**. No re-run at a different floor, universe, fold
scheme, or seed.

**ADOPT-OVERLAY(pos)** iff all eight:

| | Criterion |
|---|---|
| (a) | mean dtau_b (model − B1) over the census fold set **≥ +0.04** |
| (b) | dtau_f > 0 in **≥ 75%** of folds (ADR-E §9) |
| (c) | season-level bootstrap 95% CI on mean dtau_b **excludes 0**, AND its two-sided bootstrap p **survives BH** at α=0.05 across m=4 |
| (d) | the points-per-game-played variant agrees in **sign** (ADR-E §9(ii)) |
| (e) | **no ADR-E §8 audit trigger outstanding** — any season-points R² > 0.40 halts reporting and escalates to the founder as suspected leakage |
| (f) | cross-process determinism: two runs in **separate processes** from seed 20260729 give byte-identical output |
| (g) | **era-split sign agreement** — split the fold set at its median year; mean dtau_b is positive in **both** halves. Sign reversal in either half is reported as **REGIME-DEPENDENT**, not as clearing |
| (h) | mean dtau_b vs **B2** > 0, with ≥ 60% of folds positive |

**ADOPT-PROJECTED-POINTS(pos)** = ADOPT-OVERLAY(pos) AND mean dR2 (season points vs B1) > 0
with ≥ 75% of folds positive.

Criteria (d), (g), (h) and the dR2 gate are **conjunctions, not additional tests**: a
conjunction can only reduce rejections, so none enters the FDR denominator. The denominator is
`m=4`, fixed at `docs/preregistration/families/F-BOTTOMUP-CORE.yaml`.

**STOP — the stopping condition:**

> **If neither RB nor WR reaches ADOPT-OVERLAY, bottom-up is dead as a 2026 product input.**
> The 2026 board ships consensus-only at every position, no overlay. No further bottom-up
> configuration runs before the 2026 draft except PR-005, which is already registered. Family
> set to `closed`. The finding is written in ADR-E §9's pre-committed shelving language.

### Why the +0.04 floor does **not** move with n

The revision instruction asked me to recompute the materiality floor against the real n. **I am
declining that specific instruction, and this is the reason.** Power and materiality are
different quantities. n governs how reliably an effect of a given size can be detected; it says
nothing about how large an effect must be to matter. The floor comes from decision-relevance
arithmetic that is independent of season count: over a ~48-player draft-relevant universe
(1,128 pairs), dtau = +0.04 corrects ~23 pairwise inversions — about **one improved pick per
draft**. That arithmetic is identical at n=13 and n=25. Moving the floor because the sample got
deeper would be lowering the bar for the same benefit, which is the exact move §4's closed
exits exist to prevent. **+0.04 stands.**

### What *did* move with n: the meaning of the ≥75% rule

The same 75% rule has different stringency at different fold counts, and this is stated in
advance so nobody can later argue the bar was secretly loose or secretly tight:

| n | 75% threshold | Equivalent uncorrected two-sided sign-test p |
|---|---|---|
| 13 (first draft) | 10/13 | ≈ 0.092 — **weaker** than α=0.05 |
| 23 | 18/23 | ≈ 0.011 |
| 25 | 19/25 | ≈ 0.007 — **stricter** than α=0.05 |

ADR-E's declared 75% is kept unchanged (no goalpost movement), and the exact sign-test p is
**reported alongside it** at whatever n the census yields, so the implied stringency is visible.

### Three exits closed by name

1. **"It clears if we drop the +0.04 floor."** See above. The floor is not fitted to anything.
2. **"The descriptive arm / the blend / TE's VBD number looks better."** All pre-declared
   descriptive; `validate_exploratory_artifact` forbids them carrying a CI or p-value; none can
   promote a position.
3. **"Re-run with the usage folds / rookie-inclusive universe / un-embargoed folds / another
   seed."** Each is a different test needing a new PR id, which increments `m` and re-triggers
   BH across the whole family — every prior adjusted p must be recomputed and republished.

## 5. Predictions, registered before the run

Calibration prior applied as a rule: four of five registered prediction sets across sessions
3–4 were materially wrong, **every miss over-crediting a situation story.**

| Position | Long-arm exploratory dtau vs B1 | Prediction |
|---|---|---|
| **RB** | +0.023 [−0.006,+0.050], 15/23 (V5 long arm +0.036 [+0.006,+0.066]) | **Fails (a).** Best of the four; still below +0.04. |
| **WR** | +0.010 [−0.018,+0.034], 15/23 | **Fails (a) and (b).** |
| **TE** | +0.031 [−0.040,+0.103], 11/23 | **Fails (b) and (c).** |
| **QB** | −0.028, 7/23 | **Fails, negatively.** Run only to keep the denominator honest. |
| **Overall** | | **STOP, with higher confidence than the first draft.** |

I expect this run to end the bottom-up program on the deep sample, and I expect PR-005 (usage
folds) to be the only one with a live chance. Anyone reading a PASS should read this table first
and note that it predicted otherwise.

## 6. What would falsify this — including the registration itself

**Falsifies the hypothesis:** any position failing any one of (a)–(h). Most likely, in order:
the mean landing in (0, +0.04) — real but too small to act on; fold-positivity below 75% once
the embargo removes adjacent-season training data; (g) era-split reversal, which the deep sample
makes newly detectable and which 25 seasons of rule and scheme change make genuinely plausible.

**Falsifies the registration — makes even a PASS uninterpretable:**

- **Selection contamination, reduced but not eliminated.** The long-arm configuration was seen
  across eight exploratory configurations on overlapping folds. Deepening the sample does not
  undo that. PR-004 measures, for the first time, what the effect looks like under a
  pre-registered rule with an honest season-level CI, a fixed denominator, the ADR-E embargo,
  and a threshold that can fail. **It cannot establish out-of-sample skill for the
  configuration choice.** Only the sealed 2025 unseal (n=1, one shot, founder approval, not
  authorised here) or P-2026 could. If this sentence is dropped from any downstream summary,
  the summary is wrong.
- **Non-stationarity across 25 seasons.** Criterion (g) exists precisely because a pooled mean
  over 1999–2024 can hide a model that worked under one set of league conditions and not
  another. A pass with a failed (g) is not a pass.
- **An ADR-E §8 audit trigger firing** — season-points R² > 0.40 makes the whole run suspect.
- **Determinism failing** (ADR-028), **universe drift** (any fold's universe filtered on a
  post-season-N quantity ⇒ run is void, not caveated), or **the embargo diagnostic** —
  un-embargoed R² exceeding embargoed by >0.03 at any position is a leakage signal: audit
  before reporting either number (ADR-E §3.1).

## 7. Protocol

Embargoed LOSO, ADR-E §3.1 verbatim: test fold N trains on all in-scope seasons except
{N−1, N, N+1}. Everything fitted — ridge coefficients, S2 shrinkage `k`, standardisation means,
break detection — fitted **inside the training fold**, never hoisted; break detection for fold N
uses seasons ≤ N−2. Universe frozen per fold on pre-season information only, veterans
(prior-season positional finish inside draft-relevant depth), rookies excluded, **no filtering
on games played, "qualified" status, or any post-season-N quantity.** Four positions, m=4.
Season-level bootstrap over fold-level paired differences, B=10,000, percentile, seed
**20260729** (literal integer — never builtin `hash()`, guardrails §11); two-sided bootstrap
p with the (k+1)/(B+1) correction and a 1/(B+1) floor; `degenerate=True` surfaced rather than a
false decimal. BH within family across m=4. **2025 stays sealed** — `holdout_unsealed: false`;
**this registration does not authorise an unseal and no agent may perform one under it.**
Unsealing is irreversible, permanently closes the family, and requires a named human approver in
`UNSEAL_LOG.md`. Every season read routes through
`holdout.load_season_registered(year, "PR-004")` — the structural refusal is the point.

## 8. Reporting

One results section appended to this file. Per position: mean dtau_b vs B1 with season-level
bootstrap 95% CI, folds positive / n, exact sign-test p, raw and BH-adjusted bootstrap p across
m=4, mean dtau_b vs B2, mean dR2 with CI, ppg sign, era-split halves, embargoed/un-embargoed
gap, seed, determinism outcome, and the verdict against **each** of (a)–(h) individually — not a
summary judgement. Descriptive arms in a separate, visibly marked table with no p-values or CIs.
Then `status: RUN`, append all four positions to `test_run_log.jsonl` including failures, and
set the family status per §4.

## 9. Checks applied (guardrails accounting)

Look-ahead §1: embargoed LOSO, in-fold fitting, break detection truncated at N−2, season reads
gated. Survivorship §2: universe frozen pre-season, no outcome-conditioned filter, busts
retained. Multiple comparisons §3: m=4 fixed before the run, BH within family, conjunctive gates
excluded from the denominator by construction, descriptive arms excluded, every run logged.
Non-stationarity §4: criterion (g) era split — the deep sample's main new obligation. Baselines
§5: B1 and B2 confirmatory, the tier heuristic shown degenerate, consensus descriptive with the
§6.5 gap stated rather than papered over. Metrics §6: tau-b primary, R² and ppg as gates, list-
vs-roster gap acknowledged. Uncertainty §7: season-level bootstrap on every figure.
Reproducibility §11: integer seed, cross-process determinism is criterion (f).

## 10. Freeze procedure — before the run, after the census

`frozen.content_hash` reads `PENDING-FREEZE` because the registering agent has no shell.
`compute_content_hash()` redacts the field before hashing, so writing the real value in
afterwards does not change it.

1. Run the §3 census. Reply with `S_min`, `L`, the fold list and `n`. **If `n < 15`, stop here.**
2. Replace `evaluation_folds: MEASURED-BY-CENSUS-SEE-SECTION-3` in `data_scope` with the
   measured list.
3. `python -c "import sys; sys.path.insert(0,'src'); import preregistration as p; from pathlib import Path; print(p.compute_content_hash(Path('docs/preregistration/PR-004-bottomup-core-confirmatory.md')))"`
4. Replace `PENDING-FREEZE` with that value. Commit. **That commit is the freeze.**
5. `p.check_registration("PR-004")` must return `[]`. If not, stop and reply — do not run.
6. Only then execute. Any later edit without an `amendments:` entry is detectable and voids the
   registration.

Steps 1–2 are legitimate pre-freeze because a coverage census reveals nothing about any effect.

---

## 11. DESCRIPTIVE ONLY — the three-way consensus comparison (founder's question)

**This section is descriptive and can never become confirmatory. It carries the §2 scope limit,
which is not relaxable after the numbers are seen: nothing here may be reported as an edge, as
beating the market, or as evidence our rankings beat consensus.** No p-value, no confidence
interval, no significance flag — `validate_exploratory_artifact` enforces this. It is outside
every FDR denominator. n=4 (2021–2024; 2025 sealed), veterans-only common universe.

The founder's question, in his words: *"then we test our bottom up r squared against consensus
and consensus adjusted for what we do have for now"* — (1) bottom-up alone, (2) consensus alone,
(3) **consensus adjusted by bottom-up**, which is the shape he wants the product to take.

### 11.1 On R² — his language, and where it is and is not defensible

**He is using R² because the board's own note uses it** (ADR-016: consensus rank explains
0.158–0.266 of outcome variance). That is a real, correctly-stated number and this section
answers in the same units rather than silently substituting a different metric.

**Where R² is defensible here:** as the founder posed it — variance in actual season points
explained — for a *nested* comparison at a single position, on the points scale.

**Where it is not, stated plainly:** R² on season points is scale-sensitive and already measured
**negative** at QB (−0.13) and TE (−0.85) in this project, meaning the projections are worse
than the positional mean even where their *ordering* is good. An R²-only reading would call the
model useless at TE while tau says its ordering improves. So **both are reported side by side at
every position**, with tau-b as the ordering statistic and R² as the founder's variance
statistic, and neither presented alone. The tau equivalent of "explains 0.16–0.27 of the
variance" is simply the ordering figures already on file — consensus tau-b vs actual finish per
position — and it will be printed next to the R² so the two languages are directly comparable.

### 11.2 The three comparisons, and why they are **one** question, not three

**The blend contains consensus.** In-sample, `R²(consensus + bottom-up) ≥ R²(consensus)` is a
mechanical identity — adding a regressor can never reduce in-sample R². Reporting three numbers
side by side would therefore guarantee the blend "wins" and would mean nothing.

Two consequences, both pre-committed:

1. **The only honest quantity is out-of-sample incremental R².** Fit the blend weights on the
   other three seasons, evaluate on the held-out one, rotate. Report
   **ΔR²_oos = R²_oos(consensus + bottom-up) − R²_oos(consensus alone)**, which *can* be
   negative and usually is when the added regressor is noise. Report bottom-up-alone R²_oos in
   the same table for context.
2. **This is one nested question per position, not three independent comparisons**, so the
   multiple-comparisons concern is handled by construction rather than by correction: there is
   one increment, not a family of three. Bottom-up-alone and consensus-alone are the two
   *components* of that increment, not rival hypotheses. They must be reported as a single
   nested row per position — never as a three-way leaderboard, which is the presentation that
   would smuggle the non-independence back in.

**With n=4 seasons and blend weights fitted on three, ΔR²_oos is close to uninformative** — its
sampling variability at this n dwarfs any plausible increment. It is reported because the
founder asked and because a strongly negative value is genuinely informative (it would say
adding bottom-up actively degrades consensus). A positive value at n=4 says almost nothing, and
that asymmetry is registered here so it cannot be read the other way later.

### 11.3 The standing-law conflict, escalated not resolved

`CLAUDE.md` §4 is explicit: *"Ranking sources stay separate, never blended."* The founder's
preferred product shape — consensus adjusted by bottom-up — is a blend. **Measuring a blend
descriptively is not shipping one**, and this section only measures. **Shipping it would require
an amendment to `CLAUDE.md` §4, which is a founder decision and is escalated, not resolved
here.** A middle path worth putting to him: consensus adjusts *display and confidence* (labelled
overlay, disagreement flags) rather than being averaged into a score — which satisfies the
intuition without violating the never-blend rule or the traceability principle.

### 11.4 Successor question — registered as future work, deliberately not folded in

**"Once bottom-up exists, compare it against consensus and see which is better, with consensus
acting as an adjustment rather than a rival"** is a **separate registration (PR-006, unwritten)**
and must not widen PR-004 or PR-005. It is n-limited until January 2027 at the earliest: it
needs either more consensus seasons or P-2026's prospective result. Recorded so it is not lost
and not silently absorbed into a test it would contaminate.
