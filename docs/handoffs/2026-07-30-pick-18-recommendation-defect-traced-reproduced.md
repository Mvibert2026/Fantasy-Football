---
ID: 2026-07-30-pick-18-recommendation-defect-traced-reproduced
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: FR-2026-07-30-recommendation-logic-is-inverted (the correct-rule spec)
OPENED: 2026-07-30
---

## Ask

Diagnosis only — **no code changed**, per instruction. This is the factual base for the rule you
are specifying. Four findings, each with `file:line`, plus a reproduction. Read finding 1 first:
it changes what the fix has to be.

### 1 — Survival probability does not enter the recommendation score. It is not a sign error.

The brief asked whether the survival term enters with the wrong sign or with the wrong structure.
**Neither. There is no survival term.**

`frontend/ui/data/recommendation.ts:64-72` — the entire score:

```ts
export function recommendationScore(row, round, unfilledPositions): number | null {
  if (row.vbd.kind !== 'present') return null;
  const terms = recommendationTerms(row, round, unfilledPositions);
  return row.vbd.value + terms.reduce((sum, t) => sum + t.points, 0);
}
```

`recommendationTerms` (`recommendation.ts:32-49`) can return exactly three terms: `unfilled_need`
+8, `tier1_te` +18, `early_qb_penalty` −25. No availability, no pick number, no survival.
`rankByRecommendation` (`recommendation.ts:82-97`) sorts on that number alone.

The call site passes no availability either — `DraftRoom.tsx:914`:
`rankByRecommendation(available, currentRound, unfilledPositions)`.

`applyStrategyPreference` (`strategySelector.ts:119-134`), which runs after it, is a
position-promote/demote reorder taking `(scored, round, key)` — also no availability. At the
default strategy `bpa_consensus` (`DraftRoom.tsx:413`) it is a no-op.

**Survival is computed only after the order is already fixed**, at `DraftRoom.tsx:945-1023`
(`recommendationDetail`), purely to build display strings.

Consequence for your spec: this is not a term to re-sign. It is a term to **introduce**, and the
brief's framing — a discount on the wait branch rather than a score addend — is an open design
choice with nothing in the code to preserve.

### 2 — Two strings assert a causal role that the code does not implement

Both reached the founder verbatim.

**`DraftRoom.tsx:960-961`** — the word "only" is unconditional, so 71% renders as "only 71%":

```ts
const survivalFragment = (pct: number | null) =>
  pct !== null && followingUserPick !== null
    ? `, and only ${percent(pct)} likely to survive to your pick at ${followingUserPick}.` : '.';
```

**`DraftRoom.tsx:1005`** — the load-bearing false claim:

```ts
survivalClause = ` ${topName} is ${percent(topPct)} to still be there at ${followingUserPick} and ${altName} is ${percent(altPct)}. That difference, not the point gap, is the reason for the order.`;
```

The point gap **is** the reason for the order (finding 3 shows the arithmetic). The survival
difference plays no part. The sentence is false as written for every pick, not just this one.

This is the mechanism behind the founder's item 2. Both strings are handed to the assistant model
verbatim — `pageContext.ts:145-168` (`recommendationItem`, carries `rec.reason`) and
`pageContext.ts:170-178` (`giveUpItem`, carries the string above). The assistant prose is generated
by `claude-sonnet-5` (`frontend/server/proxy.ts:208`, prod `worker/index.js:222`), so the garbled
"McBride still shows more value over replacement (49) than Allen does not, actually Allen's is
higher (114)" is **model output, not a template**. It reads as the model trying to reconcile the
app's own false causal claim against the VBD numbers it was also given, and self-correcting
mid-sentence. Fix the two strings and that class of garble loses its cause; it is not primarily an
assistant-prompt problem.

### 3 — Reproduced. The VBD numbers on screen are correct; Allen genuinely outscores McBride.

New diagnostic test, **asserts what the code does today, not what it should do**:
`frontend/ui/__tests__/repro-fr-inverted-recommendation.test.ts`. Delete it when your rule lands.

Pick 18 with the next pick at 23 pins the state exactly: 10 teams, slot 3, round 2
(`roundOfPick = ceil(18/10) = 2`, `draft.ts:135-137`; `pickNumbersForSlot`, `draft.ts:175-182`).
Round 2 < 6, so the QB penalty **does** fire. Measured, against the real `board.json`:

| | VBD | +8 need | +18 T1 TE | −25 early QB | score |
|---|---|---|---|---|---|
| Josh Allen (QB1, tier 1) | 113.71 | +8 | — | −25 | **96.71** |
| Trey McBride (TE2, tier 1) | 49.01 | +8 | +18 | — | **75.01** |

Allen wins by 21.70. The three constants are collectively worth 51 points against him and his raw
VBD edge is 64.7, so **the constants are not the proximate cause — VBD is.** Allen is not the
board's #1 either; the shortlist runs Bijan Robinson 180.17, Chase 160.02, Gibbs 145.08, Nacua
131.46, McCaffrey 124.56, Smith-Njigba 114.75. Allen surfaced as top-of-card because the founder's
roster state had those taken. Both VBD figures match `board.json:players[].vbd` exactly (113.71 /
49.01) — **the founder's item on inconsistent VBD is a text defect only; the numbers are right.**

A fourth assertion in that file confirms finding 1 mechanically: mutating the row's availability to
0.01 leaves the score bit-identical.

**On the founder's item 3 (two availability numbers).** Both are correct and they are different
quantities, which nothing on screen says. The board `AVAIL` column is fed `nextUserPick`
(`DraftRoom.tsx:646`), and on the clock `nextUserPick === currentPick === 18`
(`DraftRoom.tsx:634-635`) — so it reads survival **to the pick you are already making**: Allen
0.7875, McBride 0.4042, i.e. the 79% / 40% on screen, sigma-10 at pick 18. The card uses
`followingUserPick = 23` with live re-weighting (`liveAvailability.ts:125-172`, sigma-10 baseline
plus need/run logit adjustment): baselines there are 0.6312 / 0.2250, and the live adjustment lands
them at the 71% / 25% shown. Not a numeric bug. A labelling one — and the `AVAIL` header's own
tooltip says "at your next pick" (`DraftRoom.tsx:1870`) while showing the current pick, which is
close to tautological on the clock.

### 4 — The early-QB finding: read at source, and it is narrower than the assistant said

Source is `docs/preregistration/PR-003-hero-rb-draft-simulation.md:114-121` (result table) and
`:147-153`. Registry mirror at `docs/test-registry.md:331`.

- `qb_early` **−115.4** roster points vs BPA at **sigma=10**, season 95% CI **[−176.3, −54.4]**,
  **0 of 4** seasons positive, sign **p = 0.125**.
- Negative in **12 of 12** season×sigma cells, margins spanning **−64 to −115**.
- **Not significant, and cannot be.** Four development seasons floor the exact sign test at 0.125;
  zero of 15 comparisons survived Benjamini–Hochberg (`PR-003:133-139`).
- Window **2021–2024**, 2025 sealed. Simulated from **slot 3 of a 10-team snake** — the founder's
  own slot, which makes it unusually transferable here.
- `qb_early` is the round ≤ 3 arm (`strategySelector.ts:105`); `PR-003:196` licenses only
  "**strongly suggests** not reaching for a TE or a QB in the first three rounds, on consistency and
  magnitude rather than on a p-value."
- Assumption-bound (`PR-003:198-200`): opponents do not adapt, lineups set with perfect hindsight,
  no in-season management.

**The assistant's summary was wrong in one specific way.** It called −115.4 the "worst case." It is
the **point estimate at the default sigma**; the CI low is −176.3. Calling a point estimate a worst
case understates the uncertainty in the direction that flatters the claim.

**Does the recommender encode it? Partially, and the encoding does not match the finding.**
`recommendation.ts:45-47` applies −25 for `pos === 'QB' && round < 6`. Three mismatches:

1. **Window.** The finding covers rounds 1–3; the penalty covers rounds 1–5.
2. **Units.** −115.4 is season roster points from a draft simulation. −25 is a VBD addend. Nothing
   maps one onto the other; −25 is unfitted, and `PR-007:99-106` records it as such.
3. **Magnitude.** Empirically insufficient — it loses to Allen's VBD edge by 21.7 here.

`PR-007:455-484` (§8.2) already anticipated this term and predicted **DELETE on redundancy**, on the
grounds that VBD against a QB10 replacement baseline in a 10-team 1-QB league already suppresses QB
value, so −25 double-counts. It also flags the regime problem: the QB rank-curve slope collapsed
−67 → −4 across 2021→2025, and a flat penalty is being applied to a regime that no longer exists.

**PR-007 is registered, frozen (`content_hash: sha256:bdcd090e...`) and unrun** — zero entries in
`docs/preregistration/test_run_log.jsonl`, `families/F-RECOMMENDATION-CONSTANTS.yaml` status `open`,
and **thread 093 is open and addressed to me**. That is the instrument that adjudicates these three
constants, and it has not been fired.

## Why

Your spec for the correct rule will be written against whatever the code is assumed to do. Two of
those assumptions are wrong in ways that change the design: there is no survival term to re-sign
(finding 1), and the constants are not what produced this recommendation (finding 3). A spec built
on "flip the sign" would land on nothing.

There is also a sequencing question that is yours, not mine: **PR-007 may delete the −25 outright**,
and a new survival/wait-branch rule specified on top of a term about to be removed will need
rewriting. I hold thread 093 and can run PR-007; I have not, because ordering the two is a
methodology call and I do not grade my own work.

## Confidence, per finding

| Finding | Confidence | Basis |
|---|---|---|
| 1 — no survival term in the score | **Very high** | Read every function in the path end to end; confirmed mechanically by a perturbation test |
| 2 — the two strings assert a false cause | **Very high** for the code claim; **high** for the garble's causal chain | The strings are literal; the model-output link is inference from an LLM call site, not instrumented |
| 3 — reproduction and VBD figures | **Very high** | Reproduced against the real export; both figures match `board.json` |
| 3 — the 79/40 vs 71/25 explanation | **High**, not certain | Baselines and picks match exactly; the exact live-adjusted values depend on the founder's logged picks, which I do not have |
| 4 — PR-003 content and PR-007 unrun | **Very high** | Read at source, not via summary |
| 4 — whether −25 is *wrong* vs *redundant* | **Low, and not mine to settle** | That is exactly what PR-007 measures |

**Standing caveat: I do not judge my own diagnosis.** Nothing above should be treated as a fix
recommendation.

## Done looks like

A reply here stating (a) whether the rule you specify introduces survival as a score term or as a
wait-branch discount, and (b) whether PR-007 runs before or after that spec, so I know whether to
pick up thread 093 now. No code change from me until then.
