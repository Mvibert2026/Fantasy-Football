---
ID: 053
FROM: pm
TO: data-ops, strategist
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: FR-001 comparison view
---

## Ask

Ingest three founder-supplied CSVs. They are three different data types, not three copies of one, and
one of them enables something the project does not currently have.

Files land in `data/raw/founder-export/2026-07-27/`.

### 1. Underdog ADP — 407 players, real ADP with decimals

`Rank, Player, Pos, Team, ADP, Pos Rank`. Actual average draft position (`1.1`, `2.0`, `5.4`), which
is a genuine improvement on MFL's n=50 hobbyist sample.

**Carry this caveat in the schema, not just in a comment: it is best-ball ADP.** Underdog runs
best-ball, which has no waivers and no start/sit, so it systematically overvalues volatile
spike-week players and undervalues week-to-week consistency relative to redraft. It is also a
different roster shape from this league. Do not present it as redraft ADP, and do not blend it with
MFL's without recording that they measure different populations.

Store the source name on every row. `adp_source = 'underdog_bestball'`, not `adp = 1.1`.

### 2. FantasyPros ALL Rankings — 578 players, and it contains ADP implicitly

`RK, TIERS, PLAYER NAME, TEAM, POS, BYE WEEK, UPSIDE, BUST, SOS SEASON, ECR VS. ADP`.

`RK` is ECR. **`ECR VS. ADP` is populated for 566 of 579 rows**, so ADP is recoverable as
`ADP = RK − delta` (verify the sign convention against the Underdog file, where several players
overlap — that is a free cross-check).

Also here and not elsewhere: **`TIERS`** (15+ tiers, expert-assigned rather than derived), **bye
weeks**, and **strength of schedule** as a 1–5 star rating.

`UPSIDE` and `BUST` are placeholder strings ("Coach Upside rating") — the export did not include the
actual values. Ignore those two columns; do not parse them into anything.

### 3. Three-analyst rankings — 395 players, and this is the interesting one

`Player, Team, Position, Ratcliffe, Popielarz, Orginski, Consensus`. Three **individually named**
analysts plus a consensus.

**This gives the project something it has never had: a direct, external measure of expert
disagreement per player.** 265 players carry all three ranks. The spread between them is an
uncertainty signal derived from independent human judgement rather than from our own model.

The signal is real and large:

| | Spread | Ranks |
|---|---|---|
| Puka Nacua | **0** | 4, 4, 4 |
| De'Von Achane | **0** | 16, 16, 16 |
| Omarion Hampton | **14** | 12, 15, 26 |
| Saquon Barkley | **13** | 14, 27, 14 |

Three experts placing Nacua identically and disagreeing by 14 slots on Hampton is exactly the
distinction this product exists to surface. Store per-analyst ranks, not just the spread — the raw
values allow anything later; a pre-computed spread does not.

Handle missing ranks honestly: several players are ranked by only one or two analysts. `NULL`, never
zero, never imputed.

## For `strategist`

Two questions, and the first may be more valuable than anything else in these files.

**Is expert disagreement predictive of outcome variance?** If players with wide analyst spread also
show wider realised outcome variance, that is an externally-sourced uncertainty input — and it is
**testable on historical data** if analyst rankings can be obtained for prior seasons. It would let
the product say "the experts genuinely disagree about this player" as a fact rather than an
impression. Pre-register before testing.

**A caution the data already shows.** The widest disagreements are almost entirely **kickers and
defences** — Steelers DST spread 167, Cairo Santos 156, Jason Myers 155. That is not meaningful
uncertainty about football; it is three analysts not really ranking positions nobody drafts on merit.
Any disagreement metric must exclude or separately handle K and DST, or it will be dominated by noise
at positions the project has already declined to model.

## Done looks like

Three sources ingested with source attribution on every row, best-ball caveat in the schema, ADP
cross-check between files 1 and 2 reported, per-analyst ranks stored raw with honest nulls. Then a
`strategist` reply on whether the disagreement signal is worth pursuing and what would test it.

---
### pm · 2026-07-27

**This thread just became higher priority than originally scoped.** Thread 067 (T1 multi-league
consensus rescope) found that T1's live-data plan never actually worked — the FantasyPros live
API caps every response at 10 players (`docs/deferred.md`, known since 2026-07-25), and the
board currently runs on a shared, unscored, format-blind mirror for every league including the
primary one. File 2 in this thread's own ask (`FantasyPros ALL Rankings`, 575-579 rows, no cap)
is the actual fix, sitting unused.

**Scoring format confirmed:** founder had **Half PPR** selected on FantasyPros' site when
exporting this CSV. That matches both leagues currently in scope (Westwood is 0.5 PPR + yardage
bonuses; league 2 "Ethan's Expert League" is also 0.5 PPR, no bonuses) — the same ECR list should
serve both, since `scoring.py` applies each league's actual point rules downstream of the ranking
order. Founder can pull STD/PPR exports too if a later league needs them, but not right now
("the site is slow") — do not ask again, wait for it to be offered.

Recommend prioritizing file 2's ingestion (the ECR/tiers/bye/SOS data) ahead of files 1 and 3 if
time is constrained this session — it is the one that unblocks T1/board-correctness for both
current leagues; the Underdog ADP and 3-analyst disagreement files are valuable but not
draft-blocking the way file 2 is.

---
### data-ops · 2026-07-27

**File 2 done. Files 1 and 3 NOT attempted this session** — per the PM's own reprioritization,
time went entirely into file 2 plus its schema/quarantine work. Leaving them for a follow-up
session; they are not draft-blocking.

**Source file used:** `data/user pulled fantasy data/FantasyPros_2026_Draft_ALL_Rankings (1).csv`
(575 data rows). Note: a *different* partial pull of the same export
(`data/raw/founder-export/2026-07-27/fantasypros-all-rankings.csv`, staged by some earlier session,
timestamped 2026-07-26 21:39) already existed in the target directory with slightly different
`RK`/`ECR VS. ADP` values for at least two players (Jonathan Taylor / CeeDee Lamb rows 8-9 swapped
with different deltas) — it was not ingested and not deleted, just left alone; flagging in case
someone assumes it's authoritative. The file this thread named explicitly was used as source of
truth and copied to `data/raw/founder-export/2026-07-27/FantasyPros_2026_Draft_ALL_Rankings.csv`.

**Ingestion:** `src/ingest_fantasypros_csv.py` (new). `rankings` table extended with four new
columns (`scoring_format`, `tier`, `bye_week`, `sos_season`) via `ALTER TABLE ADD COLUMN` —
existing `fantasypros_ecr` rows get NULL in all four, harmless. New `rankings_quarantine` table
for unresolved rows.

- **Rows ingested: 465** into `rankings` as `source='fantasypros_csv_2026draft'`,
  `ranking_source='expert'`, `season=2026`, `as_of_date='2026-07-27'`, `scoring_format='half_ppr'`
  (founder-confirmed, stored as fact not assumption), `is_preseason_final=0`.
- **Rows quarantined: 110** into `rankings_quarantine`, all with reasons, none dropped silently:
  - 32 DST rows — no individual `gsis_id` exists for team defenses in nflreadpy's crosswalk by
    construction. Same permanent gap `src/ingest_rankings.py` already documents for the
    DynastyProcess mirror; not a defect of this file.
  - 78 skill/K rows — name+position not found in `nflreadpy.load_ff_playerids()`. Spot-checked a
    sample: mostly 2025 rookies (Jeremiyah Love, Carnell Tate, Jordyn Tyson, etc.) not yet present
    in the static crosswalk snapshot, plus a handful of legal-name-vs-nickname mismatches (e.g.
    "Hollywood Brown" vs. crosswalk's "Marquise Brown", "Chig Okonkwo" vs. "Chigoziem Okonkwo").
    Per CLAUDE.md, these were **not** fuzzy-matched — a human or a future crosswalk refresh should
    resolve them, not this ingestion guessing. Full list with reasons is in `rankings_quarantine`
    and printed by the script.
  - One label fix applied (not a guess): the CSV uses `K` for kickers, nflreadpy's crosswalk uses
    `PK` — mapped explicitly in code with a comment, this is a documented label difference, not an
    inference.
- **UPSIDE/BUST columns:** confirmed placeholder ("Coach Upside/Bust rating" in every row of this
  file) — not parsed, not stored, per this thread's instruction.
- **Source name chosen:** `fantasypros_csv_2026draft` — distinguishes from the existing
  `fantasypros_ecr` mirror (`PRAGMA table_info(rankings)` checked first; `source` values before
  this were `{'fantasypros_ecr'}`). Both now coexist.
- **ADP sign-convention finding:** `ADP = RK + delta`, where `delta` is the numeric value of
  `ECR VS. ADP` (e.g. `+2` → `-2`, `0`, or blank/`-` → NULL). Verified by cross-checking direction
  (not magnitude — different platforms, not expected to match exactly) against
  `data/raw/founder-export/2026-07-27/underdog-adp.csv` on 4 overlapping players: positive delta
  consistently meant the player's Underdog ADP rank was *later* (worse) than their FantasyPros ECR
  rank, negative meant *earlier*. Full worked table is in the script's module docstring
  (`src/ingest_fantasypros_csv.py`). This is inference from a same-day external file, not a
  documented FantasyPros convention — flag if it needs re-verification later.
- **`ECR VS. ADP` population:** 327/575 rows in this specific CSV, not 566/579 — that figure in
  this thread's opening ask appears to be from a different pull of the file (the founder's original
  579-row count doesn't match this file's 575 rows either). Not investigated further; recorded as
  observed, not corrected to match the expected figure.
- **Board builder:** NOT rewired. `make_board.py` still reads whatever it currently reads (not
  audited in depth this session) — per this thread's scope boundary, that call belongs to backend
  via thread 067, flagged there as an open item rather than changed here.
- **Tests:** `tests/test_ingest_fantasypros_csv.py` (new), 7 tests, all passing — covers the
  parsing helpers (position-rank stripping, SOS star parsing, name normalization), the RK+delta ADP
  sign convention with the same worked example as the docstring, and schema/quarantine-table
  idempotent creation. Full-suite run was in progress at session end; will report count separately
  if it finishes before handoff.
- **Commit:** not committed this session (see reply for hash if/when committed).

`docs/CURRENT-STATE.md` updated in place with a summary of this ingestion.

Leaving `STATUS: OPEN` — strategist's file-3 disagreement-signal analysis and files 1/3 ingestion
are both still outstanding on this thread.

---
### pm · 2026-07-27 (sequencing directive from founder)

**Founder, directly, in a Claude Code session:** *"Do not rewire make_board.py yet. Fix the
crosswalk first. 78 skill players from the Half-PPR CSV failed to resolve, including 2026 rookies
who may go in the first few rounds. Rewiring the board onto the new source before those resolve
makes them invisible — worse than the wrong-format board they'd replace, because a missing player
gives no signal at all."* Full entry: [[FR-015]] in `founder-requests.md`.

**Sequence, binding on this thread and 067:**
1. `data-ops` refreshes the crosswalk against the 78 unresolved skill/K rows in
   `rankings_quarantine` (`source='fantasypros_csv_2026draft'`). **No silent fuzzy matching** — any
   fuzzy match must be gated at a stated threshold and every match logged. Report anything still
   unresolved by name, don't drop it.
2. Only then does `backend` rewire `make_board.py` onto `fantasypros_csv_2026draft` (thread 067's
   open item).
3. Rebuild and confirm: total player count, 2026 rookie class present, app header shows the new
   source/scoring format.

The 32 quarantined DST rows are **structural, not a bug** (no individual `gsis_id` for team
defenses, by construction) — leave them quarantined, out of scope for this fix.

Dispatching `data-ops` for step 1 now.

---


## data-ops reply — 2026-07-27 — FR-015 crosswalk refresh (skill/K quarantine only)

**Scope:** founder directive FR-015 (`docs/founder-requests.md`) — resolve the 78 skill/K rows
quarantined by `src/ingest_fantasypros_csv.py`'s first run (name/position not found in
`nflreadpy.load_ff_playerids()`). `make_board.py` was **not** touched, per explicit instruction.

**Root cause.** `load_ff_playerids()` is a static snapshot that hadn't picked up most 2026
draft-class rookies yet. `nflreadpy.load_players()` (a different, more frequently refreshed
nflreadpy source) already carries real `gsis_id`s for the same players — confirmed by direct
lookup (e.g. Jeremiyah Love `00-0041027`, Carnell Tate `00-0041438`, Jordyn Tyson `00-0041029`,
all absent from `ff_playerids`, all present in `load_players()`).

**Fix, `src/ingest_fantasypros_csv.py::build_crosswalk()`:**
1. Layered `load_players()` on top of `load_ff_playerids()` as a second exact-match source
   (`ff_playerids` keeps priority when both have an entry). Fixed 72/79 skill/K quarantine rows.
2. Also indexed each player's `football_name` (nickname/short form field, e.g. "Mitch" for
   "Mitchell Tinsley") against the same `gsis_id` — an exact match against a real nflverse field,
   not fuzzy matching. Fixed "Mitch Tinsley" (RK 453).
3. `load_players()` labels kickers `"K"` natively; `ff_playerids`-era code expects `"PK"`. Both
   position keys are populated from `load_players()` rows so kicker lookups work either way
   (fixed Andy Borregales RK 228, Trey Smack RK 378 — both actually resolved in step 1 already
   since `load_players()` also had them under the RB/WR/TE keys they needed... note: both are `K`,
   resolved via the K/PK dual-key logic).
4. Added one hand-verified, explicitly logged alias — **not fuzzy matching, a single curated
   entry checked against public reporting**: `("hollywood brown", "WR") -> "marquise brown"`.
   Marquise Brown's own adopted nickname is not present under any spelling in either nflreadpy
   name field, so no exact-field fix was possible. Logged at ingest time
   (`[alias] 'Hollywood Brown' (WR) -> 'marquise brown' via _KNOWN_ALIASES -> gsis_id=00-0035662`).
   No other aliases were added — every other quarantine row was resolved via an exact field
   match or is reported below as still unresolved.

**Before / after (this run, `source='fantasypros_csv_2026draft'`, `season=2026`,
`as_of_date='2026-07-27'`):**

| | Before | After |
|---|---|---|
| Rows ingested into `rankings` | 465 / 575 | 539 / 575 |
| Rows quarantined | 110 | 36 |
| — DST (structural, out of scope) | 32 | 32 |
| — skill/K unresolved | 78 | 5 |

**Still unresolved, named individually (not dropped, still quarantined with reason
`"name/position not found in nflreadpy ff_playerids crosswalk"`):**

- Tommy Myers (FA, TE) — RK 389. No player under any spelling of "Myers" in `load_ff_playerids()`,
  `load_players()`, or the 2025 `load_rosters()` snapshot at TE.
- Devonte Boyd (FA, WR) — RK 467. No "Devonte Boyd" in any of the three sources checked.
- Matt Hibner (BAL, TE) — RK 493. A "Matthew Hibner" (`00-0040879`, BAL, TE) exists and is
  almost certainly the same person, but `football_name` for that record is "Matthew", not "Matt"
  — the CSV's short form isn't backed by any exact field, so this was left unresolved rather than
  guessed. Flagging for founder/backend judgment call: fuzzy-match "Matt"↔"Matthew" explicitly,
  or add as a second hand-verified alias if confirmed.
- Graig Cooper (FA, RB) — RK 520. No "Graig Cooper" in any of the three sources checked
  (nearest name-match, "Craig Cooper", also absent).
- Desmond Reid (FA, RB) — RK 565. No "Desmond Reid" in any of the three sources checked.

All five are almost certainly undrafted 2026 rookies not yet on any 53-man roster snapshot
nflreadpy has picked up (no 2025 `load_rosters()` entry either) — genuinely absent from every
source checked, not a normalization gap. Re-check once rosters update closer to Week 1.

**Files changed:** `src/ingest_fantasypros_csv.py` (`build_crosswalk()`, `_KNOWN_ALIASES`, alias
lookup + logging in `ingest()`), `tests/test_ingest_fantasypros_csv.py` (4 new tests: load_players
fallback, football_name nickname indexing, K/PK dual-key, alias table entry).

**Tests:** `pytest tests/ -k "ranking or crosswalk or fantasypros"` → 34 passed. Full suite
(`pytest -q`) → 604 passed, 1 failed. The 1 failure (`test_handoffs.py::test_mailbox_health`,
duplicate handoff ID 066 between `066-recurring-injury-suspension-feed.md` and
`066-contract-1-10-0-board-json-rows-gained-roster-st.md`) predates this session (both files
already existed, untracked, before this task started) and is unrelated to the crosswalk work —
flagging, not fixing, since it's outside this task's scope.

`make_board.py` rewire remains blocked pending backend pickup, per FR-015. This reply resolves the
crosswalk half of that block for skill/K players; the 5 named above and the 32 DST rows remain
quarantined by design/absence, not by oversight.

---

## backend reply — 2026-07-27 — FR-015 steps 2+3: make_board.py rewired, boards rebuilt (ADR-051)

**Scope:** steps 2 (rewire `make_board.py`) and 3 (rebuild + confirm) of FR-015, per the founder's
own sequencing ("do not rewire make_board.py yet... then rewire... then rebuild"). Step 1
(crosswalk) confirmed done by data-ops above, not touched.

**Rewire, `src/make_board.py`:** `SOURCE` (the live/display consensus board) moved from
`fantasypros_ecr` to `fantasypros_csv_2026draft`. **Not a straight swap** — the new CSV source has
no historical seasons (2026 only), but the rank->points curve that drives `projected_points`/`vbd`
needs multiple prior seasons to fit against. Swapping the training data too would have silently
emptied the board (every position's curve fit starves for lack of >=5 observations, with no error
raised). Introduced a second constant, `TRAINING_SOURCE = "fantasypros_ecr"`, kept on the
historical mirror; `_consensus_board`/`collect_observations`/`resolve_training_seasons`/
`build_board`/`board_as_ranking` all gained an explicit `source` param so every call site is
deliberate about which one it means. `board_ranking_for_season` (the backtest baseline arm, which
runs over historical seasons that only exist under `TRAINING_SOURCE`) now pins to
`TRAINING_SOURCE` explicitly rather than inheriting whatever `SOURCE` happens to be. Full
reasoning in ADR-051 (`docs/decisions.md`).

Also fixed a latent bug independent of the `SOURCE` rewire: `export_contract.py`'s `team_of`/
`positional_rank` lookup was hardcoded to the literal string `'fantasypros_ecr'` rather than
following `make_board.SOURCE` — would have desynced team/positional-rank display from the actual
board player set the moment `SOURCE` changed. Now reads `make_board.SOURCE`.

**`export_contract.py`:** `board_source`/`consensus_source` updated to name
`fantasypros_csv_2026draft`. New top-level `board.json` field `scoring_format` (read from
`rankings.scoring_format`, not hardcoded — `"half_ppr"` today), plus `scoring_format_note`.
`CONTRACT_VERSION` bumped **1.10.0 -> 1.11.0**. Handoff thread 069 opened to `frontend` (schema
change + the header needs a `scoring_format` field it doesn't have yet).

**Rebuilt and confirmed (2026-07-27):**

| | Old (`fantasypros_ecr`) | New (`fantasypros_csv_2026draft`) |
|---|---|---|
| Primary ("Westwood") board player count | 378 | **511** |
| `ethans_expert_league` board player count | (not rebuilt this session before now) | **511** |
| `board_source` | `fantasypros_ecr re-scored...` | `fantasypros_csv_2026draft re-scored...` |
| `consensus_source` | `fantasypros_ecr` | `fantasypros_csv_2026draft` |
| `scoring_format` (new field) | (did not exist) | `half_ppr` |
| `contract_version` | 1.10.0 | 1.11.0 |

Player count went 378 -> 511 (up 133), consistent with the new source resolving 539/575 CSV rows
vs. the old source's 408 rows for season 2026 — both filtered down by the board's own QB/RB/WR/TE
scope (no K/DEF, ADR-039/041) and `RELEVANT_DEPTH` caps, so 511 != 539 is expected, not a
discrepancy.

**2026 rookie class confirmed present on the rebuilt board, real ranks (not just in `rankings`):**
Jeremiyah Love #33 overall, Carnell Tate #70, Jordyn Tyson #84 (`data/export/board.json`).

**App header:** `frontend/ui/views/Board.tsx:176` already renders `data.board.consensus_source`
directly — the exported field now reads `fantasypros_csv_2026draft`, so the string that reaches
the header changed with no frontend code change required. `scoring_format` is a genuinely new
field with no frontend type or display yet (thread 069) — **visual verification of the header is
pending frontend's pickup of that thread**, not confirmed by screenshot this session.

**T3 bye-week regression check:** re-ran the floor check manually against the rebuilt board — 0
players with a real team code and a null bye week (no regression from the rewire).

**Tests:** `tests/test_make_board.py` gained 2 tests pinning `SOURCE`/`TRAINING_SOURCE` to their
literal values; 4 existing fixture-backed tests updated to pass `source=make_board.TRAINING_SOURCE`
explicitly (the shared fixture only seeds `fantasypros_ecr` rows, and the module default changed
out from under them). `tests/test_rosters_export.py::test_contract_version_bumped` updated to
1.11.0. `tests/test_holdout_audit.py`'s `CONNECT_ALLOWLIST` gained `ingest_fantasypros_csv.py`
(mechanical — it's the same shape of ingestion script as the other allowlisted `ingest_*.py`
files; this was a gap left by the earlier data-ops session, not part of this rewire). Full suite:
**603 passed, 1 failed** — the failure is the pre-existing, already-flagged
`test_handoffs.py::test_mailbox_health` (duplicate handoff ID 066), unrelated to this work, not
fixed per the standing instruction not to touch it.

**Files changed:** `src/make_board.py`, `src/export_contract.py`, `tests/test_make_board.py`,
`tests/test_rosters_export.py`, `tests/test_holdout_audit.py`, `docs/decisions.md` (ADR-051),
`data/export/board.json` + `data/export/{availability,league,rosters,glossary,nulls,opponents}.json`
+ `data/export/ethans_expert_league/{board,availability,league,rosters}.json` (all regenerated).

FR-015 steps 2 and 3 are done. Step 3's "app header" confirmation is data-confirmed but not
visually screenshot-confirmed — see thread 069.
