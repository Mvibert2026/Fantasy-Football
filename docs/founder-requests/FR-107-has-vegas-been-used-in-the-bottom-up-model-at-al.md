---
ID: FR-107
STATUS: NEW
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Has Vegas been used in the bottom-up model at all — player props and team props

Founder's own words:

> "have we used vegas at all in our bottoms up model?"
>
> "player props and team props"

## Why it matters / PM's read

**Answer: no. Not anywhere, in any form.**

The component model (`experiments/bottomup/components/`) projects from historical usage and
efficiency only — games, targets/carries/attempts per game, catch rate, yards per unit, TD rate,
fumbles. No market input of any kind enters it. `docs/test-registry.md` #11 (Vegas win totals and
implied team totals) is **NEW — never started**, and the `odds` data source is still listed as "TBD"
with no provider selected.

**Player props are a materially different proposition from team totals, and probably the stronger
one.** A team implied total is a team-environment signal, and the insights backfill recovered a
finding that the team-environment channel is near-zero ("do not fund the sourcing"). A **player**
prop — receiving yards, rushing yards, receptions — is a direct market projection of the exact
quantity our component model is trying to project. That is not an environment proxy; it is a
competing forecast of the same number, produced by people with money at risk.

That makes it the most interesting untested external input the project has considered, and also the
one with the sharpest methodological trap: **a season-long prop is a market consensus, so beating it
is the same problem as beating ADP** — and we do not currently beat ADP. Its likely value is as a
**baseline to measure against**, or as an input to the components rather than the ranking, not as a
free edge.

**Blockers, both real:** no odds provider is selected, and preseason *player* props (as opposed to
in-season weekly props) have thin and inconsistent public availability, with historical archives
harder still. Licensing must be checked before building (`CLAUDE.md` §5).

**Recommended framing if this is ever run:** treat season-long player props as a fourth baseline
alongside consensus ADP, expert consensus, and prior-season points — not as a factor. Ask whether our
component projections beat them, the same question §6.5 already requires against ADP.
