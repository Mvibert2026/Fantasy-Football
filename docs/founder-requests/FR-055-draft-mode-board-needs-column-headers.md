---
ID: FR-055
STATUS: SHIPPED
PRIORITY: HIGH
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Draft mode board needs column headers

Founder's own words:

> "Board in \"Draft\" needs column headers so I know what I'm looking at"

## Why it matters

**Unlabelled numbers under a draft clock are worse than no numbers.** The founder is being asked to
read a grid of figures and infer what each one is, at the moment he has least time to do it. Prep's
board has a full header row (`frontend/ui/views/Board.tsx:89-101` — RANK, PLAYER, POS, TM, BYE,
PROJ (CI), CONS, ADP, Δ, VBD, TIER); the draft-room list does not carry it across.

It is also the cheapest possible fix for the highest-traffic screen in the product, and it is
adjacent to FR-050 (VBD in the draft player list) — same table, same gap, and they should be done
together rather than as two passes over one component.

## Initial read

Not the founder's own words — PM's read. Not yet diagnosed in the code; the claim above about
Prep's header row is verified, the draft room's absence is the founder's report and should be
confirmed before building.

Three things for whoever picks it up:

1. **Port, do not reinvent.** Reuse Prep's labels verbatim where the columns match. Two different
   names for the same number across two screens is its own defect.
2. **Sticky, if the list scrolls.** A header that scrolls away during a draft has solved the problem
   only for the first ten rows.
3. **Space is the real constraint.** The draft list is narrower than the prep board and FR-050 wants
   VBD added to it. Abbreviations need to survive without a legend — or the glossary has to be
   reachable from the header, which is a design decision rather than an engineering one.

Batch with FR-050. Both are small, both are the same table, and the founder hit both in the same
sitting.

## Resolution (2026-07-29, frontend)

Confirmed the gap first: `frontend/ui/views/DraftRoom.tsx`'s board list (position tabs, then SORT
row, then straight into rows) carried no header row at all before this change — the founder's
report was accurate.

Added a static header row (`RANK · PLAYER · POS · TM · ADP · Δ · VBD · AVAIL`) directly above the
scrollable row list, outside the `overflowY: auto` container the rows scroll inside — so it never
scrolls away without needing `position: sticky`, satisfying item 2 above the same way the
position/sort bars above it already do. Labels ported verbatim from `Board.tsx:89-101` where the
same number is shown (RANK, PLAYER, TM, Δ, VBD); ADP is abbreviated to fit the narrower column
(34px vs Prep's 70px) with the full "MyFantasyLeague proxy" caveat moved to the header's own hover
title (`computeAdpHeaderTitle`, now exported from `Board.tsx` and reused, not reimplemented) — the
per-row cell already carries an "MFL" superscript, so nothing lost the source label, per item 3's
"abbreviations need to survive without a legend." AVAIL spans both the baseline→live percent text
and the ten-dot frequency array beside it, one label for one concept shown two ways.

Built together with FR-050 (same commit, same component) per this request's own instruction.
Screenshot: `frontend/e2e/artifacts/fr055-fr050-headers-and-vbd.png`. Tests: `board-filters.test.tsx`
(14/14, unaffected — Board.tsx's only change was exporting one existing helper),
`draft-room-recommendation.test.tsx` (10/10, unaffected). No new automated assertion targets the
header row's text directly; verified by screenshot per `docs/operating-model.md`'s evidence-standards
table (UI screen/component → "a screenshot a human has looked at," never a test suite alone).
