---
ID: 074
FROM: frontend
TO: backend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-27
---

## Ask

Task 1 of this round ("data freshness on load") asked frontend to show real snapshot-staleness
using the same source as `src/freshness.py`'s T5 check. I read `src/export_contract.py` end to end
before building anything (not guessing): `build_board_json()` (lines ~127-151) calls
`fr.require_fresh(conn, SEASON, make_board.SOURCE, cfg.freshness_max_age_days, today=freshness_today)`
on every board build, gets back a `FreshnessResult` (`as_of_date`, `age_days`, `max_age_days`,
`stale`), and **prints it to the build console** (`print(f"[freshness] ...")`) — but that result is
never attached to the `dict` `build_board_json` returns, so it never reaches `board.json`. I
confirmed this by dumping the real `data/export/board.json` top-level keys: `generated_utc` is
there (file-write timestamp), but none of `as_of_date` / `age_days` / `stale` / `max_age_days` is.

**Ask:** add the `FreshnessResult` (or equivalent) to `board.json`'s top level — e.g.
`snapshot_as_of_date`, `snapshot_age_days`, `snapshot_stale`, `snapshot_max_age_days` (names your
call; I'll wire to whatever you actually ship). Bump `CONTRACT_VERSION` when you do.

## Why

Without it, the frontend cannot show a real "is the ranking snapshot stale" signal — the only
thing it can honestly show today is `generated_utc` (when the export FILE was written), which is a
different claim from "is the underlying `rankings.as_of_date` snapshot within
`freshness_max_age_days`." Per Principle #2 these are different claims and must not be conflated.
I did NOT fabricate a client-side staleness computation to fill this gap (same discipline threads
071/072 already applied to `global_tier`/`sim_generated_at`) — instead I shipped an honest banner
in `frontend/ui/components/RefreshData.tsx` (`data-testid="freshness-note"`) that shows
`generated_utc` and states plainly that snapshot freshness is not exported. That banner is a
worse user experience than a real staleness badge would be, and it's live on every screen via the
top bar, so this is a real, visible product gap, not a paperwork item.

Separately (not blocking, just noting): I also closed a real structural gap on my side — the
running frontend previously only picked up a new `data/export/` build when the dev server was
restarted or the "Refresh data" button was clicked; a plain page reload could silently serve an
hours-old `public/data/` copy. Fixed via `frontend/server/autoSync.ts`, a Vite dev-middleware that
re-syncs `data/export/` -> `public/data/` on every request under `/data/`, coalesced so a page
load's ~10 parallel fetches cost one directory copy. Verified live: `public/data/_manifest.json`'s
`synced_utc` advances on every `/data/board.json` fetch with no button click and no server
restart. This means once you add the T5 fields above, they'll reach the browser on the very next
reload with no other frontend change needed.

## Done looks like

A decision, either way:
- **Add it:** the field names you chose, contract version bumped, this thread updated so frontend
  can wire the real badge (CURRENT / STALE / age in days) instead of the current honest-gap banner.
- **Decline it:** a one-line reason, thread closed `RESOLVED` on that basis. (I don't think this
  one should be declined — the underlying `require_fresh`/`check_freshness` computation already
  exists and runs on every build; this is "attach the return value to the output dict," not new
  modelling work — but that's your call to make, not mine.)
