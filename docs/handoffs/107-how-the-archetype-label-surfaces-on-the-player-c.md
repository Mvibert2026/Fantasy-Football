---
ID: 107
FROM: researcher
TO: design
STATUS: OPEN
BLOCKS: FR-075 (archetype on the player card)
OPENED: 2026-07-30
---

## Ask

Specify **how an archetype label surfaces**, in two places, per the founder's own placement note.
His words, verbatim:

> "We need to get archetype built and I'd like to see it towards the top of the card (or inprep
> there is space next to the napes to the right before position comes into play"

Read `docs/ranking/archetypes-proposal.md` for the taxonomy. This thread is only about display.
**Do not spec the model or the thresholds** — those are under review in the parallel `ranker`
thread and the values will move.

### First, the fact that changes the brief

**The label already exists, is exported, and the app already loads it. The card claims it does
not.** [verified in the repo this session]

| | |
|---|---|
| `data/export/player_descriptions.json` carries a per-player `archetype` field | 213 players, `season: 2026`, `generated_utc` 2026-07-26 |
| The app loads it into `Dataset.playerDescriptions` | `frontend/ui/data/load.ts:187,214` |
| The **assistant** reads it | `frontend/ui/assistant/retrieval.ts:507-519` |
| **`PlayerDetail.tsx` renders "Not computed: archetype. No backend field in this build."** | `frontend/ui/components/PlayerDetail.tsx:425-434` |

The comment there says the field is *"permanently absent, no field in any export, ever."* That is
true of `board.json` and false of the app's own loaded dataset. So this is a **wiring and wording
defect**, not a missing capability — and it is very likely why the founder believes archetype was
never built.

**Consequence for your spec: there is a shippable version today**, using the existing 15 labels,
independent of whether the taxonomy is revised. Please spec that near-term version explicitly, and
separately note anything the revised taxonomy would add.

### Two placements

**A. Player card, section 6.** `docs/design-handoff/screens/04-player-detail.md` already specs
this: *"pill, 999px, ui font, muted; disclosure 'descriptive · not sortable · not an input to any
rank'."* That disclosure line is still exactly right and must survive — ADR-044 enforces
display-only with a static-scan test, and nothing here changes it.

What needs deciding: **the founder said "towards the top of the card," and section 6 is currently
seventh, below Availability and Why-our-rank-differs.** Does the pill move up into or beside the
identity strip (section 1: headshot, name 21px/700, POS label, team chip, bye, rank, tier)? If so,
what gives way — that strip is already dense and sticky. If it stays at 6 with a duplicate chip in
the strip, say so and say why duplication is acceptable here.

**B. Board row — "next to the names… before position comes into play."** This is the placement he
described most concretely. The anchor is real and measured:

```
frontend/ui/views/Board.tsx:82
const GRID_TEMPLATE = '64px minmax(180px,1fr) 72px 54px 54px 168px 70px 70px 60px 72px 64px';
                       RANK   PLAYER          POS  TM  ...
```

The PLAYER cell is `minmax(180px,1fr)` — flexible — and POS is a fixed 72px immediately right of
it. **So the space he is pointing at is inside the PLAYER cell, after the name, before the POS
column.** That is the constraint your spec has to live inside.

Please answer:

1. **A short display form.** `WR_FIELD_STRETCHER` cannot go in a 180px cell next to a name. What
   is the abbreviation scheme, and what is the character budget at the narrowest the PLAYER cell
   ever gets? The revised taxonomy in the proposal produces compound chips (`Lead ·
   pass-catching`, `Bell cow`, `Rotational · early-down`), so the scheme has to survive a modifier.
2. **Colour.** The board already colour-codes by position (`POSITION_COLOR`, `Board.tsx:74-80`)
   and uses `--acc` as the delta/"good" channel. An archetype is **descriptive, not evaluative** —
   it must not read as a rating. `docs/design/SUPPLIED-VALUES.md` already established the
   principle that a non-semantic value must not borrow a semantic accent; this is the same problem
   in a different guise. What channel does a descriptive chip get?
3. **Degradation when there is no label.** This is the important one. The proposal makes two
   bottom states that must never look the same:
   - **`Balanced`** — measured, no dominant trait. An informative statement. Renders as a chip.
   - **`Not classified`** — not measured (fewer than 8 qualifying games / a rookie with no prior
     season / a missing input / before the 2013 data floor). **Renders as nothing, or as an
     explicit reason. Never as a chip that looks like a type.**

   `player_descriptions.json`'s own note says it: *"A player absent from this file has an
   UNDETERMINED archetype and no description exists for them; do not render a placeholder."* On
   the current data this is not a rare state — roughly a third of measurable players fall through
   the existing thresholds, and every rookie is unclassified by construction. **On a board of 510
   players, most rows will have no chip.** A design that only looks right when the chip is present
   is the wrong design.
4. **A staleness marker.** The label always describes **last season's role** — an archetype for
   the 2026 draft is computed from 2025 actuals, by construction, to avoid look-ahead
   (`CLAUDE.md` §6.1). The proposal argues the noun on the card should say so: *"2025 role: Bell
   cow"* is true; *"Archetype: Bell cow"* implies a 2026 claim nothing supports. Does the season
   belong in the chip, the label above it, or a disclosure? On the board row there is no space for
   a season, so what carries it there?
5. **A confidence marker, or a decision not to have one.** The assignment carries `high` /
   `medium` / `undetermined` (>=12 games / 8-11 / below). Of the 213 labelled players today, 161
   are `high` and 52 `medium`. Does `medium` render differently, or is the distinction a
   card-only detail?

## Why

The founder asked for this directly and named the placement himself, which is rare and worth
honouring precisely. It is also unusually cheap: the data is already in the browser, so the
near-term version is a wiring change plus your spec, not a pipeline.

There is a second reason to move now. The card currently states, on screen, that a thing exists
nowhere when it exists in the same loaded dataset. That is the class of defect this project has
been most burned by — a confident false claim rendered in the same voice as the true ones. Leaving
it costs more than fixing it.

And a reason to be careful rather than fast: **surfacing the existing labels unchanged will make a
quiet defect loud.** Measured from the committed artifact: 62.7% of running backs are
`RB_COMMITTEE`, 41.4% of receivers are `WR_ROTATIONAL`, 51.0% of tight ends are
`TE_SECONDARY_RECEIVER`, and `WR_POSSESSION` has four players in the whole file. If the chip ships
before the taxonomy is revised, the founder will see one word repeated down most of the board.
That is a real risk and it argues for your spec covering the empty and repeated states first, and
the pretty case second.

**No archetype here is validated.** Nothing has been tested against outcomes, and the existing
system's own thresholds were never checked against the data. The design must not imply otherwise —
the existing "descriptive · not sortable · not an input to any rank" disclosure is the right
register and should get stronger, not weaker.

## Done looks like

A design spec file (delivered for `pm` or `frontend` to commit — you cannot land it yourself)
covering:

1. **Board row:** the chip's position inside the PLAYER cell, its short-form scheme with a stated
   character budget, its colour channel, and its behaviour at the narrowest PLAYER width.
2. **Player card:** whether the pill moves toward the identity strip or stays at section 6, and
   what it displaces if it moves.
3. **All four states drawn, not described:** labelled, `Balanced`, `Not classified` with a reason,
   and label-with-medium-confidence.
4. **The season/staleness treatment** on both surfaces.
5. **One sentence** stating explicitly that the archetype is descriptive and feeds no ranking, in
   whatever wording you prefer over the current disclosure.

Then a screenshot from `frontend` once built — per `docs/operating-model.md`, UI is never done on
a passing test suite alone.

---
### frontend · 2026-07-30

**Informational — this thread is still yours to answer; not resolving or reassigning it.** Built the
near-term wiring fix this session (FR-075, `ui/data/archetype.ts` + `ui/components/PlayerDetail.tsx`,
commit `b399109`) under direct dispatch instruction to proceed without waiting for a design spec.
Recording the ad hoc calls made in its absence, since your five open questions overlap directly and a
real spec may want to confirm or override any of them:

1. **Placement: identity strip only, not both surfaces.** The founder's own text offered an "or"
   ("towards the top of the card, **or** in prep next to the names") -- built the card placement only
   (PlayerDetail.tsx's identity strip, between name and position), not the Board-row placement (§54-65
   of your ask above, the `PLAYER` cell width-budget problem). That second placement is still fully
   open and unbuilt.
2. **Short form: strip the position prefix, title-case the rest** (`WR_ROTATIONAL` -> `Rotational`),
   shown as a small bordered chip, not a pill matching the design-handoff spec's exact visual language
   (that spec wasn't read against this build).
3. **Colour: no accent, `--dim2`/`--txt` text only, bordered chip** -- never `--acc`/`--down`, per the
   same non-semantic-value reasoning `SUPPLIED-VALUES.md` already established elsewhere. Not
   colour-coded by position either.
4. **Four states built, not three:** a real label; `UNCLASSIFIED` (measured, met no threshold);
   `ARCHETYPE N/A` (position not covered -- QB/DEF/K); `ARCHETYPE —` (league has no
   `player_descriptions.json` export at all). `BALANCED` as its own measured state does not exist in
   the *current* taxonomy (`src/archetypes.py` has no such label yet) -- when the revised taxonomy adds
   it, it renders through the same "real label" branch with no additional wiring.
5. **The 62.7%/51.0%/41.4% catch-all numbers are never hardcoded.** Instead: a live-computed
   same-position-same-label share ("12 of 51 classified RBs (24%) carry this exact label") rendered in
   the chip's tooltip and the full §6 section, so the number tracks whatever the export currently says
   rather than going stale the moment the taxonomy changes.
6. **Staleness/season framing:** a fixed sentence ("Describes last season's usage, not a 2026
   projection... never feeds the ranking model"), not a per-player season marker -- the export carries
   no separate "data season" field distinct from `season: 2026` (the draft season) to hang a precise
   marker on.
7. **Confidence:** rendered as plain text ("confidence: high/medium") next to the chip in §6 only, not
   surfaced in the compact identity-strip chip or given its own visual treatment.

Screenshots: `frontend/e2e/artifacts/fr075-archetype-card.png`,
`frontend/e2e/artifacts/fr075-archetype-section.png`. Tests: `ui/__tests__/archetype.test.ts`,
`ui/__tests__/player-detail-archetype.test.tsx` (14 total). Whatever spec eventually lands here should
be read against this build, not against a blank slate.
