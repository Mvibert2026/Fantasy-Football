---
ID: FR-067
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Draft view column headers do not align with the data beneath them

Founder's own words:

> "the column headers don't align in draft view with the stuff underneath, a little confusing."

Also, from the same message:

> "the slot selection is barely visible (screenshot sent earlier)"

## Why this matters more than a layout nit

**The headers were added this session, at his request (FR-055), to remove exactly this confusion.**
They shipped misaligned, so the fix did not land the improvement it was for. That is worth stating
plainly rather than filing as a minor visual issue.

Likely cause, to verify rather than assume: the header row and the data rows are laid out
independently — a static header above a separately-composed row list — so their column widths are
not derived from the same source. Any change in content width then desynchronises them. The
durable fix is one grid definition shared by both, not hand-tuned widths that drift again.

## The slot selector's visibility, same message

The `SLOT` control in the top bar is legible but does not read as the significant control it is —
it changes what every downstream number means. Compare FantasyPros, which gives draft position a
labelled field and a Randomize button of equal weight
(`docs/design-handoff/competitor-screenshots/README.md`).

**Separately and already logged:** the selector's open dropdown renders near-white options on a
near-white background in dark mode, with only the highlighted row legible (FR-063). Different defect,
same control.

## Sequencing

The alignment fix is `frontend` and should not wait for design — it is a defect in shipped work.
The selector's prominence is design's, with FR-064 and FR-065.
