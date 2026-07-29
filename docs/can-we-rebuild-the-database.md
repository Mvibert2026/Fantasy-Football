# Can `data/nfl.db` be rebuilt from the repo plus public sources?

**Measured 2026-07-29 by actually doing it** in a scratch directory. The live database was
opened read-only (`mode=ro`) and never written to.

---

## Answer

**Yes — verified end-to-end 2026-07-29 from a clean clone, both suites green, no credentials.**

> **Read this first.** Two claims below were measured against a scratch *database path* on the
> Windows box and are now superseded by a full clean-*clone* rehearsal on Linux. Corrections are
> marked inline and summarised in "Measured again 2026-07-29" at the end.
>
> 1. The 2021–2025 rankings history **does** re-pull, identically. It was reported here as
>    permanently unrecoverable. It is not.
> 2. The four-command rebuild sequence is **incomplete** — following it leaves the suite at
>    18 failed / 9 errors. The complete order is at the end of this document.
>
> What survives unchanged: the 99.3%/four-minute figure for the bulk tables, the drift warning
> on `depth_charts_snapshots` and `contracts`, and the look-ahead-bias warning on re-pulled ADP.

99.3% of the database by size — every play-derived, stat-derived and reference table — rebuilds
from a clean checkout with no credentials in **under four minutes**. The three artifacts this
document was written to flag are now all committed (thread 080, `bdda50e`), so they rebuild too.

**For the cloud-session decision:** the daily development loop is safe to move, and the full
build + test path has now actually been run in a cloud container rather than argued about. The
remaining gaps are packaging-level, not architectural — see the table at the end.

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

### 1. Rankings history, 2021–2025 — ~~NOT reproducible~~ **CORRECTED 2026-07-29: it re-pulls exactly**

**This section's original claim was wrong and is retained below only so the correction is
legible.** Measured 2026-07-29 in the clean-clone cloud rehearsal
(`docs/status/2026-07-29-cloud-path-rehearsal.md`): running the ingester itself, unmodified,
in a fresh clone with an empty database:

```
python src/ingest_rankings.py     # 4.3s
  2021: 519 rows, as_of=2021-08-27
  2022: 504 rows, as_of=2022-08-26
  2023: 485 rows, as_of=2023-08-25
  2024: 558 rows, as_of=2024-08-30
  2025: 474 rows, as_of=2025-08-29
  2026: 408 rows, as_of=2026-07-24
```

The 2,540 re-pulled 2021–2025 rows were then diffed row-for-row against the committed rescue
export `data/rankings-history/rankings_2021_2025.csv`, keyed on
`(season, player_id, position)` across all 14 data columns (`ingested_at` excluded — it is a
write-time stamp):

| | |
|---|---|
| Re-pulled rows | 2,540 |
| Rescue CSV rows | 2,540 |
| Only in re-pull | 0 |
| Only in rescue CSV | 0 |
| Shared keys with any differing field | **0** |

**Identical.** The DynastyProcess mirror does serve dated historical ECR snapshots, and each
season resolves to a plausible late-August pre-draft date. The original finding — reproduced
verbatim below — is superseded:

> The hard blocker. `ingest_rankings.py` pulls FantasyPros ECR via
> `nflreadpy.load_ff_rankings()` → DynastyProcess's public mirror. **That mirror serves only the
> current scrape.** Today it carries exactly one snapshot date: `2026-07-24`. Tested using the
> ingester's own `resolve_snapshot_date`: 2021–2025 all **NOT re-pullable**, only 2026 resolves.
> Delete the DB and the entire pre-2026 expert-consensus baseline is gone permanently.

Why the original measurement disagreed has not been diagnosed. Do not assume the mirror is
guaranteed stable — **keep `rankings_2021_2025.csv` committed.** Its value is now as a *pin*
against future upstream change, not as the only surviving copy. Note there is currently **no
loader that reads it back into the DB**; none is needed while the re-pull matches, but that
means the pin cannot actually be used if the mirror does change. See the rehearsal narrative.

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

Items 1–3 were **done** in thread 080 (`bdda50e`) and the artifacts are committed. Items 4–5
stand. The rehearsal on 2026-07-29 then found a further set — see below.

1. ~~Commit the 160-pick real draft as a fixture.~~ Done — `tests/fixtures/real_draft_2025/`.
   Note the ingestible copy is `data/real_drafts/2025_league_draft.json`; the `tests/fixtures/`
   export is a table dump the ingester rejects.
2. ~~Commit the four `data/raw/founder-export/` files.~~ Done — `.gitignore` now exempts them.
3. ~~Export `rankings` 2021–2025 to CSV and commit it.~~ Done — and per the correction above,
   it turns out to re-pull identically anyway. Keep it as a pin.
4. Keep the scheduled MFL ADP snapshots running and committed — they are the only defence
   against a rolling window.
5. Treat `depth_charts_snapshots` and `contracts` as drifting. Pin artifacts, not commands, for
   any result that must reproduce exactly.

## Measured again 2026-07-29 — full clean-clone rehearsal

The rebuild above was measured against a scratch *database path*. It has now been measured
against a scratch **clone**: fresh `git clone`, no `data/*.db`, nothing copied across, on Linux
with no preinstalled dependencies. Narrative and full timings in
`docs/status/2026-07-29-cloud-path-rehearsal.md`.

**Result: both suites green — 641 backend passed / 8 skipped, 202 frontend passed — in ~9
minutes wall clock, with zero credentials and zero `.env`.** No source needed a login. That is
the cloud gate, and it passes.

Four things had to be supplied by hand that a clean clone does not provide:

| # | What | Fix |
|---|---|---|
| 1 | `pandas` is imported by 15 `src/` modules and 9 tests but is **absent from `requirements.txt`**. Collection aborts outright. | Add `pandas` (and pin `numpy`, currently present only as a scipy transitive). |
| 2 | **No Python version is declared anywhere** except `.github/workflows/adp-snapshot.yml`. `scipy==1.18.0` requires >=3.12; the default `python3` on a stock image is often 3.11, and the install fails hard. | Add a `.python-version` / `requires-python`. |
| 3 | The documented 4-step order runs `identity.py` before any rankings ingest, so it **exits non-zero** on `no such table: rankings`. Its table writes commit first, so it is cosmetic — but it breaks any chained or CI-driven rebuild. | Reorder, or guard the coverage report. |
| 4 | The rebuild order in this doc is **incomplete**. After the 4 documented steps the suite is 18 failed / 9 errors, all tracing to missing `rankings` / `adp_snapshots`. | The full order is below. |

**The actual complete rebuild order**, all with default paths, from a clean clone:

```
python src/ingest_weekly_stats.py                                  # 37.9s
python src/ingest_reference.py                                     # 37.8s
python src/ingest_league_metrics.py                                # 37.5s
python src/ingest_rankings.py                                      #  4.3s
python src/ingest_fantasypros_csv.py                               #  ~5s
python src/ingest_mock_drafts.py data/real_drafts/2025_league_draft.json
python src/ingest_mfl_adp.py
python src/identity.py                                             # last -- needs rankings
```

Yielding 22 tables / 2,856,629 rows / 854.4 MB, and a fully green suite.

**Note `identity.py` takes no `--db` argument** — it has no argparse at all and always writes
`DB_PATH`. The `--db <scratch>` shown for it earlier in this document is silently ignored, and
following it writes to the real database.

**Still unrestorable: `adp_snapshots` history.** `src/ingest_mfl_adp.py` has
`export_snapshot_csv` but no import counterpart, so the ~478 rows of point-in-time ADP sitting
in the committed `2026-07-26` and `2026-07-28` CSVs cannot be loaded back. A rebuild gets only
today's pull (225 rows against the live DB's 451). The module docstring calls the CSV canonical
and the DB a cache of it — there is currently no code that can rebuild that cache. **This is
the one genuine remaining rebuild gap, and it grows by one snapshot a day.**
