# Factor campaign family manifest — 2026-07-30

**Purpose: one denominator for the whole concurrent campaign.** Four factor batches are running in
parallel against the same component model, the same eleven seasons and the same player universe.
`CLAUDE.md` §6.3 is explicit that ~200–300 heavily autocorrelated players against ~30 candidate
factors is a textbook overfitting setup — and correcting *inside* each batch while ignoring the other
three is exactly the multiplicity failure that section names. **Benjamini–Hochberg is applied once,
at the campaign level, with the denominator recorded here.**

**This file is shared and append-only by section.** Each batch owns its own `## Batch N` heading and
edits nothing else. Do not renumber, do not rewrite another batch's row, do not delete a section when
a batch ends — a closed batch's tests still count in the denominator.

---

## The registered denominator

| | |
|---|---|
| **Campaign m (registered)** | **80** |
| Basis | four concurrent batches × 20 registered tests, declared in advance as a planning figure |
| q | 0.10 headline, 0.05 also reported |
| Direction rule | **If the realised campaign total exceeds 80, every grade is recomputed at the realised total. If it comes in under 80, nothing is relaxed.** A denominator that shrinks after the results are seen is not a pre-registration |
| Batch-level BH | may be reported, **only** as a clearly-labelled secondary. It is never the headline |

**Closed campaigns are not folded in.** Batch 3 registered and ran its own campaign at m = 24
(`docs/ranking/factor-batch-3-precommit.md` §4) and closed before this manifest existed; its grades
stand at m = 24 and its 24 tests are **not** counted here. Batches 1 and 2 likewise. This manifest
covers the 2026-07-30 concurrent campaign only.

---

## Registered batches

| batch | scope | registered tests | precommit | status |
|---|---|---|---|---|
| 4 | *(unregistered — batch 4 appends its own row)* | — | — | — |
| 5 | *(unregistered — batch 5 appends its own row)* | — | — | — |
| 6 | *(unregistered — batch 6 appends its own row)* | — | — | — |
| **7** | **RB usage and efficiency — sweep N14–N19** | **16** | [`factor-batch-7-precommit.md`](factor-batch-7-precommit.md) | registered 2026-07-30 |

---

## Batch 7 — running-back usage and efficiency

**Owner:** `ranker`. **Registered tests: 16, all at RB.** FDR endpoint **E1a** = out-of-sample MAE of
one declared component, arm − primary, paired by season, season-block bootstrap.

| # | id | factor | E1 component | first target |
|---|---|---|---|---|
| 1 | Z1 | N14 red-zone (inside-20) **snap** rate → carries | carries | 2018 |
| 2 | Z2 | N14 inside-5 snap rate → carries | carries | 2018 |
| 3 | Z3 | N14 red-zone snap rate → targets | targets | 2018 |
| 4 | Z1c | CONTROL — red-zone snap coverage flag | carries | 2018 |
| 5 | G1 | N15 inside-5 TD conversion vs league base rate | rush_tds | 2014 |
| 6 | G1p | CONTROL — binomial placebo, identical shrinkage geometry | rush_tds | 2014 |
| 7 | G1c | CONTROL — inside-5 coverage flag | rush_tds | 2014 |
| 8 | Y1 | N16 YAC per reception | rec_yards | 2014 |
| 9 | Y1c | CONTROL — YAC coverage flag | rec_yards | 2014 |
| 10 | S1 | N17 receiving share of his own fantasy points | targets | 2014 |
| 11 | S2 | N17 ≥40% receiving-share bin | targets | 2014 |
| 12 | P1 | N18 prior snap share | carries | 2015 |
| 13 | P2 | N18 ≥60% snap-share gate | carries | 2015 |
| 14 | P1c | CONTROL — snap-count coverage flag | carries | 2015 |
| 15 | L1 | N19 his own late/early opportunity ratio | carries | 2014 |
| 16 | L2 | N19 group late lift, draft round × career year | carries | 2014 |

**Five of sixteen are controls, on purpose.** They are expected to be uninformative and including
them costs the treatment arms power; that is the conservative direction and it is taken deliberately.

---

## Batch 4 — *(append here)*

## Batch 5 — *(append here)*

## Batch 6 — *(append here)*
