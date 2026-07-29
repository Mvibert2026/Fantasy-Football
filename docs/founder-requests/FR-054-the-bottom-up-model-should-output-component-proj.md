---
ID: FR-054
STATUS: IN-PROGRESS
PRIORITY: HIGH
ROUTED-TO: ranker
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
The bottom-up model should output component projections, not just a rank

Founder's own words:

> "I can try to download theirs - but our bottoms up projection needs to basically land there too, so
> once that's done we'll have that, I think FTN also has projections, and we aren't..."

And, on the screenshots that prompted it:

> "I am not saying you need to have everything in those screenshots it was just research basically"

## Why it matters

**This reframes the component-projection problem and the founder is right.** The PM had it as a
sourcing question — who publishes per-player yards, catches and touchdowns, and can we licence them.
His point is that a genuine bottom-up projection **produces those numbers as its output**. You cannot
project a player from first principles without projecting the components; points are what you get
when you score them.

So the gap closes as a by-product of the core work rather than as a separate acquisition. Sourcing
someone else's components would be a stopgap for a thing the product is meant to do itself.

**What it unlocks, and it is not small.** Component projections make **any** scoring format
computable from one set of numbers:

- Custom scoring in the browser — reported as "definitively dead" today (FR-040) purely because
  `board.json` carries a rank-curve points lookup and nothing underneath it.
- The stacking-bonus edge. A threshold bonus is a nonlinear function of a *per-game* distribution and
  cannot be recovered from a season points total. With components it becomes computable; without
  them it stays an assertion.
- The other leagues (FR-042's generic track), each scored correctly from the same projection.

## Initial read

Not the founder's own words — PM's read.

**This is a change to what the ranker is building toward, and it should be stated now rather than
discovered late.** The target is not "a better ordering of players." It is **a per-player projection
of the components that scoring consumes** — passing/rushing/receiving yards, receptions, touchdowns,
turnovers — from which a rank falls out under any given ruleset.

That is a harder problem than ranking and it is the right one. It also has to survive the same gates:
look-ahead discipline, a pre-season-defined universe, and holdout evaluation against the baselines in
`CLAUDE.md` §6.5. A component model that produces worse rankings than the current curve is not an
improvement, however much more useful its shape is.

**Per-game distribution, not just season totals.** For the bonuses to be priced, the projection needs
a distribution or at least a variance estimate per player, not a single season number. The founder
has said repeatedly that his league pays for ceiling; this is the mechanism by which that belief
becomes a number.

**On downloading a competitor's projections** — the founder offered to. Worth having as a *baseline
to beat*, and worth nothing as an input to our own model: blending consensus back in is exactly what
`CLAUDE.md` §4's separate `ranking_source` rule exists to prevent. Licensing applies either way; the
researcher pass (FR-053) covers it.

**FTN is named by the founder as another projection source.** Note it for the researcher; it appears
in Yahoo's own source dropdown as a paid option.

---

## Start condition, set 2026-07-29

Founder: *"Ok start the big one when it makes sense. Continue work in sequence as allowed."*

**Approved to start, gated on two things that are running now.** This is the largest piece of work on
the list and both of these change its foundations, so starting before them means building on numbers
that are about to move:

1. **Ranker pass 3 — the rank curve across positions.** The current curve pools all seasons flat and
   the QB slope collapsed −67 → −4. A component model has to be fitted against *something*; fitting
   it against a regime that has already been shown to be mis-specified would bake the same error in
   one layer deeper.
2. **Thread 055 — FFC ADP history, 2018-2024.** Named by the ranker as the binding constraint on
   everything pass 2 found. It takes the usable sample from 4 seasons to 7 and replaces an ECR proxy
   with real draft position. A component model built on the 4-season proxy would need refitting the
   week it lands.

**Start when both have reported.** Neither needs to have *succeeded* — a clear negative from either
is equally usable, and thread 055 reporting "the historical endpoint does not serve dated snapshots"
would itself be the answer that unblocks this.

**What it is, restated so the next session does not have to reconstruct it:** a per-player projection
of the components scoring consumes — passing/rushing/receiving yards, receptions, touchdowns,
turnovers — from which a rank falls out under *any* ruleset. Not a better ordering. The ordering is
the by-product.

**With a per-game distribution or at least a variance estimate**, because a threshold bonus is a
nonlinear function of a per-game distribution and cannot be recovered from a season total. That is the
mechanism by which "my league pays for ceiling" becomes a number.

**Sleeper's 2,007 component rows (`data/projection-snapshots/`) are a baseline to beat, never an
input.** Blending a vendor's projections into our own is precisely what `CLAUDE.md` §4's separate
`ranking_source` rule exists to prevent.


---

## Pass 1 delivered, 2026-07-29 — ranker

**Wide receiver only.** `docs/ranking/component-model-wr-pass-1.md`, code
`experiments/bottomup/components/`, 14 tests, commits `61012d0` / `43ad7b1` / `be1c571`.

**What now exists.** A per-player projection of games, targets, receptions, receiving yards,
receiving touchdowns, carries, rushing yards, rushing touchdowns and fumbles lost, plus
`p_100yd_game` / `p_150yd_game` / `p_200yd_game` — a real per-game distribution, so the stacking
bonuses are computed rather than asserted. `wr_model.score_components()` re-scores the same
projection under any ruleset without refitting, which is the thing FR-040 and FR-042 need.

**What it does not do yet.** It does not beat consensus ADP (+0.048 ρ, 95% CI [−0.013, +0.124], and
the design is underpowered — consensus itself cannot be shown to beat a three-line heuristic on the
seven available seasons). It covers one position. It has not been run for 2026, because that needs
2025 features and 2025 is the sealed holdout.

**The founder's ceiling belief, now measured rather than assumed.** He is right that the rules pay
for ceiling and wrong about the exploitable consequence, at WR. Perfect foresight of realised
stacking-bonus points is worth **+0.026 ρ**; the modelled version is worth +0.0002 and moves five
receivers out of 2,271. Conditional on mean yards per game, receivers do not differ in how often
they spike — the dispersion is *below* binomial noise. This does not transfer automatically to RB
or TE and both remain open.

**Not read, deliberately:** the 2,007 Sleeper/Rotowire component rows. Baseline to beat, never an
input, per `CLAUDE.md` §4.
