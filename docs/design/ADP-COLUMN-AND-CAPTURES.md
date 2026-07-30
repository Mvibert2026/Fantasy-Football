---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 6 (briefing §12)
DATE: 2026-07-29
COVERS: contract 1.14.0, FR-024, capture list (briefing §6 item 4)
---

# The large-null ADP column, and the capture list

## The column

144 of 511 rows carry a value; **366 are genuinely null.** A reader scrolling past row 230 sees a
column that is empty far more often than not. The glyph is already correct — `—`, per the
vocabulary. What is missing is that **the emptiness must read as expected rather than as a
failure**, and the header is where that costs nothing.

### The header carries both facts

    ADP  mfl · 144/511

- `mfl` is the **proxy caveat at a glance**. It is not this league's ADP and the label never pretends
  otherwise. The population is whoever drafts on MyFantasyLeague, captured at full PPR against a
  half-PPR league.
- `144/511` is the **null population**, so an empty cell is the documented majority case rather than
  a suspected bug.

### The paragraph does not go on the board

`adp_source_note` is written for display and is far too long for a column. It renders **verbatim in
exactly one place** — the player detail sheet, which already does this correctly
(`PlayerDetail.tsx:706`). Everywhere else the header label plus the provenance footer carries it.
**One long caveat, stated fully once, referenced everywhere.**

### One thing to confirm rather than assume

In `adp-draft-room-null-row-2026-07-29.png`, row 33 renders `—` for ADP *and* projection *and* the
frequency array — three absences, one glyph. Here they are the same claim (no data for this player)
so it is defensible, but **a row null for three different reasons must not look like a row null for
one.** Worth a check, not a redesign.

## Capture list, trimmed to surfaces that exist

My earlier list had seven entries; four were Settings and Mock Lab, which do not exist. Six real
surfaces plus the component reference files. Both themes, fixed 1440x900.

| # | Surface | Why this one |
|---|---|---|
| 1 | Prep board | Densest table. Headers, tier bands, ADP nulls, sort state. |
| 2 | Draft room · Board tab | The new middle pane plus the shipped headers and VBD. **No current capture of either exists.** |
| 3 | Draft room · Opponents | Typed name against sourced name — the supplied-value rule. |
| 4 | Draft room · Predictions | The `not yet` column and the calibration banner. Five null claims in one view. |
| 5 | Player detail · ADP present **and** null | The only place the full caveat renders verbatim. Both states. |
| 6 | Glossary / Methodology | Where the inert per-term control lives today. |
| 7 | `docs/design-system/components/*.dc.html` | Cheapest diff in the set — no data dependency, so it cannot fail for a reason unrelated to design. |

### Fail the diff in this order

1. **Any null glyph changing into another.** The five claims are distinct. This is a correctness
   failure, not a visual one, and the one defect class that cannot be cheaply retrofitted.
2. A number appearing where a null belongs, and the reverse.
3. Stale treatment vanishing.
4. Radius appearing on a data row.
5. Ordinary pixel drift **last** — it will be the loudest signal and the least informative.

Baselines: component reference files are design's and regenerate on component change; screen
baselines are frontend's. Per the briefing §2, this split is accepted.
