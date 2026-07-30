---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 3 of 8
DATE: 2026-07-31
COVERS: FR-044 reinstated by the founder; supersedes DRAFT-MIDDLE-PANE.md §1.1's rejection
---

# The periodic table — reinstated, additive, popped out

## Standing objections, both closed

- **Colour — resolved, no action.** `POSITION-COLOUR-RESOLUTION.md` is `STATUS: RESOLVED`: no position
  hue changes, families separated by role and shape, **semantic accents banned from the grid
  outright.** Build against it.
- **Space — the founder answered it.** Pop-out is the expected shape. The pane keeps its ~640px.

`BUILD-STATE-AUDIT-2026-07-30.md` confirms the four-tab pane, FR-045 suppression, the look-ahead
toggle and the next-pick reference are all built. **The grid is the only unbuilt part of that spec.**

## Additive, as instructed

**A fifth tab. Nothing removed.** Recommend · Scarcity · Queue · Insights · **Grid**. The four
existing tabs keep their content, their order and their default.

## The mechanism — a sheet, not a window, not a drag

The Grid tab holds a preview and one **Expand** control.

| | |
|---|---|
| **Open** | Click Expand, or `⌥G` from anywhere on the draft screen. |
| **Extent** | Covers the board and pane area. Top bar, clock and roster rail stay visible — they are what you are drafting against. |
| **Close** | `Esc`, or Expand again. One key, no aim required. |
| **State** | Closes itself when a pick lands. You never return from a pick to find the board hidden. |

**Not a real browser window.** Popup blockers, a second taskbar entry and window management are all
things you do not want to be doing with fourteen picks to go.

This is the same mechanism as `PANE-LAYOUT-MODES.md` — one gesture serves both, so the grid needs no
separate invention.

## What a cell carries

**Identity, position as text, and depletion. No VBD, no projection, no delta.**

- Position hue tints the cell (~13%) and owns its left edge, in a filled pill around the letters.
- Available is full text; gone is dimmed and struck; under 50% by your next pick carries a dot.
- Every cell states its position as text — `--f-ui`, 10px floor, semibold, never mono.

The grid answers pattern questions — *how much of a position is left*, *am I stacking one offence*. A
number in every cell would make it a table with worse alignment, and **the board is three inches to
the left and better at numbers.**

## Sort modes

By draft order (default) and by position-by-team. The position-by-team matrix is 32 teams × 5
positions and is the reason Expand exists — it cannot be squeezed into the pane at all.
