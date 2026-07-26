# Design heads-up — trace surface change at contract 1.3.0

**Date:** 2026-07-25
**Raised by:** front-end session (branch `frontend-prep`)
**Severity:** reference material is now out of date; no UI rework needed

## What changed

The league's startable thresholds moved:

| Position | Was | Now |
|---|---|---|
| QB | 10 | 10 (unchanged) |
| RB | 28 | **30** |
| WR | 41 | **40** |
| TE | 10 | 10 (unchanged in the export; the earlier design handoff said 11) |
| DEF | — | still none published |

Source: `league.json:replacement_levels` at contract `1.3.0`, per ADR-029. The backend
derived these from measurement rather than carrying over the 12-team convention.

## Why this needs a heads-up rather than just a commit

**No field was renamed, and no label changed.** Under a naming rule alone this would not
qualify. It is being raised anyway because the rule exists to protect the *trace
affordance* — the thing a user reads when they want to check a number — and a value
change breaks that affordance in the same way a rename does.

Concretely: the tooltips, the methodology table and the assistant's provenance lines all
render these thresholds as user-visible text. Anyone who noted "startable through RB28"
from the previous build now holds a wrong number, with no visible signal that it changed.
The label they'd search for is identical.

This also cascades. ADR-029 moved every `vbd`, `projected_points` and `overall_rank` on
the board, so any screenshot, mock, or worked example built against 1.0.0–1.2.0 shows
stale figures throughout — not just in the thresholds row.

## What Design should check

1. Any mock, spec or reference doc quoting RB28 / WR41 / TE11 — those numbers are dead.
2. Any worked example using a specific player's rank, VBD or projection. The whole board
   re-sorted; examples need regenerating from 1.3.0, not patching.
3. The DEF row. The roster still starts one DEF, the board still carries no DEF players,
   and `league.json` still publishes no DEF replacement level. The app renders the
   board's own `def_note` there rather than a number. If the design reference shows a
   DEF threshold, it is showing something that does not exist in the data.

## What the front end did

- `TRACE_CONTRACT` bumped `1.0.0` → `1.3.0` in `ui/data/trace-fields.ts`, with the change
  recorded in `TRACE_CHANGELOG`.
- Thresholds were already read from `league.json` rather than hardcoded, so no threshold
  value was edited in the front end. The new numbers appeared on refresh.
- The drift banner cleared on its own once the export caught up to the expected version.
- A visible **Refresh data** control now re-reads the exports on demand and reports a
  before/after, so the next contract bump surfaces without anyone noticing a stale banner.

## Still open, filed to the backend

Neither is a front-end workaround and neither is fixed here:

1. `league.json` emits a bare `Infinity` token for the DEF points-allowed upper bound.
   That is invalid JSON — `JSON.parse` and `fetch().json()` both throw on it.
2. DEF has no published replacement level while the roster starts one.
