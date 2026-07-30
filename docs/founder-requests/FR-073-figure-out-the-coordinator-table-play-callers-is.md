---
ID: FR-073
STATUS: IN PROGRESS
SOURCE: PM dispatch, data-ops session 2026-07-30
RAISED: 2026-07-30
---

## Request
Founder's words (relayed via PM dispatch, not verbatim chat capture): "FIgure out the coordinator
table."

## Why it matters

`play_callers` had zero rows. CLAUDE.md §4 makes `coach_id` a first-class schema dimension on the
explicit reasoning that coordinators change teams and tendency signals must follow the person —
so the project had committed to a factor (test-registry #29/#30) it had no data for at all.

## Investigation (2026-07-30, data-ops)

**1. Why empty?** Not an oversight or a silent no-op — `src/ingest_play_callers.py` was
deliberately PARKED with a documented completion trigger (the ESPN 32-team play-caller roundup,
not published until late August; the supplied source data was only 22/64 cells populated and the
module refuses to ingest an admitted guess).

**2. Licensing.** CLAUDE.md §5 names PFR "or equivalent," requiring verification before building.
Re-verified this session: PFR `robots.txt` and `sports-reference.com/data_use.html` both HTTP 403
— unreadable programmatically, conservative default applies, PFR stays blocked (matches the
2026-07-29 finding in `docs/research/missing-inputs-sourcing-2026-07-29.md`). That same document
had already found and licence-verified an alternative: Wikipedia's `Template:NFL final staff` on
team-season articles, CC BY-SA 4.0 — fetch AND display both permitted with attribution, a better
licence position than any other source in this project. That finding was research-only, not yet
built.

**3. Populated.** Built `src/ingest_coordinators_wikipedia.py` against that template. **607 rows
stored** (300 OC, 307 DC), **32 quarantined** (real gaps in Wikipedia's own coverage, not parser
failures — detail in `data/qa/coordinator-quarantine-2026-07-30.csv`), covering all 32 teams,
seasons 2015–2024. `coach_id` is the coordinator's own name (Wikipedia gives no stable numeric
ID — a named, unverified simplification). `play_callers`' primary key was widened from `(team,
season, start_week)` to `(team, season, start_week, title)` to let OC and DC coexist for the same
team-season (free — the table had zero production rows).

## Known limitation, not resolved this session

Wikipedia's template is named **"final staff"** — end-of-season, not going-into-the-season. Every
row is stamped `is_final_season_snapshot=1` and a real `as_of_date` (that season's actual final
game date, from `nflreadpy`), so nothing is silently mistaken for a preseason value. But
test-registry #29/#30 need the *going-into-the-season* answer, and end-of-season data is wrong for
any team with a mid-year firing. This is a look-ahead judgment call (CLAUDE.md §6.1), not a
mechanical one, so it was handed to Backend rather than resolved here:
`docs/handoffs/NEW-coordinator-final-staff-lookahead-semantics.md` (unallocated, PM to assign an
ID). Status held at IN PROGRESS, not SHIPPED, until that thread resolves.

Coverage is also currently 2015–2024 only — Wikipedia's template goes back to 1946; extending
further back is the same script with a wider `--start-season`, not attempted this session to keep
scope bounded. Full writeup: `docs/status/2026-07-30-data-ops-adp-and-coordinators.md`.
