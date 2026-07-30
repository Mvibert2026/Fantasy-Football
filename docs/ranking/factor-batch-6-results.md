# Factor batch 6 — results

**Ranker, 2026-07-30.** Design and every endpoint in `factor-batch-6-precommit.md`, committed at
`f6e09da` **before any arm was fitted**. Runner `3541f40`. All 23 registered tests ran **once**. No
arm was re-specified after a result was seen.

**Headline, and it is a negative.** Registry **#18 (xFP)** — "the highest-value unbuilt Tier 1 item"
— is **rejected with evidence in its strongest form**: replacing realised prior points per game with
a prebuilt xFP model's *expected* prior points per game is **worse at all four positions**, and the
overlap diagnostic registered in advance says why. **N10 (passing efficiency)** produces this
project's **first non-null QB-specific inputs** — ANY/A and passer rating both improve the QB
attempts projection on the full universe *and* on the draft board — but **neither improves the QB
ranking**, and passer rating makes it measurably worse. **N11 (sack avoidance)** is MARGINAL and
board-negative.

**So: QB now has two measured inputs and the board cannot use either of them yet.** §7 says what that
points at next, and it is not another volume arm.

---

## 0. What ran, and the checks that passed before any result was read

| | |
|---|---|
| Target seasons | 2014–2024 (11) for every arm. No arm had a shorter window |
| Universe | frozen pre-season, busts retained at 0 (QB 869 / RB 1,441 / WR 2,271 / TE 1,041 player-seasons) |
| Holdout | 2025 sealed at the SQL gate. **Not opened** |
| **Season-N reads** | **zero, proven not asserted.** Every arm ran `allow_preseason_proxy=False`; `n_preseason_proxy_reads == 0` on all 23 arms and all 4 primaries, enforced as a `RuntimeError` |
| Uncertainty | season-block bootstrap, 4,000 reps, seasons the unit |
| Leak trigger (2% of primary error) | **0 arms fired.** Largest improvement anywhere is 1.26% |
| Campaign m | **80** — see the correction immediately below. Every survivor carries a **breaking m** |

> ### The denominator was corrected after the run, and the device built to allow that did its job
>
> Batch 6 registered **m = 23 before fitting** and graded at a campaign denominator of **47** (its
> own 23 plus batch 3's 24). It did not know that batch 5 had already opened a campaign manifest,
> **C2** (`docs/ranking/factor-campaign-manifest/`), whose rule is
> `M_campaign = max(Σ m_b, FLOOR = 80)` and which excludes batches 1–3 from retroactive re-grading.
> Two concurrent batches independently built a manifest for the same problem without seeing each
> other. **C2 wins** — one file per batch, safe under concurrent writers — and batch 6's manifest
> is retired to a pointer.
>
> **The correct denominator was 80, and every grade below is at 80.** Nothing was rerun, because
> the pre-commitment required every surviving arm to carry a **breaking m** — the largest
> denominator at which it would still clear BH q=0.10.
>
> **Exactly one arm changed, and it moved conservatively: X3 (xFP luck residual) at RB, breaking
> m = 56 — BOARD-NEUTRAL at 47, MARGINAL at 80.** Every other graded arm has a breaking m of
> 140–1721 and is untouched. This is the correction working as designed rather than a result
> surviving a denominator chosen after the fact; the CSV carries both `bh_c47_*` and `bh_c80_*`
> columns so the change is checkable.

**Coverage, measured on the ADP board (gate 0.80, set before the coverage was known):**

| position | `qbeff_known` | `cpoe_known` | `xfp_known` |
|---|---|---|---|
| QB | 0.938 | 0.938 | 0.938 |
| RB | 0.110 | 0.092 | **0.836** |
| WR | 0.208 | 0.206 | **0.897** |
| TE | 0.076 | 0.076 | **0.937** |

Every gate that mattered passed. No cell was marked NO DATA. (The QB-efficiency flags are near-zero
at RB/WR/TE because those players do not throw — the P and K arms are QB-only by design and were
never gated on those cells.)

**The VOID rule did not fire anywhere, and the reason is worth recording.** Batch 2 lost three arms
because a "we know his club" coverage flag was 95–97% of the effect. Here the coverage controls are
**numerically zero**: Pc, P4c and X4c at QB/WR/TE all return |E1a| ≈ **2×10⁻¹⁴** — floating-point
noise, because those flags are perfectly collinear with `present_1`/`evidence`, which the model
already holds, and least squares returns an identical fit. RB's X4c is the only one with a real
value, −0.0058, which is **1.2%** of its paired treatment arm — far under the 50% threshold.

> **One artefact to name rather than let stand.** WR's X4c is *graded* MARGINAL because its bootstrap
> interval excludes zero. Its point estimate is **−2.2×10⁻¹⁴ targets**. That is a rounding-scale
> number, not an effect; the grading rule has no magnitude floor. It is reported as a grader artefact
> and carries no claim.

---

## 1. The full table — 23 arms, E1a = full-universe component MAE, negative = better

BH at **campaign m = 80, q = 0.10** (campaign C2's floor). `breakM` = the largest campaign denominator at which the arm
would still clear BH q=0.10, so a later reader can re-check it against the finished manifest.

### N10 — passing efficiency over volume (QB, E1 component = `attempts`, primary MAE 112.93)

| arm | E1a | 95% CI | % of error | p | E1b (board, primary 136.94) | E2 (board ρ) | grade |
|---|---|---|---|---|---|---|---|
| **P2 ANY/A** | **−1.425** | [−2.054, −0.844] | **−1.26%** | 0.0013 | **−3.058 (−2.23%)** | −0.0118 [−0.047, +0.022] | **PROJECTION-ONLY**, breakM **308** |
| **P3 passer rating** | **−0.960** | [−1.322, −0.548] | **−0.85%** | 0.0010 | **−3.453 (−2.52%)** | **−0.0180 [−0.0350, −0.0005]** | **PROJECTION-ONLY**, breakM **308** |
| P1 EPA per dropback | −1.218 | [−2.018, −0.401] | −1.08% | 0.0200 | +0.601 (+0.44%) | −0.0128 [−0.049, +0.026] | MARGINAL |
| P4 CPOE | +0.090 | [−0.443, +0.579] | +0.08% | 0.7505 | +0.231 | +0.0025 | NULL |
| P4c CPOE coverage CONTROL | +2e−14 | — | — | 0.3996 | −3e−13 | 0.0000 | NULL |
| Pc QB-efficiency coverage CONTROL | +2e−14 | — | — | 0.3996 | −3e−13 | 0.0000 | NULL |

### N11 — sack avoidance (QB)

| arm | E1a | 95% CI | % | p | E1b | E2 | grade |
|---|---|---|---|---|---|---|---|
| K1 sack rate per dropback | −0.532 | [−0.945, −0.112] | −0.47% | 0.0380 | +0.572 (+0.42%) | +0.0041 | MARGINAL |

### #18 — expected fantasy points (all four positions)

| arm | pos | E1a | 95% CI | % of error | p | E1b | E2 (board ρ) | grade |
|---|---|---|---|---|---|---|---|---|
| **X2 REPLACE `ppg_w`** | **RB** | **+0.768** | [+0.564, +0.992] | **+1.55%** | 0.00006 | +1.069 (+1.64%) | **−0.0141 [−0.0249, −0.0034]** | **HARMFUL**, breakM **1721** |
| **X2 REPLACE `ppg_w`** | **WR** | **+0.395** | [+0.240, +0.545] | **+1.64%** | 0.0007 | +0.309 (+0.98%) | −0.0101 [−0.026, +0.006] | **HARMFUL**, breakM **308** |
| **X2 REPLACE `ppg_w`** | **QB** | **+0.776** | [+0.388, +1.141] | **+0.69%** | 0.0036 | +1.353 (+0.99%) | −0.0060 | **HARMFUL**, breakM **140** |
| X2 REPLACE `ppg_w` | TE | +0.129 | [+0.038, +0.223] | +0.66% | 0.0272 | +0.305 (+1.08%) | **−0.0148 [−0.0304, −0.0005]** | MARGINAL-HARMFUL |
| X1 add xFP/g | QB | −1.028 | [−1.868, −0.210] | −0.91% | 0.0473 | +0.730 | +0.0066 | MARGINAL |
| X1 add xFP/g | RB | −0.472 | [−0.879, −0.087] | −0.95% | 0.0468 | +0.376 | +0.0044 | MARGINAL |
| X1 add xFP/g | WR | −0.008 | [−0.032, +0.021] | −0.03% | 0.5986 | +0.101 | −0.0036 | NULL |
| X1 add xFP/g | TE | +0.061 | [−0.002, +0.134] | +0.31% | 0.1400 | −0.047 | −0.0034 | NULL |
| X3 luck residual | RB | −0.459 | [−0.744, −0.182] | −0.93% | 0.0106 | **+0.344** | +0.0036 | **MARGINAL** (BOARD-NEUTRAL at m=47; breakM **56**) |
| X3 luck residual | QB | −0.686 | [−1.360, −0.074] | −0.61% | 0.0770 | +0.236 | +0.0048 | MARGINAL |
| X3 luck residual | WR | −0.021 | [−0.054, +0.020] | −0.09% | 0.3131 | +0.009 | −0.0028 | NULL |
| X3 luck residual | TE | +0.045 | [−0.010, +0.127] | +0.23% | 0.2791 | +0.010 | −0.0017 | NULL |
| X4c coverage CONTROL | QB/WR/TE | ≈0 (1e−14) | — | — | — | ≈0 | 0.0000 | NULL (WR grader artefact, §0) |
| X4c coverage CONTROL | RB | −0.006 | [−0.021, +0.003] | −0.01% | 0.4369 | −0.016 | 0.0000 | NULL |

**Counts at campaign m = 80:** NULL 10 · MARGINAL 7 · HARMFUL 3 · PROJECTION-ONLY 2 ·
MARGINAL-HARMFUL 1. **Zero SURVIVES.**

**Survivors under the campaign correction.** Five arms clear BH at m = 80, with breaking m of 140,
308, 308, 308 and 1721 — all robust to a campaign several times larger than the registered one. The
sixth, **X3-RB, did not survive the correction from 47 to 80** (breaking m 56) and is graded
MARGINAL. **Campaign C2's registered batches are 4 (m=8), 5 (m=17), 6 (m=23) and 7 (m=16), Σ = 64,
so the floor of 80 binds.** If further batches register, only breaking m matters, and nothing below
140 remains.

---

## 2. #18 xFP — rejected with evidence, and the pre-registered diagnostic explains it

The registry's claim was that xFP **isolates luck from skill**. Tested three ways at four positions:

**X2 is the claim in its strongest form, and it loses at every position.** Swapping realised prior
points per game for expected prior points per game costs **+1.64% (WR), +1.55% (RB), +0.69% (QB),
+0.66% (TE)** of the model's own error, three of four BH-significant at the campaign denominator, all
four worse on the ADP board as well, and all four with **negative** board Spearman — two of them
(RB, TE) with intervals excluding zero. **Realised production beats a prebuilt expected-points model
as a predictor of next-season opportunity, at every position, on eleven seasons.**

**The mandatory overlap diagnostic, run regardless of result and pre-committed with a threshold:**

| position | corr(`xfp_pg_w`, `ppg_w`) | corr(`xfp_pg_w`, lagged volume) | corr(residual, `ppg_w`) |
|---|---|---|---|
| WR | **0.964** | 0.989 | 0.470 |
| RB | **0.961** | 0.856 | 0.465 |
| TE | **0.961** | 0.985 | 0.366 |
| QB | 0.949 | 0.887 | 0.457 |

The pre-commitment fixed the rule in advance: *if `corr(xfp_pg_w, ppg_w) > 0.95`, X1/X2 are reported
as a restatement of `ppg_w` whatever their p-values say.* **That rule fires at WR, RB and TE.** So
the honest statement is not "xFP is a worse feature" — it is:

> **xFP is 95–96% the same object as realised points per game, and 86–99% the same object as the
> lagged volume column already in the spec. The few percent where it differs makes the projection
> worse, not better.** #19 already established why: the model's existing empirical-Bayes TD shrinkage
> extracts most of the luck correction, and discarding a player's own TD rate was HARMFUL at all four
> positions. xFP re-does that job less well and throws away the part the model was doing right.

**X1 (add xFP alongside, do not replace)** is MARGINAL at QB and RB, NULL at WR and TE, and **worse
on the ADP board at three of four positions**. No edge.

### The one registered directional prediction — and it failed

The pre-commitment stated, before fitting: *if the luck story is right, `xfp_resid_pg_w` should carry
a **negative** coefficient — over-performance regresses.* Fitted coefficients, all 44 walk-forward
fits:

| position | mean coefficient | range | seasons negative |
|---|---|---|---|
| QB | **+0.989** | +0.178 … +2.039 | **0 of 11** |
| RB | **+0.894** | +0.712 … +1.004 | **0 of 11** |
| WR | **+0.177** | +0.051 … +0.225 | **0 of 11** |
| TE | −0.216 | −0.654 … −0.037 | 11 of 11 |

**The prediction is wrong at three of four positions, unanimously and in every season.** Beating your
expected points last year predicts *more* opportunity next year, not less. The residual is not
measuring luck that regresses; it is measuring something the play-context model cannot see — most
plausibly that a player who outperforms his context is being given better context by his coaches next
year. This is the alternative outcome the pre-commitment named ("a different finding, and must be
reported as one"). It is stated here as a failed prediction, not retro-fitted into a success.

It also does not rescue X3: the arm is MARGINAL at RB and QB, NULL at WR and TE — and at RB, where it was
significant under the wrong denominator, the entire gain sat among players nobody drafts (E1b
**+0.344 worse** on the ADP board), which is batch 2's named failure mode.

---

## 3. N10 / N11 — QB's first non-null inputs, and why the board still cannot use them

**Two arms clear both E1a and E1b**, which no QB-specific factor in this project had done before:

- **ANY/A** improves the QB attempts projection by **1.26%** of the model's own error on the full
  universe and by **3.06 attempts (2.23%)** on the draft board.
- **Passer rating** improves it by **0.85%** and by **3.45 attempts (2.52%)** on the board.

Both survive BH at campaign m = 47 with breaking m = 308, i.e. they are robust to any plausible
campaign size. Both also improve the declared secondary `mae_pass_yards` (−8.5 and −6.8 yards).

**And both are graded PROJECTION-ONLY, because the ranking does not improve.** E2, the ADP-board
Spearman, is negative for both — and for passer rating the interval **excludes zero on the wrong
side**: **−0.0180 [−0.0350, −0.0005]**. Under `CLAUDE.md` §6.5 a factor that does not beat consensus
on the decision-relevant metric has no edge, regardless of how good the component number looks.

> **This is the most decision-relevant sentence in the batch: at quarterback, projecting attempts
> better does not rank quarterbacks better, and one of the two arms that projects attempts best ranks
> them measurably worse.** The volume channel is improvable and improving it does not help.

**P1 EPA per dropback — the strongest claim in the external sweep — is the weaker arm here.** It beats
the primary on the full universe (−1.08%) but is **worse on the draft board** (+0.44%), and it is not
BH-significant at the campaign denominator. Two independent shops called EPA/dropback the stickiest QB
stat; on our data it does less than a passer rating anyone can compute from a box score.

**P4 CPOE is NULL** (+0.08%, p = 0.75). The one metric in the batch that genuinely requires a model
the box score cannot produce contributes nothing to the attempts channel.

**K1 sack rate is MARGINAL and board-negative** (−0.47% full universe, **+0.42% worse on the board**).
Not an edge.

---

## 4. Descriptive secondaries — outside the family, no claim attached

Reported because "does QB have a usable input" is not answerable from a component MAE alone.
**None of these is a test. None entered m. None may be quoted as a finding.**

### 4a. The external stickiness claims, measured on our data

QBs with ≥100 dropbacks in consecutive seasons, 1999–2023, 782 pairs (562 for CPOE, 2006+):

| metric | YoY Pearson | YoY Spearman | external claim |
|---|---|---|---|
| EPA per dropback | **0.473** | 0.460 | SumerSports: "stickiest QB stat since 2021, **r≈0.60**" |
| Passer rating | 0.471 | 0.468 | — |
| CPOE | 0.472 | 0.450 | — |
| Sack rate | 0.471 | **0.484** | SumerSports: **r≈0.50**, "second-stickiest" |
| ANY/A | 0.422 | 0.407 | — |

**The claimed ordering does not reproduce.** EPA, passer rating, CPOE and sack rate are
indistinguishable at ~0.47, and ANY/A is the *least* sticky of the five. The sack-rate number (0.471)
is close to its claimed 0.50; the EPA number (0.473) is well below its claimed 0.60 — consistent with
`analyst-factor-sweep-2026-07-30.md` §0's warning that every published correlation there is measured
on survivors and is an upper bound under §6.2.

**And stickiness is not the question.** ANY/A is the least persistent metric of the five and the best
performing arm in §3. `analyst-factor-sweep` §3 flagged exactly this ("sticky ≠ predictive") as a
methodology finding that applies to us; batch 6 is a direct instance of it.

### 4b. Against outcomes, and against what the market has already priced

Lagged metric vs realised season-N QB points **under this league's rules**, Spearman, mean over 11
seasons, ~72 QBs per season, busts retained:

| metric | vs season-N points | vs the residual on consensus ADP |
|---|---|---|
| ANY/A | **+0.560** | +0.148 |
| Passer rating | +0.553 | +0.121 |
| EPA per dropback | +0.519 | **+0.159** |
| CPOE | +0.356 | +0.129 |
| Sack rate | −0.188 | −0.045 |

The second column is the one that matters and the one most likely to be misread. It says: after
consensus ADP, lagged passing efficiency still correlates **~+0.13 to +0.16** with what a quarterback
actually did. **That is descriptive on n = 11 seasons of ~19 drafted QBs, `CLAUDE.md` §6.5 says a
beats-consensus claim cannot reach significance on this sample, and the confirmatory arms in §3 found
no ranking gain.** A positive number here alongside a negative E2 is not a contradiction — it is the
difference between "correlates with the residual" and "improves the ranking when put in the model",
and this batch measured the second one and it was not there.

---

## 5. What this changes in the registry

Proposed, not applied — `docs/test-registry.md` and `docs/factor-ledger.md` are shared files and three
factor batches were running concurrently. Handed to `librarian` as a thread rather than edited here.

| row | was | should be |
|---|---|---|
| **#18 / T1-18 xFP** | untested, "highest-value unbuilt Tier 1 item" | **rejected-with-evidence.** Replacing `ppg_w` with xFP is worse at all four positions (+0.66% to +1.64%, 3 of 4 BH-significant, campaign m=47); adding it is MARGINAL at best and board-negative; the luck residual is BOARD-NEUTRAL at best. `corr(xFP/g, points/g) = 0.95–0.96` — a restatement of a column the model already holds |
| **N10 passing efficiency** | untested | **measured. PROJECTION-ONLY at QB.** ANY/A −1.26% / −2.23% on the board; passer rating −0.85% / −2.52%; both BH-significant, breakM 308; **both E2-negative**, passer rating's E2 CI excludes zero on the wrong side. EPA/dropback MARGINAL and board-negative. CPOE NULL |
| **N11 sack avoidance** | untested | **measured. MARGINAL, board-negative.** −0.47% full universe, +0.42% worse on the board |
| **T0-10 / N4 / N16 red-zone, first downs, YAC** | "needs PBP, PBP now ingested" | **still blocked.** `pbp` was ingested with 24 columns and carries no `epa`, `cpoe`, `sack`, `success`, `first_down_pass` or `yards_after_catch`. Thread open to `data-ops` |
| Sweep §1's "`passing_cpoe` only 11% populated" | stated as a computability limit | **wrong.** 2.7% across all positions, **99.9%** on QB rows with ≥10 attempts, 2006+; `passing_epa` **100%** populated 1999–2025 |

---

## 6. Threats to this result, stated by me rather than left for the reviewer

1. **The arms test the volume channel only.** §4a of the pre-commitment registered this before
   fitting: `ShrunkRate` has no covariate mechanism, so "does efficiency predict future *efficiency*"
   was not tested. A null in §3 is a null about **opportunity**, not about efficiency in general.
2. **xFP's model was fitted on all seasons including the target.** Named in the pre-commitment §6. It
   puts no player-specific season-N information into an N−1 feature, but it is non-zero contamination
   — and it points *toward* xFP, which makes the negative result stronger rather than weaker.
3. **xFP is PPR, this league is half-PPR with stacking bonuses.** Verified (Dotson 2023: 124.8 =
   49 + 51.8 + 24 exactly). It was used as a usage index only. A version rescored under our rules is
   a different, untested object.
4. **The xFP result is not reproducible from the database alone.** `model_version_requested` = the
   literal `latest`; the only anchor is `ingested_at = 2026-07-30T19:55:20Z`, `nflreadpy 0.1.5`.
   Thread open to `data-ops`.
5. **E2 is underpowered at QB, WR and TE** (7 seasons) and was declared so before running. That cuts
   both ways: it weakens "no ranking gain" as much as it would have weakened a ranking gain. What it
   does *not* excuse is P3's E2 interval excluding zero on the wrong side.
6. **Eleven seasons, heavily autocorrelated.** Seasons are the bootstrap unit and the t-test's n, but
   the same quarterbacks recur.

---

## 7. What this points at next — one recommendation, not a list

The pre-commitment's stopping condition said: *if P1–P4 and K1 are all null, N10/N11 are dead on this
specification and the next move is the rate-channel specification, not a third volume re-specification.*

**They were not all null, and that makes the recommendation sharper rather than weaker.** Two arms
improved the QB attempts projection significantly and on the draft board, and the ranking still did
not improve. So the QB ranking's error is **not in the attempts channel**. It is in the rate channel
(`ypa`, `tdpa`, `intpa`), in the rushing channel (batch 3's territory), or in availability.

**The specification to register next is the one §4a deferred**: a covariate on `ShrunkRate`, so that
"does last season's efficiency predict next season's efficiency beyond the player's own shrunk lagged
rate" becomes answerable.

**And the mechanism to do it already exists — built concurrently, by batch 7, for a different
position.** `factor-batch-7-precommit.md` §2 registers a *batch-local subclass* that adds one linear
covariate to one declared rate: after the ordinary fit, the residual of the realised rate against the
model's own shrunk prediction is regressed on the centred covariate by weighted least squares,
weights = the rate's own denominator, veterans only. **One extra parameter, an overridden
`_make_model`, and `pos_model.py` untouched.** Batch 7 uses it on `tdpc` (inside-5 conversion) and
`ypr` (YAC per reception) at RB.

Batch 6 deferred the same construction on the grounds that it required editing shared model code.
**That premise was wrong, and batch 7 found the way around it on the same day.** So the QB
rate-channel test is not a build — it is batch 7's subclass pointed at `ypa`, `tdpa` and `intpa`
with `epa_db_w`, `anya_w`, `pratg_w`, `cpoe_w` and `sackrate_w`, all of which this batch has already
built and validated. What is still genuinely a `strategist` question is the *design*: which rates it
may attach to, how many tests that is in the campaign denominator, and whether the QB ranking error
is even in the rate channel rather than in availability or the rushing stream.

**What must not happen:** a third volume arm at QB. Five have now been run.

---

## 8. Who checks this, because I do not check my own work

| claim | independent check | status |
|---|---|---|
| the design, the campaign family, the breaking-m device, the decision rules | **`strategist`** | thread open |
| the rate-channel specification proposed in §7 | **`strategist`** | in the same thread |
| the result | **`fable`**, maximum effort, separate budget | to be dispatched |
| `pbp`'s missing columns and `ff_opportunity`'s unpinned version | **`data-ops`** | thread open, `2026-07-30-pbp-was-ingested-without-epa-cpoe-sack-and-ff-op` |
| registry and ledger row changes in §5 | **`librarian`** | thread open |
| shipping anything (nothing here is shippable) | **`backend`** | not required — zero arms graded SURVIVES |
