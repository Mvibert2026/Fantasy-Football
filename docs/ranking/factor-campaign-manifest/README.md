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

*(Other batches: add your row and your `batch-<n>.md` file. If your row is missing at grading
time, the floor is what protects the campaign.)*
