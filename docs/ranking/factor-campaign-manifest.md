# RETIRED — superseded by `docs/ranking/factor-campaign-manifest/`

**Retired in place by `ranker` (batch 7), 2026-07-30. Not deleted, because the episode is part of
the record.**

This single file was created by batch 7 on 2026-07-30 as the shared campaign family manifest its
dispatch required, **before any batch-7 arm was fitted**. It registered batch 7's 16 tests at a
campaign denominator of **m = 80** with a one-directional rule: if the realised campaign total
exceeds 80 every grade is recomputed at the realised total; if it comes in under 80 nothing is
relaxed.

**It was the third such manifest built the same day.** Batch 5 had already opened
`docs/ranking/factor-campaign-manifest/` — a **directory, one file per batch**, which is the better
design precisely because four concurrent agents on one checkout cannot clobber each other's
registration in it. Batch 6 built a fourth
(`docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`) and migrated. Batch 7 has now
done the same.

**All three independently derived the same denominator, 80, from the same premises** (four
concurrent batches × ~20 registered tests each). Batch 7's grades are unchanged by the migration:
C2's rule is `M_campaign = max(Σ_b m_b, 80)`, and with batch 7's 16 added Σ m_b = 56, so the floor
of 80 still binds and 80 is exactly what batch 7 graded at.

**Go to:**

- `docs/ranking/factor-campaign-manifest/README.md` — the aggregation rule and the registered-batch table
- `docs/ranking/factor-campaign-manifest/batch-7.md` — batch 7's registration, its 16 tests, and the
  cross-batch coverage-flag finding it owes the campaign
- `docs/ranking/factor-batch-7-precommit.md` §4 — the original registration, committed `fb7627a`
  before any arm was fitted
