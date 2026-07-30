---
ID: FR-065
STATUS: NEW
PRIORITY: MEDIUM
ROUTED-TO: design
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Resizable panes and pop-out views for the draft screen — founder ideas for design

Founder's own words, and note how he framed them:

> "well from a width standpoint, it would be interesting to allow me to drag to change the pane size
> as needed - if there's an issue with the periodic table, maybe that can pop out? or a whole pane
> can? **These are ideas, not suggestions, design should weigh in based on best practices.**"

> "go ahead and look for other options"

**The framing is the instruction.** He is handing design a problem and two candidate shapes, not a
specification. Design is explicitly asked to weigh them against practice and to look for options
neither of them has thought of.

## The problem underneath

FR-064 asks for a wider rankings pane. Design's round-one finding was that the periodic-table grid
**needs full width to be a pattern** — six cells across is a list with extra steps. **Both cannot
have the width.** These ideas are attempts to dissolve that conflict rather than adjudicate it.

## The two candidates, and what to weigh

**Drag-to-resize.** Gives the founder control instead of forcing one right answer. Costs: a
persisted per-user layout that every screenshot, every acceptance capture and every design reference
then has to account for; and content that must stay legible at any width the user drags to, which is
a stronger constraint than designing for one width.

**Pop-out — the grid, or a whole pane.** Solves the width problem completely for the thing popped
out. Costs: a second window during a live draft is a second thing to manage under a clock, and the
project's own principle is that the app should not hide what it knows — a pane that is elsewhere is
a pane you are not looking at.

**Neither is obviously right and the founder has not asked us to pick.** Other shapes exist —
collapse-to-rail, a full-width mode toggled per view, the grid as an overlay rather than a window.
That is the "other options" he asked for.

## Constraint that does not move

Density is a stated architectural principle. Whatever is chosen, **the answer is not to solve width
by showing less** (FR-025).

Queued for design's next round, with FR-064.
