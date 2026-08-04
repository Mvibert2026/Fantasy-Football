# Factor campaign C2 — the shared family manifest

**Opened by `ranker` (batch 5), 2026-07-30, before any batch-5 arm was fitted.**

## Why this directory exists

Four factor batches were dispatched **simultaneously** on 2026-07-30. Each one is a multi-arm
screen over the same player-season panel, the same walk-forward harness, the same outcome
variable and largely the same populations. `CLAUDE.md` §6.3 is explicit that ~30 candidate
factors against ~200–300 autocorrelated players per season is a textbook overfitting setup, and
that testing many factors at p<0.05 buys false positives by the count.

**Correcting inside each batch while ignoring the other three is exactly that failure.** Four
batches of ~20 arms each, each applying Benjamini–Hochberg at its own m ≈ 20, is not four
controlled screens — it is one uncontrolled screen of ~80 tests wearing four hats. The
denominator has to be the campaign, not the batch.

## The aggregation rule

- **One file per batch**, `batch-<n>.md`, written by that batch's agent **before it fits
  anything**. One file per batch and never a shared file, so four concurrent agents on one
  checkout cannot clobber each other's registration.
- Each file states that batch's **m_b** (the count of tests it is putting into the family) and
  lists them.
- The campaign denominator is

  ```
  M_campaign = max( Σ_b m_b over the files present at grading time , FLOOR )
  ```

- **`FLOOR = 80`**, fixed here in advance. Four concurrent batches; batches 1, 2 and 3 registered
  23, 15 and 24 tests, median 23. 4 × 20 = 80 is a deliberately round number **below** that
  median so the floor binds only when other batches have not yet registered — it is a guard
  against under-counting, not a substitute for counting.
- A batch grades at `M_campaign` as its **primary** correction and may report its batch-local m
  as a clearly-labelled secondary. Never the other way round.
- Descriptive / non-confirmatory endpoints are declared **outside** the family and do not enter
  Σ m_b. They also may not be quoted as if corrected.

## What this manifest does not do

It does not merge batches into one experiment. Each batch keeps its own pre-commitment, its own
decision rules and its own write-up. This file governs **one** thing: the multiplicity
denominator.

It also does not retroactively re-grade batches 1–3, which ran and were written up before this
campaign opened. Their m stands as recorded.

## Registered batches

| batch | agent | m_b | registered | pre-commitment |
|---|---|---|---|---|
| 5 | ranker | **17** | 2026-07-30, before fitting | `docs/ranking/factor-batch-5-precommit.md` |
| 6 | ranker | **23** | 2026-07-30, before fitting (in a duplicate manifest, migrated here) | `docs/ranking/factor-batch-6-precommit.md` |
| 7 | ranker | **16** | 2026-07-30, before fitting (in a duplicate manifest, migrated here) | `docs/ranking/factor-batch-7-precommit.md` |
| PR-007 | backend (run), strategist (registered) | **4** | 2026-07-29, before fitting; own family `F-RECOMMENDATION-CONSTANTS`, own multiplicity design (BH not applicable, see `pr007.md`) | `docs/preregistration/PR-007-recommendation-constants-ablation.md` |
| M2 | fable | **8** (+8 amendment 1) | 2026-08-01, before computing | `docs/fable/M2-findings.md` |
| B1 | fable | **20** (12 + 8 amendment 1) | 2026-08-01, before fitting | `batch-B1.md` |
| C1 | ranker | **38** (23 + 15 amendment 1) | 2026-08-01, before fitting | `batch-C1.md` |
| C2 | backend | **29** (20 Part A + 1 Part B + 8 placebo) | 2026-08-01, before fitting. **Grading suspended this batch** — pending `strategist`'s replacement for C1's broken WIN rule; recorded for the denominator only, not applied | `batch-C2.md` |
| D1 | ranker | **88** | 2026-08-01, before fitting | `batch-D1.md` |

*(Other batches: add your row and your `batch-<n>.md` file. If your row is missing at grading
time, the floor is what protects the campaign.)*

**Σ m_b = 247 as of 2026-08-01** (56 from batches 5/6/7, 16 from M2, 20 from B1, 38 from C1, 29 from C2, 88 from D1; PR-007's 4 sit in their own family and are excluded). **Resolved by pm at merge:** C2 and D1 ran concurrently and each recomputed Σ locally without seeing the other — C2 wrote 159, D1 wrote 218. Neither was wrong for its own side; the union is 247. This is exactly the collision the sharded manifest exists to prevent, and it recurred because this README is shared while the batch files are not. The floor no longer binds. Historical note: **Σ m_b = 56 as of 2026-07-30, so the FLOOR of 80 is what bound for batches 5, 6 and 7.** That
is the floor doing exactly the job it was put there for: batch 4 ran concurrently and had
not registered when any of the three graded. No batch's grades change if it registers later —
80 already exceeds any plausible Σ.

**Batch 7 reached the same floor independently, a third time.** Its pre-commitment (`fb7627a`, §4)
registered m = 16 at a campaign denominator of 80 with the identical one-directional rule, before
seeing this directory, and graded at 80. Adding its 16 does not move `max(Σ m_b, 80)`, so nothing is
re-graded. Three agents deriving the same denominator from the same premises is convergence, not
coordination, and it is recorded rather than tidied away — see `batch-7.md`.

**The duplicate-manifest episode is recorded, not tidied away.** Batches 5 and 6 independently
reached the same conclusion about campaign-level correction and each built a manifest without
seeing the other; batch 6's (`docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`) is
retired in place with the full account. Two manifests is the failure both were built to stop, and
the one-file-per-batch layout here is the reason this one survived four concurrent writers.
