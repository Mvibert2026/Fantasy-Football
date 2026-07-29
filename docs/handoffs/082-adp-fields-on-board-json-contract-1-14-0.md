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

<<<<<<< HEAD
### frontend · 2026-07-29

**STATUS: RESOLVED.** Built, screenshots looked at directly (not just captured) — 6 images in
`frontend/e2e/artifacts/`, paths below. 202/202 frontend tests pass (22 files), `tsc -b --noEmit`
clean, `npm run smoke` 18/19 (the one failure is the pre-existing missing-`ANTHROPIC_API_KEY`
network error documented in `docs/frontend-cloud-runbook.md`, unrelated to this work).

Wired: `frontend/ui/data/types.ts` (5 new optional player-row fields, 4 new optional top-level
`RawBoard` fields), `frontend/ui/data/board.ts` (`BoardRow.adp`/`adpMinPick`/`adpMaxPick`/
`adpSelectedPct` as `Cell<number>`, `adpSource` as a plain string alongside them — null cells carry
an authored reason citing the ~230-player MFL coverage limit), `frontend/ui/data/contract.ts`
(`EXPECTED_CONTRACT` -> 1.14.0), `frontend/ui/data/trace-fields.ts` (`TRACE_CONTRACT` -> 1.14.0,
changelog entry, all 5 player-row + 4 header fields registered — `trace-fields.test.ts` passes).

**Board (prep):** new `ADP (MFL)` column between CONS and Δ. Header label itself carries the
glance-level "this is not your league's ADP" signal; per-cell tooltip carries source, pick range,
selected%; absent cells render the same em-dash convention as every other column, tooltip explains
why (MFL's ~top-230 coverage). Screenshots: `adp-board-2026-07-29.png` (top of board, ADP present
for the top 16), `adp-board-null-row-2026-07-29.png` (scrolled to rank 33, Jeremiyah Love, ADP
genuinely null — "—" visible, distinct from populated neighbors).

**Draft Room:** compact figure with an "MFL" superscript beside each available player, next to the
existing Δ-vs-consensus column — not merged with it. Screenshots: `adp-draft-room-2026-07-29.png`,
`adp-draft-room-null-row-2026-07-29.png` (Jeremiyah Love again, "—" with no MFL tag).

**Player Detail:** new MARKET ADP block below the WHY OUR RANK DIFFERS section — value, pick
range, selected%, and the full `adp_source_note` verbatim (this is the one place the whole caveat
is always visible, not just on hover). Screenshots: `adp-player-detail-present.png` (Bijan
Robinson, 3.3 avg pick, range 1–7, 16% selected), `adp-player-detail-null.png` (Jeremiyah Love,
"No MFL ADP data for this player... Not a zero, not a rank -- not computed.").

**Judgement call on the delta column, as invited:** did NOT add a second delta (ADP vs. our rank)
next to the existing `delta_vs_consensus` column. Reason: the board already has one delta measuring
one thing (expert consensus vs. our rank); a second, differently-defined delta (market vs. our
rank) sitting beside it would read as the same signal at a glance, and the difference between the
two deltas isn't itself a field this app can source — computing it client-side would be inventing a
number, not displaying one. Instead the raw ADP value sits beside CONS, so a reader compares three
sourced numbers (CONS, ADP, our rank) rather than trusting an implied fourth. Recorded in the
trace-fields.ts 1.14.0 changelog entry too.

Never rendered `consensus_rank` under an ADP label, never blended `mfl_proxy` with anything else
(there is nothing else wired yet — `ffc_*` sources exist in the backend ingester per your note but
this app only reads `adp`/`adp_source` as exported, no client-side merge logic was written).

Commit: `75bf095` (this work landed inside a coordinator commit alongside unrelated handoffs
tooling work — verified via `git diff HEAD` before and after, empty diff, byte-for-byte the same
as authored) plus a follow-up commit for the e2e screenshot script and the 6 screenshots
themselves, hash below in the session log.

**STATUS: RESOLVED**
=======
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
>>>>>>> 9bbdf42896affb6e345b99e1970fdbe1c3c9f4b7
