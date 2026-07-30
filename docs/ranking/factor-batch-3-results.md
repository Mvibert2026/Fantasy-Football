# Factor batch 3 — results

**Ranker, 2026-07-30.** Runs the researcher's ranked five
(`docs/research/analyst-factor-sweep-2026-07-30.md` §5) plus the founder's correction that
coordinator continuity be specified as **tenure**, and that **QB was never tested at all** in
batch 2.

Design fixed in `docs/ranking/factor-batch-3-precommit.md`, content committed **`1c452a1` before any
arm was fitted**. 24 registered tests, **BH at the campaign level, m = 24**, q = 0.10. Sealed 2025
holdout **not opened**. Results `c7161ce`, post-hoc diagnostics `bda27ea`.

Reproduce:

```
.venv/bin/python -m experiments.bottomup.factors.run_factors3    # the 24 registered tests
.venv/bin/python -m experiments.bottomup.factors.diagnostics3    # the post-hoc work
```

---

## 1. Conclusion first — four answers, and the best one demotes my own best result

### (1) The real find is a missing wire inside our own model, not a factor from the sweep

The registered arm **X1 (explosive rush rate, ≥10-yard share of a back's carries)** improved RB
carry MAE by **−0.7508, −1.51% [−1.086, −0.387], p = 0.0025**, BH-significant, with its
pre-registered control arm flat (**−0.0058, p = 0.44**). Clean. Not a coverage artifact.

Then the post-hoc check nobody asked for:

| RB `carries` MAE, arm − primary, 11 seasons | E1a | % of primary error | E1b (ADP board) |
|---|---|---|---|
| **X1 explosive rush rate** (registered) | −0.7508 | −1.51% | −0.0264 |
| **D1d lagged YARDS PER CARRY, alone** (post-hoc) | **−0.9331** | **−1.88%** | **−0.7200** |
| D1e explosive rate *on top of* lagged YPC | −0.9784 | −1.97% | −0.6167 |

**Yards per carry does the same job better, and 27× better on the ADP board.** Explosive rate on top
of it buys −0.045 more. And YPC is not a new input — **this model already computes it and already
uses it, for the yards channel. It has never once been offered to the volume channel.**

So the honest headline is not *"the sweep's #4 factor works."* It is:

> **A wire is missing inside our own model. A back's efficiency predicts how much work he gets next
> year, the model holds that number already, and nothing connects the two. It is worth roughly 1.9%
> of RB carry error and costs no new data at all.**

This is post-hoc, it has not been registered, and **it must not ship until `strategist` registers it
and `backend` implements it.** It is written up first because it is the most valuable thing in the
batch and because burying it under the arm I actually registered would be self-serving.

**What survives about explosive rate itself**, from the same diagnostics:

| instrument | result | reads as |
|---|---|---|
| D1a **placebo** — identical shrinkage geometry, numerator replaced by a `Binomial(den, prior)` draw | **+0.0063, p = 0.87** | the empirical-Bayes geometry (which makes `|rate − prior|` a function of lagged carries) buys **nothing** |
| D1b **unshrunk** raw rate — the signal without the geometry | **−0.6762, p = 0.0009** | **90% of the effect survives.** It is the football |
| D5 corr(`expl_w`, **next** carries/game) | **+0.2455** | real |
| D5 corr(`expl_w`, **lagged** carries/game) | **+0.0365** | **not a volume proxy** |
| D5 partial corr, controlling lagged volume, share, games share, age, experience | **+0.2656** | *rises* after controlling — genuinely new information |

Descriptive, and the clearest way to say it (1,305 RB player-seasons, 2014–2024):

| explosive-rate quartile | n | **lagged** carries/g | **next** carries/g | next-season points |
|---|---|---|---|---|
| Q1 least explosive | 327 | 9.11 | 4.95 | 54.6 |
| Q2 | 326 | 8.20 | 4.73 | 49.2 |
| Q3 | 326 | 8.56 | 6.06 | 71.8 |
| **Q4 most explosive** | 326 | **9.52** | **8.79** | **108.7** |

Two groups of backs with **the same prior workload** (9.11 vs 9.52 carries a game) get **1.8× the
work and 2× the points** the following season. That is the mechanism, and it is why the volume
channel wants an efficiency input. It is also why YPC — a finer measurement of the same thing —
beats a binary ≥10-yard threshold.

### (2) QB rushing: the block earns its place, and it also predicts PASSING volume

QB has never been touched by a factor arm in this project until now.

| | E1a | % | 95% CI | p | grade |
|---|---|---|---|---|---|
| **A1** QB rushing block **ABLATION**, `carries` | **+1.8065** | **+14.38%** | [+1.444, +2.203] | 0.0000 | **EARNS-ITS-PLACE** |
| **A2** QB rushing added to the **passing-attempt** volume spec, `attempts` | **−1.4679** | −1.30% | [−2.276, −0.688] | 0.0068 | **PROJECTION-ONLY** |

A1's +14.4% **tripped the too-good trigger committed in advance** and is escalated in §4 rather than
celebrated. A2 is the interesting one and it is new: **a quarterback's prior rushing volume predicts
how much he will THROW**, worth 1.3% of attempt error and better on the ADP board too (E1b −3.03).
E2 is −0.016, so it does not yet improve the board ranking — PROJECTION-ONLY under the registered
rule, not an edge.

### (3) Registry #29 is dead on both specifications. Stated before measurement, honoured after.

The pre-commitment said, in advance: *if the coordinator factor is also null at QB, it is dead on
both specifications and must not be re-specified a third time.*

| | E1a | 95% CI | p | grade |
|---|---|---|---|---|
| **C1Q** `new_oc`, batch 2's own block, at **QB** | −0.0660 | [−0.181, +0.037] | 0.274 | **NULL** |
| **T1** OC **tenure**, QB | −0.2427 | [−0.514, −0.016] | 0.106 | MARGINAL |
| **T1** OC tenure, WR | +0.0140 | [−0.001, +0.034] | 0.179 | NULL |
| **T1** OC tenure, TE | −0.1227 | [−0.232, −0.020] | 0.052 | MARGINAL |
| **T1** OC tenure, RB | +0.0492 | [−0.007, +0.131] | 0.244 | NULL |

Nothing clears BH at m = 24. The founder's prior — that OC continuity matters most at QB — **is not
supported**: `new_oc` at QB is null, exactly as it was at WR, TE and RB. Tenure at QB is the batch's
best coordinator number and it is MARGINAL, **with its own control arm at 46% of it** (`|c|/|t|` =
0.46, just under the 0.50 VOID threshold fixed in advance). That is not a factor; that is a
coin-flip sitting next to a confound.

**#29 has now been measured as change (batch 2, three positions), as change at QB, and as tenure at
four positions. Seven arms, one model, nothing. It does not get a third specification.**

### (4) The researcher's highest-EV pick is wrong here — and four of my own tests were degenerate

**B2r — prior points per game *played*, replacing §6.5's baseline #2 (prior season total) — is
WORSE at every position**, full universe, 11 seasons:

| | E3 (Δ Spearman vs incumbent) | 95% CI | p | on the ADP board |
|---|---|---|---|---|
| QB | **−0.0239** | [−0.038, −0.009] | 0.013 | **+0.0479** |
| RB | **−0.0221** | [−0.038, −0.007] | 0.024 | **+0.0261** |
| WR | **−0.0210** | [−0.029, −0.011] | 0.001 | −0.0187 |
| TE | **−0.0300** | [−0.046, −0.014] | 0.006 | **+0.0400** |

All four BH-significant, all four **BASELINE-WORSE**. The reason is exactly what the researcher's
own §0 warned about and then did not apply to this row: **every published number behind it is
measured on survivors with minimum-games filters.** On a universe with busts retained, availability
is signal, and a pure-rate baseline throws it away. **The sign flips on the ADP board at QB, RB and
TE** — among players who are all real, the rate version is better — which is a genuinely useful
nuance and is reported as one, not as a rescue.

The three-lag version already in the harness (`b3_wavg_ppg`) is worse still: −0.040 QB, −0.124 RB,
−0.100 WR, −0.111 TE. **`CLAUDE.md` §6.5's baseline #2 stands unchanged.**

**And my own specification error, reported rather than hidden.** Registered tests 21–24, `B2ra`
(`ppg_1 × gshare_1`), are algebraically `pts_1 / season_len` — **a strictly monotone transform of the
incumbent**, so their rank correlation is identical by construction. Measured residual:
`1.776e-15`. **Four of my twenty-four registered tests were structurally incapable of returning
anything but zero.** This is batch 3's equivalent of batch 2's `move_known` defect: a design fault of
mine, caught by the result. It is the conservative direction — it inflated the BH denominator against
my own arms — but it is still a fault, and the corrected construction (recency-weighted, i.e. `b3`)
is post-hoc and is reported as such above.

---

## 2. The registered table — all 24

**E1a** = out-of-sample MAE of the one component declared per cell in advance, full universe, arm −
primary, paired by season, season-block bootstrap 4,000 reps. **Negative = better** (inverted for the
one ablation arm, declared in advance). **E1b** = the same on the ADP board, 7 seasons — a required
direction check, not the significance test. **E2** = ADP-board Spearman, 7 seasons, known
underpowered at WR/TE/QB before it was run. **E3** = full-universe Spearman for family F2.

| # | pos | arm | E1a / E3 | 95% CI | p | BH q=.10 | E1b | E2 | grade |
|---|---|---|---|---|---|---|---|---|---|
| 1 | QB | **A1** QB rush block ABLATION | **+1.8065** | [+1.444, +2.203] | 0.0000 | **Y** | +6.978 | −0.053 | **EARNS-ITS-PLACE** |
| 2 | QB | **A2** QB rush → passing volume | **−1.4679** | [−2.276, −0.688] | 0.0068 | **Y** | −3.035 | −0.016 | **PROJECTION-ONLY** |
| 3 | WR | **S1** NGS avg separation | −0.0635 | [−0.100, −0.028] | 0.0192 | **Y** | +0.375 | −0.000 | **VOID — COVERAGE ARTIFACT** |
| 4 | TE | **S1** NGS avg separation | −0.1462 | [−0.272, −0.071] | 0.0552 | n | +0.920 | −0.001 | MARGINAL |
| 5 | WR | **S1c** CONTROL coverage flag | +0.0584 | [+0.015, +0.104] | 0.0560 | n | +0.371 | −0.001 | MARGINAL-HARMFUL |
| 6 | TE | **S1c** CONTROL coverage flag | +0.0044 | [−0.176, +0.140] | 0.9622 | n | +0.989 | −0.006 | NULL |
| 7 | RB | **X1** explosive rush rate, own | **−0.7508** | [−1.086, −0.387] | 0.0025 | **Y** | −0.026 | −0.010 | **PROJECTION-ONLY** |
| 8 | RB | **X2** explosive rate, club-relative | **−0.4593** | [−0.681, −0.211] | 0.0043 | **Y** | −0.089 | −0.001 | **PROJECTION-ONLY** |
| 9 | RB | **X1c** CONTROL coverage flag | −0.0058 | [−0.021, +0.004] | 0.4369 | n | −0.016 | +0.000 | NULL |
| 10 | QB | **T1** OC tenure | −0.2427 | [−0.514, −0.016] | 0.1055 | n | −0.694 | +0.013 | MARGINAL |
| 11 | WR | **T1** OC tenure | +0.0140 | [−0.001, +0.034] | 0.1793 | n | −0.016 | −0.000 | NULL |
| 12 | TE | **T1** OC tenure | −0.1227 | [−0.232, −0.020] | 0.0519 | n | +0.018 | +0.005 | MARGINAL |
| 13 | RB | **T1** OC tenure | +0.0492 | [−0.007, +0.131] | 0.2436 | n | +0.026 | +0.001 | NULL |
| 14 | QB | **T1c** CONTROL coverage flag | +0.1123 | [+0.018, +0.220] | 0.0647 | n | +0.433 | +0.001 | MARGINAL-HARMFUL |
| 15 | WR | **T1c** CONTROL coverage flag | −0.0019 | [−0.034, +0.034] | 0.9187 | n | +0.095 | −0.000 | NULL |
| 16 | QB | **C1Q** `new_oc` (batch-2 spec) at QB | −0.0660 | [−0.181, +0.037] | 0.2742 | n | −0.292 | +0.010 | NULL |
| 17 | QB | **B2r** prior points per game played | −0.0239 | [−0.038, −0.009] | 0.0130 | **Y** | +0.048 | — | **BASELINE-WORSE** |
| 18 | RB | **B2r** prior points per game played | −0.0221 | [−0.038, −0.007] | 0.0239 | **Y** | +0.026 | — | **BASELINE-WORSE** |
| 19 | WR | **B2r** prior points per game played | −0.0210 | [−0.029, −0.011] | 0.0011 | **Y** | −0.019 | — | **BASELINE-WORSE** |
| 20 | TE | **B2r** prior points per game played | −0.0300 | [−0.046, −0.014] | 0.0060 | **Y** | +0.040 | — | **BASELINE-WORSE** |
| 21 | QB | **B2ra** ppg × games share † | +0.0000 | [0, 0] | 1.0000 | n | +0.000 | — | NULL † |
| 22 | RB | **B2ra** ppg × games share † | −0.0000 | [−0.000, +0.000] | 0.5236 | n | +0.000 | — | NULL † |
| 23 | WR | **B2ra** ppg × games share † | −0.0000 | [−0.000, +0.000] | 0.6809 | n | +0.000 | — | NULL † |
| 24 | TE | **B2ra** ppg × games share † | −0.0000 | [−0.000, +0.000] | 0.4521 | n | +0.000 | — | NULL † |

**† Rows 21–24 are degenerate by construction — see §1(4).** They are reported at their registered
values because that is what pre-registration means, and they are worthless as evidence.

**Grade counts:** NULL 10 · BASELINE-WORSE 4 · PROJECTION-ONLY 3 · MARGINAL 3 · MARGINAL-HARMFUL 2 ·
EARNS-ITS-PLACE 1 · VOID 1. **Nothing graded SURVIVES. Nothing is an edge over consensus.**

### Coverage gates, all measured on the ADP board before any result was read

| block | position | coverage | gate | |
|---|---|---|---|---|
| NGS separation | WR / TE | 0.826 / 0.850 | 0.60 | PASS |
| explosive rush | RB | 0.836 | 0.80 | PASS |
| OC tenure | QB / TE / WR / RB | 0.982 / 0.984 / 0.967 / 0.962 | 0.80 | PASS |
| `new_oc` (batch-2 block) | QB | 0.994 | 0.80 | PASS |

No cell was graded NO DATA. Note the gap between board and full universe for NGS — **0.83 on the
board against 0.41–0.45 on the full universe**, which is precisely why the control arms exist.

---

## 3. The VOID rule fired, and it fired on the arm I most wanted to work

The pre-commitment said: *if a control arm's |E1a| reaches 50% of its paired treatment's, the
treatment is a coverage artifact and loses its interpretation.* Measured:

| pairing | treatment | control | \|c\|/\|t\| | |
|---|---|---|---|---|
| **NGS separation, WR** | −0.0635 | **+0.0584** | **0.92** | **VOID** |
| NGS separation, TE | −0.1462 | +0.0044 | 0.03 | not void |
| explosive rush, RB | −0.7508 | −0.0058 | 0.01 | not void |
| OC tenure, QB | −0.2427 | +0.1123 | **0.46** | not void — by 0.04 |

**NGS separation at WR is the only registered arm that cleared BH and then lost its meaning.** The
treatment and its control move the model by almost exactly the same magnitude in opposite
directions, which is the signature of a feature whose information content is "we have a tracking row
for this player," i.e. "he was a starter last year." Batch 2 discovered that shape after the fact and
had to disown three arms; batch 3 caught it mechanically, in the same run, because the control was
registered in advance.

**TE separation is the one NGS number that is not an artifact** — control at 3% of treatment,
E1a −0.1462 (−0.77%), CI excluding zero, not BH-significant at m = 24. **MARGINAL, and the most
interesting unresolved thing in the batch.** It had 7 seasons; it deserves a properly powered rerun
before it is called anything.

**OC tenure at QB missed the VOID threshold by 0.04 and should be read as if it had not.**

---

## 4. The too-good trigger fired. Escalated, not celebrated.

A1's ablation moved **+14.38% of the primary's own error**, seven times the 2% trigger committed in
advance. `CLAUDE.md` §8 says a result that looks too good is usually leakage. Decomposed before
write-up (`diagnostics3` D2):

- **Every one of 11 seasons is worse**, +0.95 to +3.16 carries MAE. Not one season carries it.
- Primary QB `carries` MAE **12.561** → ablated **14.368**.
- **What is left after the ablation:** `gshare_w`, `evidence`, `age`, `age2`, `experience`. The arm
  removes *both* volume regressors from a volume model and leaves only availability and age.

**Assessment: mechanical, not leakage.** A model asked to predict rushing carries with no rushing
history should do very badly, and it does. The trigger is doing its job — it fired on an ablation,
where "worse" is the expected direction, and the escalation is logged rather than waived. Registered
with `strategist` on the batch-3 thread.

---

## 5. What the coordinator source actually is, and what a backfill returned

`play_callers_preseason` is batch 2's pre-Week-1 Wikipedia staff-navbox read, not the end-of-season
`{{NFL final staff}}` rows. Batch 2 §3 establishes why that distinction is load-bearing.

**A tenure variable computed off a censored source is biased in one direction for exactly the
longest-serving coordinators**, so a backfill was attempted before the pre-commitment was written.

**It failed, for a documented reason, and the failure is a finding.** `coord_preseason --start-season
2004 --end-season 2009` returned **96 of 192 team-seasons as `no_revision_before_kickoff`: the club
staff navbox template pages did not exist on Wikipedia before roughly 2010.** What landed was 5 clubs
in 2007, 4 in 2008 and 12 in 2009 — partial *by club*, which is worse than a clean floor, so those
rows are present in the table and deliberately unused.

**Choice made and stated: restrict, floor at 2010.** Any spell still alive at 2010 is flagged
`oc_tenure_known = 0` and imputed, not reported as tenure. **Censoring measured before fitting:
exactly one club-season per year, 3.1%, zero in 2024.** The censoring does not bite. That is a
measurement, not a hope — and it is why the tenure nulls above are believable as nulls rather than as
artefacts of a truncated source.

---

## 6. Guardrails applied (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§6.1) | `before()` / `ngs_before()` / `rush_before()` gates; separate `outcomes()` accessor; per-target-season audit asserting max feature cutoff and max outcome season strictly < target. All 16 F1 arms × 11 (or 7) seasons passed |
| **The season-N reads, isolated** | the feature builder computes **only the blocks an arm declares**. Measured: **proxy reads 0** for all four primaries and for every A/S/X arm; 300 per OC-tenure arm, 134 for C1Q. An NGS or explosive arm is *provably* clean, not believed to be |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0. 2,271 WR / 1,441 RB / 1,041 TE / 869 QB player-seasons |
| **Multiple comparisons** (§6.3) | BH across the **campaign**, m = 24 fixed in advance, q = 0.10 and 0.05 |
| **Holdout** (§6.3) | 2025 sealed at the SQL gate. **Not opened.** No holdout spend requested |
| **Effect size** | every E1a as a % of the primary's own error; every candidate re-checked on the ADP board |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n, never player-seasons |
| **Coverage-flag confound** | three control arms registered in the family + a numeric VOID rule fixed in advance. **It fired on arm 3** |
| **Shrinkage constant** | `EXPL_K0 = 50` carries, fixed a priori, never tuned. D1a shows the geometry contributes nothing regardless |
| **"Too good" trigger** | 2% of primary error, committed in advance. **Fired on A1**; decomposed in §4 and escalated |
| **Pre-registration** (§6.3) | `factor-batch-3-precommit.md`, content committed `1c452a1` before the first fit |
| **Known defect in my own design** | rows 21–24 degenerate; §1(4) |

---

## 7. What I am not claiming

- **Not claiming explosive rush rate is an edge.** It is PROJECTION-ONLY (E2 < 0), it is dominated by
  a variable already in the database, and its E1b is 27× smaller than YPC's.
- **Not claiming the YPC → volume wire should ship.** It is **post-hoc**. It needs a `strategist`
  registration and a `backend` implementation, in that order. Its number here is a hypothesis with a
  measurement attached, not a licence.
- **Not claiming QB rushing is an edge over consensus.** A2 is PROJECTION-ONLY. A1 is an ablation and
  says only that the block already in the model is load-bearing.
- **Not claiming NGS separation is dead.** WR is VOID; **TE is MARGINAL on 7 seasons with a clean
  control** and is the one thing here worth a properly powered rerun.
- **Not claiming the ADP-board sign flip on B2r means the baseline should change.** §6.5 baseline #2
  is measured on the full universe and stays as it is.
- **Not treating any of this as final.** `strategist` has the design; `fable` has not attacked it.

---

## 8. Independent checks, because I do not grade my own work

| claim | who checks it | status |
|---|---|---|
| the design, the campaign family, the VOID rule, the too-good escalation, and my B2ra error | `strategist` | thread opened this session |
| the result once it exists, at maximum effort | `fable` | thread opened this session |
| the YPC → volume wire, before anything ships | `strategist` → `backend` | raised on the strategist thread |
| `pbp` and `ngs_receiving` in the rebuild path; the coordinator navbox 2010 floor | `data-ops` | thread opened this session |
| the factor ledger rows this batch dispositions | `librarian` | thread opened this session |
