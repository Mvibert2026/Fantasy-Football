---
ID: 037
FROM: pm
TO: frontend, backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Four follow-ups from `docs/frontend-audit-2026-07.md`. The audit itself was excellent — it read the
running code rather than eyeballing screenshots, and it found a bug nobody suspected. These are the
loose ends it surfaced.

### 1. `HON-05` — the `<1%` rendering does not exist. Fix first.

`lib/format.ts#percent()` is `Intl.NumberFormat({style:'percent', maximumFractionDigits:0})` with no
sub-0.5% branch, so **every probability under half a percent renders as `0%`**.

This is the highest-priority defect in the audit and it is small. The five-way null vocabulary has
collapsed to four, and it collapsed into the most dangerous neighbour: a real, computed zero. A player
with a 0.3% chance of surviving to your next pick and a player with a genuine 0% now render
identically, on the screen whose entire purpose is honest probability.

Note what the audit says about its character: *"it isn't drifted, it was never built."* Nobody
regressed this. It has always been wrong.

Add the branch, and add a test asserting `0.003 → "<1%"` and `0 → "0%"` are distinct.

### 2. Thread ID collision — `036` is used twice

`docs/handoffs/036-mocklab-staleness-retrofit.md` (pm → backend/frontend, the config-stamp work) and
`036-weekly-finishes-and-season-stats-exports-contrac.md` (backend → frontend) share an ID.
`tools/handoffs.py check` is supposed to fail on duplicate IDs — either it did not run, or the check
did not fire. Investigate which.

Renumber the backend one to the next free ID, re-sync, and confirm `check` now catches duplicates. A
mailbox that silently tolerates ID collisions is worse than no index, because the index looks
authoritative.

Also: that thread's `Ask` and `Done looks like` sections are **unfilled template text**. It announces
contract 1.8.0 but cannot be acted on as written. Whoever opened it should fill it in — the protocol's
"ask fully or don't ask" rule exists because a half-specified thread costs a whole session.

### 3. `tools/fidelity.py` is missing

`docs/design-fidelity.md` references it and the audit confirms it does not exist. It was written and
tested, then delivered to `docs/design-reference/fidelity.py` and never moved. Move it to `tools/`,
verify it runs, and wire it against the screens that now exist.

The audit explicitly framed itself as *"the harness's job done by hand, once."* That is exactly the
work that should not be repeated manually.

### 4. Board has no availability surface at all

`LIVE-01` is `partial` for a specific reason: `Board.tsx` — the Prep-mode screen — carries **no
availability column anywhere**, while `DraftRoom.tsx` has `baseline → live` but no tier grouping and
no dot array.

The spec describes one screen with both. The build has two screens that each have half. That is a
structural divergence rather than a missing feature, so it needs a decision before it gets patched:
reconcile toward the spec's single screen, or formally amend the spec to describe the two-screen
reality. Do not silently keep both.

Raise it with Design when the pause lifts. This is precisely the "real divergence rather than
anticipated" work Design asked to come back to.

## Done looks like

`<1%` renders correctly with a test. IDs unique and `check` proven to catch duplicates. `fidelity.py`
in `tools/` and running. Item 4 raised as a decision rather than patched. Commit hashes.
