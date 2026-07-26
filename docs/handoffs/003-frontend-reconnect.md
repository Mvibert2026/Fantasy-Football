---
ID: 003
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Four items, in this order:

1. **Record your test count** somewhere durable in your working copy, and reply with it here. No
   frontend test count exists anywhere in the backend repo — the project history claims 110 and
   `status.md` does not corroborate it.
2. **Confirm you have absorbed the export path change.** Exports now route to
   `data/export/<league_id>/` rather than flat `data/export/`. The backend log says this
   notification was never sent. Confirm whether your sync script already handles it or is silently
   reading a stale path.
3. **Confirm what actually exists** for the Board / Opponents / Predictions tab structure. Do not
   answer from memory or from a prior session's checklist — open the running app and look.
4. **Then build the Opponents tab**, but only after backend thread 007 delivers the full league
   rosters endpoint. Building it first produces a screen with nothing in it.

## Why

Item 3 is not a formality. These tabs were previously reported as "folded into a single pane" and
were in fact absent entirely — no tabs, no fallback pane, nothing. The tests passed the whole time,
because no test asserted the screens existed. That gap was found by a human comparing screenshots,
which is not a process that scales.

Item 2 is a silent-failure risk: a stale path does not throw, it just serves old data indefinitely.

## Done looks like

- Test count stated as a number
- Explicit yes/no on the `<league_id>` path
- A **screenshot** of the running app showing the current tab structure, attached for the founder to
  look at. Per `docs/operating-model.md`, UI work is reported as "built, pending screenshot
  verification" — never as done, and never on your own report alone.
- Reply with commit hash + test count
