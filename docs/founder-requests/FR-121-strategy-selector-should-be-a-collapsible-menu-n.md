---
ID: FR-121
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
NEEDS: design
---

## Request

Founder's own words:

> "Nice to have strategy selection, but it should be an expandable and shrinkable menu, doesn't have
> to be at the top for every pick - just let me click something and it expands out and pick a
> strategy and shrink it back down."

He flagged this one himself as needing design: *"I think we'll want design on the first at least."*

## Why it matters

The strategy selector shipped this session (FR-061) as permanent chrome at the top of the Recommend
pane. That was the right call for a control nobody had seen yet — it had to be discoverable. It is
the wrong call now that he has seen it.

The reason is in the measurement behind the control. Zero RB tested **NULL** against plain
value-based drafting; the selector reorders recommendations because he may want it to, not because
it wins games, and it says so on screen every time it fires. **A control with no measured edge
should not occupy permanent space on the screen he stares at for an entire draft** — it is a
preference, set once, and permanent chrome overstates it. Collapsing it is not just a space saving;
it puts the control's prominence in proportion to what it does.

## Initial read

**Design item, and it composes with work already specified.** Two patterns from the 2026-07-31
handoff are candidates rather than new inventions:

- `PANE-LAYOUT-MODES.md` establishes keystroke-driven discrete modes over continuous controls, on
  the reasoning that anything needing fine mouse work under a draft clock is a bad answer. A
  strategy menu is the same shape of problem — a small set of discrete choices, set rarely.
- `PERIODIC-TABLE-GRID.md`'s Expand sheet is already the project's "show me a thing, then get out of
  the way" mechanism. Design explicitly built it to be borrowed.

**The collapsed state has to state the current strategy**, not just be a button. If it collapses to
an anonymous icon, he cannot tell at a glance whether recommendations are currently being reordered
— and a reordering he has forgotten about is worse than no reordering at all.

**The NULL disclosure must survive the collapse.** Today it fires on every use. Collapsed, it must
still be seen when the strategy is *changed* — not buried behind the expand gesture. That constraint
is not negotiable and design should be told it up front.

**Sequencing:** behind the eight items already in flight. Nothing depends on it.
