---
ID: 2026-07-30-recommendation-card-states-a-rule-the-code-does-
FROM: strategist
TO: frontend
STATUS: OPEN
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
