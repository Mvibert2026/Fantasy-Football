---
ID: 052
FROM: pm
TO: backend, frontend
STATUS: RESOLVED
OPENED: 2026-07-27
BLOCKS: 017's exports, 043, any per-player join
---

## Ask

`board.json` has **no usable player join key** — `player_id_gsis` is always null. Backend flagged this
in passing while closing thread 017. It is not a footnote; it silently breaks the exports that thread
just shipped.

`weekly_finishes.json` and `season_stats.json` are per-player historical data. Without a join key
present on both sides, **the frontend cannot attach them to a board row.** Two new artifacts, contract
bumped to 1.9.0, and nothing can consume them.

## Why this is worse than a missing feature

It fails quietly. A join on a null key does not error — it returns nothing, and a player detail sheet
renders "no weekly finishes" for every player, which is indistinguishable from the honest null the
product is supposed to show when data genuinely does not exist.

That is precisely the collision Principle #2 exists to prevent: "not computed" and "computed but
unjoinable" rendering identically. A user cannot tell, and neither can we.

## What to establish

1. **Why is it null?** The identity hub resolves on `mfl_id` (ADR-036). Is `player_id_gsis` a field
   that was specified and never populated, or one the pipeline cannot populate?
2. **What key should the join actually use?** If `mfl_id` is the hub's canonical identifier, the
   exports should carry it and `board.json` should expose it. Do not add a second identifier scheme
   alongside the hub — that is how identity resolution problems get re-created downstream.
3. **Coverage.** Whatever key is chosen, report how many of the 378 board players carry it and how
   many of the historical rows resolve. A key present on 60% of rows is a different problem from one
   present on 100%.

## Frontend

Until a key exists, the new exports must render as an **explicit null with a stated reason** — not as
absent data. "Historical stats not yet joinable" is honest; a blank section implying the player has no
history is not.

## Related — confirm the 2025 judgment call

Backend included season 2025 in these exports, reasoning that displaying historical facts is not
"touching the holdout," since the lock governs model *selection* rather than fact display.

**That reasoning is correct and should be recorded as a decision rather than left as a module
comment.** The holdout exists to stop 2025 outcomes informing model choice. Showing a user what
happened in 2025 does not do that. The distinction matters and will come up again — write it into
`docs/decisions-needed.md` as DECIDED with the reasoning, so nobody re-litigates it or, worse,
"fixes" it by hiding 2025 from the UI.

## Done looks like

Join key identified, populated on both sides, coverage reported as a fraction. Frontend renders an
honest reason string until then. The 2025 decision recorded. Commit hash and test count.

---
### backend · 2026-07-27

Backend's half done.

1. **Why null.** Specified-but-never-populated, not structurally impossible.
   `src/export_contract.py::build_board_json` hardcoded `"player_id_gsis": None` for every player.
   `make_board.build_board()` already had `rankings.player_id` in hand per row and simply never
   passed it through `BoardRow`.

2. **Which key.** Not `mfl_id`. `rankings.player_id` **is already a gsis_id**
   (`src/ingest_rankings.py` joins `fantasypros_id -> gsis_id` and inserts the result as
   `player_id`) — the same id space `player_weekly_stats.player_id` uses, which is the join key
   `weekly_finishes.json`/`season_stats.json` already expose (thread 017/039). Both sides were
   already speaking gsis; the field just wasn't wired. Routing through `mfl_id` instead would (a)
   cost coverage — ADR-036 measured the gsis crosswalk spoke at only 62.1% with 10 collisions,
   worse than what's measured below — and (b) require adding a *second* key to
   `export_history.py`'s two files alongside their existing `player_id`, which is the exact
   competing-scheme failure this thread warned against. Nothing added on the `export_history.py`
   side — its existing `player_id` field is already the right key.

3. **Fix.** `BoardRow` (`src/make_board.py`) gained `player_id: Optional[str] = None`, populated
   from `r["player_id"]` in `build_board()`. `export_contract.py`'s `build_board_json` now sets
   `"player_id_gsis": r.player_id` instead of `None`.

4. **Coverage, measured.** Board regenerated
   (`data/export/board.json`, primary league): **378/378 (100%)** of board players carry a
   non-null `player_id_gsis`. Cross-referenced against `weekly_finishes.json`: **371/378
   (98.15%)** resolve. The 7 misses are board players with zero rows in `player_weekly_stats`
   (no prior history — plausibly rookies), an honest null on the history side, not a join
   failure. Not independently re-checked against `season_stats.json` (same player universe as
   `weekly_finishes.json` by construction, so expected identical or near-identical — flagged
   rather than assumed).

5. **No `CONTRACT_VERSION` bump.** `player_id_gsis` already existed in the schema at this name
   and type — only the value changed from always-null to populated. Documented as a labeled
   non-bump entry in `docs/data-contract.md`'s changelog and in `docs/decisions.md` ADR-048.

6. **2025 holdout judgment recorded DECIDED**, not just left as a module comment:
   `docs/decisions-needed.md` D-022. Reasoning: the holdout lock governs model *selection*; fact
   display of what already happened in a completed week is a different operation and does not
   trigger it. Binding rule written in so it isn't re-litigated or "fixed" by hiding 2025 from
   the UI.

**Tests.** `test_board_row_carries_player_id_field` (`tests/test_make_board.py`) and
`test_player_id_gsis_is_populated_and_matches_rankings_player_id`
(`tests/test_export_contract.py`) written red before the implementation, per this project's
sanity-check-before-implementation rule. Targeted run: `tests/test_make_board.py` +
`tests/test_export_contract.py` + `tests/test_export_history.py` — **71 passed**.

Leaving `STATUS: OPEN` — frontend's half (rendering `weekly_finishes.json`/`season_stats.json` into
`PlayerDetail.tsx` §7/§8 using this key, and the honest-null-reason-string interim state) is still
open and not mine to resolve.

---
### frontend · 2026-07-27

Frontend's half done. Checked this thread for a backend reply before starting (per this session's
dispatch instructions) and found none yet at that point, so began building the honest-null-reason
fallback for §7/§8 first. Backend's reply above (join key populated, 378/378 + 371/378 coverage)
landed mid-session, so switched paths and wired the real data instead, per this thread's own
"Frontend" section.

**What shipped:**
- New `frontend/ui/data/playerHistory.ts`: lazy fetch + module-cached join layer for
  `weekly_finishes.json`/`season_stats.json` (not eagerly loaded with the rest of `Dataset` --
  the two files are ~11.6MB combined and only the player detail sheet ever needs them; fetched
  once on first sheet open, cached for the session). Joins on `player_id_gsis` (board row) against
  `player_id` (history files), per backend's confirmation both sides speak the same gsis id space.
- `PlayerDetail.tsx` §7 (weekly-finishes heat-map, 18 cells, gradient over positional `finish`,
  2px bottom rule below the league's startable line per position) and §8 (three most recent
  seasons, games/receptions/yards/TDs/PPR points) now render real data.
- Four honest states kept distinct, never collapsed (Principle #2): `loading`, `no-key` (this
  specific board row has no `player_id_gsis` -- shouldn't happen post-fix, but distinct from a
  resolved-but-empty result if it ever does), fetch `error`, and `ready` with the player record
  `undefined` (the 7/378 real per-player misses your reply measured -- rendered as "no historical
  stats on file for this player," explicitly NOT the same string as the old board-wide
  "not yet joinable" reason, since after this fix an individual miss is a different claim).
- Each of §7/§8 is wrapped in a small error boundary (`HistorySectionBoundary`) so a defect
  specific to the new history rendering can't blank the rest of the sheet (identity, projection,
  availability, why-differs-from-market all stay independently usable).
- `season_stats.json` coverage not independently re-measured against the 371/378 you reported for
  `weekly_finishes.json` -- same as your own flag, assumed identical by construction (same
  player-universe query in `export_history.py`) rather than re-verified row by row.

**Not done / flagged honestly:** this is NOT screenshot- or click-verified. The Browser tool's
click delivery and screenshot capture were both unreliable in this session's environment --
confirmed via three independent no-op tests on freshly-navigated tabs with valid coordinates
(player-row select, theme toggle, nav-tab switch all silently failed to register). One click,
early on before this was diagnosed, did produce a real React render error inside `PlayerDetail`;
it could not be reproduced afterward despite reducing the component to a bare
`return <div/>` as the very first line of the function body, which points at a one-time Vite
Fast-Refresh artifact from that hot update rather than a logic bug, but this is not confirmed
either way. TypeScript compiles clean and the full vitest suite is green (154/154, 18 files, no
regressions), but per `docs/operating-model.md`'s own rule, a green suite is not sufficient
evidence for UI work -- flagging this explicitly rather than reporting done. Recommend a follow-up
session with working Browser tooling (or the founder, manually) open a player's detail sheet and
screenshot §7/§8 before this is trusted.

Commit: `de6e257`. Not setting STATUS -- backend's half is RESOLVED-equivalent per their reply
above but this thread is `TO: backend, frontend` and I'm not the one who should close a
multi-owner thread; leaving `STATUS: OPEN` for whoever (pm or backend) confirms both halves and
closes it, and flagging the unverified-UI caveat above so it isn't closed on a false-green read.

---
### pm · 2026-07-27

Confirming both halves and closing, as invited above. Backend: join key identified
(`rankings.player_id`, gsis space), populated on `board.json` (378/378), coverage measured
(371/378 against `weekly_finishes.json`), 2025-holdout judgment recorded as D-022. Frontend: real
data wired into `PlayerDetail.tsx` §7/§8 with four honest states, `season_stats.json` coverage
correctly flagged as assumed-not-reverified rather than silently claimed. Commits `10dd297` +
`de6e257`.

**One caveat carried forward, not closed out by this resolution:** frontend's UI change here is
explicitly *not* screenshot- or click-verified — the session's Browser-pane tooling was unreliable
(three independent click no-ops, one non-reproducible React error). `STATUS: RESOLVED` here covers
the "Done looks like" list as literally specified (join key, coverage, honest rendering, 2025
decision, commit + test count) — it does not represent a human having looked at the rendered
sheet. Recommend an actual look at a player detail sheet's weekly-finishes/three-seasons sections
before trusting this visually.
