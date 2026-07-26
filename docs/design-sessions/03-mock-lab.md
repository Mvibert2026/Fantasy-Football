You produce the design system and screen specs for a fantasy football draft assistant. You cannot
see the code repository, so assume nothing about what is currently built. Everything you need is in
this message.

Your Settings editor handoff was received and committed. The sixth state you added
(`04-ready-to-apply`) was the right call and is now the reference the engineers build against — the
reasoning that an engineer who doesn't see that state will auto-apply on completion was correct. Your
four flagged decisions are logged and awaiting the founder; your three engineering questions have gone
to the backend engineer.

This session is a new screen.

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
THIS SESSION — the Mock Lab
═══════════════════════════════════════════════════════════════════════════════

## Why this screen matters more than it looks

The product's central claim is **calibrated availability** — when it says a player has a 33% chance
of surviving to your next pick, that should happen about a third of the time. Validating that claim
requires roughly **30 logged practice drafts**. There is currently **one**.

So this screen is not a nice-to-have analytics view. It is the mechanism by which the product's
core claim becomes true. If logging a mock is tedious, the user stops after three, the claim stays
unvalidated, and the differentiator never materialises. **The tedium is the design problem.**

## What it is

Three connected things:

**1. Logging a mock draft.** The user runs a practice draft elsewhere — on a public mock site or in
their league's platform — and records it here. Roughly 160 picks across 16 rounds and 10 teams. Each
pick needs a player and a team slot.

Design for the realistic case: a person entering picks either live as the mock happens, or afterwards
from a results screen. Both should be fast. Consider what the fastest possible entry actually looks
like — type-ahead, keyboard-only flow, bulk paste, something else. **160 entries is a lot, and every
extra interaction per pick multiplies by 160.** That arithmetic should drive the design.

**2. Prediction versus actual, per pick.** Before each pick, the model had a view: who it expected to
go, and what survival probability it assigned to the players on the board. Show that against what
actually happened.

**Hard constraint:** predictions are shown **as they were made**. Never retroactively corrected,
never quietly recomputed with hindsight. A prediction the model got wrong is the most valuable thing
on this screen, and hiding it would break the product's entire premise.

**3. The calibration summary, after the draft.** This is the hardest part.

The technical measure is a Brier score, which means nothing to almost anyone. The claim the user
actually cares about is: *"when this thing says 33%, does it happen about a third of the time?"*
Communicate that **visually rather than numerically**. Buckets, dot arrays, something else — your
call, but the reader should be able to see at a glance where the model is honest and where it is
over- or under-confident, without knowing what calibration means.

The product already uses a 10-dot frequency array elsewhere to express probability honestly. Reuse or
extend that language if it fits; don't invent a second visual idiom for the same idea.

## States to cover

At minimum: empty (no mocks logged yet — and note the user has exactly one, so the near-empty case is
the real one), logging in progress, a completed mock's pick-by-pick review, the calibration summary,
and the aggregate view across several mocks. Add any state you think is missing — you were right last
time.

Also design the **progress-toward-30** affordance. The user needs to feel movement toward a target
that is otherwise a long grind. Be careful not to make it feel like homework.

## Deliverables

Same as Settings: a markdown spec, one reference HTML per state opening directly in that state, a 2×
PNG beside each, tokens JSON for anything new, and HANDOFF-NOTES.

Flag decisions rather than making them, and separate them clearly into ones for the founder (product
judgement) and ones for the backend engineer (facts about the system you had to assume). That split
worked well last time.

Keep the spec tight and structured. The Draft spec ran to 38,000 characters and the engineer porting
it ran out of budget before finishing and misreported what was done. Shorter specs get followed.
