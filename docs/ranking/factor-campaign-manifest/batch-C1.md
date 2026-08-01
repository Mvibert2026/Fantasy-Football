# Batch C1 — the factor **inclusion** test against ranking v2

**Registered by `ranker`, 2026-08-01, before any arm was fitted and before any evaluative number
was computed.** Mandate: `docs/founder-requests/FR-2026-08-01-need-an-inclusion-test-run-candidate-factors-as.md`.
ADR-069 binds: absolute quality against realised outcomes is the steering metric; consensus is
neither an input nor a development signal, and §6.5's four-baseline gate is a release gate run
later by someone else.

## Why this batch exists and why it is not a repeat of batches 1–7

Batches 1–7 tested ~90 factor arms against a **consensus-derived** primary. A factor can be
genuinely informative and still return NULL there, because consensus had already priced it. **v2
contains no consensus** (`experiments/bottomup/v2/`, batch-B1). The same factor now faces a model
with none of that knowledge baked in, so the old nulls are **not** evidence about inclusion in v2
and are not cited here in either direction.

**The known hazard, stated before measurement:** a model with less knowledge baked in has more room
for anything correlated with outcomes to look useful, so the expected hit rate is **higher** than
the old campaign's and a high hit rate is a warning, not a result. Two instruments hold this
honest: the campaign-level BH denominator, and **arm F0, a registered placebo** whose WIN rate is
the direct measurement of how easily this harness manufactures a win.

## The pinned primary (control)

**v2 with the G0 games arm — pinned, and no re-grade is owed.**
`experiments/bottomup/ranking_versions/v2.json`'s registered default is G0. G1/G1a were rejected by
their own rules in batch-B1. **G2a's `strategist` ruling landed during this batch's registration:
ADMIT-WITH-CONDITION, and the conditions C1–C5 are not satisfied** (thread
`2026-08-01-g2a-week-1-status-as-of-ruling-and-v2-ship-revie.md`), whose operative sentence is:

> "Until conditions C1/C2/C3 return PASS, v2's games arm stays G0. No session may flip `v2.json`
> on the ruling reply alone."

So every cell in this batch is graded against **G0**, that is recorded in the `games_arm` column of
`experiments/bottomup/results/factor_c1_contrasts.csv` per row, and no conditional caveat is
carried.

**No C1 arm reads week-1 roster rows, and this is asserted rather than believed.** Every arm runs
with `allow_preseason_proxy=False` and asserts `n_preseason_proxy_reads == 0` per position per
season. That matters because the same ruling established that `pos_data._ROSTER_SQL` filters
`week = 1 AND game_type = 'REG'` and `_STATUS_AVAILABLE` includes `INA` — so week-1 status is
**kickoff-dated, not cutdown-dated**, contrary to five documents that say otherwise. Nothing in C1
inherits that defect because nothing in C1 touches that source.

### Matched controls — one per feature window

An arm whose source starts late must be fitted on a shorter training window, and a shorter window
degrades the model on its own. Comparing such an arm to the full-window control would confound the
factor with the window. **Each arm is therefore differenced against a control run with an identical
`first_feature_season` and an identical target span.**

| control | `first_feature_season` | targets | used by |
|---|---|---|---|
| **CTRL-A** | 2012 | 2018–2024 (7) | F0, F2, F3, F6 |
| **CTRL-B** | 2015 (`snap_counts` 2013+) | 2018–2024 (7) | F1 |
| **CTRL-C** | 2017 (`participation`/`ngs_receiving` 2016+) | 2019–2024 (6) | F4, F5 |

CTRL-A is batch-B1's G0 re-run; whether it reproduces `ranking_v2_G0_cells.csv` is a descriptive
reproducibility check, contributing 0 tests.

## m_b = 23 — the graded cells  (raised to **38** by Amendment 1 below)

Every arm differs from its matched control by **exactly one thing**: one factor's column block
added to that position's volume feature spec (or, for F6, one constant). Availability arm, rate
specs, bonus curves, scoring, ordering path and evaluation population are inherited unchanged.

| arm | factor | ledger row | columns added | source | positions | cells |
|---|---|---|---|---|---|---|
| **F0** | **PLACEBO — seeded N(0,1) noise** | n/a (negative control) | `placebo_noise` | none | QB RB WR TE | 4 |
| **F1** | Offensive snap share, recency-weighted | T0-9 / N18 | `snapshare_w`, `snap_known` | `snap_counts` 2013+ | RB WR TE | 3 |
| **F2** | Red-zone (inside-20) usage share of team | T0/T1 red-zone usage | `rz_use_share_w`, `rz_use_known` | `pbp` 2009+ | RB WR TE | 3 |
| **F3** | Expected fantasy points per game **and** the realised-minus-expected residual | T1-18 | `xfp_pg_w`, `xfp_resid_pg_w`, `xfp_known` | `ff_opportunity` 2006+ | QB RB WR TE | 4 |
| **F4** | NGS average separation (lag 1) | N5 | `sep_1`, `sep_known_1` | `ngs_receiving` 2016+ | WR TE | 2 |
| **F5** | Route participation & targets per route run — **LABELLED PROXY** | T1-16 / T1-17 / N3 | `tprr_w`, `rpg_w`, `routes_known` | `participation` 2016+ | RB WR TE | 3 |
| **F6** | Steeper recency weighting of prior seasons: `LAG_WEIGHTS` 0.55/0.30/0.15 → **0.70/0.22/0.08** | `CLAUDE.md` §6.4 | none — one constant | n/a | QB RB WR TE | 4 |

**Σ m_b = 23, raised to 38 by Amendment 1. Campaign denominator `M_campaign` = 92 + 38 = 130** (batches 5/6/7 = 56, M2 = 16,
B1 = 20; PR-007's 4 sit in their own family per `pr007.md`). BH at q = 0.10.

### Which volume spec each factor enters, fixed now

| position | spec(s) the factor column is appended to |
|---|---|
| WR, TE | `tpg` (targets per game) |
| RB | `carries_pg` **and** `tpg` (the two streams a back's role splits across) |
| QB | `att_pg` **and** `carries_pg` (F0, F3, F6 only) |

F6 changes no spec: it changes the lag-weight vector used to build every recency-weighted feature
and every efficiency `(num, den)` pair. That is deliberately the whole factor — "how far back to
weight" is not a per-column question.

### Positions deliberately excluded, with the reason, before measurement

- **F1 at QB** — a starting quarterback plays ~100% of offensive snaps; snap share is degenerate at
  the position and carries no ordering information that `att_pg_w` does not already hold.
- **F2 at QB** — red-zone *usage share* for a quarterback is his team's red-zone pass rate, a team
  quantity, not a player one.
- **F4 at RB and QB** — `ngs_receiving` qualifies on receiving volume; RB coverage is thin and QB is
  not in the table.
- **F5 at QB** — a quarterback runs no routes.

## Coverage floor, fixed now

An arm is graded **NO DATA** and contributes its cells as ungradeable (still counted in `m_b`) if
fewer than **80%** of the graded population's rows in that cell have a real, non-imputed value for
the factor's `*_known` indicator. Measured after registration, reported per cell.

## Endpoint, population, and the grading rule — identical to batch-B1

- **Endpoint:** Spearman(v2 `proj_points` order, realised season points), per (position, season) —
  the ADR-069 absolute steering metric. **Not** a delta against any crowd.
- **Population:** M-panel veterans (FFC-ADP membership defines the evaluation subset only; the
  column is never a feature and never an ordering input). Rookies and the full universe are
  descriptive. Survivorship: `universe_for` freezes the season-N universe from pre-N information.
- **Look-ahead:** the panel's `feature_gate`/`outcome_gate` and the `WalkForward` audit assertions.
  No hand-rolled cutoffs. Every arm asserts `n_preseason_proxy_reads == 0` — **no arm in C1 reads
  any season-N proxy**, unlike B1's G2a.
- **Holdout:** 2025 sealed, never read. Targets end at 2024.
- **Statistics:** paired season-block bootstrap on the per-season deltas, 4,000 reps, seed
  20260801, 95% CI. **WIN** = CI > 0, **HARM** = CI < 0, else **NULL**. BH at `M_campaign` = 130,
  q = 0.10, reported as the robustness flag on top of the CI verdict.

### The inclusion verdict per factor, fixed now

| verdict | rule |
|---|---|
| **INCLUDE** | ≥1 **BH-robust WIN** cell **and** 0 CI-level HARM cells. The factor is included **only at the positions whose cells won**. |
| **INCLUDE (partial)** | ≥1 BH-robust WIN cell **and** ≥1 CI-level HARM cell at another position. Included at the winning positions only; the harm is reported, not tuned away. |
| **EXCLUDE** | ≥1 BH-robust HARM cell and no BH-robust WIN. |
| **NULL** | no cell clears either way. Reported as *measured no effect at this power*, with the CI half-width quoted — never as evidence of absence. |

A CI-level WIN that does **not** survive BH is **NULL for inclusion** and reported as a hypothesis,
per `CLAUDE.md` §6.3. Weighting is explicitly **out of scope** for this pass: a factor either earns
a place in the design matrix or it does not. No weight is tuned, and no two factors are stacked —
stacking is the next phase and needs its own registration.

## Registered predictions, so the result can surprise

- **F0 (placebo): 0 WIN, 0 HARM.** Any WIN here is a finding about the harness, and it invalidates
  the batch's WIN rate rather than adding to it.
- **F1 snap share:** WIN at RB (snap share is the strongest single role signal for a back and
  `cshare_w` sees only carries); NULL at WR/TE where `tshare_w` already encodes role.
- **F2 red-zone usage share:** NULL-to-WIN at RB, NULL at WR/TE. Registered downside: red-zone share
  is largely a monotone function of overall volume the model already holds, so the likeliest outcome
  is collinearity and no gain.
- **F3 xFP:** WIN at WR and RB; NULL at QB and TE. Registered downside, and it is specific: the
  residual `xfp_resid_pg_w` is a **luck** term whose correct coefficient is negative
  (regression to the mean). If OLS fits it positive on training rows the arm should **harm**, and
  that is the mechanism to report if it does — not a reason to re-tune.
- **F4 NGS separation:** NULL at both. It is an efficiency trait being fed to a **volume** model,
  and the external evidence puts it below prior fantasy points itself.
- **F5 routes / TPRR:** WIN at WR, NULL at TE and RB.
- **F6 steeper recency:** NULL at WR/RB/TE, possible WIN at QB — the position where this project has
  already measured a regime shift. Registered downside: a steeper decay discards evidence and should
  raise variance where roles are stable.

**Registered hit-rate prediction:** **2–5 WIN cells of the 19 non-placebo cells (10–26%).** If the
observed rate lands far above that band, the batch reports it as a hazard to interrogate — starting
with F0 and with the collinearity of the winning columns — and **not** as a breakthrough.

## Amendment 1, 2026-08-01 — the `_known` control arms, registered before any arm was fitted

**Nothing had been computed when this was written.** No arm had been run; the only numbers seen
were a wall-clock timing (a G0 TE/WR run at 5–6 s) and table row counts. This amendment is a
methodology correction arriving from the G2a ruling, not a response to a result.

**The defect being pre-empted.** Every factor in F1–F5 carries a `*_known` coverage indicator, and
each of those indicators is a **presence/join condition**, not a measurement:

| factor | `*_known` is really | why it can carry signal on its own |
|---|---|---|
| F1 | did the `snap_counts` → `player_ids` PFR→gsis crosswalk resolve, and did he take a snap | a join failure is indistinguishable from "did not play" |
| F2 | did he touch the ball inside the 20 in any lag season | zero red-zone work and "not in the league" are the same row |
| F3 | does `ff_opportunity` have him | presence is a proxy for having been on an NFL field |
| F4 | **was he in the NGS *qualified* set** | `ngs_receiving` qualifies on receiving volume — this indicator is close to a volume gate wearing a tracking-metric name |
| F5 | does `participation` have him running routes | same presence geometry |

This is the geometry **batch 7 measured at 215% of its own treatment effect** and **batch 3 wrote a
VOID rule for**, and the G2a ruling notes nobody ran the corresponding `wk1_known` control there.
It is the single most likely route to a false INCLUDE in this batch, which is exactly what the
founder's hazard warning is about.

**The fix: five paired control arms, registered now.** For each of F1–F5, an arm **F1k…F5k** that
appends **only** that factor's `*_known` indicator(s) to the same volume specs, at the same
positions, against the same matched control. No factor value column. Identical grading.

| arm | columns added | positions | cells |
|---|---|---|---|
| **F1k** | `snap_known` | RB WR TE | 3 |
| **F2k** | `rz_use_known` | RB WR TE | 3 |
| **F3k** | `xfp_known` | QB RB WR TE | 4 |
| **F4k** | `sep_known_1` | WR TE | 2 |
| **F5k** | `routes_known` | RB WR TE | 3 |

**m_b: 23 → 38. `M_campaign`: 115 → 130** (56 + 16 + 20 + 38). Controls are counted in the family
rather than declared descriptive, because each one is graded and each one can change a verdict.

### The VOID rule, fixed now

**A treatment cell's WIN is VOID if the paired `*k` cell at the same position is itself a WIN at
the CI level.** Deliberately asymmetric: voiding needs only the loose bar, claiming needs the
BH-robust one. A VOID cell counts as neither WIN nor HARM in the factor verdict, and
**INCLUDE requires a BH-robust WIN that is not VOID.**

If a `*k` arm wins where its treatment arm does not, that is a finding in its own right — the
project has been carrying a coverage indicator that outperforms the metric it was attached to —
and it is reported as such rather than quietly dropped.

**Registered predictions for the control arms:** F4k WINs (the NGS qualification threshold is a
volume gate); F1k, F3k and F5k NULL; F2k NULL. If F4k wins and F4 does not, the honest report is
that NGS separation contributed nothing and its *coverage flag* was the signal.

## Scope notes

No arm reads consensus, ADP or ECR in its ordering path. No arm reads a season-N proxy. No weights
are tuned. No factors are stacked. The 2025 holdout is not opened, and nothing in this batch would
warrant opening it — a result that appears to warrant it stops and escalates to the founder per
`CLAUDE.md` §6.3.
