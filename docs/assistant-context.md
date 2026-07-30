# Assistant Context

**This file is the ONLY project document the in-app assistant should read for "why" questions.**
Never point it at `decisions.md` (the ADR log) or `test-registry.md` — both are historical
records and both contain figures that have since been superseded. A language model handed
`decisions.md` will find `-92.9` or `RB28/WR41/TE11` and cite them with full confidence; it has
no way to know, from the text alone, that a later entry in the same file overwrote them. This
file holds no history and no superseded numbers, on purpose, so that problem cannot occur here.

**One paragraph per settled decision, current state only.** When an ADR supersedes something
written below, this file is edited in place — not appended to. If you are updating this file
after a new ADR lands, replace the affected paragraph; do not leave the old one for contrast.

Contract version referenced below: **1.16.0** (ADR-062, plus the per-league history export).

---

## What the board is

`board.json` ranks 378 players for this league's exact format — 10 teams, half-PPR with yardage
bonuses, 1QB/2RB/3WR/1TE/2FLEX. Its edge over a generic public list is **structural**: it uses
this league's own replacement levels and scoring rules, not a 12-team RB24/WR36 convention.

**It is not a player evaluation.** Every player at the same consensus positional rank gets an
identical point projection — the board has no opinion about who is *better* than their consensus
rank suggests, only about what a given rank is *worth* under this league's rules. This is why
`evaluative_adjustment` is always null: there is nothing there to report. Do not answer "does the
model like this player more than the experts do" — it cannot.

Projections are weak on their own terms: the rank-to-points curve behind them explains 16–27% of
the variance in what a player actually scores (R² 0.158–0.266 by position). Treat any single
`projected_points` value as noisy, and prefer the confidence interval on VBD over the point
estimate.

## Replacement levels: RB30 / WR40 / TE10 / QB10

Measured, not assumed — derived by ranking 26 seasons of actual outcomes under this league's
rules and counting who wins the flex slots (RB wins roughly 52% of flex slots, WR 48%, TE
effectively 0%). Public boards assume a 12-team RB24/WR36 convention, which is a different
league's math applied to this one.

TE10 is the most solid part of this: a tight end has won a flex slot in only 2 of 26 seasons
tested. The RB/WR split moves by about ±1 rank depending on which years are included — real
variance, not a precision claim.

**DEF has no replacement level, permanently.** No DST scoring data is ingested, so there is
nothing to compute a level from. `league.json` states this explicitly
(`positions_without_replacement_levels: ["DEF"]`) rather than leaving DEF's absence to look like
an oversight — it is a decision, and it is not going to change without new data being ingested.

## Registered nulls — things tested and found absent, not just untested

- **Spike-week ability is not a persistent player trait.** Whether a player clears the 100-yard
  bonus threshold more often than his volume predicts does not carry from one season to the next.
  Project the yards; the bonuses follow automatically. There is no "ceiling player" to draft for
  at equal projected volume.
- **Hero RB has no measurable edge over drafting best-available.** Simulated result is
  essentially a coin flip in either direction.
- **Reaching early for an elite TE or QB is consistently costly** — negative in every
  season/opponent-behavior combination tested, roughly 3–5% of total roster points. This is the
  one strategy result that is *not* a coin flip, even though the sample is too small to call it
  statistically significant.
- **The league-format board (structural re-scoring + corrected replacement levels) is
  directionally better than raw consensus** in most tested seasons, but this is **not
  statistically established** — there are only four seasons to test it against, and the smallest
  possible result the statistics can report is "suggestive," never "proven."

## Why alpha detection is closed for 2026

"Alpha" means beating what the market already believed, not just predicting outcomes well —
those are different questions, and this project only has enough data to answer the second one.
Market-consensus data (needed to measure alpha) only exists for 2021–2025, and one of those five
seasons has to be held back as an honest test rather than used for tuning. That leaves too few
seasons for any statistical test to ever reach a real significance threshold, regardless of how
good or bad the underlying signal actually is — the math rules it out before the test even runs.

No further alpha-detection work is planned until enough additional seasons of consensus data
accumulate (on current pace, around 2028). This is a statement about sample size, not about
whether an edge exists. Work continues on **accuracy** — how well the model predicts outcomes —
which is not limited by this constraint.

## What the availability model does now

Availability answers "who will still be on the board when my pick comes," and it is the most
trustworthy output in the project — it depends only on how the room drafts, not on any weak
scoring projection. It is driven by three things: an opponent's ranking source (currently one
source, FantasyPros consensus), a mechanical positional-need penalty derived directly from this
league's roster rules (not a guessed constant), and a noise parameter reflecting how much a real
room deviates from consensus (reported across three settings, since it is not fitted to any
observed draft).

**It no longer assumes anything about specific named managers repeating past behavior.** An
earlier version of this model produced a wide range of outcomes by assuming two particular people
would repeat a prior pick; that was found to be circular (the range came entirely from the
assumption, not from anything measured) and has been removed. The current TE-survival-to-pick-23
figure is close to what that assumption-free removal implies it should be.

`by_player` and `by_tier` in `availability.json` are **unconditional averages over every possible
draft** — treat them as pre-draft planning numbers, not as live odds once a real draft is
underway. Mid-draft, availability is recomputed against the actual picks made so far using
`live_availability.py`, which re-weights the pre-draft marginal by two mechanisms: a
continuous, share-based roster-need term (a team further above its typical final composition at
a position gets that position's hazard suppressed, not merely un-boosted) and a positional-run
term (a standardized, shrunk signal over the last 10 picks, deliberately timid since the
detection threshold folk wisdom usually reaches for turns out to be noise about a quarter of the
time). The roster-need term's strength was measured from this league's actual 2025 draft, not
assumed; the run term remains an explicit, flagged prior pending mock data with per-pick draft
state, which does not exist yet.

## Known data traps — say these before answering, don't wait to be asked

- **No player-level opinion exists on the board.** See "What the board is," above. Do not
  construct a "we disagree with the consensus about this specific player" answer — the data to
  support that claim does not exist in this project.
- **Not every player has a displayable projection.** Players outside the fitted depth of the
  rank-to-points curve carry no honest confidence interval and must not be given a point number.
- **There is no market ADP for this specific league.** `fantasypros_ecr` is expert *opinion*
  (ECR), not observed draft position. A separate MFL-sourced ADP proxy exists but is drawn from a
  different population (a 50-mock-draft sample on a hobbyist platform, not this league) and must
  never be presented as this league's own draft tendency.
- **Historical stats have a real six-season hole.** Target-share-derived stats (targets, air
  yards, and anything built on them) are unreliable for 2003–2008 — present in the data but
  effectively zero, not measuring anything. Depth-chart data stops at the end of the 2024 season,
  so no depth-chart-based signal is available for the 2026 draft.
- **Most opponents in this league are unknown.** Only draft slot is known for 7 of the league's 9
  other teams; do not invent tendencies, prior picks, or names for them.
- **2025 is a locked holdout season for anything methodology-related.** If asked to evaluate a
  new idea "on 2025," the honest answer is that this project deliberately does not do that
  outside of a small number of pre-committed, already-used checks.
