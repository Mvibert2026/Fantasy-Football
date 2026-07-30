---
ID: FR-094
STATUS: NEW
PRIORITY: MEDIUM-HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Predict "sleepers" — late-round ADP players showing breakout characteristics

Founder's own words:

> "I wonder if we can predict 'sleepers' Later round ADPs but who show some characteristics of a
> break out but not enough to warrant score adjustments or early round picks"

Related earlier request, same idea applied to one position (FR-038):

> "If we aren't taking tight end or QB early, then finding a tight end at late round ADP who is
> underrated is a good edge. Like Kraft last year."

## Why it matters

**The clause "not enough to warrant score adjustments" is the whole idea, and it is statistically
correct rather than a hedge.**

The evidence bar for moving a player's projection is high, and should be — a point estimate feeds
every downstream calculation, so a weak signal that shifts it corrupts the whole board. But a signal
too weak to justify moving a player thirty spots can still be strong enough to break a tie between
two players sitting at the same ADP in round 12. **The decision context is different, so the
evidence bar is legitimately different.** A separate low-bar flag is the right shape for this;
folding it into the projection is not.

Two further reasons the late rounds are where a weak signal pays:

1. **The payoff is asymmetric.** A wrong late pick costs almost nothing — the player is cut. A right
   one returns a starter at bench cost. Expected value under a weak signal is genuinely positive
   late and genuinely negative early, so "act on weak evidence late, not early" is sound.
2. **The alternatives are near-equivalent.** By round 12 the VBD spread between adjacent players is
   small. When candidates are nearly tied on projection, a tiebreaker with even modest precision
   adds value that the same signal could not add in round 2.

**We may already have one.** `docs/analysis/adp-vs-production-2026-07-30.md` found young WR/TE
(age ≤ 23) beat ADP by roughly 35 VBD points per season, holding across both eras, at moderate-high
confidence. That is a sleeper signal in everything but name. This request asks for it to be built
into something usable rather than left in an analysis document.

## Initial read

Not the founder's own words — PM's read.

**This is the single most overfitting-prone thing the project has proposed.** Screening ~200
late-round players against a wide feature set, looking for "breakout characteristics", is a textbook
false-positive generator (`CLAUDE.md` §6.3). It needs the guardrails applied harder than usual, not
more loosely because the stakes per pick are lower:

- **Survivorship is acute.** "Sleepers who broke out" is a hindsight category. The candidate universe
  must be frozen before the season — every late-ADP player, including the hundreds who did nothing.
  Building the sample from players who broke out measures nothing.
- **Base rate first, before any model.** What share of late-round players return startable value in a
  normal season? Without that denominator, any hit rate is unreadable. If the base rate is 6% and the
  flag hits 12%, that is a genuine doubling and worth having — but it must be stated that way.
- **Report precision and recall, never examples.** Kraft is one player and an anecdote. The question
  is whether the characteristic was identifiable in advance, across many players, in seasons nobody
  cherry-picked.
- **Hold out seasons.** Same rule as everything else; one look at the holdout.

**Scope note.** The output should be a **flag with a stated confidence and reason**, sitting beside
the ranking rather than inside it — consistent with the project's rule that ranking sources stay
separate and never silently blend (`CLAUDE.md` §4). A sleeper flag that quietly moved a projection
would be the exact failure this request's own wording avoids.

**Likely inputs**, all pre-season observable: age (already evidenced), prior-season efficiency on low
volume, snap-share or target-share trend within the prior season rather than its average, depth-chart
change, vacated targets/carries on the team, and archetype once that lands (FR-075). Route
participation would be a strong candidate and is currently BLOCKED on data we do not have.
