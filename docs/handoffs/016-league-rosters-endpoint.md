---
ID: 016
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: the Opponents tab
---

## Ask
Build the full league rosters export: all 10 teams' complete rosters including bench and IR, not just
the drafted board. Add it to the export set with a contract version bump, and open a thread to
`frontend` announcing the new artifact and its shape.

## Why
It is the first item in the confirmed backend gap list and the hard blocker on the Opponents tab.
Frontend has been asked to build that tab; without this it can only render an empty screen, which is
worse than not building it — it looks finished and says nothing.

Note the design constraint: the Opponents view distinguishes what a team *has* from what a team still
*needs*, and the need side is mechanical arithmetic over roster slots. The inferential side — guessing
an opponent's latent strategy — was explicitly refused as indefensible. Export the observable facts
only.

## Done looks like
New artifact in `data/export/<league_id>/`, contract version bumped, tests covering shape and the
empty-roster case, thread opened to `frontend`. Reply with commit hash and test count.
