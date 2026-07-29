# 2026-07-29 — rescue, environment doc, rebuildability test, closeout, code map

Founder-directed session, five items in a fixed order, run without approval checkpoints
("decide and log").

## 1. Rescue — done

`.claude/worktrees/backend-mock-calibration` held 11 uncommitted files (7 modified, 4 new).
Committed **as-found** to `backend/mock-calibration-kickers` @ `11c794a` and pushed. Not merged,
not reviewed, completeness not assessed — that was the instruction.

Contents: `src/mock_prediction.py` (ingest-time prediction snapshots for the batch mock path,
reusing `mock_lab_store.predict_next_pick`), `freshness.historical_snapshot_date`, a frozen
league-config snapshot plus `calibration_usable` gate in `ingest_mock_drafts.py`, kicker export
changes, three new test files, and ADR-054. ~1,116 insertions.

Two premise notes. The branch had **no unique commits** — `f1d51d0` was already an ancestor of
`origin/main`, so the working tree was the only thing at risk. And the worktree carries an
**older CLAUDE.md**, under which `docs/status.md` was still the live log; its `status.md` append
was correct when written, not a violation of the current freeze.

## 2. `docs/environment.md` — done

Six environment facts that subagents were rediscovering every session, each re-verified against
current code rather than copied forward. Linked from CLAUDE.md §12 and inserted as session-start
reading item 2, ahead of the role docs.

Two facts changed on verification:

- The hook gained a `dequote()` step on 2026-07-28, so the semicolon false positive is
  **narrower** than previously recorded. Measured truth table: `@{n='FE';e={...}}` and
  `ForEach-Object { $a = 1; $b = 2 }` are still blocked; `;` inside quotes is now allowed. A
  third case was found — interleaved quote types can misalign the textual dequote and expose a
  `;` you believed was protected.
- Here-strings fail differently per shell: PowerShell 5.1 breaks on embedded double quotes, and
  the Bash tool does not parse `@'...'@` at all (it passed literal `@` characters into a commit
  message this session). Recorded `git commit -F <file>` as the pattern that works in both.

## 3. Rebuildability — done, and it changes a standing claim

`docs/can-we-rebuild-the-database.md`. Measured by actually rebuilding into a scratch directory;
the live DB was opened `mode=ro` throughout.

**99.3% rebuilds in ~4 minutes** with no credentials (`ingest_weekly_stats` 22.2s → 475,626 rows
exact; `ingest_reference` 75.0s; `identity.py` 12,468/49,391/57 exact; `ingest_league_metrics` 27
exact). Scratch DB 807.8 MB vs the real 813.7 MB.

**Three things do not rebuild** — full detail in thread 080 and CURRENT-STATE open item 9:
the 2025 real draft (160 picks, `user_provided_screenshots`, the `n=160` behind λ=0.352); the
founder FantasyPros export under gitignored `data/raw/`; and rankings history 2021–2025, which
the DynastyProcess mirror no longer serves — verified per season with the ingester's own
`resolve_snapshot_date` (2021–2025 all fail, 2026 resolves).

**Committed ADP CSVs cannot substitute** for the rankings history: wrong source (`mfl_proxy`
market ADP vs FantasyPros expert ECR, which CLAUDE.md §4 forbids blending), wrong period (both
July 2026), wrong scale (232 vs 3,487 rows).

This corrects CURRENT-STATE's standing claim that `adp_snapshots` is "the one table in
`data/nfl.db` that cannot be rebuilt" — corrected in place. MFL *does* serve historical periods,
but stamps every response today and returns an accumulated aggregate, so re-pulling reintroduces
look-ahead. Its window also shrank: 2026 `totalDrafts` read 43 on 07-29 against 50 in the 07-26
CSV.

Also measured: `depth_charts_snapshots` (+9,522) and `contracts` (+48) drift upward on rebuild.
Reproducing a past backtest number needs pinned artifacts, not pinned commands.

## 4. Closeout — done (five items, ideas inbox skipped as instructed)

**Defects registered.** Thread 080 (three unreproducible artifacts → backend, blocks cloud
sessions). Thread 081 (thread 079 ID collision between `main` and the `phase3-chain1` worktree —
a *fourth* instance after 043/049/053/ADR-048; the mechanism is that `sync` cannot see unsynced
threads in sibling worktrees, so parallel worktrees make the documented protocol insufficient
rather than merely forgettable). FR-019 filed for the founder's working preferences.

**Founder interruptions counted** across 57 prior transcripts, structured events only: 45 total,
0.8/session. Ask-the-founder 19 (42%), manual interrupt 9 (20%), tool denied 6 (13%), hook
chaining 6 (13%), hook destructive 5 (11%). An earlier regex pass gave 173 and was inflated by
docs and hook source that merely quote those strings — **that number should not be used.**
This overturns FR-018's premise: permission denials are 6 of 45, and `permissions.allow` is
already fully wildcarded, so the request was rescoped in place rather than worked as written.

**Branch audit.** 28 local branches; **0 have unique work missing from origin**. Five dirty
worktrees, not one — but the four beyond the rescue target hold regenerated exports or
superseded drafts already landed on `main` (`export_history.py`, `league_scoring_live.json`,
`season_stats.json` are all tracked; `export_rosters.py` was superseded by `build_rosters_json`
inside `export_contract.py`). The founder's premise that the mock-capture work was the only real
orphan was correct.

**CURRENT-STATE.md** updated in place: `Last verified` moved to 2026-07-29 @ `c96739c`, the
ADP-is-the-only-unrebuildable-table claim corrected, open item 9 added. Build-state table
regenerated via `tools/state.py --apply`, not hand-typed.

**Dashboard.** `docs/dashboard.html` was a hand-written snapshot with no date in it, making
staleness undetectable. Replaced with `tools/dashboard.py`, which renders from
`CURRENT-STATE.md` + `handoffs/OPEN.md` + git, per the standing CLAUDE.md preference. `--check`
mode exits 1 when stale, so it can go in the suite later. One bug found and fixed while
verifying: the page counted its own file in the dirty count, so writing it made `--check`
permanently red.

**Still stale, not regenerated:** `docs/roles-workflow-map.html` — no generator exists and
writing a second one was out of scope.

## 4b. Artifacts committed mid-session — founder interrupt, thread 080 closed

The founder redirected mid-session to act on thread 080 immediately rather than leave it
queued. All three are now committed and pushed (`bdda50e`), verified by reading the blobs back
out of `origin/main` rather than trusting the working tree:

| Artifact | Path | Verified from `origin/main` |
|---|---|---|
| 2025 real draft | `tests/fixtures/real_draft_2025/` | 145 picks + 15 quarantined + 1 draft = 160 |
| Rankings history | `data/rankings-history/rankings_2021_2025.csv` | 2,540 rows, 5 seasons, dispersion intact |
| Founder exports | `data/raw/founder-export/2026-07-27/` | 4 files, board source 574 players |

`.gitignore` now reads `data/raw/*` with `!data/raw/founder-export/` — the negation only works
against the `*` form, since git does not descend into an excluded directory. Repo confirmed
private before committing third-party data (unauthenticated API read → 404), consistent with
the already-settled D-020.

`tests/test_unreproducible_artifacts.py` adds 13 tests that read the *fixtures*, not the
database, so they pass in a fresh clone with no DB — the exact situation they protect against.

One number corrected: the rankings history is **2,540** rows, not the 3,487 quoted earlier in
the session. 3,487 is the whole table; 2021–2025 is 2,540, and the 36 quarantined rows are all
2026, which is re-pullable.

## 5. Code map — done

`docs/CODE-MAP.md`, read-only, five questions answered with file:line. Nothing refactored.

## Commits

`11c794a` (rescue branch), `7b9a5a4`, `c96739c`, plus the closeout and code-map commits on
`main`. All pushed.
