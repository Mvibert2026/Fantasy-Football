---
ID: FR-2026-08-01-need-an-inclusion-test-run-candidate-factors-as
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Need an inclusion test: run candidate factors as arms against v2, not against the old consensus-derived board

Founder's own words, chat 2026-08-01, correcting PM for repeatedly citing the factor campaign's
nulls as if they settled what belongs in the model:

> "Again stop with referencing the tests. They were all run vs consensus. We need something to tell
> us if we should include the factor or not in our model. As far as I know we haven't tested that."

## Why it matters

**He is right, and the correction is binding on how results are cited from here.** PM has repeatedly
used "~90 factor tests, zero edges" as evidence that the external factor well is dry. It is not
evidence of that, and it does not answer the inclusion question.

**The precise mechanism, which differs slightly from the founder's stated reason and matters for
what we do next.** Strategist's Ruling 1 established that the batch arms compared a feature against
*the batch's own primary model*, not against consensus directly. But that primary model was itself
**consensus-derived** -- the shipped board is consensus re-scored, within-position identical to
consensus. So the campaign asked: *does factor X improve a model that already contains consensus's
embedded knowledge?* A factor can be genuinely informative and still return NULL there, because
consensus already priced it.

**v2 contains no consensus.** The same factor now faces a model with none of that knowledge baked
in. **A null on the old board carries almost no information about inclusion in v2.** The founder's
conclusion -- that we have not run the test that matters -- is correct.

## Initial read

**The inclusion test, stated plainly:** add the factor to v2, measure absolute rank correlation
against realised finish on dev seasons, grade WIN / HARM / NULL against a threshold registered
before measurement, corrected at the campaign level.

**The rig already exists.** This is exactly the harness Fable's B1 batch used on the three games arms
(`docs/ranking/factor-campaign-manifest/batch-B1.md`) -- registration before compute, per-position
WIN/HARM grading, BH at campaign M. Two arms were rejected by it and one passed. It has never been
pointed at the factor list.

**So the work is re-running candidates as arms against v2, not inventing methodology.** Practical
notes:

- `docs/factor-ledger.md` (95 rows) is the candidate pool and the multiple-comparisons denominator.
  Its dispositions were assigned under the old frame and **should be treated as un-tested for v2
  purposes**, not as settled -- otherwise the same error repeats in the other direction.
- Not every factor needs re-running: some were excluded on data availability or licensing rather
  than on measured signal, and those reasons still hold. The ledger distinguishes them.
- Expect a *higher* hit rate than the old campaign, and treat that as a hazard rather than good
  news: a model with less knowledge baked in has more room for anything correlated with outcomes to
  look useful. Registered thresholds and the campaign M are what keep that honest.

**Sequencing.** Queued behind the pending strategist G2a ruling, which is cheaper and unblocks the
shipped games model. Pairs naturally with the two data items in
`FR-2026-08-01-bar-is-parity-with-any-single-analyst-not-with-c` (per-analyst rankings, Vegas odds)
-- new inputs and a working inclusion test are the same programme.

**Citation rule going forward:** do not cite the ~90 nulls as evidence about factor inclusion. They
measured a different model.
