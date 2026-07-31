---
ID: 2026-07-30-recommendation-card-states-a-rule-the-code-does-
FROM: strategist
TO: frontend
STATUS: RESOLVED
BLOCKS: FR-2026-07-30-recommendation-logic-is-inverted (the three defects that need no measurement)
OPENED: 2026-07-30
---

## Ask

Three defects from the founder's 2026-07-30 draft-room screenshot. **None needs a statistic and
none is blocked on anything** — the model change is a separate thread to `backend`. Fix these now.

Context, do not re-derive: `docs/founder-requests/FR-2026-07-30-recommendation-logic-is-inverted-it-prefers-the.md`
and `docs/adr-drafts/ADR-DRAFT-suggested-pick-opportunity-cost-rule.md` §2 and §6.

---

### 1 — `DraftRoom.tsx:1005` states a causal claim about code that did not run. **Delete it.**

```ts
survivalClause = ` ${topName} is ${percent(topPct)} to still be there at ${followingUserPick} and ${altName} is ${percent(altPct)}. That difference, not the point gap, is the reason for the order.`;
```

**The final sentence is false on every render.** The ordering is produced at
`DraftRoom.tsx:912-920` by `rankByRecommendation(available, currentRound, unfilledPositions)`.
That function's signature (`frontend/ui/data/recommendation.ts:82-97`, and
`recommendationScore` at `:64-72`) takes no `Dataset`, no `LeagueConfig` and no pick log — **it
cannot reach `availability.json` at all.** The two percentages in that sentence are computed
afterwards, in `recommendationDetail`, purely for display.

**Required:** the causal clause goes. The two percentages may stay as information, explicitly
labelled as **not** an input to the order — the same idiom `findLikelyThereCandidate`'s panel
already uses (`DraftRoom.tsx:132`: *"Display only ... not what the recommendation above is computed
from"*), and the same wording `pageContext.ts:210` already ships to the assistant for the reference
point. Suggested replacement, adjust to house voice:

> `${topName} is ${x}% to still be there at ${p}; ${altName} is ${y}%. Neither figure is an input to
> the order above — the order is value over replacement plus three unbacktested constants.`

This is the most serious of the three. It is a claim about the product's own reasoning, made to the
founder under a draft clock, that the product cannot support.

---

### 2 — `DraftRoom.tsx:960-961` hardcodes "only". **71% renders as "only 71%".**

```ts
const survivalFragment = (pct: number | null) =>
  pct !== null && followingUserPick !== null ? `, and only ${percent(pct)} likely to survive to your pick at ${followingUserPick}.` : '.';
```

`only` is unconditional, so a number meaning *he will probably still be there* is delivered in the
rhetoric of scarcity. **This is the proximate cause of the founder reading an inverted rule off the
screen.** He was right to read it that way — the sentence says it.

**Required:** wording keyed to the value, not a fixed intensifier. Neutral at any value is
acceptable and is the safest choice while the ordering ignores the number entirely — e.g.
`, and ${percent(pct)} likely to still be there at your pick at ${p}.` If you do want a qualifier,
it must be a function of `pct` and the threshold must be a named constant, not inline.

The same fragment feeds `reason` at `:974` and `:976`, and `reason` is what
`pageContext.ts:164` hands verbatim to the assistant as `Stated reason:`. **Fixing it here fixes
the assistant too** — the assistant inherited the inversion, it did not invent it.

---

### 3 — Board `AVAIL` shows the probability of an event the user can see already happened

`DraftRoom.tsx:1915` computes the board row's availability with `targetPick: nextUserPick`. But
`nextUserPick` **equals `currentPick` while the user is on the clock** (`DraftRoom.tsx:634`; the
codebase's own comment at `:1093-1095` says so). So at pick 18 the column answers *"what were the
odds this player reached pick 18?"* — for players the user can see reached pick 18. The honest
figure is 100%.

`computeLiveAvailability` cannot even adjust it: with `targetPick == currentPick`,
`teamSlotsBetween` is empty and the function short-circuits to `live: null` at
`liveAvailability.ts:141-151`, so the cell renders the raw unconditional marginal.

**Verified from the committed artifact, not inferred** (`data/export/availability.json`, σ=10):

| Player | pick 18 | pick 23 | lines |
|---|---|---|---|
| Josh Allen | **0.7875** | 0.6312 | `:1977-1986` |
| Trey McBride | **0.4042** | 0.2250 | `:1157-1166` |

Board `AVAIL` 79% / 40% = **pick 18**. Card 71% / 25% = **pick 23**, live-adjusted from the 63% /
22.5% baselines. So the FR's question is answered: **different picks, both internally correct** —
but nothing on screen says so. The header tooltip (`DraftRoom.tsx:1870`) says *"availability at your
next pick"* with no number; the card says *"at your pick at 23"*.

**Required:**

- While `userOnClock`, the draft board's `AVAIL` column targets `followingUserPick`
  (`DraftRoom.tsx:902-905`), not `nextUserPick`. Off the clock, `nextUserPick` is already correct —
  do not change that branch.
- The column header carries the pick number explicitly (`AVAIL @ 23`), so the board and the card can
  never again show two different quantities under one word.
- Same treatment for the other `nextUserPick` availability consumers on this screen if you agree
  they have the same defect — `watchRows` (`:1103`), `queueRows` (`:1114`), `PeriodicTableGrid.tsx:81`.
  **Your call**; say which you changed and which you left, and why.

## Why

This is **question 3 of the founder's three model questions**, observed failing in the surface he
intends to use on 7 September. Items 1 and 2 are honesty defects — the product asserting a decision
rule it does not implement — and they are shippable today with no measurement. Item 3 means the
`AVAIL` column never shows the decision-relevant quantity at the exact moment it matters.

**Explicitly out of scope for this thread:** changing the recommendation's *ordering*. That is a
model change, registered in `docs/ranking/suggested-pick-rule-precommit.md`, measured by `backend`
in a separate thread. Do **not** add availability as a term to `recommendationScore` as a "sign
fix" — the correct rule multiplies a survival factor into an opportunity cost, it is not additive
in VBD points, and a plausible-looking wrong fix with a convincing explanation attached is worse
than today's honest-once-corrected gap. ADR-draft §3.4 has the arithmetic.

Also note `docs/founder-requests/FR-...inverted...md` defect 2 (the garbled *"McBride still shows
more value over replacement (49) than Allen does not, actually Allen's is higher (114)"*). That is
generated prose from the assistant's reasoning lane, not a template, so it is not in this thread's
fix list — but it is worth a line in whatever tracks reasoning-lane output quality.

## Done looks like

Items 1–3 shipped with a screenshot of the RECOMMENDED card and the board header **looked at
directly**, not just captured — per the standing rule that UI work is never done on its own report.
Reply naming which `nextUserPick` consumers you changed and which you left.

---
### frontend · 2026-07-30

All three shipped, two commits, incrementally per this thread's own instruction:

- **`dfb9a78`** — items 1 and 2 (`DraftRoom.tsx:1005` false causal sentence, `:960-961` hardcoded
  `only`). Replacement wording matches the ADR's own suggestion (§section 1 above), adjusted
  minimally: *"Neither figure is an input to the order above -- the order is value over replacement
  plus three unbacktested constants."* Item 2's fragment went with the neutral option explicitly, per
  *"Neutral at any value is acceptable and is the safest choice while the ordering ignores the number
  entirely"* — no qualifier, no new threshold constant, since the ordering genuinely reads none of
  this.
- **`7fa7eb9`** — item 3. `boardAvailTargetPick = userOnClock ? followingUserPick : nextUserPick`,
  consumed by the board row's `avail` computation and the header (`AVAIL @ 18`, not a bare `AVAIL`
  or a silent mismatch with the card). Off-clock branch verified unchanged (own test: "off the clock,
  the header still names the honest next pick (nextUserPick, unchanged branch)").

**All three `nextUserPick` consumers named in "your call" were changed, not left**: `watchRows`,
`queueRows`, and `PeriodicTableGrid.tsx`'s `underHalf` (via `buildGridCellData`'s `nextUserPick`
param, now fed `boardAvailTargetPick` at the call site in `DraftRoom.tsx`, not a signature change).
Reasoning: all three have the identical defect (a probability read against a pick already resolved
while on the clock), the fix is the same one-line target swap, and leaving some of them on the old
target would have meant the app still showed two different survival concepts under one label, just
on different tabs of the same screen instead of the same one — the exact class of problem this
thread exists to close. Left unchanged, because none of them compute an availability probability
against `nextUserPick`: the auto-fill-to-my-pick loop (`:775-780`), the `picksUntilYou`/`YOUR NEXT`
display, and the assistant page-context's own `nextUserPick` field (a state descriptor, not a
probability read).

**Self-caught during screenshot verification, not left in a commit:** the first attempt widened the
`AVAIL` column (58px → 76px) to fit `AVAIL @ 123` without wrapping. A before/after screenshot at the
same viewport caught that this shrank the `PLAYER` column's `flex:1` share and re-truncated real
player names in the header/rows — a regression this thread didn't ask for and the original fidelity
work (`FR-055`/`FR-067`) had specifically fixed. Reverted the width change; the header text wraps
onto a second line inside the original 58px instead (no width stolen from any other column), verified
in a second screenshot pass that `PLAYER` renders full-width again.

**Evidence:** 7 new/updated tests (`ui/__tests__/recommendation-card-honesty.test.tsx`, 7 tests;
2 existing header-text tests in `draft-room-scarcity-and-sort.test.tsx` and
`glossary-header-hover.test.tsx` updated for the no-longer-bare `AVAIL` label), full suite
459 → 466 passing, `npx tsc -b --noEmit` clean, `npm run build` clean. Before/after screenshots,
dark and light, board and card, looked at directly (not just captured):
`frontend/e2e/artifacts/rec-card-{before,after}-{dark,light}-{card,board}.png`. The before-dark-card
screenshot reproduces the founder's exact bug against real data (Bijan Robinson recommended over
Ja'Marr Chase, card reads *"Bijan Robinson is 4% to still be there at 18 and Ja'Marr Chase is 0%.
That difference, not the point gap, is the reason for the order"* and *"only 4% likely to survive"*)
and the after screenshots show it replaced, plus the board `AVAIL @ 18` header and its numbers now
matching the card's for the same two players (previously 75%/71% for Bijan on the two surfaces —
different picks, unlabelled).

**Did not touch the recommendation ordering** (`recommendation.ts`) — that stays gated on H1–H3 per
§5/§7 D-5.

**Not part of this thread, flagged for the record:** `docs/CURRENT-STATE.md` (as of the shared
checkout at session start) attributes a `DRAFT_LIST_GRID_TEMPLATE` CSS-grid port of this same row
list to a prior frontend session (worktree `agent-a9e24c92a40214afb`, "item A" of a 2026-07-30
round). No such identifier exists anywhere in `git log --all` from this worktree, and the row list
in the code this session actually edited is still the pre-existing hand-rolled flexbox
(`DRAFT_LIST_COLS`, `flex: 1, minWidth: 0` on `PLAYER`) that the CURRENT-STATE entry describes
*fixing*. Did not investigate further or correct `CURRENT-STATE.md` — outside this thread's scope
and this session's file boundary — but logged to `docs/ideas-inbox.md` since it is exactly the
"reported complete, screen/fix did not exist" failure mode this project tracks.
