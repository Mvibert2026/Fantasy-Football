---
ID: 063
FROM: pm
TO: frontend
STATUS: RESOLVED
OPENED: 2026-07-27
REOPENS: 051 — treat as a regression, not a new request
---

## Founder report

> "You haven't fully fixed the predictive name generator. It should only open when I click into the
> text box, no other triggers. It seems to trigger every pick."

**This is the second attempt at this behaviour.** Thread 051 asked for the suggester to stop opening
unasked. It still opens on every pick. Do not add another guard on top of the last one — **find why it
reopens** and fix the cause. A third partial fix is worse than the current state, because it makes the
component harder to reason about while leaving the founder's problem in place.

## The rule

**The panel opens on explicit user intent to enter a pick. Nothing else opens it, ever.**

| Event | Opens? |
|---|---|
| Click into the pick-entry field | **Yes** |
| Typing into the field | **Yes** |
| A pick is committed (yours or an opponent's) | **No** |
| The board updates or recomputes | **No** |
| Component mount / page load / refresh | **No** |
| League switch | **No** |
| Returning to the Draft tab from another tab | **No** |
| Undo | **No** |
| Programmatic focus from any source | **No** |

**Closes on:** click outside, `Escape`, blur, and on commit.

## The likely cause, and the distinction that matters

The classic shape of this bug is an effect keyed on draft state — something along the lines of a
dependency on the current pick number — that calls focus or open on every change. Committing a pick
changes that state, the component re-renders, and the panel reopens. It looks like "opens every pick"
because that is exactly what it is.

**The distinction to build around: programmatic focus is not user focus.** A field that is focused by
code must not behave as though the founder clicked it. If the component cannot currently tell the two
apart, that is the actual defect — give it an explicit user-intent signal rather than inferring intent
from focus state.

Note that auto-focusing the field after a commit may well be *desirable* for fast entry — the `1-5 to
commit` affordance implies speed matters. **Focus and open must therefore be decoupled**: the field
may take focus, the panel must stay shut until the founder does something.

## Report the root cause

In the reply, state plainly what was actually causing it and why the 051 fix did not catch it. That
sentence is worth more than the diff — the same pattern is likely present elsewhere, and this is the
only way we find out.

## Done looks like

- One fix at the cause, not a guard stacked on a guard.
- **A test per row of the table above.** Nine rows, nine assertions. This is what stops a third round:
  enumerated triggers, each one pinned. A single "does not open unexpectedly" test is what allowed
  this to regress.
- The reply names the root cause and whether the pattern appears in other components.

**File boundary:** `frontend/` only, and the pick-entry component specifically. Coordinate with
threads 051 and 058 — both touch this screen, and 058 § C is on adjacent chrome.

---
### frontend · 2026-07-27 (branch `frontend/063-suggester-reopen-fix`)

**Root cause, stated plainly:** 051's fix guarded exactly one programmatic-focus call site — the
mount/remount ref callback (`setSearchInputRef`) — with a `suppressNextFocusOpen` flag consumed
once by `onFocus`. It never looked at `recordPick`, which is the function every commit funnels
through (digit shortcut, typed/pasted Enter, clicking a candidate row, *and* the board row's own
"mark taken" X — the way an opponent's pick gets logged). `recordPick` ends with a bare
`searchRef.current?.focus()`, kept deliberately for fast keyboard re-entry, but that call went
through the *same* `onFocus` handler with the suppress flag never set for this call site. So the
very next commit's own refocus looked exactly like a genuine user click and reopened the popover.
"Opens every pick" was not an approximation — that is literally what the code did, on every single
commit, including ones logged from the board row rather than the search box. 051's fix was real and
correct for what it covered (mount/remount); it simply didn't cover the call site that fires on
every pick, which is why the founder still saw it on every pick after that fix shipped.

**Why a third guard would have been wrong, and what was done instead:** the fix is not a new,
competing mechanism bolted on top of 051's. It's the *same* `suppressNextFocusOpen` guard, applied
at the one additional call site that needed it, via a single shared helper
(`refocusSearchWithoutOpening`) both call sites now use. That helper also closes a latent leak in
051's own mechanism: it only arms the suppression when `document.activeElement !== el`, because
calling `.focus()` on an already-focused element fires no `focus` event at all in a real browser —
arming the flag unconditionally (as 051 did, harmlessly, since its only call site is a genuine
remount that's never pre-focused) would, at this new call site, leave a stale `true` sitting
unconsumed and wrongly suppress the *next* real click-to-focus later on, which would have been a
third, quieter regression of the exact same rule.

Separately, `recordPick` now also explicitly calls `setSuggesterOpen(false)` on every commit, to
satisfy the stated rule "closes on ... commit" for the case where the panel was genuinely open
(user had focused/typed) at the moment of commit — independent from the reopen-prevention fix
above; one is "commit must close it if open," the other is "commit must never open it."

**A second, related defect found and fixed in the same file, same rule:** the project's own smoke
harness (`frontend/e2e/smoke.mjs`, already in the tree from a prior/parallel session, checks every
row of this thread's table against a real Chromium session) caught that "click into the field"
itself was silently broken on the very first real click after page load. Cause: mount autofocus
already gives the field real DOM focus before the user can click it, and clicking an
already-focused element does not fire a new `focus` event in any real browser — so `onFocus`-only
detection means the panel's *opening* trigger was itself unreliable, not just its *not*-opening
guarantee. Fixed with an `onMouseDown` handler on the input that opens the panel directly — a real
mousedown is never produced by this component's own `.focus()` calls, so it's an independent,
unambiguous "the user actually clicked here" signal, not a second thing arguing with `onFocus` over
the same event. This was pre-existing (confirmed via `git show HEAD:frontend/e2e/artifacts/
report.json`, which already recorded this exact failure before this session touched anything) and
in scope only because it's the same rule (table row 1) on the same component.

**Does the same anti-pattern exist elsewhere?** Checked: `grep -rn "\.focus()" ui` (excluding
tests) turns up exactly three call sites, all in `DraftRoom.tsx` — the mount/remount ref callback,
the global `/` shortcut handler (which correctly wants to open, since `/` is itself explicit user
intent), and the now-fixed post-commit refocus. No other component in `frontend/ui` infers open/
visible state from DOM focus state, and no other `useEffect` is keyed on draft/pick state to drive
an open-style side effect. This pattern is contained to this one component as far as this
codebase's current file set goes.

**Tests:** `frontend/ui/__tests__/draft-room-typeahead.test.tsx`, new `describe` block "thread 063:
suggester opens ONLY on explicit user intent (regression fix)" — one test per row of this thread's
table, nine tests, in the table's own order (click opens, typing opens, commit does not open/does
close, board recompute does not open, mount does not open, league switch does not open, tab-return/
remount does not open, undo does not open, programmatic focus from this component's own call sites
does not open while still genuinely moving DOM focus). Row 3 and row 9 were verified to actually
catch the regression: `git stash`-ing only the `DraftRoom.tsx` fix and re-running showed exactly
those two tests fail against the un-fixed source, confirming they pin the real bug rather than
passing vacuously. Full suite: **163/163 passing, 18 files** (was 154/18 before this session — nine
net-new tests, no existing test touched). `tsc -b --noEmit` clean.

**`npm run smoke` (Playwright, real Chromium, thread 063's own founder-loop harness): 16/16
passing**, including the harness's own thread-063-labelled assertions ("suggester NEVER reopens
after a commit," "suggester closed after undo," "suggester closed on return to Draft tab," "suggester
closed after reload"). One live-browser-only gotcha hit and resolved along the way, noted in case it
recurs: `smoke.mjs` spawns its own dev server but does not fail loudly if port 5173 is already bound
by a stale leftover process from an earlier invocation — it just proceeds against whatever is
already listening there. A stale server from before the `onMouseDown` fix was silently serving the
old code for two consecutive "green-except-one" smoke runs; killing the orphaned process and
re-running is what actually confirmed the fix. Screenshot: `frontend/e2e/artifacts/draftroom.png`
(regenerated this session, real Chromium capture via the smoke harness, mid-draft state after five
committed picks, dropdown correctly closed).

Commit and branch: see `docs/status.md` session entry / this reply's accompanying commit for the
hash. Branch `frontend/063-suggester-reopen-fix`, pushed to origin.

Setting `STATUS: RESOLVED`.
