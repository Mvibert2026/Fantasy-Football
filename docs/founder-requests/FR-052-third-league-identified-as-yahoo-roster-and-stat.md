---
ID: FR-052
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-29, PM session, Yahoo screenshots
RAISED: 2026-07-29
---

## Request
Third league identified as Yahoo; roster and stat categories captured, point values still missing

Founder supplied two screenshots from the Yahoo platform, 2026-07-29, while preparing a mock draft.

**Screenshot 1 — Yahoo's "Pre-Draft Player Rankings" selector**, listing all three of his teams:

| Team | League |
|---|---|
| Two balls no Kupp | **Westwood** |
| Matthew Vibert's Cool Team | **Ethan's Expert League** |
| Return of the Champ | **Shawn PEARSON's Superb League** |

**Screenshot 2 — roster and stat categories** for one of the non-Westwood leagues (which one is not
identified in the screenshot):

- **Roster:** QB, WR, WR, RB, RB, TE, W/R/T, K, DEF — nine starters, **one** flex, **with a kicker**.
- **Stat categories, offense:** passing yards, passing TD, interceptions, rushing yards, rushing TD,
  receptions, receiving yards, receiving TD, return TD, 2-point conversions, fumbles lost, offensive
  fumble return TD.
- **Kickers and DEF/ST categories** listed in full.
- **No point values shown** — categories only.

## Why it matters

**All three leagues are Yahoo.** Every project record to date has described the third as "ESPN
league, settings not captured" — including `docs/pm-dashboard.html`'s Leagues tab and FR-027's
two-tier framing. That is now wrong and should be corrected rather than left to be rediscovered.

**The roster shape confirms the two-track split is real, and by a wider margin than assumed.**

| | Westwood | This league |
|---|---|---|
| WR starters | 3 | 2 |
| Flex | 2 (W-R-T) | 1 (W-R-T) |
| Kicker | **No** | **Yes** |
| Starters | 10 | 9 |

A kicker slot and one fewer flex change replacement level at every position. Any board built for
Westwood is materially wrong for this league — which is exactly what FR-042 (presets to standard
scoring) and FR-040 (custom league option) exist to fix, and this is the first hard evidence of the
size of the gap.

## Initial read

Not the founder's own words — PM's read.

**Still missing, and it is the part that decides everything: the point values.** The category list
says *what* scores, never *how much*. Whether this league has Westwood's stacking yardage bonuses —
or any bonuses — cannot be read from the screenshot. Yahoo's settings page shows a value beside each
category; that column is what is needed.

**Two things worth capturing while he is on the platform**, both cheap and neither obtainable by any
agent (every Yahoo host blocks research agents by name — a standing, verified constraint):

1. **The point values** for each stat category, in whichever of the two leagues the screenshot came
   from, plus which league it is.
2. **The pre-draft rankings comparison.** Screenshot 1 is the control that makes this a one-minute
   test: open the same Yahoo pre-draft ranking list under Westwood, then under a league without the
   yardage bonuses. **If the player order is identical, Yahoo is not pricing the bonuses at all** —
   which would mean everyone in Westwood is under-valuing ceiling in a league that specifically pays
   for it. That is a real, mechanical edge, and it costs one minute to establish.

**Do not infer the missing values from the ones we have.** The whole reason `generate_config_matrix.py`
shipped 24 presets wearing Westwood's rulebook is that someone treated one league's scoring as a
reasonable default for another.
