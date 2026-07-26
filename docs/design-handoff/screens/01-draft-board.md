# Screen — Draft room · Board tab
**Spec id:** `draft.board` · **Pinned:** 26 Jul 2026 · **Machine-readable:** `spec/screens.json#draft.board`, `spec/design-tokens.json`, `spec/formulas.json`
**Assert against:** `spec/acceptance-checks.json`

## Composition
Pane 1 of the three-pane draft room. Tab bar (Board / Opponents / Predictions) sits above.

```
[ Board | Opponents | Predictions ]              ← tabs, radius 6px top corners only
[ ALL ][ QB ][ RB ][ WR ][ TE ][ DEF ]           ← position filter chips
SORT  our rank · consensus · delta · proj pts        N left
─────────────────────────────────────────────────
TIER 2                                3 players left ← surface lift + count
 12  Brock Bowers      TE1  LV   ▲3   33%→41%   ✕
 16  Josh Allen        QB1  BUF   ·    39%→48%   ✕
```

## Pick entry — amended 26 Jul 2026 (RETROFIT-5)

**Draft pick entry now uses the Mock Lab TypeAhead implementation.** Two were built; this screen had
the slower one, and it is the surface that runs under a pick clock.

| Key | Action |
|---|---|
| `1`–`5` | commit that candidate directly — the common case is one keystroke |
| `Enter` | commit the highlighted candidate |
| `ArrowUp` / `ArrowDown` | move the highlight |
| `Backspace` on an empty field | undo the last pick |
| `Esc` | clear the field |

Requirements, all three load-bearing:

- **Autofocus on mount, re-asserted when the input node attaches.** A one-shot guard that fires before
  the element is focusable leaves the field unfocused, and the screen claims keyboard-only operation.
- **Auto-advance on commit** — clear the field, advance the pick, re-rank. No confirm step.
- **Candidate order randomised.** The five are shown in random order so position no longer encodes our
  confidence, which breaks the "press 1 for our top pick" reflex. The displayed probability travels
  with its row — shuffle the rows, never the numbers.

Also log `entry_mode` per pick (`shortcut` | `typed` | `pasted`), so shortcut-entered picks can be tested
for systematically different behaviour rather than argued about. Same field as Mock Lab.

Component: `design_system/components/data-row.dc.html#typeahead`.

## Row grid
`display:flex; gap:7px; padding:6px 10px 6px 12px`

| Cell | Width | Font | Notes |
|---|---|---|---|
| rank | 20px, right | num | dim2 |
| name | flex, min 52px | ui 600 13px | ellipsis |
| POS | 30px | **ui**, letter-spacing .045em, 600 | position colour — it is a label, not a measurement |
| TM | 22px | **ui**, letter-spacing .045em, 10px | dim2 |
| delta + `why` | 24px, right | num 10px 600 | up/down colour; carries the derivation toggle |
| base→live | 58px, right | num | baseline 9.5px dim2 · arrow 7.5px · live 11.5px 600 coloured |
| mark taken | auto | — | ✕, 1px border, radius 6px |

Pane must carry `min-width:0; overflow:hidden` or these intrinsically-sized cells paint outside it.

## The two-number availability cell
Never one number. `34%` `→` `28%` where baseline is quiet and live is loud. States:
- **live computed** — `33%→41%`, live coloured by band (`>=.6` acc, `>=.25` down, else dim2)
- **thin signal** — same, arrow tinted `--down`
- **not computed** (fewer than `max(4, teams/2)` picks logged) — live renders `·`, never the baseline again
- **stale sim** — both cells `—`

Tooltip carries the full derivation: baseline + range, live + thin flag, `need` and `run` adjustments separately, and the run context (`3 of last 5 at WR`).

## Inline rank derivation
The `why` toggle on the delta cell expands **inside the row container** (not a modal): headline
(`Your format moves him up 2 slots — market 14, ours 12`), one sentence of why, then three cards —
replacement level, roster shape, kicker — each with value and backing field. One row open at a time
(`state.bexp`).

This is the product's strongest differentiator. It was two clicks deep; it must be one interaction.

## Tier grouping
Rows are grouped by tier with a header carrying a surface lift and the count. No zebra striping.
Drop rules between rows within a tier if you want the tier to read as the unit.

---
## The four constraints (they override any styling instinct)
1. Every number traces to a named backend field. 2. An explicit null is a real state — `0%`, `0`, `—` and "not computed" are four different claims. 3. Never show a part-applied recompute. 4. Density is the product; premium means better organised, not roomier.
