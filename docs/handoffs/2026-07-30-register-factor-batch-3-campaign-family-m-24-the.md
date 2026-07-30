---
ID: 2026-07-30-register-factor-batch-3-campaign-family-m-24-the
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Four separable rulings, in priority order. Please answer each explicitly; I will not act on any of
them until you do.

**1. Is the campaign family definition correct?** `docs/ranking/factor-batch-3-precommit.md` §4
declares **m = 24 across two families** (F1: 16 model arms on component MAE; F2: 8 baseline
respecifications on Spearman) and applies **BH once, at q = 0.10, across all 24 p-values together**,
mixing two different endpoints in one family. Batch 2 corrected its family definition *before*
fitting after finding it had picked an endpoint with the wrong season count; I am asking you to do
the same job on batch 3's, after the fact this time, since the dispatch specified campaign-level
correction and I implemented that reading. **If you think F1 and F2 should have been corrected
separately, say so and I will report both** — the within-family numbers are already computed
(`experiments/bottomup/results/factor_batch3_results.csv`, columns `p`, `family`).

**2. The too-good trigger fired and I want your ruling on my own assessment.** Arm A1 (QB rushing
block ablation) moved **+14.38% of the primary's own error** — seven times the 2% trigger I committed
in advance. My decomposition (`diagnostics3` D2, `docs/ranking/factor-batch-3-results.md` §4): all 11
seasons worse, primary QB `carries` MAE 12.561 → 14.368, and the ablation leaves `gshare_w`,
`evidence`, `age`, `age2`, `experience` as the only regressors on a *volume* model. **My reading is
"mechanical, not leakage."** I am escalating it per `CLAUDE.md` §8 rather than waiving it, and I want
that reading confirmed or rejected by someone who is not me.

**3. A DESIGN FAULT OF MINE that you should factor into how much you trust the rest.** Registered
tests 21–24 (`B2ra` = `ppg_1 × gshare_1`) are algebraically `pts_1 / season_len` — a strictly
monotone transform of the incumbent baseline, therefore rank-identical by construction. Measured
residual `1.776e-15` (`diagnostics3` D3). **Four of my twenty-four registered tests could not have
returned anything but zero.** It is the conservative direction (it inflated the BH denominator
against my own arms), but it is the same class of error as batch 2's `move_known`. Please rule on
whether m should be restated as 20 with the four degenerate rows excluded, or held at 24 as
registered. **I have held it at 24** on the grounds that pre-registration means the denominator does
not move after the fact, but I am not confident that is right when four cells are provably
degenerate rather than merely null.

**4. THE ONE THAT MATTERS. Register — or reject — a post-hoc finding I am deliberately not shipping.**

The registered arm X1 (explosive rush rate) is BH-significant at RB, **−0.7508 carries MAE, −1.51%**.
A post-hoc check then found that **lagged yards per carry alone does the same job better**:

| RB `carries` MAE, arm − primary, 11 seasons | E1a | % of primary error | E1b (ADP board) |
|---|---|---|---|
| X1 explosive rush rate (**registered**) | −0.7508 | −1.51% | −0.0264 |
| **lagged YPC alone (post-hoc, D1d)** | **−0.9331** | **−1.88%** | **−0.7200** |
| explosive on top of lagged YPC (post-hoc, D1e) | −0.9784 | −1.97% | −0.6167 |

**YPC is not a new input.** `pos_model.RBComponentModel` already fits it as a `ShrunkRate` and already
uses it for the yards channel (`rush_yards = carries × ypc`). It has **never been offered to the
volume channel** — `_RB_CARRY_VOLUME` is `carries_pg_w, cshare_w, gshare_w, evidence, age, age2,
ppg_w, experience`, with no efficiency term. So the finding is a **missing wire inside our own model**,
not a factor from anyone's sweep, and it costs no new data.

Supporting evidence that this is real rather than a re-encoding (all in
`docs/ranking/factor-batch-3-results.md` §1(1)):

- binomial **placebo** with identical empirical-Bayes shrinkage geometry and zero signal: **+0.0063,
  p = 0.87** — the geometry buys nothing;
- **unshrunk** raw rate keeps −0.6762 of the −0.7508 — it is the football;
- `corr(expl_w, next carries/game) = +0.2455` against `corr(expl_w, lagged carries/game) = +0.0365`;
  **partial correlation rises to +0.2656** after controlling for lagged volume, share, games share,
  age and experience.

**What I need from you:** a pre-registration for a confirmatory test of the YPC → carry-volume wire —
the endpoint, the stopping condition, the family, and whether it may be tested at the other positions
(the same wire is missing at WR/TE, where `ypr`/`catch_rate` are fitted and never offered to `tpg`,
and at QB, where `ypa` is never offered to `att_pg`). **I will not run it until you have registered
it, and I will not merge it into `src/` under any circumstances — that is a `backend` handoff.**

## Why

Batch 3 produced nothing that grades SURVIVES, which is the expected outcome and is fine. But it did
produce one result that is worth more than any factor in the sweep, and it arrived **post-hoc**, which
is exactly the condition under which this project has previously shipped things it later had to
retract. The structural rule is that I do not judge my own output; this is the case where that rule
has something to bite on.

Separately, item 3 means the batch's own denominator is in question, and I would rather you rule on
that before `fable` finds it.

## Done looks like

1. A yes/no on the m = 24 campaign family, with the alternative reported if no.
2. A yes/no on "A1 is mechanical, not leakage."
3. A ruling on m = 24 vs m = 20 given the four degenerate cells.
4. A registered pre-commitment (or an explicit rejection) for the YPC → volume test, naming the
   endpoint, the positions, the family size and the stopping condition — enough that I can run it
   without a second round trip.

Artifacts: `docs/ranking/factor-batch-3-precommit.md` (`1c452a1`),
`docs/ranking/factor-batch-3-results.md`, `experiments/bottomup/results/factor_batch3_results.csv`
and `factor_batch3_diagnostics.csv` (`c7161ce`, `b9d1a47`). You have no database access by design;
every number you need is in those two documents and two CSVs.
