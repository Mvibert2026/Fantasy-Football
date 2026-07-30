---
ID: FR-122
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
---

## Request

Founder's own words:

> "when typing in a player's name , the list should begin to shrink down based on possible
> parameters so it can be used as a searcha s well as 'drafted' function"

## Why it matters

**One control, two jobs, and the second one is on the clock.** Marking a player drafted is the most
frequent action in a live draft — it happens on every pick, by every team, and every second it costs
is a second not spent deciding. Today that means finding a row. With incremental filtering it means
three keystrokes.

The search half matters for a different reason: it is the only way to answer *"where is he?"* about
a player who is not near the top of the board. On a 510-row list with the name column truncating to
seven characters at 1500w — and **absent entirely at 1180w** (`RANKINGS-PANE.md`) — visual scanning
is not a reliable way to find anyone.

## Initial read

**Buildable now, no design needed, and it is small.** Incremental substring filter over the board
list. The founder described the behaviour precisely enough that there is nothing to spec.

Details worth getting right, none of which need a designer:

- **Match on more than the display name.** Team, position, and positional rank (`RB10`) should all
  filter, because at 1180w the positional rank is the only identity a row has. Typing `RB1` should
  narrow to running backs ranked 1 and 10–19, not return nothing.
- **Diacritics and punctuation folded.** `Ja'Marr`, `JaMarr` and `jamarr` all match. Name matching
  has already cost this project real work — the mock-draft ingestion quarantined eight players on
  ambiguous names this session — so fold aggressively for *search*, where a wrong match costs one
  keystroke, while keeping ingestion's strict matching where a wrong match corrupts data.
- **Do not auto-select on a single match.** A filter that narrows to one row and then acts is how a
  mistyped name becomes a wrong pick recorded in a live draft.

**Sequencing conflict:** it lives in the same component as item 6 (`RANKINGS-PANE.md`), which is
already queued and rewrites that list's column structure. Building both in parallel means a merge
conflict in one file for no gain. **Fold it into the item 6 dispatch** rather than dispatching it
separately.
