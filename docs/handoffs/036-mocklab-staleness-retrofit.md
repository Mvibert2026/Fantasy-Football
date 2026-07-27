---
ID: 036
FROM: pm
TO: backend, frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: Mock Lab build
---

## Ask

Mock Lab needs a configuration stamp and a three-state staleness model before it is built. Design's
`STALE-01` finding, expanded after a second pass.

## Three states, not two

The obvious model is current/stale. It is wrong, and the third state only became visible once the
retrofit impossibility was pointed out:

- **current** — the mock's configuration hash matches the league's present configuration.
- **stale** — hashes differ. Excluded from calibration by default, includable by explicit user action.
- **unknown** — hash is null, because the mock predates the field. **Excluded, and *not* includable.**
  There is no basis on which a user could make that call, so offering the toggle would be false
  precision dressed as control.

That third state exists because the data forces it, not because anyone wanted it. It is also why this
must land before collection scales: every mock logged before the field exists is permanently `unknown`.
At one logged mock the cost is zero. At fifteen it is unrecoverable.

## Not everything in a stale mock is stale

Design's distinction, and it must survive implementation. **The picks are facts.** What a manager
actually selected does not change when scoring changes. The *derived* fields go stale — `WE SAID`,
`OUR TOP CALL`, `VERDICT`, `SURPRISE`.

Marking whole rows stale would imply we are no longer sure what the manager picked, which is both
false and corrosive to the one thing this screen exists to establish. Stale treatment applies at field
level, not row level.

## If calibration is per configuration — and it currently is

D-015's default makes the stamp the **grouping key for the whole analysis**, not a flag:

- The aggregate becomes pooled *within* a configuration, with a configuration selector.
- The 30-square progress array and the evidence ladder both count **within the selection**, not
  globally. Thirty mocks across four configurations is not thirty mocks.
- **The Brier score is suppressed entirely when configurations are mixed.** Design's framing is exact:
  a score spanning two scoring systems is not a worse number, it is not a number. Suppress it rather
  than caveat it.
- The realistic post-change state — every mock stale — renders as an **honest empty form** stating that
  calibration starts from zero. Not an error, not a zero. It is a true statement about what we know.

## Backend

Stamp each logged mock with the league configuration in force at logging time — scoring rules and
roster shape, hashed. Not the league id, which survives an edit that invalidates the mock. Export it.
A mock must not be writable without a stamp; enforce at the storage layer so `unknown` can only ever
mean "predates the field" and never "we forgot".

## Frontend

Compare stamped hash against current. Apply the existing Settings stale treatment at field level.
Exclude stale and unknown from aggregate calibration by default; allow including stale only, never
unknown. Suppress Brier on mixed selections.

## Also — the TypeAhead back-port

Design amended `01-draft-board.md` to use Mock Lab's TypeAhead: key map, autofocus, order
randomisation, and `entry_mode`. The Draft board runs under a pick clock and currently has the worse
of the two implementations. **Note:** that amended file has not yet reached this repo — see the
missing-amendments note below.

## Missing amendments — do not build from an incomplete set

Design's index lists five amended files. Three have not arrived:
`handoff_mock_lab/MOCK-LAB-SPEC.md` §5a · `handoff_mock_lab/spec/mocklab-screen.json` (checks ML-17–22,
new endpoint) · `design_handoff_draft_assistant/screens/01-draft-board.md`.

The reasoning above is captured here so the design intent is not lost, but **the build-fidelity spec is
those three files.** Do not implement from this summary alone.

## Done looks like

Configuration hash stamped and exported, unwritable without it. Three states implemented with `unknown`
non-includable. Field-level not row-level staleness. Per-configuration aggregate with Brier suppressed
on mixed selections. Test asserting a mock cannot be written without a stamp. Commit hash and test count.

---
### frontend · 2026-07-27

**The "Also -- the TypeAhead back-port" sub-item only.** Everything else in this thread (the three-state
staleness model, configuration-hash stamping, per-configuration aggregate, Brier suppression) is backend
and Mock-Lab-UI work, none of it touched here, and this thread is not close to done as a whole -- leaving
`STATUS: OPEN`.

**The missing-amendments blocker no longer applies to this sub-item specifically.**
`docs/design-handoff/screens/01-draft-board.md` has since arrived in the repo (pinned 26 Jul 2026, RETROFIT-5
section present in full: key map, autofocus requirement, auto-advance, order randomisation, `entry_mode`).
The other two files this thread named as missing -- `MOCK-LAB-SPEC.md` §5a and `mocklab-screen.json`
checks ML-17-22 -- are about the staleness/config-hash work above, not about the TypeAhead port, so their
absence doesn't block this piece.

**Built:** ported the key-handling logic from the Mock Lab *design-reference* mockup
(`docs/design-reference/mock-lab/03-logging.dc.html`'s `Component` class -- there is no Mock Lab
*application* code in this repo to port from; Mock Lab's own UI and backend remain unbuilt per
`docs/CURRENT-STATE.md`, so the reference HTML's `onKey`/`log`/`undo` functions are the actual thing
ported, not a summary of them) into `DraftRoom.tsx`'s pick-entry input:

- Digits 1-5 commit the shown candidate directly; Enter commits the highlighted one; arrows move the
  highlight; Backspace on an empty field undoes the last pick; Escape clears the field.
- Autofocus re-asserted via a stable ref callback on every (re)attach, not a one-shot guard (the ML-02
  failure mode this thread's parent spec explicitly calls out). Caught a real bug here: the first
  implementation deferred the `focus()` call behind `requestAnimationFrame` and it silently failed in a
  backgrounded browser tab during live verification (rAF is throttled/never fires off-screen) --
  jsdom's test environment did not catch this, only running it in an actual browser did. Fixed to a
  synchronous `focus()` in the ref callback.
- Default (no-query) shortlist: top 5 still-available players by real board rank, shuffled per pick.
- `entry_mode` (`'shortcut' | 'typed' | 'pasted'`) recorded on every commit path, threaded through
  `DraftPickRecord` and the "Export draft log" output.

**One deliberate, load-bearing departure from the spec, flagged rather than silently resolved:** the
Mock Lab reference's shortlist shows a "probability this player goes next" number computed by a
synthetic softmax (`Math.exp(-(cons-avail[0].cons)/2.4)`) -- that formula exists only in the design
mockup, not as real backend math, and this codebase has **no model that predicts "which player is
picked next"** (the availability model predicts "still available at a *future* pick," a different
target). Rendering a next-pick probability in `DraftRoom.tsx` would be inventing a number with no named
backend field behind it -- a direct Principle #1 violation. Built the shortlist ordered by real board
rank instead (`overallRank`, an honest field), with no probability shown on it at all.

**A second thing worth flagging, found while implementing, not asked for in this thread:**
`docs/adr-drafts/ADR-D-mock-logging-instrumentation.md` (Status: Proposed, Strategist-authored, scoped
to Mock Lab's own `mock_picks`/`mock_drafts` tables) explicitly **rejects** randomising a prediction
shortlist's order and **prohibits showing probabilities during entry**, for calibration-contamination
reasons -- almost the opposite of what RETROFIT-5 asks for. The two do not actually conflict as built,
for two reasons: (1) ADR-D is scoped to Mock Lab's own logging screen and tables, which don't exist yet,
not to DraftRoom; and (2) because no next-pick probability is shown here at all (see above), the exact
contamination mechanism ADR-D worries about -- a shortlist that *is* the model's own guess, with
probabilities attached, so one keystroke both records data and agrees with the model -- doesn't apply to
what got built. But `DraftRoom.tsx`'s own `toDraftLog` doc comment says its export "matches the backend's
mock-logging schema field-for-field," and `entry_mode` here is a simpler 3-value vocabulary
(`shortcut`/`typed`/`pasted`) than ADR-D's closed 8-value enum for `mock_picks.entry_mode`
(`shortcut_digit`/`shortcut_enter`/`shortcut_arrow_enter`/`typed`/`paste_exact`/`paste_fuzzy`/
`paste_confirmed`/`grid`). **If DraftRoom's exported log is ever wired into calibration, these two
entry_mode vocabularies and the shortlist-source question need deliberate reconciliation against
ADR-D by Strategist/Backend before that happens, not an assumption that this build already complies.**
Not resolved here -- raising it because I found it, per this project's own rule that Red-team-adjacent
findings get flagged rather than silently decided by whoever happens to notice.

**Tests:** new `ui/__tests__/draft-room-typeahead.test.tsx`, 9 tests -- default-shortlist membership,
digit-commit + auto-advance + `entry_mode`, backspace-undo (and non-undo mid-text), typed vs. pasted
`entry_mode` via a real native `insertFromPaste` input event, Escape-without-committing, a legacy
(pre-field) record round-tripping to an explicit `null` rather than a guessed mode, and a
20-independent-mount statistical check that the shuffle actually varies the order (not just "capable
of it" -- probability of a false pass is on the order of (1/120)^19). `tsc -b --noEmit` clean. Also
verified live in a running browser (own dev-server instance, port 5174, to avoid another session's
5173 server) -- this is where the autofocus bug above was actually caught, not in the test suite.
Commit `82eb2d8`.

**Not screenshot-verified.** The `computer` screenshot action failed in this session with "the Browser
pane is not displayed, so the page is not compositing frames" (also hit and noted in the thread-029
reply this same session) -- appears to be an environment limitation, not an app problem, since
`javascript_tool`/`get_page_text`/`read_page` all worked normally against the same live page. Reporting
this as built and verified by DOM/state inspection in a real browser, **not** as screenshot-verified.

---
### frontend · 2026-07-27

Re-verified live in a real running browser (own dev-server instance, port 5174) as part of this
session's separate work on threads 051/049, which touch the same file (`DraftRoom.tsx`) and its
pick-entry input directly. Confirmed still working after this session's changes: digit-key commit
(pressed `1` via a real `key` action, a filler player got logged and the pick clock advanced), typed
free-text entry (used in this session's own auto-fill/seed setup), and the default shortlist itself
(now BPA-ordered rather than shuffled per thread 051 -- a *change* to this same shortlist, flagged in
the 051 reply, not a regression of RETROFIT-5's core mechanics). Autofocus-on-attach and the field's
"never needs the mouse" behaviour are unchanged; this session added an explicit `suggesterOpen` gate on
top of RETROFIT-5's key handling (thread 051, no auto-open on arrival), which is additive, not a
replacement of anything built here.

Still no screenshot -- same environment limitation as before (`computer` screenshot action times out,
"the Browser pane is not displayed"). Leaving `STATUS: OPEN` for the TypeAhead sub-item's evidence gap
specifically; the rest of this thread (three-state staleness model, configuration-hash stamping,
per-configuration aggregate, Brier suppression) remains untouched and is not this reply's concern.
