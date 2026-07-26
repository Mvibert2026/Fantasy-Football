# Screen — Player detail side sheet
**Spec id:** `playerDetail` · **Pinned:** 26 Jul 2026 · **Machine-readable:** `spec/screens.json#playerDetail`, `spec/design-tokens.json`, `spec/formulas.json`
**Assert against:** `spec/acceptance-checks.json`

## Surface
**Right side sheet, 440px, no dark scrim.** `position:fixed; top:0; right:0; bottom:0`, z-index 90,
with a transparent click-catcher at z-index 80. The board and the pick clock must stay visible —
losing sight of them to read a player is a real cost under a clock. This is not a centred modal.

## Order — fixed, and the order is the point
| # | Section | Notes |
|---|---|---|
| 1 | **Identity strip** | headshot (or initials on team colour), name 21px 700, POS label, team chip with colour swatch, bye, our rank in accent, tier. Sticky at the top |
| 2 | **Verdict line** | generated; left accent rule; 14.5px; provenance line beneath |
| 3 | **Projection** | point estimate 26px + "pts", honest range as a **bar with a mid tick**, VBD, plain-language gloss. CI weight sits BELOW the estimate |
| 4 | **Availability at your picks** | baseline → live pair, 10 dots, frequency sentence, band, then `adjustment.need` / `adjustment.run` / run context. Then the 5-pick strip |
| 5 | **Why our rank differs** | consensus / format correction / our rank, then components with fields. Below the numbers |
| 6 | **Archetype** | pill, 999px, ui font, muted; disclosure "descriptive · not sortable · not an input to any rank" |
| 7 | **Weekly finishes** | 18 cells, gradient over finish, **2px bottom rule** on cells below that player's startable line |
| 8 | **Three seasons** | table |
| 9 | **Takeaways** | bullets; flat declaratives for measured history, hedges only for speculation |
| 10 | **Sticky action bar** | `position:sticky; bottom:0`. Mark taken (accent fill) · Add to queue · Watchlist · Compare · Ask |

## The verdict line is generated, never written
Three clauses, fixed order, joined ` · `:
1. **structure** — position within tier and how many remain (`board.position_tier`)
2. **cost of waiting** — live probability with the frequency phrasing (`availability.live_p`)
3. **value over the alternative** — VBD gap to the next player at the position (`board.vbd`)

Example: *"Top of tier 1 at QB, 3 in the tier · 48% to reach your pick at 23 (5 in 10 drafts) · 12 VBD points clear of Jackson, the next QB on the board."*

Null-safe: no projection → "no projection, so this is a rank-and-availability call only"; stale
availability → "availability is stale for this league, so waiting is unpriced". No adjectives, no
ranking language. It must work for all ~378 players with zero hand-written copy.

## Headshot
`profile.headshot_url`, nullable, hotlinked, URL only, never re-hosted (nflverse roster join, ESPN
CDN). **Unpopulated in the prototype** — no sample player has a real ESPN id and we do not invent
them, so every card renders initials on the team colour. Mount the `<img>` only when a URL exists;
a template-interpolated `src` makes the browser fetch the literal placeholder string.

## Sparse players
Consecutive empty sections collapse into **one** line naming everything missing at once:
*"No archetype, notes or news for Brock yet — one season of usage on file, and the news feed isn't
connected. Measured history below is unaffected."* Three stacked empty headers read as broken
rather than candid.

---
## The four constraints (they override any styling instinct)
1. Every number traces to a named backend field. 2. An explicit null is a real state — `0%`, `0`, `—` and "not computed" are four different claims. 3. Never show a part-applied recompute. 4. Density is the product; premium means better organised, not roomier.
