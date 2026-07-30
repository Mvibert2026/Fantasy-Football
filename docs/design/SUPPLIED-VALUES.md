---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 2 (briefing §12)
DATE: 2026-07-29
COVERS: FR-034, FR-036
---

# Supplied values versus derived values

## What is built, and the problem with it

Both new controls mark the supplied value in `--acc` green — the typed opponent name
(`fr036-opponents-prep-typed.png`) and the slot value (`fr034-slot-selector-draft-mode.png`).

In this system green already means **good, positive, better than baseline**. It is the delta colour
on the board. A name you typed is not good; it is *yours*. The one distinction the standing rule
requires be unmistakable is currently expressed in a colour that already means something else — and
it carries no second channel, so it fails silently for a colour-blind reader.

## The rule

**A supplied value carries a dotted underline and a lowercase marker naming how it got there.**

- Markers: `typed`, `set by you`, `randomised`.
- **Never a semantic accent.** Hue is spoken for; this uses shape and words instead, and both survive
  greyscale.
- The dotted underline appears nowhere else in the app and means exactly one thing: you put this here.
- **Where a supplied value overrides a sourced one, the sourced value stays visible in the same
  control.** Replacement without disclosure is the app hiding a substitution — the same defect class
  as a silent null.
- **Derived values carry neither marker, ever**, so absence of the marker is itself information.

### Built today, then specified

    The Testers [TYPED] pencil x     ->  The Testers  typed  pencil x
    (name and badge in --acc)            (name in --txt, dotted underline, lowercase marker)

    SLOT 5 · sourced 1 x             ->  SLOT 5 · set by you, league file says 1  x
    (label and value in --acc)           (value in --txt with dotted underline)

The `· sourced 1` half of the existing slot control is **right and should be kept** — it discloses
what was overridden. Only the colour changes.
