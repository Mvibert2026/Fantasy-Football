---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 2 of 8
DATE: 2026-07-31
COVERS: card order, density, reading level, the archetype chip
DEPENDS ON: PROVENANCE-DISCLOSURE.md
---

# Player profile — three separate answers

## 1 · Order

The card is opened at one moment: deciding whether to spend *this* pick on *him*. So it is ordered by
that question, not by data structure.

1. **Identity** — name, positional rank, team, bye. Archetype only when it has a real label.
2. **The number** — projected points with its honest range, together. The range is not a footnote.
3. **Both values** — `vs replacement` and `vs your options`, side by side (see `TWO-VALUE-COLUMNS.md`).
4. **Availability** — odds he lasts to your next pick, and who is likely there instead.
5. — *everything above is what a pick is made on; everything below is why to believe it* —
6. **Disclosed** — method, structural breakdown, full ADP caveat, archetype reasoning.

Below the line is **disclosed, not deleted**: one anchored section, reached from the strip, same
gesture pattern as *Why that matters*.

## 2 · Density

The test for a row is **would a different value change my pick.** Three rules, in the order they
remove the most. Applied to the captured card they take out about a third of its height and no fact
with a bearing on a pick leaves the screen.

1. **A row whose every component is zero by construction does not render.** The captured breakdown is
   `±0` against `±0` with seven lines of explanation. It cannot change a pick and it cannot vary. One
   line in the disclosed section covers it: *this board holds no player-level opinion, all movement is
   structural.*
2. **A caveat renders in full exactly once, on the surface that owns it.** The ADP paragraph is about
   a third of the captured card's height. It stays reachable, in one place, behind *Why that matters*.
3. **A timestamp renders at human precision.** `exported 2026-07-29T23:31:48.664540+00:00` becomes
   *data from yesterday 23:31*. Microseconds and a UTC offset are for a log; the full stamp is class 1
   and lives in trace mode.

## 3 · Reading level

Same claim, no statistics vocabulary — and **the warning gets stronger, not softer.**

**Now:** *projected_points comes from E[our_points | position, consensus positional rank]. R-squared
is 0.16–0.27, so consensus rank explains only part of it. Treat projections as weak.*

**Specified:** *Projections follow consensus rank, which explains well under half of what actually
happens. Use them to separate tiers, not to split two players who are close.*

The formula and the R² go to trace mode. "Treat as weak" is advice; "don't split two close players"
is an instruction he can act on under a clock. **Lower reading level does not mean lower stakes.**

## 4 · The archetype chip

Four states: a real label, `UNCLASSIFIED`, `ARCHETYPE N/A`, `ARCHETYPE —`.

The last three are three renderings of an absence, and they may be three *different* absences —
classifier ran and found no class; classifier does not cover this position; no data reached the
classifier. **If they are three claims they need three sentences; if they are one claim they need one
glyph.** Rendering all three as chips in the identity strip is the worst of both: it looks like three
facts about the player and is none.

### The rule

**The chip renders only when it has a real label.**

The identity strip is the most valuable line on the card and is reserved for facts that hold. With no
archetype, the strip is one item shorter and the reason moves to the disclosed method section, in a
sentence, where the three cases can be told apart properly. **An absence is worth one line of prose
in a place he chose to look — never a chip in the place he cannot avoid looking.**

**Open question for whoever owns the classifier:** are those three states three claims or one? The
chip rule holds either way, but the disclosed sentence depends on the answer.
