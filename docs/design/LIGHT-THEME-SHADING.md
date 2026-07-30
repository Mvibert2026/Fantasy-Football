---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 5 of 8
DATE: 2026-07-31
COVERS: founder ask "light view… it's very bright, it could use some shading"
---

# Light theme — shading without dimming

## Why it is bright

**White is doing two jobs**: it is the page *and* every panel. With nothing but hairlines between
them, the eye gets one enormous lit surface and reads the borders as the only structure.

## The fix — three surfaces, and the page is not the brightest

The dark theme already works this way. Invert the light one to match its *model*, not its values.

| Token | Hex | Role |
|---|---|---|
| page | `#eef0f3` | Grey. Recedes. |
| panel | `#fbfcfd` | Sits on the page. |
| raised | `#ffffff` | The row you are on, and only that. |
| border | `#dde1e6` | Same-level joins only. |

**Total ink drops and no value gets dimmer.** Text contrast is unchanged; only the surfaces move.

## Two consequences

- **Borders survive only where two surfaces of the same level meet.** Everywhere else the step in
  tone does the work a hairline was doing — which removes most of the lines on the screen, and most
  of what reads as clutter.
- **Alternating row tint replaces row borders** in tables. The highlighted row is true white, which
  now reads as raised because it is no longer what everything else is.

Data rows keep zero radius. Position and semantic hues are **identical in both themes** — this
changes surfaces only.

## Constraint honoured

**Dark is not touched.** He mostly uses dark and it is not broken. The two themes stay independently
coherent; there is no shared "elevation scale" being retrofitted across both.
