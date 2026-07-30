---
ID: 120
FROM: frontend
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
Report only, no action needed from `pm` beyond closing this thread (or relaying to `design` if a
response to their open questions is wanted — see below).

Shipped `docs/design/ASSISTANT-WINDOW.md` item 4, the founder's container complaint ("needs to
have a constant window to be able to continue the conversation, it also doesn't allow for
scrolling"), sequenced behind item 1 (trace mode) per the design doc's own ordering.

**Container** (`frontend/ui/components/shell/AssistantDock.tsx`):
- Width 520px (spec's floor, not its 720px ceiling — see `docs/ideas-inbox.md`'s 2026-07-30
  entry for the measured case).
- Height: `position: fixed` with both `top: 64` (46px TopBar + 18px gap) and `bottom: 18` set,
  giving the browser a definite box (viewport height minus both margins) instead of the old
  `maxHeight: '72vh'`, which is why the transcript couldn't actually scroll before — a
  `maxHeight`-only flex parent gives its `flex: 1` children no definite box to overflow within.
- **Never unmounts.** `children` (the `<Assistant/>` instance, which owns the conversation's
  question/answer/history state) is now rendered on every render regardless of `open`; only its
  `display` toggles. Previously the collapsed branch returned before `children`, so React
  unmounted the conversation on every collapse — the actual mechanism behind "doesn't continue
  the conversation."
- `.answers` (`base.css`) is `overflow-y: scroll` (not `auto`) per the spec's "scrollbar always
  visible" -- see the caveat below.

**Kept, per the design doc's explicit instruction not to touch them:** the three suggestion
chips, and the scope note ("Answers come only from the exports... Nothing is ever answered from
general football knowledge") in the empty state.

**Per-answer sources disclosure** (`Assistant.tsx`, `ui/assistant/claim.ts`'s new
`answerSources()`): the old per-claim `.provenance` line (always in the DOM, gated by the trace
switch) is now one line per answer -- "Answered from what is on screen. N sources" -- closed by
default. Opening it shows one row per source (a MODEL/SOURCE claim's field path, or -- for an
INFERENCE claim -- one row per context id in its `model prose over context: ...` provenance
string, since one reasoning-lane paragraph can cite several context items). Off, each row is a
bare tag pill (MODEL/SOURCE/INFERENCE), no field path. On (Alt+T), the same pill grows the raw
id/field path next to it -- literally "expands to the page.* keys," verified in a real browser:
`frontend/e2e/artifacts/fr077-followup-assistant-sources-off.png` /
`-sources-trace-on.png`.

## Why
This was the item design flagged as blocking (item 4 of 8, sequenced behind item 1). The founder
named this exact gap directly ("the window is crap").

## Done looks like — delivered

- Commit: see this session's write-back in `docs/status/`.
- Tests: `npx vitest run` from `frontend/` — **48 files / 389 tests** (baseline 47/386 + 1 new
  file, `assistant-dock-container.test.tsx`, covering the container's definite-height inline
  style, the conversation surviving a collapse+reopen (including a live follow-up after
  reopening, proving it's a real conversation and not leftover DOM text), and a long
  multi-paragraph answer reaching the DOM in full). `npx tsc -b --noEmit` clean. `npm run build`
  succeeds.
- Screenshots (`frontend/e2e/artifacts/`, all `fr077-followup-assistant-*.png`): empty state with
  the scope note and 3 chips; a long multi-paragraph answer scrolled to its top and to its
  bottom (header/input visibly pinned in both); collapsed to the header pill; reopened with the
  same conversation intact, scroll position included; the sources disclosure open in both trace
  states. Captured against a real dev server + real Chromium
  (`frontend/e2e/verify-assistant-window.mjs`), not just unit tests.
- **One honest gap, not resolved this session:** headless Chromium in this sandbox renders zero
  scrollbar pixels in ANY screenshot, even for a minimal test page with guaranteed overflow and
  explicit `::-webkit-scrollbar` styling (`offsetWidth === clientWidth`, confirmed via an
  isolated repro, not just this app). The screenshots prove the transcript scrolls (different
  content visible top vs. bottom, header/input pinned) but cannot prove scrollbar-track
  *visibility* -- that needs a look at the real app in a real desktop browser. Full account:
  `docs/ideas-inbox.md`'s 2026-07-30 entry, item 3.
- **Two open questions from `docs/design/ASSISTANT-WINDOW.md` I did not answer** (design's own
  §"Sequence, and what I need back" applies to the whole 8-item round, not just item 4, so these
  may already be tracked elsewhere): item 1 in that section (archetype chip states) and item 4
  (a fresh 1500px board capture) are outside this thread's scope (items 1/6 respectively, not
  4). Nothing outstanding from design specifically on item 4.

## Reply

### frontend · 2026-07-30
Shipped as described above. No action needed unless `pm`/`design` want to weigh in on the 520px
width call or the scrollbar-visibility gap (both logged in `docs/ideas-inbox.md`). Leaving
`STATUS: OPEN` since only the `TO:` role may resolve a thread per `docs/handoffs/README.md`.
