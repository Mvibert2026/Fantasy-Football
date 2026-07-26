---
ID: 019
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKED-BY: 018
---

## Ask
Add season-level bootstrap confidence intervals to `backtest.py`. Build a reusable
`bootstrap_seasons()` utility rather than inlining it — several tests will need it.

## Why
Guardrails §7 requires season-level bootstrap and none exists anywhere. The project's own docs
describe the current point estimates (−1,070 pts, −226.4 pts) as "close to meaningless" without them.

**The resampling unit is the season, not the player and not the game.** This is not a stylistic
preference — it is the argument that closed the alpha-detection track. Drafts and players within a
season share the same realized outcomes and are not independent; resampling at a finer grain produces
intervals that shrink with compute rather than with evidence, which is worse than no interval because
it looks rigorous.

**Report n beside every interval.** At n=4 seasons the interval is wide and its coverage is not
nominal. Print it anyway, with the 4 visible. An honest wide interval is the deliverable.

## Done looks like
`bootstrap_seasons()` implemented and tested, every reported metric carries an interval and its n,
existing point estimates either regenerated with intervals or explicitly marked "no CI, do not cite".
Commit hash and test count.
