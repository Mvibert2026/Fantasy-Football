# 2026-07-29 · data-ops · Sleeper component projection ingestion

**Dispatch:** PM/founder-relayed task, licensing question pre-decided ("personal use, proceed"),
answering thread 091/092 item 1 (`docs/research/component-projections-and-fr-053-features-
2026-07-29.md`).

## What was built

`src/ingest_sleeper_projections.py` — matches `src/ingest_ffc_adp.py`'s shape: descriptive
User-Agent, HTTP 429 backoff, at most one fetch per position per calendar day, CSV snapshot
canonical under `data/projection-snapshots/`, `data/nfl.db` a rebuildable cache of it.

**Independently re-verified the researcher's endpoint record before building** (the researcher's
session had no shell tool and could not run anything itself):
- `GET https://api.sleeper.com/projections/nfl/2026?season_type=regular&position[]=QB` → HTTP 200,
  355 QB rows, every row `company: "rotowire"`, `stats` block carrying real per-component numbers
  (`pass_att/cmp/yd/td/int`, `rush_att/yd/td`, `rec/rec_yd/rec_td`, `fum_lost`, `gp`, 2pt fields,
  reception-distance buckets). RB=741, WR=1362, TE=647 rows the same session.
- `https://api.sleeper.com/robots.txt` is entirely commented out — nothing disallowed.

Both match the researcher's record; no schema drift found.

**Identity resolution:** `identity.resolve(conn, "sleeper", player_id)` — a real crosswalk spoke
already present in `ff_playerids.sleeper_id` (identity.py's `DIRECT_CROSSWALK_SOURCES`), not name
matching. An unresolved `sleeper_player_id` is quarantined with reason
`no_sleeper_crosswalk_match`, never guessed.

**A real bug found and fixed before landing:** Sleeper's own `player.position` field is not
reliably consistent with the `position[]=` query filter — an `RB` fetch returned some rows Sleeper
itself tagged `WR`/`TE`/`FB`. The first version keyed the once-a-day skip-check and the re-run
DELETE scope on that field, which caused the WR and TE fetches to be silently (and wrongly)
skipped as "already fetched today" because a stray mistagged row from the RB fetch satisfied the
check. Added a separate `query_position` column carrying the actually-requested filter and
rekeyed gating/DELETE/CSV export on it. Caught by running the real ingester against the real
crosswalk, not just the unit tests (which used single-position fixtures and would not have
exposed this).

**As-of-date convention:** Sleeper's payload has no as-of-date field of its own, only per-row
`last_modified`/`updated_at` (Rotowire's own last-touch timestamps). Per CLAUDE.md §4,
`as_of_date` is stamped as OUR capture date (UTC); the source's own timestamps are preserved
verbatim as `source_last_modified`/`source_updated_at` so the two are never conflated.

## Scope discipline

Ingestion only — no scoring changes, no re-ranking, `board.json` untouched. **Not wired into any
export, not behind the public site** (CLAUDE.md §10; the app is public per `docs/CURRENT-STATE.md`,
and Sleeper's ToS §9.2 forbids redistribution, per the researcher's artifact). Lands only in
`data/nfl.db` (gitignored) and `data/projection-snapshots/` (committed, canonical).

## Rows ingested / quarantined

| Position | Stored | Quarantined | Match rate | Reason (100% of quarantine) |
|---|---|---|---|---|
| QB | 250 | 105 | 70.4% | `no_sleeper_crosswalk_match` |
| RB | 538 | 203 | 72.6% | `no_sleeper_crosswalk_match` |
| WR | 840 | 522 | 61.7% | `no_sleeper_crosswalk_match` |
| TE | 379 | 268 | 58.6% | `no_sleeper_crosswalk_match` |

Spot-checked: quarantined names are deep practice-squad/UDFA QBs (Tim DeMorat, James Blackman,
etc.) absent from `ff_playerids`, not real starters — resolved rows include Dak Prescott, Jared
Goff, Patrick Mahomes with real component values. Match rate is lower than FFC's ADP ingester
(~98.5%) because Sleeper's pool includes far more fringe/UDFA players than the ADP boards do; not
a resolution defect.

## Sources attempted and status

| Source | Status |
|---|---|
| `api.sleeper.com/projections/nfl/2026` (QB/RB/WR/TE) | Fetched successfully, 4/4 positions |
| Every other source in the researcher's artifact (FantasyPros API, NFL.com, PFF, SportsDataIO) | Not attempted — out of scope for this dispatch, which named the Sleeper route specifically |

## Records written

- `docs/handoffs/092-component-projections-exist-and-are-cheap-for-pe.md` — allocated the
  previously-staged unallocated thread (`091-...md`, deleted, no shell to allocate it originally)
  via `tools/handoffs.py new`, pasted the full staged body, appended a data-ops reply recording
  what was built against item 1's licensing ruling. Left `STATUS: OPEN` — only `pm`/`design` may
  resolve; items 2-5 are untouched and outside data-ops scope.
- `docs/founder-requests/FR-056-...md` — the founder's "personal use, proceed" ruling, marked DONE.

## Tests / commit

- `python3 -m pytest tests/test_ingest_sleeper_projections.py -q` → 10 passed.
- `python3 -m pytest tests/ -q` → 33 failed / 718 passed / 9 errors — **identical to the baseline
  measured with this session's new files absent** (confirmed via re-run without them); every
  failure is the missing/partial-local-`nfl.db` condition documented in
  `docs/can-we-rebuild-the-database.md`, none touch `ingest_sleeper_projections.py`.
- `python3 tools/handoffs.py check` → fails only on the two pre-existing, deliberately-known-red
  ADR-054/055 collisions (`docs/CURRENT-STATE.md` top open item #15) — unrelated, unchanged by
  this session.
- Commit `fdd4685b9ac4a902b31bc6107821de02b1150bfe`.
