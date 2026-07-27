---
ID: 029
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
Add the 10-dot frequency array to the Board's inline availability badges. It is already implemented
on the player detail sheet and the Availability Explorer — this is applying an existing component in
one more place, not building something new.

## Why
The frequency array is how this product expresses probability honestly: ten dots, three filled, for a
33% chance. It is the single clearest expression of the product's whole thesis.

It is currently missing from the Board — the screen users spend nearly all their time on. So the
signature feature is inconsistently applied, and it is absent from precisely the surface where it
would do the most work. A bare "33%" on the board is the same point-estimate presentation every
competitor ships.

## Constraint
Density is the product. Ten dots inline must not push the row taller or reduce rows per screen. If it
cannot be done inside the existing row height, say so and propose an alternative rather than trading
away density — that trade is the ESPN 2025 mistake this product is explicitly organised against.

## Done looks like
Frequency arrays on Board availability badges, row height unchanged, screenshot attached showing
before and after at the same viewport. Commit hash and test count.

---

## AMENDMENT — 2026-07-27. Retargeted from Prep Board to Draft room.

**This thread originally said "the Board's inline availability badges." That was wrong.** Build it on
`DraftRoom.tsx`, not `Board.tsx`.

**Why.** The founder looked at the running app and observed that the Prep Board has no availability
column — and that this is arguably correct rather than a defect. The two are genuinely different
quantities:

- **Prep** availability is an *unconditional* average over every possible draft. A planning number.
- **Draft** availability is *conditioned on the picks actually made*. A live number.

The frontend audit marked `LIVE-01` as `partial` on the assumption that the spec was right to put a
two-number cell on the Prep board. That assumption is now itself in question and goes to Design when
the pause lifts. Do not build it there in the meantime.

**What DraftRoom actually needs**, per the audit: it already renders `baseline → live` per row, so the
numbers exist. Missing are the **10-dot frequency array** beside them, and **tier grouping with
headers** ("TIER 2 — 3 players left").

The dots are the point. A bare percentage on a row is the same point-estimate presentation every
competitor ships; the dot array is how this product says the same thing honestly. It already exists on
the player detail sheet and the Availability Explorer — this is applying an existing component to the
screen users spend the draft looking at.

**Constraint unchanged:** density is the product. Ten dots inline must not increase row height or
reduce rows per screen. If it cannot be done inside the existing row height, say so and propose an
alternative rather than trading away density.

(Folded in from the standalone `029-AMENDMENT-retarget-to-draftroom.md` fragment this session, which
had no `TO:`/frontmatter of its own and so was invisible to `tools/handoffs.py check` as its own
thread — content preserved here, fragment file removed, per `check`'s "no TO: role" failure this
session found.)

---
### frontend · 2026-07-27

Built against `DraftRoom.tsx`, per the amendment -- not `Board.tsx`.

**Dot array:** added a `RowDots` component to the availability cell in `DraftRoom.tsx`'s available-
players list, next to the existing baseline→live text. Reused the same `dotsFilled`/`freqText`
helpers (`ui/data/liveAvailability.ts`) that already back `Dots` in `PlayerDetail.tsx` and
`SpotlightDots` in `Availability.tsx` -- this is the same component logic at a smaller scale (4px
dots, 1.5px gap vs. the 6-7px used on those two screens), not a reimplementation. Same honesty rule
as `PlayerDetail`'s `HON-02` fix: the array only renders when there is a real number behind it
(`avail.live ?? avail.baseline` when baseline is present), never a fabricated zero-filled array when
neither exists yet.

**Tier grouping:** ported `Board.tsx`'s existing band-divider pattern (it already had this for the
Prep board -- see thread 037 item 4, which is what surfaced that Board and DraftRoom each have half
of the full spec). Headers read `TIER N -- M players left`. Restricted to a single position tab
(not `ALL`), for the same reason `Board.tsx` restricts it: `tier_label` is assigned per position, so
under `ALL`, consecutive rows from different positions can carry the same tier string without
describing the same tier, and grouping them would misrepresent it as one group.

**Row-height constraint (verified, not assumed):** ran the app in a real browser session (own dev-
server instance on port 5174 via a new `prep-verify` entry added to `.claude/launch.json`, since
another chat had port 5173's `prep` server running for this same repo). Measured a live row's
`getBoundingClientRect().height` at 32.15px, then set the dot wrapper's `display` to `none` in the
live DOM and re-measured: still 32.15px, identical. The row's height is governed by its 13px name
text, not by the 4px dots, which is why this holds. Also confirmed: `TIER` headers render only on
non-`ALL` tabs, dot fill counts (e.g. "7 in 10 drafts") track the underlying unrounded probability
correctly against the rounded percent shown alongside it, and there is no horizontal overflow
(`documentElement.scrollWidth === clientWidth`, pane `scrollWidth === clientWidth`).

**Screenshot:** attempted twice (fresh preview-server start, `wait` before capture) -- the `computer`
screenshot action failed both times with "the Browser pane is not displayed, so the page is not
compositing frames," which appears to be an environment limitation of this session rather than an
app problem (`get_page_text`, `read_page`, and `javascript_tool` all worked normally against the same
live page). So: **built and verified live in a running browser via DOM measurement, but no actual
screenshot image exists from this session.** Per the project's own evidence standard (`operating-
model.md`: "a screenshot a human has looked at"), this does not clear the bar on its own -- reporting
it as "built, pending screenshot verification," not done. Whoever can get a screenshot out of this
environment (or the founder, glancing at the running app) should close the loop.

`tsc -b --noEmit`: clean. No dedicated `DraftRoom.tsx` test file exists in the suite to run against
this change; `ui/__tests__/draft.test.ts` (7 tests) and `ui/__tests__/board-filters.test.tsx` (13
tests, covers `Board.tsx`'s unaffected tier-band code) both still pass. Commit `2e38f96`.

Leaving `STATUS: BLOCKED-ON-YOU` is not right either since the ask (TO: frontend) is functionally
done -- setting `STATUS: OPEN` rather than `RESOLVED` specifically because the screenshot half of
"Done looks like" is unmet, and this project's postmortem is exactly a case of a screen being marked
done without one.

---
### frontend · 2026-07-27

Re-verified live, in a real running browser (dev server, own instance on port 5174), as part of this
session's separate work on threads 051/049 in this same file. Both still render correctly after this
session's changes (suggester open/close rework, RECOMMENDED panel rebuild, tab shell, etc. -- none of
which touch the availability-cell or tier-band code paths, but worth confirming rather than assuming):

- **Dot array:** on the RB tab, queried the DOM directly for an element carrying the frequency-array
  title convention (`title` containing `"in 10 drafts"`) -- found one reading `"7 in 10 drafts"` with
  exactly 10 child dot elements, matching `RowDots`.
- **Tier headers:** same RB tab, `document.body.innerText` contains `"TIER 1\n4 players left"` followed
  later by `"TIER 2\n6 players left"`, in board order, restricted to the single position tab as
  designed.

**Still not a screenshot.** Same environment limitation as the original build session and as this
session's other two threads (051, 049): the `computer` screenshot action times out with "the Browser
pane is not displayed, so the page is not compositing frames" -- `javascript_tool`/`get_page_text`/
`read_page` all work fine against the same live page, which is how the above was pulled. Leaving
`STATUS: OPEN` -- this is stronger re-confirmation than before, not the screenshot the thread actually
asked for. Whoever gets a working screenshot tool in this environment (or the founder, glancing at the
running app) should be the one to close this out.
