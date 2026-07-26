# Screen — Draft room · Predictions tab
**Spec id:** `draft.predictions` · **Pinned:** 26 Jul 2026 · **Machine-readable:** `spec/screens.json#draft.predictions`, `spec/design-tokens.json`, `spec/formulas.json`
**Assert against:** `spec/acceptance-checks.json`

## Composition
Full-width table in pane 1 (the pane widens automatically when this tab is active — it takes 42% of
the centre rail's share).

Header block states the **signal condition in plain language**, coloured `--down` when the signal is
absent or thin:
- < `max(4, teams/2)` picks: "Roster-need and run signals need N picks before they say anything. M logged — the live column is an explicit null, not the baseline repeated."
- < one full round: "Only M picks logged, under one full round. The adjustment is computed but its band is widened and every row is marked thin."
- otherwise: "M picks logged across R rounds. Roster-need arithmetic and run detection are both in play."

## Grid
`grid-template-columns: minmax(120px,1.5fr) 46px 64px 64px 44px 108px 96px; gap:10px; padding:6px 14px`

| Column | Content |
|---|---|
| PLAYER | rank chip + name + inline `+ queue` toggle |
| POS | ui label, position colour |
| BASELINE | num 12px dim2 — the unconditional probability |
| LIVE | num 13px 600, coloured by band; `not yet` when signal is none |
| Δ | ▲/▼ + points, acc/down/dim2 |
| IN 10 DRAFTS | 10 dots, 6px, filled = `round(p*10)` |
| RANGE | num 10.5px dim2, `lo–hi%` |

## Why the dots exist
A bare probability presented alone reads as decisive — that is the specific failure this product
exists to avoid. The dot array makes `41%` read as "4 in 10 drafts". Never ship the percentage
without it, and never print more precision than the model supports.

## Formula
See `spec/formulas.json#liveAvailability`. Summary: log-odds shift on the baseline, from
roster-need demand across the teams picking before your turn plus positional-run pressure over the
last five picks. `need` and `run` are surfaced separately, never pre-combined.

---
## The four constraints (they override any styling instinct)
1. Every number traces to a named backend field. 2. An explicit null is a real state — `0%`, `0`, `—` and "not computed" are four different claims. 3. Never show a part-applied recompute. 4. Density is the product; premium means better organised, not roomier.
