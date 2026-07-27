# CURRENT STATE

**This file is the canonical answer to "where is the project right now."**
It is edited **in place**. When something changes, replace the affected line — never append a new
section, never leave the old value "for contrast." If you find yourself adding a second version of
a number that already appears here, you are doing it wrong.

`docs/SNAPSHOT-*.md` files are frozen point-in-time captures, not rivals to this file — they drift
the moment this file changes and this file always wins.

Do **not** read `docs/status.md` to answer a current-state question. That file is an append-only
session log and contains superseded figures presented in the same voice as current ones. Same
hazard `docs/assistant-context.md` warns about for `decisions.md`. It is fine to read `status.md`
to learn *what happened*; it is not fine to read it to learn *what is true*.

**Last verified:** 2026-07-27, sprint-closeout session (main @ `cf5935e`, post-merge with
`origin/main`) — build-state table below is measured directly from `git rev-parse HEAD`, real
backend/frontend full-suite runs, `CONTRACT_VERSION` in `src/export_contract.py`, and
`tools/handoffs.py check`. `CONTRACT_VERSION` is **1.11.0** (ADR-051: `board.json` gained
top-level `scoring_format`; `board_source`/`consensus_source` now name
`fantasypros_csv_2026draft`; ADR-050: `board.json` gained `roster_status`, contract 1.10.0).
Primary board and `ethans_expert_league` both rebuilt at 511 players; 2026 rookies confirmed
present with real ranks (Jeremiyah Love #33, Carnell Tate #70, Jordyn Tyson #84). Half-PPR yardage
bonuses independently verified to stack against the live Yahoo platform (ADR-052) — see §7 of
`CLAUDE.md`. Handoff thread 069 (scoring_format display) and the trace-field-registry gate (below)
are both still open to `frontend`, not touched this session.

---

## Build state

| | Value | Notes |
|---|---|---|
| Backend branch / commit | `main`, `cf5935ef4bd3d79e8b51b480a207fb4b622f0cf3` | Pushed, in sync with `origin/main` (remote: `github.com/Mvibert2026/Fantasy-Football`) |
| Backend tests | **607 passing, 0 failures** | Full suite, `pytest tests/ -q`, single run, ~417s, real `data/nfl.db`. |
| Agent infrastructure | **Live** | Six subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`) — **72 threads, 46 open, 0 stale** (`tools/handoffs.py check`, 2026-07-27) |
| Data contract | **1.11.0** | `CONTRACT_VERSION` in `src/export_contract.py`, read directly. `board.json` carries `scoring_format` (ADR-051) and `roster_status` (ADR-050). |
| Frontend location | `frontend/` subdirectory of this repo | Merged from `frontend-prep` via `git subtree add`, full history preserved. No longer a separate working copy. |
| Frontend tests | **179 passing, 2 failing** (19 files) | Full suite, `npx vitest run`, single run, ~55s. The 2 failures are `ui/__tests__/trace-fields.test.ts` — **red by design**: `TRACE_CONTRACT` is still pinned to `1.9.0` and the trace registry doesn't know `roster_status` yet, correctly catching that nobody has acknowledged the 1.10.0/1.11.0 contract bumps in the frontend's own field registry. Not fixed here — frontend's to pick up (handoff 069 territory). |
| Python modules | **36** in `src/` | `ls src/*.py \| wc -l` |
| Export artifacts | **11** top-level files in `data/export/` | `ls data/export/*.json \| wc -l` |
| Config matrix | 26 dirs under `data/export/` | board + league + availability stub only; **hazard model not rerun per config**; count is a raw directory count, not inspected for which are real league configs vs. scratch. The 26th is `ethans_expert_league` (real league 2, see below), not a scratch probe config. |

## Statistical constants in force

| Constant | Value | Standing |
|---|---|---|
| `DEFAULT_LAMBDA` (roster-need weight) | **0.352** | Measured — 2025 real draft, n=160 / 10 clusters, clustered SE 0.070, z=5.04. One season, one draft. Keep the caveat attached. |
| `delta` (positional-run weight) | **0.10** | **D-004, defaulted:** keep at 0.10, visibly flagged as an unvalidated prior, honouring the pre-registered rule — if need+run does not beat marginal-only on Brier across ≥30 conforming mocks, `delta` goes to zero automatically. Not re-verified against code this pass. |
| `NEED_ADJUSTMENT_SCALE` | **D-001, decided: delete** | Founder decided 2026-07-27 to delete this parameter outright — do not adopt 10.0, do not fit a value. This is what the decision says; whether the code has been updated to match was **not checked this pass** (out of this session's narrowed scope). |
| Replacement levels | RB30 / WR40 / TE10 / QB10 | Measured over 26 seasons under this league's rules. TE10 is the solid part; RB/WR split moves ±1 rank by year selection. |
| DEF replacement level | **None, permanently** | No DST scoring ingested. Declared in `league.json`, not an oversight. |

## Decisions applied from `docs/decisions-needed.md` (this pass, narrow set only)

Recorded as what each decision *says*, not verified against implementation:

- **D-001** — delete `NEED_ADJUSTMENT_SCALE`. Do not adopt or tune a value.
- **D-003** — show rank numbers at TE/QB/DEF, but the unproven-ordering status must be structural
  (a visibly distinct treatment on the rank number itself, not a footnote) — founder departed from
  the rigorous tiers-only default. Re-evaluate when per-position n rises materially above ~20.
- **D-004** — see Statistical constants above.
- **D-006** — **CLOSED.** `nfl.db` is not tracked in git, `.gitignore` covers it. No history rewrite
  needed.
- **D-013** — **MOOT.** Single-user tool; the founder is the only league-settings editor. Reopens on
  any second user.
- **D-015 / D-016** — harvested drafts (e.g. FFC) and the founder's own drafts are both counted
  toward calibration, but reported as two separate numbers, tagged by population, and **never
  blended**. Other users' mocks are stored in the harvested pool, never silently merged into the
  personal pool.
- **D-020** — **CLOSED — no FantasyPros licence needed.** The product is private, personal, and
  displayed to nobody but the founder. Reopens on any second user, alongside D-021.
- **D-021** — **DECIDED — loosened.** Founder authorised harvesting Fantasy Football Calculator ADP
  history back to 2007 for private use, via the HTML endpoints (not the robots-disallowed CSV path),
  rate-limited, cached, pulled once per season-format. Void if the product ever ships to a second
  human.

No other entries in `decisions-needed.md` were applied this pass — this list is deliberately
narrower than earlier attempts at a full sweep.

**League 2 ("Ethan's Expert League", Yahoo 834236) — config + board built, 2026-07-27
(handoff 067, data-ops piece); teams corrected to 10 same day (pm reply, founder override).**
Real `LeagueConfig` at `data/leagues/ethans_expert_league.json` (**10 teams — founder directive,
overriding the screenshot's "Max Teams: 12," which was transcribed correctly but reflects the
platform's configured slot count, not expected real participants; do not revert to 12 by
re-reading the screenshot**; no yardage bonuses, INT -1, K starter slot, 1 FLEX). Board exported
to `data/export/ethans_expert_league/`, its own measured replacement levels
(`QB10/RB25/WR35/TE10` — distinct from both the primary league's `QB10/RB30/WR40/TE10` and the
earlier, now-superseded 12-team build's `QB12/RB30/WR42/TE12`), K and DEF correctly excluded from
ranking (ADR-039 filter). Rebuilt via `scripts/rebuild_ethans_expert_league.py`. 6 tests in
`tests/test_league2_ethans_expert.py`, all passing. `user_draft_slot=1` is an unresolved
placeholder — founder has not supplied their actual slot in this league.

**Consensus-pull format-awareness — partially unblocked 2026-07-27 (handoff 053).** The live-API
plan above is still dead (10-player cap, unfixed). But the founder manually downloaded a full,
uncapped, browser-side FantasyPros export with **Half PPR confirmed selected at export time** —
575 players, no cap. Ingested via `src/ingest_fantasypros_csv.py` into `rankings` as
`source='fantasypros_csv_2026draft'` (kept separate from the existing `fantasypros_ecr` mirror,
which still has zero format info — both coexist during the transition). `rankings` gained four
columns (`scoring_format`, `tier`, `bye_week`, `sos_season`); a new `rankings_quarantine` table
holds unresolved rows with reasons. **465 of 575 rows ingested, 110 quarantined** (32 DST — no
individual gsis_id by construction, same permanent gap `fantasypros_ecr` already documents; 78
skill/K players — mostly 2025 rookies not yet in nflreadpy's static id crosswalk, plus a handful of
nickname-vs-legal-name mismatches like "Hollywood Brown"/Marquise Brown that were correctly left
unresolved rather than fuzzy-matched). ADP is recovered as `ADP = RK + delta` where `delta` is the
CSV's `ECR VS. ADP` column (populated on 327/575 rows in this pull, not the 566/579 the founder's
original file showed — the two counts are from different pulls); sign convention was inferred by
direction-matching against the same-day Underdog ADP pull, not documented by FantasyPros — see the
module docstring for the worked cross-check. **`make_board.py` has NOT been rewired to consume
this source** — that is a board-builder decision left open for backend/thread 067, not done here.
Full detail: handoff 053's 2026-07-27 data-ops reply.

Still true, unrelated to this fix: no per-league-2 format pull exists either, and the live API
remains capped. Open decision for founder/backend unchanged: pay for a FantasyPros paid tier, or
find another half-PPR-native *live* source, if a fresher-than-one-time CSV pull is ever needed.

**T2 — CLOSED, 2026-07-27 (ADR-052).** CLAUDE.md §7's "verify against live league settings"
caveat is resolved: the primary league ("Westwood", Yahoo, 10 teams) scoring table matches
CLAUDE.md §7 / `scoring.py`'s `LEAGUE` value-for-value, yardage bonuses confirmed to stack, and
team count / roster shape (1 QB/3 WR/2 RB/1 TE/2 FLEX/1 DEF, 6 bench, 1 IR) are now known. Fixture
at `tests/fixtures/league_scoring_live.json`. Two DEF-side discrepancies found and flagged (not
fixed, DEF scoring has no consumer) — see ADR-052.

## Validation status — read this before quoting the product's core claim

The signature claim is **calibrated availability**. It is currently **not calibrated**.
**1 of ~30** required mock drafts is logged (and that one is the real 2025 draft, `is_mock=0`).
Until that number moves, availability output is an honest estimate, not a validated probability.
This is a data-volume fact, not a defect, and stating it plainly is required by Principle #2.

Mock-logging contamination control is **specified and must land before the first logged pick**
(ADR-D, thread 034): entry shortlist ordered by frozen board rank with no probabilities shown, a
seeded block-randomised blind arm of 10 of 30, `entry_mode`/dwell instrumentation, and a matcher
forbidden from consulting model output. Retrofitting discards mocks, so this precedes collection.
The realistic precision at 30 mocks is **±8 to ±10 points**, not the ±6 currently on the Mock Lab
screen — Wilson ignores intra-mock correlation. Absolute calibration will rest on the 10 blind mocks
(≈±14) because the sighted arm's absolute number is not contamination-free.

**Alpha detection: CONTESTED between ~2028 and ~2029 in the docs.** `docs/CURRENT-STATE.md`
(previously) and `docs/dashboard.html` say ~2028 (ADR-026). `docs/decisions-needed.md` (D-001) and
`docs/adr-drafts/ADR-A-need-adjustment-scale.md` say ~2029. Both cite a sign-test-floor /
multiple-comparisons argument over consensus-history seasons, but the two documents were not
compared closely enough this pass to state with confidence whether they are the same claim at
different correction stringency or two different claims — flagging as `CONTESTED` per this
session's instruction to not sink real effort into resolving it. **Do not treat either figure as
settled until a session with the digging in scope confirms one.**

## Built and working

**Last verified 2026-07-26 — not re-verified, EXCEPT the four bullets below (2026-07-27, ADR-050,
this session, directly measured).**

**T9 team-code crosswalk** (`src/team_codes.py`) — fixed the live JAC/LAR (FantasyPros) vs JAX/LA
(nflverse) bye-week gap; `tests/test_floor_checks.py::test_t3_every_board_player_has_a_bye_week`
went from measured-red (22 players, live symptom) to green by wiring the crosswalk into
`export_contract.py`'s bye lookup and regenerating `board.json`, no other change.

**T5 freshness tripwire — RE-VERIFIED end-to-end, 2026-07-27 (ADR-053), no gap found.**
`export_contract.build_board_json` calls `fr.require_fresh(...)` unconditionally
(`enforce_freshness=True` default) before every board build, via the single shared `write_all`
path every league config uses — there is no per-league way around it. Previously only the pure
`freshness.py` functions had test coverage; added `tests/test_freshness.py::
TestBoardBuildActuallyRefuses` (2 tests, `@pytest.mark.requires_db`) proving the real entrypoint
against the real `data/nfl.db` actually raises `StaleSnapshotError` when forced stale, and does
NOT raise on the real (actually-fresh) snapshot. No code change needed — this was already solid.

**T6 interim roster-status proxy** (`src/roster_status.py`) — spot-checked 2026-07-27, unchanged,
still passing (6 tests incl. the Tom Brady case). `board.json` rows carry `roster_status`, derived
from the pre-existing `contracts.is_active` column; explicitly labeled a proxy, not a real
active/IR/PS feed (that needs new ingestion, out of scope this round).

**T4 interim suspension mechanism — WIRED INTO THE LIVE BOARD, 2026-07-27 (ADR-053, thread 057
reply).** `src/suspensions.py`'s deterministic games-adjustment (no probability model) is now
called from `export_contract.build_board_json` for every league config via `write_all`, reading a
new real, hand-curated list at `data/suspensions_2026.json` (`as_of_date: 2026-07-27`,
WebSearch/WebFetch-sourced, `sources_checked` cited in the file). That list is **currently empty**
— an exhaustive research pass found no confirmed, current, unserved, skill-position (QB/RB/WR/TE)
2026 suspension (the one real 2026 suspension found, Charles Snowden/DE, has zero board
consequence since this league has no individual defensive-player scoring at all, ADR-039); per
project rule, nothing was fabricated to fill the gap. Every board row still emits the four
suspension fields unconditionally (`suspension_flag: false` today, correctly, not silently
absent). Synthetic fixture (`tests/fixtures/suspensions_2026.json`) is unchanged and still tests
the mechanism itself. Contract version bumped 1.11.0 → 1.12.0 for the four new fields
(`suspension_flag`/`suspension_games`/`projected_points_suspension_adjusted`/
`suspension_adjustment_note`); handoff thread 073 opened to frontend. Thread 057 (data source
research) remains open — this closed the narrower "not wired in" gap, not the fuller structured-
source design its §4 reply proposed.

Board + VBD with format-corrected replacement levels · identity hub (`mfl_id`) with quarantine ·
live-availability hazard model · need-weighted `strategy_balanced` · mock-draft ingestion and
validation report · archetype assignment and display-only descriptions · multi-league config and
export routing · 24-config board matrix · deterministic narration Facts layer · FantasyPros ECR
preseason rankings 2021–2025 (`rankings` table, `is_preseason_final` flagged) · historical injury
reports 2010–2024 with enforced `as_of_date` (`injuries` table, `src/ingest_reference.py`; 2009
mostly undated at the source and dropped, 2025 has no `date_modified` column upstream yet) ·
**Opponents tab** (built this sprint, verified rendering live this session — thread 038/041;
`rosters.json`/`opponents.json`-backed, honest "not supplied"/"partial"/empty-roster null states,
5/5 tests passing) · league rosters export (`rosters.json`, mechanical starters/flex/bench/needs
from real draft picks on file; currently all-empty because the real 2026 draft hasn't started,
which is the correct state, not a bug) · **Mock Lab live-logging store** (`src/mock_lab_store.py`,
thread 025, ADR-046: `mocklab_drafts`/`mocklab_picks`, pick-at-a-time create/append/undo/close,
event-sourced per the thread 040 amendment — undo truncates and replays, no voided records, no
undo count; predictions derived on demand and guarded by a `model_version` pin, not stored;
Brier/calibration scoring built over an unfitted rank-decay baseline pending the real hazard model
being wired for arbitrary slots — see ADR-046 gap note; no UI, no export artifact yet) ·
**ADR-C pre-registration convention** (thread 020, `src/preregistration.py`/`src/holdout.py`,
additive to the original PR-001..003 mechanism): nine-field confirmatory / four-field exploratory
registration format, the data_seen-amendment-irreversibly-demotes-to-exploratory rule, content-hash
integrity checking, family manifests fixing the BH denominator, and `holdout.load_season(year,
prereg_id)` tying season reads to a registration's declared scope with a signed-unseal-log
requirement on top of the front-matter flag. **Not yet enforced at any entrypoint** — the `prereg`
CLI/pre-commit gate and the PR-001..003 retrofit are deferred, see thread 020 reply.

**Weekly finishes / season stats exports** (thread 017/039, `src/export_history.py`, contract
1.9.0): `data/export/weekly_finishes.json` + `data/export/season_stats.json`, real
`player_weekly_stats` data, 1481-player universe (`season >= 2018` at QB/RB/WR/TE), 2003-2008
target-derived fields explicitly `target_data_unavailable: true`/`targets: null` rather than
zeroed. **Join key fixed 2026-07-27 (thread 052, ADR-048):** `board.json`'s `player_id_gsis` was
hardcoded `null`; now populated from `rankings.player_id` (already a gsis id) threaded through
`make_board.BoardRow.player_id`. **378/378 board players carry it; 371/378 (98.15%) resolve
against `weekly_finishes.json`** (the ~7 misses are players with no `player_weekly_stats` history
at all — an honest null, not a join failure). No `CONTRACT_VERSION` bump — the field already
existed in the schema, only its value changed. Still not wired into `PlayerDetail.tsx`'s
consistency heat-map / three-seasons section — that is frontend's remaining half of thread 052 —
but the join key that blocked it now exists and is measured.

**DraftRoom pick-entry TypeAhead + availability presentation** (thread 029 retargeted off
`Board.tsx`, thread 037 item 1, RETROFIT-5/thread 036): `DraftRoom.tsx`'s available-player rows now
carry the same 10-dot frequency array as the player detail sheet / Availability Explorer, and rows
group under `TIER N — M players left` headers (restricted to a single position tab, since
`tier_label` is per-position — mixing under `ALL` would merge unrelated tiers sharing a label); row
height verified unchanged by live measurement. Pick entry backported from the Mock Lab
design-reference mockup (there is no Mock Lab application code — its UI remains unbuilt, only the
backend store above): digits 1-5 commit a shortlisted candidate directly, Backspace on an empty
field undoes the last pick, autofocus re-asserted on every input-node attach (not a one-shot guard),
default shortlist is the top 5 available by real board rank shuffled per pick (no fabricated
"predicted next pick" probability — this codebase has no model for that target), and every pick now
records `entryMode` (`'shortcut' | 'typed' | 'pasted'`), exported through `toDraftLog`. Deliberately
a smaller vocabulary than ADR-D's `mock_picks.entry_mode` (Status: Proposed, Mock-Lab-scoped) — not
yet reconciled with it; flagged in the thread 036 reply as needing deliberate resolution before
DraftRoom's exported log is treated as calibration input. `lib/format.ts::percent()`'s `<1%` branch
(thread 037 item 1) was already shipped in `09391e4`; this session only added the literal test case
the thread asked for and closed the reply loop. None of this is screenshot-verified — verified via
live DOM/state measurement in a real (non-screenshotting) browser session instead; see thread
replies for detail.

**Thread 063 (regression of 051), resolved:** the suggester was reopening on every commit. Root
cause was `recordPick`'s post-commit refocus call (kept deliberately, for fast keyboard re-entry)
going through the same `onFocus` handler as a real click with no suppression flag set for that
specific call site — 051 only guarded the mount/remount autofocus call, not this one. Fixed via a
shared `refocusSearchWithoutOpening` helper used at both programmatic-focus call sites, plus an
explicit `setSuggesterOpen(false)` on every commit. A second, related defect (a real click on the
field silently failed to open the panel on the very first click after page load, since mount
autofocus already held focus and a browser fires no `focus` event from clicking an
already-focused element) was found via the project's own `frontend/e2e/smoke.mjs` Playwright
harness and fixed with an explicit `onMouseDown` handler. `npm run smoke`: 16/16. Screenshot at
`frontend/e2e/artifacts/draftroom.png`, real Chromium capture. See the thread 063 reply for the
full root-cause narrative.

**Draft board design-gap sections A/B/C, partial D/E/F** (thread 058, branch
`frontend/058-draft-board-design-gap`, scoped away from thread 063's pick-entry/suggester
territory in the same file): Position Scarcity's `+2`/`±0` pace is now a legible phrase
(`"2 ahead of pace"` / `"on pace"` / `"1 behind pace"`), plus a per-position tier-depletion line
(`tier 1 gone · tier 2: 1 left`) and an `N <50% by <pick>` line, DEF added as a fifth row rendering
`board.json:def_note` verbatim (ADR-039 — no fabricated 0/±0 since there is no DEF board data at
all), positions ordered by urgency (`scarcity.ts::orderByUrgency`, this session's own tie-break rule,
not spec-mandated), and a `board.position_remaining · board.position_tier · pace vs
board.consensus_rank` footer. Board rows now show `board.json:positional_label` (`WR12`, already a
real field) instead of bare position; explicit SORT controls (Our rank / Consensus / Delta / Proj
pts) added and applied before tier-banding; DEF added to the position filter with an honest empty
state. Hub tabs (`Board`/`Opponents`/`Predictions`) restyled sentence-case/boxed per the design's own
markup; a `DRAFT LIVE` badge added to the top bar; league identity string extended with real
`platform`/`draft_type` fields (both newly typed in `league.ts`/`types.ts`); the assistant dock
(already mounted on this screen pre-thread) now reports `pick N` context. IR slot added to the roster
list sized from the real `league.json:roster.ir` (never auto-filled — no injury data exists to decide
what belongs there); roster requirement chips restyled as bordered boxes; a matching traceability
footer added to the Queue/Watchlist panel. **Audit findings, not built:** the design's ALL-tab tier
grouping mixes positions under one header using a `gtier` field the prototype computes via its own
VBD-gap clustering (~4.5pt gap, min bucket 2, max 9) — real backend export has no equivalent
`global_tier` field, and fabricating one client-side would be an invented statistical judgment, so
board banding stays position-scoped (already correct pre-thread); the design's "CURRENT" league badge
turned out to be the §5.1 sim-staleness state (no `sim_generated_at`/`sim_settings_hash` in this
export), not a multi-league marker, and isn't buildable without those backend fields. Full detail and
corrections to the thread's reading in the thread 058 reply. (Frontend test count for this thread
alone was 172, measured before 063 was merged in — see Build state above for the real, current
post-merge count.)

## Not built / null-stated

Predictions tab (**absent from the shipped app**) · Season mode entirely · Settings editor ·
Mock Lab UI (backend store now exists, thread 025 — see Built and working) · Compare tray ·
league creation / real multi-league slot support (thread 040 item 1, open) · live "Ask the
assistant" wiring · LLM prose renderer
(deliberately deferred — hallucination risk, reasoning stated in code) · `RB_HANDCUFF` archetype
(depth charts end 2024) · recompute progress streaming.

## Top open items

1. **Per-pick draft-state logging + ADR-D contamination instrumentation** — must land *before* mock
   collection begins, or the mocks collected cannot validate `delta` no matter how many there are,
   and cannot be defended against shortcut bias at all.
2. **ADP snapshot capture** — unrecoverable if delayed; a past date's snapshot cannot be backfilled.
3. **Mock drafts toward n=30** — gates the pre-registered availability decision rule.
4. **FantasyPros licence decision — CLOSED (D-020).** No licence needed while the product stays
   private/personal/founder-only. Reopens on any second user, alongside D-021.
5. **`strategies.json` re-export** — stale at contract 1.7.0 while every other export artifact is
   now 1.10.0; app's version banner correctly flags this (thread 042, open to backend).
6. **T4 real suspension data — interim CLOSED 2026-07-27 (ADR-053).** Real, dated, sourced list
   wired into the live board (`data/suspensions_2026.json`, currently empty — verified, not an
   oversight). Thread 057's fuller structured-source design (per-source schema, staleness test as
   a blocking gate) remains open if a more permanent solution is wanted later.
7. **T6 full roster-status ingest** — the live `roster_status` field on `board.json` is a proxy
   derived from `contracts.is_active` (ADR-050), not a real active/IR/practice-squad feed. Needs a
   new `roster_status_weekly`-shaped table from `nflreadpy.load_rosters()`, which is a DB-writing
   task, deliberately not done this round.
8. **T7 depth-chart contradiction** — still unresolved (`SELECT MAX(dt) FROM depth_charts` not run
   this pass; out of this round's scope).
