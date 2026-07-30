---
ID: FR-083
STATUS: NEW
STATUS: IN PROGRESS
SOURCE: chat 2026-07-30, PM session (feedback batch)
RAISED: 2026-07-30
---

## Request
Player card ADP does not match the selected league's format

Founder's own words:

> "Why do player notes cards not show adp for the correct format for the league selected?"

## Why it matters

## Initial read
<Not the founder's own words -- PM's read on scope, constraints, sequencing.>

## Resolution (2026-07-30, frontend)

**Not a frontend propagation bug — checked directly, not assumed.** `ui/data/board.ts::buildRows`
reads `row.adp`/`adpSource` straight off the currently-loaded `data.board.players[i]`, no caching
across a league switch; `loadDataset(leagueId)` already re-fetches the full per-league dataset on
every switch. The seam the task brief expected to find (league selection stopping partway through
the app) does not exist here.

**Real cause, traced to `src/export_contract.py`:** `_load_adp_snapshot(conn)`
(`export_contract.py:279`) takes no `cfg` argument and always uses `adp_source='mfl_proxy'` —
identical for every league, including Westwood's own. Worse: the note text explaining this
(`adp_source_note`, `export_contract.py:531-547`) is hand-written prose asserting "this league
scores half-PPR," which is only true for Westwood — reproduced live this session against
`espn_10_standard` (a real STANDARD/0-PPR league per FR-042), which carries that exact sentence
unchanged and false.

This is a genuine backend defect, not something to patch from the frontend by rewriting or
suppressing backend-authored text (that would mean frontend second-guessing backend content, its
own kind of dishonesty). Instead: added `league.json:scoring_ruleset_note` — which DOES vary
correctly per league (contract 1.15.0, ADR-062) — as a second, adjacent disclosure right next to
the ADP block, so a reader can see the two don't necessarily describe the same league. Screenshot
proving the contradiction is now visible rather than silent:
`frontend/e2e/artifacts/fr083-player-card-standard-league-adp-block.png` (STANDARD league: the
backend note says "half-PPR," the new line right below it says "STANDARD ruleset (FR-042)... no
stacking yardage bonuses").

Backend fix logged: `docs/handoffs/NEW-adp-and-history-not-league-scoring-aware.md` (pending PM's
ID allocation). `npx tsc -b --noEmit` clean. Test count/commit: see session report in
`docs/status/`.
