# 2026-07-30 — data-ops: FFC PPR historical ADP backfill + coordinator table populated from Wikipedia

Two founder-named gaps (FR-072, FR-073), dispatched directly (PM allocates thread/FR numbers;
none hand-typed here — `tools/founder_requests.py new`/`sync` used for FR-072/FR-073).

## Gap 1 — historical ADP (FR-072), SHIPPED

`docs/analysis/adp-vs-production-2026-07-30.md` had run entirely on FFC's 12-team archive; the
founder's leagues are 10-team, and asked to "get the rest" of historical ADP.

**Finding: no 10-team or 14-team historical archive exists anywhere.** FFC's archived pages for a
past season silently serve the 12-team board regardless of the requested team count (already
documented in `docs/research/historical-adp-availability-2026-07-29.md`, re-confirmed, not
re-litigated). What was genuinely missing was the third FFC scoring format — PPR — at 12-team,
which prior thread 055 had left as an explicit `[GAP]`.

Extended `tools/backfill_ffc_adp_history.py` with a `ppr` format key. Reused the existing
season-level look-ahead gate (kickoff dates are format-independent — GATE_FAIL: 2007–2009, 2011,
2012). Independently re-verified content validity rather than assuming it transfers from non-PPR:
fetched PPR 2010 directly, found the identical migration-artifact failure (26 rows, DEF/QB-heavy,
missing every real 2010 RB1) as non-PPR 2010 — excluded on the same basis. Spot-checked PPR 2013
sane (42 rows, real top players in plausible order).

**Result: 1,370 rows stored, 204 quarantined, 12 seasons (2013–2024), `adp_source =
ffc_ppr_12team`.**

| Format | Seasons | Rows | adp_source |
|---|---|---|---|
| non-PPR | 2013–2024 (+2010) | 1,395 | `ffc_non_ppr_12team` |
| half-PPR | 2018–2024 | 1,072 | `ffc_half_ppr_12team` |
| PPR | 2013–2024 | 1,370 | `ffc_ppr_12team` |
| (all three, daily, 10-team, today forward) | — | 564 | `ffc_*_10team` |

Quarantine (204 rows, mostly `no_name_match` on team-defense entries, the same structural ceiling
documented in ADR-054 — `ff_playerids` carries zero DEF rows): `data/qa/ffc-adp-history-
quarantine-ppr-2026-07-30.csv`. 12 new/changed tests in `tests/test_backfill_ffc_adp_history.py`
(was 10, now 12, all passing).

## Gap 2 — coordinator table (FR-073), IN PROGRESS (mechanical build done, semantics question
handed to Backend)

`play_callers` had zero rows. Investigated in the order the dispatch specified:

**1. Why empty?** `src/ingest_play_callers.py` was deliberately PARKED (its own docstring):
waiting on the ESPN 32-team play-caller roundup (not published until late August), and the
supplied source data was only 22/64 cells populated — the module refuses to ingest an admitted
guess rather than silently no-op. Not an oversight.

**2. Licensing.** Re-verified PFR blocked: `robots.txt` and `sports-reference.com/data_use.html`
both return HTTP 403 today, matching the existing finding in
`docs/research/missing-inputs-sourcing-2026-07-29.md`. That same document had already found and
licence-cleared an alternative — Wikipedia's `Template:NFL final staff` on team-season articles,
CC BY-SA 4.0, fetch AND display both permitted with attribution — but left it as research, not a
build.

**3. Populated.** Built `src/ingest_coordinators_wikipedia.py`: fetches each team-season article
via the MediaWiki API (descriptive User-Agent, 0.5s between requests, every response cached to
`data/raw/wikipedia/`), parses OC/DC/HC out of the `{{NFL final staff ...}}` template block only
(never picks up an unrelated mention elsewhere in the article), and stores into `play_callers`.

Two real defects found and fixed during testing, not assumed correct:
- `play_callers`' original `PRIMARY KEY (team, season, start_week)` silently overwrote the OC row
  with the DC row for the same team-season on `INSERT OR REPLACE` — widened to include `title`
  (free: the table had zero production rows anywhere).
- The OC/DC title can be compounded with another role on one bullet line (verified real case, WAS
  2023: "Assistant head coach/offensive coordinator – Eric Bieniemy") — the initial regex assumed
  a standalone "Offensive coordinator –" line and missed it; widened to match the phrase anywhere
  in the bullet's title text, with a word-boundary guard against false positives like "Pass game
  coordinator."

**Result: 607 rows stored (300 OC, 307 DC), 32 quarantined, all 32 teams, seasons 2015–2024.**
Sample rows spot-checked against known real-world facts (Kyle Shanahan ATL OC 2015, Eric Bieniemy
WAS OC 2023, Kliff Kingsbury WAS OC 2024) — all correct. Quarantine reasons (19
`no_oc_field_in_template`, 12 `no_dc_field_in_template`, 1 `no_final_staff_template_on_page`) are
real gaps in Wikipedia's own per-page coverage, not parser failures:
`data/qa/coordinator-quarantine-2026-07-30.csv`.

**Residual look-ahead question, handed to Backend, not resolved here.** The template is "final
staff" — end-of-season, not who was hired going into the season. Every row is stamped
`is_final_season_snapshot=1` with a real `as_of_date` (season's actual last game date, from
`nflreadpy`), so nothing downstream can mistake it for a preseason value silently. But
test-registry #29/#30 (coordinator continuity, first-time play-callers) need the going-into-
the-season answer, which end-of-season data gets wrong for any team with a mid-year firing. This
is a statistical/look-ahead judgment call (CLAUDE.md §6.1), not a mechanical one — per my own
operating brief ("if a task genuinely needs statistical judgment, hand it to Backend"), I did not
resolve it myself. Opened `docs/handoffs/NEW-coordinator-final-staff-lookahead-semantics.md`
(unallocated — PM assigns the ID) naming the two options the prior research doc already left
uncosted (restrict to no-mid-season-change team-seasons, or reconstruct via Wikipedia revision
history) and asking Backend to decide. FR-073 held at `IN PROGRESS`, not `SHIPPED`, until that
resolves.

Coverage is 2015–2024 only (Wikipedia's template goes back to 1946); not extended further to keep
this session's scope bounded — same script, wider `--start-season`, is the follow-up.

11 new tests in `tests/test_ingest_coordinators_wikipedia.py`, all passing (including a regression
test for the PK-collision defect above). `ingest_coordinators_wikipedia.py` added to
`tests/test_holdout_audit.py`'s `CONNECT_ALLOWLIST` (new ingestion module, same class as the
other `ingest_*` modules already there).

## Rows ingested / quarantined summary

| Item | Stored | Quarantined |
|---|---|---|
| FFC PPR 12-team ADP, 2013–2024 | 1,370 | 204 |
| Coordinators (OC/DC), 2015–2024 | 607 | 32 |

## Sources attempted and status

| Source | Status |
|---|---|
| FFC `/adp/ppr/12-team/all/<year>` | Fetched — not on `robots.txt` disallow list, re-verified |
| Pro Football Reference | Blocked — `robots.txt` and `data_use.html` both HTTP 403, re-verified |
| Wikipedia MediaWiki API (`Template:NFL final staff`) | Fetched — CC BY-SA 4.0, permitted with attribution |

## Tests

- `tests/test_backfill_ffc_adp_history.py`: 12 passed (was 10)
- `tests/test_ingest_coordinators_wikipedia.py`: 11 passed (new file)
- `tests/test_holdout_audit.py`: 1 pre-existing failure (`ingest_sleeper_projections.py`, thread
  094, unrelated to this session's changes — confirmed by re-running on the unmodified main
  checkout), 3 passed
- `tests/test_ingest_ffc_adp.py`: 3 pre-existing failures, confirmed identical on the unmodified
  main checkout (`ingest_ffc_adp.py` untouched this session) — not caused by this work

## Files touched

- `tools/backfill_ffc_adp_history.py` — added PPR format
- `src/ingest_coordinators_wikipedia.py` — new
- `src/ingest_play_callers.py` — widened `play_callers` PRIMARY KEY
- `tests/test_backfill_ffc_adp_history.py`, `tests/test_ingest_coordinators_wikipedia.py` (new),
  `tests/test_holdout_audit.py`
- `docs/founder-requests/FR-072-*.md`, `FR-073-*.md`, `INDEX.md`
- `docs/handoffs/NEW-coordinator-final-staff-lookahead-semantics.md`
- `data/qa/ffc-adp-history-quarantine-ppr-2026-07-30.csv`,
  `data/qa/coordinator-quarantine-2026-07-30.csv`
- `data/adp-snapshots-ffc/2026-07-30_ppr_12team_period*.csv` (12 files)
