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

**Last verified:** 2026-07-30, frontend session (worktree `agent-af87493d6c285e241`) shipping FR-076
(the assistant couldn't see what the Draft Room screen was already showing) and FR-077 (the assistant
dock needed real conversation history, not just a persistent input, and fewer suggested-question
buttons). **Two root causes for FR-076, both confirmed by a failing test, not assumed:** the
reasoning lane's retrieval corpus (`ui/assistant/retrieval.ts`) was built only from static export
artifacts and never carried anything about the live draft (current pick, roster state, the
recommendation, scarcity) — the root cause named in the dispatch, and real; separately, and
unexpectedly, the founder's own literal reported question ("what are my likely choices and trade
offs ... at my next pick") never reached the reasoning lane at all — `ui/assistant/intent.ts`'s
news-pattern regex matched the bare word "trade" inside "trade offs" (meant for "player X was
traded") and misrouted the whole question to the news lane, which correctly reported "no player
named in that question," a message easily paraphrased as "the backend doesn't have that." New
`frontend/ui/assistant/pageContext.ts` builds a bounded `ContextItem[]` bundle from values
`DraftRoom.tsx` already computed for its own render (current pick, roster needs, the live
recommendation and its stated reason, the give-up trade-off, the WHY NOT HIGHEST VBD explanation,
the next-pick reference point, position scarcity — never re-derived, per the dispatch's own "two
code paths that can disagree is worse than one"), reported via a new `onAssistantContext` prop
(additive only — one prop, one effect, no JSX touched) and merged into every reasoning-lane call
alongside lexical retrieval. The classifier's `trade`/`trade-off` collision and `defineTerm`'s
unbounded "term" capture (which would have swallowed the same sentence into a "not in the glossary"
message even after the news-pattern fix) are both fixed and covered by a regression test asserting
the founder's exact sentence now classifies as `reasoning`. FR-077: `ask()` now threads a bounded
`ConversationTurn[]` history (last 6 turns, 600 chars/answer) through to `/__reasoning`;
`frontend/server/proxy.ts` and `worker/index.js` (kept in sync per `docs/assistant-persona.md`) both
build alternating user/assistant messages from it and gained a 9th binding rule (history is for
continuity only, never a fact source — the current answer must still trace to the current turn's
retrieved context) added to all three files including the persona doc itself. Suggested-question
buttons capped from 6 to a curated 3 (`SUGGESTED_TEMPLATES`). Verified against a real, seeded draft
(not just unit tests): `frontend/e2e/verify-fr076-fr077.mjs` intercepts `/__reasoning` and confirms
the founder's exact question retrieves 7 real page-context items from a real `DraftRoom` render, and
a follow-up carries 1 prior turn — screenshots
`frontend/e2e/artifacts/fr076-founder-question-answered.png` and
`fr077-followup-conversation.png` looked at directly; the answer text matches the real Recommend-tab
panel numbers behind it. `ANTHROPIC_API_KEY` remains absent in this container (confirmed again, per
`docs/frontend-cloud-runbook.md`), so the real hosted Anthropic call itself was not exercised — the
screenshot proves the request payload, not the model's live reply. `npx tsc -b --noEmit` clean; 301
tests, 300 passed + 1 flaky-under-full-suite-contention timeout (`draft-room-typeahead.test.tsx`,
25/25 passing in isolation — reproduces the same container-speed finding a prior session already
recorded for this file, not a regression). Full resolution detail:
`docs/founder-requests/FR-076-*.md`, `FR-077-*.md`.

**Prior verification:** 2026-07-30, frontend session (worktree `agent-a160788e8e9ccc925`) porting two
design specs in order, both in `docs/design/`: `DRAFT-MIDDLE-PANE.md` and `SUPPLIED-VALUES.md`. The
Draft screen's middle pane (`frontend/ui/views/DraftRoom.tsx`) is now one tab set — **Recommend ·
Scarcity · Queue · Insights** — replacing the old fixed stack (RECOMMENDED-when-on-clock, else
Position Scarcity + Queue/Watch + NEXT DECISION all in one column); NEXT DECISION is now a
persistent footer, never behind a tab. Recommend gained FR-049's look-ahead toggle (recommendations
computed at the user's next real turn, not just the current pick) and FR-051's next-pick reference
point (CONSIDERING / LIKELY THERE AT `<pick>`, display-only, no arithmetic — a documented divergence
from the design mock's illustrative VBD-range numbers: built as a real sigma 5/10/20
survival-probability spread instead, since VBD itself is not sigma-dependent). Scarcity gained
FR-045's pace-suppression rule (`positionScarcity`'s new `hasAutoFillPlaceholders` param nulls
`pace` and states why once Auto-fill has logged placeholder picks, rather than showing every
position as "behind pace" simultaneously, which is arithmetic noise from mixing real and
placeholder pick populations). Insights (FR-048) is an honest not-yet-built state, not an
approximation — no `findings.json` artifact exists to scope research to a specific pick. FR-044
(the periodic-table grid) stays explicitly out of scope, per design's own manifest: its position
colours are unpicked. Separately, both places the founder supplies a value rather than the app
deriving one — the typed opponent name and the TopBar draft-slot override — no longer render in
`--acc` (the board's delta/"good" colour); both now carry a dotted underline plus a lowercase
marker (`typed` / `set by you`), per `SUPPLIED-VALUES.md`'s rule that a supplied value's channel
must never be a semantic accent. A third instance of the same defect, not named in the spec
(`Predictions.tsx`'s own overridden-slot readout), was found and fixed for consistency.
**Opportunistically closed thread 093** (contract 1.15.0 pin, already the one pre-existing red test
in the 251-test baseline) — bumped `EXPECTED_CONTRACT`/`TRACE_CONTRACT`, no UI change. **Found and
fixed a real path bug in `docs/design-reference/fidelity.py`** (off-by-one `REPO_ROOT`); even fixed,
the harness cannot check this build — `screens.json` names routes the app doesn't have (no router)
and no per-screen reference HTML exists, a separate, larger gap not fixed this session (see
`docs/ideas-inbox.md`). Screenshots looked at directly:
`frontend/e2e/artifacts/middle-pane-*.png` (6), `supplied-*.png` (2). `npx tsc -b --noEmit` clean;
**265 passed, 0 failed** (251 baseline + 14 new tests across `draft-room-middle-pane-tabs.test.tsx`,
`topbar-supplied-slot.test.tsx`, `formulas.test.ts`, `opponents.test.tsx`, `predictions.test.tsx`).
Full writeup: `docs/status/2026-07-30-frontend-draft-middle-pane-supplied-values.md`.

**Prior verification:** 2026-07-29, data-ops session (PM-dispatched, worktree
**Last verified:** 2026-07-30, backend session (worktree `agent-ab49d060d089f26a1`, ADR-063,
FR-062) building the Yahoo Fantasy Sports connector the founder promoted to near-term work
("add the yahoo connection work... sooner than later"). No real Yahoo credential exists yet
(registration is the founder's own account, undone at build time), so this is built against
documented shapes and tested against constructed fixtures — never a live response — per the
dispatch's explicit constraint. New `src/providers/` package: `base.py` (the `LeagueProvider`
adapter interface CLAUDE.md SS4 calls for — `Bonus(points, target)`, `StatModifier`,
`RosterPositionSpec`, `LeagueSettings`, `DraftResult`, `ProviderUnavailable`), `yahoo_oauth.py`
(OAuth2 Installed-Application flow — authorization URL, code exchange, refresh, a file-backed
`TokenStore`), `mapping.py` (signature-key-based, defensive JSON extraction — never asserts an
exact response shape, since none has ever been read), `yahoo.py` (`YahooProvider`: settings,
draft results, a best-effort caveated live-draft-picks read, league discovery), `espn.py`
(`ESPNProvider` — always raises `ProviderUnavailable`, citing Disney ToU SS2.B.x/SS2.A/SS3.H by
section; ESPN remains a clean, permanent no). **Real finding, not assumed:** `pip install yfpy`
fails in this environment — its `yahoo-oauth` dependency drags in unmaintained legacy YQL
packages (`myql`, `rauth`) that don't build under current `setuptools` — so the connector talks
to Yahoo's OAuth2 + REST v2 endpoints directly via `requests` instead of vendoring `yfpy`,
replicating its verified field shapes as this project's own dataclasses. **Fetch-on-demand only:
nothing persists to `nfl.db`** — the research doc's [SNIPPET]-tagged reading of Yahoo's 24-hour
retention clause is treated as binding pending verification; the only Yahoo-derived data
persisted anywhere is the OAuth token itself (`data/.yahoo_token.json`, gitignored). Two new
scripts: `scripts/yahoo_connect.py` (one-time interactive authorize) and
`scripts/yahoo_pull_league_settings.py` (fetch, print, diff against CLAUDE.md SS7's Westwood
table; `--out` opt-in only). 58 new tests, all passing without network/credentials
(`tests/test_providers_{base,mapping,yahoo_oauth,yahoo,espn}.py`); full suite otherwise shows
only pre-existing failures (missing `data/nfl.db` in this worktree; the already-known
`ingest_sleeper_projections.py` sqlite-allowlist finding from thread 094) — none touch
`src/providers/`. Full reasoning and the founder's exact next steps: ADR-063
(`docs/decisions.md`). No contract-version bump (this doesn't touch the frontend export). FR-062
still `TO: pm` per unallocated thread 095 — not resolved by this session, since it isn't backend's
thread to resolve; this entry documents what backend built in response to the founder's own
promotion of the work, dispatched directly rather than via that thread.

**Last verified:** 2026-07-29, data-ops session (PM-dispatched, worktree
`agent-a1bcc65cbaf0f88d7`), closing thread 055: historical FFC ADP is no longer absent from
`nfl.db`. Backfilled 2,467 rows across 19 season-formats into new `adp_source` values
`ffc_half_ppr_12team` (2018-2024, 7 seasons — the ranker's stated priority format) and
`ffc_non_ppr_12team` (2013-2024 minus five gate/content exclusions, 12 seasons), never blended
with the daily 10-team capture or `mfl_proxy`. This directly answers the ranker's pass-2 gap
(`docs/ranking/bottom-up-research-pass-2.md`): the only pre-draft market history in `nfl.db` was
previously FantasyPros ECR, 2021-2025 (4 usable seasons), forcing ECR rank to stand in for real
draft position. `as_of_date` on every new row is the parsed window-END date from FFC's own dated
sample sentence (verified against `nflreadpy.load_schedules()` per-season kickoff, not assumed),
never the day the script ran. Full writeup:
`docs/research/ffc-adp-history-backfill-2026-07-29.md`; quarantine detail (333 rows, mostly the
documented team-defense `no_name_match` ceiling):
`data/qa/ffc-adp-history-quarantine-2026-07-29.csv`. New script:
`tools/backfill_ffc_adp_history.py`, one-time not scheduled, 10 new tests
(`tests/test_backfill_ffc_adp_history.py`), 44 passed across the touched suites. Thread 055
replied and `STATUS: RESOLVED`.

**Last verified:** 2026-07-29, backend session (PM-dispatched, worktree
**Last verified:** 2026-07-29, frontend session (worktree `agent-a2ac0a9c4c8191c5e`) shipping
FR-055/FR-050/FR-058 together — the same draft-room screen, the same founder complaint ("the
numbers do not explain themselves"). Confirmed FR-055's premise first: the Draft-mode board list
had no column header row at all (Prep's `Board.tsx` has one). Added a static header row (RANK ·
PLAYER · POS · TM · ADP · Δ · VBD · AVAIL, labels ported verbatim from `Board.tsx` where the
number matches) and a VBD cell on every row plus a fifth SORT option (FR-050). The substantial
piece, FR-058: `ui/data/recommendation.ts` gained `recommendationTerms()` (the three reachable
stopgap constants — unfilled-need +8, tier-1-TE +18, early-QB −25 — each paired with a plain-word
reason) and `findVbdOverride()`, comparing the recommendation's #1 pick against the whole board's
real VBD leader, not just the six-deep shortlist. `DraftRoom.tsx`'s RECOMMENDED card now shows a
"WHY NOT HIGHEST VBD" panel exactly when they disagree — the displaced player by name, the exact
VBD points overridden, and every firing term explicitly tagged "an unbacktested stopgap constant,
not a finding" — and nothing when the ordering already agrees with VBD. Verified against a real,
reproducible scenario built from the live board export (not synthetic): with the board's real top
five VBD players drafted off, the recommendation prefers Jaxon Smith-Njigba over the actual VBD
leader Josh Allen, and the panel names him, the 7-point gap, and both firing terms; a second
scenario (the user's real first turn) confirms no panel renders when recommendation already agrees
with VBD. Screenshots looked at directly (`frontend/e2e/artifacts/fr055-fr050-headers-and-vbd.png`,
`fr058-vbd-override-explanation.png`, `fr058-no-override-when-order-agrees.png`). `npx tsc -b
--noEmit` clean; 16 tests added/changed across `ui/__tests__/recommendation.test.ts` and
`ui/__tests__/draft-room-scarcity-and-sort.test.tsx`. Caught and fixed one real defect via the
suite itself, not eyeballing: the first header-row test used an unscoped text query and correctly
failed on "VBD" appearing twice on screen (header cell + pre-existing SORT tab button) — scoped
with `within()`. Three flaky test-file timeouts in the full suite (`board-filters.test.tsx`,
`draft-room-typeahead.test.tsx`, `offline.test.tsx`) were reproduced identically against
unmodified (`git stash`) code under the same CPU contention and disappeared entirely re-run alone
— container speed, not a regression, confirmed rather than assumed. FR-058's "or any selected
strategy" is explicitly out of scope: no strategy selector exists in the app to depart from; noted
as separate, dependent work. `docs/founder-requests/FR-055-*.md`, `FR-050-*.md`, `FR-058-*.md` each
carry `STATUS: SHIPPED` with a `## Resolution` section. Full test count and commit hash: see
`docs/status/2026-07-29-frontend-fr050-055-058.md`.

Prior verification: 2026-07-29, backend session (PM-dispatched, worktree
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
| Backend branch / commit | `worktree-agent-af87493d6c285e241`, `f07cf88d21546e21ef7e5bc7df1a4b8d7d9bf723` | `git rev-parse --abbrev-ref HEAD` / `HEAD` |
| Data contract | `1.15.0` | `CONTRACT_VERSION` in `src/export_contract.py` |
| Python modules | 44 | `src/*.py`, counted |
| Export artifacts | 11 | top-level files in `data/export/` |
| Config matrix | 26 | dirs under `data/export/` |
| Backend tests | (skipped — pass --tests to run the suite) |  |
| Frontend tests | (skipped — pass --tests to run the suite) |  |

<!-- BUILD-STATE:END -->

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

5. **Non-primary leagues are still missing four export artifacts** (data gap, unresolved):
   `strategies.json`, `player_descriptions.json`, `season_stats.json`, `weekly_finishes.json` —
   primary carries 11, the 26 sub-leagues carry 7. **The UI now explains this rather than reading
   as broken**, fixed 2026-07-29 (frontend, `docs/design/TWO-TRACK-EXPRESSION.md`): the league
   selector carries a PRIMARY/GENERIC track badge and a ●/○ marker per option before a league is
   even selected, and the Strategy guide's old single "Not available for this league" string
   (which conflated "generic track, by design" with "not yet run") is split by track. Only
   `strategies.json` actually reads as a thinned screen in practice — `weekly_finishes.json`/
   `season_stats.json` are fetched from a genuinely shared, unprefixed path regardless of which
   league is loaded (`ui/data/playerHistory.ts`), so PlayerDetail's history sections render the
   same on every league; that correction is logged in `docs/ideas-inbox.md` (2026-07-29, frontend,
   item 5) since it revises this line's own earlier "three other screens thin out" framing.
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
12. **The shipped rank curve pools all seasons flat — and measured 2026-07-29, that costs almost
    nothing** (`ranker` pass 3, `docs/ranking/bottom-up-research-pass-3.md`, thread **093** to
    `strategist`, awaiting ruling). The QB slope point estimates reproduce exactly (−66.6, −72.6,
    −58.6, −45.0, −4.1) but **the collapse is not established**: trend +15.3/season [−3.5, +34.1],
    CI spanning zero; 2025's own CI [−46.5, +69.2] contains 2024's estimate; the monotonicity is a
    property of `RELEVANT_DEPTH["QB"]=20` (at depth 12 the series is not monotone and 2021 is the
    flattest season); and dropping one player (Jayden Daniels, consensus QB3) moves 2025 from −4.1
    to **+28.6**. **Other positions checked and the answer is no** — RB's 2025 slope is −77.9, the
    *steepest* of its five; WR is flat; TE is monotone with a magnitude CI spanning zero.
    **The mechanism is market ordering skill, not positional value**: the 2025 realised QB value
    curve is −58.7, flat against era means of −57.7/−59.0/−56.8, while consensus τ_b at QB went
    +0.484 → **−0.042** (worse than random). Ordering skill has **zero measured persistence**
    (lag-1 r = −0.007 [−0.414, +0.411]), so recency-weighting the *consensus* curve would track the
    least persistent quantity in the system. On the *value* curve the answer is position-specific
    (QB strongly yes, hl1 −22.6 [−30.3, −13.6] on a 9-season holdout; RB no; **WR contraindicated**,
    last1 +2.75 [+0.96, +4.80] worse; TE weak) **and at QB it points the opposite way from the fix
    on record** — the QB value curve is steepening, so weighting it recently makes the QB premium
    *larger*. Board cost: `vbd = b·ln(rank/base)` exactly (intercept cancels; verified against the
    live 510-row board, zero ordering mismatches), so the board is four numbers — under half-life 3
    **one** top-150 player moves ≥10 places, under half-life 5 **none**, and every scheme from last3
    down leaves all four slopes inside the board's own published 95% CI. **The board-curve weighting
    question itself is unanswerable on current data: n = 2 evaluable targets, disagreeing at the 4th
    decimal of Kendall τ.** Threads **055**/**084** are what unblock it.

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
