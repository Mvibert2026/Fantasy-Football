# Campaign C2 registration — batch 5, pass-catcher opportunity

**`ranker`, 2026-07-30. Written and committed BEFORE any batch-5 arm was fitted.**
Full design: `docs/ranking/factor-batch-5-precommit.md`.

## m_5 = 17

All 17 are **F1 model arms**, endpoint **E1a** (out-of-sample component MAE, arm − primary,
paired by season, season-block bootstrap 4,000 reps). The denominator is 17 regardless of how
many turn out to be computable; a cell graded NO DATA still consumes its slot.

| # | id | block | factor | pos | E1 comp | target seasons |
|---|---|---|---|---|---|---|
| 1 | R1 | routes | targets per route run | WR | targets | 7 (2018–2024) |
| 2 | R1 | routes | targets per route run | TE | targets | 7 |
| 3 | R1 | routes | targets per route run | RB | targets | 7 |
| 4 | R2 | routes | **routes per game** (route volume itself) | WR | targets | 7 |
| 5 | R2 | routes | routes per game | TE | targets | 7 |
| 6 | R2 | routes | routes per game | RB | targets | 7 |
| 7 | R3 | routes | receiving first downs per route run | WR | targets | 7 |
| 8 | R3 | routes | receiving first downs per route run | TE | targets | 7 |
| 9 | R1c | routes | **CONTROL** — `routes_known` coverage flag alone | WR | targets | 7 |
| 10 | R1c | routes | CONTROL — `routes_known` alone | TE | targets | 7 |
| 11 | R1c | routes | CONTROL — `routes_known` alone | RB | targets | 7 |
| 12 | D1 | firstdown | receiving first downs per game | WR | targets | 11 (2014–2024) |
| 13 | D1 | firstdown | receiving first downs per game | TE | targets | 11 |
| 14 | D1 | firstdown | receiving first downs per game | RB | targets | 11 |
| 15 | D2 | firstdown | receiving first downs per target | WR | targets | 11 |
| 16 | D2 | firstdown | receiving first downs per target | TE | targets | 11 |
| 17 | D2 | firstdown | receiving first downs per target | RB | targets | 11 |

## Declared OUTSIDE the family, and therefore not in m_5

**Family F3 — the Heath-0.79-vs-Hoopes-0.68 contradiction, endpoint E4.** A descriptive
cross-sectional replication with **no model refit and no BH claim attached**. It is a
measurement of published numbers on our data, not a test of our model, and it is reported as
such. Details in the pre-commitment §6.

**Not registered at all, with the reason recorded rather than the arm quietly dropped:** the two
FTN-charting arms in the dispatch, **N1 first-read target share** and **N2 catchable target
share/rate**. They are ungradeable in this harness — see the pre-commitment §2, which shows the
walk-forward yields **exactly one** target season for a 2022-start feature once the 2025 holdout
stays sealed. Registering an arm that cannot resolve anything would spend campaign m to buy a
guaranteed NULL.
