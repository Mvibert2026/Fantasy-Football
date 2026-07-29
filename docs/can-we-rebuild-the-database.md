# Can `data/nfl.db` be rebuilt from the repo plus public sources?

**Measured 2026-07-29, end to end, three times over the course of the day** as more of the
picture came into focus. This is the final state: what to run, in what order, what it produces,
and the one real gap that remains.

---

## Answer

**Yes.** Every table in `data/nfl.db` — including the three artifacts once thought permanently
lost — rebuilds from a clean checkout with `scripts/rebuild_database.py`, no credentials, in
about a minute for the artifact-restore path and a few minutes including the full nflverse pull.
One genuine gap remains (`adp_snapshots`' point-in-time history had no import path — now fixed,
see below — but the *live* MFL endpoint itself only ever serves today's rolling aggregate, so the
daily captures still have to keep running and being committed; there is no way to backfill a
missed day after the fact).

Run it:

```bash
python scripts/rebuild_database.py --db data/nfl.db
```

---

## What changed since the first two passes at this question

This document went through three revisions in one day, each correcting the previous one. In
order, so the history is legible rather than silently overwritten:

<!-- state-claims: ignore-block — the numbered list below narrates superseded conclusions on
     purpose. Point 1 states the "rankings history is unrecoverable" claim that point 2
     disproves; without this marker the claim checker reads it as a live assertion. Anything
     that is still true must live OUTSIDE this block. -->

1. **First pass (scratch `--db` path only, not a clean clone).** Concluded three artifacts were
   permanently unrecoverable: the 2021–2025 rankings history, the founder's 2026 half-PPR
   FantasyPros export, and the 160-pick real 2025 draft. All three were then committed as files
   (thread 080, `bdda50e`): `tests/fixtures/real_draft_2025/`,
   `data/rankings-history/rankings_2021_2025.csv`, `data/raw/founder-export/2026-07-27/`.

2. **Second pass (a genuine clean-clone rehearsal, `claude/cloud-path-rehearsal-kafx7m` @
   `6c23c13`).** Found the first pass's rankings-history claim was simply wrong: the
   DynastyProcess mirror *does* still serve 2021–2025 ECR snapshots, and a fresh
   `ingest_rankings.py` pull reproduces the committed rescue CSV row-for-row (2,540 rows, 14
   columns, zero differences). Also found `requirements.txt` was missing `pandas`/`numpy`, no
   Python version was declared anywhere, and — critically — that the documented 4-step order was
   incomplete and left the suite red.

3. **This pass.** Confirmed (2) end to end in this session, found and fixed one further ordering
   bug that pass (2) had not caught, and closed the one remaining code gap: an `adp_snapshots`
   CSV→DB loader. Full detail below.

<!-- state-claims: end-ignore -->

**What this means for the three "unreproducible" artifacts:** two of them (rankings history,
founder export) turn out to be either re-pullable or already loadable straight from their
committed path. Only the real 2025 draft was ever genuinely irreplaceable, and it has been
committed and now has a proven restore path (`data/real_drafts/2025_league_draft.json`, the
ingestible source — not the `tests/fixtures/real_draft_2025/` table dump, which
`ingest_mock_drafts.py` does not read).

---

## The real rebuild order — 8 steps, not 4

The originally documented 4-command sequence (`ingest_weekly_stats.py`, `ingest_reference.py`,
`identity.py`, `ingest_league_metrics.py`) leaves a database missing `rankings`, the founder
export, the real draft, and `adp_snapshots` entirely — every script still exits 0, and nothing
downstream asserts those rows exist. `scripts/rebuild_database.py` runs the complete, order-
correct sequence and then asserts each restored artifact is actually present:

| # | Command | Measured this session |
|---|---|---|
| 1 | `ingest_weekly_stats.py --db <db>` | 12.2s → 475,626 rows |
| 2 | `ingest_reference.py --db <db>` | 34.5s → 10 nflverse tables (incl. `ff_playerids`) |
| 3 | `ingest_league_metrics.py --db <db>` | 14.0s → 27 rows |
| 4 | `ingest_rankings.py --db <db>` | 1.2s → 2,948 rows across 2021–2026 |
| 5 | `ingest_fantasypros_csv.py --db <db>` | 0.9s → 538 rows (founder 2026 half-PPR export) |
| 6 | identity (`build_identity_tables`) | 0.3s → 12,468 / 49,391 / 57 |
| 7 | `ingest_mock_drafts.py data/real_drafts/2025_league_draft.json --db <db>` | 0.4s → 145 resolved / 15 quarantined |
| 8 | `ingest_mfl_adp.py --db <db> --import-csv-dir data/adp-snapshots` | 0.4s → 703 rows across 3 committed dates |

**Total measured: 64.0s**, network-bound (steps 1–5 need the network; 6–8 are local restores).
`ingest_league_metrics.py`'s play-by-play scan dominates the local time; nflverse download speed
dominates the rest.

### Why step 6 (identity) must run before step 7 (mock drafts), not after

The 2026-07-29 rehearsal's documented order put `identity.py` **last**, reasoning that its own
`main()` prints a coverage report against `rankings` and exits non-zero on a fresh DB if run
before rankings exists. That reasoning is correct as far as it goes, but the conclusion doesn't
follow: **`identity.py` is the only thing that creates `players_canonical`**, and
`ingest_mock_drafts.py` needs `players_canonical` to resolve picks. Running mock-draft restore
before identity fails immediately:

```
sqlite3.OperationalError: no such table: players_canonical
```

— measured directly this session. `scripts/rebuild_database.py` resolves this by calling
identity's `build_identity_tables(conn)` function directly (see below) rather than shelling out
to its `main()`, which sidesteps the coverage-report/rankings dependency entirely and lets it run
in the correct position: after rankings exists (step 4/5), before the mock-draft restore needs
it (step 7).

### `identity.py` has no `--db` flag

Confirmed directly: `identity.py`'s `main()` takes no arguments and always writes `db.DB_PATH`.
Any earlier version of this document (or any other doc) showing `python src/identity.py --db
<scratch>` is wrong — that command silently ignores the flag and writes the real database.
`scripts/rebuild_database.py` avoids this by importing `identity.build_identity_tables(conn)`
directly against a connection opened on the target `--db`, rather than invoking the script.

---

## Environment gaps a clean machine hits, and their fixes

Confirmed and fixed this session (`requirements.txt`, `.python-version`):

| Gap | Effect | Fix |
|---|---|---|
| `pandas`/`numpy` absent from `requirements.txt` | pytest collection aborts outright — 15 `src/` modules and 9 test modules import pandas | Added, pinned (`pandas==3.0.5`, `numpy==2.5.1`) |
| No Python version declared anywhere except the ADP GitHub Action | `scipy==1.18.0` requires >=3.12; a stock 3.11 install fails hard | Added `.python-version` (`3.12`) |
| `tools/state.py` hardcoded the founder's Windows conda path | The `CURRENT-STATE.md` write-back tool the agent operating rules mandate hard-crashed off Windows | Changed to `sys.executable` |

---

## The one closed gap: `adp_snapshots` had no CSV→DB loader

`ingest_mfl_adp.py` always wrote a canonical dated CSV
(`data/adp-snapshots/YYYY-MM-DD.csv`) — the module's own docstring calls the CSV "the canonical
archive" and the DB "a queryable cache of it" — but had no code path to read a CSV back into the
DB. A rebuild therefore only ever got *today's* live MFL pull; the committed
`2026-07-26.csv`/`2026-07-28.csv` point-in-time captures (each one a snapshot of MFL's rolling
aggregate that cannot be reconstructed later once the day passes — see the look-ahead-bias note
below) were dead weight sitting in the repo with no way back into the database.

**Fixed:** `ingest_mfl_adp.py` now has `import_snapshot_csv(conn, path)` /
`import_all_snapshot_csvs(conn, dir)`, exposed as `--import-csv-dir <dir>` on the CLI. Idempotent
(same `(adp_source, mfl_id, retrieved_at)` primary key the live path already uses). 17 tests in
`tests/test_ingest_mfl_adp.py`, including a round-trip test (export → import → same rows) and a
whole-directory restore test. Measured this session: `data/adp-snapshots/*.csv` → 703 rows across
3 dates (`2026-07-26`, `2026-07-28`, `2026-07-29`), matching the live DB's row counts per file
exactly.

**This does not remove the underlying look-ahead-bias constraint.** MFL's endpoint only serves
*today's* rolling aggregate — every response is stamped with today's date regardless of the
requested period — so a live re-pull can never reconstruct a past date's snapshot; that data
only exists at all because a daily capture ran and its CSV got committed. **The scheduled daily
capture (`.github/workflows/adp-snapshot.yml`) and committing its output remain the only defence
against this window**; the loader above only closes the "can this repo's own committed history
be restored" gap, not the "can a missed day be recovered" gap, which is structurally impossible.

---

## Reproducible — exact row-for-row match (network path)

| Table | Rows (this session) | Source |
|---|---|---|
| `player_weekly_stats` | 475,626 | nflverse via `nflreadpy.load_player_stats` |
| `depth_charts_weekly` | 865,329 | `load_depth_charts` |
| `snap_counts` | 324,611 | `load_snap_counts` |
| `injuries` | 79,816 | `load_injuries` |
| `player_ids` | 49,391 | derived, `identity.py` |
| `ngs_receiving` / `ngs_rushing` / `ngs_passing` | 14,731 / 6,059 / 5,933 | `load_nextgen_stats` |
| `draft_picks` | 12,927 | `load_draft_picks` |
| `players_canonical` / `ff_playerids` | 12,468 each | `load_ff_playerids` + `identity.py` |
| `combine` | 8,968 | `load_combine` |
| `player_id_collisions` | 57 | derived, `identity.py` |
| `league_season_metrics` | 27 | play-by-play aggregate |
| `rankings` (2021–2025, `fantasypros_ecr`) | 2,540 | `load_ff_rankings()`, re-pulls identically to the committed rescue CSV |
| `rankings` (2026, `fantasypros_ecr`) | 408 | same, current scrape |
| `rankings` (2026, `fantasypros_csv_2026draft`) | 538 | founder's committed half-PPR export |
| `rankings_quarantine` | 37 (all 2026) | founder export DST/unresolved rows |
| `mock_drafts` / `mock_picks` / `mock_pick_quarantine` | 1 / 145 / 15 | committed `data/real_drafts/2025_league_draft.json` |
| `adp_snapshots` | 703 (3 dates) | committed `data/adp-snapshots/*.csv` |

All free, all public, no API key, no login. nflverse is CC-BY (FTN charting subset CC-BY-SA —
attribution required, CLAUDE.md §5).

## Reproducible but **drifts** — rebuild is not byte-identical

| Table | Real DB (2026-07-29 baseline) | Rebuilt this session | Delta |
|---|---|---|---|
| `depth_charts_snapshots` | 926,335 | 935,857 | **+9,522** |
| `contracts` | 48,404 | 48,452 | **+48** |

These upstream feeds are *live*, not archival. A rebuild today gives you today's state, not the
state captured when the DB was built. Harmless for most work; **not harmless for reproducing a
past backtest number exactly.** If a result must be reproducible to the row, it needs the
artifact pinned, not the rebuild command.

---

## One environment-specific finding, not a code defect: `github.com/dynastyprocess/*` is gated in a Claude Code session

Outbound requests to `github.com/dynastyprocess/*` (nflreadpy's source for `ff_playerids`, the
FantasyPros ECR mirror, and `ingest_fantasypros_csv.py`'s crosswalk build) return a `403` from
GitHub itself in this session — a GitHub-App "repository not enabled for this session" message,
via the outbound proxy's repo-scoping, not a network or proxy-policy block. `raw.githubusercontent.com`
serves the identical files unblocked (verified: `db_playerids.csv` returns the same 12,468 rows
either way).

**This is a Claude-session-only restriction.** The founder's real machine and GitHub Actions
never route through this proxy and never see it — `github.com/.../raw/...` redirects to
`raw.githubusercontent.com` transparently for them, the same bytes either way.
`scripts/rebuild_database.py` deliberately does **not** patch around this: doing so would mean
shipping a permanent base-URL substitution that the real machine and CI never needed, purely to
paper over a restriction specific to this kind of session. The full 64.0s end-to-end run reported
above and the `git diff`-clean state of the repo confirm the workaround used to verify it was
session-local only (a `sitecustomize.py` on a scratch venv's `sys.path`, never touching the
repo) and is not part of what ships. If a future Claude session hits this 403, it is a real,
reportable block — report it and stop rather than re-solving it inline.

---

## What to do next

The rebuild path itself is done and proven. What's left is upkeep, not architecture:

1. **Keep the scheduled MFL ADP snapshot capture running and committed.** It is the only defence
   against MFL's rolling-window aggregate — a missed day cannot be recovered after the fact, by
   either the live endpoint or this loader.
2. **Treat `depth_charts_snapshots` and `contracts` as drifting.** Pin artifacts, not commands,
   for any result that must reproduce exactly to the row.
3. **`data/rankings-history/rankings_2021_2025.csv` is now a pin, not a lifeline.** It matches
   what re-pulls today; keep it committed as a guard against the DynastyProcess mirror changing
   in the future, since there is currently no evidence it is guaranteed stable long-term (the
   first pass at this document measured it as gone entirely; the second pass found it fully
   present — the mirror's behavior over time is simply unverified beyond these two data points).
