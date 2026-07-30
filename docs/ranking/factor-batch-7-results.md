# Factor batch 7 — results

**Ranker, 2026-07-30.** The six running-back rows of the external analyst sweep
(`docs/research/analyst-factor-sweep-2026-07-30.md` §2c) — **N14 red-zone snap rate, N15 inside-5
TD conversion, N16 YAC per reception, N17 receiving share of own points, N18 snap-share persistence,
N19 late-season role trajectory.**

Design fixed in `docs/ranking/factor-batch-7-precommit.md`, content committed **`fb7627a` before any
arm was fitted**. **16 registered tests, all at RB. BH at the CAMPAIGN level, m = 80** — registered in
the shared `docs/ranking/factor-campaign-manifest.md`, not a batch-local family. Sealed 2025 holdout
**not opened**. Results `2d7a6e2`, post-hoc diagnostics `f8d7757`.

Reproduce:

```
.venv/bin/python -m experiments.bottomup.factors.run_factors7                # the 16 registered tests
.venv/bin/python -m experiments.bottomup.factors.run_factors7 --diagnostics  # the post-hoc work
```

> **Reading the CSV.** The grade string `NULL` is in `pandas.read_csv`'s default `na_values`, so it
> loads as `NaN` unless you pass `keep_default_na=False`. Batches 1–3 share this and the vocabulary is
> kept for comparability rather than diverged from.

---

## 1. Conclusion first — and the most useful result is a defect in the campaign's own method

### (1) Zero of sixteen. Nothing survives, and nothing closes the RB deficit

**No arm graded SURVIVES, PROJECTION-ONLY or BOARD-NEUTRAL.** Eleven NULL, two MARGINAL, two
MARGINAL-**HARMFUL**, one RESTATEMENT. Nothing reached BH significance at the campaign denominator
m = 80, and nothing reached it at the batch denominator m = 16 either — the multiplicity correction
is not what killed anything here.

The question the dispatch asked, answered directly:

| | |
|---|---|
| primary RB board deficit vs consensus ADP (E4) | **−0.0523**, 7 seasons |
| best arm's deficit | **−0.0515** (G1, inside-5 conversion) |
| worst arm's deficit | **−0.0572** (L1, own late-season ratio) |
| arms that closed it | **zero** |

**Nothing in this batch moves the RB deficit.** The whole 16-arm spread is ±0.005 around −0.052,
which is inside the season-to-season noise of the quantity. That is the honest headline and it is
stated before the per-arm table so it cannot be buried under a marginal.

### (2) The finding worth more than any arm: a `*_known` coverage flag is a TIME DUMMY when its source starts inside the training window

Batch 2 lost three arms to a coverage flag (`move_known`) that turned out to be 95–97% of an
apparently large treatment effect. Batch 3 responded by registering every coverage flag as **its own
control arm** with a 50%-of-treatment VOID rule. Batch 7 inherited that and it fired — but the
**mechanism is not the one the rule assumes**, and the difference matters for three other batches.

`rzsnap_known` — a binary "is this player in the `participation` table at all" flag — produced
**−0.1239 carries MAE, more than DOUBLE either red-zone treatment** (−0.0576, −0.0533). Post-hoc
decomposition D2:

| measurement, RB universe, target seasons 2018–2024, n = 919 | value |
|---|---|
| `rzsnap_known` agrees with "is **not** a rookie" | **99.89%** |
| P(unknown \| rookie) | **1.000** |
| P(rookie \| unknown) | 0.988 |
| mean `games_1`, known vs unknown | 10.37 vs **0.06** |

And then the part that is not about rookies at all — the flag measured **among veterans only**, by
target season:

| target season | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | … | 2024 |
|---|---|---|---|---|---|---|---|---|---|---|
| veteran `rzsnap_known` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.869 | **1.000** | **1.000** | | **1.000** |

`participation` begins in 2016 and the training window begins in 2012. **Inside the veteran design
matrix the flag is therefore a pre-2017 / post-2017 indicator — a time dummy — and what it is fitting
is an era shift in carries per game, not a coverage confound.** It is bookkeeping wearing a factor's
clothes, and it beat both treatments.

**This is not confined to batch 7.** The same geometry is already in a published result:

| batch | control flag | source starts | covers the 2012+ training window? | result |
|---|---|---|---|---|
| 3 | `sep_known_1` (NGS separation) | 2016 | **no** | **+0.0584, p = 0.056, MARGINAL-HARMFUL** — and it VOIDed S1 |
| 3 | `expl_known` (pbp explosive rush) | 2009 | **yes** | **−0.0058, p = 0.44, NULL** — the control behaving correctly |
| 7 | `rzsnap_known` (participation) | 2016 | **no** | **−0.1239, p = 0.038** — the largest effect in its family |
| 7 | `snap_known` (snap_counts) | 2013 | **nearly** (0.00 in 2012–13, 0.99 from 2014) | −0.0478, p = 0.12, and it voids P1 |
| 7 | `i5_known`, `yac_known` (pbp 2009, weekly 2006) | 2009 / 2006 | **yes** | +0.0005 and −0.0029, both NULL |

**The pattern is exact: every flag whose source covers the training window is null; every flag whose
source starts inside it is not.** That is a property of the calendar, not of the football.

**What follows, and it is a design change I am not making unilaterally.** Batch 3's registered rule
"first target season = source first season + 2" guarantees the arm differs from the primary in at
least one *training* season — but it leaves four or five **uncovered** training seasons inside the
fit, which is what creates the dummy. The fix is to restrict the arm's **training** window to seasons
with coverage, not only its target window. That is registered to `strategist` as an amendment
request; it is not applied here and no batch-7 grade is changed by it.

### (3) Every arm that helped, helped on the players nobody drafts — and hurt on the ones they do

The registered endpoints already say this (E1a negative, E1b positive). The post-hoc split D1 says
where it physically sits. **Same sign for every arm, across three unrelated sources:**

| arm | source | ADP board (51 players/season) | off-board (80 players/season) |
|---|---|---|---|
| Z1 RZ-20 snap rate | participation | **+0.877 (+1.35%)** worse | −0.659 (−1.73%) better |
| Z2 inside-5 snap rate | participation | **+0.716 (+1.10%)** worse | −0.537 (−1.41%) better |
| P1 prior snap share | snap_counts | **+0.425 (+0.65%)** worse | −0.329 (−0.86%) better |
| L2 group late lift | weekly stats + draft | **+0.299 (+0.46%)** worse | −0.154 (−0.40%) better |

L2's source covers the whole training window, so **this is a separate defect from (2)** and it is not
explained by the era dummy. Batch 1 §1(3) found this shape once and batch 2 gave it the name
BOARD-NEUTRAL. **Batch 7 finds it is not an occasional trap — it is what a usage feature does at RB
by default.** A snap-share or red-zone-presence variable sharpens the model where role is uncertain,
which is exactly the population a ten-team draft never reaches, and adds noise where role is already
known, which is exactly the fifty players it does.

### (4) Two of the sweep's own claims point the wrong way when tested directly

**N17.** McFarland: *70% of league-winning RB seasons came from backs at ≥40% receiving share.*
Tested as a target-projection input, both specifications are **MARGINAL-HARMFUL** — the continuous
share **+0.0295 [+0.0094, +0.0503], p = 0.021**, and his own ≥40% cut **+0.0224 [+0.0074, +0.0385],
p = 0.022**. Both CIs exclude zero on the wrong side of it. Neither is BH-significant at m = 80 or at
m = 16, so neither is graded HARMFUL — but the direction is consistent across two independent
parameterisations and it is not what the claim predicts.

The reconciliation is almost certainly that his statistic is **conditioned on the outcome**: it
describes the composition of seasons that already turned out to be league-winners. That is a
different object from "receiving share predicts next season's targets", and this project has been
wrong in exactly this way before — `CLAUDE.md` §7's retired ceiling claim and the calibration prior
that four of five registered prediction sets over-credited a situation story.

**N16.** Barfield: YAC per reception is *the clear best efficiency stat for RBs in the pass game*,
with a separate summary quoting r = 0.421. Fitted as a covariate on the model's own `ypr` rate:
**+0.0028 [−0.1082, +0.1027], p = 0.96.** A flat zero on 11 seasons, with the coverage control also
flat. Not underpowered, not blocked — measured, and nothing there.

---

## 2. The registered table, in full

**E1a** = out-of-sample component MAE, arm − primary, paired by season, season-block bootstrap,
4,000 reps. **Negative = better.** **E1b** = the same MAE on the ADP board, 7 seasons, a required
direction check and not the significance test. **E2** = ADP-board Spearman, arm − primary. **E4** =
the deficit itself, `adpsub_rho_model − adpsub_rho_b1_adp`, primary **−0.0523**.

| # | arm | comp | n | **E1a** [95%] | p | % | E1b | E2 | **E4** | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Z1 RZ-20 snap → carries | carries | 7 | **−0.0576** [−0.1320, +0.0271] | 0.236 | −0.12% | **+0.877** | −0.0038 | −0.0561 | NULL · **interpretation VOID** |
| 2 | Z2 inside-5 snap → carries | carries | 7 | **−0.0533** [−0.0990, −0.0004] | 0.101 | −0.11% | **+0.716** | −0.0036 | −0.0559 | MARGINAL |
| 3 | Z3 RZ-20 snap → targets | targets | 7 | +0.0097 [−0.0026, +0.0280] | 0.323 | +0.07% | +0.054 | −0.0007 | −0.0530 | NULL |
| 4 | **Z1c CONTROL** coverage flag | carries | 7 | **−0.1239** [−0.2143, −0.0448] | 0.038 | −0.25% | +0.493 | −0.0010 | −0.0533 | MARGINAL — **and see §1(2)** |
| 5 | G1 inside-5 conversion → tdpc | rush_tds | 11 | −0.0010 [−0.0021, +0.0002] | 0.144 | −0.05% | −0.004 | +0.0008 | −0.0515 | NULL |
| 6 | **G1p CONTROL** binomial placebo | rush_tds | 11 | +0.0001 [−0.0013, +0.0020] | 0.893 | +0.01% | +0.001 | +0.0002 | −0.0521 | NULL |
| 7 | **G1c CONTROL** coverage flag | rush_tds | 11 | +0.0005 [−0.0009, +0.0018] | 0.546 | +0.02% | +0.000 | +0.0003 | −0.0520 | NULL |
| 8 | Y1 YAC/rec → ypr | rec_yards | 11 | +0.0028 [−0.1082, +0.1027] | 0.962 | +0.00% | −0.003 | +0.0002 | −0.0521 | NULL |
| 9 | **Y1c CONTROL** coverage flag | rec_yards | 11 | −0.0029 [−0.0113, +0.0061] | 0.548 | −0.00% | −0.026 | +0.0001 | −0.0522 | NULL |
| 10 | S1 receiving points share | targets | 11 | **+0.0295** [+0.0094, +0.0503] | 0.021 | +0.21% | +0.034 | −0.0013 | −0.0536 | **MARGINAL-HARMFUL** |
| 11 | S2 ≥40% bin (McFarland) | targets | 11 | **+0.0224** [+0.0074, +0.0385] | 0.022 | +0.16% | +0.018 | +0.0007 | −0.0516 | **MARGINAL-HARMFUL** |
| 12 | P1 prior snap share | carries | 10 | −0.0752 [−0.1570, +0.0172] | 0.146 | −0.15% | **+0.425** | −0.0025 | −0.0548 | **RESTATEMENT** |
| 13 | P2 ≥60% gate (McFarland) | carries | 10 | −0.0008 [−0.0525, +0.0450] | 0.976 | −0.00% | −0.004 | −0.0002 | −0.0525 | NULL |
| 14 | **P1c CONTROL** coverage flag | carries | 10 | −0.0478 [−0.1007, +0.0041] | 0.123 | −0.10% | +0.198 | +0.0001 | −0.0522 | NULL |
| 15 | L1 his own late/early ratio | carries | 11 | −0.0503 [−0.2174, +0.1111] | 0.588 | −0.10% | +0.029 | −0.0049 | −0.0572 | NULL |
| 16 | L2 group late lift, round × year | carries | 11 | −0.0397 [−0.2893, +0.1914] | 0.765 | −0.08% | +0.299 | −0.0007 | −0.0530 | NULL |

**BH at q = 0.10, campaign m = 80: nothing passes.** The smallest p-value in the batch is 0.021, and
rank-1 BH at m = 80 requires p ≤ 0.00125. **At the batch denominator m = 16 nothing passes either**
(rank-1 threshold 0.00625). Reported so nobody has to wonder whether the campaign correction is what
killed a result: it is not.

**The too-good trigger did not fire.** The largest |E1a| in the batch is 0.25% of the primary's own
error, against a 2% escape hatch.

---

## 3. The independence gate — computed before any result, reported for every arm

Each arm's declared column regressed on **the model's own existing RB feature set**
(`carries_pg_w, cshare_w, gshare_w, evidence, age, age2, ppg_w, experience, tgt_pg_w, tshare_w`), on
the ADP board. **R² ≥ 0.90 ⇒ RESTATEMENT**, whatever the p-value.

| column | R² vs the model's own columns | R² vs `age, age2, experience` |
|---|---|---|
| `snapshare_w` | **0.9014 — GATE FAILED** | 0.2186 |
| `rz20_snap_w` | 0.8762 | 0.2106 |
| `i5_snap_w` | 0.8185 | 0.1778 |
| `recpts_share_w` | 0.7586 | 0.0177 |
| `recpts_ge40` | 0.5560 | 0.0495 |
| `snap_ge60_w` | 0.5462 | 0.1375 |
| `yac_per_rec_w` | 0.4384 | 0.2667 |
| `i5_conv_w` | 0.1425 | 0.0205 |
| `late_lift_grp` | 0.1879 | 0.1107 |
| **`late_ratio_w`** | **0.0402** | **0.0095** |

Two things the dispatch specifically asked to be established rather than asserted:

- **N18 prior snap share is 90.1% inside the span of columns the model already holds.** It is a
  restatement, and it is graded as one before its p-value is looked at. That answers "324,611 rows,
  unused by any model" cleanly: the rows are unused because the information is already in the model
  by another route (`cshare_w`, `gshare_w`, `carries_pg_w`), not because nobody got round to it.
- **N19 is genuinely new information and is still null.** `late_ratio_w` is 4% explained by the whole
  model and **0.95% explained by age and experience**. The restatement objection the dispatch raised
  is measured and rejected — and the factor is null anyway. That is a stronger negative than a
  restatement would have been: this is not age wearing a disguise, it is a real, independent variable
  that does not predict next-season carries.
- N17 at 0.76 is high but under the gate, so its MARGINAL-HARMFUL sign is reported as measured rather
  than dismissed as collinearity.

---

## 4. Controls, and one place the VOID rule is uninformative

| treatment | its control | ratio | ruling |
|---|---|---|---|
| Z1 (−0.0576) | Z1c (−0.1239) | **215%** | **VOID — the control is more than twice the treatment.** And §1(2) says what the control actually is |
| Z2 (−0.0533) | Z1c (−0.1239), same block flag | **233%** | same reading; not machine-flagged because the registered pairing is Z1c→Z1 |
| P1 (−0.0752) | P1c (−0.0478) | **64%** | **VOID** — and independently RESTATEMENT |
| G1 (−0.0010) | G1p placebo (+0.0001), G1c (+0.0005) | 13%, 48% | **clean.** Neither the shrinkage geometry nor coverage is doing anything. G1 is simply null |
| Y1 (+0.0028) | Y1c (−0.0029) | 101% | **the rule fires and says nothing.** Both numbers are indistinguishable from zero, so a ratio between them is a ratio of two noise draws. Reported as a limitation of the rule, not as "YAC is a coverage artifact" |

**G1p is the one control that worked exactly as designed.** Batch 3 discovered the empirical-Bayes
geometry problem post-hoc; batch 7 registered the placebo up front, and it came back **+0.0001,
p = 0.89** — the shrinkage geometry buys nothing, so G1's small negative is signal-shaped even though
it is null. That is what a pre-registered control is for.

---

## 5. Data findings — three of them correct the dispatch's own source

Measured before any arm was fitted, per `CLAUDE.md` §11 ("football claims must be grounded in
verifiable data from the pipeline").

| claim | measured | consequence |
|---|---|---|
| N16 from `pbp` `yards_after_catch`, **1999+** | **`pbp` in `nfl.db` has no `yards_after_catch` column** — 24 columns, none of them YAC — and the table starts **2009**, not 1999 | routed to `player_weekly_stats.receiving_yards_after_catch`. **Reported rather than silently worked around** |
| the same | that column is **identically 0 for 2000–2005**; 1999 holds 378 yards league-wide against 1,957 RB receptions; real from **2006** | YAC is a **2006+** feature. Not binding here (features start 2012) but it would be binding for any deep-sample design |
| N14 `participation` × `pbp`, 2016+ | correct: 2016–2025, 478,989 rows. `offense_players` is empty on ~8.5% of rows in 2016–2022 — **every one a non-scrimmage play.** On rush/pass plays the missingness is **0.0000** | usable |
| N18 `snap_counts`, 324,611 rows, unused | correct, **and keyed on PFR ids, not gsis** | joined through `player_ids`; **99.34% of RB player-seasons match, 99.55% snap-weighted**. The crosswalk is not in the rebuild path — flagged to `data-ops` |

**Nothing was blocked.** All six factors were computable from `nfl.db` with no new ingest, which is
itself a finding: the sweep's RB block is entirely testable today and now has been.

---

## 6. Guardrails actually applied

| check | evidence |
|---|---|
| **Look-ahead** (§6.1) | every batch-7 source goes through a gate asserting `max(season) ≤ cutoff` and logging to the panel's own audit; per-target-season assertion that max feature cutoff < target |
| **Zero season-N reads** | **no batch-7 block reads season N at all.** Every arm asserted `n_preseason_proxy_reads == 0` as a `RuntimeError` and every arm returned 0 |
| **Reproduction** | the batch-7 primary reproduces batch 3's RB primary `mae_carries` to **+0.000000e+00**. Asserted in the run and printed, not assumed |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0 |
| **Multiple comparisons** (§6.3) | BH at campaign m = 80, q = 0.10 and 0.05; batch m = 16 reported as secondary. Nothing passes at either |
| **Holdout** | 2025 sealed at the SQL gate and excluded at load in every batch-7 source. **Not opened** |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n throughout |
| **Uncertainty** | every point estimate above carries a 95% interval. No bare point estimates |
| **No shared module edited** | `pos_data.py`, `pos_model.py`, `pos_eval.py` untouched — three other factor agents were working the same checkout |

---

## 7. What this batch does NOT license

- **It does not license a sentence on the draft board about red-zone role, snap share, receiving
  share, or late-season trends.** Batch 2 §7's insight-string rule stands: nothing graded, so nothing
  renders. A sentence asserting a mechanism the model does not price is a false claim about our own
  product regardless of whether the football is right.
- **It does not close registry #10** (red-zone *touches*). Batch 7 tested *presence*. They are
  different objects and only one of them has now been measured.
- **It does not establish that N15 is independent of `ff_opportunity`'s xFP**, which batch 6 tested
  concurrently. The overlap was declared in the pre-commitment and no independence was claimed.
- **It does not change any batch-3 grade.** §1(2) is a methodological finding about batch 3's control
  design, registered to `strategist`; batch 3's published numbers stand until it rules.

---

## 8. Who checks this, because I do not check my own work

| claim | independent check |
|---|---|
| the campaign family, the m = 80 denominator, and the coverage-flag-as-time-dummy amendment | **`strategist`** — thread opened this session |
| every number in this document | **`fable`**, at maximum effort, separate budget |
| `participation` red-zone snaps, the PFR→gsis crosswalk, and the YAC 2006 floor in the rebuild path | **`data-ops`** — thread opened |
| the six ledger dispositions | **`librarian`** — thread opened |
| shipping anything that grades | **`backend`** — nothing grades, so there is nothing to ship |
