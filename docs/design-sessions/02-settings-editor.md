You produce the design system and screen specs for a fantasy football draft assistant. You cannot
see the code repository, so assume nothing about what is currently built. Everything you need is in
this message.

Your previous handoff (four Draft screens: board, opponents, predictions, player detail) has been
received and committed. This session is a new screen.

═══════════════════════════════════════════════════════════════════════════════
STANDING CONTEXT — applies to everything you design for this product
═══════════════════════════════════════════════════════════════════════════════

## Four hard constraints. Architecture, not style preferences.

1. **Every number on screen traces to a named backend field.** No decorative or illustrative
   numbers. If you draw a value, a real field is behind it.
2. **An explicit null is a real state.** `0%`, `0`, `—`, and "not computed" are four different
   claims and must never substitute for one another. Null states are a first-class part of this
   product, not an error case.
3. **Never show a part-applied recompute.** While a recompute is in flight, every displayed number
   holds its pre-edit value. A half-updated board is worse than an old one.
4. **Density is the product.** Do not add whitespace or raise font sizes to modernise. ESPN's 2025
   redesign is the cautionary tale — they spent it on air and imagery, and users experienced it as
   losing information per screen. Premium here means better organised, not roomier.

## Type — two roles only

- `--f-ui` IBM Plex Sans — names, prose, nav, buttons, labels
- `--f-num` IBM Plex Mono — numeric cells only, `tabular-nums` scoped to the cell

Position and team codes (WR1, LV, BUF) are **labels**, not measurements: sans at small size with
letter-spacing, never mono.

## Colour and shape

Dark: bg `#0a0d12` · panel `#0f131a` · panel2 `#151a23` · line `#222937` · line2 `#2e3646` ·
txt `#e7ecf3` · dim `#8b95a7` · dim2 `#5b6474` · up `#4cc9f0` · down `#f0a35e` · acc `#7dd3a0` ·
live `#ff5f56` · QB `#b39ddb` · RB `#4dd0b1` · WR `#f2a65a` · TE `#6fa8ff` · DEF `#94a0b0`

Light theme is its own design, not an inversion — elevation rises toward white, accents need higher
chroma because light backgrounds swallow desaturated colour.

Radius 4–6px on chrome, **zero on data cells and table rows**, 10–12px on modals only. No gradients
or shadows except a side-panel drop shadow. **Colour never carries meaning alone** — every
colour-carried signal needs a redundant non-colour cue. Colourblind-safety requirement, not a nicety.

═══════════════════════════════════════════════════════════════════════════════
THIS SESSION — the Settings editor
═══════════════════════════════════════════════════════════════════════════════

## What it is

The screen where a user edits their league's roster shape and scoring rules. It is entirely unbuilt
and entirely unspecified, and it is the screen most likely to be designed wrong if left late —
because its hard problem is temporal, not visual.

## The hard problem

A scoring change invalidates essentially every number in the product. Player values are computed
against this league's specific rules, so changing "reception = 0.5" to "reception = 1.0" changes
every projection, every replacement level, every ranking, and every availability probability.

Recomputing takes **roughly 60 seconds**.

Principle #3 forbids showing any partially-updated number during that window. So the design has to
answer: what is the user looking at for those 60 seconds, and how do they know what is safe to trust?

Roster changes (adding a bench slot, changing flex eligibility) are cheaper but still invalidate
replacement levels — a lighter version of the same problem, and worth distinguishing.

## What to spec

**Editing surface.** Roster slots (starters by position, bench count, IR, flex eligibility) and
scoring rules (points per reception, passing/rushing/receiving TD values, interception penalty,
yardage bonus thresholds). Dense, scannable, editable in place. Reference format: 10 teams, 0.5 PPR,
QB/RB/RB/WR/WR/WR/TE/FLEX/FLEX/DEF, 6 bench, 1 IR, yardage bonuses at 100/150/200 yards.

**Pending-change state.** Edits do not apply immediately. Show what has changed and what it will
cost before the user commits — a diff of old value versus new, and an honest statement of impact
("this will recompute 378 player values, about 60 seconds").

**The blocking behaviour.** During recompute, specify precisely what the user sees. Options worth
considering, and pick one with reasoning: freeze the whole app behind a modal; let them navigate but
show every affected number in a visibly-stale treatment; or something else. Whichever you choose,
Principle #3 means no number may quietly show a new value while others show old ones.

**Progress feedback.** The backend can emit a stage name plus percent complete. Design what that
looks like — a 60-second wait with no signal reads as a crash.

**Staleness marking.** After a change, availability data specifically is stale until recomputed.
Design how a stale number is distinguished from a fresh one and from a null. Three states, three
distinct treatments, and remember colour alone cannot carry it.

**Failure.** A recompute that fails partway. The user must know nothing was applied, or exactly what
was, and be able to get back to a known-good state.

## Deliverables

Same format as the Draft screens: a markdown spec, reference HTML, and any new tokens as JSON.
Keep the spec tight and structured — the last one ran to 38,000 characters and the engineer porting
it ran out of budget before finishing and misreported what was done. Shorter specs get followed.

If a decision genuinely needs the founder rather than you, mark it clearly in the spec rather than
picking silently.
