# Pre-registration: test-registry #35 (global flex baseline) and #36 (VONA pick-gap awareness)

Written before either test runs, per `docs/statistical-guardrails.md` §3.4/§8. Both tests are run
by `experiments/valuation/replacement_and_vona.py`, executed once against this document with no
edits afterward. If the plan below turns out to be unworkable once code is written, the fix is a
new dated addendum section, not a silent rewrite.

**Author:** backend session, 2026-07-30. **Data source for player universe/outcomes:**
`fantasypros_ecr` (rankings table, restored from the committed rescue CSV,
`docs/can-we-rebuild-the-database.md`) + `player_weekly_stats`, both already in `data/nfl.db`.
**Simulator:** `src/draft_sim.py`, unmodified — both tests build alternative `board` arrays / new
`Strategy` callables and feed them through the existing `run_strategy`/`simulate_one`/
`paired_season_bootstrap`/`sign_test` machinery. No change to `src/draft_sim.py` itself.

---

## Shared setup

- **Seasons.** Train/eval on 2021, 2022, 2023, 2024 — the four seasons `draft_sim.load_season`
  can serve from the restored `fantasypros_ecr` table. **2025 is the locked holdout and is not
  touched by this pass.** With n=4 seasons, `sign_test`'s own stated power ceiling applies: the
  smallest attainable two-sided p is 0.125. That is a fact about the data, stated up front, not
  discovered after a null.
- **Opponent noise.** `sigma ∈ {10.0, 20.0}` (two of `draft_sim.SIGMA_SWEEP`'s three points, to
  bound runtime — a result that only holds at one sigma is flagged as an artifact of the guess,
  per `draft_sim.py`'s own assumption-1 comment).
- **Sims per cell.** 300, seeded via `zlib.crc32` of a stable string key (never Python's builtin
  `hash()` — `docs/statistical-guardrails.md` §11 rule 1).
- **Metric.** Realised roster points (`weekly_optimal_points`, the simulator's existing
  perfect-hindsight lineup score) and `p_top4` (finishes top-4 of 10 in a simulated draft), paired
  by season via `draft_sim.paired_season_bootstrap` (season-level bootstrap, respects
  autocorrelation) and `draft_sim.sign_test` (exact, since bootstrap p-values are meaningless at
  n=4 per that function's own docstring).
- **Multiple comparisons.** Both tests are pre-registered and run together as one batch.
  Benjamini-Hochberg is applied once, across every sign-test p-value produced by *either* test
  (arm-vs-baseline, both sigmas) — 3.4 requires correcting across the pass, not per-test.
- **Grading.** SURVIVES (CI excludes zero at both sigmas AND the corrected sign-test p clears
  0.05), MARGINAL (a CI endpoint sits near zero, or only one sigma clears), NULL (does not clear
  zero). A null is a valid, reportable outcome — not a reason to re-run.

---

## Test 1 — #35, global flex baseline

**Question.** Does replacing the current per-position replacement levels (RB30/WR40/TE10/QB10,
`scoring.ReplacementLevels`, ADR-029) with a single global flex-eligible baseline — the Nth-best
flex-eligible (RB/WR/TE) player by realised value, applied as ONE replacement points figure to
all three flex-eligible positions — produce better draft outcomes?

**Why N=80, derived not assumed.** Mandated starters under this league's roster
(`draft_sim.STARTERS`, 10 teams): QB 1×10=10, RB 2×10=20, WR 3×10=30, TE 1×10=10 (total 70 across
QB/RB/WR/TE). `FLEX_SLOTS=2` × 10 teams = 20 more picks drawn from the flex-eligible pool
(RB/WR/TE only — QB is not flex-eligible in this league). Restricting to the *flex-eligible*
starters plus flex slots: RB 20 + WR 30 + TE 10 + flex 20 = 80. This also equals the current
scheme's own total (RB30+WR40+TE10=80) — the two schemes move the SAME 80 picks' worth of
"who counts as freely available," just splitting them differently. QB is unaffected by either
scheme (QB10 in both) and is not part of the comparison.

**How each board is built (no player-level projections exist yet, ADR-017), so both schemes use
the same look-ahead-safe stand-in used elsewhere in this project — season S-1 actual points,
scored under this league's real rules via `scoring.score_offensive_game`, read through
`db.CutoffEnforcedStore(conn, cutoff_season=S).player_week_rows(seasons=[S-1])`** (never a raw
query — the structural cutoff guard is exercised, not bypassed):

- **Arm A — `vbd_current`.** Per-position replacement, exactly `scoring.ReplacementLevels()`'s
  measured baselines (RB30/WR40/TE10/QB10) applied against the S-1 points curve within each
  position separately. This is baseline #1 required by `docs/statistical-guardrails.md` §5
  (BPA by our own VBD and replacement levels) — it is simultaneously the CURRENT scheme under
  test and one of the three required baselines.
- **Arm B — `vbd_global_flex`.** QB keeps QB10 (unaffected, per above). RB/WR/TE are ranked
  together as one pool by S-1 points; the 80th-best player in that pool sets ONE replacement
  points figure applied to all three positions' VBD.
- **Baseline — `bpa_consensus`.** Unmodified `draft_sim.strategy_bpa` against
  `data.consensus_rank` (market ECR/ADP) — required baseline #2/#3 (this project's only available
  ADP/expert-consensus source doubles as both, per `docs/ranking/component-model-rb-qb-te-pass-1.md`
  precedent).

Each VBD arm becomes a rank-ordered `board` (argsort descending VBD → rank 1..n, lower=better, the
convention `draft_sim._best_by`/`strategy_bpa` already use) and is driven through the UNCHANGED
`strategy_bpa` — so this test isolates the replacement-level definition, not a different pick
policy.

**Warning carried into the write-up per the dispatch:** VBD magnitudes are NOT compared directly —
a shifted replacement level moves every player's VBD number by construction and a raw-magnitude
comparison would show a large, meaningless difference. Only realised roster/decision outcomes
count.

**Win condition (fixed before running).** `vbd_global_flex` "wins" only if its season-paired
margin over `vbd_current` (points and/or p_top4) clears zero at both sigmas with the corrected
sign-test p < 0.05. Anything less is NULL or MARGINAL — the registry entry closes as measured
either way.

---

## Test 2 — #36, VONA with pick-gap awareness

**Question.** Does weighting "value over next available" by the REAL, structurally-known gap to
the user's next pick (short right after the turn, long right before it) rather than a single
constant assumption change the recommended pick, and do the changes help?

**The gap is deterministic, not simulated.** `draft_sim.user_pick_numbers()` for `USER_SLOT=3`,
`N_TEAMS=10` gives picks 3, 18, 23, 38, 43, ... — intervening-opponent-pick gaps alternate
14, 4, 14, 4, ... (a 3.5× ratio, matching the registry's "~3×" framing and exactly the founder's
live setup, since his slot fixes this pattern). This is arithmetic on the snake order, not a
measurement with uncertainty.

**VONA definition used (both arms identical except for the gap value):**

```
VONA(player) = VBD(player) - E[VBD of best still-available player at the same position
                                at the user's next turn]
E[...] estimated by: expected_next_rank = current_position_rank + gap_length * share(pos)
  share(pos) = this league's measured per-round position share (`live_availability.TARGET`,
  ADR-055/SS2), renormalised over QB/RB/WR/TE only (sums to 15 of 16 rounds once DEF's fixed
  1.0 share is dropped — 15 is exactly `N_ROUNDS-1`, the number of rounds `draft_sim.simulate_one`
  actually drafts before its reserved DEF round, so no rescaling assumption is smuggled in)
  VBD at a fractional rank is linearly interpolated between the two bracketing ranks in the
  CURRENTLY-AVAILABLE pool at that position; a rank past the pool's end resolves to VBD=0
  (replacement level, by construction).
```

- **Arm A — `vona_gap_blind`.** `gap_length` fixed at `N_TEAMS - 1 = 9` for every decision (the
  textbook "assume one round" approximation — a single urgency level, never varying by turn).
- **Arm B — `vona_gap_aware`.** `gap_length` = the real, exact number of intervening picks before
  the user's next scheduled turn (4 or 14, alternating).
- Both arms use `vbd_current`'s VBD points (Arm A of Test 1) as the underlying value function, so
  Test 2 is not confounded by Test 1's question — replacement level is held fixed at the current,
  in-production scheme while only gap-awareness varies.
- **Baselines.** `bpa_consensus` (market ADP/consensus) and `vbd_current`'s own plain BPA strategy
  (VBD-ranked, no VONA reasoning at all) — both already defined in Test 1, reused here as the
  required `docs/statistical-guardrails.md` §5 baseline set.

**Decision-divergence measurement (pre-registered, not added after seeing results).** For each
simulated draft, `vona_gap_blind` and `vona_gap_aware` are run against the SAME opponent-noise
realisation (identical seed feeding `simulate_one`'s single `rng.normal` draw for `effective_rank`,
so any difference in outcome traces to the user's own strategy, not re-randomised opponents).
Reported: the fraction of simulated drafts where the two arms' full pick sequences diverge at
least once, and the season-paired points/p_top4 margin between them.

**Win condition (fixed before running).** `vona_gap_aware` "wins" over `vona_gap_blind` only if
the season-paired margin clears zero at both sigmas with corrected sign-test p < 0.05. Divergence
rate is reported regardless of the win condition — "changes the pick" and "the change is better"
are two different, both pre-registered questions, and a high divergence rate with a null outcome
margin is itself a reportable result (urgency matters for WHICH player, not for whether the roster
ends up better), not a discarded intermediate step.

---

## What would falsify each hypothesis

- Test 1: `vbd_global_flex`'s season-paired margin over `vbd_current` is indistinguishable from
  zero, or negative, at either sigma.
- Test 2: `vona_gap_aware` picks diverge from `vona_gap_blind` at a materially higher rate than
  chance-level draft variance would produce on its own, but the resulting margin does not clear
  zero — i.e., gap-awareness moves the recommendation without moving the outcome. This is a
  legitimate, expected shape of null (the registry's own framing — "urgency differs ~3x" is a
  claim about the INPUT signal, not a guaranteed claim about realised value) and must be reported
  as such rather than silently reframed as a partial win.
