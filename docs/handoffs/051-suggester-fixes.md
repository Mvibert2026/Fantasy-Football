---
ID: 051
FROM: pm
TO: frontend
STATUS: RESOLVED
OPENED: 2026-07-27
BLOCKS: none
---

## Ask

Three fixes to the pick-entry suggester in the Draft room. Founder observed all three in the running
app.

### 1. It does not dismiss on click-outside

The suggester stays open. It should close on a click anywhere outside it, and on `Esc` (the help row
already advertises `esc clear`, so confirm that path works too). Standard popover behaviour and
currently absent.

### 2. It opens automatically on page load

It should not. The user has not asked for it, and it covers the board — which is the screen they came
to look at. Open it on focus of the pick-entry field, on `/`, or on typing. Not on arrival.

This is a density violation as much as an interaction one: an overlay obscuring roughly a third of the
available-players list, unrequested, on every page load.

### 3. Remove the order randomisation — show BPA order

**This one is my error and the founder is right to overrule it.**

I recommended randomising the top-five order as a free mitigation against shortcut bias: if position 1
always holds our top pick, a tired user pressing `1` repeatedly is logging our prediction rather than
the actual pick, which self-servingly inflates apparent calibration.

That reasoning is sound **for the Mock Lab**, where the entire purpose of the screen is generating
calibration data. It is wrong **here**. The Draft room is not collecting calibration data — the user is
trying to record a real draft quickly, under a clock. Randomising means they must read all five names
every single pick. Pure friction, mitigating a bias that is not being measured on this screen.

**The rule: randomise where calibration data is collected, order by BPA everywhere else.** Draft room
shows board-rank order, top of list first.

Note the header currently reads `TOP 5 BY BOARD RANK, STILL AVAILABLE — ORDER RANDOMISED`. The first
half stays; the second half goes.

**Check ADR-D before changing Mock Lab.** The Strategist's contamination-control ADR (thread 034) may
have superseded the randomisation recommendation there too. Do not apply this change to Mock Lab
without reading it — this thread governs the Draft room only.

## Two things worth keeping, noted so nobody "cleans them up"

- `RECOMMENDED (unvalidated stopgap score, not a backtested model)` — exactly right. Keep the
  qualifier until there is a backtested model behind it.
- `fills an open starting slot` on each recommendation — this is roster awareness already surfacing,
  and it partially satisfies thread 044. Build on it rather than replacing it.

## Done looks like

Click-outside and `Esc` both dismiss. No auto-open on load. BPA order in the Draft room, header text
updated. Mock Lab untouched pending ADR-D. Screenshot. Commit hash.

---
### frontend · 2026-07-27

All three fixes built in `frontend/ui/views/DraftRoom.tsx`. Mock Lab untouched (no Mock Lab
application code exists in this repo to touch — confirmed again this session).

**1. Click-outside + Esc dismiss.** Added explicit `suggesterOpen` state (previously the dropdown's
visibility was implicitly `candidates.length > 0`, with no independent open/closed concept at all).
A `document.addEventListener('mousedown', …)` effect, subscribed only while open, closes it when the
click target is outside a new `suggesterWrapperRef` around the search box + dropdown (so clicking a
candidate row to commit it — which is *inside* that wrapper — never mis-fires as a dismiss). `Esc`'s
existing handler (which already cleared the query) now also calls `setSuggesterOpen(false)` — it was
advertised in the help row (`esc clear`) but genuinely didn't close anything before this.

**2. No auto-open on arrival.** The field still autofocuses on mount (RETROFIT-5's "never needs the
mouse" — unchanged), but a `suppressNextFocusOpen` ref, set immediately before the ref-callback's own
`el.focus()` call, means that *specific* programmatic focus doesn't open the popover — only a genuine
subsequent focus (click, tab back in, refocus after a commit), typing, or `/` (new global keydown
listener, ignored while already typing in an input/textarea/contenteditable) does. Verified live in a
real running browser: right after navigating to Draft mode the dropdown is absent from the DOM even
though the field has real focus (`document.activeElement` confirmed); a genuine blur→focus transition
opens it; a real `Escape` keypress and a `mousedown` dispatched outside the wrapper both close it (the
outside-click check needed a separate JS read after the dispatch to see the closed state — React's
state update isn't synchronous with the native event, a testing artifact, not a bug — confirmed the
unit tests, which use `act()`-flushed `fireEvent`, close it deterministically on both paths).

**3. BPA order, not randomised.** Removed the Fisher-Yates `shuffled()` helper (now dead code, deleted
rather than left unused) and the `.slice(1)`-then-shuffle step in the default-candidate `useMemo` — it
now returns `defaultCandidateIds` mapped straight to rows, already sorted by real `overallRank`. Header
now reads `TOP 5 BY BOARD RANK, STILL AVAILABLE` with the `— ORDER RANDOMISED` half removed. Verified
live: the dropdown's five rows (Bijan Robinson, Ja'Marr Chase, Jahmyr Gibbs, Puka Nacua, Christian
McCaffrey) exactly match the main board's own top-5 order, every time.

**Kept exactly as asked, untouched:** `RECOMMENDED (unvalidated stopgap score, not a backtested model)`
and `fills an open starting slot` (both live in the *center-pane* recommendation card, a different
element from the search-box suggester this thread covers — see the thread 049 reply for what changed
there, which is additive to these, not a replacement).

**Tests:** `ui/__tests__/draft-room-typeahead.test.tsx`, rewritten for the new behaviour — 16 tests
(was 9): explicit not-open-on-mount / opens-on-focus / opens-on-typing / dismiss-on-Escape /
dismiss-on-outside-click / no-dismiss-on-inside-click cases added; the old
"order is actually randomised" statistical test replaced with its mirror, "order is deterministic
across 8 independent mounts, not randomised"; every pre-existing digit/backspace/typed/pasted/legacy
test still passes unmodified in intent (only needed an explicit `fireEvent.focus()` added where a test
reads `candidate-row-N` before interacting, since that no longer opens for free). `tsc -b --noEmit`
clean. All 16 pass, plus verified live in a real running browser (dev server, port 5174) as described
above — DOM/JS-state inspection, not an image; the `computer` screenshot action still times out in this
session with "the Browser pane is not displayed, so the page is not compositing frames," the same
environment limitation prior sessions (threads 029, 036) hit. Reporting this as built and verified live,
not as screenshot-verified.

Commit `a424a0d` (bundled with thread 049, same file, same session — see that thread's reply for the
049-specific parts of the diff). Setting `STATUS: RESOLVED` — all three asks are done, with real
evidence, and the one thing "Done looks like" asked for that this environment cannot produce
(a screenshot image) is called out explicitly rather than silently skipped.
