# Factor campaign C2 — batch 6 registration

**Registered by `ranker` (batch 6), 2026-07-30.**

| | |
|---|---|
| batch | 6 |
| agent | ranker |
| **m_6** | **23** |
| pre-commitment | `docs/ranking/factor-batch-6-precommit.md` (`f6e09da`, committed before any arm was fitted) |
| results | `docs/ranking/factor-batch-6-results.md` |
| scope | N10 passing efficiency (QB), N11 sack avoidance (QB), registry #18 expected fantasy points (all four positions) |

## An honesty note that belongs on the record, not buried

**This registration is late, and the batch initially graded at the wrong denominator.** Batch 6
ran concurrently with batches 4, 5 and 7 and did not see this directory. It created its own
manifest at `docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`, registered m = 23
there **before fitting**, and graded at a campaign denominator of **47** (its own 23 plus batch
3's 24). C2's rule gives **M_campaign = max(Σ_b m_b, 80) = 80**, and C2 explicitly excludes
batches 1–3 from retroactive re-grading.

**Batch 6 was re-graded at M = 80 without rerunning anything**, because its pre-commitment required
every surviving arm to carry a **breaking m** — the largest denominator at which it would still
clear BH q = 0.10. The device did the job it was registered for:

| arm | breaking m | at M=47 | at M=80 |
|---|---|---|---|
| X2 REPLACE `ppg_w`, RB | 1721 | HARMFUL | HARMFUL |
| P2 ANY/A, QB | 308 | PROJECTION-ONLY | PROJECTION-ONLY |
| P3 passer rating, QB | 308 | PROJECTION-ONLY | PROJECTION-ONLY |
| X2 REPLACE `ppg_w`, WR | 308 | HARMFUL | HARMFUL |
| X2 REPLACE `ppg_w`, QB | 140 | HARMFUL | HARMFUL |
| **X3 luck residual, RB** | **56** | BOARD-NEUTRAL | **MARGINAL — loses significance** |

**Exactly one arm changed grade, and it moved in the conservative direction.** All published
batch-6 grades are at M = 80. `F-FACTOR-CAMPAIGN-2026-07-30.yaml` is superseded by this directory
and now says so.

## The 23 registered tests

E1a = out-of-sample MAE of one declared component, full universe, 11 target seasons (2014–2024),
season-block bootstrap, 4,000 reps. E1 component: QB `attempts`, RB `carries`, WR/TE `targets`.

| # | id | arm | positions |
|---|---|---|---|
| 1 | P1 | EPA per dropback → `att_pg` | QB |
| 2 | P2 | ANY/A → `att_pg` | QB |
| 3 | P3 | passer rating → `att_pg` | QB |
| 4 | P4 | CPOE → `att_pg` | QB |
| 5 | P4c | `cpoe_known` only — CONTROL | QB |
| 6 | Pc | `qbeff_known` only — CONTROL | QB |
| 7 | K1 | sack rate per dropback → `att_pg` | QB |
| 8–11 | X1 | add `xfp_pg_w` to the E1 volume spec | QB, RB, WR, TE |
| 12–15 | X2 | replace `ppg_w` with `xfp_pg_w` | QB, RB, WR, TE |
| 16–19 | X3 | add `xfp_resid_pg_w` (realised − expected) | QB, RB, WR, TE |
| 20–23 | X4c | `xfp_known` only — CONTROL | QB, RB, WR, TE |

Control arms count in m: they are expected to be uninformative and including them costs the
treatment arms power, which is the conservative direction and is taken on purpose.

**Outside the family, entering no denominator and carrying no claim:** the xFP overlap diagnostic
(mandatory regardless of result), YoY persistence of the five QB efficiency metrics, and their
correlation with season-N points and with the residual on consensus ADP.
