# CURRENT STATE

**This file is the canonical answer to "where is the project right now."**
It is edited **in place**. When something changes, replace the affected line — never append a new
section, never leave the old value "for contrast." If you find yourself adding a second version of
a number that already appears here, you are doing it wrong.

`docs/SNAPSHOT-*.md` files are frozen point-in-time captures, not rivals to this file — they drift
the moment this file changes and this file always wins.

Do **not** read `docs/status.md` (frozen 2026-07-28) or its successor `docs/status/` to answer a
current-state question. Both are append-only session logs and contain superseded figures presented
in the same voice as current ones. Same hazard `docs/assistant-context.md` warns about for
`decisions.md`. It is fine to read either to learn *what happened*; it is not fine to read them to
learn *what is true*.

**THE APP IS LIVE ON THE INTERNET, 2026-07-29** — `https://fantasy-football.soft-water-e755.workers.dev`,
a Cloudflare Worker serving the static Vite build from `main` and rebuilding on every push
(`wrangler.jsonc` at the repo root). Founder confirmed it working in his own browser; independently
verified (2026-07-29, before this session's ADR-062 bump) that `/data/board.json`'s
`contract_version` field matched `src/export_contract.py` at the time, confirming it was the
current build then; the deployed worker has not been redeployed since, so it now lags this
repo's bumped value (see this file's contract-version line under Build state) until the next push.
`maplerock.net` moved to Cloudflare nameservers and the custom domain is added, pending certificate.
**Public by explicit founder choice**, with the exposure trade stated to him. No credential in this
repo — Cloudflare holds its own deploy token. This closes the last dependency on the founder's
machine: development, tests, the database rebuild, the daily capture and now viewing the app all run
without it.

**Last verified:** 2026-07-29, backend session (worktree `agent-a03895ae72315d84c`, ADR-062,
FR-042) fixing a real defect: all 24 `generate_config_matrix.py` presets and every league built
through `league_builder.create_league()` (including the real, previously-created
`ethans_expert_league`) were silently copying Westwood's verified custom scoring ruleset
(`scoring.LEAGUE` — stacking yardage bonuses, ADR-052) with only reception value changed/overridden,
so a preset labeled "ESPN-default" or a founder-created custom league carried Westwood's bonuses/
TD values/defense while claiming to be something else. New `src/standard_scoring.py::
STANDARD_LEAGUE` (25 yd/pt passing, 4 pt passing TD, −2 INT, 10 yd/pt rushing/receiving, 6 pt TD,
−2 fumble lost, **no yardage bonuses** — the founder's own explicit FR-042 definition) is now what
every non-primary league builds on; only the primary (Westwood) league still uses `scoring.LEAGUE`,
unreachable through either preset-matrix or custom-builder path. **Contract 1.14.0 → 1.15.0
(additive):** `league.json` gains `scoring_ruleset_note`, stating on screen which ruleset a league
actually uses. All 24 presets + `ethans_expert_league` regenerated (not edited); Westwood's own
board verified byte-identical (Bijan Robinson 303.16 pts / VBD 172.17, unchanged) — only its
`league.json`'s contract version and new note field changed. Non-primary boards moved for real:
e.g. `espn_10_half` Bijan Robinson 303.16 → 296.68 pts (rushing-yardage bonus removed). Handoff
thread 093 opened to frontend for the contract bump. See ADR-062 for full before/after evidence.

**Prior verification:** 2026-07-29, backend session (PM-dispatched, worktree
`agent-a2a7e52225b3a7db0`, ADR-060) closing a real gap: contract 1.14.0 (thread 082) put real ADP
fields on the board but defined the term nowhere reachable — 13-term glossary, zero mentions in
Methodology. Added an `ADP` glossary term (`src/export_static.py`, folding
`adp_min_pick`/`adp_max_pick`/`adp_selected_pct` into it rather than four separate terms) and a
Methodology section confirming, with evidence, **ADP is display-only** — it does not feed
`projected_points`, VBD, tiers, availability, or any recommendation (`_load_adp_snapshot()`'s own
docstring, ADR-035's "NOT wired into the shipped default" status note, and thread 082's frontend
reply all agree). Regenerated all 27 `glossary.json` files (primary + 26 saved league configs) —
no `.db` needed for that path. Also corrected two now-false "no ADP source is legally obtainable
(ADR-018)" claims sitting next to the new text (the `consensus rank` glossary entry,
`board.json`'s `consensus_source_note`) — stale since ADR-035. **No contract bump** — every field
used already existed at 1.14.0. Found and mechanically fixed (marker lines only, no content
change) two files carrying literal leftover git-conflict markers: `docs/decisions.md` around
ADR-057/058, and `docs/handoffs/082-...md` around its two frontend replies — did NOT touch the
actual ADR-054/055 duplicate-header collision underneath, which is ADR-056's already-made,
deliberately-left decision. **Known gap left open:** the live `board.json` artifact's
`consensus_source_note` field still carries the old ADR-018 text — the Python source is fixed but
regenerating the artifact needs a working `nfl.db`, which this session's `scripts/
rebuild_database.py` run could not get past step 4 (`github.com/dynastyprocess/*` 403s in this
kind of session — documented, pre-existing, see `docs/can-we-rebuild-the-database.md`). Tests:
backend 688 passed / 29 failed / 9 errors / 3 skipped (every failure/error is the missing-`nfl.db`
condition or the pre-existing ADR-054/055 mailbox failure, none touch glossary/methodology code);
frontend 203/203 passed, `tsc -b --noEmit` clean. Screenshots looked at directly (not just
captured), 4 images in `frontend/e2e/artifacts/adp-*-2026-07-29.png`. Prior verification:
2026-07-29, PM check-in session running **in the cloud, not on the founder's
machine** (`origin/main` @ `4a299df`; no local worktrees exist here, so anything sitting untracked in
a worktree on the founder's machine — see thread 081 — is invisible to a cloud session and cannot be
fixed from one). Three facts measured this session: the mailbox check now **passes**; the daily ADP
capture **ran successfully off this machine** for the first time (`4a299df`, authored by
`github-actions[bot]` at 15:38 UTC, `data/adp-snapshots/2026-07-29.csv`, 225 rows) which retires the
local Windows Scheduled Task; and the **Fable "M" mandate — the founder's three model questions,
`docs/fable-mandate-M-2026-07-29.md` — has never been run** (no `docs/reviews/fable-M1/M2/M3-*`
files exist). Prior verification: 2026-07-29, rescue + rebuildability session (main @ `c96739c`).
That session preserved the orphaned mock-calibration work as
`backend/mock-calibration-kickers` @ `11c794a` (ADR-054, 11 files, **committed as-found and not
reviewed** — completeness not assessed), added `docs/environment.md`, and measured whether
`data/nfl.db` is rebuildable (`docs/can-we-rebuild-the-database.md` — yes for 99.3% in ~4 minutes,
no for three artifacts; see open item 9 and thread 080). Prior verification: 2026-07-27, overnight
PHASE 1/PHASE 2 closeout session (main @ `9d8e09b`, merge of `integration-2026-07-27` into `main`)
— build-state table below is
measured directly from `git rev-parse HEAD`, real backend/frontend full-suite runs,
`CONTRACT_VERSION` in `src/export_contract.py`, and `tools/handoffs.py check`. `CONTRACT_VERSION`
is **1.15.0** (measured from `src/export_contract.py`, 2026-07-29, this session's ADR-062 bump —
was 1.14.0; this line previously said 1.13.0 until an earlier claim checker caught that drift).
The 1.13.0 bump, from the Phase 3 Chain 1 backend session (worktree
`phase3-chain1-adp-and-exports`, thread 074 closed), added: `board.json` top level gained
`snapshot_as_of_date`/`snapshot_age_days`/`snapshot_max_age_days`/`snapshot_stale`/
`snapshot_freshness_note`, the `FreshnessResult` `build_board_json` already computed via
`fr.require_fresh` on every call and previously only printed to the build console. Prior bump,
1.12.0 (ADR-053): `board.json` gained four unconditional suspension fields —
`suspension_flag`/`suspension_games`/`projected_points_suspension_adjusted`/
`suspension_adjustment_note` — real, dated, sourced, currently empty; T4 wired into the live board
via the shared `write_all` path; ADR-051: top-level `scoring_format`, `board_source`/
`consensus_source` now name `fantasypros_csv_2026draft`; ADR-050: `roster_status`, contract 1.10.0.
Primary board and `ethans_expert_league` both rebuilt at 510 players; 2026 rookies confirmed
present with real ranks (Jeremiyah Love #33, Carnell Tate #70, Jordyn Tyson #84). Half-PPR yardage
bonuses independently verified to stack against the live Yahoo platform (ADR-052) — see §7 of
`CLAUDE.md`. Handoff threads 069 (scoring_format display) and 073 (suspension fields display) are
**RESOLVED** (frontend chain, branch `frontend/069-073-trace-registry-1-12-0` @ `0da321f`): the
trace registry and `EXPECTED_CONTRACT` were pinned to 1.12.0 there, then re-pinned to **1.13.0**
in this merge session once thread 074 landed on `main` underneath it (`ui/data/contract.ts`,
`ui/data/trace-fields.ts`; the five new snapshot-freshness fields registered in
`BOARD_HEADER_TRACE_FIELDS` and wired into `RefreshData.tsx`, which previously asserted freshness
"is not exported by backend" — false the moment thread 074 landed, now reads the real
`snapshot_age_days`/`snapshot_max_age_days`/`snapshot_stale` values). Thread 074 (T5 freshness
result export to `board.json`) is **RESOLVED** — see this doc's contract-version line above.
`main` and `integration-2026-07-27` diverged independently this round (2 commits vs. 7) and
required a founder-authorized merge rather than the fast-forward the standing runbook expects —
see `docs/handoffs/076-...md` and this session's `docs/status.md` entry for the allocator-race
root cause. Separately, this merge session also caught and fixed a real identity bug unrelated to
either branch: `src/league_config.py`'s `build_current_league()` still hardcoded
`name="Primary league (10-team half-PPR)"` / `platform="other"` — a pre-ADR-052 placeholder that
was never updated once the live platform verification named the real league ("Westwood", Yahoo,
ID 154693). Now `name="Westwood"`, `platform="yahoo"`; `data/export/league.json` regenerated and
re-synced to `frontend/public/data/`.

---

## Build state

Rows below the markers are regenerated by `python tools/state.py --apply` (`--tests` to also run
the suites) — do not hand-edit them; the next `--apply` overwrites whatever's there. The two rows
above the markers aren't measured by a single command, so they stay hand-maintained: edited only
by the session whose work changed them, per the agent operating rules.

| | Value | Notes |
|---|---|---|
| Agent infrastructure | **Live, mailbox check FAILING — deliberately, see Top open items #15** | Seven subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian, pm), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`). `tools/handoffs.py check` (2026-07-29, PM closeout, cloud): **FAILS on two cross-branch ADR collisions only — 90 threads, 49 open / 41 resolved, none stale, all addressed.** Threads 083/084/087 collided the same way and were renumbered to 088/089/090 at this closeout. The earlier 069/073 failure was fixed when the frontend replies landed and `047ff90` corrected thread 080's reply heading. The check still emits ~29 non-fatal contradiction warnings (shared-target antonym pairs, plus five threads citing D-021 as undecided when it is DECIDED) — glance-and-disposition items, not failures. |
| Document-claim detector | **Live, PASSING** (ADR-059, 2026-07-29) | `docs/state-claims.toml` (registry) + `tools/state_claims.py` (checker) + `tests/test_state_claims.py` (21 tests). Fails when one of ten **live** documents asserts something the repo contradicts: existence, a constant quoted in prose, a source/capability status, a count, or two live docs disagreeing. Append-only logs are deliberately out of scope. Caught **eight live false claims** on its first run, all corrected here; proved on six planted faults reproducing the real 2026-07-29 failures, in both directions. **Rule it enforces: a factual claim of those classes in a live document must be registered with its verification.** Known gap, asserted in a test: whether a GitHub Actions *schedule* has fired is not readable from a checkout, so the ADP-capture claim has no registered truth — a single document asserting the false version still passes. `docs/pm/**` is not yet scanned (thread 083). |
| Frontend location | `frontend/` subdirectory of this repo | Merged from `frontend-prep` via `git subtree add`, full history preserved. No longer a separate working copy. |

<!-- BUILD-STATE:START (generated by `python tools/state.py --apply` -- do not hand-edit between these markers) -->

| | Value | Notes |
|---|---|---|

## Top open items

Current state only. An item leaves this list when it is done — history lives in ADRs and
`docs/status/`, not here. Verified 2026-07-29 (PM session); every claim below was measured this
pass or is marked as unverified.

**Data capture — time-sensitive, cannot be backfilled**

1. **A *scheduled* ADP capture has still never fired.** `.github/workflows/adp-snapshot.yml`
   (09:15 UTC daily) has exactly one run in repository history, `event: workflow_dispatch`,
   triggered by hand. First scheduled opportunity is **2026-07-30 09:15 UTC**. Check `event:`, never
   the commit author — `github-actions[bot]` authors manual dispatches too, and that is precisely
   how this was got wrong once already. Do not retire the local Windows task until an
   `event: schedule` run succeeds, and do not treat one success as a track record.
   Captured so far: MFL proxy `data/adp-snapshots/` (2026-07-26, -28, -29 — **07-27 UTC is a
   permanent gap**), FFC three-format `data/adp-snapshots-ffc/` (2026-07-29 half/non/full only).
2. **Pick-level ADP velocity is not built.** No longer blocked — FFC is unblocked by the founder
   (FR-023). MFL cannot serve it (`TYPE=adp` is final figures with no pick sequence). Standing
   conditions: private single-user use, one fetch per day per format, and `adp_source` values are
   never blended into one consensus figure.
3. **Mock drafts toward n=30.** Gates the pre-registered availability decision rule. Still 0 of ~30
   usable; the one logged draft was placeholder data.

**Correctness — the app states something that is not so**

4. **All 24 preset leagues carry Westwood's scoring ruleset while being labelled platform
   defaults** (FR-042, founder ruling). `src/generate_config_matrix.py:71-74` deep-copies `LEAGUE`
   and swaps only the reception value. Regenerate, do not edit — this invalidates projections in
   every preset export. **Sequence before the custom-league builder**, or the builder inherits it.
   That file's docstring also contradicts itself on whether ESPN scoring was ever verified
   (lines 6-11 versus 52-53).
5. **Non-primary leagues are missing four export artifacts.** Primary carries 11, the 26
   sub-leagues carry 7. Absent everywhere: `strategies.json`, `player_descriptions.json`,
   `season_stats.json`, `weekly_finishes.json`. Consequence: **the Strategy guide is empty in 26 of
   27 leagues**, and three other screens thin out on league switch.
6. **Six present-but-inert controls** (FR-037): Export CSV, Export PDF, League settings, Compare,
   Ask, and Ask-the-assistant per glossary term. All carry `aria-disabled`. The founder is finding
   them by clicking. One design treatment covers all six.
7. **Duplicate founder-request ids.** FR-029 and FR-030 each name two different requests, so a
   status update to one is invisible in the other. `tools/dashboard.py` now flags this on every run.

**Data the model wants and does not have**

8. **T6 full roster-status ingest.** `board.json:roster_status` is a proxy derived from
   `contracts.is_active` (ADR-050), not a real active/IR/practice-squad feed. Needs a
   `roster_status_weekly`-shaped table from `nflreadpy.load_rosters()`.
9. **T7 depth-chart contradiction.** Unresolved and unmeasured — `SELECT MAX(dt) FROM depth_charts`
   has not been run.
10. **Three nflverse pulls worth making**, from the 13 of 23 loaders this repo never calls
    (`docs/research/nflverse-unused-data-audit-2026-07-29.md`): `load_schedules()` head-coach
    columns (1999-2026, closes coach *identity* but not coordinator duty), `load_participation()`
    route columns (2016-2025, a documented proxy for the route gap — must be labelled a proxy), and
    `load_ff_opportunity()` (2006-2025 pre-fitted xFP, needs Statistician sign-off before it is a
    ranking input). Nothing ingested yet.
16. **Per-player COMPONENT projections now exist, personal-use only** (2026-07-29, data-ops,
    thread 092, FR-056 — founder ruled "personal use, proceed").
    `src/ingest_sleeper_projections.py` pulls `api.sleeper.com/projections/nfl/2026`
    (`company: rotowire`) for QB/RB/WR/TE into `sleeper_projections` (as_of_date-stamped) and
    `data/projection-snapshots/`. 2007 rows stored (250/538/840/379 by position), 1098 quarantined
    as `no_sleeper_crosswalk_match` (real, all deep bench/UDFA). **Not wired into `board.json` or
    any export, not behind the public site** — Sleeper's ToS forbids redistribution and the app is
    public (thread 092 item 2's public-hosting/FantasyPros/FFC licensing escalation is still open,
    unresolved by this work). Whether these projections improve the ranking model is a separate,
    unregistered question for `ranker`/`strategist`.

**Model**

11. **Where the TE mispricing sits in the draft is unanswered.** 33.6% of a tight end's stable
    quality is unpriced by consensus versus 15.1% RB/WR and 6.3% QB, but that is pooled across all
    tight ends. If it concentrates in the top few, the founder's late-round strategy is wrong and
    the finding argues the opposite way. Survivorship is the specific way this analysis fails.
12. **The shipped rank curve pools all seasons flat.** The QB slope collapsed monotonically
    2021→2025 (−67, −73, −59, −45, **−4**), so the board recommends from a regime that has
    disappeared. Whether other positions are doing the same has never been checked.

**Known-red, deliberately**

15. **`tools/handoffs.py check` fails on two ADR numbers, and that failure is the record.** ADR-054
    and ADR-055 each carry a second, different definition on the unmerged branch
    `origin/backend/mock-calibration-kickers` ("Batch mock-draft ingestion…" and "Kickers get a
    consensus-only export artifact…"). Both sets are real work. Renumbering belongs to whoever merges
    that branch, knowingly — not to a passing session guessing which wins. Do not silence it.
    `tests/test_handoffs.py::test_mailbox_health` is red for this reason and no other.

**Suspended, not forgotten**

13. **T4 suspension data** — interim closed (ADR-053); `data/suspensions_2026.json` is real, dated
    and currently empty, which is verified rather than an oversight. Thread 057's fuller
    structured-source design stays open if a permanent solution is wanted.
14. **FantasyPros licence** — closed (D-020) while the product stays private and single-user.
    Reopens on any second user, alongside D-021.
