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
verified that `/data/board.json` serves `contract_version 1.14.0`, so it is the current build.
`maplerock.net` moved to Cloudflare nameservers and the custom domain is added, pending certificate.
**Public by explicit founder choice**, with the exposure trade stated to him. No credential in this
repo — Cloudflare holds its own deploy token. This closes the last dependency on the founder's
machine: development, tests, the database rebuild, the daily capture and now viewing the app all run
without it.

**Last verified:** 2026-07-29, PM check-in session running **in the cloud, not on the founder's
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
is **1.14.0** (measured from `src/export_contract.py`, 2026-07-29 — this line said 1.13.0 until
the claim checker caught the drift; the Build state table below had been right all along).
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
| Agent infrastructure | **Live, mailbox check PASSING** | Seven subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian, pm), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`). `tools/handoffs.py check` (2026-07-29, PM session, cloud): **OK — 81 threads, none stale, all addressed; 47 open / 34 resolved.** The earlier 069/073 failure was fixed when the frontend replies landed and `047ff90` corrected thread 080's reply heading. The check still emits ~29 non-fatal contradiction warnings (shared-target antonym pairs, plus five threads citing D-021 as undecided when it is DECIDED) — glance-and-disposition items, not failures. |
| Document-claim detector | **Live, PASSING** (ADR-059, 2026-07-29) | `docs/state-claims.toml` (registry) + `tools/state_claims.py` (checker) + `tests/test_state_claims.py` (21 tests). Fails when one of ten **live** documents asserts something the repo contradicts: existence, a constant quoted in prose, a source/capability status, a count, or two live docs disagreeing. Append-only logs are deliberately out of scope. Caught **eight live false claims** on its first run, all corrected here; proved on six planted faults reproducing the real 2026-07-29 failures, in both directions. **Rule it enforces: a factual claim of those classes in a live document must be registered with its verification.** Known gap, asserted in a test: whether a GitHub Actions *schedule* has fired is not readable from a checkout, so the ADP-capture claim has no registered truth — a single document asserting the false version still passes. `docs/pm/**` is not yet scanned (thread 083). |
| Frontend location | `frontend/` subdirectory of this repo | Merged from `frontend-prep` via `git subtree add`, full history preserved. No longer a separate working copy. |

<!-- BUILD-STATE:START (generated by `python tools/state.py --apply` -- do not hand-edit between these markers) -->

| | Value | Notes |
|---|---|---|
| Backend branch / commit | `claude/pm-agent-setup-gobxa0`, `47e589cee90f0c49fb435be3f3ee7da58f9ab6b3` | `git rev-parse --abbrev-ref HEAD` / `HEAD` |
