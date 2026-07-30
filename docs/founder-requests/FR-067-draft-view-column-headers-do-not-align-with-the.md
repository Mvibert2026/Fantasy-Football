---
ID: FR-067
STATUS: SHIPPED
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

## Resolution (2026-07-30, frontend)

Confirmed the "hand-typed pixel widths in two places" hypothesis, plus a second, larger cause the
ticket flagged as worth verifying: the header row (`frontend/ui/views/DraftRoom.tsx`, the
draft-list header block) ended after AVAIL, but every player row went on to render three more
fixed-width elements the header never accounted for — a 10-dot availability array, a watch star,
a "mark taken" x. Both the header and every row share one `flex: 1` PLAYER cell that absorbs
whatever width is left over; with a different number of trailing fixed-width siblings, PLAYER (and
therefore every column after it) came out a different width in the header than in a row — a
constant pixel offset, present at every viewport width, not something a one-width nudge could ever
fix. A second, independent bug: some rows conditionally *omitted* their AVAIL/dots cells entirely
(`{avail ? <span/> : null}`) rather than rendering an empty slot, so rows drifted from each other
too, not just from the header.

**Fix:** one shared `DRAFT_LIST_COLS` width table (plus a `DRAFT_LIST_GAP` constant), consumed by
both the header and every row, including new unlabeled reserved slots for the dots/watch/taken
columns the header previously ignored. Rows now always render every column's slot at its declared
width, with a neutral "—" state inside when there's nothing to show, instead of omitting the
element. `DraftRoomAdpCell`'s own hardcoded ADP width was folded into the same table.

**Regression found and fixed by testing at a second viewport width (1180px, per this ticket's own
instruction):** giving the header the same `minWidth: 0` the row's PLAYER cell needs (so both
shrink identically under space pressure) caused the header's short "PLAYER" text to overflow
into POS at narrow widths, since (unlike the row) it had no `overflow`/`whiteSpace` handling.
Fixed by matching the row's own `overflow: hidden; textOverflow: ellipsis; whiteSpace: nowrap`
on the header cell too.

Not touched (out of scope for this ticket, logged separately): the SLOT selector's visibility.

Screenshots: `frontend/e2e/artifacts/fr067-fr087-draft-board-1500w.png` (1500px),
`fr067-fr087-draft-board-1180w.png` and `fr067-draft-board-scrolled-1180w.png` (1180px, list
scrolled — the state that previously triggered the scrollbar-gutter variant of this bug).
`npx tsc -b --noEmit` clean. Test count/commit: see session report in `docs/status/`.
