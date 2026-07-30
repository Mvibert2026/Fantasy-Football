# Factor batch 1 — pre-commitment

**Ranker, 2026-07-30. Written and committed BEFORE any arm was fitted.** Same discipline as
`component-model-multipos-precommit.md` (`5f8efc1`). If a number in the results document is not
predicted by an endpoint declared here, it is post-hoc and must be labelled so.

**Scope.** Four `derived`/`nflverse` factors from `docs/test-registry.md` that the registry records
as never measured: **#19 TD-rate regression**, **#20 opportunity share**, **#28 vacated targets and
carries**, **#13 target-share stability YoY**.

**Exploratory, not confirmatory.** Nothing here may be reported as an edge. The sealed 2025 holdout
is not touched and no holdout spend is requested. Promotion of any arm into the shipped model is a
`strategist` registration plus a `backend` handoff, not a decision this pass may make.

---

## 1. Harness — unchanged, deliberately

`experiments/bottomup/components`, the walk-forward from `component-model-multipos-precommit.md`.

| | |
|---|---|
| Target seasons | 2014–2024 (11). ADP board exists 2018–2024 (7). |
| Features | seasons ≤ N−1 only, plus April-of-N draft slot and season length |
| Training | (features, outcome) pairs whose OUTCOME season is ≤ N−1 |
| Universe | frozen from pre-N information; busts retained, scoring zero |
| Holdout | 2025 sealed at the SQL gate (`pos_data.HOLDOUT_SEASON`). **Not opened.** |
| Uncertainty | season-block bootstrap, 4,000 reps, **seasons** the resampling unit |

**Every arm differs from its position's primary by exactly one thing.** No arm changes the
availability sub-model, the bonus machinery, the universe or the scoring.

---

## 2. Endpoints, fixed now

Two endpoints per arm, in a fixed hierarchy. Declared before fitting so neither can be swapped for
the other after the fact.

**E1 — the gate: out-of-sample MAE of the one component the factor is supposed to improve.**
11 seasons. This is "out-of-sample projection error" and it is the FDR family.

| factor | E1 component, per position |
|---|---|
| #19 TD-rate regression | WR `rec_tds` · TE `rec_tds` · RB `rush_tds` · QB `pass_tds` |
| #20 opportunity share | WR `targets` · TE `targets` · RB `carries` |
| #28 vacated opportunity | WR `targets` · TE `targets` · RB `carries` |
| #13 target-share stability | WR `targets` · TE `targets` · RB `targets` |

**Exactly one E1 per cell.** Reporting the best of several components per cell would be selection on
the outcome, which is the thing this document exists to stop.

**E2 — the bar that matters: ADP-board Spearman, arm − primary.** 7 seasons. `CLAUDE.md` §6.5: the
headline is the comparison against consensus, never the raw number. **E2 is known to be
underpowered before it is run** — `component-model-rb-qb-te-pass-1.md` §1 measured that seven
seasons cannot show consensus beating a three-line heuristic at WR, QB or TE. Only at RB does this
endpoint resolve anything. That is stated here, in advance, so it cannot be produced afterwards as a
caveat.

**Secondary, reported descriptively and NOT in the FDR family:** full-universe Spearman (11
seasons), top-k capture at this league's k, all other component MAEs.

---

## 3. The arms

### 3.1 Factor #19 — TD-rate regression · 8 cells (WR, TE, RB, QB)

The model already projects TD/target, TD/carry and TD/attempt as empirical-Bayes shrunk rates whose
target is a **single pooled position mean** and whose shrinkage constant `k` is picked on training
seasons. Two arms, each one change away from that:

- **T1 — volume-conditional prior.** The shrinkage target becomes a fitted function of volume,
  `prior_i = a + b·log(1+denominator_i)`, estimated by weighted least squares on training rows.
  Mechanism: goal-line and red-zone role scales with volume, so shrinking a 300-carry back toward
  the same TD/carry as a 40-carry back is wrong in a knowable direction.
- **T2 — full regression.** `k → ∞` for the TD rates **only**. Every player receives the pooled
  prior; his own past TD rate is discarded entirely. This is the sharp form of the registry's claim
  and the cheapest possible test of it: if T2 does not lose, a player's own TD rate carries no
  out-of-sample signal at all.

### 3.2 Factor #20 — opportunity share · 6 cells (WR, TE, RB)

QB excluded on a structural argument, not a result: a starting QB's share of his own team's pass
attempts is ~1 by construction and carries no information.

- **O1 — share reparameterisation.** Project team-relative share (targets / team targets, carries /
  team carries) and multiply by the team's **lagged** per-game volume, instead of projecting the
  player's per-game volume directly. Team volume features are recency-weighted over N−1..N−3 and
  read nothing from season N.
- **O2 — share ablation.** Delete `tshare_w` / `cshare_w` from the volume designs. They are already
  in the primary; nobody has ever measured what they are worth. A positive MAE difference here
  means share is currently earning its place.

### 3.3 Factor #28 — vacated targets and carries · 6 cells (WR, TE, RB)

**Data gap, declared before running and not designed around silently.** `nfl.db` contains **no
pre-season-N roster or team-membership table.** `depth_charts_weekly` begins at REG week 1;
`depth_charts_snapshots` is a single 2026-03-14 snapshot; there is no `rosters` table.
`nflreadpy.load_rosters_weekly()` is the source that would fix this and it is **already commissioned
from `data-ops`** for a different reason (the IR/suspension gap in
`component-model-rb-qb-te-pass-1.md` §5.2). This factor is a second, independent consumer of that
same ingestion, and that strengthens the case for it.

Until it lands, season-N team membership is a **PROXY**: appearance on the team's season-N **Week-1
REG depth chart**.

- It contains **no season-N production**, so it cannot inflate any outcome.
- It is dated roughly one week **after** a real draft, so it is later than `CLAUDE.md` §6.1's
  "preseason N" bound. It is used anyway, labelled PROXY everywhere, because the alternative —
  inferring departure from who appears in season-N box scores — is outright survivorship
  contamination.
- **Known leak channel, stated in advance:** a player injured in Week 1 of N may be absent from the
  Week-1 chart and be miscounted as departed, inflating his team's measured vacancy. The feature is
  a team-level aggregate, which dilutes this, but it is not zero.

Definition. For team T entering season N:
`vacated_targets(T, N) = Σ over players with season-N−1 usage for T who are NOT on T's Week-1
depth chart in N, of their N−1 targets` — and the same for carries. Player feature = that quantity
as a share of T's N−1 team total, joined on the player's season-N team where the proxy supplies one
and his N−1 team otherwise.

- **V1 — vacated features** added to the volume designs.
- **V0c — the free control, reading no season-N data at all.** Team N−1 volume per game and the
  player's own N−1 share of it, with **no** vacancy term. Arm C in the availability test existed for
  exactly this reason and it is the reason that result was interpretable: without a free control, a
  V1 gain cannot be told apart from "we added a team-volume feature." **V0c is what makes V1
  attributable.**

### 3.4 Factor #13 — target-share stability YoY · 3 cells (WR, TE, RB)

- **Descriptive measurement, outside the FDR family.** Lag-1 → lag-0 correlation of target share
  across consecutive-season pairs, per position, season-block bootstrap CI. Reported on the same
  scale as the archetype persistence numbers already measured (snap share r = +0.707, yards per
  carry r = +0.175, mean PPG r ≈ 0.72) so the comparison the brief asks for is direct.
- **S1 — stability-weighted share.** Two features added: the SD of target share across the lag
  seasons the player was actually present for, and how many such seasons there were. Hypothesis: a
  share observed consistently across three years predicts better than the same share observed once.

---

## 4. Multiple comparisons

**m = 23** E1 tests: 8 (#19) + 6 (#20) + 6 (#28) + 3 (#13).

- **Benjamini–Hochberg on the 23 E1 p-values, q = 0.10**, reported alongside q = 0.05.
- p-values from a **paired two-sided t-test across seasons** on the per-season MAE differences
  (n = 11), because seasons are the independent unit. Bootstrap CIs are reported as the interval;
  the t-test supplies the p-value BH needs.
- E2 is **not** in the family. It is the confirmatory bar, it has 7 seasons, and correcting an
  underpowered secondary alongside the gate would hide the gate.
- **The denominator is 23 whatever happens.** An arm that crashes, is abandoned, or is dropped for
  any reason still counts. `docs/preregistration/README.md`: an unrecorded failed test inflates
  every surviving result.

---

## 5. Grading — committed now

| grade | condition |
|---|---|
| **SURVIVES** | E1 improves, BH-significant at q=0.10 with the correct sign, **and** E2 point estimate > 0 |
| **PROJECTION-ONLY** | E1 BH-significant with the correct sign, E2 ≤ 0 or spanning zero. **Knowledge, not a win.** Explicitly not recommended for the shipped model. |
| **MARGINAL** | E1 clears zero uncorrected but fails BH. A hypothesis. Never advice. |
| **NULL** | E1 does not clear zero |
| **HARMFUL** | E1 significantly worse |

**No arm is promoted on this pass regardless of grade.** A SURVIVES result becomes a thread to
`strategist` asking for a confirmatory registration, and nothing else.

**Prior stated before the numbers exist:** most of these will be NULL. Four clean nulls with tight
intervals is a good outcome and is worth more than one MARGINAL that gets quoted for two years.
`docs/strategic-insights.md` §3 already lists seven measured nulls; this batch is expected to
lengthen that list, not §2.

**Calibration against my own record**, per the standing prior that four of five registered
prediction sets in this project were wrong and every miss over-credited a situation story: **#28 is
the situation story in this batch.** "Where opportunity actually opened" is exactly the narrative
shape that has misfired before. It is priced at half weight going in, and the V0c control exists
because of that.

---

## 6. Look-ahead and survivorship enforcement

- The panel's `before(cutoff)` gate, the separate `outcomes(season)` accessor, and the per-season
  audit assertion (max feature cutoff and max outcome season strictly below target; zero outcome
  reads at target) all stay in force, unmodified.
- The Week-1 depth-chart proxy gets its **own** accessor and its **own** access-log tag. The audit
  gains `n_preseason_proxy_reads`, and **every arm except V1 asserts it is exactly zero.** The proxy
  cannot leak into an arm that did not declare it.
- Universe construction is untouched: frozen pre-season, busts retained.
