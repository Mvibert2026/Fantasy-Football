# 2026-07-30 — backend — test-registry #35/#36 (global flex baseline, VONA pick-gap awareness)

**Dispatch:** run the two remaining untested HIGH-edge valuation items from `docs/test-registry.md`
(founder asked for the remaining bottom-up tests to start). Worktree `agent-a299a75833b30b593`.

## What was done

1. Merged `origin/claude/pm-agent-setup-gobxa0` (already up to date, no-op).
2. Read `docs/statistical-guardrails.md`, `docs/strategic-insights.md`, `docs/environment.md`,
   `docs/CURRENT-STATE.md`, `docs/operating-model.md` per session protocol.
3. Rebuilt `data/nfl.db` for this worktree (`docs/environment.md` §4 — worktrees never inherit
   it). `scripts/rebuild_database.py` step 4 hit the documented DynastyProcess 403 (Claude-session
   proxy restriction, `docs/can-we-rebuild-the-database.md`); restored via the committed rescue
   path (`experiments/restore_rankings_from_committed_csv.py`) then completed the remaining steps
   (`ingest_fantasypros_csv.py`, `--skip-network` for identity/mock-draft/ADP restore). Verified
   row counts against the rebuild script's own assertions.
4. Wrote the design **before any code ran**: `docs/ranking/valuation-tests-35-36-precommit.md`
   (narrative), then `docs/preregistration/PR-006-global-flex-baseline.md` and
   `docs/preregistration/PR-008-vona-pick-gap-awareness.md` (the project's real
   `src/preregistration.py` mechanism — `require_preregistration`/FDR-over-the-persistent-log,
   not just the narrative doc). Both committed at `status: REGISTERED` before running.
5. Wrote sanity checks (`tests/test_valuation_experiments_sanity.py`, 10 tests) **before** the
   module they check, per the project's non-negotiable rule — arithmetic invariants (the 80-pick
   derivation, the renormalised position share summing to `N_ROUNDS-1`, the real 14/4 gap
   alternation for `USER_SLOT=3`, seed stability via `zlib.crc32` not builtin `hash()`, the
   structural look-ahead guard via `db.CutoffEnforcedStore`). Committed, then implemented
   `experiments/valuation/replacement_and_vona.py` to satisfy them (all 10 pass).
6. Wrote and ran `experiments/valuation/run.py`, driving `src/draft_sim.py` **unmodified** — new
   board arrays / `Strategy` callables only, no change to the simulator itself. 2021-2024 (2025
   sealed holdout untouched), σ ∈ {10, 20}, 300 sims/cell. Full output:
   `data/qa/valuation-tests-35-36-run-2026-07-30.log`.
7. Updated `docs/test-registry.md` #35/#36 and `docs/strategic-insights.md` §5b in place with
   verdicts. Opened `docs/handoffs/NEW-valuation-tests-35-36-results.md` to `strategist` for
   methodology sign-off (not a blocker — nothing was wired into anything live).

## Results

**#35 (PR-006), global flex-eligible replacement baseline: NULL.** Season-paired points margin
(global minus current) +1.7 [-67.6,+74.8] σ=10, -6.7 [-51.2,+37.8] σ=20 — sign flips, both CIs
wide around zero, well under the measured simulation noise floor (~8.5 pts/300 sims — confirmed
directly; more simulated drafts would not narrow this, the n=4-season bootstrap is what's
binding, matching `run_draft_sim.py`'s own established separation of the two noise sources). No
change to `scoring.ReplacementLevels` — current per-position scheme (ADR-029) stays in
production. Both VBD arms lose to market ADP by ≈-270 pts (expected — season S-1 persistence is
a known-weak projection stand-in, no player-level projection exists yet per ADR-017; this
reconfirms strategic-insights.md §1's existing headline, not a new finding).

**#36 (PR-008), VONA pick-gap awareness: NULL on realised outcome, decision-divergence
CONFIRMED.** Real alternating gap (14 vs. 4 intervening picks, `USER_SLOT=3`, ~3.5x) vs. a
gap-blind constant (`N_TEAMS-1=9`). Realised-points margin -37.2 [-118.8,+36.0] σ=10, -2.8
[-48.0,+37.1] σ=20 — NULL. **Decision divergence measured directly (identical opponent-noise
seed feeding both arms): the two arms pick a different full roster in 100% of paired simulated
drafts, all 8 season x σ cells.** Gap-awareness changes WHICH player almost every time without
reliably changing whether the resulting roster is better, at n=4 seasons. Secondary, uncorrected
caution: this VONA formulation (either gap variant) underperforms plain best-available-by-VBD by
~-110 to -126 pts both σ (CIs exclude zero, but the n=4 sign test floors at p=0.125 and neither
survives BH) — a caution against shipping VONA reaching under this share-based scarcity estimate
(a flat, round-averaged position share, coarser than the real round-varying demand), not a
confirmed loss.

**Multiple comparisons:** 12 comparisons (3 per σ per test x 2 σ), Benjamini-Hochberg against the
persistent run log (`n_total=63`). Zero survived — expected at n=4 seasons, where the exact sign
test floors at p=0.125 below the 0.05 threshold regardless of effect size.

**Power check (per the coordinator's explicit ask):** measured simulation SE directly for one
cell (`vbd_current`/`vona_gap_aware`, 2024, σ=10): 8.5/9.3 pts at 300 sims. Both are small
relative to the reported CI widths (70-150 pts) and to the observed margins (37-126 pts) — the
imprecision in every NULL verdict above is the n=4-season bootstrap, not an under-powered
simulation count. More sims per cell would not have changed any verdict here.

## A note on process

The first full run (`--sims 300 --record`, ~4-6 CPU-minutes given the VONA strategy's O(candidates
x pool) per-pick cost) was launched as a background Bash task and monitored via the `Monitor`
tool. The monitor's completion notification did not arrive promptly and this session paused
waiting on it rather than checking the process directly — flagged by the coordinator mid-session
("the notification you are waiting on is not coming, and you were not stopped for cause"). Fixed
by checking `ps`/log line counts directly with short (<=20s) `sleep` calls between checks instead
of relying solely on the notification, and by committing/pushing `experiments/valuation/run.py`
and the run log as WIP rather than holding them uncommitted until the run finished. The run did
complete correctly in the end (both notifications eventually arrived, one very late) — no data was
lost, but the pattern is worth remembering: check background work directly, do not block turns on
a notification alone.

## Commits (this session, in order)

1. `60d5b31` — pre-register design (precommit doc)
2. `544cf7f` — sanity checks + harness implementation
3. `e48ff1f` — PR-006/PR-008 registered via the real preregistration mechanism
4. `0685af8` — runner script (WIP, committed before the run finished)
5. `ed36c2b` — run results, PR-006/PR-008 updated to `status: RUN` with results, run log
6. (this commit) — test-registry.md / strategic-insights.md / CURRENT-STATE.md / status log /
   handoff

All pushed to `origin/worktree-agent-a299a75833b30b593` after each step, not held to the end.

## Test count

See final report for the full-suite number (a run was in progress at write time). Sanity suite:
`tests/test_valuation_experiments_sanity.py`, 10/10 passing. Pre-existing, unrelated red test
confirmed unaffected: `tests/test_holdout_audit.py::test_no_new_direct_sqlite_connections_in_src`
(the known `ingest_sleeper_projections.py` finding from thread 094 — not touched this session).
