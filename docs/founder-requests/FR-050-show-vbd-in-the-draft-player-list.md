---
ID: FR-050
STATUS: SHIPPED
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

## Resolution (2026-07-29, frontend)

Added a VBD cell (`<Value cell={r.vbd} render={decimal} />`, same field, same formatting as
`Board.tsx:590` — a port, not a second version) to each draft-room board row, placed between the
Δ (vs. consensus) and availability cells, mirroring `Board.tsx`'s own Δ-then-VBD ordering. Labeled
in the new header row (FR-055, same commit).

Also made VBD a sixth SORT option (`Our rank | Consensus | Delta | Proj pts | VBD`) — Prep's own
VBD column is sortable, and the existing `SORT_TABS`/`compareBySort` mechanism in `DraftRoom.tsx`
generalizes to a fifth key at near-zero cost, so "already a sortable column in Prep, absent in
Draft" is now true in both senses (visible and sortable), not just the display half.

FR-049's width concern didn't force a displacement: the row already had headroom after the ADP
column (contract 1.14.0) landed narrower than a full delta column, so VBD got its own 40px cell
rather than sharing one.

Screenshot: `frontend/e2e/artifacts/fr055-fr050-headers-and-vbd.png`. Tests unaffected
(`draft-room-recommendation.test.tsx` 10/10); no dedicated unit test added for the sort comparator
itself since `compareBySort`'s other four branches follow the identical present/absent pattern and
aren't separately unit-tested either — verified by direct screenshot inspection instead, per
`docs/operating-model.md`'s evidence-standards table.
