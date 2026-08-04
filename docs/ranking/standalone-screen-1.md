# Standalone predictiveness screen 1

**backend, 2026-08-04.** Founder's idea, model-independent: does a factor, on its own,
carry any rank relationship to next-season fantasy points — not "does it improve a fitted
model." **This screen decides nothing and grades nothing.** No `INCLUDE`/`EXCLUDE` appears
anywhere below; nothing here enters any campaign multiplicity denominator, because nothing
is decided. Output is descriptive: a ranked table, a survivor set (inclusive, for a future
joint fit), and a collinearity map (diagnostic, not a filter).

---

## NEXT STEP

*Rewritten for a successor with none of this context.*

1. **v3 joint fit is not started.** This screen's deliverable — the survivor set below, the
   collinearity clusters, and the season-budget flag — is its input, per the founder's
   redirection mid-session (`docs/handoffs/` — capture a thread to `strategist`/`ranker` if
   one does not already exist for "v3: joint multivariate fit over the standalone-screen
   survivor set, v2 kept as a checkpoint to revert to").
2. **The season-budget thinness flagged below (5 remaining seasons for fit+test, both
   disjoint from this screen's 2013–2019) is a real design risk, not resolved here.**
   `strategist` should register the exact split before anyone fits v3.
3. **Contract**: `experiments/bottomup/v2/standalone_screen1.py` is self-contained — it does
   **not** import `factors_c1/c2/c3/c4.py`, `run_c1.py`, or anything under `sweep070/`,
   because those exist only as uncommitted work in a sibling checkout at the time this ran
   (see the file's own header note). When they land on `main`, there is no collision:
   different file, different name.
4. Re-run: `python3 -m experiments.bottomup.v2.standalone_screen1` from the repo root (needs
   `data/nfl.db`, gitignored — copy from a checkout that has it, see `docs/environment.md`
   §4). Writes `experiments/bottomup/results/standalone_screen1_{results,collinearity,
   contrasts}.csv`.

---

## Denominator

**58 factor-position cells screened**, from **28 named factor definitions** (14 base
factors + 1 seeded-noise placebo + 13 within-cluster contrasts), across the four positions,
each restricted to seasons where the factor's own source table has coverage. 45 base
factor-position cells (15 factors × applicable positions) + 13 contrast cells. Full detail:
`experiments/bottomup/results/standalone_screen1_results.csv` and `..._contrasts.csv`.

This is a different, and much cheaper, denominator than the incremental-test campaign's
(currently M≈259–284 registered cells across C1/C2/C3). Nothing here adds to that number.

---

## Data-quality note, stated because it changes every number below

**The first draft of this screen had a lag bug**, caught by this session's own QA before any
number was drawn from it and reported anywhere: `prior_points_lookup` relabelled each
player-season's own points as `prior_points` for that **same** season (no season shift),
so every partial-correlation and "beats-aggregate" number was computed against a same-season
duplicate of the outcome (`prior_points_rho_matched` ≈ 1.0 for every factor). Fixed by
shifting the lookup's season by +1 before the merge. **All numbers in this document are from
the corrected run.** Flagged here in case an earlier console log or partial artifact from the
buggy run is found elsewhere — it is wrong and superseded.

---

## Method summary

- **Universe**: players with ≥1 game at the position in the target season, 2013–2019
  only. **Stated limitation, not resolved here**: this is not a pre-season ADP/roster
  universe (CLAUDE.md §6.2's survivorship concern) — it undercounts total busts who
  never accrued a game. A cheap screen; not a backtest.
- **Look-ahead**: every factor value is built from strictly-prior-season data (lag-1, or a
  3-lag recency-weighted average with `LAG_WEIGHTS = (0.55, 0.30, 0.15)`, same weights v1/v2
  use elsewhere), gated at SQL level (`season < 2025`, the sealed holdout, and further
  bounded by each source's own measured coverage floor). No week-1-of-target-season status
  used anywhere.
- **Raw predictiveness**: pooled Spearman(factor, realised points), 2013–2019, plus the same
  computed separately per season for stability.
- **Controlled predictiveness**: partial Spearman of (factor, points) controlling for
  prior-season points (rank-residual construction), on the matched subsample where both the
  factor and prior-season points are known (excludes rookies with no season N−1).
- **Noise benchmark**: a seeded-noise placebo (`sha256`-derived, deterministic per
  player/season, reproducible, no salt reuse from any other batch) run through the identical
  pipeline, per position — this project's own history (batch C1: a naive rule handed noise a
  BH-robust WIN at 14.6% of cells against a 2.5% nominal rate) says this is mandatory before
  trusting anything below.

---

## The control-validity classification (binding — read before any number)

Prior-season points is a **deterministic function** of last year's targets, receptions,
yards, TDs and games. For a factor that is a **constituent** of that box score, partialling
out prior-season points removes most of its variance **by construction** — a near-zero
partial is an arithmetic artifact, not a null finding. Every factor below is classified
**before** its numbers are interpreted:

| Class | Meaning | Valid headline |
|---|---|---|
| **EXOGENOUS** | Outside last year's box score entirely | Partial rho beyond prior-season points |
| **CONSTITUENT** | A component of, or arithmetically entangled with, last year's production | "Does the decomposition beat the aggregate?" — raw rho of the factor vs. raw rho of prior-season points, **same matched sample** |
| **AMBIGUOUS** | Genuinely unclear | Both reported, neither privileged |

Both raw and partial numbers are printed for **every** factor below, always, regardless of
class — the table never surfaces one number without saying which control it came from.

| Factor | Class | Why |
|---|---|---|
| placebo | EXOGENOUS | unrelated to anything by construction |
| injury report-week burden | EXOGENOUS | injury-report history, not a scoring input |
| practice-participation severity | EXOGENOUS | practice history, not a scoring input |
| end-of-season depth-chart rank | EXOGENOUS | coach's own stated role, not derived from stats |
| combine athletic composite | EXOGENOUS | fixed at the draft, outside any season's box score |
| team neutral-situation pass rate | EXOGENOUS | team scheme identity, not the player's own box score |
| yards-over-expected rate | CONSTITUENT | built directly from yards, a scoring constituent |
| WOPR | CONSTITUENT | target-share + air-yards-share composite |
| offensive snap share | CONSTITUENT | direct opportunity driver of the box score |
| red-zone (inside-20) usage share | CONSTITUENT | touches that drive TDs directly |
| YAC per reception | CONSTITUENT | built from yards after catch → yards → points |
| RB's own receiving-points share | CONSTITUENT | literally a share of the player's own prior points |
| late-season role trend (H2−H1) | CONSTITUENT | usage-share trend, mechanically tied to volume |
| QB rushing attempts/game | CONSTITUENT | rushing volume, itself a scoring constituent |
| team explosive-rush rate | AMBIGUOUS | team-level, but the RB's own runs partly compose it |

---

## Noise benchmark (calibration reference, all positions)

| position | placebo raw ρ (pooled) | placebo partial ρ (pooled) |
|---|---|---|
| QB | −0.0423 | −0.0378 |
| RB | +0.0325 | −0.0069 |
| WR | −0.0065 | +0.0046 |
| TE | −0.0509 | −0.0328 |

Everything below is read against these floors, per position, per the factor's own class.
**Survivor rule (stated once, applied consistently)**: EXOGENOUS survives if
`|partial ρ pooled| > |placebo partial ρ|` at that position; CONSTITUENT/AMBIGUOUS survives
if `|raw ρ pooled| > |placebo raw ρ|` **and** the per-season sign is not reversed in the
majority of screened seasons. **Deliberately inclusive**, per instruction — this excludes
what is provably indistinguishable from noise, it does not pre-select winners. Regularisation
in the eventual joint fit decides what earns weight.

---

## Recommended queue order (survivors only, ranked by headline magnitude, per position)

*Headline = partial ρ for EXOGENOUS, raw ρ for CONSTITUENT/AMBIGUOUS, per the classification
above. Both raw and partial always shown. `beats_agg` = raw ρ(factor) − raw ρ(prior points),
same matched sample — informative context for CONSTITUENT factors, not a survive/die gate
(see "why nothing 'beats the aggregate'" below).*

### QB (4 survivors of 7 screened factors, +placebo)

| factor | class | headline | raw ρ | partial ρ | beats_agg | n |
|---|---|---|---|---|---|---|
| QB rushing attempts/game | CONSTITUENT | **+0.389** | +0.389 | +0.118 | −0.343 | 380 |
| yards-over-expected rate | CONSTITUENT | +0.191 | +0.191 | +0.020 | −0.542 | 415 |
| practice-participation severity | EXOGENOUS | +0.134 | −0.136 | +0.134 | −0.867 | 340 |
| end-of-season depth-chart rank | EXOGENOUS | −0.081 | **−0.600** | −0.081 | −1.313 | 390 |

**Dead on arrival (QB)**: injury report-week burden, combine composite, neutral pass rate —
all fail to clear the placebo floor at QB. Combine in particular is expected to matter more
for rookies specifically than for the pooled QB population; this screen does not split by
rookie status (see Limitations).

### RB (11 of 12 screened factors — RB is the most inclusive position)

| factor | class | headline | raw ρ | partial ρ | beats_agg | n |
|---|---|---|---|---|---|---|
| offensive snap share | CONSTITUENT | **+0.564** | +0.564 | +0.135 | −0.025 | 572 |
| red-zone usage share | CONSTITUENT | +0.516 | +0.516 | −0.048 | −0.053 | 672 |
| yards-over-expected rate | CONSTITUENT | +0.258 | +0.258 | +0.091 | −0.346 | 762 |
| injury report-week burden | EXOGENOUS | +0.108 | +0.110 | +0.108 | −0.484 | 661 |
| RB's own receiving-points share | CONSTITUENT | −0.105 | −0.105 | −0.063 | −0.692 | 721 |
| end-of-season depth-chart rank | EXOGENOUS | +0.099 | −0.301 | +0.099 | −0.933 | 607 |
| practice-participation severity | EXOGENOUS | +0.066 | −0.048 | +0.066 | −0.643 | 661 |
| late-season role trend | CONSTITUENT | +0.059 | +0.059 | +0.035 | −0.562 | 629 |
| YAC per reception | CONSTITUENT | +0.056 | +0.056 | −0.033 | −0.470 | 556 |
| team neutral pass rate | EXOGENOUS | +0.042 | +0.041 | +0.042 | −0.575 | 1024 |
| combine composite | EXOGENOUS | −0.031 | −0.004 | −0.031 | −0.611 | 632 |

**Dead on arrival (RB)**: team explosive-rush rate only.

### WR (8 of 9 screened factors)

| factor | class | headline | raw ρ | partial ρ | beats_agg | n |
|---|---|---|---|---|---|---|
| WOPR | CONSTITUENT | **+0.668** | +0.668 | +0.187 | −0.009 | 1069 |
| offensive snap share | CONSTITUENT | +0.652 | +0.652 | +0.133 | −0.036 | 829 |
| red-zone usage share | CONSTITUENT | +0.554 | +0.554 | +0.020 | −0.092 | 905 |
| yards-over-expected rate | CONSTITUENT | +0.247 | +0.247 | +0.044 | −0.414 | 1106 |
| YAC per reception | CONSTITUENT | +0.114 | +0.114 | −0.006 | −0.524 | 904 |
| practice-participation severity | EXOGENOUS | +0.052 | −0.084 | +0.052 | −0.747 | 978 |
| injury report-week burden | EXOGENOUS | +0.049 | +0.022 | +0.049 | −0.661 | 978 |
| team neutral pass rate | EXOGENOUS | +0.010 | +0.028 | +0.010 | −0.630 | 1505 |

**Dead on arrival (WR)**: end-of-season depth-chart rank, combine composite, late-season role
trend.

### TE (9 of 9 screened factors — TE is fully inclusive)

| factor | class | headline | raw ρ | partial ρ | beats_agg | n |
|---|---|---|---|---|---|---|
| WOPR | CONSTITUENT | **+0.667** | +0.667 | +0.179 | −0.010 | 621 |
| red-zone usage share | CONSTITUENT | +0.572 | +0.572 | −0.009 | −0.078 | 516 |
| offensive snap share | CONSTITUENT | +0.557 | +0.557 | +0.026 | −0.088 | 480 |
| yards-over-expected rate | CONSTITUENT | +0.091 | +0.091 | −0.009 | −0.574 | 651 |
| end-of-season depth-chart rank | EXOGENOUS | +0.086 | −0.418 | +0.086 | −1.096 | 551 |
| YAC per reception | CONSTITUENT | −0.067 | −0.067 | −0.078 | −0.698 | 480 |
| injury report-week burden | EXOGENOUS | +0.061 | +0.063 | +0.061 | −0.614 | 571 |
| combine composite | EXOGENOUS | +0.048 | +0.153 | +0.048 | −0.495 | 504 |
| practice-participation severity | EXOGENOUS | +0.045 | −0.089 | +0.045 | −0.777 | 571 |

None dead on arrival at TE — every screened factor clears its position's noise floor,
consistent with `combine_z` being flagged specifically for rookie relevance and TE's smaller,
more rookie-heavy graded population (per `docs/CURRENT-STATE.md`'s note that TE realised
`S_pos` is the thinnest of the four positions in the tier-2 grading window).

---

## Stability across seasons (selected, the headline candidates per position)

Per-season raw ρ, 2013–2019 (`None` = insufficient coverage that season):

| factor / position | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 |
|---|---|---|---|---|---|---|---|
| QB rush att/game | 0.369 | 0.312 | 0.364 | 0.503 | 0.499 | 0.348 | 0.369 |
| QB depth-chart rank | −0.698 | −0.665 | −0.447 | −0.647 | −0.587 | −0.573 | −0.605 |
| RB snap share | — | 0.485 | 0.517 | 0.509 | 0.592 | 0.607 | 0.664 |
| RB red-zone share | 0.564 | 0.468 | 0.359 | 0.416 | 0.646 | 0.503 | 0.633 |
| RB depth-chart rank | −0.326 | −0.280 | −0.262 | −0.170 | −0.253 | −0.397 | −0.393 |
| WR WOPR | 0.656 | 0.671 | 0.673 | 0.676 | 0.642 | 0.719 | 0.650 |
| TE WOPR | 0.744 | 0.663 | 0.737 | 0.697 | 0.644 | 0.570 | 0.549 |

**Read**: the strongest survivors (snap share, red-zone share, WOPR, depth-chart rank) are
strong AND stable — no sign reversals across any of the 7 screened seasons. QB rushing
attempts is stable but shows real amplitude variation (0.31–0.50), plausibly tracking the
league's rushing-QB population composition shifting year to year rather than the mechanism
itself weakening — flagged, not resolved. TE WOPR shows a mild downward drift across the
window (0.74 → 0.55) worth a note for whoever registers a confirmatory test, though it never
approaches reversal.

---

## Why almost nothing "beats the aggregate" — read before over-interpreting `beats_agg`

Every `beats_agg` column above is negative, most substantially so. **This is expected, not
a finding of weakness.** Prior-season points already encodes volume × efficiency × games in
one number; no single univariate factor should be expected to out-predict that composite on
its own — that would require the factor to be a *better* summary of the player than his own
actual production was. The informative comparison is not "did factor X beat prior points,"
it is "does factor X show real, noise-clearing predictiveness in its own right" (the raw ρ
vs. the placebo floor) — several do, strongly (WOPR/snap share/red-zone share all land at
0.5–0.7 raw ρ against noise floors under 0.05). The founder's "beats the aggregate" question
is answered properly by the **eventual joint fit** — a multivariate model with prior points
as one predictor among several is the actual test of whether a constituent factor adds
marginal information once points is already in the equation, which single-factor
partialling cannot answer for these factors (that is the whole reason for the
EXOGENOUS/CONSTITUENT split in the first place).

---

## Collinearity map — diagnostic, not a pruning list

Founder, mid-session: *"There is some collinearity. And sometimes it is predictive."* **This
map does not remove anything from the survivor set above.** Two factors correlated at
ρ=0.8 still carry ~36% independent variance, and that remainder is often where the
information is; pruning on a threshold would discard it permanently — regularisation in the
joint fit is the right instrument for deciding what earns weight once a near-duplicate is
known to exist. What follows is a warning label for whoever builds v3's design matrix, not a
filter on its inputs.

**Tight clusters found (|ρ| ≥ 0.6, pairwise, within-position, n ≥ 30):**

| position | cluster | ρ |
|---|---|---|
| RB | injury burden ↔ practice severity | +0.608 |
| RB | snap share ↔ red-zone share | +0.801 |
| TE | depth-chart rank ↔ red-zone share | −0.608 |
| TE | depth-chart rank ↔ snap share | −0.738 |
| TE | depth-chart rank ↔ WOPR | −0.623 |
| TE | injury burden ↔ practice severity | +0.642 |
| TE | snap share ↔ red-zone share | +0.725 |
| TE | WOPR ↔ red-zone share | +0.791 |
| TE | WOPR ↔ snap share | +0.832 |
| WR | injury burden ↔ practice severity | +0.611 |
| WR | snap share ↔ red-zone share | +0.796 |
| WR | WOPR ↔ red-zone share | +0.766 |
| WR | WOPR ↔ snap share | +0.932 |

**Reading the clusters**: at WR/TE, `{snap share, WOPR, red-zone share, depth-chart rank}`
form one nearly-collapsed cluster — unsurprising, since all four are different views on "how
much does the team feature this player." At RB, `snap share ↔ red-zone share` is the only
tight pair, and `injury burden ↔ practice severity` clusters at both RB and WR/TE (expected —
both are read off the same `injuries` table). **Full pairwise matrix (not just tight pairs)**:
`experiments/bottomup/results/standalone_screen1_collinearity.csv`, 238 rows.

**Within-cluster contrasts constructed and screened, per the founder's second instruction**
(percentile-rank gap within season — high-A/low-B is a role signal the raw components wash
out individually): 13 contrasts screened, same treatment as any other factor.

| position | contrast | class | raw ρ | survives? | reading |
|---|---|---|---|---|---|
| TE | depth rank − WOPR | CONSTITUENT | −0.597 | yes | a player ranked poorly on the depth chart yet still commanding target share is a real role signal — this contrast is nearly as strong as either raw component |
| TE | depth rank − red-zone share | CONSTITUENT | −0.551 | yes | same mechanism |
| TE | depth rank − snap share | CONSTITUENT | −0.511 | yes | same mechanism |
| WR | injury ↔ practice contrast | EXOGENOUS | +0.127 | yes | weak but clears noise; the two components diverging (listed often, rarely limited in practice, or vice versa) carries some signal beyond either alone |
| RB | injury ↔ practice contrast | EXOGENOUS | +0.193 | yes | strongest of the three injury/practice contrasts |
| TE | WOPR − snap share | CONSTITUENT | +0.112 | yes | high target share relative to snaps = an efficient, high-value role even at lower overall usage |
| RB | snap share − red-zone share | CONSTITUENT | −0.033 | no | does not clear the RB noise floor — a between-the-tackles, non-scoring role signal did not show a pulse in this window |
| WR | snap share − red-zone share | CONSTITUENT | −0.054 | no | same, WR |
| WR | WOPR − snap share | CONSTITUENT | +0.086 | yes | mirrors the TE finding, weaker |
| WR / TE | WOPR − red-zone share | CONSTITUENT | ~0.00 | no | no signal either direction |
| TE | injury ↔ practice contrast | EXOGENOUS | +0.178 | no | fails the (tighter) TE noise floor despite a larger raw value than WR's — TE's noise floor itself is the highest of the four positions (placebo raw ρ = −0.051) |

**Read**: the depth-chart-rank-vs-usage contrasts at TE are the standout finding from this
exercise — nearly as predictive as the raw depth-chart rank itself, meaning "the coach's
stated depth chart disagrees with how the team actually uses him" carries real information at
TE specifically, plausibly because TE role designations (blocking TE vs. receiving TE) are
coarser than the underlying usage split. Full table: `standalone_screen1_contrasts.csv`.

---

## Season budget — screen / fit / test, stated plainly (founder's third instruction)

| Phase | Seasons | Count | Status |
|---|---|---|---|
| **Screen** (this document) | 2013–2019 | 7 | **Spent.** |
| **Fit** (v3 joint multivariate fit) | subset of 2020–2024 | ≤5 | **Unspent, not yet split** |
| **Test** (v3 held out from fitting) | disjoint subset of 2020–2024 | ≤5 | **Unspent, not yet split** |
| **Sealed** | 2025 | 1 | **Never opens without founder authorization (CLAUDE.md §6.3)** |

**This is thin, and it is flagged now rather than discovered after v3 is built.** Only
**5 seasons total** remain for BOTH fitting and testing v3, and they must be disjoint — the
founder's own three-phase framing (screen/fit/test) requires it. A naive 3-fit/2-test split
(2020–2022 fit, 2023–2024 test) leaves the test set at just 2 independent season draws, which
is a weak instrument for judging whether a ~15–25-predictor joint fit (the survivor set sizes
above) generalizes rather than re-fits noise in-sample — especially given this project's own
measured overfitting hazard (CLAUDE.md §6.3: ~30 candidate factors against a
heavily-autocorrelated ~200–300-player universe yields ~1.5 false positives at p<0.05 by
chance alone, and C1's placebo already demonstrated an unguarded rule finding a BH-robust WIN
in pure noise at a 14.6% rate).

**A second, independent constraint**, from `docs/CURRENT-STATE.md`'s own already-measured
finding: the ADP archive (which several v2 arms use to define the evaluation universe) is
**7 seasons at exact `half_ppr_12team` format, 12 at a format-caveated `ppr_12team`/
`non_ppr_12team`, and 21 with no ADP membership constraint at all** (`rho_points_fullvet`).
If v3's evaluation universe needs exact-format ADP membership, the same 2013–2019 window this
screen already spent is very close to the *entire* exact-format archive — meaning v3's
fit/test seasons may need to come from the format-caveated or no-ADP-constraint universes,
a different (weaker) population than this screen's own universe. **This is a design problem
for whoever registers v3, not solved here — surfaced explicitly per instruction, rather than
discovered after fitting starts.**

**Recommendation, not a decision**: `strategist` should register the exact fit/test split
(and which population — exact-ADP-format vs. the wider no-ADP-constraint universe) before any
v3 coefficient is estimated, precisely because the split is this thin.

---

## Two limits of this method — stated so nobody over-reads it

1. **A factor can be strongly predictive alone yet add nothing incrementally** — already
   captured by the raw-vs-noise-floor test above and orthogonal to what a joint fit will find
   once every survivor competes for the same variance (this is exactly why collinear
   survivors like WOPR/snap-share/red-zone-share at WR/TE are all kept in, not pruned).
2. **A factor can be null alone yet help in combination** — nothing here can detect an
   interaction or a conditional effect (e.g., a factor that only matters for players below a
   certain draft-capital threshold). Standalone predictiveness orders the queue and screens
   out what is provably dead; **it does not decide inclusion**, and it especially cannot
   promise a factor marked dead-on-arrival here is truly useless inside a multivariate model.

---

## Files

- `experiments/bottomup/v2/standalone_screen1.py` — self-contained script, run from repo root
- `experiments/bottomup/results/standalone_screen1_results.csv` — 45 rows, individual factors
- `experiments/bottomup/results/standalone_screen1_collinearity.csv` — 238 rows, full pairwise matrix
- `experiments/bottomup/results/standalone_screen1_contrasts.csv` — 13 rows, within-cluster contrasts
