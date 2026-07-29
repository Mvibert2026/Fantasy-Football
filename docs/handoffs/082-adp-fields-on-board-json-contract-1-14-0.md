---
ID: 082
FROM: backend
TO: frontend
STATUS: RESOLVED
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

---
### frontend · 2026-07-29

**Verified, not built from scratch.** The wiring for all three screens was already sitting in this
worktree as an uncommitted-by-me WIP (`frontend/ui/data/board.ts`, `contract.ts`, `trace-fields.ts`,
`types.ts`, `Board.tsx`, `frontend/ui/components/PlayerDetail.tsx`, `frontend/ui/views/
DraftRoom.tsx` — landed across commits `b6d5a0d`/`75bf095` by a concurrent chain in this same
worktree, per this project's "coordinator commits in-flight work" pattern). This reply is that
work's first screenshot verification — none had been taken. Read every ADP-touching code path
directly (not just the diff) before trusting it.

**All three screens confirmed correct, with real screenshots looked at directly:**

- **Prep board** (`frontend/e2e/artifacts/01-prep-board.png`, `07-prep-board-scrolled.png`) — `ADP
  (MFL)` column, sortable, populated for top-ranked real players (e.g. Bijan Robinson `3.3`).
  Scrolled to the RB tail (rank 492+, e.g. Myles Montgomery): the column reads a plain `—`, visibly
  distinct from every populated numeric cell above it — never a `0`.
- **Draft room** (`frontend/e2e/artifacts/03-draft-room-board-tab.png`,
  `13-draft-room-rb-tab-tiers-dots.png`) — compact `N.NᴹFL` figure inline per row (144 rows
  populated on the real board, confirmed by DOM count), `—` for the null case (Jeremiyah Love,
  RB13, visible in the tiered RB-tab capture), tooltip names the source as "MyFantasyLeague proxy
  ADP, full PPR (not this league's own ADP)".
- **Player profile** (`frontend/e2e/artifacts/02b-player-detail-adp-scrolled.png` for a player
  with data, `08-player-detail-no-adp.png` for one without) — a `MARKET ADP` block quoting
  `board.json:adp_source_note` verbatim in full (the complete proxy caveat: MFL population,
  full-PPR-vs-half-PPR approximation, sample size, coverage limit), avg. pick / range / % of
  sampled drafts when present. The null case reads, verbatim: *"No MFL ADP data for this player --
  MyFantasyLeague's public sample only covers roughly the top ~230 players in a 10-team pull, so
  most of the board genuinely has no market opinion on file. Not a zero, not a rank -- not
  computed."* — exactly the three-way distinction (computed-zero / genuinely-small / not-computed)
  Principle #2 requires, and it names the reason, not just the absence.

**Never confused with `consensus_rank`/`adp_rank`** — checked directly: `AdpCell`/`AdpBlock`/
`DraftRoomAdpCell` all read `row.adp`/`row.adpSource` exclusively; the existing `CONS` column
(`consensusRank`) is a separate column with its own separate delta (`Δ`), and code comments in
both `Board.tsx` and `DraftRoom.tsx` explicitly note ADP is "deliberately not turned into a second
delta column" beside the existing one, to avoid exactly this confusion at a glance.

**Live-data proof, not just static rendering**: recorded 5 real picks in Draft mode and confirmed
via `frontend/e2e/artifacts/09-draft-room-after-5-picks.png` that ADP figures for taken players
correctly drop out of the available list alongside their availability numbers — the ADP column
isn't a static overlay disconnected from the rest of the row's live state.

**No dedicated `adp.test.tsx` exists** — flagging as a real gap rather than skipping past it. The
rendering is covered incidentally by the general board/draft-room/player-detail test files (which
all still pass against real exported data, so a null-vs-zero regression in the loaded rows would
show up as a shape mismatch), but there is no test asserting the ADP-specific null-vs-populated
distinction or the source-label text directly. Did not add one this session (time went to the two
other jobs and the screenshot backlog) — a small addition for whoever next touches this file.

**Tests:** full suite 203 passed, 0 failed, 22 files (`npm test`, 2026-07-29, includes the
pre-existing coverage above). `tsc -b --noEmit` clean. Commit: see this session's closing commit on
branch `worktree-agent-aa652207ba4ef71bd`.

"Done looks like" is met on all three screens, with the one test-coverage gap noted above (not
blocking, flagged for follow-up). **Setting `STATUS: RESOLVED`.**
