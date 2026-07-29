---
ID: FR-055
STATUS: NEW
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
