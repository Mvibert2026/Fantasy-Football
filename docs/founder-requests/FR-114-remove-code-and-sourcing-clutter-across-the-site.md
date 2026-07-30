---
ID: FR-114
STATUS: NEW
SOURCE: chat 2026-07-30, PM session (screenshot feedback)
RAISED: 2026-07-30
---

## Request
Remove the code and sourcing text scattered across the UI

Founder's own words:

> "Generally across the site, can we remove the code and sourcing that's all over, it will give design more room to work with and clean it up."

## Why it matters / PM's read

Screenshot shows the pattern clearly: raw field paths rendered inline as UI text —
`availability.json:by_player`, `board.json:players[].vbd`,
`board.json:players[0].structural_breakdown.replacement_levels`, and a full `model prose over
context: page.draft_state, page.roster_needs, ...` dump in the assistant panel.

**This is provenance machinery leaking into the product surface.** It exists for a good reason —
Principle #1/#2 require every value to trace to a real backend field — but the founder is right that
the *audience* for a field path is a developer, not him mid-draft.

**Do not delete the provenance; relocate it.** The rule that a rendered number must be traceable
stays. What changes is that the trace belongs behind a hover or a disclosure, not inline in the
reading flow. This pairs directly with the founder's hover-over request in the player-profile item.
