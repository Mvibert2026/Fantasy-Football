---
ID: 2026-07-30-four-selectable-ranking-sources-board-contract-s
FROM: backend
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

The founder's architecture request (`docs/founder-requests/FR-2026-07-30-four-selectable-ranking-sources-driving-every-fe.md`):
"The draft board should be able to be fully functional off of consensus or my own rankings. All
features. Toggle able." Backend's half — the export contract — is done. **Yours is the toggle
itself and wiring the app's consumers to read the selected file.**

**Contract bumped `1.17.0` → `1.18.0`.** Update `EXPECTED_CONTRACT` in
`frontend/ui/data/contract.ts:17` to match, or the app's own staleness banner will (correctly)
flag every export as unversioned/stale.

**Four sources, three built, one explicitly not:**

| Founder's name | `ranking_source_selection` | File | Built |
|---|---|---|---|
| Consensus adjusted | `expert_adjusted` | `board.json` (same name as always, unchanged default) | yes |
| Consensus | `expert_raw` | `board.expert_raw.json` | yes |
| ADP | `market_adp` | `board.market_adp.json` | yes |
| Proprietary bottom-up | `proprietary` | none — see `ranking_sources.json` | **no** |

**New file: `ranking_sources.json`** — the picker's source of truth. `{sources: [{
ranking_source_selection, label, built, source_table, as_of_date, row_count, note }, ...four
entries...], board_files: {expert_adjusted: "board.json", expert_raw: "board.expert_raw.json",
market_adp: "board.market_adp.json", proprietary: null}}`. Render `proprietary` in the picker as
disabled/unavailable using its `note` — do not hide it (the founder specifically wants the gap
visible, not silently absent from the UI).

**Every `board*.json` file now carries**, at top level: `ranking_source_selection` (one of the four
enum values), `ranking_source_label` (human string), `ranking_source_built` (bool — always `true`
for the three files above; a client that somehow requests `proprietary`'s absent file should read
this from `ranking_sources.json` instead, never assume `true`), `ranking_source_as_of_date`,
`ranking_source_row_count`, `ranking_source_note`. **Each file's own count/date — never share one
across sources**, per the founder's own words ("a user switching sources is entitled to know what
they switched to").

**All existing per-player fields (`vbd`, `projected_points`, `tier`, `overall_rank`,
`consensus_rank`, `delta_vs_consensus`, `structural_breakdown`, availability, adp display fields
etc.) are present and populated in all three built files** — VBD/tiers/projections are computed
under every selection, so nothing needs a null-check beyond what board.json already required.
The only thing that changes between files is **board order**: `expert_adjusted` orders by our VBD
(unchanged); `expert_raw` and `market_adp` order by that source's own rank — never re-derived from
our VBD (CLAUDE.md §4 never-blend). `overall_rank`/`consensus_rank`/`delta_vs_consensus` all still
reconcile under the same additivity identity board.json has always guaranteed
(`attribution_is_additive`), independently per file.

**`market_adp` coverage is honestly thin** — ~160-170 players vs. ~554 on the expert boards
(FFC's own sampled depth). `ranking_source_row_count`/`ranking_sources.json`'s `note` say so. Do
not pad or extrapolate a market_adp board past its real length; a player absent from it just isn't
in that file.

**Not wired to the toggle in this pass, and why (audit finding, not an oversight):**
`simulate_availability`'s opponent model and the user's own "best available" pick both still run
off a single hardcoded source (`fantasypros_ecr`) regardless of which board is selected — so
`availability.json` and every per-player `availability` block in `board*.json` describe the SAME
draft-behavior simulation no matter which source the user has toggled to. This is a real gap, not
cosmetic (the founder's own words: "the two live sources disagree on 73 of the top 80 players").
It is left unfixed here **because an open, unresolved thread**
(`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md`) is mid-flight on exactly this
code path with an explicit "do not implement the change yet." See ADR-068 for the full reasoning.
**If you build the toggle, surface this honestly** (e.g. availability numbers do not change when
the source is switched) rather than implying they do.

**The recommender's fallback value** (`recommendation.ts`'s `g` term) needs no backend change —
once you request the source-matched board file, it follows automatically; there is no
server-side recommender.

## Why

Backend cannot build the toggle UI or wire predictions/opponents/grid to it — that is squarely
frontend's surface. Without this thread the shape of what backend built is only discoverable by
reading `export_contract.py` cold.

## Done looks like

A reply here stating: which consumers (board, VBD, tiers, recommender fallback, predictions,
opponents, grid, assistant) now read the selected source's file vs. which still silently read
`board.json` regardless of toggle state, plus a screenshot of the picker (including the disabled
`proprietary` option) per this project's UI evidence standard.
