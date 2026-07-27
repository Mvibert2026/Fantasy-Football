---
ID: 049
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: none
---

## Ask

Draft mode gap list, from a side-by-side of the running app against Design's prototype. Founder
compared them directly; this is observed, not inferred from the spec.

**What the app already has and is good:** available-player list with `baseline → live` percentages
**and dot arrays** (so thread 029's dots are partly there already — verify before rebuilding), position
scarcity bars with "vs expected by pick N", a scarcity insight line, Queue/Watchlist, Next Decision,
roster panel, undo, export draft log, reset.

**What the prototype has and the app does not:**

1. **The three tabs.** Prototype has `Board / Opponents / Predictions` inside Draft mode. The app is a
   single pane. This is the long-standing gap and it is still the headline.

2. **The recommendation panel — the biggest functional gap.** Prototype shows a `RECOMMENDED` card:
   player, position rank, team, bye · projected points with an **honest range** (`202`, `156–250`) ·
   a plain-language reason ("best value by VBD — 72 points over replacement in your format, and only
   1% likely to survive to your pick at 38") · a `Why this rank` action · and a **`WHAT YOU GIVE UP`**
   section naming the next-best alternative and the exact trade ("Jaxon is 74 over replacement vs Tee's
   72 — you give up 2 points of value today. Both are 1% to survive to 38. That difference, not the
   point gap, is the reason for the order.").

   That last part is the product. It is the "why our rank differs" feature in its strongest form —
   showing the *cost of the recommendation*, not just the recommendation.

3. **Roster slot counts as chips** — `QB 0/1 · RB 0/2 · WR 2/3 · TE 0/1 · FLEX 0/2 · DEF 0/1 · BN 0/6`.
   The app shows a roster list; the prototype shows fill state at a glance.

4. **`MY PICKS` showing the full sequence** — 3, 18, 23, 38, 43, 58, 63, 78, 83, 98 with the current
   one highlighted. The app shows only picks taken so far.

5. **`Auto-fill to my pick`** — advance the draft to the user's next turn in one action. In a real
   mock this is the difference between usable and not.

6. **A live-draft indicator** (`DRAFT LIVE`) and a richer league selector showing platform, size, slot
   and draft type (`Dynasty of Dorks · Sleeper · 10T · pick 3 · Snake · CURRENT`).

7. **`not yet` rendering, visibly.** The prototype's Predictions table shows `not yet` in the LIVE
   column with empty dot rings. The audit found this string missing from DraftRoom rows. The prototype
   demonstrates exactly what it should look like.

## Priority

2 first — the recommendation panel with `WHAT YOU GIVE UP` is the single highest-value item, and it is
mostly presentation of numbers the backend already produces.

Then 3, 4, 5 together — they are small, they are all roster/pick-sequence display, and 5 materially
changes whether the app can be used in a real mock.

Then 1, the tabs, which is the larger structural change.

## Note on 029

The dots appear to be present on the app's available-player rows already. Confirm what is actually
missing before rebuilding — tier grouping headers may be the only real gap. Do not rebuild something
that exists.

## Done looks like

Screenshots of each change beside the prototype. Report as "built, pending screenshot verification".
Commit hashes.

---
### frontend · 2026-07-27

**Renumbered 043 -> 049.** `tools/handoffs.py check` failed this session with a duplicate ID: this
file and `043-weekly-finishes-json-season-stats-json-ready-con.md` both claimed 043. That file is the
established one (committed 2026-07-26, referenced by ID from `017-weekly-finishes-season-stats.md`
and `039-weekly-finishes-and-season-stats-exports-contract.md`); this one was created uncommitted this
session, so this is the one renumbered, following the same precedent thread 037 item 2 used for the
last 036 collision. `check` passes clean after the rename plus the `029-AMENDMENT-*` fix below.

Note on 029 only -- items 1-7 are untouched and out of scope for the three tasks assigned this session
(thread 037 item 1, thread 029, RETROFIT-5/thread 036's TypeAhead sub-item). Leaving `STATUS: OPEN` for
whoever picks up the rest of this list.

**The dots and tier grouping this note describes as "appear to be present already" were built in this
same session**, per `029-frequency-array-on-board.md`'s amendment and reply -- commit `2e38f96`. If the founder's side-by-side happened to run against the dev server after
that commit landed, that would explain seeing them already there without anyone having told this thread
about it yet. Tier grouping headers are also built, not just the dots (contra this note's "may be the
only real gap" phrasing) -- restricted to a single position tab, not `ALL`, for the reason given in the
029 reply (`tier_label` is per-position). Row-height was verified unchanged. See `029-frequency-array-
on-board.md` for full detail, including that it is not yet screenshot-verified.

---
### frontend · 2026-07-27

Worked items 2 (highest priority) and 3-4-5 (together, as instructed) in full. Made a start on item 1
(the tab shell) and did not touch items 6-7. All in `frontend/ui/views/DraftRoom.tsx`; commit `a424a0d`
(bundled with thread 051's suggester fixes, same file, same session).

**Item 2 -- RECOMMENDED panel + WHAT YOU GIVE UP (done).** The center-pane on-clock card now shows:
name / `positionalLabel` (e.g. `RB1`) / team / bye; projected points plus an **honest range** --
derived, not fabricated: `board.json`'s `ci_low`/`ci_high` are confirmed (checked directly against the
export, all 378 rows) to be an interval on **VBD**, not points (`ci_applies_to: "vbd"` always), and
this codebase already has a comment saying so (`board.ts`). Rather than either mislabeling that
interval as a points range or dropping the ask, this derives one: `projected_points − vbd` is a real,
per-row-computable, per-position-constant offset (verified empirically across the whole board --
RB 130.99-131.00 across 116 players, WR 124.45-124.46 across 148, etc., i.e. constant to floating-point
noise), so adding it back to both ends of the real VBD interval is an exact unit conversion of two
already-real fields on the same row, not a second data source. Documented at length in
`pointsRangeFromVbdInterval`'s doc comment, and flagging it here too: **this is a considered judgment
call, not an uncontested one** -- if backend/PM would rather this be a real contract field
(`points_low`/`points_high`) than a frontend-side derivation, say so and I'll swap it. Below the range:
a plain-language reason (VBD-based, or tier-scarcity-based when the top pick's tier is down to ≤2
players at that position, or the sparse-projection case when there's no projection at all -- three real
branches, no synthetic fourth), a `Draft {name}` button and a `Why this rank` button (opens the same
player-detail sheet the board rows use), and a **`WHAT YOU GIVE UP`** section naming `recommended[1]`
(the actual next-best-scored alternative, not simply next-highest-VBD -- see the live example below for
why that distinction matters) with its VBD trade and both players' real live-availability percentage at
the user's *next* pick after this one (a new `followingUserPick` value, distinct from the existing
`nextUserPick` which equals the current pick while on the clock). Verified live against the real running
app, pick 3 on the clock: *"Bijan Robinson RB1 ATL · BYE 11 / 303.2 projected pts / honest range
266.3 – 353.4 / VBD 172.2 · fills an open starting slot / Best value by VBD — 172 points over
replacement in your format, and only 4% likely to survive to your pick at 18." / WHAT YOU GIVE UP:
"Ja'Marr Chase (WR) is the next best. Ja'Marr Chase is 152 over replacement vs Bijan Robinson's 172 —
you gain 20 points of value today. Bijan Robinson is 4% to still be there at 18 and Ja'Marr Chase is
0%. That difference, not the point gap, is the reason for the order."* -- this is the exact shape the
thread's worked example asked for, with real numbers. `RECOMMENDED (unvalidated stopgap score, not a
backtested model)` and `fills an open starting slot` kept verbatim, per thread 051's explicit note not
to touch them.

**Items 3-4-5 (done, together as instructed).**
- **3, roster chips:** `QB 0/1 · RB 0/2 · WR 0/3 · TE 0/1 · FLEX 0/2 · DEF 0/1 · BN 0/6` (exact format
  from the thread, verified live at that exact string on a fresh draft) -- aggregated from the same
  `rosterSlots` the roster list already builds, not a second computation, fixed display order
  (QB/RB/WR/TE/FLEX/DEF/BN) since the underlying `league.json:roster.starters` key order (QB/RB/WR/TE/
  DEF/FLEX) doesn't match the thread's own example order.
- **4, MY PICKS full sequence:** now renders every pick in `league.pickSequence`
  (`league.json:pick_sequence`, a real field, already loaded and previously unused in this file), not
  just picks already made -- done/current/upcoming styled distinctly, current pick (the next one
  belonging to the user) highlighted in accent. Verified live: `3 18 23 38 43 58 63 78 83 98 103 118
  123 138 143 158` -- all 16 of this league's real pick numbers, matching the thread's own worked
  example for the first 10.
- **5, Auto-fill to my pick:** built, but **deliberately not** the design prototype's `simToMe`.
  Flagging this because it reverses something this exact file's own doc comment previously argued
  against building at all, for a real reason: the prototype's version assigns a **random real board
  player** to every skipped opponent pick, which is indistinguishable from a real logged pick in
  "Export draft log" and silently wrong for every availability/scarcity number downstream (an invented
  player would read as actually taken, when the app has no idea who was really picked). This build
  instead advances the pick clock and writes each skipped pick with `playerId: null` and a fixed,
  unmistakably-synthetic name (`(auto-filled — unknown pick)`), `entryMode: null` -- honestly "someone
  picked, we don't know who," never a fabricated identity. The real tradeoff this leaves: availability/
  scarcity math through the auto-filled range won't reflect the opponents' actual picks, since none are
  invented to stand in for them. If the founder specifically wants the prototype's fabricated-identity
  version instead (accepting that data-integrity cost for a punchier UI), that's a explicit call to
  make, not one I made unilaterally here. Written as a single `persist()` over the whole batch
  (Principle #3 -- no intermediate render with only some of the skipped picks present). Verified live:
  disabled while genuinely on the clock (nothing to skip), enabled and functional otherwise.

**Item 1 -- tab shell (started, not complete).** Added a real `BOARD / OPPONENTS / PREDICTIONS` tab bar
at the top of Draft mode; Board is exactly the existing three-pane content (unchanged); Opponents and
Predictions each render an honest, plainly-worded "not wired into Draft mode yet" state. Deliberately
**not** importing or duplicating the real Opponents/Predictions screens from this file -- both are owned
by sibling sessions working concurrently in this same checkout this round (Opponents is shipped in Prep
mode; Predictions may or may not exist yet depending on this round's build order), and importing
mid-edit files from another active session risks a broken build with no way to coordinate the fix.
Verified live: switching tabs works, Board's content is intact, the other two states render and switch
back cleanly. **What's still missing from item 1** and from the thread as a whole: a real `DRAFT LIVE`
indicator and the richer league selector (item 6), and `not yet` rendering on Predictions specifically
(item 7) -- neither touched this session. Leaving `STATUS: OPEN` for whoever picks up items 1 (full),
6, and 7.

**Tests:** `ui/__tests__/draft-room-recommendation.test.tsx`, new, 8 tests -- roster chip format/order,
full pick-sequence rendering, auto-fill's synthetic-placeholder behavior and its disabled state on-clock,
the RECOMMENDED card's content + WHAT YOU GIVE UP presence, and the tab shell's default/switch/honest-
placeholder behavior. All real-data-backed (`loadDatasetFromDisk()`), same rationale as this repo's other
DraftRoom/board tests: these are properties of the real board/league shape, not a fixture's. `tsc -b
--noEmit` clean. 24 tests total across both `DraftRoom.tsx`-scoped test files (16 + 8), all passing.

**Screenshot status:** same as thread 051 and as thread 029/036 before it -- the `computer` screenshot
action times out in this session ("the Browser pane is not displayed, so the page is not compositing
frames"), an environment limitation, not an app problem (`javascript_tool`/`get_page_text`/`read_page`
all worked normally against the live app the whole session, which is how every number quoted above was
actually pulled off the running page). Reporting this as **built and verified live in a real running
browser, pending screenshot verification** -- not as done, per `docs/operating-model.md`'s evidence bar.
