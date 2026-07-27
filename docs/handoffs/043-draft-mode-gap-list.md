---
ID: 043
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

Note on 029 only -- items 1-7 are untouched and out of scope for the three tasks assigned this session
(thread 037 item 1, thread 029, RETROFIT-5/thread 036's TypeAhead sub-item). Leaving `STATUS: OPEN` for
whoever picks up the rest of this list.

**The dots and tier grouping this note describes as "appear to be present already" were built in this
same session**, per `029-AMENDMENT-retarget-to-draftroom.md` and `029-frequency-array-on-board.md`'s
reply -- commit `2e38f96`. If the founder's side-by-side happened to run against the dev server after
that commit landed, that would explain seeing them already there without anyone having told this thread
about it yet. Tier grouping headers are also built, not just the dots (contra this note's "may be the
only real gap" phrasing) -- restricted to a single position tab, not `ALL`, for the reason given in the
029 reply (`tier_label` is per-position). Row-height was verified unchanged. See `029-frequency-array-
on-board.md` for full detail, including that it is not yet screenshot-verified.
