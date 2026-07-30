# ADR-DRAFT — Table-stakes inclusion, the FDR denominator, and the `CLAUDE.md` §11 tension

**Status:** Proposed (ruling issued; number to be allocated by `tools/handoffs.py adr next` at landing)
**Date:** 2026-07-30
**Owner:** Strategist (ruling) / Ranker (execution)
**Answers:** ask 5 of `docs/handoffs/2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar.md`
(ranker's reply, 2026-07-30), raised by `FR-2026-07-30-bottom-up-must-include-all-tier-0-table-stakes-n`
**No `CLAUDE.md` change is required. See §4.**

---

## 0. The ruling

| | |
|---|---|
| **The PM's multiplicity argument** — table stakes included on construction grounds, never tested individually, contribute **zero** to the FDR denominator | **RATIFIED.** It is correct, and the ranker was right to adopt it |
| **The ranker's operational form** — include by construction, do not test each factor, the Tier 0 block takes **one** holdout evaluation *as a block* (denominator +1), every feature passes the `SeasonPanel` access-log audit | **RATIFIED, with three binding amendments** (§2) |
| **"Table stakes are free"** | **REJECTED**, exactly as the ranker refused to let it carry. Multiplicity is avoided; estimation variance and leakage surface are not (§3) |
| **The `CLAUDE.md` §11 tension** | **Resolved without amending `CLAUDE.md`** — the ranker's reading is correct *under a condition he did not state*, and the condition is checkable (§4) |

---

## 1. Why the multiplicity argument is right

Benjamini–Hochberg corrects for **selection among tested hypotheses**. The inflation it controls comes
from choosing what to report *after* seeing which candidates looked good. An input that is included
unconditionally, whose individual contribution is never examined and never used to decide whether to
keep it, produces **no selection event**. There is no hypothesis, no test, no p-value, and therefore
nothing to correct.

Adding such inputs to the denominator would be worse than a harmless conservatism: it would inflate
`m`, raise every adjusted p in the family, and make the Tier 1/Tier 2 tests that *are* selections
harder to clear — spending the correction budget on things that were never at risk of being false
positives.

**Ratified.** The ranker says he would have got this wrong; he would have, and adopting the PM's
version was the right call.

---

## 2. Three binding amendments to the operational form

### 2.1 Unconditionality must be structurally enforced, not promised

**This is the whole load-bearing condition and everything else in the ruling depends on it.**

"Included by construction" is only exempt from correction while it is *actually* unconditional. The
failure mode is post-hoc pruning, and it is the most natural thing in the world to do:

> include twelve table stakes → fit → *"air yards has the wrong sign, drop it"* → refit

That second step **is** a selection event. It used the data to choose the feature set, it is a test,
and it is now an unrecorded one — which per `docs/preregistration/README.md` inflates every surviving
result in the family.

**Required, in PR-004 §4's closed-exit style:**

1. The Tier 0 feature list is **frozen by name** in the registration before any fit, and covered by
   the registration's `content_hash`.
2. **Any removal of any feature from the block, for any reason discovered after a fit, converts the
   block into a selection procedure.** It then requires a new `PR-` id, `m` incremented, and BH
   recomputed and republished across the whole family. Not a caveat — a new registration.
3. A feature may be removed **before** any fit for a reason that is not about its performance (it
   does not exist in the data, coverage is below a pre-stated floor, it leaks). That reason is
   recorded in the registration at removal time.

Without (2), "construction grounds" is an unbounded researcher degree of freedom wearing a principled
hat. With it, the exemption is real and safe.

### 2.2 The block's one holdout evaluation must be against the same model without the block

The ranker's "denominator +1, evaluated as a block" is right, and one thing must be pinned down or it
does not test what it claims to.

> **The one evaluation is: same architecture, same fitting procedure, same folds, Tier 0 block
> included vs. Tier 0 block omitted.**

Not "the model with table stakes vs. some unrelated baseline." Only the ablation form answers
`CLAUDE.md` §6.3's *"every added parameter must earn its place against a holdout"*, and it costs one
extra arm on the same fit. Adopt all twelve or adopt none — evaluating the block as a unit is exactly
what makes it one test rather than twelve.

Graded on the primary metric ruling's gate, with its §5.2 regime **B** applying: a table-stakes block
is by definition an independent within-position claim, so it must show `mean Δτ_b > 0` and
`Δτ_b ≥ −0.02` at every position, alongside criteria (a) and (b).

### 2.3 The `SeasonPanel` access-log audit is necessary and not sufficient

Ratified as required. Add: **every feature in the block is separately checked for the disguised
look-ahead forms in guardrails §1** — retroactively-assigned role flags, full-season aggregates used
for a pre-season decision, and any status field whose value in the database is its *final* value
rather than its pre-Week-1 value. Depth chart and injury status are the two features in this block
most exposed to that last form, and both are already implemented, so the check is on existing code.

---

## 3. Why "table stakes are free" is rejected — and the ranker understates his own point

He is right that multiplicity is avoided while estimation variance and leakage surface are not. The
variance concern is larger than "real":

**Twelve features against ~13 usable seasons is not a multiplicity problem at all. It is a
degrees-of-freedom problem**, and it degrades holdout performance through *variance* rather than
through false positives — which means no amount of FDR correction touches it, and it will not show up
as a suspicious p-value. It shows up as a model that fits the training folds and does worse out of
sample than the simpler thing it replaced.

The existing control is adequate and must be stated rather than invented: **ridge, with the penalty
fitted inside the training fold**, shrinks a useless feature toward zero automatically. PR-004 §7
already requires in-fold fitting of ridge coefficients, shrinkage `k`, and standardisation means, with
nothing hoisted. **Required here: the registration states that the penalty is fitted in-fold and the
holdout evaluation reports the block's realised effective degrees of freedom**, so "twelve features"
can be checked against how many the fit actually used. If the penalty is hoisted, or hand-set, the
exemption in §1 does not apply and §4's condition also fails.

---

## 4. The `CLAUDE.md` §11 tension — resolved, no amendment needed

§11: *"Football claims must be grounded in verifiable data from the pipeline, not intuition or
received wisdom. 'Everyone knows X' is a hypothesis to test."*

The ranker's reading — §11 governs *claims*, and "this is an input" is not a claim — is **correct**,
and he was right to flag that it is convenient for him and therefore not his to adopt. It holds, but
only under a condition he did not state, and the condition is what does the actual work:

> **Construction-grounds inclusion is legitimate only where the model's own fitting procedure can
> assign the feature zero weight, and where no human hand-sets, hand-floors, or force-weights it.**

The distinction is whether a person asserted that the factor matters:

| Form | §11 verdict |
|---|---|
| Feature is offered to a penalised fit which may shrink it to zero; the data decides | **No claim is made.** §11 is satisfied. Include by construction, denominator +0 |
| Feature is given a hand-chosen weight, a non-zero floor, or a guaranteed influence | **A human has asserted "X matters."** That is precisely §11's *"everyone knows X."* It is a hypothesis, it needs a test, and the test enters the denominator |

This resolves the tension without touching standing law, and it is **checkable by reading the code**
rather than by taking anyone's word — which is why it is the right form of the condition. `CLAUDE.md`
is unchanged and no escalation past the ranker and me is required.

**The boundary case that *would* require an amendment**, recorded so it is recognised if it arrives:
a founder instruction to include a factor **with a guaranteed non-zero weight** on the grounds that
it is obviously right. That is a §11 conflict on its face, it cannot be resolved by either of us, and
it goes to the founder as a `CLAUDE.md` question.

---

## 5. Registered predictions, before the block is wired

The ranker recorded his in `fr136-q1-bottom-up-assessment.md` §6a.3 **before anything was wired** —
at most four of the twelve carry non-zero weight. That is good practice and it is what makes "we
added the table stakes and nothing moved" a prediction rather than a retrofit. Mine, alongside his,
and mine is more pessimistic:

> **Prediction: the Tier 0 block fails its single holdout evaluation. Moderate confidence.**

Grounds, all measured rather than intuited:

1. **Two of the twelve are already built and both measured NULL on ranking at all four positions** —
   #5 depth-chart role and #6 injury status, arms B/D/E in
   `experiments/bottomup/components/pos_features.py`. Eight NULLs from the two features most people
   would name first.
2. The component models as a whole do not beat consensus on rank anywhere, and at RB — the one
   position with demonstrated power — the point estimate is **−0.052**.
3. The standing calibration prior: four of five registered prediction sets across sessions 3–4 were
   materially wrong, and **every** miss over-credited a story about why a factor should work.

**This is a prediction, not a ruling.** The block is approved to run and the run decides. If it
clears, the prediction was wrong and the finding is real — and it will be more credible for having
been predicted against.
