# Captures for design — 2026-07-30

Taken by the PM from a local build of `main`, viewport 1600×1000, after the column headers, VBD,
draft-slot selector and standard-scoring preset rebuild had all landed.

**Honest limitation: all three are Prep, not Draft.** The mode switch did not take in this run —
the click landed but the view did not change, so `02-draft-room.png` and `03-prep-back.png` are
both the Prep board. **The FR-050/055 review still cannot be done from these**, because the column
headers and VBD that shipped are in the *draft room's* list, and that is the one surface not
captured here. Frontend's own run is capturing it properly.

Whether the mode switch failing is a defect or a scripting error is not established — recorded
rather than assumed.

## What these do show, which the repo did not have before

`01-prep-board.png` — the Prep board on current `main`:

- **The draft-slot selector in the top bar** (`SLOT 7`, `sourced 3`, a clear control, and `rand`)
  — FR-034 as shipped, including the override marker distinguishing the chosen slot from the one
  in `league.json`.
- **ADP and VBD as columns**, with the Δ column showing disagreements (Josh Allen ▲20, Lamar
  Jackson ▲19, Justin Jefferson ▼4).
- **Three of the six inert controls in one frame**: `Export CSV`, `Export PDF` and
  `League settings`. Useful for design's INERT-CONTROLS spec — this is what they look like today.
- The projection caveat rendered in full above the table.
- League switcher showing `WESTWOOD · yahoo · snake`.

`02-draft-room.png`, `03-prep-back.png` — same view, retained only so the failed switch is visible
rather than quietly dropped.
