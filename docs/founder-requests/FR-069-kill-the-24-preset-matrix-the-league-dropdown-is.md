---
ID: FR-069
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Kill the 24-preset matrix; the league dropdown is my three leagues plus Custom

Founder's own words:

> "they shouldn't be built on the same settings, the preset leagues should be built on their own
> specific settings - remove this item, the drop down should show 4 league options - my three leagues
> and 'custom' which allows you to use the league settings don't necessarily need the separate button,
> if custom is selected, pop open a pane to ask me for the inputs."

## This supersedes FR-042 rather than extending it

FR-042 corrected the presets to standard scoring, which was right given they existed. **He is now
saying they should not exist.** A grid of 24 synthetic leagues — espn/yahoo × 8/10/12/14 teams ×
standard/half/full — is 24 leagues nobody plays in, and it made the app's central control a list of
hypotheticals with his real leagues buried among them.

**The dropdown becomes four entries:**

| | |
|---|---|
| Westwood | Yahoo, connected settings, real opponents |
| Ethan's Expert League | Yahoo, generic track |
| The ESPN league | manual, settings not yet captured |
| **Custom** | opens a pane for the inputs |

**"Custom" replaces the League settings button.** He was explicit: the separate control is
unnecessary — selecting Custom *is* the request to configure something, so the pane opens then. That
collapses FR-040's settings screen into the selector and removes one of the six inert controls by
deleting the need for it rather than relabelling it.

## What this changes, and it is not small

- **`src/generate_config_matrix.py` and the 24 export directories go**, along with the work just
  done to regenerate them on standard scoring. That is fine — the regeneration proved the builder
  works and the same code paths serve the Custom pane.
- **`src/league_builder.py` becomes the primary path**, not a fallback. It already does exactly this:
  name, teams, scoring, roster, draft slot in; a full export out. **This is the third time that
  module has turned out to be the answer** (FR-040, FR-042, now this).
- **The two-track expression shipped this session still holds**, and gets simpler: one connected
  league, one generic, one manual, plus whatever Custom creates.
- **FR-061's strategy pre-computation gets much cheaper** — three leagues plus custom, not 27.

## The constraint that does not change

The Custom pane must not accept a setting it cannot apply. On the hosted site, roster shape, team
count and draft slot can be recomputed in the browser; **anything touching scoring cannot**, because
the board ships final points with no components underneath. A form that takes a touchdown value and
then shows a board scored under a different one is the worst available outcome — that was FR-040's
finding and it survives this change intact.

So Custom either triggers a rebuild, or the scoring fields are honestly out of reach on the hosted
site and available locally. **Design and backend should settle which before it is built.**
