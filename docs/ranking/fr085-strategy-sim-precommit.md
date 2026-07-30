# FR-085 draft-strategy simulation — rules fixed in advance

**Ranker, 2026-07-30. Written and committed BEFORE any simulation was run.** Every rule below is
mechanical: a strategy that requires judgement cannot be simulated, so none of them contain any.

This exists because the founder asked for it directly: *"you'll need to define the rules to each
strategy tested somewhere — like how long till you take your first RB in zero RB, do you take a TE
or no judgment? within it is it BPA? VBD? etc. what is balanced?"*

Nothing here is a confirmatory registration. `strategist` owns those and has not registered this.
This document exists so the strategy definitions cannot be adjusted after seeing which one wins.

---

## 0. The logical gap this simulation exists to close

Backend's `docs/analysis/adp-vs-production-2026-07-30.md` found early-round RBs underperform their
ADP slot. **That is not the same claim as "do not draft early-round RBs."** A player who returns
less than his slot's realised value curve can still be the correct pick if the drop-off behind him
is steeper than the drop-off behind the alternative — which is the entire content of VBD, and which
a rank residual cannot see. `CLAUDE.md` §6.6 says rank correlation is a proxy and the decision-
relevant object is the roster.

So the residual work (`experiments/strategy/residuals.py`) answers *"is RB mispriced relative to
other positions"*. This simulation answers *"does acting on that produce a better roster"*. They are
different questions and only the second one is a strategy recommendation.

---

## 1. Universe, seasons, and the sealed holdout

| | |
|---|---|
| Seasons | **2018–2024** on the FFC board; **2021–2024** on the FantasyPros ECR board |
| Sealed holdout | **2025 — never loaded.** `season_vbd()` raises if asked for ≥2025. Not a convention |
| Universe | the season's pre-season market board, frozen before Week 1. Busts retained, scoring what they actually scored (usually ~0) |
| Scoring | this league's exact rules via `src/scoring.py`, stacking yardage bonuses included |

**Power ceiling, stated before running.** With 7 seasons the smallest attainable two-sided paired
sign-test p is 2/2⁷ = **0.0156**; with 4 seasons it is **0.125**, i.e. *no* result on the ECR board
can reach conventional significance at the season level regardless of effect size or how many drafts
are simulated. That is a fact about the data, not about the strategies.

## 2. Two market boards, and why both

| source | seasons | what it is | why included |
|---|---|---|---|
| `ffc` | 2018–2024 (7) | FanballFootballCalculator half-PPR **12-team mock** ADP, genuine pre-draft `as_of_date` | longest window; the only ADP history in the DB |
| `ecr` | 2021–2024 (4) | FantasyPros expert consensus rank | independent second market, and deep enough (485–558 players) to draft 150 with **no synthetic tail at all** |

**Known substitution, stated rather than worked around: no true 10-team historical ADP exists in
this project.** The FFC archive is 12-team. What is used is the *ordering*, applied to a 10-team
draft with this league's real roster shape. What that costs: positional scarcity differs between a
12-team and a 10-team room — in a 10-team league the replacement level at every position is
shallower, so the market's 12-team ordering slightly over-weights scarce positions relative to what
a true 10-team room would do. The direction of that bias is *toward* RB and TE (the scarce
positions), which if anything flatters RB-heavy strategies. Both boards get the same treatment, so
it cannot explain a difference between strategies within a board.

### 2.1 Board depth and the synthetic tail

A 10-team draft with 16 roster spots (one reserved for DEF, §3) needs **150 offensive players**.
FFC boards carry 112–171. The board is therefore built in three declared layers:

1. FFC half-PPR rank (primary ordering);
2. players present only in the same season's FFC **non-PPR** 12-team board, inserted at their
   non-PPR rank mapped onto the half-PPR scale by monotone interpolation over the players common to
   both (Spearman between the two boards on the overlap is 0.94–0.99, measured);
3. if still short of 150, a tail ordered by **prior-season fantasy points under this league's
   scoring** — a pre-draft-observable quantity and one of `CLAUDE.md` §6.5's required baselines.

Per-season layer counts are reported with the results. Layer 3 is a construction, not a market, and
its players are deep bench in every season. Two guards against it mattering:

- the **ECR board needs no tail at all** and is run as an independent check;
- a declared **11-round sensitivity** (110 offensive picks ≤ the smallest layer-1+2 board) in which
  no layer-3 player can be drafted by anyone.

## 3. League shape

10 teams · snake · 16 rounds. Roster 1 QB / 2 RB / 3 WR / 1 TE / 2 FLEX (RB/WR/TE) / 1 DEF, 6 bench.
No kicker. Playoffs weeks 16–17, 4 teams, no reseeding.

**DEF is a constant.** No DST scoring exists in this project (ADR-039). The final round is reserved
for it and contributes zero to every team equally. Absolute roster totals are therefore understated
by one starter's worth of points; the comparison between strategies is unaffected.

## 4. Opponent model

Nine opponents draft to the board's own consensus rank perturbed by noise, plus a positional-need
penalty, exactly as `src/draft_sim.py` already does.

**One thing changes, and it is an improvement to a documented weakness.** `draft_sim.py` assumption
1 says the opponent noise σ "is NOT fitted to anything: no observed draft-position data exists in
this repo or is obtainable." **That is now false.** FFC ships a per-player `std_dev` of realised
mock-draft pick position, measured over 700–1,300 drafts per player. So:

- **primary:** per-player σ = FFC's own measured `std_dev` (mean 4.1–5.8 picks, rising from ~1.2 at
  the top of the board to ~12 by round 8 — measured, not assumed);
- **sensitivity:** flat σ ∈ {5, 10, 20} picks, the existing `SIGMA_SWEEP`, so the result can be read
  against the old uncalibrated posture;
- ECR has no dispersion column, so it uses the flat sweep only, with σ=10 as its primary.

Noise is drawn **once per draft** (a board realisation, i.e. "the room valued him a round high this
year"), not per pick. Opponents **do not adapt** to the user — an unfixed limitation that makes
reaching look cheaper than it is, and therefore biases *toward* whichever strategy reaches.

## 5. The strategies — mechanical rules

**Every strategy ranks players by the same value estimate**, so the comparison is about *strategy*
and not about whose projections are better. That estimate is VBD from a **positional-rank → points
curve fitted on seasons strictly before the target season** (look-ahead safe; it is also exactly what
the shipped board does, per `CLAUDE.md`'s note that the shipped board holds no player-level opinion).
Replacement levels are ADR-029's measured RB30 / WR40 / TE10 / QB10.

Curve construction, fixed here: mean **points per game** at each positional *finish* rank over the
**five seasons immediately preceding** the target season, smoothed with a 3-wide moving average,
then multiplied by the target season's scheduled game count (16 before 2021, 17 from 2021 — known
pre-draft). Five seasons rather than all history because `CLAUDE.md` §6.4 says how far back to
weight is empirical and older seasons can be actively misleading; the window is declared here so it
cannot be tuned after seeing a result. A player's ADP *positional* rank is read onto this curve —
which is precisely the shipped board's assumption, and deliberately so: it holds no player-level
opinion, which is what isolates strategy from projection quality.

**No strategy contains a TE or QB rule.** They are handled by the same VBD ordering as every other
position. That is the answer to *"do you take a TE or no judgment?"* — no judgement, and stating so
is part of the definition.

| strategy | rule, in full |
|---|---|
| **VBD** (default) | Every pick: take the highest-VBD available player, subject only to §5.1 legality. No positional rules whatsoever. |
| **Zero RB** | Rounds 1–4: RB is forbidden. Round 5 onward: highest VBD. §5.1 legality still applies (it will force RBs late if the roster cannot otherwise be filled). |
| **Robust RB** | Rounds 1–2: take the highest-VBD **RB** available (if no RB is available at all, take highest VBD). Round 3 onward: highest VBD. |
| **Balanced** | Take the highest-VBD player among positions where the team is still short of a **mandatory starter** (1 QB / 2 RB / 3 WR / 1 TE). Once all mandatory starters are filled, take the highest-VBD **flex-eligible** player until both FLEX slots are covered. After that, highest VBD overall. |
| **BPA-consensus** (reference) | Take the lowest consensus-rank available player — i.e. do exactly what the room says. Not one of the four requested, included because "does any strategy beat just following the market" is the question underneath all of them and it costs nothing. |

**Declared sensitivity, reported and never selected on:** Zero RB with the ban lasting 3, 5 and 6
rounds instead of 4. Promoting whichever wins would be selection on the outcome; the primary is and
stays 4.

### 5.1 Legality (applies to every strategy identically)

- Hard caps QB 3 / RB 8 / WR 9 / TE 3.
- If remaining picks equal remaining unfilled mandatory starter slots, those positions are forced.
- A roster that still cannot field a legal lineup is recorded as a **failed run**, not as a low
  score. Recording it as zero points would silently reward a strategy for being unable to play.

## 6. Draft slot

The user's slot is **drawn uniformly from 1–10 per simulation**, not fixed. Zero RB from pick 1 and
from pick 10 are different strategies in practice, and fixing the slot (as `draft_sim.py` does at
slot 3) would answer only one of ten questions. Results are reported pooled and split early (1–3) /
mid (4–7) / late (8–10).

**Common random numbers.** For a given (season, simulation index) every strategy sees the *same*
drawn slot and the *same* board noise realisation. Drafts still diverge once the user picks
differently, but the pairing removes most of the between-simulation variance and makes the paired
comparison valid.

## 7. Evaluation — three metrics, and what each one is biased toward

| metric | definition | known bias |
|---|---|---|
| **A — best-ball points** | each week, the optimal legal lineup chosen with perfect hindsight | upper bound no manager achieves; **flatters deep, high-variance rosters** |
| **B — realistic points** | each week, start the highest **pre-season-ranked** roster players who actually appeared in a game that week | no in-season skill, no waivers; **flatters top-heavy rosters** relative to A |
| **C — head-to-head** | metric-B weekly scores played through a round-robin schedule, weeks 1–15; top 4 by record (points break ties) make the playoffs; weeks 16–17 single elimination, **no reseeding** (1v4, 2v3, then the final) | the actual league structure; the only metric that prices "a slow start is unusually costly" |

**A and B bracket the truth in opposite directions, which is why both are reported.** Headline is
**C** — `CLAUDE.md` §6.6 asks for rosters, not lists, and §7 says the playoff structure is a real
constraint. Reported for C: P(make playoffs), P(win title), and mean seed.

## 8. Uncertainty and multiplicity

- Every comparison is **paired by season**, and the bootstrap resamples **seasons**, never
  simulations or players. Simulations within a season share one realised set of player outcomes, so
  resampling them would measure simulation noise and call it evidence.
- Exact paired **sign test** across seasons, reported with its `min_achievable_p` so the power
  ceiling is visible in the output rather than in a footnote.
- Grades are pass-1 §0's, unchanged: **SURVIVES** / **MARGINAL** / **NULL**. The total interval-test
  count is reported and the implied false-positive count stated.

## 9. What would count as an answer

- **Zero RB beats VBD** only if the margin clears zero on metric C, on **both** boards, in the same
  direction, at the primary σ and across the σ sweep.
- **"Not distinguishable from VBD"** is the expected outcome and is a full answer, not a failure.
  It is written here in advance so that reporting it later cannot look like a retreat.
- No strategy result licenses a ranking-model change. That is a separate object with a separate
  owner (`strategist` registers, `backend` ships).
