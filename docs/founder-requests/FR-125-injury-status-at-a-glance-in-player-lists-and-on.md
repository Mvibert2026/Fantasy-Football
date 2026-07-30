---
ID: FR-125
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
NEEDS: data-ops (ingestion) before any UI
---

## Request

Founder's own words:

> "injury status should show in lists of players and in player card, if no injury, it should show
> healthy - needs to be easy to see at a glance - this includes suspension or IR, or PUP etc  but
> all the regular status as well"

## Why it matters

He described it as a display item. **It is not — the data does not exist.** That is the finding, and
it is the whole reason this needs an FR rather than a one-line dispatch.

Measured against the shipping export, `data/export/board.json`, all 510 players:

| `roster_status` value | Count |
|---|---|
| `active` | 402 |
| `unknown_no_contract_data` | 72 |
| `no_active_contract_on_file` | 36 |

| `suspension_flag` | Count |
|---|---|
| `False` | 510 |

**There is no injury status in the export at any granularity.** No IR, no PUP, no NFI, no
questionable / doubtful / out. `roster_status` is a *contract* field — whether the player is under
contract — which is a different question wearing a similar name, and would be actively misleading if
rendered as health. `suspension_flag` is uniformly false, which is a plausible reading for the
current date but is not evidence that suspensions are tracked.

So the honest state today is: the app cannot say a player is healthy, because it does not know.

## Initial read

**Building the UI first would produce exactly the defect this project refuses.** His "if no injury,
it should show healthy" is the dangerous half of the request — rendering `HEALTHY` from the absence
of an injury field is fabricating a value from missing data, which `CLAUDE.md` §1 and the never-
fabricate rule prohibit outright. **Absence of an injury record is not evidence of health.** Until
ingestion exists, the correct render is that status is not tracked, stated in place with the reason.
That distinction must be built in from the start.

**Two threads already cover the ingestion half and both are open and unworked:**

- **070** — recurring injury / suspension feed. `TO: pm`, OPEN 3 days. Blocks *"T4 suspensions and
  roster-status table stakes"* and `E[games_played]`.
- **097** — ingest nflverse weekly roster status. `TO: ranker`, OPEN. Named as *"the only source"*
  for the season-ending-IR and suspension error classes in the bottom-up component model.

Thread 097 is the concrete one: nflverse's weekly roster data carries status codes, it is already a
dependency this project uses, it is free and its licensing is settled. **That is the cheapest path
to a real answer and it is already written up.** This FR should not spawn a third parallel effort —
it should raise the priority of 097 and give it a consumer, which is what it has lacked.

**Once the data exists, the display half is genuinely small and folds into work already specified:**

- **In lists** — `RANKINGS-PANE.md` defines a strict column drop order for width. A status indicator
  has to enter that order explicitly, and it must drop *before* the player's name, which never drops.
- **On the card** — `PLAYER-PROFILE.md` §1 puts identity first. Status belongs in the identity strip,
  which is the same contested line the archetype chip wanted and could not have. Design should rule
  on whether both fit, given that the archetype chip is absent on 57.8% of players and status would
  be present on all of them — arguably the stronger claim on that space.

**Sequencing:** ingestion (097) → export field + contract bump → design ruling on the strip →
frontend. Not a fold-in to current work. Do not build the UI against `roster_status`.
