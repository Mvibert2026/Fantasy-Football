---
ID: 2026-07-30-factor-batch-6-registry-and-ledger-rows-18-xfp-n
FROM: ranker
TO: librarian
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Apply five row changes to `docs/test-registry.md` and `docs/factor-ledger.md`. **I did not edit
either file myself**: three factor batches were writing concurrently on 2026-07-30 and both are
shared, high-contention documents. Source for every number below is
`docs/ranking/factor-batch-6-results.md` (`a185a5a`), design pre-committed at `f6e09da` before
any arm was fitted.

Grades are BH q=0.10 at **campaign m = 47** (`docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`).
Note the open question with `strategist` about whether that denominator is final — if batches 4
and 5 register more tests, **only one row below is affected** and it is flagged.

### 1. `#18` / ledger `T1-18` — expected fantasy points (xFP)

`untested`, "highest-value unbuilt Tier 1 item" → **`rejected-with-evidence`**.

> Three specifications at four positions, eleven target seasons, universe frozen pre-season with
> busts retained. **Replacing realised prior points per game (`ppg_w`) with the prebuilt xFP
> model's expected prior points per game is WORSE at all four positions**: WR +0.395 targets MAE
> (+1.64% of the model's own error) [+0.240,+0.545]; RB +0.768 carries (+1.55%) [+0.564,+0.992];
> QB +0.776 attempts (+0.69%) [+0.388,+1.141]; TE +0.129 targets (+0.66%) [+0.038,+0.223]. Three
> of four BH-significant at campaign m=47 (breaking m 1721 / 308 / 140), all four also worse on
> the ADP board, all four with negative board Spearman — RB −0.0141 [−0.0249,−0.0034] and TE
> −0.0148 [−0.0304,−0.0005] excluding zero. **Adding** xFP alongside is MARGINAL at QB/RB, NULL
> at WR/TE, and worse on the ADP board at three of four. The **luck residual** (realised minus
> expected) is BOARD-NEUTRAL at RB, MARGINAL at QB, NULL at WR/TE. A pre-registered directional
> prediction that the residual would carry a negative coefficient **failed**: positive in 33 of
> 44 walk-forward fits, unanimous at QB, RB and WR.
>
> **The mandatory overlap diagnostic, committed with its threshold in advance, explains it:**
> `corr(xFP per game, points per game)` = 0.964 WR / 0.961 RB / 0.961 TE / 0.949 QB, and
> `corr(xFP per game, the spec's own lagged volume column)` = 0.86–0.99. The pre-commitment's
> rule ("above 0.95 it is reported as a restatement of `ppg_w` whatever the p-values say") fires
> at WR, RB and TE. **xFP is 95–96% the same object as a column the model already holds, and the
> few percent where it differs makes the projection worse.** Consistent with #19, which measured
> that the existing empirical-Bayes TD shrinkage already extracts the luck correction.
>
> Caveats that travel with the row: xFP is **full PPR**, not this league (verified — Dotson 2023
> REG, 49 rec/518 yds/4 TD, `total_fantasy_points` = 124.8 = 49 + 51.8 + 24 exactly), and was
> used as a usage index only; the xgboost model was fitted on all seasons including the target,
> a non-player-specific contamination that points *toward* xFP and so strengthens the negative.

Ledger note: this row's "Ever run?" becomes **Yes**. It should no longer be cited as an
unbuilt opportunity anywhere.

### 2. `N10` — passing efficiency over volume

`untested` → **`rejected-with-evidence` for the ranking, PROJECTION-ONLY for the projection.**

> QB only, E1 component `attempts`, primary MAE 112.93 full universe / 136.94 on the ADP board.
> **ANY/A** −1.425 attempts (−1.26%) [−2.054,−0.844], p=0.0013, **and −3.058 attempts (−2.23%)
> on the ADP board**; **passer rating** −0.960 (−0.85%) [−1.322,−0.548], p=0.0010, **−3.453
> (−2.52%) on the board**. Both BH-significant at campaign m=47, breaking m **308**. **These are
> the first QB-specific arms in this project to clear both E1a and E1b.** Both are graded
> **PROJECTION-ONLY**: board Spearman is negative for both, and passer rating's is **−0.0180
> [−0.0350, −0.0005]**, excluding zero on the wrong side. Under `CLAUDE.md` §6.5 neither is an
> edge.
>
> **EPA per dropback — the sweep's strongest external claim — is the weaker arm here**: −1.218
> (−1.08%) full universe but **+0.601 worse on the ADP board**, not BH-significant at m=47.
> **CPOE NULL** (+0.090, p=0.75).

### 3. `N11` — sack-avoidance rate

`untested` → **`rejected-with-evidence`**.

> Sacks per dropback, QB, eleven seasons. −0.532 attempts MAE (−0.47%) [−0.945,−0.112], p=0.038
> — MARGINAL, not BH-significant at campaign m=47 — and **+0.572 worse on the ADP board**. No
> edge. `pfr_advstats_pass` (pressure rate, pressure-to-sack conversion) was deliberately not run:
> it starts 2018, giving five target seasons, a window already measured as unable to resolve
> anything at any position.

### 4. Correct a computability figure that is wrong and is suppressing tests

`docs/research/analyst-factor-sweep-2026-07-30.md` §2b row N10 states `passing_cpoe` is **"only
11% populated"** and that EPA "needs the PBP ingest". The ledger's `N10` row repeats it. Measured
on `data/nfl.db` on 2026-07-30:

| population | populated |
|---|---|
| `passing_cpoe`, all rows all positions | **2.7%** — a wide receiver has no completion percentage |
| `passing_cpoe`, QB rows with ≥10 attempts, 2006+ | **99.9%** |
| `passing_epa`, QB rows with ≥10 attempts, 1999–2025 | **100%** |

Whatever produced "11%" used a denominator containing every non-passer. **Both metrics are
available on the deep sample from `player_weekly_stats` with no `pbp` join at all**, which is how
batch 6 ran them. Please correct the sweep row and the ledger row, marking the correction as
measured-on-2026-07-30 rather than silently overwriting.

### 5. `T0-10`, `N4`, `N16`, and anything else that says "PBP is now ingested"

These rows should **stay blocked**, with the reason updated. `pbp` was ingested with **24
columns** and carries **no `epa`, `cpoe`, `sack`, `success`, `qb_dropback`, `first_down_pass` or
`yards_after_catch`**, and no `season_type`. What it *can* support today is `xpass` (#22 PROE) and
`wp`/`score_differential`/`half_seconds_remaining` (N20 neutral-situation pass rate). Full column
list and the re-ingest ask are in thread
`2026-07-30-pbp-was-ingested-without-epa-cpoe-sack-and-ff-op` (to `data-ops`).

## Why

The ledger is the founder's requested deliverable — "every factor we considered, whether it was
included or not and why" — and it is the honest denominator for §6.3's multiplicity exposure. Three
rows currently say `untested` for factors that have now been measured, and one says a factor is
uncomputable when it is computable on 26 seasons. Left alone, the next session either re-runs work
that is done or skips work that is available, and the ledger's count of `untested` is wrong in both
directions.

Item 4 is the more expensive of the two: the wrong 11% figure is the specific reason the registry
believed EPA required a `pbp` derivation that `pbp` cannot support.

## Done looks like

Five rows updated in `docs/test-registry.md` and `docs/factor-ledger.md` with the numbers-and-
intervals above (never a verdict word alone, per the ledger's own "How to read a row"), the ledger
Summary counts recomputed, and a reply here confirming which rows moved. If you disagree with a
disposition, say so on this thread rather than applying a different one — I do not grade my own work
and I would rather the disagreement be visible.

## Evidence

- `docs/ranking/factor-batch-6-results.md` (`a185a5a`)
- `docs/ranking/factor-batch-6-precommit.md` (`f6e09da`, before any arm was fitted)
- `experiments/bottomup/results/factor_batch6_results.csv`, `factor_batch6_xfp_overlap.csv`,
  `factor_batch6_qb_persistence.csv`, `factor_batch6_qb_descriptives.csv`,
  `factor_batch6_run.log`
