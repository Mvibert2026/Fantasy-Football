---
ID: FR-2026-07-30-four-selectable-ranking-sources
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGHEST — an architecture requirement, not a feature
NEEDS: backend (contract), then frontend (toggle), then librarian (assistant)
---

## Request

> "The draft board should be able to be fully functional off of consensus or my own rankings. All
> features. Toggle able.
>
> From me I'd like 3 rankings. Proprietary bottom up, consensus adjusted, consensus and ADP. App
> should run based on any at user toggle.
>
> And all of this information and inference you're doing needs to be available in chat bot."

## This resolves the §4 tension rather than violating it

**PM raised this exact conflict to him earlier today and it was the open escalation from PR-004 §11.3:**
`CLAUDE.md` §4 says ranking sources stay **separate, never blended**, so the model's independent view
is always visible against consensus — while his stated product shape, "consensus adjusted by
bottom-up", is a blend.

**His answer resolves it, and in §4's favour.** He is not asking for one merged number. He is asking
for **four separate, named, selectable sources, side by side**, with the user choosing which drives
the app. The independent view stays visible against consensus at all times — which is precisely what
§4 exists to protect. "Consensus adjusted" is a distinct artifact under its own name, not a
contamination of the proprietary one.

**The schema already anticipated this.** `ranking_source` is an enum with exactly four values —
`proprietary` / `expert` / `league_adp` / `market_adp`. His four map onto it directly. This was
designed for on day one and never wired.

## The four sources

| Founder's name | `ranking_source` | State today |
|---|---|---|
| Proprietary bottom-up | `proprietary` | **Does not exist.** Component models measured worse than the incumbent at all four positions (2026-07-30) |
| Consensus adjusted | `expert` (re-scored) | **This is what ships today** — consensus re-scored into league value structure. Within-position identical to consensus; deviation is cross-positional only |
| Consensus | `expert` (raw) | In the DB — `fantasypros_csv_2026draft`, 554 rows, `as_of` 2026-07-30 |
| ADP | `market_adp` | In the DB — FFC half-PPR 10-team plus MFL proxy, both current |

**Ambiguity flagged, not silently resolved:** he says "3 rankings" then names four things. Building
all four as separate selectable sources is the safe superset — if he meant three, one is simply never
selected. Worth confirming, not worth blocking on.

## "All features" is the hard part, and it is the point

Every consumer must run off the selected source, not just the board:

- The board's ordering, VBD and tiers
- **Availability** — `simulate_availability` currently hardcodes `fantasypros_ecr` for both the
  opponent model *and* the user's own BPA pick (thread 119). Two sources disagree on 73 of the top 80
  players, so this is not cosmetic
- **The recommender** — its `g` term is value over the realistic fallback, which is a ranking output
- Predictions, opponents, the grid, the assistant's answers

**Anything that silently keeps using a different source than the toggle says is the exact class of
defect the founder caught this morning** — a surface asserting something the code does not do.

## The chatbot half

Already underway: `docs/assistant-context.md` now carries 11 curated entries with number, interval,
effective n and scope inline, and a thread is open to `frontend` to confirm the retrieval layer
surfaces them. **This request extends it** — the assistant must also know *which source is selected*
and answer accordingly, or it will explain a board the user is not looking at.
