# Can `data/nfl.db` be rebuilt from the repo plus public sources?

**Measured 2026-07-29 by actually doing it** in a scratch directory. The live database was
opened read-only (`mode=ro`) and never written to.

---

## Answer

**Structurally yes, historically no.**

99.3% of the database by size — every play-derived, stat-derived and reference table — rebuilds
from a clean checkout with no credentials in **under four minutes**. What does *not* rebuild is
small, and it is precisely the part the modelling work rests on: the **2021–2025 rankings
history**, the **2026 half-PPR board input**, and the **single real draft the availability model
was calibrated against**.

**For the cloud-session decision:** the daily development loop is safe to move. Nothing in the
build, test, or export path needs the local machine. But three artifacts exist *only* on this
Windows box and are gitignored. **They must be committed or re-exported before a cloud session
becomes the primary environment**, or they are one disk failure from gone — and two of them
cannot be regenerated from any source, at any price.

---

## What was measured

| | Real DB | Rebuilt from scratch |
|---|---|---|
| Size | 813.7 MB | 807.8 MB |
| Rows | 2,847,285 | 2,790,777 |
| Wall clock | — | **97.2 s** (two scripts) + a play-by-play pass |

Rebuild commands, in order, each against a scratch `--db` path:

```bash
python src/ingest_weekly_stats.py --db <scratch>   # 22.2s -> 475,626 rows
```
```bash
python src/ingest_reference.py --db <scratch>      # 75.0s -> 9 nflverse tables
```
```bash
python src/identity.py --db <scratch>              # 12,468 / 49,391 / 57
```
```bash
python src/ingest_league_metrics.py --db <scratch> # 27 rows; slowest step
```

`ingest_league_metrics.py` scans play-by-play for 1999–2025 and dominates the remaining runtime;
budget a few minutes. Total realistic cold rebuild: **~4 minutes**, network-bound, no login.

---

## Reproducible — exact row-for-row match

| Table | Rows | Source |
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

All free, all public, no API key, no login. nflverse is CC-BY (FTN charting subset CC-BY-SA —
attribution required, CLAUDE.md §5).

## Reproducible but **drifts** — rebuild is not byte-identical

| Table | Real | Rebuilt | Delta |
|---|---|---|---|
| `depth_charts_snapshots` | 926,335 | 935,857 | **+9,522** |
| `contracts` | 48,404 | 48,452 | **+48** |

These upstream feeds are *live*, not archival. A rebuild today gives you today's state, not the
state captured when the DB was built. Harmless for most work; **not harmless for reproducing a
past backtest number exactly.** If a result must be reproducible to the row, it needs the
artifact pinned, not the rebuild command.

---

## NOT reproducible

### 1. Rankings history, 2021–2025 — `rankings` (3,487 rows) + `rankings_quarantine` (36)

The hard blocker. `ingest_rankings.py` pulls FantasyPros ECR via
`nflreadpy.load_ff_rankings()` → DynastyProcess's public mirror. **That mirror serves only the
current scrape.** Today it carries exactly one snapshot date: `2026-07-24`.

Tested using the ingester's own `resolve_snapshot_date`, not a reimplementation:

| Season | Result |
|---|---|
| 2021 | **NOT re-pullable** — no `redraft-overall` snapshot in 2021-03-01 … 2021-08-31 |
| 2022 | **NOT re-pullable** |
| 2023 | **NOT re-pullable** |
| 2024 | **NOT re-pullable** |
| 2025 | **NOT re-pullable** |
| 2026 | re-pullable — `as_of=2026-07-24`, `preseason_final=False` |

Those five seasons were captured when the mirror still served them. **Delete the DB and the
entire pre-2026 expert-consensus baseline is gone permanently.** Since CLAUDE.md §6.5 makes
consensus the yardstick every ranking version is scored against, losing it does not degrade the
backtest — it removes the ability to run one on those seasons at all.

### 2. The 2026 half-PPR board input — not in the repo at all

`ingest_fantasypros_csv.py` reads
`data/raw/founder-export/2026-07-27/FantasyPros_2026_Draft_ALL_Rankings.csv`.

`.gitignore:2` excludes `data/raw/`. Four founder-export files exist on disk and in no commit:

- `FantasyPros_2026_Draft_ALL_Rankings.csv` ← the half-PPR board source
- `fantasypros-all-rankings.csv`
- `three-analyst-rankings.csv`
- `underdog-adp.csv`

This is a manual export from a logged-in FantasyPros session. It is the *only* half-PPR-native
ranking input in the project — `ingest_rankings.py` deliberately stays on the non-half-PPR
DynastyProcess mirror because the FantasyPros free API tier caps every response at 10 rows.
Re-exporting requires a FantasyPros account and produces a *current* file, not the 2026-07-27
one.

### 3. The real draft — `mock_drafts` (1) + `mock_picks` (145) + `mock_pick_quarantine` (15)

The single `mock_drafts` row is `mock_id=2025_league_draft_real`, `platform=manual`,
`source=user_provided_screenshots`, `drafted_at=2025-08-30`.

145 + 15 = **160 picks — the n=160 that `DEFAULT_LAMBDA = 0.352` was fit from**
(`live_availability.py`, conditional-logit, se=0.070, z=5.04). It is the only real-draft
calibration anchor in the project, it was transcribed by hand from screenshots, and **it exists
in no public source and in no commit.** If the DB is lost, λ reverts from measured to guessed,
and the availability model's "calibrated" claim becomes unsupportable.

Highest-value, lowest-effort fix available: commit these 161 rows as a CSV or JSON fixture.

### 4. ADP snapshots — `adp_snapshots` (451 rows)

Subtler. MFL's endpoint **does** serve historical periods:

| Period | Players | totalDrafts | Server timestamp |
|---|---|---|---|
| 2021 | 277 | 2,322 | today |
| 2023 | 279 | 3,030 | today |
| 2025 | 263 | 1,300 | today |
| 2026 | 225 | 43 | today |

But every response is stamped **today** and returns the *accumulated* aggregate. The 2021 figure
reflects 2,322 drafts across that whole cycle, including drafts run after any realistic 2021
draft date. Re-pulling it and treating it as a preseason board is **textbook look-ahead bias**
(CLAUDE.md §6.1) — the numbers would look fine and be wrong.

Note also that 2026 `totalDrafts` reads **43 today versus 50 in the 2026-07-26 committed CSV**.
The window is rolling, and it can move *down*. MFL is not an archive.

---

## Are the committed ADP snapshot CSVs sufficient to restore the rankings history?

**No — and they are not the same kind of thing.** Only two are committed:
`data/adp-snapshots/2026-07-26.csv` and `2026-07-28.csv`.

Three independent reasons, each sufficient on its own:

1. **Wrong source.** Their `adp_source` is `mfl_proxy` — observed market ADP, feeding
   `adp_snapshots`. The rankings history is FantasyPros ECR — aggregated expert opinion, feeding
   `rankings` (`ranking_source='expert'`). CLAUDE.md §4 requires ranking sources stay separate
   and never blended. Substituting one for the other is a **spec violation, not a workaround**.
2. **Wrong period.** Both files are July 2026. Neither contains a single row for 2021–2025.
3. **Wrong scale.** 232 rows in the 2026-07-26 file against 3,487 rows of rankings history.

What those two CSVs *are* is genuinely valuable, for a different reason: since MFL serves only a
rolling current aggregate, they are the only point-in-time capture of that window that exists.
**Keep taking them.** They just cannot backfill a different source's history.

---

## What to do before moving to cloud sessions

Ordered by consequence. The first three are the whole risk.

1. **Commit the 160-pick real draft** as a fixture. Unreproducible, irreplaceable, tiny, and the
   sole empirical basis for λ.
2. **Commit the four `data/raw/founder-export/` files**, or carve an exception into
   `.gitignore:2` for that directory. Check FantasyPros redistribution terms first (CLAUDE.md
   §5/§10) — if committing is not permissible, back them up outside git and say where.
3. **Export the `rankings` table for 2021–2025 to CSV and commit it.** Five seasons of expert
   consensus that no source will sell back at any price.
4. Keep the scheduled MFL ADP snapshots running and committed — they are the only defence
   against a rolling window.
5. Treat `depth_charts_snapshots` and `contracts` as drifting. Pin artifacts, not commands, for
   any result that must reproduce exactly.

With 1–3 committed, a cloud session can rebuild a complete, correct database in ~4 minutes from
a clean checkout with no credentials. Without them, a cloud session silently rebuilds a database
that is missing the history — and every script still runs green, because nothing currently
asserts those rows exist.
