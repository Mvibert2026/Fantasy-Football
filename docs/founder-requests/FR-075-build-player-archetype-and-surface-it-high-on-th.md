---
ID: FR-075
STATUS: IN PROGRESS
SOURCE: chat 2026-07-30, PM session (feedback batch)
RAISED: 2026-07-30
---

## Request
Build player archetype and surface it high on the card

Founder's own words:

> "We need to get archetype built and I'd like to see it towards the top of the card (or inprep
> there is space next to the napes to the right before position comes into play"

## Why it matters

## Initial read
<Not the founder's own words -- PM's read on scope, constraints, sequencing.>

## Resolution (2026-07-30, frontend)

The card was actively lying: `PlayerDetail.tsx` rendered "Not computed: archetype. No backend field
in this build" for every player, unconditionally, and commented that the field was "permanently
absent, no field in any export, ever." False -- `data/export/player_descriptions.json` carries a real
per-player `archetype` field (ADR-044), the app already loads it into `Dataset.playerDescriptions`,
and the assistant already reads it (`docs/ranking/archetypes-proposal.md` SS0, `researcher`,
same day). This was a wiring/wording defect, not a missing capability.

**Fixed the false claim and surfaced what exists**, per this session's dispatch (not waiting on the
taxonomy revision, which is separate, unbuilt work -- see the open thread to `design`/`ranker`):

- New `ui/data/archetype.ts`: the join (`archetypeFor`), a display label that strips the redundant
  position prefix (`archetypeLabel`), and a **live-computed** same-position/same-label share stat
  (`archetypeShareOfPosition`) -- never a hardcoded percentage, so the catch-all-bucket problem
  (measured this session: RB_COMMITTEE 62.7% of RBs, TE_SECONDARY_RECEIVER 51.0%, WR_ROTATIONAL
  41.4%) stays visible and can never go stale.
- **Placement:** the founder's own "or" -- built the card placement (identity strip, next to the
  name, before position) per his literal request; the Board-row placement is still open, flagged to
  `design`.
- **Four honest states**, never collapsed: a real label with confidence + description + live share
  stat; `UNCLASSIFIED` (measured, met no threshold); `ARCHETYPE N/A` (position not covered --
  taxonomy is RB/WR/TE only); `ARCHETYPE —` (this league has no `player_descriptions.json` export at
  all, e.g. every non-primary league today).
- A fixed caveat: "Describes last season's usage, not a 2026 projection... never feeds the ranking
  model" -- matches the taxonomy proposal's own recommended wording fix.

Commit `b399109`. Tests: `ui/__tests__/archetype.test.ts` (9), `ui/__tests__/player-detail-
archetype.test.tsx` (5) -- against the real committed export, not a hand-written fixture, including a
regression guard that the old false-claim string never renders again for any player.
Screenshots (looked at directly): `frontend/e2e/artifacts/fr075-archetype-card.png`,
`fr075-archetype-section.png`.

**Not built, logged for `design`/`ranker`:** the Board-row placement, the revised taxonomy itself
(`docs/ranking/archetypes-proposal.md`, gated on thread 099 to `ranker`), and a formal design spec for
this exact fix (open, unallocated thread `NEW-how-the-archetype-label-surfaces-on-the-player-card-
fr-075.md`, `TO: design` -- replied with the ad hoc calls made this session for design to confirm or
override).
