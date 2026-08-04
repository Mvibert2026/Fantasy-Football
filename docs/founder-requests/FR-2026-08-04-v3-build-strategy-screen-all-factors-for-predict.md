---
ID: FR-2026-08-04-v3-build-strategy-screen-all-factors-for-predict
STATUS: NEW
SOURCE: chat 2026-08-03
RAISED: 2026-08-04
---

## Request
v3 build strategy: screen all factors for predictive power, fit weights jointly, compare v3 vs v2 once; v2 stays as checkpoint

<Founder's own words where possible -- paraphrase only when necessary, and say so.>

## Why it matters

## Initial read
<Not the founder's own words -- your read on scope, constraints, sequencing.>

## Collinearity — binding constraints on the v3 joint fit

Founder, 2026-08-03: *"There is some collinearity. And sometimes it is predictive."* and
*"Let's just be very careful with collinearity."* These bind whoever fits v3.

**1. Ridge or elastic net. Never pure lasso.** Lasso picks arbitrarily among correlated predictors
and zeroes the rest — with snap share, target share and routes run all measuring similar things, it
would keep one at random and discard information the founder has explicitly said is sometimes
predictive. Ridge shrinks correlated predictors *together*, which is the behaviour we want.

**2. Standardise every predictor before penalising.** An unstandardised penalty is applied unevenly
across predictors on different scales, and silently prefers whichever factors happen to have large
units.

**3. Do not prune on correlation.** Anything clearing the screen's noise benchmark goes into the fit
however collinear it is. The penalty decides what earns weight; a human threshold on `r` does not.

**4. Measure coefficient stability and report it.** Refit under leave-one-season-out and bootstrap
resampling. **If a coefficient's sign flips across refits, that factor's weight is not
interpretable** — record it as such rather than letting someone discover it by quoting the number.

**5. Construct the within-cluster contrasts as their own candidates.** Snaps minus routes, routes
minus targets, carries minus red-zone carries. Cancelling the shared variance is what leaves the
*role* behind, and these can outpredict either component.

**The consequence that is easy to miss, and it touches a deliverable the founder asked for.**
Collinearity damages *explanation* far more than *prediction*. A ranking built on collinear inputs
can be accurate while its individual weights mean almost nothing. That is tolerable for the board —
and **not** tolerable for the explained-deviation report
(`FR-2026-08-01-respectability-check...`), which requires a stated reason for every large
disagreement with consensus, nor for the in-app assistant answering "why is this player ranked here."

**So v3 must ship, alongside its weights, an honest statement of which coefficients are stable enough
to explain a ranking with and which are not.** A good prediction score does not license after-the-fact
stories about individual factors.

## Per-position factor sets — founder, 2026-08-03

> "For different positions certain factors may be in or out. And not in others."

**v3 is four models, not one.** There is no global factor set, and no factor is required to appear at
every position. Screening, selection, fitting and grading are all per position — QB, RB, WR, TE — and
a factor that earns weight at one position and is dropped at another is a **normal outcome, not an
inconsistency to reconcile.**

**Why this is not merely tidy.** Air yards and aDOT are meaningful for receivers and close to
meaningless for backs. Red-zone carries matter at RB and do not exist at QB in the same sense. Route
participation has no analogue for a quarterback. Forcing one shared feature list would either drop
signal that only exists at one position, or feed every model columns that are structurally empty for
it — which is the same error as fitting rookies and veterans jointly (see `CLAUDE.md` §2a): a
predictor that is *structurally absent* rather than merely weak teaches the model something false.

**Consequences that bind:**

- **Report every result per position.** A pooled number hides that a factor is carrying one position
  and harming another. Batch C1's snap share was NULL at RB and WR and HARM at TE — one row, three
  different answers.
- **Sample size differs sharply by position**, and it drives what is decidable. Tier-2 grading spans
  12 seasons but the per-position `S_pos` differs, and QB and TE have far fewer draftable players
  than WR. **INCLUDE may be unreachable at QB and that is the correct answer at this sample size**,
  not a failure of the factor.
- **The collinearity clusters differ by position too.** Snap share and route participation are near
  duplicates at WR; at RB, snaps and carries diverge because of passing-down roles. Cluster the
  factors **within each position**, never once across all four.
- **The per-position sets are themselves a finding worth reporting.** Which factors matter at RB but
  not WR is a football claim the founder can sanity-check by eye — the same method that caught two
  real defects already.

## Incumbent features get no grandfather clause — founder, 2026-08-04

> "So how many tested factors do we have, why aren't we retesting those 'already in the model'."

**Nine factors are currently inside the model and none has faced the ADR-070 instrument.** They were
admitted under judgement or under the frame that has since been invalidated — i.e. **exactly the
evidence basis that caused twelve tested factors to be thrown out.**

| Ledger | Factor | Kind |
|---|---|---|
| T0-5 | Depth chart / role | predictive |
| T0-6 | Injury designations & status | predictive |
| T0-7 | Age as a decline curve | predictive |
| T0-8 | Prior-year target / touch share | predictive |
| T1-14 | Air yards, aDOT | predictive |
| T1-25 | NFL draft capital (rookies) | predictive |
| T0-4 | Bye weeks | structural |
| T2-33 | Re-score under this league's rules | structural — the scoring engine |
| T2-34 | Replacement levels QB10/RB30/WR40/TE10 | structural — the VBD config |

**Batch C4 skipped T1-14 and T1-25 on the grounds that they are "already base-spec features, not new
candidates." That reasoning is backwards** and must not be repeated: being already included is a
reason to test, not a reason to skip. An untested incumbent adds variance to every arm measured
against it, which makes every *other* factor harder to detect.

**Binding on the v3 fit:**

1. **The six predictive incumbents enter the candidate pool on equal footing with every new
   factor.** No feature is assumed in. Regularisation decides what earns weight; prior membership
   confers nothing.
2. **The three structural rows are out of scope** — scoring rules, replacement levels and bye weeks
   are configuration, not predictors, and are not fitted.
3. **If v3 loses to v2 and we revert to incremental testing, the incumbents get explicit ablation
   arms** — remove the feature, does the model degrade? That is the only way to test an incumbent
   inside the incremental frame, and it has never been run for any of them.
4. **Report which incumbents survive.** An incumbent shrunk toward zero by the fit is a finding, and
   a more valuable one than a new factor failing — it means the current model has been carrying
   something that does not earn its place.
