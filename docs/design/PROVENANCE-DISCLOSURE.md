---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 1 of 8 — HIGHEST, and it sequences the rest
DATE: 2026-07-31
COVERS: founder ask "remove the code and sourcing that's all over" + "use hover over more for explanations and sources"
---

# Provenance is leaking — the disclosure pattern

Visual spec: `docs/design/spec-2026-07-31.html` §1.

## The move, and it is not a deletion

**"Provenance" is currently three different things wearing one costume.** Sort them, and two of the
three leave the default view without a single fact being lost.

| Class | What is on screen now | Where it goes |
|---|---|---|
| **1 · field paths** | `board.json:players[].vbd` · `availability.json:by_player` · `board.json:players[0].structural_breakdown.replacement_levels` · `model prose over context: page.draft_state, …` | **Trace mode.** Off by default, one keystroke on. Verbatim, in place, unchanged. |
| **2 · caveats** | "MyFantasyLeague proxy, full PPR — not this league's own ADP", and the 180-word paragraph behind it | **Stays visible, always.** Rewritten to one human phrase at the value, long form one click away. |
| **3 · developer notes** | "SUPPRESS this row in the UI while `evaluative_adjustment_available` is false." | **Never renders.** It is an instruction to the app. |

**The no-fabrication rule is untouched**, because it lives in class 2 and class 2 stays on screen.
What changes is the audience: a field path is for a developer, not for the founder mid-draft.

## Class 3 first — the app is rendering its own instructions

The captured player card prints this in full, as body text, including the last sentence:

> Zero by construction, not by omission. This board assigns every player at the same positional
> consensus rank an identical projection, so it holds no player-level opinion to attribute. All rank
> movement is structural. A real evaluative component requires component-level projections
> (test-registry #2), which no accessible source provides. **SUPPRESS this row in the UI while
> evaluative_adjustment_available is false.**

The row it describes shows `±0` against `±0`. **The founder is reading seven lines to be told nothing
happened.** Treat as representative, per the brief: any export string containing an instruction to
the UI is a developer note and never renders. The fix is not copywriting — it is obeying the field.

## Trace mode

**Off by default. `⌥T` toggles every field path on, in place, verbatim.**

- **Why a mode and not a tooltip per number.** Auditing is a *whole-screen* activity — "does this
  screen trace" is one question, not forty. Forty tooltips means forty gestures, and each one covers
  the neighbouring value while you read it. A mode answers it in one keystroke and lets you scan.
- **It is close to the cheapest item in the round.** The current design already *is* trace-on: every
  path is placed, styled and correct. The work is a visibility condition and a keystroke, not new UI.
- A persistent indicator shows when it is on, so a screenshot is never ambiguous about which mode
  produced it.

## What hover is for, and its limit

Hover carries **one short human sentence**, ~12 words, on a dotted-underlined label. It never carries
a field path and never carries a paragraph.

    MFL proxy   →   "Average pick on MyFantasyLeague — not this league's own ADP."

The 180-word ADP caveat **cannot** be a hover: too long to read in a transient layer, impossible to
copy, unreachable by keyboard. It goes to one anchored place on the card, reached by *Why that
matters* — which `ADP-COLUMN-AND-CAPTURES.md` already specified and the build audit confirms is
already working on that card.

## The one thing trace mode must never swallow

**A reason a value is absent is not provenance and never goes behind a gesture.**

`—`, `<1%`, `0%`, `not yet` and `·` stay exactly as they are, with their reasons, in the default view.
Trace mode hides *where a number came from*. It must never hide *that a number is missing* — that
would turn the highest-priority cleanup of the round into the one defect this app refuses.

## Why this goes first

It removes the class-1 text from the assistant prose (item 4), frees the card height item 2 then
reorders, and buys the pane width item 6 needs. Doing 2, 4 or 6 first means designing around text
that is about to leave.
