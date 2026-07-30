# ADR-DRAFT — Which market rank series the board's value curve is fitted on

**Status:** Proposed (ruling issued; number to be allocated by `tools/handoffs.py adr next` at landing)
**Date:** 2026-07-30
**Owner:** Strategist (ruling) / Ranker + Backend (execution)
**Answers:** `docs/handoffs/2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar.md` item 2
**Related:** PR-004 §2 (the founder's ADP-is-not-consensus correction), assessment §6.2

---

## 0. The ruling

**NO to refitting the board's rank→points curve on FFC ADP as proposed.**

**Conditional YES to a narrower path**, gated by one cheap exchangeability measurement with a
decision rule pre-committed in §4 below. If that measurement fails, the refit is **rejected
permanently** and the three-season limitation is reported as a limitation rather than engineered
away.

---

## 1. What was actually asked

Refit `E[our_points | positional market rank]` on FFC half-PPR ADP (2018–2024, 12-team) instead of
`fantasypros_ecr` (2021–2025, `scoring_format` NULL on all 2,540 rows), to raise the
board-vs-anything comparison from **three** evaluation seasons to **six**. Argued explicitly as a
power argument only, because today's H1 measured NULL — ADP is *not* more accurate than expert
consensus at predicting realised pick order (mean gap −1.27 picks, in consensus's favour).

The ranker was right to route this rather than take it. Three things are wrong with it, and only one
of them is the one the ranker flagged.

---

## 2. The three objections, in increasing order of how badly they bite

### 2.1 It is not a power gain on a fixed estimand. It changes the estimand.

`E[points | FantasyPros ECR positional rank]` and `E[points | FFC ADP positional rank]` are different
conditional expectations, over different conditioning variables, on different league sizes (12-team
vs this league's 10), over different populations. Six seasons of the second is not six seasons of the
first.

This is the founder's own correction from PR-004 §2, applied one layer further in:

> *"Market ADP is not consensus rankings — people use consensus rankings, not ADP."* … **"The
> baseline is not swapped to ADP**, not even to buy FFC's deeper history. Depth bought by measuring a
> different quantity is not depth."

PR-004 applied that to the *baseline* — the yardstick. The present request is about the *input* —
what the board is made of. Those are genuinely different questions, and I am not going to pretend the
founder already answered this one. But the principle transfers, and it transfers *harder*, because
assessment §1.1 established that **100% of the board's content lives on the input side.** The board
has no independent player-level opinion; it *is* a monotone re-scoring of its rank input. Change the
rank series and you have not tuned a parameter, you have changed what the object is.

### 2.2 Train/serve mismatch, unaddressed by the proposal

FFC has no 2025 and no 2026. The 2026 board's rank input is `fantasypros_csv_2026draft` consensus,
and it will stay consensus. So the proposal is: **fit the slopes on FFC ADP rank, serve them on
FantasyPros consensus rank.** Nothing in the proposal reconciles the two scales.

The intercept is harmless — it cancels in VBD (the ranker's own pass-3 §0 reproduced all 510 board
rows from four slopes and four replacement ranks). **So the entire transferred quantity is four
slopes**, in points per log-rank:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| current slope (fitted on ECR) | −49.38 | −50.62 | −41.21 | −30.45 |

If FFC ADP rank and FantasyPros ECR rank are not on the same scale — and there is a specific,
mechanical reason to think they are not — then a slope fitted on one and applied to the other is
biased.

### 2.3 The bias lands exactly on the board's only proprietary content, and QB is the worst case

The board's whole opinion is the *relative* steepness of the four slopes, which sets the positional
tilt. Assessment §2 measured that tilt: **all twelve of the board's largest top-100 disagreements
with consensus are quarterbacks or tight ends** (mean signed Δ: QB **+5.3**, TE **+10.6**, RB −1.2,
WR −1.8; the three biggest are Josh Allen +20, Lamar Jackson +20, Travis Kelce +19).

Now consider what ADP is at QB in a **1-QB league**. Stated expert rankings order quarterbacks by
value. Realised draft position orders them by *when people actually take them*, which in a 1-QB
league is systematically late, because drafters correctly price the positional scarcity. **ADP rank
at QB therefore encodes a market behaviour; ECR rank at QB encodes a value opinion.** A slope fitted
on the first and served on the second re-prices the exact channel — QB tilt — that constitutes the
board's largest claim.

RB and WR are the mild cases: their tilts are −1.2 and −1.8 places, so a perturbation of two places
can **reverse the sign of the board's opinion** at two of four positions. That is the concrete
decision-relevant harm, and it is why §4's threshold is stated in rank places rather than in
percentage of slope.

### 2.4 H1's NULL does not rescue the argument

H1 tested whether ADP is *more accurate at predicting realised pick order*. That is a statement about
ADP as a forecast of drafter behaviour. It is silent on whether ADP rank and ECR rank are
**interchangeable as a conditioning variable for a value curve** — a different property
(exchangeability of the conditioning distribution), which nobody has measured. The ranker is right
that H1 forbids the accuracy argument. The surviving power argument still needs exchangeability, and
the request assumes it.

---

## 3. A fourth objection the proposal does not distinguish, and it is structural

Assessment §6.2 presents the refit as an **evaluation-side** move: *"doubles the power of every
board-vs-anything comparison at zero model complexity."* But the slopes feed `projected_points`,
which feeds VBD, which feeds rank ordering, tiers, availability and the recommender. So there are
only two possibilities and neither is what §6.2 describes:

| | Consequence |
|---|---|
| **Refit is used for shipping too** | It is a **product change**, not an evaluation change. It changes every number on the board and must clear the primary metric's own gate before it lands. "Zero model complexity" is true and irrelevant — the cost is not complexity, it is that the shipped object changed |
| **Refit is used for evaluation only** | The six-season result is about **an object that does not exist**. Power bought this way is not power |

**Stated as a standing rule:** *you cannot buy evaluation power by evaluating a different object than
the one you ship.* This applies to any future proposal of the same shape, not just this one.

---

## 4. The narrower path, and its pre-committed decision rule

The exchangeability assumption in §2.2 is **directly measurable on data already in `nfl.db`**, over
the seasons both sources cover, at a cost of fitting eight curves. It is not a test of any football
hypothesis — it is a calibration/coverage check, the same category PR-004 §3 already established as
safe to run before a freeze because it reveals nothing about any effect. **It does not enter any FDR
denominator.**

### 4.1 The measurement — specified precisely enough to hand to `backend`

Over the overlap seasons only, **2021–2024** (`fantasypros_ecr` starts 2021; FFC half-PPR ends 2024;
2025 sealed and not touched):

1. For each source `s ∈ {fantasypros_ecr, ffc_half_ppr_12team}` and each position
   `p ∈ {QB, RB, WR, TE}`, fit `points = a + b·ln(positional rank)` on that source's own board
   universe, outcomes scored with `scoring.score_offensive_game` under this league's rules, **busts
   retained at 0**, no games filter.
2. Report `b_ECR(p)`, `b_FFC(p)`, and `Δb(p) = b_FFC(p) − b_ECR(p)`, each with a **season-level**
   bootstrap 95% CI (n=4 seasons, 10,000 draws, integer seed recorded, `degenerate=True` surfaced —
   the interval will be wide and that is the point).
3. **The decision-relevant readout, which is the one that actually governs:** rebuild the 2026 board
   twice — once with `b_ECR`, once with `b_FFC`, everything else identical, both served on the same
   `fantasypros_csv_2026draft` consensus ranks — and report the **top-100 mean signed Δ-vs-consensus
   per position** for each, i.e. the two versions of the `+5.3 / −1.2 / −1.8 / +10.6` row.

### 4.2 The rule, committed before the numbers exist

**APPROVE the FFC refit iff both hold:**

| | Criterion |
|---|---|
| (a) | the induced **top-100 positional tilt** changes by **≤ 2.0 rank places at every one of the four positions** |
| (b) | all four `Δb(p)` season-bootstrap 95% CIs contain zero |

**REJECT PERMANENTLY if either fails.** No re-run at a different season window, universe, or fit
form. If it fails, the three-season limit stands, and the board-vs-market comparison is reported as
ADR-B:65 already requires: the raw paired season differences, no p-value, no directional claim.

**Why 2.0 rank places, chosen a priori.** The board's own asserted effect at RB and WR is −1.2 and
−1.8 places. A perturbation of 2.0 places can flip the sign of the board's opinion at two of four
positions — i.e. it can make the object assert the opposite of what it asserts today. That is the
smallest change that is unambiguously not a rounding artefact of the refit. It is derived from the
board's published effect size, not tuned to any result.

**Criterion (b) is deliberately weak and (a) is deliberately the binding one.** At n=4 seasons a
slope-difference CI will contain zero almost regardless, so (b) alone would wave anything through.
(a) is a *materiality* test on the shipped consequence, not a significance test, and materiality does
not move with n (PR-004 §4's reasoning, applied here).

### 4.3 What an APPROVE licenses, and what it never licenses

If approved, the six-season series becomes usable and a two-sided sign test floors at **p = 0.031** —
a genuine and worthwhile gain, since three seasons floor at 0.25. Bound by:

1. **Never "ADP is a better input."** H1 measured NULL. The only supportable claim is a longer rank
   series of a demonstrated-exchangeable quantity.
2. **The 12-team-vs-10-team confound travels with every number.** FFC history is a 12-team market;
   this league is 10-team. It is a real confound and it is never dropped from a caption.
3. **BH still applies across the campaign's true denominator.** Six seasons buys the *ability* to be
   significant; it does not buy an exemption from correction.
4. **It is a product change.** Approving it means the shipped board's numbers move, which requires an
   ADR, a rebuild, a `board.json` regeneration, and clearance against the primary-metric gate — not a
   backtest-only edit (see §3).

---

## 5. Separately and unconditionally: label the NULL scoring format

The precondition finding stands on its own and should not wait on any of the above.
`make_board.TRAINING_SOURCE = "fantasypros_ecr"` has `scoring_format = NULL` on all 2,540 rows, so
`projected_points` is today `E[half-PPR points | rank on a consensus board of unrecorded format]`.

**This is fixed by labelling, not by substitution.** Substituting FFC to escape an unlabelled
assumption would replace it with a *different* unlabelled assumption (12-team, behaviour-based).
Required: `board.json` carries a note stating that the outcome side is scored under this league's
verified rules while the rank side's source format is unrecorded, in the same place
`curve_caveat` already lives. One field, no methodology consequence, closes a live honesty gap.

---

## 6. What would falsify this ruling

- **Falsifies the NO:** the §4.1 measurement returning four tilts within 2.0 places and four CIs
  containing zero. That is not a hypothetical escape hatch — it is the registered path, and I give it
  maybe even odds.
- **Falsifies the QB argument specifically (§2.3):** `Δb(QB)` coming back the *smallest* of the four.
  I have predicted it will be the largest. If it is the smallest, the mechanism I described is wrong
  and this ADR's central reasoning should be re-examined rather than patched.
- **Falsifies §3's structural objection:** a design in which the evaluation curve and the shipped
  curve are provably the same object across both sources. I cannot construct one; someone else might.
