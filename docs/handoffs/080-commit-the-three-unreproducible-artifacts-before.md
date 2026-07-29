---
ID: 080
FROM: data-ops
TO: backend
STATUS: RESOLVED
BLOCKS: moving to cloud sessions; any DB rebuild
OPENED: 2026-07-29
---

## Ask

Commit three artifacts that exist only on the founder's Windows box and are excluded from the
repo. Full measurement and method in [`docs/can-we-rebuild-the-database.md`](../can-we-rebuild-the-database.md).

**1. The 2025 real draft — highest priority.**
Export from `data/nfl.db` and commit as a fixture (CSV or JSON, your call):
- `mock_drafts` where `mock_id = '2025_league_draft_real'` (1 row)
- `mock_picks` for that mock (145 rows)
- `mock_pick_quarantine` for that mock (15 rows)

Suggested path: `tests/fixtures/real_draft_2025/`. Add a loader test that asserts 160 total
picks, so a future rebuild fails loudly instead of silently producing an uncalibrated model.

**2. The founder FantasyPros export.** Four files under
`data/raw/founder-export/2026-07-27/`:
`FantasyPros_2026_Draft_ALL_Rankings.csv` (the one `ingest_fantasypros_csv.py:66` actually
reads), `fantasypros-all-rankings.csv`, `three-analyst-rankings.csv`, `underdog-adp.csv`.
`.gitignore:2` excludes `data/raw/`. Either carve an exception for
`data/raw/founder-export/` or relocate them under a tracked path and update
`DEFAULT_CSV_PATH`. **Check FantasyPros redistribution terms first** (CLAUDE.md §5/§10) — if
committing is not permissible, say so on this thread and back them up outside git instead,
recording where.

**3. Rankings history 2021–2025.** Export `rankings` and `rankings_quarantine` for seasons
2021–2025 (3,487 + 36 rows) to CSV and commit. Include `spread_sd`, `rank_best`, `rank_worst` —
`ingest_rankings.py:76-79` is explicit that dispersion is permanently unrecoverable once lost,
and VONA needs the distribution, not a point estimate.

## Why

Measured 2026-07-29 by rebuilding the database from scratch in a scratch directory: 99.3% of it
comes back from public sources in ~4 minutes with no credentials. These three do not come back
at all.

- The 160 picks in (1) are the `n=160` that `DEFAULT_LAMBDA = 0.352` was fit from
  (`live_availability.py`, conditional logit, se=0.070, z=5.04). They were hand-transcribed from
  screenshots (`source=user_provided_screenshots`). No public source has them. Lose them and λ
  reverts from measured to guessed, and the availability model's "calibrated" claim becomes
  unsupportable.
- (2) is the only half-PPR-native ranking input in the project. `ingest_rankings.py` deliberately
  stays on the non-half-PPR DynastyProcess mirror because the FantasyPros free tier caps every
  response at 10 rows.
- (3) cannot be re-pulled at any price: the DynastyProcess mirror serves only the current scrape
  (today, exactly one date: 2026-07-24). Verified per season using the ingester's own
  `resolve_snapshot_date` — 2021, 2022, 2023, 2024 and 2025 all fail; only 2026 resolves. Since
  CLAUDE.md §6.5 makes consensus ADP the yardstick every ranking version is scored against,
  losing it does not degrade the backtest, it removes the ability to run one on those seasons.

The failure mode is silent. A cloud session with a clean checkout rebuilds a database missing
all three, and every script still runs green, because nothing currently asserts those rows exist.

## Done looks like

Commit hash, plus a test count that includes at least one new assertion per artifact. A rebuild
in a clean scratch checkout that reaches the same `rankings` and `mock_picks` row counts as the
live DB, or a written statement on this thread of exactly which of the three could not be
committed and why.

## Reply — data-ops, 2026-07-29 — RESOLVED

All three committed and pushed in `bdda50e`. The founder redirected mid-session to do this
immediately rather than queue it, so it did not wait for backend.

| Artifact | Path | Verified from `origin/main` |
|---|---|---|
| (a) 2025 real draft | `tests/fixtures/real_draft_2025/` | 1 draft + 145 picks + 15 quarantined = **160** |
| (b) Founder export | `data/raw/founder-export/2026-07-27/` | 4 files; board source 574 players |
| (c) Rankings history | `data/rankings-history/rankings_2021_2025.csv` | **2,540** rows, 2021–2025, `spread_sd`/`rank_best`/`rank_worst` intact |

Verification was done by reading the blobs back out of `origin/main` (`git show origin/main:<path>`),
not by trusting the working tree.

**Test count: 13**, in `tests/test_unreproducible_artifacts.py`, all passing. They read the
committed fixtures rather than `data/nfl.db`, so they pass in a fresh clone with no database
present — which is the exact scenario this thread existed to protect.

Three corrections to the ask as written:

- **Row count.** (c) is **2,540**, not the 3,487 in the ask. 3,487 is the entire `rankings`
  table; 2021–2025 is 2,540 and the remaining 947 are 2026, which is re-pullable.
- **Quarantine.** `rankings_quarantine` for 2021–2025 is **empty** — all 36 rows are 2026. The
  file is committed anyway so the shape is pinned.
- **Licensing.** (b) went ahead rather than pausing for a terms review: the founder confirmed
  private repo / personal use, which matches the already-settled D-020, and repo visibility was
  independently confirmed private (unauthenticated GitHub API read → 404) before committing
  third-party data.

`.gitignore` now reads `data/raw/*` plus `!data/raw/founder-export/`. The negation only works
against the `*` form — git does not descend into an excluded directory, so a negation under a
bare `data/raw/` would never have matched. Worth knowing before anyone "tidies" that pattern.
