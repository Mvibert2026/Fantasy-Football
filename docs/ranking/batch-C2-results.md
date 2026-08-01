# Batch C2 results — more factors, plus the RB high-carry breakpoint, against v2

**Conclusion first. Live document, updated as each arm completed — not written at the end.**

> ## GRADING IS SUSPENDED. This batch builds, runs, and records — it does not include or exclude
> ## anything.
>
> C1 found that its registered inclusion rule hands a BH-robust `INCLUDE` to seeded noise that
> provably cannot carry signal (false-positive rate measured at 9.6% of cells against a nominal
> 2.5%). `strategist` owns the replacement rule
> (`docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi.md`, BLOCKED-ON-YOU).
> **Every cell below is `PENDING-RULE` regardless of what its CI verdict says.** Re-grading once
> the replacement rule lands needs no refit —
> `python3 -m experiments.bottomup.v2.run_c2 --regrade`.

> ## All 12 arm-runs complete, 29 of 29 registered cells. **Two cells clear CI-level WIN, both at
> ## the noisier CTRL-D control, both smaller than that control's own placebo delta.**
>
> - **A5 QB** (implied team total, lagged): +0.0140, CI [0.0072, 0.0204], p = 0.0002 — but the
>   matched-control placebo (F0D at QB) produced +0.0216 on the *same 4-season window*, itself only
>   just short of its own CI bar (p = 0.0635). CTRL-D's placebo is not calibrated the way CTRL-A2's
>   is; A5 QB cannot be told apart from harness noise at this control without more seasons.
> - **A5k RB** (the *coverage indicator alone*, not the value): +0.0015, CI [0.0006, 0.0023],
>   p = 0.0002 — smaller than F0D's own RB placebo (+0.0080). **A5 RB itself is flat NULL
>   (−0.0000)**, so this is not the batch-7/C1 coverage-artifact pattern (treatment wins because of
>   its presence flag) — here the treatment doesn't win at all, only its control does, on a delta
>   about the size of `odds_snapshots`' own 2018-vs-earlier coverage boundary.
>
> **Everything else is NULL or HARM at the CI level**, all of it inside or below this batch's own
> placebo comparison. **Part B (the founder's RB carry-hinge) is confirmed underpowered as
> registered**: only 1 board-veteran RB-season across the entire graded population crossed 350
> carries in its feature year, and the arm's delta is effectively zero (−0.0002).
>
> **`F0D` (CTRL-D, n = 4 seasons) is noisier than `F0` (CTRL-A2, n = 7)** — the 4-season placebo
> won CI-level at RB (+0.0080, p = 0.0100) and TE (+0.0366, p = 0.0055), against 0 of 4 at the
> 7-season control. That is a second, independent measurement of the same mechanism C1's 34-draw
> replication found (shorter windows are more miscalibrated) and it directly bears on A5 (which
> shares CTRL-D): **A5's cells should be read as measured on the noisier of this batch's two
> controls, not adjusted for it here, since no adjustment rule is registered.**

Registration: `docs/ranking/factor-campaign-manifest/batch-C2.md`, committed at `ee87b53` before
any arm was fitted. m_b = 29 (20 Part A + 1 Part B + 8 placebo), confirmed by row count in
`experiments/bottomup/results/factor_c2_contrasts.csv`. Control: v2 games arm G0, pinned
(unchanged from C1).

---

## NEXT STEP

*Rewritten on every update. Written for a successor with none of this context.*

**Everything registered has run. Nothing in C2 is outstanding except what other roles own:**

1. **`strategist` ruling on C1's WIN criterion** — same blocking thread as C1
   (`docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi.md`). No factor in
   this batch may be graded INCLUDE/EXCLUDE until it lands. This batch adds one more argument for
   the replacement rule to be **control-window-aware**: a fixed CI bar cannot be right for both a
   7-season and a 4-season control, since this batch's own placebo shows the 4-season one wins
   spuriously far more often (2/4 vs 0/4 cells).
2. **A5's QB/RB cells specifically need the CTRL-D placebo bar applied, not the CTRL-A2 one**,
   whenever the replacement rule is written — do not naively apply a single global threshold across
   both this batch's controls.
3. **A candidate next batch (C3)**, if wanted: the ledger still has WOPR-adjacent alternatives at
   RB (the ledger does not currently have a dedicated RB opportunity-share composite beyond what
   batch 1 already tested and found NULL/earns-its-place-at-WR-only), N13 (explosive rush rate,
   `pbp`, RB), N9 (QB rushing volume, mostly already covered by the model's own `_QB_RUSH_VOLUME`
   spec and batch 3's rushing-block ablation — see that batch's finding before re-registering), and
   the O-line public-formula rows (N27, T1-23) once someone ingests `pbp`-derived Adjusted Line
   Yards.
4. **To re-grade after the rule change, with no refits:**
   ```
   python3 -m experiments.bottomup.v2.run_c2 --regrade
   ```
5. **State on disk after every arm:** `experiments/bottomup/results/factor_c2_cells.csv` (per
   position-season) and `factor_c2_contrasts.csv` (CI-graded, placebo-compared, BH not computed —
   29 rows, one per registered cell).

---

## Run log — every arm, one commit each

| arm | what | commit |
|---|---|---|
| F0 (placebo, CTRL-A2) | reproduces C1's CTRL-A numbers byte-for-byte | `6dab690` |
| F0D (placebo, CTRL-D, n=4) | 2 of 4 cells CI-WIN (RB, TE) — CTRL-D is noisier | `1e80cc8` |
| A1 (WOPR, WR/TE) | both NULL, both below placebo | `7cae66e` |
| A2, A2k (YAC per reception, RB) | both NULL, delta ~0 | `d213232` |
| A3, A3k (receiving share of RB's own points, RB) | both NULL; A3 +0.0101 largest RB delta, CI wide | `b3cb337` |
| A4, A4k (late-season role trajectory, RB/WR/TE) | RB HARM(CI)/NULL(k); WR NULL/NULL; TE identical deltas both arms (flagged, not resolved) | `1d48b22` |
| A5, A5k (implied team total, QB/RB/WR/TE, CTRL-D) | QB CI-WIN smaller than its own placebo; RB/WR/TE NULL; A5k RB itself CI-WIN | `c1b11f4` |
| B1 (RB carry-hinge, 350/375/400 knots) | NULL, confirms registered underpowered-arm prediction | `06f04cb` |

---

## Results table — all 29 registered cells

<!--C2-TABLE-START-->
| factor | position | control | n_seasons | coverage | delta | lo | hi | p | verdict | vs placebo (this batch's own instrument) |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 WOPR | WR | CTRL-A2 | 7 | n/a | -0.0021 | -0.0089 | 0.0048 | 0.525 | NULL | below (F0 WR +0.0005) |
| A1 WOPR | TE | CTRL-A2 | 7 | n/a | -0.0005 | -0.0078 | 0.0063 | 0.8995 | NULL | below (F0 TE +0.0303) |
| A2 YAC/reception | RB | CTRL-A2 | 7 | 0.9775 | +0.0004 | -0.0061 | 0.0070 | 0.8865 | NULL | below (F0 RB +0.0007) |
| A2k (yac_known control) | RB | CTRL-A2 | 7 | 0.9775 | +0.0046 | -0.0029 | 0.0124 | 0.2285 | NULL | clears (F0 RB +0.0007) |
| A3 receiving share of own pts | RB | CTRL-A2 | 7 | 0.9935 | +0.0101 | -0.0124 | 0.0286 | 0.3445 | NULL | clears (F0 RB +0.0007) |
| A3k (recpts_known control) | RB | CTRL-A2 | 7 | 0.9935 | +0.0001 | 0.0000 | 0.0003 | 0.672 | NULL | below (F0 RB +0.0007) |
| A4 late-season trajectory | RB | CTRL-A2 | 7 | 0.9726 | -0.0044 | -0.0089 | -0.0001 | 0.0405 | **HARM (CI)** | below (F0 RB +0.0007) |
| A4 late-season trajectory | WR | CTRL-A2 | 7 | 0.9798 | +0.0001 | -0.0012 | 0.0013 | 0.7975 | NULL | below (F0 WR +0.0005) |
| A4 late-season trajectory | TE | CTRL-A2 | 7 | 1.0000 | +0.0086 | 0.0000 | 0.0225 | 0.191 | NULL | below (F0 TE +0.0303) |
| A4k (late_known control) | RB | CTRL-A2 | 7 | 0.9726 | +0.0009 | -0.0022 | 0.0034 | 0.549 | NULL | clears (F0 RB +0.0007) |
| A4k (late_known control) | WR | CTRL-A2 | 7 | 0.9798 | +0.0001 | 0.0000 | 0.0003 | 0.186 | NULL | below (F0 WR +0.0005) |
| A4k (late_known control) | TE | CTRL-A2 | 7 | 1.0000 | +0.0086 | 0.0000 | 0.0225 | 0.191 | NULL | below (F0 TE +0.0303) |
| A5 implied team total | QB | CTRL-D | 4 | 1.0000 | **+0.0140** | 0.0072 | 0.0204 | 0.0002 | **WIN (CI)** | below (F0D QB +0.0216) |
| A5 implied team total | RB | CTRL-D | 4 | 1.0000 | -0.0000 | -0.0065 | 0.0039 | 0.969 | NULL | below (F0D RB +0.0080) |
| A5 implied team total | WR | CTRL-D | 4 | 1.0000 | +0.0040 | -0.0090 | 0.0175 | 0.741 | NULL | clears (F0D WR +0.0006) |
| A5 implied team total | TE | CTRL-D | 4 | 1.0000 | +0.0035 | -0.0080 | 0.0147 | 0.524 | NULL | below (F0D TE +0.0366) |
| A5k (itt_known control) | QB | CTRL-D | 4 | 1.0000 | +0.0000 | 0.0000 | 0.0000 | 1.000 | NULL (no change) | below (F0D QB +0.0216) |
| A5k (itt_known control) | RB | CTRL-D | 4 | 1.0000 | **+0.0015** | 0.0006 | 0.0023 | 0.0002 | **WIN (CI)** | below (F0D RB +0.0080) |
| A5k (itt_known control) | WR | CTRL-D | 4 | 1.0000 | +0.0009 | 0.0000 | 0.0021 | 0.1125 | NULL | clears (F0D WR +0.0006) |
| A5k (itt_known control) | TE | CTRL-D | 4 | 1.0000 | +0.0043 | 0.0000 | 0.0129 | 0.6425 | NULL | below (F0D TE +0.0366) |
| B1 RB carry-hinge (350/375/400) | RB | CTRL-A2 | 7 | n/a¹ | -0.0002 | -0.0027 | 0.0024 | 0.8875 | NULL | below (F0 RB +0.0007) |
| F0 PLACEBO | QB | CTRL-A2 | 7 | n/a | +0.0135 | -0.0043 | 0.0394 | 0.2645 | NULL | is the placebo |
| F0 PLACEBO | RB | CTRL-A2 | 7 | n/a | +0.0007 | -0.0007 | 0.0020 | 0.311 | NULL | is the placebo |
| F0 PLACEBO | WR | CTRL-A2 | 7 | n/a | +0.0005 | -0.0005 | 0.0016 | 0.5395 | NULL | is the placebo |
| F0 PLACEBO | TE | CTRL-A2 | 7 | n/a | +0.0303 | 0.0134 | 0.0459 | 0.0002 | **WIN (CI)** | is the placebo |
| F0D PLACEBO | QB | CTRL-D | 4 | n/a | +0.0216 | -0.0053 | 0.0507 | 0.0635 | NULL | is the placebo |
| F0D PLACEBO | RB | CTRL-D | 4 | n/a | +0.0080 | 0.0008 | 0.0151 | 0.0100 | **WIN (CI)** | is the placebo |
| F0D PLACEBO | WR | CTRL-D | 4 | n/a | +0.0006 | -0.0039 | 0.0063 | 0.905 | NULL | is the placebo |
| F0D PLACEBO | TE | CTRL-D | 4 | n/a | +0.0366 | 0.0123 | 0.0609 | 0.0055 | **WIN (CI)** | is the placebo |

¹ B1's `n_ge350_carries` (summed across all 7 graded seasons): **1** — see Part B write-up below.

**Every WIN cell in this table (A5 QB, A5k RB, F0 TE, F0D RB, F0D TE) is `PENDING-RULE`, not a
finding.** Two of the five are the placebo itself; the other two are smaller than or comparable to
their own matched control's placebo delta.

**Grading status, all factors: `PENDING-RULE`.**
<!--C2-TABLE-END-->

---

## Part A — factor by factor

### A1 — WOPR (WR, TE)

**NULL both positions**, both deltas negative or near-zero and both below their placebo comparison.
Registered downside (collinearity with `tshare_w`/`adot`-adjacent terms already in the model) reads
as the likely mechanism, though this batch does not isolate it.

### A2 / A2k — YAC per reception (RB)

**Both NULL, delta ~0.** Reused `factor_features7._yac` verbatim (batch 7's own block, never run
against v2). The old-frame measurement was also ~0 against a published external r = 0.421; moving
to v2's primary does not change the mechanism (an efficiency trait, fed to a volume-oriented
spec, contributes little to a *rank* order among established backs).

### A3 / A3k — receiving share of an RB's own points (RB)

**Both NULL.** A3 (+0.0101) is this batch's largest RB delta outside the placebo band, and it
clears the RB placebo (F0's +0.0007) on magnitude — but its CI is wide (`[-0.0124, +0.0286]`,
p = 0.3445) and does not exclude zero. Reported as the batch's one genuine near-miss, same
epistemic status C1 gave xFP-at-RB: a hypothesis worth a future confirmatory design, not a result.

### A4 / A4k — late-season role trajectory (RB, WR, TE)

**RB is a CI-level HARM** (-0.0044, `[-0.0089, -0.0001]`, p = 0.0405) — below the placebo band, so
not obviously a coverage artifact, but the paired control A4k is flat NULL, meaning the harm is not
attributable to the presence flag alone; it sits in the value columns (`late_ratio_w`/
`late_lift_grp`). WR is flat NULL both arms.

**TE: A4 and A4k report bit-identical deltas (+0.0086 to four decimal places, same CI) despite
adding different feature sets.** Investigated directly rather than left unexplained: a targeted
walk-forward re-run comparing the two arms' raw point projections shows they are **not**
identical — predictions differ by up to 2.5 points per player-season, only 0.3% of rows tie exactly.
The graded-population coverage for TE is 1.0000 (every board-veteran TE in every one of the 7
target seasons has `late_known = 1`), so A4k's only added column is a season-level constant among
the graded rows — which by Spearman's invariance to any per-season additive shift cannot move that
season's rank correlation on its own. That A4's *additional*, genuinely varying columns
(`late_ratio_w`, `late_lift_grp`) also fail to move rank order among the small graded TE population
(n≈10-14) in any of 7 separate seasons is a real but surprising finding, not an artifact of a
software bug (confirmed by the direct point-level diff). Recorded as an open oddity rather than
resolved further, since grading is suspended regardless.

### A5 / A5k — implied team total, lagged (QB, RB, WR, TE)

**The first read of `odds_snapshots` by any model in this project.** QB clears the CI bar
(+0.0140, p = 0.0002) but is **smaller than this batch's own QB placebo delta at the same control**
(F0D QB +0.0216, itself not CI-significant at p = 0.0635) — the two numbers are in the same
neighbourhood, and CTRL-D (4 seasons) is measurably the noisier of this batch's two controls (see
the headline). RB/WR/TE are NULL on the value column. **A5k RB clears CI (+0.0015, p = 0.0002)
while A5 RB itself does not (-0.0000)** — the coverage indicator wins where the value doesn't, on a
delta about the size of the 2018 odds-coverage boundary itself; not the batch-7/C1 coverage-artifact
pattern (which requires the *treatment* to win on the back of its control), but flagged as adjacent
to it and worth the replacement rule's attention.

---

## Part B — the RB high-carry-season breakpoint

**NULL, confirming the registered underpowered-arm prediction rather than falsifying the
workload-cliff hypothesis.** One arm, three fixed knots (350/375/400 carries, the founder's own
values, used as spline knots and never searched — batch-C2.md's registered design choice to run a
single non-linearity test rather than a three-way cutoff sweep). Delta -0.0002, CI
`[-0.0027, +0.0024]`, effectively the null result C1's numerical-hygiene convention treats as "no
change."

**The reason is power, not the hypothesis being wrong**: summed across all 7 graded seasons, only
**1** board-veteran RB-season had ≥350 carries in its feature (prior) year. Measured directly
before running (batch-C2.md): 3 RB player-seasons league-wide hit ≥350 carries in the 2011-2023
feature-season window, 2 hit ≥375, 0 hit ≥400 — and the graded (board-veteran) population is a
strict subset of that. **This project cannot test the founder's literal threshold values with any
power on its current data.** A workload-cliff effect could exist and this arm would not detect it.
The honest framing, unchanged from what batch 3/4 found in the old frame: the hypothesis remains
untested in any statistically meaningful sense, not falsified.

---

## The placebo, this batch's own instrument

**F0 (CTRL-A2, n=7) reproduces C1's CTRL-A numbers byte-for-byte** (same generator, same salt,
same control parameters) — the strongest possible confirmation that this batch's harness reuse is
correct. Its one CI-WIN (TE, +0.0303) is the same defect C1 already characterized (discreteness +
small-n bias in season-block bootstrapping Spearman deltas at n=7).

**F0D (CTRL-D, n=4) is measurably noisier: 2 of 4 cells CI-WIN (RB +0.0080 p=0.0100, TE +0.0366
p=0.0055) against 0 of 4 at CTRL-A2's n=7.** This is a single extra data point on C1's already-
published mechanism (shorter windows → more discrete per-season deltas → more spurious CI
exclusions of zero), not a fresh calibration study — one draw per control here, not C1's 34-draw
replication. It is enough, though, to say plainly: **A5's QB and RB cells are measured on the
noisier of this batch's controls, and neither of A5's two CI-level effects (QB WIN, RB via A5k)
would be reported as a finding under C1's own published false-positive-rate logic.**

---

## Scope notes, unchanged from registration

No arm reads consensus, ADP, or ECR in its ordering path. No arm reads a season-N proxy (asserted,
not believed — every arm passes `n_preseason_proxy_reads == 0`). No weights are tuned. No factors
are stacked. The 2025 holdout is not opened, and nothing in this batch would warrant opening it — a
result that appears to warrant it stops and escalates to the founder per `CLAUDE.md` §6.3.
