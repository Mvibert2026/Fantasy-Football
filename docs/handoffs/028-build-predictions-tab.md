---
ID: 028
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
Build the Predictions tab in Draft mode, against
`docs/design-reference/reference/03-draft-predictions.png` and
`docs/design-handoff/screens/03-draft-predictions.md`.

## Why
The second of the two screens that were reported complete and did not exist. Unlike Opponents, this
one is not blocked — the availability model already produces what it needs, so it can be built now.

This is also the screen that most directly shows the product's differentiator. Availability
probability with a stated number is the thing no competitor ships; this is where it lives.

## Hard requirements
- Probabilities must render with their honest uncertainty treatment, not as bare point estimates.
- Where a probability is not computed for a player, show the explicit null. Not `0%` — those are
  different claims, and confusing them here would undercut the exact feature the screen exists for.
- The current availability figures are **unvalidated** — 1 of ~30 mocks logged. Nothing in this
  screen may imply the numbers are calibrated. If the design does not already carry that caveat,
  flag it rather than inventing wording.

## Done looks like
Tab renders with real data, nulls render as nulls, a screenshot attached, and a test asserting the
tab exists. "Built, pending screenshot verification." Commit hash and test count.

---
### frontend · 2026-07-27

Built, pending screenshot verification (see the caveat on that below -- image capture itself failed
in this session, not the app). Commit `d9492ae`. New: `frontend/ui/views/Predictions.tsx`,
`frontend/ui/__tests__/predictions.test.tsx` (+7 tests, all passing in isolation). Modified:
`frontend/ui/App.tsx`, `frontend/ui/components/shell/Sidebar.tsx` (new `predictions` nav entry,
inserted after `opponents`).

**Architecture departure, deliberate, flagged for whoever next owns `DraftRoom.tsx`:** the reference
design (`03-draft-predictions.png`/`.md`) draws this table nested inside Draft mode's own hub, as a
third tab beside Board/Opponents, with pane 1 widening to hold it. This build does not do that --
this round's dispatch reserved `DraftRoom.tsx` for a sibling session, and `DraftRoom.tsx`'s own
module doc already names the alternative taken here ("Opponents and a standalone Predictions table
exist as their own Prep-mode screens"), so it follows that precedent, same as Opponents.tsx. Folding
this into the live Draft-mode hub as an actual tab is real follow-up work, not done here. Reference
availability comes from `ui/data/liveAvailability.ts`'s `computeLiveAvailability`, unmodified -- no
new formula, this screen just reads it per-row over the full available-player list instead of one
row at a time.

**Hard requirement 1 (honest uncertainty treatment):** LIVE renders the sigma-5/sigma-10/sigma-20
sweep as a RANGE column (`lo–hi%`) plus a 10-dot frequency array (`round(p*10)` filled, same idiom
as DraftRoom's `RowDots`/Availability's `SpotlightDots`), never a bare percentage alone.

**Hard requirement 2 (explicit null, never `0%`):** LIVE renders the literal text `not yet` when
`computeLiveAvailability` reports signal `'none'` (verified live in-browser at 0 picks logged: every
row read `not yet`, zero occurrences of a bare `0%` anywhere on screen). BASELINE renders its own
`Cell`-driven `—` for the ~230 players `availability.json` never simulated. Verified with real picks
seeded to reach signal `'thin'` and `'ok'` too (via an automated test, `seedDraft(7)`/`seedDraft(12)`
in `predictions.test.tsx`) -- both compute and display real numbers distinctly from the null state.

**Hard requirement 3 (calibration caveat) -- flagging per the ask, not inventing wording:** the design
spec (`03-draft-predictions.md`) carries no caveat about validation status at all. Rather than author
new copy for the single most differentiator-bearing screen in the app, I quoted (trimmed) the exact
sentence from `docs/CURRENT-STATE.md`'s "Validation status" section verbatim, rendered as a standing
banner (same dashed/`--down` treatment `Availability.tsx` already uses for its own marginals-note
banner, not a new visual pattern): *"The signature claim on this screen is calibrated availability.
It is currently not calibrated: 1 of ~30 required mock drafts is logged, and that one is the real
2025 draft, not a mock. Until that number moves, every probability below is an honest estimate, not
a validated probability."* This needs a real design pass, not a permanent home in component code --
over to design/pm for that.

**Screenshot:** attempted from a real running dev server (`npm run dev -- --port 5176`, launch.json
config `frontend-predictions-c`, added there), navigated and clicked through in a real browser tab,
confirmed via the accessibility tree and full page-text extraction (not just tests) -- the tab is
reachable from the sidebar, renders all 378 real board rows, shows the calibration caveat, and every
LIVE cell reads `not yet` at 0 picks logged. Attempting an actual pixel screenshot
(`computer{action:"screenshot"}`) failed repeatedly across ~10 retries (different tabs, resizes,
waits) with "the Browser pane is not displayed, so the page is not compositing frames" --
`preview_list` showed every dev-server tab this round sharing one `Browser` preview surface across
the 9 concurrent sessions, and I could not get it to composite frames for my tab. This is an
environment limitation in this concurrent-dispatch round, not a rendering defect in the screen --
DOM/accessibility-tree verification was real and thorough, but per `docs/operating-model.md` a
screenshot a human has looked at is still the standard, and I don't have one to attach. Flagging
rather than claiming otherwise.

Test count: 7 new (`predictions.test.tsx`), all pass in isolation and in two of three full-suite runs
this session; the third run's failures were in `offline.test.tsx`/`draft-room-typeahead.test.tsx`
(files I did not touch, DraftRoom.tsx is out of scope for me this round) and reproduced as passing
when re-run in isolation -- consistent with CPU contention from the other 8 concurrent sessions in
this tree, not a regression from this change. Typecheck (`tsc -b --noEmit`) is clean.

Not done: the Draft-mode hub tab fold-in (see departure note above) and the pane-2/pane-3
(scarcity/roster) side panels the reference screenshot also shows -- those are DraftRoom's own
panes, duplicating them here is out of scope for this round by the same reservation.

STATUS: OPEN -- leaving open rather than resolving, specifically because the screenshot a human has
looked at is missing (operating-model.md's own standard) and the Draft-mode hub-tab fold-in is real,
undone work. Everything else in "Done looks like" is met.
