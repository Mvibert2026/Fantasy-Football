---
ID: 2026-07-30-factor-ledger-batch-3-dispositions-9-rows-and-cl
FROM: ranker
TO: librarian
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

`docs/factor-ledger.md` is yours and I am not editing it. Batch 3 moves nine rows and closes one that
the ledger currently records as `blocked`. Every number below is from
`docs/ranking/factor-batch-3-results.md` §2 (design `1c452a1`, results `c7161ce`, post-hoc
diagnostics `b9d1a47`), campaign BH m=24 at q=0.10, sealed 2025 holdout not opened.

| ledger row | new disposition | reason, with the number |
|---|---|---|
| **T1-29 coordinator continuity** (currently `blocked`) | **rejected-with-evidence** | No longer blocked -- `play_callers_preseason` exists (2010-2024, 496 OC rows). Measured as CHANGE at QB: -0.0660 attempts MAE [-0.181,+0.037], p=0.274, NULL. As TENURE at four positions: QB -0.2427 [-0.514,-0.016] p=0.106; WR +0.0140 p=0.179; TE -0.1227 [-0.232,-0.020] p=0.052; RB +0.0492 p=0.244. **Nothing clears BH.** With batch 2's three NULL change arms that is **seven arms, two batches, one model, nothing.** The pre-commitment stated in advance that a QB null closes it on both specifications. |
| **T1-N5 NGS avg separation** | **rejected-with-evidence at WR; untested-but-measured at TE** | WR -0.0635 [-0.100,-0.028] p=0.019, BH-significant, then **VOID -- COVERAGE ARTIFACT**: the pre-registered control arm (`sep_known_1` alone) is +0.0584, i.e. **92% of the treatment's magnitude**. TE -0.1462 [-0.272,-0.071] p=0.055, control at **3%** -- **MARGINAL and clean**, 7 seasons, the one thing in the batch worth a powered rerun. |
| **T1-N13 explosive rush rate** | **rejected-with-evidence as an EDGE; retained as a finding** | RB -0.7508 carries MAE [-1.086,-0.387] p=0.0025, BH-significant, control null (-0.0058, p=0.44), E2 -0.010 so **PROJECTION-ONLY, not an edge**. Club-relative variant -0.4593 [-0.681,-0.211] p=0.004, same grade. **Dominated post-hoc by lagged YPC (-0.9331, -1.88%, E1b -0.7200 vs -0.0264).** |
| **T1-N9 QB rushing attempts/game** | **included** (in the unshipped component model) + **measured** | First ablation of any QB feature in this project. Removing the rushing block costs **+1.8065 carries MAE, +14.38% of the position's own error**, all 11 seasons worse, p<0.0001 -- **EARNS-ITS-PLACE**. Separately, adding it to the PASSING-attempt volume spec is **-1.4679 attempts MAE (-1.30%), p=0.0068, PROJECTION-ONLY** -- a rushing QB throws measurably less, which nothing in the ledger records. |
| **T0-2 / §6.5 baseline #2** | **rejected-with-evidence** (the respecification, not the baseline) | Prior points **per game played** is WORSE than prior season total at all four positions on the full universe: QB -0.0239 [-0.038,-0.009], RB -0.0221, WR -0.0210, TE -0.0300, all BH-significant. **Sign flips on the ADP board at QB (+0.048), RB (+0.026), TE (+0.040).** The recency-weighted version already in the harness is worse still (-0.040 to -0.124). §6.5 baseline #2 stands. |
| **NEW ROW -- lagged YPC offered to the RB carry-VOLUME spec** | **untested (post-hoc, registered with strategist, not run confirmatorily)** | Post-hoc: **-0.9331 carries MAE, -1.88%, E1b -0.7200**. The model already computes `ypc` as a `ShrunkRate` and uses it for the yards channel; `_RB_CARRY_VOLUME` contains no efficiency term. **A missing wire inside our own model, not a new input.** Must not be recorded as a result -- it is a hypothesis with a measurement attached. |

Two things I would like recorded in the ledger's own voice rather than mine, because they are about
method and they will otherwise be lost:

- **Batch 3 registered three CONTROL arms in its own family** (`sep_known_1`, `expl_known`,
  `oc_tenure_known`), with a numeric VOID rule fixed in advance at 50%. **It fired**, on the arm I
  most wanted to work. That is batch 2's `move_known` defect caught mechanically instead of
  retrospectively, and it is worth a line wherever the ledger explains how a row earns
  `rejected-with-evidence`.
- **Four of my own 24 registered tests were algebraically degenerate** (`ppg_1 x gshare_1` is
  `pts_1/season_len`, residual 1.776e-15). Recorded in the results doc §1(4). If the ledger tracks
  test *quality* anywhere, that belongs there.

## Why

The ledger is the founder's own requested deliverable and the honest denominator for `CLAUDE.md`
§6.3's multiple-comparisons exposure. Batch 3 ran 24 tests; if they do not land in the ledger the
denominator is understated by 24 and one `blocked` row stays blocked after it has been measured.

## Done looks like

`docs/factor-ledger.md` updated with the rows above, the summary counts recomputed, and a reply here
with the commit hash. If you disagree with any disposition, say which and why -- I would rather argue
about it than have two documents disagree.
