---
FROM: design
TO: pm
STATUS: OPEN
PRIORITY: 7 of 8
DATE: 2026-07-31
COVERS: founder ask "allow me to drag to change the pane size… these are ideas, design should weigh in"
---

# Resizable panes — pushing back, as invited

## Recommendation: no drag handles

- Dragging asks for a two-pixel target and a sustained press **at the moment attention is worth the
  most.**
- It is a **continuous** control answering a **discrete** need. There is no width he wants that is not
  one of about three, and the good ones are worth one click rather than a hunt.
- **The sharper reason: item 6 is a drag handle's best case, and it is a defect.** Something that only
  works when the user notices the pane is too narrow and fixes it by hand is not a layout — it is
  homework, and the price of forgetting is drafting the wrong `RB10`. **Handles would let that ship.**

## Instead — three preset modes, one keystroke each

| Mode | Key | Shape | For |
|---|---|---|---|
| **Board** | `⌥1` | rankings wide, pane narrow | Scanning between picks. |
| **Balanced** | `⌥2` | today's layout | Default — with the name column no longer truncating. |
| **Decide** | `⌥3` | pane wide | On the clock, reading one recommendation. |

Plus **Expand** from `PERIODIC-TABLE-GRID.md` — `⌥G` to fill, `Esc` to close. **One mechanism**, so the
grid needs no separate invention and any future pane can borrow it.

Each mode is a layout someone chose and tested, which a dragged width is not.

## Not a refusal

If after living with the modes he still wants continuous control, a handle can be added on top of
this — the modes become its snap points. It just should not be the *answer* to a problem that better
defaults solve, and it should not be built before the defaults are right.
