# G-A — Does the pick recommendation flip inside λ's confidence interval?

**Session:** 2026-07-28, Fable mandate G-A (`docs/fable-mandate-G-2026-07-28.md`). Read-only:
no code changed, no builds, no git operations. All numbers below were computed this session
against `main @ 9d8e09b`, the real `data/nfl.db` (2025 preseason-final ECR, as-of 2025-08-29),
and the real 2025 draft log (`data/real_drafts/2025_league_draft.json`), using the production
functions themselves (`draft_sim.strategy_balanced`, `live_availability.live_survival`,
`lambda_estimation.fit_conditional_logit`) — not re-derivations. The replication harness was
verified against `strategy_balanced` directly: 160/160 states agree at λ̂.

---

## Conclusion

**Yes, the recommendation flips inside the CI — in 4 of 160 realistic decision states (2.5%),
and the top-3 reorders in 16 of 160 (10%). Every single top-1 flip is the same configuration:
a team already holding its one starting QB, rounds 5–8, deciding between a falling
best-value QB and the best WR/RB. But the FR-007 verdict is not "floor defect in the shipped
product," because a channel audit shows λ never reaches the founder-facing draft-day
recommendation at all — and that disconnect is itself the more important finding.**

Five headline results:

1. **Where λ bites, it flips only the luxury-second-QB decision.** All four flips (picks 44,
   47, 54, 72 of the replayed 2025 draft) are teams with exactly `{QB: 1}` filled, where the
   best remaining QB sits 5–6 ECR points clear of the field. λ controls the *penalty* on a
   filled position, and across [0.21, 0.49] that penalty moves from ≈3.4 to ≈6.3 rank points
   — enough to cross the gap. Flip boundaries sit at λ ≈ 0.395–0.458, inside the CI. The
   founder's own slot-3 states never flip top-1 (closest margins 6.6 and 9.0 rank points);
   two of their 16 states reorder the top-3.

2. **λ is disconnected from the shipped recommendation surface.** The DraftRoom RECOMMENDED
   card is `recommendationScore` (`frontend/ui/data/recommendation.ts:16`): VBD + flat
   +8 unfilled-need / +18 tier-1-TE / −25 early-QB — self-described "stopgap, not a validated
   model," λ-free. The shipped live survival number is the frontend's own §5.2 logit model
   (`frontend/ui/data/liveAvailability.ts:30`, `NEED_COEFFICIENT = −0.62`,
   `RUN_COEFFICIENT = −1.25`) — also λ-free. λ's only consumers are
   `draft_sim.strategy_balanced` (simulation strategy; feeds the strategy comparisons behind
   the Strategy Guide, whose `strategies.json` export is itself stale at contract 1.7.0) and
   `live_availability.live_survival` (Mock Lab prediction path, no UI wiring). So the measured,
   scrutinised parameter steers nothing the founder sees on draft day, while the card they
   *will* see runs on five constants that were never fitted to anything. Under FR-007's own
   logic — the founder cannot tell which rows are affected — that is the exposure to fix
   before arguing about λ's third decimal.

3. **The CI is honest; 10 clusters is thin but not hiding variance.** Pairs-cluster bootstrap
   (B=2000, resampling teams): 95% interval [0.229, 0.500], sd 0.069. Leave-one-cluster-out
   jackknife: SE 0.0737 → [0.207, 0.496]; per-cluster deletion moves λ̂ only within
   [0.315, 0.399]. Both reproduce the Wald interval [0.215, 0.489] to within ~0.015 at each
   end. The real uncertainty is not sampling — it is population (one draft, one league, one
   season, need mechanically confounded with round).

4. **λ is not defensibly a single global parameter — same construction-error class as
   `playoff_weeks`.** `live_availability.py` hard-codes the primary league's 2025 observed
   roster shape at module level: `TARGET` (:55, must sum to 16 = *this* league's rounds),
   `EPS` (:64, "1 of 10 teams" empirical rates), `SHARE_BAR` (:66), and `POSITIONS` (:50,
   no K at all). League 2 rosters a kicker — its drafts are not even *representable* in the
   need term, let alone correctly weighted. λ itself was fitted on one 10-team Yahoo draft;
   applying it to a 12-team league with different picks-between-turns assumes a behavioural
   invariance nobody has tested. Today the blast radius is contained only because nothing
   per-league consumes λ yet (see 2); the error becomes live the day `live_survival` is wired
   into a second league's output. Belongs on G-B's sweep list.

5. **The survival channel is λ-robust; the display fix is about margins, not decimals.**
   Across the whole CI, `live_survival` moves survival probabilities by at most ~2.3
   percentage points in realistic gap states (real 2025 roster states, k=4 and k=14 gaps) —
   second-order against the sigma-5/20 band the UI already draws. Early-draft gaps show
   *zero* λ-sensitivity (empty rosters ⇒ share ≡ share_bar ⇒ N ≡ 1 at any λ). What the
   product should display: when two candidates' adjusted scores sit within ~3 rank points —
   the width λ's CI can actually move — present them as an explicit coin-flip, not an ordered
   recommendation. That is computable with two extra evaluations (λ = 0.21 and 0.49) per
   pick, and it is structural honesty rather than false precision.

**Priority-rule check (mandate preamble):** this mandate is *not* edge work in disguise — but
its premise ("the parameter the differentiator rests on") assumed a wiring that does not
exist. The floor-shaped items that fall out of it are the ones in headline 2 and headline 4,
plus one incidental defect below (D-001 unimplemented).

---

## 1. Method

Replayed the real 2025 draft pick-by-pick. At each of the 160 picks, reconstructed the
decision state exactly as `strategy_balanced` would see it: the on-clock team's real
positional counts, the real set of players already taken (159/160 skill picks name-matched
to the 2025 preseason board; the one miss, "Hollywood Brown" at pick 136 — the same
nickname-vs-legal-name case `ingest_fantasypros_csv` documents — leaves one WR erroneously
available from round 14 on; immaterial), the pre-draft consensus board (as-of 2025-08-29,
one day before the draft — no look-ahead), and `draft_sim._legal_mask`. Swept λ over
[0.21, 0.49] in 0.005 steps (0.0025 near boundaries) and recorded the top-1 and ordered
top-3 of the adjusted board at each λ, versus λ̂ = 0.352.

Two honesty notes. First, these 160 states are realistic but **in-sample**: they come from
the same draft λ was fitted on. That is fine for a sensitivity question (does the output
move as λ moves), and would be circular for a validation question (is λ right). Second, the
flip arithmetic is conditional on `NEED_ADJUSTMENT_SCALE = 10.0` — see §7.

## 2. Q1 — does the recommendation change inside the CI?

| Phase | states | top-1 flips | top-3 reorders |
|---|---|---|---|
| Early (R1–3) | 30 | 0 (0%) | 0 (0%) |
| Middle (R4–7) | 40 | 3 (7.5%) | 9 (22.5%) |
| Late (R8–16) | 90 | 1 (1.1%) | 7 (7.8%) |
| **All** | **160** | **4 (2.5%)** | **16 (10%)** |
| Founder slot 3 | 16 | 0 | 2 |

Early rounds are structurally immune: with near-empty rosters, `share_t ≈ share_bar`, so
N ≈ 1 at *any* λ — the parameter cannot matter before rosters differentiate. The middle
rounds are where both flips and top-3 churn concentrate, which matches the founder's stated
belief that need bites hardest in rounds 4–7 — but see Q2 for what is actually flipping.

Magnitudes: the λ-driven adjustment shift across the full CI (max over positions,
`10·|N₀.₄₉ − N₀.₂₁|`) has median 0.30 rank points early, 1.58 middle, 2.48 late (max 8.2, a
late-round empty-QB state). Against that, the cross-position margin at λ̂ has median 5.78
rank points, p25 = 2.18, p10 = 1.51 — so roughly the closest tenth of decisions sit inside
λ's reach, and the observed 2.5–7.5% flip rates are exactly that arithmetic playing out.

**Is this a floor defect under FR-007?** In the λ-consuming channel, yes by the mandate's
own definition — the recommendation is not stable across the parameter's honest uncertainty.
But that channel is `strategy_balanced`, which today drives simulation-based strategy
comparisons, not the draft-day card (§Conclusion, headline 2). The shipped card cannot flip
with λ because it never consults λ. The defect that reaches the founder is therefore not
"recommendation unstable in λ" but "recommendation surface runs on unfitted constants while
the fitted parameter runs nothing."

## 3. Q2 — where is the flip most likely?

All four flips are one configuration, and it is not the one the mandate's framing suggests:

| Pick | Round | Roster when on clock | Flips from → to | Boundary λ |
|---|---|---|---|---|
| 44 | R5 | QB 1, RB 2, WR 1 | Jayden Daniels (QB, ECR 34) → DJ Moore (WR, ECR 40) | 0.395 |
| 47 | R5 | QB 1, RB 2, WR 1 | Jayden Daniels (QB, ECR 34) → DJ Moore (WR, ECR 40) | 0.395 |
| 54 | R6 | QB 1, RB 2, WR 2 | Jayden Daniels (QB, ECR 34) → Alvin Kamara (RB, ECR 39) | 0.395 |
| 72 | R8 | QB 1, RB 2, WR 3, TE 1 | Patrick Mahomes (QB, ECR 62) → Aaron Jones (RB, ECR 68) | 0.458 |

The λ-sensitive quantity is the **penalty on an already-filled position**, specifically QB.
QB's target share is the league minimum (1/16), so filling the slot collapses its need share
toward `EPS` and produces the most extreme ratio on the board (N_QB ranges 0.65 → 0.37
across the CI in these states; every other position's N moves by hundredths). The flip
condition, stated as a rule: *a team holding exactly one QB, facing a best-available QB
whose ECR is 3.5–6.5 rank points clear of the best available non-QB* — i.e. the classic
"Daniels/Mahomes is falling, do I take a luxury second QB" decision, in rounds 5–8. Inside
its CI, λ genuinely cannot answer that question: the low end says take the value, the high
end says fill the roster.

Unfilled-need boosts, by contrast, never flip anything anywhere in the sweep: they are
bounded by ratios much closer to 1 until the late rounds, by which point cross-position
margins are large.

## 4. Q3 — is 10 clusters enough, and would a bootstrap change the interval?

Ran two standard small-cluster checks this session (both trivially cheap — seconds):

- **Pairs-cluster bootstrap** (resample the 10 teams with replacement, refit, B = 2000,
  seed 20260728): mean 0.357, sd 0.069, percentile 95% interval **[0.229, 0.500]**.
- **Leave-one-cluster-out jackknife** (10 refits): λ̂ ranges [0.315, 0.399] — no single team
  drives the estimate — jackknife SE 0.0737 → Wald **[0.207, 0.496]**.

Both agree with the analytic cluster-robust interval [0.215, 0.489] to within ~0.015 per
end, and the bootstrap distribution is symmetric around the point estimate. Answer: **the SE
means what it appears to mean for within-draft sampling variation, and a wild-cluster
bootstrap would not materially move an interval that three independent constructions already
agree on.** The cheapest defensible standing check is the jackknife — 10 refits, sub-second;
recommend attaching it to any future refit of λ rather than building a wild-cluster
implementation (the score-based wild bootstrap is the right variant for this MLE if anyone
ever wants it, but it is not where the uncertainty lives).

Where the uncertainty *does* live: the fit's own docstring already says it — one season, one
league, deficits mechanically correlated with round (nobody has a filled roster in round 2),
and no ADP/rank preference term in the regression. The CI is a within-population statement.
A λ refit with round controls, or on a second league's draft, could legitimately land
outside [0.21, 0.49], and no resampling of these 160 picks can detect that. This is
uncertainty about the *construct*, and it dwarfs the sampling story the SE tells.

## 5. Q4 — is λ even a single global parameter?

No, and the code makes the problem concrete rather than hypothetical. Everything the need
term is built from is a module-level constant transcribing the primary league's 2025 draft
(`src/live_availability.py`): `TARGET` (:55) sums to 16 because *this* league drafts 16
rounds; `EPS` (:64) is "1 of 10 teams did each"; `SHARE_BAR` derives from both;
`POSITIONS` (:50) is QB/RB/WR/TE/DEF with **no K**. Consequences, per league:

- **Westwood (primary):** internally consistent. λ, TARGET, EPS all measured/observed on
  this league's one real draft. Fragile (n=1), not wrong.
- **Ethan's Expert League:** not merely mis-weighted — **unrepresentable**. It rosters a K;
  a K pick has no slot in `POSITIONS`, `need_share` cannot see it, and `TARGET`'s 16-round
  primary shape is the wrong denominator for every share. 1 FLEX (not 2) also changes
  `MECHANICAL_NEED_TARGETS`-style arithmetic. Any future λ-consumer for this league inherits
  all of it silently.
- **League 3 (unconfirmed settings, FR-012):** unknown, which is the point — the constants
  give no way to be right for a shape nobody has entered.

And λ itself is a *behavioural* parameter — how hard real drafters chase need — fitted on
one room's one draft. Different league sizes change picks-between-turns, which changes how
need expresses in pick order, which changes the fitted coefficient. Treating it as global is
exactly the `playoff_weeks` construction error: a per-league field stored as a constant,
wrong by construction for at least one league whichever value it holds. **Recommended shape
(for G-B's consolidated fix):** `lambda`, `target`, `eps` become `LeagueConfig` fields;
primary league gets the measured values with provenance attached; other leagues get
`null` → need term disabled (N ≡ 1) with an honest "not fitted for this league" flag, never
a silent inheritance of Westwood's numbers.

## 6. Q5 — what should the product display about its own uncertainty?

The honest answer to "can we narrow the CI before the draft" is no — the only data that
narrows the *construct* uncertainty is more real drafts, and the mock-collection pipeline is
gated behind ADR-D instrumentation (1 of ~30 logged). So display, concretely:

1. **Margin-aware recommendation, not decimal confidence.** Wherever a need-weighted
   ordering reaches the UI, evaluate it at λ = 0.21 and λ = 0.49 (two cheap extra passes).
   If the top pick differs, render both candidates as an explicit tie — "A / B: this comes
   down to how hard you weight roster need, which we measured from one draft" — rather than
   an ordered pair. The flip analysis shows this fires rarely (≈2.5% of states) and almost
   always on the luxury-QB decision, so the label will not wallpaper the UI.
2. **Keep survival percentages coarse.** λ's CI contributes ≤ ~2 points; sigma dominates.
   The existing sigma band is the right display; never render a λ-derived survival
   difference smaller than the band as if it ordered two players.
3. **Provenance line where λ's output surfaces** (Strategy Guide balanced-strategy numbers,
   future Mock Lab predictions): "need weight fitted on the 2025 league draft, n=160,
   95% CI [0.21, 0.49]" — the same caveat `CURRENT-STATE.md` already carries, put where the
   founder actually looks.

## 7. Incidental findings (out of mandate scope, recorded not fixed)

- **D-001 is decided but not implemented.** `NEED_ADJUSTMENT_SCALE = 10.0` is still present
  and load-bearing at `src/draft_sim.py:284` (`strategy_balanced` multiplies N−1 by it).
  The founder's decision says delete the parameter outright. Every flip count in this review
  is conditional on that 10.0 — the flip rate scales roughly linearly with it, and if
  deletion removes the need nudge from `strategy_balanced`, λ's last recommendation-shaped
  consumer disappears entirely. Whoever implements D-001 should re-read §2 in that light.
- **`strategies.json` staleness** (already tracked, thread 042): the Strategy Guide's
  balanced-strategy numbers were computed under some historical λ; after any λ or D-001
  change they silently describe a strategy that no longer exists.
- One name-match miss in the replay harness (Hollywood/Marquise Brown) — a known ingestion
  pattern, no bearing on conclusions.

## 8. Reproduction

Scratchpad scripts (session-local, not committed, per mandate rules): a replay harness
sweeping λ over the 160 states with a 160/160 agreement check against
`ds.strategy_balanced`, and a bootstrap/jackknife pass over
`lambda_estimation.fit_conditional_logit`. Inputs: `data/nfl.db` (`rankings`,
`fantasypros_ecr`, season 2025, as-of 2025-08-29, `is_preseason_final=1`, 443 skill rows),
`data/real_drafts/2025_league_draft.json`. Guardrails statement per
`docs/statistical-guardrails.md`: no target-season data used (board pre-dates the draft by
one day); no holdout touched; this is a sensitivity analysis on an already-fitted parameter,
not a backtest, and none of its numbers certify predictive validity.
