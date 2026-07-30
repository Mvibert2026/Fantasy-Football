---
ID: FR-071
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
A Simulate feature — real autopick from ADP with widening deviation and roster needs

Founder's own words:

> "Adding a 'simulate' feature which actually implemented the autopick would be nice - the autopick
> can be ADP with the SD widening and needs analysis baked in"

## What exists and what does not

**Today's "Auto-fill to my pick" takes nobody.** It advances the clock with placeholder records
(`playerId: null`, `DraftRoom.tsx:544-563`) — deliberately, so it never invents who was taken. The
consequence the founder found himself: *"too many great players available too late"*, and the pace
line reading every position as behind (FR-045, FR-063).

**He has now specified the mechanism, and every ingredient is already in the repo:**

| Ingredient | Where | State |
|---|---|---|
| ADP as the base | `adp_snapshots` — 2,467 rows, 2013-2024, half-PPR and non-PPR | **New as of this session** |
| Deviation around it | `src/draft_sim.py:196` `opponent_pick()` — consensus + Gaussian noise | Built, **sigma unfitted** |
| Roster-need weighting | `_need_penalty()` in the same module | Built |
| Widening over the draft | — | **Not built.** His hypothesis: starts ~round 3, widens after |

**So this is assembly plus one new behaviour, not a new model.** Fourth time `draft_sim.py` has turned
out to hold the answer.

## The one substantive change: ADP, not consensus rank

`opponent_pick()` currently drafts to **consensus ECR**. The founder is asking for **ADP** — where
players actually go, not where experts rank them. Those are measurably different: median ADP − ECR is
**+12 for tight ends**, IQR [+4, +16].

**ADP is the right base and it only became possible this session.** The whole point is simulating
what drafters do, and ADP *is* what drafters did.

## The honest caveat, and it should be on screen

**Sigma is a guess.** `draft_sim.py:17-27` says so: not fitted to anything, and a result that holds at
one sigma is an artifact of the guess. Widening it over the draft adds a second unfitted parameter —
the founder's *"third round is where it starts"* is a recollection, and this project's own record is
that confident recollections about draft behaviour are where it has been wrong.

**So: build it, ship it with the three sigma settings selectable (he asked for that in FR-047), and
label the widening as an assumption rather than a measurement** until FR-070's mocks fit it. A
simulate feature that looks authoritative while resting on two guesses is worse than one that says
what it is.

## Interaction with what is already open

- **FR-046** (wire the opponent model into auto-fill) — this supersedes it with a specific mechanism.
- **FR-047** (per-opponent deviation, widening over the draft) — the widening half lands here; the
  per-opponent half remains separate and depends on this.
- **FR-070** (behaviour-only mocks) — **this is what those mocks would calibrate.** Build the
  simulator, run mocks, fit sigma, and the guess becomes a measurement.
- **FR-045/FR-063** — a simulate that takes real players makes the pace line meaningful again,
  because the board would actually deplete.

Owner: `backend` for the pick logic, `frontend` for the control. **`strategist` registers the
widening function before it is fitted** — not before it is shipped as a stated assumption.
