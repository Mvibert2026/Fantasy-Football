# Screen — Draft room · Opponents tab
**Spec id:** `draft.opponents` · **Pinned:** 26 Jul 2026 · **Machine-readable:** `spec/screens.json#draft.opponents`, `spec/design-tokens.json`, `spec/formulas.json`
**Assert against:** `spec/acceptance-checks.json`

## Composition
Card grid in pane 1. `grid-template-columns: repeat(auto-fill, minmax(232px, 1fr)); gap:10px`.
Above the grid, one honest line: roster shape is derived from picks logged in this draft, not a
platform sync; slots fill in league order; a player counts once.

## Card anatomy
```
┌─────────────────────────────┐
│ Team 4              next #24 │ ← header, panel2, hairline below
├─────────────────────────────┤
│ QB   Josh Allen         QB1  │ ← slot rows, 2px left rule in position colour
│ RB   empty                   │ ← empty: dim2 text, line-coloured rule
│ FLEX empty                   │
├─────────────────────────────┤
│ 4 / 9 starters · 1 on bench  │
│ STILL NEEDS  [RB ×2] [TE ×1] │ ← chips, radius 6px, position colour
└─────────────────────────────┘
```

Border: `--live` if on the clock, `--acc` if it is you, else `--line`.

## Slot order and eligibility
`QB×qb, RB×rb, WR×wr, TE×te, FLEX×flex, DEF×def, K×(k?1:0)`. FLEX takes RB|WR|TE. Each drafted
player fills exactly one slot, in that order. Anything past the starters counts as bench.

## Needs chips
Derived, not stored: `want = {QB:qb, RB:rb+1, WR:wr+1, TE:te, DEF:def}` (the +1 absorbs flex),
`gap = max(0, want - have)`. Chips render only for gaps > 0; when all are zero show
"starters complete".

## Team count is dynamic
Renders `teams` cards for any league size. Nothing may assume 10.

---
## The four constraints (they override any styling instinct)
1. Every number traces to a named backend field. 2. An explicit null is a real state — `0%`, `0`, `—` and "not computed" are four different claims. 3. Never show a part-applied recompute. 4. Density is the product; premium means better organised, not roomier.
