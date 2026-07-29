---
ID: FR-050
STATUS: NEW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Show VBD in the draft player list

Founder's own words:

> "I'd also like to see VBD in the player list"

## Why it matters

VBD — value over replacement — is the number the board actually ranks on. It is what makes a
quarterback projected for 359 points sit sixth rather than first. Not showing it in the draft room
means the founder is picking from an ordering whose basis is invisible at the moment he uses it.

## Initial read

Not the founder's own words — PM's read.

**Already solved in Prep, not carried into Draft.** `frontend/ui/views/Board.tsx:99` has a `VBD`
column, sortable, defaulting to descending. The draft room's own player list is a separate component
and does not carry it. So this is a port, not a new feature — check `Board.tsx`'s formatting and
null handling and match it rather than writing a second version.

**Watch the width.** The draft-room list is narrower than the prep board and already carries rank,
name, position, team, bye and projection. VBD may need to displace something or share a column. That
is a real layout decision, not an afterthought — and it overlaps FR-049, since both are about what
earns space on the draft screen.

Small, and it should ride along with the next draft-screen change rather than being its own pass.
