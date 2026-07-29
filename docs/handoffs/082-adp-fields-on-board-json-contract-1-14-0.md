---
ID: 082
FROM: backend
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask
Per the founder's request ("ADP should be shown on both the prep and draft screens as well as
player profile"), `board.json` player rows now carry real ADP fields (`CONTRACT_VERSION` 1.13.0 ->
1.14.0, already committed at `3690217`, artifact regeneration/version-test fixes at `c6b45be`):

- `players[].adp` — average pick from the most recent MFL-proxy snapshot, or `null`
- `players[].adp_min_pick` / `players[].adp_max_pick` — the observed range, or `null`
- `players[].adp_selected_pct` — % of sampled drafts the player was taken in, or `null`
- `players[].adp_source` — always `"mfl_proxy"` when `adp` is non-null, always `null` when it
  isn't. **Must travel with the value everywhere it's displayed** — never render a bare "ADP"
  number without this label, and never merge/average it with any other ADP source you add later
  (e.g. the FFC ingester landed the same day, `adp_source` values `ffc_*_10team` — those are a
  SEPARATE, not-yet-wired source; do not blend the two into one figure client-side).
- Top level: `adp_source`, `adp_as_of_date` (snapshot date, for "N days old" display),
  `adp_source_note` (full proxy caveat — population is whoever drafts on MFL, not this league;
  full-PPR capture (`IS_PPR=1`) approximating this half-PPR league, so receivers likely read a few
  picks earlier than this league would actually take them), `adp_match_rate_note`.

**Note there is a real numbering collision risk flagged by PM**: an untracked thread on the
founder's own machine independently proposed a 1.14.0 bump for a different field (a
consensus-input-source field), invisible from any cloud session. If you find `board.json` or
`CONTRACT_VERSION` disagreeing with what's described here, that's why — reconcile against
whichever is actually on `main`, don't assume this thread's version is final.

## Why
`adp_snapshots` has been captured daily since 2026-07-26 (ADR-035) and nothing has ever displayed
it. The founder asked for it on three screens (prep, draft, player profile); this closes the
backend half of that ask.

## Done looks like
Backend side is done: `src/export_contract.py::_load_adp_snapshot` (join gsis -> `player_ids` ->
`mfl_id`, latest snapshot only, never blends across `adp_source`), 5 new unit tests plus 1
board-level integration test in `tests/test_export_contract.py`, `tests/test_rosters_export.py`
version-bump test updated. Measured on the real rebuilt DB: 144 of 510 board rows (28.2%) carry a
real ADP value, 366 honest nulls (MFL only covers roughly the top ~230 players in a 10-team pull),
147 of 225 `mfl_proxy` rows resolved a gsis id via the identity join. Snapshot `as_of_date`:
2026-07-29.

Closes when the three screens (prep, draft, player profile) render `adp`/`adp_source`/
`adp_as_of_date` with the proxy caveat visible somewhere reachable from each screen (a tooltip or
info affordance is fine — it doesn't need to be inline on every row), and honest "no ADP data"
states for the null case. Reply here with commit hash + screenshot when done.
