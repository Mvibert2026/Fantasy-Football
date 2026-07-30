---
FROM: design
TO: pm, frontend
STATUS: RESOLVED — grid is unblocked
PRIORITY: 1 (round two)
DATE: 2026-07-30
COVERS: FR-044
---

# The position-colour collision — resolved

## The decision

**No position hue changes. The two colour families are separated by role and shape instead, and the
semantic family is banned from the grid outright.**

Engineering can build the periodic table against this.

## The reason, corrected after seeing the FantasyPros captures

My first pass said our palette already *was* the category convention, reasoning from the written
record, which described Yahoo only. **That is wrong, and the correction is the more useful finding:**

| Source | QB | RB | WR | TE | DEF | Provenance |
|---|---|---|---|---|---|---|
| **Ours** | `#9d93c4` | `#63b39b` | `#c39468` | `#7d9fcf` | `#8b939f` | `tokens.css`, verbatim |
| **Yahoo** | not described | *"green"* | *"orange"* | not described | not described | FR-053 prose only — **no hex, not sampled** |
| **FantasyPros** | not shown | `#83dcef` | `#85dd9e` | not shown | not shown | **Sampled** from the capture (see below) |

**Only two of the three rows carry hex values, and that asymmetry is deliberate.**

- **FantasyPros' two are measured**, not judged by eye: the pill fills were read with a canvas from
  `pasted-…127622.png` — WR at (611–650, 362–378) in the suggestion card, RB at (1709–1738, 310–325)
  in the picks rail. Both are light pills with dark navy text, confirmed by zooming the crop.
- **Yahoo's row has no hex because nobody has sampled it.** FR-053 records the words "orange WR,
  green RB" from observation, and the two Yahoo PNGs in the repo show the rankings selector and the
  roster categories — not the coloured board. Their other three positions were never described at
  all. Publishing a swatch for any of that would be inventing a value.

**The comparison survives the gap**, because the argument only needs the two words FR-053 does
record: Yahoo puts **green on RB**, FantasyPros puts **green on WR**. That is the disagreement and it
holds without a hex.

**The two leading products disagree about the same five positions.** FantasyPros badges WR green and
RB blue — visible on every rankings row, every suggestion card and every pick in the right rail.
Yahoo badges WR orange and RB green.

Note how far apart the two green claims are: FantasyPros' WR green is `#85dd9e`, a light mint pill
fill. Ours is `#63b39b` on RB, as text. Even where two products "both use green" they are not using
the same green for the same thing.

So FR-044's instruction to *follow the convention* cannot be executed as written: matching one means
diverging from the other, and the founder prefers the product whose palette is further from ours.

**This removes the constraint I thought was binding, and it does not change the decision — it
improves the reason for it.** With no convention to match, the only real constraints are internal:
the accent collision, legibility, and colour-blind safety. Our hues satisfy the last two and are
already shipped in both themes. Changing them buys nothing and costs a retrofit across every screen.

The only thing all three palettes agree on is that **positions get distinct hues at all.** That is
the actual convention, and we already follow it.

## The collision, and why hue cannot resolve it

    --rb #63b39b   vs  --acc  #5ecf9e     (both green)
    --wr #c39468   vs  --down #f0993f     (both orange)
    --te #7d9fcf   vs  --up   #5bb4f2     (both blue)

Three of five positions sit on the three semantic accents. Both families are individually correct —
the accents are the delta colours, the positions are distinct-per-position. Neither can move. So the
separation is by **role**, not hue.

| Family | Where it may appear |
|---|---|
| **position** | Only on a position code, a cell tint, or a cell's left edge. Always adjacent to the letters it names, so it is self-labelling. |
| **semantic** | Only on a signed delta — arrow plus number. Never on a label, never on a fill. |
| **never both** | No element carries a hue from both families. Shape keeps them apart: positions are letters, deltas are arrows and digits. |
| **in the grid** | The semantic family is **banned outright**. Depletion is carried by luminance, strikethrough and a dot — never by hue. |

## Worth taking from their treatment

FantasyPros puts the hue in a **filled pill wrapped around the position letters**, so the colour and
the word it means are one object. That is why their palette survives being arbitrary.

**Adopt for the grid cell**, where the hue does the most work. **Do not retrofit onto the board** — a
filled pill on all 511 rows would out-shout the player names.

## The residual risk, named

A user who has learned green-is-good from the board carries that association *into* the grid.
Banning the accents removes the competing signal, not the learned one. Three things hold it down:

1. The tint is low (~13%), so it reads as a category band rather than a verdict.
2. Hue is always adjacent to the letters naming it — the filled pill above.
3. **Every hue appears on good and bad players alike within one screenful.** The grid is sorted by
   draft order, so the top rows are green and orange and blue together. No hue can correlate with
   quality for long.

The third is the real defence, and it is structural rather than a matter of taste.

## The text label, unchanged from round one

`--f-ui` always — never mono. **Dense label** (grid cells, table rows, chips, scarcity rows): 10px
floor, semibold. **Inline annotation** following a player name at display size: 11px, regular.
The distinction is whether the code is the only thing identifying the position.
