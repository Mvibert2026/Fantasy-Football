---
ID: FR-115
STATUS: NEW
SOURCE: chat 2026-07-30, PM session (screenshot feedback)
RAISED: 2026-07-30
---

## Request
Value over next flex — pure VBD is over-suggesting tight ends

Founder's own words:

> "Probably need Value of next Flex also - because getting alot of tight end suggestiosn based on pure VBD"

## Why it matters / PM's read

Screenshot evidence: at pick 43 the Recommend pane offers **Colston Loveland TE3 (VBD 36.7)** over
Jaylen Waddle WR, and the board's top rows are TE-heavy — TE3 at rank 37, TE4 at 46, TE5 at 53.

**The mechanism is a known consequence of the current replacement levels.** TE replacement is set at
**TE10** (10 teams x 1 TE starter). But this roster has **2 FLEX (W-R-T)** slots, and a tight end
almost never wins a flex slot — `assistant-context.md` records TE winning a flex in **2 of 26 seasons
tested**. So TE10 measures the gap to the last *starting* TE, while the real alternative use of that
roster spot is a flex-eligible WR or RB.

The founder's proposed fix is the correct one: compare against **value over the next flex-eligible
player**, not value over positional replacement, once mandatory starters are covered. That is
test-registry **#35's** neighbourhood but is not what #35 tested — that one replaced all four levels
with a single global figure and closed NULL.

**This is the same parameter the FR-109 audit flagged as decisive and untested:** current baselines
make the round-2 call WR by 25.3; a "last rostered" baseline flips it to RB by 2.8. Needs a
`strategist` pre-registration, because choosing a baseline after seeing which way it moves the answer
is exactly the failure that structure prevents.
