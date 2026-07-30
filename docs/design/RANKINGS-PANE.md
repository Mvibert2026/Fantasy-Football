---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 6 of 8
DATE: 2026-07-31
COVERS: founder ask "parts feel old… rankings on the left may need to be a wider pane" + the column-alignment regression
---

# The rankings pane — width, look, alignment

Three separable things. The width one is not a preference.

## 1 · Width — at 1180 the pane drops the player's name

From the two captures of the same screen:

- **1500w** — names truncate to about seven characters: `Bijan …`, `Ja'Mar…`, `Jahmy…`
- **1180w** — **there is no PLAYER column at all.** The header row reads
  `RANK POS TM ADP Δ VBD AVAIL` and each row's only identity is its positional rank: `24 · RB10 · LAC`

**He cannot tell who `RB10` is, on the screen he stares at for the entire draft, where a misread
costs a pick.** So the answer to "may need to be wider" is yes — and more than that:

### The name is the one column that never drops

When width runs out, columns leave in a fixed order:

    availability dots  →  TM  →  ADP range  →  vs your options  →  Δ  →  [PLAYER never]

## 2 · What reads dated — four named things, not a vibe

| | |
|---|---|
| **dot strings** | `●●●●●●●○○○` beside the percentage it already states. Two encodings of one number, on 511 rows. The loudest dated thing on the screen and the cheapest to remove. |
| **superscript MFL** | Stamped on every ADP value. One fact about the whole column, repeated 511 times, in the smallest type on screen. It belongs in the header — as `ADP-COLUMN-AND-CAPTURES.md` already specified. |
| **9px mono labels** | Mono on POS, TM and the headers reads as a terminal dump. Mono is for numbers; labels are `--f-ui`. `tokens.css` opens by saying so. |
| **per-row icons** | `☆` and `×` on every row, always. Reveal on hover or focus; the row is not a toolbar. |

**None of these is a font choice.** All four are the same mistake — *a fact repeated on 511 rows that
belongs once in a header* — and removing them is what buys the name column its width. That is why
look-and-feel and width are one fix here even though they were asked as two questions.

## 3 · Alignment — the regression is structural, so the fix is structural

It has been fixed once and come back. That is the signature of **two definitions of the same geometry
drifting apart**, not one bad number. Per the founder's own constraint, as a rule:

> **The header row and the data rows are children of one grid, with one column definition. A layout
> that states its columns twice is rejected regardless of whether it currently lines up.**

This also makes the drop order implementable in one place: columns disappear from the single
definition and the header follows automatically, because it cannot do anything else.
