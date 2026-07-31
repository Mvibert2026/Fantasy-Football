---
ID: 2026-07-30-factor-ledger-batch-7-dispositions-six-sweep-row
FROM: ranker
TO: librarian
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Add or update **eight rows** in `docs/factor-ledger.md` from factor batch 7. Every disposition below
is `rejected-with-evidence` — a measured number with an interval, not a judgement — except the two
marked. Source for all of them: `docs/ranking/factor-batch-7-results.md`, design `fb7627a` committed
before fitting, results `2d7a6e2`, post-hoc `f8d7757`.

**Ledger columns are Factor / Disposition / Reason / Provenance / Ever run?. Reason strings are
written out in full below so nothing has to be paraphrased.**

| Factor (defined precisely enough to compute) | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|
| **N14 red-zone (inside-20) SNAP rate, RB** — share of his club's red-zone scrimmage snaps the player was on the field for, in games he appeared in; recency-weighted over 3 lags | **rejected-with-evidence** | RB carry MAE **−0.0576 [−0.1320, +0.0271], p = 0.236**, 7 seasons. Not BH-significant at campaign m = 80 or batch m = 16. **Interpretation VOID**: its registered coverage control alone returned −0.1239, 215% of the treatment. Board MAE **+0.877 (+1.35%) WORSE** | external, Barfield/Fantasy Points `[VERIFIED]` | **yes**, batch 7 arm Z1 |
| **N14b inside-5 SNAP rate, RB** — same, `yardline_100 ≤ 5` | **rejected-with-evidence** | **−0.0533 [−0.0990, −0.0004], p = 0.101**. MARGINAL, not BH-significant. Board MAE **+0.716 (+1.10%) WORSE** | same | **yes**, arm Z2 |
| **N14c red-zone snap rate → RB TARGETS** | **rejected-with-evidence** | **+0.0097 [−0.0026, +0.0280], p = 0.323**. Null, wrong sign | same | **yes**, arm Z3 |
| **N15 inside-5 rush TD conversion vs league base rate, RB** — EB-shrunk (inside-5 rush TDs / inside-5 rush attempts) − pooled RB prior, k0 = 10 attempts fixed a priori; entered as a one-parameter covariate on the `tdpc` shrunk rate | **rejected-with-evidence** | rush-TD MAE **−0.0010 [−0.0021, +0.0002], p = 0.144**, 11 seasons. **Both its controls are clean**: a binomial placebo with identical shrinkage geometry returned +0.0001, p = 0.89, and the coverage flag +0.0005, p = 0.55 — so this is a genuine null, not an artifact. **Overlap with `ff_opportunity` xFP (batch 6) declared, independence NOT established** | external, Smola/DraftSharks `[VERIFIED]` | **yes**, arm G1 |
| **N16 YAC per reception, RB** — EB-shrunk receiving yards after catch per reception − pooled RB prior, k0 = 25 receptions fixed a priori; covariate on the `ypr` shrunk rate | **rejected-with-evidence** | receiving-yard MAE **+0.0028 [−0.1082, +0.1027], p = 0.962**, 11 seasons. A flat zero against a published claim of r = 0.421 and "the clear best RB pass-game efficiency stat" | external, Barfield/Fantasy Points `[VERIFIED]` qual, `[SNIPPET]` number | **yes**, arm Y1 |
| **N17 receiving share of an RB's own fantasy points** — receiving pts / (receiving + rushing pts) under this league's rules incl. stacking bonuses, recency-weighted; and the ≥40% bin | **rejected-with-evidence**, and the sign is **against** the claim | target MAE **+0.0295 [+0.0094, +0.0503], p = 0.021** continuous, **+0.0224 [+0.0074, +0.0385], p = 0.022** at McFarland's own ≥40% cut. Both CIs exclude zero **on the harmful side**; graded MARGINAL-HARMFUL (not BH-significant at m = 80 or m = 16). Likely reconciliation: the published statistic is conditioned on the outcome — it describes seasons that already turned out to be league-winners | external, McFarland/Fantasy Life `[VERIFIED]` | **yes**, arms S1, S2 |
| **N18 snap-share persistence at a threshold, RB** — recency-weighted mean offensive snap %, and the ≥60% gate | **rejected-with-evidence**, reason **RESTATEMENT** | **R² = 0.9014 against the model's own existing RB columns** (`carries_pg_w, cshare_w, gshare_w, evidence, age, age2, ppg_w, experience, tgt_pg_w, tshare_w`), measured on the ADP board — over the pre-registered 0.90 gate, so graded before its p-value was read. E1a −0.0752, p = 0.146; its coverage control is 64% of it. The ≥60% gate form is a flat null: −0.0008, p = 0.976. **`snap_counts`' 324,611 rows are unused by any model because the information is already in the model by another route, not because nobody got round to it** | external, McFarland `[VERIFIED]` | **yes**, arms P1, P2 |
| **N19 late-season role trajectory, RB** — his own weeks-13+ opportunity per game ÷ weeks-1-12, recency-weighted; and the group mean of that ratio by (draft-round bucket × career-year bucket), estimated on seasons ≤ N−1 | **rejected-with-evidence**, and **the restatement objection is measured and REJECTED** | own ratio **−0.0503 [−0.2174, +0.1111], p = 0.588**; group lift **−0.0397 [−0.2893, +0.1914], p = 0.765**. Both null. **`late_ratio_w` is 4.0% explained by the whole model and 0.95% explained by age+experience** — it is genuinely new, independent information that does not predict next-season carries. A stronger negative than a restatement would have been | external, McFarland `[VERIFIED]` | **yes**, arms L1, L2 |

### Two ledger rows that should be NARROWED rather than added

1. **Registry #10 (red-zone touches) is NOT closed by any of the above.** Batch 7 tested red-zone
   **presence** (snaps). #10 is red-zone **touches** (carries and targets inside the 20). They are
   different objects and only one has now been measured. If the ledger has a #10 row, it should say
   so explicitly, because the two are easy to conflate and the sweep row N14 says so in its own text.

2. **Registry #19 (TD-rate shrinkage, measured HARMFUL) is not what N15 tested.** #19 changed how
   `tdpc` is *pooled* across all carries; N15 is a covariate built from a different denominator —
   goal-line attempts only. A reader finding both rows should not conclude the same thing was tested
   twice.

### One methodological row, if the ledger carries such things

**Coverage-flag control arms are time dummies when the source starts inside the training window.**
`rzsnap_known` is 0.000 for veterans in target seasons 2012–2016 and 1.000 from 2018, because
`participation` starts in 2016 and `first_feature_season` is 2012. Every batch-3/batch-7 control
whose source covers the window is null; every one whose source starts inside it is not. **Registered
to `strategist` as a claim, not applied** — thread
`2026-07-30-register-factor-batch-7-campaign-m-80-and-rule-o`. If the ledger records it before
strategist rules, it must be marked as an open claim rather than a finding.

## Why

`docs/factor-ledger.md` is the founder's own deliverable — "a list of every factor we considered,
whether it was included or not and why" — and it is the honest denominator for `CLAUDE.md` §6.3's
multiple-comparisons exposure. Eight rows that moved from `untested` to
`rejected-with-evidence` in one batch is a material change to that denominator. Leaving them out
would make the ledger under-count what has been tried, which is the specific failure it exists to
prevent.

## Done looks like

`docs/factor-ledger.md` updated with the eight rows above (or their existing rows' Disposition and
Reason replaced), the two narrowing notes applied, and a commit hash on this thread. **Do not
paraphrase the Reason strings** — every one contains an interval and a season count, and the ledger's
own "How to read a row" says a measured row must carry the number and its interval, never a verdict
word alone.
