---
FROM: design
TO: pm, frontend, strategist
STATUS: OPEN
PRIORITY: 2 (round two)
DATE: 2026-07-30
COVERS: new spec · strategies.json contract 1.15.0
---

# The strategy selector

## Where it lives

Rankings do not move; recommendations do, and they explain why. So this is not a filter on the board
— it is a statement about how the recommendation is derived. **It sits at the head of the Recommend
tab** specified in round one. Choosing a strategy changes what Recommend says and nothing else on
screen.

## The constraint that shapes the whole control

`strategies.json` carries a `power_floor` block whose own plain-English text is unambiguous: with four
seasons, the best a perfect result could score is **p=0.125 against a bar of 0.05. Nothing here can
be called significant, no matter how many drafts are simulated.**

**So the control cannot rank options by margin** — that would dress four seasons up as a finding.
The trustworthy signal is **direction consistency**, which the data carries per season, and it is
what the design leads with.

## The control

| Strategy | Margin across σ | Seasons up | What that means |
|---|---|---|---|
| **Best player available** `default` | baseline | — | The comparison everything else is measured against. |
| **Balanced** | +13 to +28 | 4 of 4 | Better in all four seasons. The only option that never went the wrong way. |
| **Zero RB** | +20 to +28 | 3 of 4 | Better in three of four. One season roughly level. |
| **Hero RB** | −25 to −14 | 2 of 4 | No real difference from best available, and it swings hard both ways. |
| **Elite TE early** | −96 to −62 | 0 of 4 | Worse in all four seasons. Direction never wavers. |
| **QB early** | −117 to −93 | 0 of 4 | Worst measured option. Worse in all four seasons. |

Fields: `strategies[].by_sigma[].margin_vs_baseline` · `.per_season_margin` · 600 sims per cell ·
seasons 2021–2024 · seed 20260725.

### Four rules in that table

1. **Margin is a range across the three sigma settings, never one number.** Zero-RB is +28 at σ5 and
   +20 at σ20; a single figure would pick one and hide the dependency. Same rule as FR-051.
2. **Season dots come before the margin in reading order**, because direction consistency is the
   signal the sample size can actually support.
3. **Losing options stay selectable and keep their costs.** This is the Methodology screen's
   tested-and-found-nothing content made operational — per briefing §11, the most trust-earning
   material in the product.
4. **No option is ever labelled "recommended" or "best".** Four seasons cannot carry that word.

### The season dots

Four segments because there are four seasons. Each is filled from the **sign of that season's own**
`per_season_margin` — positive fills `--acc`, negative fills `--down`. One segment is one season.

This is deliberately the FantasyPros meter idiom with something real behind it, and it avoids their
valence bug: their meters all fill green regardless of direction, so a player with *high* bust risk
renders as five green segments and reads as excellent. **A meter whose direction is bad must not
fill in the good colour.**

## Two caveats that sit under the control, always

> **Four seasons cannot prove any of this.** The strongest possible result at this sample size is
> p=0.125 against a bar of 0.05. The directions below are consistent; none is significant. That is a
> limit of the data, not the method.

> **Lineups are set with perfect hindsight.** This flatters deep rosters, so strategies that hoard
> bench depth look better here than they would in a season you actually managed. The correcting arm
> is not in this export.

Both are read from `power_floor.plain_english` and `lineup_assumption`. Neither is design copy.
**Neither should be shortened into a single "results are indicative" line** — that is the standing
footer this project deliberately refuses, and it is exactly what FantasyPros' *"Coach can make
mistakes"* does.

## The generic-track state, and the substitution it must refuse

`strategies.json` exists only at the primary export root. The 26 other leagues have no strategy data,
so the obvious shortcut is to show Westwood's margins everywhere.

**That is the worst available outcome and it must be structurally impossible, not merely
discouraged.** The simulation ran against Westwood's roster shape — ten starters, two flex, no
kicker. `yahoo-02` shows a non-primary league with nine starters, one flex **and a kicker**. A margin
measured on one shape is not a margin on the other.

    ETHAN'S EXPERT LEAGUE · GENERIC TRACK
    Best player available    —    —    Still the default. Needs no simulation to be the default.
    Balanced                 —    —    Selectable. Measured cost unknown for this roster shape.
    Zero RB                  —    —    Selectable. Measured cost unknown for this roster shape.
    Elite TE early           —    —    Selectable. Measured cost unknown for this roster shape.

    Not simulated for this league's roster shape — nine starters, one flex, one kicker. The
    strategies are still selectable; only their measured costs are unknown here. Westwood's
    figures are not shown because they were measured on a different roster.

This is the **not yet** state from the two-track spec, not the **generic** one — the data could
genuinely arrive by running the simulation against this shape, and the copy names that missing input.
The control still works, which is the point: the strategies are definitions, not measurements.

## Note for `strategist`

Whether selecting a strategy **writes into** the recommendation model or only **reorders its output**
is unresolved and is not a design decision. FR-051 flagged the same question. The current
recommendation runs on four unbacktested constants; adding a genuinely measured input is a model
change to register, not a display change.
