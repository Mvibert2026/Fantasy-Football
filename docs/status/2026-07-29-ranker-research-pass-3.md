# 2026-07-29 — ranker — research pass 3: the rank-curve slope collapse

**Task.** `docs/CURRENT-STATE.md` item 12: is the QB rank-curve slope collapse real, is it
happening at other positions, what weighting does a holdout support per position, and what does
flat pooling cost in board positions.

**Output.** `docs/ranking/bottom-up-research-pass-3.md`. Code:
`experiments/bottomup/pass3_rank_curve_regimes.py`, `pass3_artifacts.py`, `pass3_weighting.py`,
`pass3_persistence.py`. Thread **093** opened to `strategist`. All exploratory; nothing
registered, no multiplicity correction, nothing wired to the board.

## What was found

**The board is four numbers.** `make_board`'s VBD is `(a + b·ln i) − (a + b·ln base)` — the
intercept cancels exactly. Reconstructing the live 2026 board from the four slopes and four
replacement ranks alone reproduces all 510 rows with **zero ordering mismatches**. So the slope
question is the whole board question, and no setting of it can give the board a player-level
opinion.

**The QB collapse is not established.** Point estimates reproduce exactly; the confidence does
not. Trend +15.3/season [−3.5, +34.1]. 2025's CI [−46.5, +69.2] contains 2024's estimate. The
monotone appearance is a property of `RELEVANT_DEPTH["QB"]=20` — at depth 12 the series is
−15.0, −106.9, −68.5, −41.7, −38.5 and 2021 is the flattest. Jackknife: dropping Jayden Daniels
alone takes 2025 from −4.1 to +28.6, a swing larger than the effect.

**Other positions: no.** RB 2025 is −77.9, steepest of five. WR flat. TE monotone (ρ = +1.00 at
the permutation floor) but magnitude CI spans zero and it breaks at depth 32.

**Mechanism: the market, not the position.** 2025 realised QB value curve −58.7, flat against era
means −57.7/−59.0/−56.8. Consensus τ_b at QB: +0.484, +0.305, +0.263, +0.263, **−0.042**. RB the
mirror image: τ_b +0.507, its best, on a flat value curve.

**Weighting, per position, on the value curve (20 targets, split at 2016).** QB strongly yes
(RMSE 45.00 → 22.41, −22.6 [−30.3, −13.6]); RB no; **WR contraindicated** (last1 +2.75 [+0.96,
+4.80] *worse*); TE weak (hl5 −2.69 [−4.71, −0.48]) with its training pick returning nothing on
test. On the board's own consensus curve: **n = 2 evaluable targets, disagreeing at the 4th
decimal of Kendall τ. Unanswerable.**

**The recorded fix inverts at QB.** The QB value curve is steepening (−0.461/season [−0.874,
−0.034]), so recency weighting it makes the premium *larger*. The consensus curve's movement
tracks ordering skill, whose lag-1 autocorrelation is −0.007 [−0.414, +0.411].

**Board cost ≈ zero.** Half-life 3: one top-150 player moves ≥10. Half-life 5: none. Every scheme
from last3 down leaves all four slopes inside the board's own published 95% CI.

## Escalated, not celebrated

Mean attenuation ratio 0.686 / 0.702 / 0.693 / 0.691 across QB/RB/WR/TE — four positions agreeing
to 0.016. Cannot separate a real regularity from shared fitting mechanics. Flagged in thread 093.

## Own-code bug, recorded

The trend test originally used an exact permutation over `n!` orderings — fine for the 5-season
consensus series, infeasible for the 26-season realised one, and it hung silently rather than
erroring. Now switches to 20,000 sampled permutations above n = 8 and reports the attainable
floor either way.

## Not done, deliberately

No confirmatory run. No change to `src/`. No board rebuild shipped. Thread 093 asks `strategist`
for the ruling on the diagnosis, the sealed-2025 judgment call, and the registration.
