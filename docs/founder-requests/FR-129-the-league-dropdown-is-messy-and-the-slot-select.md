---
ID: FR-129
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat with screenshots
RAISED: 2026-07-30
NEEDS: design
---

## Request

Founder's words, with screenshots of both controls open:

> "Also for league drop down, can we clean it up or organize it some how, it's a bit messy, slot is
> still hard to see"

**"Still"** — the slot selector has been raised before and is not fixed.

## Why it matters

### The dropdown

His screenshot shows a flat, unsorted list of **26 entries**: `WESTWOOD` at the top, then twelve
`ESPN-DEFAULT` presets, then `ETHAN'S EXPERT LEAGUE (YAHOO 834236)` in the middle, then the
`YAHOO-DEFAULT` presets. The entries read:

    ESPN-DEFAULT, 10 TEAMS, FULL SCORING
    ESPN-DEFAULT, 10 TEAMS, HALF SCORING
    ESPN-DEFAULT, 10 TEAMS, STANDARD SCORING
    ESPN-DEFAULT, 12 TEAMS, FULL SCORING
    …

Three problems, and they compound:

1. **One real league is buried among 24 synthetic presets.** `WESTWOOD` is the league he actually
   drafts in. `ETHAN'S EXPERT LEAGUE` is a second real one, and it is sorted alphabetically into the
   middle of the ESPN block, between `ESPN-DEFAULT, 8 TEAMS, STANDARD` and `YAHOO-DEFAULT, 10 TEAMS,
   FULL`. **Real leagues and generated presets are not the same kind of thing and should not share a
   flat list.**
2. **Every label is a three-part string with the varying part last.** Provider, team count, scoring —
   so scanning for "half scoring, 12 teams" means reading to the end of 24 near-identical lines.
   Three dimensions rendered as one string is the actual mess.
3. **The collapsed control truncates to `YAHOO-DEFA…`**, which is the least informative part of the
   label. The scoring format and team count — the parts that change what the board says — are what
   gets cut.

### The slot selector

A bare number in a native `<select>`, sitting between the league control and Settings. His screenshot
of it open shows an unstyled white native dropdown listing 1–10, visually unrelated to everything
around it.

**Slot is not a minor setting.** It determines every pick number, which drives the entire Availability
model — change it and every probability on that screen changes. It currently has less visual weight
than the theme toggle beside it.

## Initial read

**Design item. Two controls, one row, and they should be solved together** — they are adjacent, they
are both draft-defining, and the slot's weight problem is partly that the league control next to it is
loud and disorganised.

Worth naming in the design prompt:

- **The real/synthetic split is the organising principle**, not provider or team count. Two real
  leagues exist today; 24 presets exist to answer "what would this board look like elsewhere." Those
  are different jobs.
- **The label's three dimensions want three columns or a grouped structure**, not one comma-joined
  string. Provider, teams, scoring.
- **What survives truncation should be what changes the board.** Today it is the provider name, which
  is the least useful third.
- **The slot needs weight proportional to consequence.** Design's own reasoning on the strategy
  selector (FR-121) was that a control with no measured edge should not hold permanent chrome. This is
  the mirror case: a control that silently re-bases every availability number is currently the
  quietest thing in the row.
- **Related and already specified:** `docs/design/LEAGUE-SETTINGS-BOUNDARY.md` and FR-069's settings
  panel. Check both before designing a third home for league state.

**Sequencing:** behind the 2026-07-31 items in build. Goes into the next design prompt with FR-126
(the Scarcity facelift).
