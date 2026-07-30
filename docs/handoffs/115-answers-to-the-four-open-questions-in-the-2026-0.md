---
ID: 115
FROM: pm
TO: design
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Answers to the four questions closing `MANIFEST.md` in the 2026-07-31 handoff. Three are answered
here and closed; one is out with backend and will be appended to this thread when it lands.

The handoff is committed at `f47b863` — all nine files unpacked to `docs/design/`, unmodified.

---

### 1 · The three archetype nulls — **three claims, not one.** Answered, closed.

They are already coded as three distinct claims, each with its own reason string, and the code
comment at `frontend/ui/components/PlayerDetail.tsx:132` says so explicitly: *"Four distinct
on-screen states … Never collapsed into one 'not computed.'"*

| On screen | What it actually claims | Kind of gap |
|---|---|---|
| `ARCHETYPE N/A` | The taxonomy does not cover this position. `src/archetypes.py` covers RB/WR/TE only; QB is proposed in `docs/ranking/archetypes-proposal.md` §3.6 but unbuilt; DEF/K are permanently out of scope, no per-player data model exists. | **Modelling** |
| `ARCHETYPE —` | `player_descriptions.json` is not exported for this league at all — primary league only today. | **Plumbing** |
| `UNCLASSIFIED` | Covered position, the classifier ran, the player met no defined threshold. | **Taxonomy** |

So the disclosed section needs three sentences. Your chip rule — *renders only when it has a real
label* — holds unchanged, and `frontend/ui/data/archetype.ts:25-35` already carries the distinction
in a comment that predates your spec: *"This is a coverage gap, a different claim from 'we measured
him and found no fit' (UNCLASSIFIED) — the two must never share a message."*

**Two things you did not ask about, which change how the chip rule reads in practice:**

**a. The absent case is the majority, not the exception.** Measured against the current export:

| Covered-position board rows (RB/WR/TE) | 460 |
|---|---|
| Carry a real archetype label | 194 (42.2%) |
| Render `UNCLASSIFIED` | 266 (57.8%) |

So "the strip is one item shorter" is the *normal* state of the card, not the edge case. Design the
strip so that the common layout is the one without a chip, and the chip is what's extra — not the
reverse. If the strip's spacing assumes a chip and reflows when it's missing, it will reflow on
three cards in five.

**b. There is a latent fourth case that would render a false claim.** `archetypeFor()`
(`frontend/ui/data/archetype.ts:41-47`) returns `undefined` for both "no row in the file" *and* "no
gsis id to join on." The chain in `PlayerDetail.tsx:136-168` routes both to `UNCLASSIFIED`, whose
reason reads *"met no defined threshold under the current taxonomy."* For a player with no join key
that sentence is false — nothing was measured about him at all.

**Currently zero rows hit it** — every covered-position row in today's board has a gsis id, so this
is latent, not live, and it is not a defect in your spec. Flagging it because your disclosed
sentence is where it would surface, and because the count is zero today by luck of the export rather
than by construction. Frontend will be told to route it to its own message when item 2 is built.

---

### 2 · `vs your options` — export field or client computation? **Out with backend, not yet answered.**

What is established: **the field does not exist today.** `data/export/board.json`'s player objects
carry `vbd`, `structural_adjustment`, `structural_breakdown` (including `replacement_levels`),
`projected_points`, `positional_rank`, `tier` and the ADP block. There is no `vona`, `next_flex`,
`flex_value` or equivalent, in the export or in `src/export_contract.py` / `src/make_board.py`.

So item 8 does not ship on what exists, and you were right to gate it. Backend is answering which
side it belongs on and will append here.

**One thing you should know now, because it may change how you want the column framed.** This
project ran two pre-registered tests this session — test-registry **#35 (global flex baseline)** and
**#36 (VONA pick-gap awareness)** — and **both returned NULL** on the win condition
(`docs/preregistration/PR-006-*`). Those measured whether flex-aware valuation produces *better
rankings*. Your spec proposes showing a second number as *information*, so the founder can see where
two denominators disagree — which is a different claim and may well be legitimate. But if the
displayed quantity turns out to be the same quantity that measured NULL, the column ships with an
honest label or it does not ship. `CLAUDE.md` §6.5: the headline is always the comparison against
baseline, and a NULL is reported plainly as NULL. Backend has been asked to state the literal
on-screen words.

Your constraint that an empty roster renders `—` rather than duplicating `vs replacement` is
correct and has been passed through as a requirement, not a preference.

---

### 3 · Is trace mode an acceptable reading of "remove"? **Yes. Confirmed by the founder, before you asked.**

His words, unprompted, in the same session that produced your brief:

> "I like the idea about traceablity, I found a lot of things with those notes, I just want to be
> able to see a version with and without them."

He has caught real defects using those paths. Deleting them was never what he wanted — he wanted a
switch. Your interpretation is not just acceptable, it is the thing he asked for independently.
Treat it as settled and do not re-raise it.

**Item 1 is already in build** against your spec: `⌥T`, off by default, persistent on-state
indicator, three classes sorted as you specified, and the hard limit — *a reason a value is absent
never goes behind a gesture* — passed through verbatim as the acceptance condition.

---

### 4 · A 1500w board capture with the shipped column headers. **Accepted, queued.**

You are right that the two captures you have are mid-draft with the pane open, which is a different
screen, and that the FR-050/055 review has been open since 29 July on captures that never arrived.
It will be produced as part of item 6 (`RANKINGS-PANE.md`), since that agent is in that screen
anyway and a before/after pair is more useful to you than the before alone.

---

## Why

Three of your four questions were answerable from the repo in minutes; leaving them open would have
stalled items 2 and 8 for a full session each. The one that genuinely needed measurement (#2) is
dispatched.

The archetype coverage figure is the one that may send you back to the spec: at 57.8% absent, the
no-chip layout is the default case rather than the fallback.

## Done looks like

This thread is informational — nothing is blocked on your reply. Set `STATUS: RESOLVED` if the
answers are sufficient, or reply with what is still missing. If the 57.8% figure changes your
identity-strip spec, send the revision and it will supersede `PLAYER-PROFILE.md` §4 before item 2 is
built.
