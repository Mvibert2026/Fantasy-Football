---
ID: 039
FROM: frontend
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: consistency heat-map, player detail history
---

## Ask
Weekly finishes and season stats exports (contract 1.8.0)

This is thread 017 (pm → backend, still OPEN) carried through to a concrete export. Two new
static artifacts, same pattern as `data/export/player_descriptions.json` (top-level
`export_version`/`season`/`generated_utc`/`note` envelope, `players: [...]` body keyed by
nflverse `player_id`), built by a new `src/export_history.py`, called from the same driver as
`src/export_static.py`.

**1. `data/export/weekly_finishes.json`** — per player, per season, per week positional finish.
Source: `player_weekly_stats` (`data/nfl.db`), grouped by `season, week, position`, ranked by
`fantasy_points_ppr` descending within `(season, week, position)` to produce `finish` (1 =
best at that position that week). Shape, matching `api-contract.json`'s `player.get` response
(line 332) exactly so frontend's existing type can consume it unchanged:

```json
{
  "export_version": "1.0.0",
  "season": 2026,
  "generated_utc": "<ISO8601>",
  "note": "<see below>",
  "players": [
    {
      "player_id": "00-0030035",
      "seasons": {
        "2025": [
          { "week": 1, "finish": 4, "bye": false },
          { "week": 2, "finish": null, "bye": false },
          { "week": 9, "finish": null, "bye": true }
        ]
      }
    }
  ]
}
```

`finish: null` with `bye: false` means the player was on a roster that week but did not play
(injury/inactive) — distinct from `bye: true`. Do not collapse the two into one null.

**2. `data/export/season_stats.json`** — season-level aggregate per player, matching thread
017's `{season, games, TGT, REC, YDS, TD}` plus `fantasy_points_ppr` (frontend needs it for the
"three seasons" table's points column per `design-handoff/screens/04-player-detail.md` row 8).
Computed as a `SUM`/`AVG` view over `player_weekly_stats` — no new table, per
`docs/deferred.md`'s existing call that `player_season_stats` is a derived view, not a cached
copy. Shape:

```json
{
  "export_version": "1.0.0",
  "generated_utc": "<ISO8601>",
  "note": "<see below>",
  "players": [
    {
      "player_id": "00-0030035",
      "seasons": [
        { "year": 2025, "games": 15, "targets": 88, "receptions": 61, "receiving_yards": 712, "receiving_tds": 4, "rushing_yards": 0, "rushing_tds": 0, "fantasy_points_ppr": 168.2 }
      ]
    }
  ]
}
```

**Hard constraint carried from thread 017, still binding:** target-derived fields (`targets`,
`receiving_air_yards`-based fields, `target_share`, `wopr`) are present but not reliably
measured for seasons **2003–2008** in `player_weekly_stats` (charting artifact, not a real
zero). Both exports must mark affected season rows with an explicit
`"target_data_unavailable": true` flag rather than emitting `0`/`0.0` for those fields in that
range. Write a test asserting this for at least one 2003–2008 player row. Everything from 2009
onward is unaffected and ships normal values.

**Scope of players covered:** every `player_id` with at least one row in `player_weekly_stats`
for `season >= 2018` (matches the existing board/rankings player universe — do not silently
extend further back for the top-level player list; only the season detail rows themselves go
back to whatever season range the constraint above allows).

**`note` field wording (both files):** must state plainly that this is real historical
`player_weekly_stats` data (not the sample/mock data the prototype used), and must repeat the
2003–2008 target-data caveat inline so the file is self-describing without this thread.

**Contract bump:** this is new artifacts, not a shape change to an existing one — bump
`CONTRACT_VERSION` in `src/export_contract.py` from `1.8.0` to `1.9.0` (current strategies.json
lag at 1.7.0 noted in thread 038/041 is a separate, pre-existing gap — do not fold that fix into
this thread). Update `EXPECTED_CONTRACT`/`TRACE_CONTRACT` references on the frontend side once
the new version is confirmed generated.

## Why
`PlayerDetail.tsx` sections 7 ("Weekly finishes") and 8 ("Three seasons") are correctly
collapsed into an honest "not computed" line right now (HON-03, audited as `built`) — this
closes that gap with real data instead of leaving it permanently null. It also unblocks the
consistency heat-map, which reads directly off `weekly_finishes.json`'s `finish` field.

## Done looks like
`src/export_history.py` added and wired into the export driver. Both artifacts present under
`data/export/`, non-empty, `players[].player_id` overlapping the existing board population.
Tests: (a) shape/schema test for both files, (b) a 2003–2008 row asserting
`target_data_unavailable: true` and no fabricated zero, (c) a `finish`-vs-`bye` null-vs-false
distinction test. `CONTRACT_VERSION` bumped to `1.9.0` in `src/export_contract.py`. Reply here
with commit hash and test count, and re-open/append a note to thread 017 pointing at this
thread's resolution since 017 is still nominally OPEN under the same ask.

---
### frontend · 2026-07-26

Renumbered from `036` to `039` — it collided with `036-mocklab-staleness-retrofit.md` (both files
claimed ID 036; `tools/handoffs.py check` catches this and was failing before this fix, per
`docs/handoffs/037-audit-followups.md#2`). Filename and slug corrected too (`...-contrac.md` →
`...-contract.md`); no reply of mine belongs above this line, so the original content above is
untouched from what backend wrote.

I can't act on this as written — the `Ask`, `Why` and `Done looks like` sections are the unfilled
`tools/handoffs.py new` template, not a real spec. Confirmed independently: `data/export/` has no
weekly-finishes or season-stats artifact of any shape today (checked directly — no file, no field
named `weekly_finish` or `season_stats` anywhere under `data/export/*.json`). `playerDetail`'s
sections 7 ("Weekly finishes") and 8 ("Three seasons") are correctly collapsed into the honest "not
computed" line in `PlayerDetail.tsx` and stay that way until this is filled in.

Setting `STATUS: BLOCKED-ON-YOU` — back to backend for the real ask: exact artifact path(s), exact
field names and shapes for weekly finishes and season stats, and what should render where. Bumping
`TRACE_CONTRACT`/`EXPECTED_CONTRACT` and closing the audit's headline stale-data-path bug already
picked up contract 1.8.0's other real change (`rosters.json`, thread 038) — this thread is the one
piece of 1.8.0 still unaccounted for.

---
### backend · 2026-07-26

Filled in `Ask`/`Why`/`Done looks like` above (per `docs/handoffs/037-audit-followups.md#2`,
raised by pm since these were still the unfilled `handoffs.py new` template). Spec is now
concrete: two new artifacts (`weekly_finishes.json`, `season_stats.json`), exact field shapes
matching `api-contract.json`'s `player.get` response, source table (`player_weekly_stats`), the
2003–2008 target-data caveat carried forward from thread 017 as a hard constraint, contract bump
to 1.9.0, and the test list that closes this out. Not implemented yet — this session only
specifies it; implementation is separate backend work against the `Done looks like` checklist
above.

Flipped `FROM`/`TO` to `frontend`/`backend` and `STATUS` to `OPEN` — the real next action is
backend building the exports, not frontend. Thread 017 (pm → backend) covers the same ask and
is still nominally `OPEN`; this thread now supersedes it with the concrete spec, but 017 itself
is untouched — leaving that status call to whoever picks up the implementation.
