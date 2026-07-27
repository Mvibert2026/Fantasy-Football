---
ID: 067
FROM: pm
TO: data-ops, backend
STATUS: OPEN
BLOCKS: T1 completion for leagues 2/3, board correctness for the non-primary leagues
OPENED: 2026-07-27
---

## Ask

Founder input, 2026-07-27: there are **three real leagues**, not one, and T1 (half-PPR consensus
pull, `docs/reviews/ACTION-PLAN-2026-08.md` Day 2 item 2.1) was scoped for a single format. It
must pull consensus per scoring format and build per-league boards with team count carried
through.

Clarified this session (do not re-ask, this was confirmed directly with the founder):

1. **Westwood (Yahoo, primary)** — CONFIRMED 10 teams, scoring matches `scoring.LEAGUE` exactly.
   See `docs/screenshots/League Settings 2-5.png` and `decisions.md` ADR-052 (backend session
   closing T2 this turn). **T1 as originally scoped already covers this league correctly — no
   rework needed for Westwood.**
2. **A second, distinct Yahoo league** — different scoring, different team count. No data yet.
3. **An ESPN league** — different scoring, ~12 or 14 teams (founder unsure which). No data yet.

## Why

Replacement levels move with roster count (RB30/WR40/TE10/QB10 is Westwood's answer only, per
CLAUDE.md §4's "coach_id is first-class" sibling principle — schema fields exist for exactly this
reason). `league_builder.py` / `ReplacementLevels.from_league_config()` (ADR-041/047/049, thread
040) already derives replacement levels from whichever `LeagueConfig` is passed — confirmed
correct in thread 040's backend reply, so that machinery is not the gap. The gap is (a) actual
league-config data for leagues 2/3, which only the founder has, and (b) T1's consensus pull
being hardcoded to `type=ST&scoring=HALF` instead of format-aware.

## Cost, stated plainly (per FR-004 / the founder's standing instruction to say what it costs)

- Leagues 2/3 are **blocked on the founder** supplying the same two things Westwood's screenshots
  gave us: the league-settings scoring table and team count/roster shape (`League Settings N.png`
  equivalents). No agent can synthesize this.
- Once supplied: FantasyPros only exposes STD/HALF/PPR presets (`type=ST&scoring={STD,HALF,PPR}`)
  — it cannot represent arbitrary custom scoring (unusual bonus thresholds, non-standard TD/INT
  values, TE premium, etc.). For each of leagues 2/3, pick the closest FantasyPros preset by
  reception value and **flag the approximation explicitly** — which knobs diverge and by how much
  — never present it as that league's true consensus. This is a data-availability ceiling, not an
  engineering shortcut, and it should be visible on whatever surface shows that league's board.
- Rough cost: T1 was budgeted 1 sonnet-session-unit for one format. Two more league configs
  (fetch + preset-match + `scoring_format`/`league_id`/`as_of_date` columns + the board-builder
  "raises on wrong format" test, tripled) is roughly **+1 to +1.5 session-units**, more if a
  league's scoring diverges far enough from any preset to need explicit callout logic rather than
  just a different query param.
- Cross-reference, do not duplicate: thread 040 already covers league *creation* (the Settings
  editor capability, backend's piece already built per its reply on that thread). This thread is
  narrower — getting the *consensus rankings pull* to be per-format for leagues that already have
  configs, once the founder supplies leagues 2/3's data.

## Done looks like

- Founder supplies league-2 and league-3 scoring/team-count screenshots (same shape as
  Westwood's) — flag this back to the founder if it hasn't happened yet; this thread cannot
  proceed past design without it.
- `ingest_rankings.py` (or successor) accepts a `scoring_format` param per league, pulls the
  closest FantasyPros preset, records `scoring_format` + `as_of_date` + the approximation delta.
- Board builder raises if a league's rows don't carry the expected `scoring_format`.
- Three per-league boards exist, each using its own measured replacement levels.

---
### pm · 2026-07-27

**League 2 data now supplied — unblocked. ESPN (league 3) explicitly not ready yet per the
founder ("ESPN not ready just yet") — do not wait on it, proceed with league 2 now and pick up
ESPN in a follow-up when it lands.**

`docs/screenshots/Yahoo League 2 settings.png` through `...4.png`: League 2 is **"Ethan's Expert
League"**, Yahoo, League ID 834236, **12 teams**, **Offline Draft** (not a live Yahoo draft room —
picks won't come from a Yahoo live-draft API integration for this league, if that ever mattered
to any tool). Head-to-Head, playoffs 4 teams weeks 16-17 (same as Westwood/`league_config.py`).

**Scoring, transcribed in full:**
- Passing Yards: 25 yards/pt, **no bonus tiers** (unlike Westwood's 300/350/400 bonuses — this
  league has none. Confirmed by reading the full offense table in one screenshot; nothing is cut
  off between "Passing Yards" and "Passing Touchdowns").
- Passing TD: 4. Interceptions: **-1** (Yahoo's own default — Westwood overrides to -2, this
  league does not).
- Rushing Yards: 10 yards/pt, no bonus tiers. Rushing TD: 6.
- Receptions: 0.5. Receiving Yards: 10 yards/pt, no bonus tiers. Receiving TD: 6.
- Return TD: 6. 2-pt: 2. Fumbles Lost: -2. Offensive Fumble Return TD: 6.
- **Kickers scored** (Westwood has no K anywhere): FG 0-19/20-29/30-39 = 3, 40-49 = 4, 50+ = 5,
  PAT = 1.
- DEF/ST: identical to Westwood, value for value (Sack 1, INT 2, Fumble Rec 2, TD 6, Safety 2,
  Block Kick 2, KO/Punt Return TD 6, Points Allowed tiers 10/7/4/1/0/-1/-4, XP Returned 2).
- Roster: QB, WR, WR, WR, RB, RB, TE, W/R/T, **K**, DEF, BN×5, IR — 1 FLEX not 2 (Westwood has 2),
  plus a K starter slot Westwood doesn't have.

**Why this is actually the easier of the two remaining leagues, not harder:** no yardage bonus
thresholds at all means this maps cleanly to a plain FantasyPros HALF-PPR preset with no bonus
approximation needed — the only real divergence from a vanilla half-PPR pull is INT at -1 (which
is likely FantasyPros' own default anyway, verify against whatever the pull currently assumes).
The team-count change (12 vs 10) is pure replacement-level/roster-shape, already handled by
`ReplacementLevels.from_league_config()`.

**Kicker slot — do not treat as a blocker.** `scoring.py:172-182` already filters K (and DEF) out
of replacement-level computation for exactly this reason ("this scoring engine cannot compute K,
DEF -- no kicker or DST scoring exists, ADR-039"). League 2's board will build correctly with K
silently excluded from ranking, the same known gap DEF already has — not a new decision needed,
just confirm the existing filter actually fires for a league whose `starters` includes `"K"`
(should already work, but this is the first real config to exercise that path — worth one
assertion in the League 2 test).

**Revised scope: this thread can proceed on league 2 now, independent of ESPN.** Only ESPN
remains genuinely blocked. Recommend treating league 2 and ESPN as two separate landings rather
than waiting to batch them — the founder's own framing ("ESPN not ready just yet") signals they
want progress on what's available now.

---
### data-ops · 2026-07-27

**Transcription verified against the actual screenshots** (`Yahoo League 2 settings.png` through
`...4.png`) before building anything on it, per the ask. Value-for-value match: no bonus tiers on
any yardage category, INT -1, DEF/ST identical to Westwood tier-for-tier, K schedule as stated,
roster `QB, WR, WR, WR, RB, RB, TE, W/R/T, K, DEF, BN×5, IR`. No discrepancies found.

**Item 1 (FantasyPros consensus pull) — did NOT build a new pull. Load-bearing finding first:**

The premise "whatever module currently pulls the primary league's half-PPR consensus... hits
FantasyPros with `type=ST&scoring=HALF`" is **incorrect**. Read `src/ingest_rankings.py` in full
before writing anything: the actual, only working ingestion path is the DynastyProcess mirror via
`nflreadpy.load_ff_rankings()` — **not the FantasyPros live API, and not scoring-format-aware at
all.** It stores one shared, unscored ECR ranking used for every league including the primary one
today. `rankings` table schema has no `scoring_format` column (checked directly:
`PRAGMA table_info(rankings)`; `SELECT DISTINCT source` → only `fantasypros_ecr`). This is not a
regression — the file's own docstring already documents the 2026-07-26 decision to stay on the
mirror specifically because the FantasyPros live API's free tier caps every response at 10 players
regardless of position filter or offset/page params, which is already the finding in
`docs/deferred.md` under "FantasyPros API — probed 2026-07-25."

**Re-confirmed live this session, not assumed stale:** `GET consensus-rankings?type=ST&scoring=
HALF&position=RB` → HTTP 200, `total_experts: 71`, `public_api_limited: true`, **10 rows returned**
out of an available RB pool that would need 30+ for the primary league alone and more for a
12-team league. Same wall as before, unchanged. Building a "league-2 HALF preset pull" against
this endpoint would not be a smaller/cheaper version of the ask — it would reproduce the exact
already-documented failure and ship 10-player-per-position coverage as if it were a real pull.
Per this project's "never fabricate a value to fill a gap" rule, I did not build it.

**Consequence for item 2 (`scoring_format`/`as_of_date`/`league_id` columns):** not added.
There is nothing format-differentiated to tag yet — league 2's board draws on the same shared,
single, unscored consensus ranking the primary league already uses (confirmed by reading
`make_board.py`'s rankings query — it's positional draft order, not something the bonus/INT
scoring differences would change; `scoring.py` applies the league's actual scoring rules to raw
stats on top, downstream of this data, which is why the primary league's board is closer to
correct than it looks despite the shared source). Adding `scoring_format`/`league_id` columns to
`rankings` now, with only one real value in play, would be schema churn with no second value to
distinguish yet — deferred until either (a) a paid FantasyPros tier is purchased, or (b) another
half-PPR-native source is found. Recorded as an open decision for the founder/backend, not
silently dropped.

**Items 3 and 4 (league config + replacement-level confirmation) — built:**

- `data/leagues/ethans_expert_league.json` — real `LeagueConfig` via
  `league_builder.create_league()`, 12 teams, `starters={"QB":1,"RB":2,"WR":3,"TE":1,"K":1,
  "DEF":1}`, `flex_slots=1`, `bench=5`, `ir=1`, `ppr=0.5`, `scoring_overrides` zeroing all three
  yardage-bonus lists and setting `interception=-1`. **`user_draft_slot=1` is an explicit
  placeholder** — the founder has not supplied their actual draft slot in this league; flagged in
  both the config-build script and the test docstring, never presented as measured.
- Exported via `league_builder.export_league()` → `data/export/ethans_expert_league/{board,
  league,availability,rosters}.json`. Measured output: `replacement_levels_used = {"QB":12,
  "RB":30,"WR":42,"TE":12}` — confirmed distinct from the primary league's RB30/WR40/TE10/QB10,
  `unsupported_positions=["DEF","K"]`, `def_supported=false` — the K-starter-slot path (thread's
  own flagged "first real config to exercise this") does fire correctly.
- New test file `tests/test_league2_ethans_expert.py`, 6 tests, all passing: config field
  correctness against the transcribed settings, replacement levels differing from primary,
  K/DEF exclusion, flex-split-unmeasured flag, strict-JSON board output. This is item 3's DB-backed
  confirmation the thread asked for, same pattern as thread 040's generic 14-team probe league
  (`tests/test_multi_league_export.py`).
- **Item 4 (board-builder per-league format assertion) — left for backend, not attempted.** No
  such global "raises on non-HALF row" assertion currently exists to extend (searched; the T1
  action-plan item describing it was never actually built against the live API for the reason
  above). Backend's decision to make, once/if item 1's data-source question is resolved.

**Full suite: 564 passed, 1 pre-existing failure** (`test_floor_checks.py::
test_t3_every_board_player_has_a_bye_week`, JAC/LAR team-code mapping — unrelated to this
session, already flagged red in the action plan under item 3.1). Commit not made (told not to
commit/push this session) — working tree has these new/changed files:
`data/leagues/ethans_expert_league.json`, `data/export/ethans_expert_league/*.json`,
`tests/test_league2_ethans_expert.py`.

**Still open on this thread:** ESPN/league 3 (not supplied, not attempted, per instruction).
Whether to pay for the FantasyPros paid API tier or find a different half-PPR-native ADP source,
to make item 1/2 actually buildable for any league (this blocks Westwood too, not just league 2 —
the primary league's own consensus pull has never been format-scored either, it just happens to
be closer to right because this league's bonuses are a modest fraction of typical scoring). Item 4
(board-builder format assertion) for backend. **Leaving `STATUS: OPEN`** — this is `data-ops`'s
piece only; the thread also names `backend` and ESPN remains unresolved.

---
### pm · 2026-07-27

**Correction — league 2's team count is 10, not 12.** Founder, verbatim: *"Ethan's expert league
may likely only end up being 10 people, treat it as a 10 person league unless otherwise
directed."* The screenshot's "Max Teams: 12" was the platform's configured slot count, not a
confirmation that 12 real participants will draft — record both facts (screenshot said 12,
founder directs building for 10) rather than treating this as a transcription error.

**Action needed, superseding item 3/4's "built" status above:** `data/leagues/
ethans_expert_league.json` and its exports under `data/export/ethans_expert_league/` were built
this session with `teams=12` and `replacement_levels_used={"QB":12,"RB":30,"WR":42,"TE":12}`.
Rebuild with `teams=10` (roster shape, scoring, and everything else transcribed this session is
unaffected — only the team count changes). Update `tests/test_league2_ethans_expert.py`'s
assertions to match. Note the screenshot-vs-founder-directive discrepancy in the config's
metadata or a comment, the same way `user_draft_slot=1`'s placeholder status is already flagged,
so a future session doesn't "fix" it back to 12 by re-reading the screenshot.

---
### data-ops · 2026-07-27 (teams=10 correction)

Rebuilt per the founder override above. `data/leagues/ethans_expert_league.json` and
`data/export/ethans_expert_league/{board,league,availability,rosters}.json` now built at
`teams=10` via new `scripts/rebuild_ethans_expert_league.py` (same `league_builder.create_league`
/ `export_league` path used originally). No other field changed — same roster shape, scoring
overrides (no yardage bonuses, INT -1), `user_draft_slot=1` placeholder.

**Measured replacement levels at teams=10: `{"QB": 10, "RB": 25, "WR": 35, "TE": 10}`.** Confirmed
distinct from both:
- the primary league's `QB10/RB30/WR40/TE10` (same QB number by coincidence — both leagues are
  10 teams x 1 QB starter with no flex QB eligibility — but RB/WR differ because league 2 has only
  1 flex slot vs. primary's 2), and
- the now-superseded 12-team build's `QB12/RB30/WR42/TE12`.

`tests/test_league2_ethans_expert.py` updated: `teams=10` throughout (was 12), the
replacement-levels test now pins the exact dict above instead of only asserting inequality with
primary. **6/6 tests passing.**

Screenshot-vs-founder-directive discrepancy recorded per the same convention already used for
`user_draft_slot=1`'s placeholder (no free-text metadata field exists on `LeagueConfig`, so this
is a comment/docstring convention, not a schema change): module docstring and inline `teams=10`
comment in `tests/test_league2_ethans_expert.py`, docstring + inline comment in
`scripts/rebuild_ethans_expert_league.py`, and `docs/CURRENT-STATE.md`'s league-2 paragraph. A
future session re-reading the screenshot should not "fix" this back to 12.

Full suite: **565 passed, 2 failed** (`test_floor_checks.py::test_t3_every_board_player_has_a_bye_week`
— pre-existing, already flagged; `test_holdout_audit.py::test_no_new_direct_sqlite_connections_in_src`
— new `src/ingest_fantasypros_csv.py` from a concurrent session isn't yet in the allowlist, unrelated
to this correction, not investigated further here). Commit hash: `f1b4ecf0b288812391f73f0faacaecbfc9ba2c1e`
(HEAD at session start/end — no commit made per instruction not to commit/push).

Scope respected: did not touch item 1/2 (consensus-pull source decision — appears another session
progressed this in parallel per CURRENT-STATE.md, not reviewed here), did not touch Westwood/primary,
did not touch ESPN/league 3. Leaving `STATUS: OPEN`.
