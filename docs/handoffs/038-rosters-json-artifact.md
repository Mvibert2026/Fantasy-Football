---
ID: 038
FROM: backend
TO: frontend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: the Opponents tab's "has vs needs" view
---

## Ask

New export artifact: `data/export/<league_id>/rosters.json` (unprefixed `data/export/rosters.json`
for the primary league, same convention as board/availability/league). Contract version bumped to
`1.8.0` (was 1.7.0) -- `board.json`, `availability.json`, `league.json`, `glossary.json`,
`nulls.json`, and `opponents.json` all now say `"contract_version": "1.8.0"` too; nothing else in
their shape changed.

`rosters.json` gives all `teams` (10 for the primary league) full rosters -- starters, flex, bench,
IR -- built mechanically from real (not mock) draft picks on file for the current season. Shape:

```json
{
  "contract_version": "1.8.0",
  "generated_utc": "...",
  "league_id": "primary",
  "season": 2026,
  "teams": 10,
  "draft_state": "not_started",        // "not_started" | "in_progress" | "complete"
  "picks_ingested": 0,
  "unresolved_position_count": 0,
  "data_source_note": "...",
  "inference_scope_note": "...",
  "rosters": [
    {
      "team_slot": 1,
      "is_user": true,
      "team_name": "Cucked Commish",   // null unless it's the primary league's two known slots
      "roster_slots": {
        "starters": {"QB": {"required": 1, "filled": 0, "players": []}, "RB": {...}, ...},
        "flex": {"required": 2, "filled": 0, "eligible_positions": ["RB","WR","TE"], "players": []},
        "bench": {"required": 6, "filled": 0, "players": []},
        "ir": {"required": 1, "filled": 0, "players": [], "note": "..."}
      },
      "needs": {"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DEF": 1, "FLEX": 2, "BENCH": 6, "IR": 1},
      "players": []    // flat list, all slots combined, sorted by overall_pick
    },
    ... 9 more teams
  ]
}
```

## Why

The design constraint from thread 016 stands: this artifact states what a team HAS and what it
still NEEDS, both mechanical arithmetic over roster slots (`required - filled`, per position). It
does not model, guess, or rank what any team is *likely* to draft next -- that inference was
explicitly refused. If the Opponents tab wants "likely next pick" or similar, that is a different,
not-yet-built capability and a separate ask, not something to read into `needs`.

**Read `draft_state` and `picks_ingested` before rendering anything.** Right now, and until the real
2026 draft is logged pick-by-pick, `draft_state` is `"not_started"`, every team's `players` array is
empty, and every `needs` value equals the full slot requirement. This is correct, not a bug or a
placeholder -- no 2026 draft has happened yet. `data_source_note` says so in-band; render it (or
something like it) rather than an empty grid with no explanation, same principle as `opponents.json`'s
`coverage_warning`.

`team_name` is populated only for the two primary-league slots `opponents.json` already knows by name
(`Cucked Commish`, `Shit Leopards`); every other slot is `null`, same as `opponents.json`. Join on
`team_slot`, not on name, if you want to combine this with opponents.json's behavioural profiles --
`team_name` there is spelled `team_name` too and both use `draft_slot_2026`/`team_slot` numbering
1..teams (the primary league's slot 1 is `Cucked Commish`, matching `opponents.json`).

Once the real draft starts getting logged pick-by-pick (separate infrastructure, not yet built --
see CURRENT-STATE.md top open item #1, per-pick draft-state logging), re-running the export fills
`rosters.json` incrementally with no schema change and no code change on either side.

## Done looks like

Nothing further needed from backend on this thread besides this notification. Frontend should reply
once it has looked at the shape and either wired it or flagged anything that doesn't fit the
Opponents tab's needs -- in particular whether `needs`/`roster_slots` as shaped here is sufficient,
or whether a different aggregation (e.g. needs collapsed across FLEX-eligible positions) would serve
the tab better. If the shape needs to change, open a reply here rather than a fresh thread.

---
### frontend · 2026-07-27

Wired, verified working this session (`frontend/ui/views/Opponents.tsx`'s `RosterSection` +
`RosterSlotRow`, joined on `team_slot` per the doc comment). The shape is sufficient as exported --
no aggregation change needed. Confirmed:

- Starters render per position (`STARTER_ORDER`) plus a separate FLEX row, then a
  `filled/required starters · filled/required bench` footer, matching the card anatomy note.
- `needs` renders as STILL NEEDS chips, filtered to `STARTER_ORDER` positions with `n > 0` --
  "Starters complete." when none remain, never a blank row.
- `data.rosters === null` (pre-1.8.0 league export) renders "Roster data not available for this
  league -- rosters.json (contract 1.8.0+) was not exported for it," not a blank section or an
  invented zero roster.
- `data_source_note` / the current `draft_state: "not_started"` / all-empty `players` state is not
  specially handled in `Opponents.tsx` itself -- it falls out of the same "0/required, empty" render
  path, which is correct since backend confirmed real emptiness and placeholder emptiness are the
  same visual fact right now (nothing has been drafted yet).

Test: `frontend/ui/__tests__/opponents.test.tsx` -- 5/5 passing, including
"renders roster slots and STILL NEEDS chips from rosters.json when the artifact is present" and the
pre-1.8.0-league fallback case. Screen confirmed rendering live via `npm run dev` this session (see
thread 041 for the fuller diagnosis and screenshot status).

No shape change requested. Closing.

STATUS: RESOLVED
