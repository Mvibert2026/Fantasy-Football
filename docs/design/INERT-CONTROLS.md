---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 3 (briefing §12)
DATE: 2026-07-29
COVERS: FR-037 — six controls
---

# One treatment for controls that cannot work

## The rule

**A control that cannot act is not a control. Render the fact instead of the dead affordance.**

Not a disabled button with a tooltip. A disabled button still occupies the place where an action
goes and still makes the user click to learn. Both causes in the list resolve the same way — remove
the button, put a statement where it was. Only the statement differs.

| Control | Cause | What goes there instead |
|---|---|---|
| Export CSV (`Board.tsx:225`) | not built | Absent. One line in the board's provenance footer: *export not built*. |
| Export PDF (`Board.tsx:237`) | not built | Absent, same line. Two dead buttons is not twice the information. |
| Compare (`PlayerDetail.tsx:509`) | not built | Absent from the action row. The row shrinks; it does not hold a gap. |
| Ask (`PlayerDetail.tsx:512`) | not built | Absent. The assistant dock is already reachable and does this job. |
| Ask the assistant (`Glossary.tsx:81`) | not built | Absent per term. The dock stays; the per-term button goes. |
| Refresh data | cannot work hosted | Replaced by the fact it would have produced: *data rebuilt 2026-07-29 16:39*. Locally, where it works, it stays a button. |

## Two sub-rules

**Not-built states name the thing and stop.** No "coming soon" without a date. The sidebar already
carries six `SOON` badges and none commits to anything — that is a promise the app cannot keep.

**Cannot-work-when-hosted states show the output the control would have produced.** This is almost
always more useful than the control itself: nobody wants to press Refresh, they want to know the
data is current. The briefing's §1 asked whether such a control should be absent, disabled with a
reason, or replaced by a statement of when the data last rebuilt. **The third, and it generalises —
that is why one rule covers all six.**
