# 2026-07-29 — Cloud-path rehearsal: clean clone, cold rebuild, both suites

**Role:** claude code session (cloud container, Linux)
**Ask:** Rehearse the cloud path. Clean clone from origin into a scratch directory outside the
repo — nothing copied across, no data folder — rebuild the database from scratch, run both test
suites against it. Report what had to be supplied by hand. This is the gate for moving to cloud.
**Founder request:** FR-020.

---

## Verdict

**The gate passes.** A clean clone produces a working project with both suites green, in ~9
minutes, with **zero credentials, zero `.env`, and no file that exists only on the founder's
machine.**

| Suite | Result |
|---|---|
| Backend (`pytest`) | **641 passed, 8 skipped, 0 failed** |
| Frontend (`npm test`) | **202 passed across 22 files, 0 failed** |
| Database | 22 tables, 2,856,629 rows, 854.4 MB |

But it does not pass *unattended*. Four things had to be supplied or worked around by hand, two
of which stop a fresh machine dead. All four are packaging-level. None is architectural.

This was run in a genuinely cold container: no Python packages, no `node_modules`, no
`data/nfl.db`. The rehearsal is therefore a real measurement, not a simulation.

---

## What had to be supplied by hand

### 1. `pandas` is missing from `requirements.txt` — **hard stop**

`pip install -r requirements.txt` installs nflreadpy, polars, pytest, scipy. Then:

```
ERROR collecting tests/test_ingest_fantasypros_csv.py
E   ModuleNotFoundError: No module named 'pandas'
!!!! Interrupted: 1 error during collection !!!!
```

Collection aborts — **not one test runs.** `pandas` is imported by **15 `src/` modules and 9
test modules**, including `make_board.py`, `backtest.py`, `export_contract.py`,
`live_availability.py` and `lambda_estimation.py`. This is a core dependency, not incidental.

`numpy` is also imported directly by project code and is not pinned either; it happens to be
installed as a scipy transitive. That is luck, not specification.

**Fix:** add `pandas` and `numpy` to `requirements.txt`. One line each.

### 2. No Python version is declared — **hard stop**

`scipy==1.18.0` requires Python >=3.12. The container's default `python3` is 3.11.15:

```
ERROR: Ignored the following versions that require a different python version:
       1.18.0 Requires-Python >=3.12
ERROR: No matching distribution found for scipy==1.18.0
```

The repo has no `.python-version`, no `pyproject.toml`, no `requires-python`, no setup script,
and no devcontainer. The **only** place 3.12 is written down anywhere in the repository is
`.github/workflows/adp-snapshot.yml`. `docs/environment.md` names a conda path
(`C:/Users/matth/miniconda3/...`) that means nothing off Windows.

Recreating the venv on `/usr/bin/python3.12` fixed it. A fresh machine has to guess.

**Fix:** add a `.python-version` pinning 3.12.

### 3. `identity.py` exits non-zero on a fresh database

The documented order runs `identity.py` third, before any rankings ingest:

```
sqlite3.OperationalError: no such table: rankings
  at identity.py:260 in coverage_report_for_board
```

`build_identity_tables()` commits first, so all three tables land correctly (49,391 / 12,468 /
57 — exact match to the documented figures). Only the trailing coverage *report* fails. But the
process exits non-zero, so any chained or CI-driven rebuild aborts here. Re-running `identity.py`
last, after rankings exist, succeeds and prints 98.5% board name-match.

Separately: **`identity.py` has no argparse at all.** The `--db <scratch>` shown for it in
`docs/can-we-rebuild-the-database.md` is silently ignored — it always writes `db.DB_PATH`.
Anyone following that documented command against a scratch path is writing to the real database.

### 4. The documented rebuild order is incomplete

After the four documented steps the suite is **18 failed, 614 passed, 9 errors** — every failure
tracing to missing `rankings` or `adp_snapshots`. This is exactly the silent-degradation failure
mode `can-we-rebuild-the-database.md` predicted, except louder: the suite does catch it.

The complete order, all with default paths:

| # | Command | Time |
|---|---|---|
| 1 | `python src/ingest_weekly_stats.py` | 37.9s |
| 2 | `python src/ingest_reference.py` | 37.8s |
| 3 | `python src/ingest_league_metrics.py` | 37.5s |
| 4 | `python src/ingest_rankings.py` | 4.3s |
| 5 | `python src/ingest_fantasypros_csv.py` | ~5s |
| 6 | `python src/ingest_mock_drafts.py data/real_drafts/2025_league_draft.json` | ~2s |
| 7 | `python src/ingest_mfl_adp.py` | ~2s |
| 8 | `python src/identity.py` — **last** | ~3s |

---

## Correction: the 2021–2025 rankings history IS re-pullable

`docs/can-we-rebuild-the-database.md` and `CURRENT-STATE.md` open item 9(c) both stated this was
permanently gone — "no source will sell it back at any price" — and it was cited as a reason
cloud migration was blocked. **That is wrong.**

`python src/ingest_rankings.py`, unmodified, in a fresh clone against an empty database, pulled
all six seasons in 4.3 seconds with plausible late-August pre-draft dates:

```
2021: 519 rows, as_of=2021-08-27      2024: 558 rows, as_of=2024-08-30
2022: 504 rows, as_of=2022-08-26      2025: 474 rows, as_of=2025-08-29
2023: 485 rows, as_of=2023-08-25      2026: 408 rows, as_of=2026-07-24
```

2021's top five reads McCaffrey (CAR) / Dalvin Cook (MIN) / Kamara (NO) / Adams (GB) / Elliott
(DAL) — correct for that preseason, not a current-board fallback.

Diffed row-for-row against the committed rescue export `data/rankings-history/rankings_2021_2025.csv`,
keyed on `(season, player_id, position)` across all 14 data columns (excluding the `ingested_at`
write stamp):

| | |
|---|---|
| Re-pulled 2021–2025 rows | 2,540 |
| Rescue CSV rows | 2,540 |
| Only in re-pull / only in CSV | 0 / 0 |
| Shared keys with any differing field | **0** |

Identical. Why the earlier measurement concluded otherwise was not diagnosed — it should not be
assumed the mirror is guaranteed stable. **Keep the rescue CSV committed**, but its role is now a
pin against future upstream change, not the last surviving copy.

Caveat on that pin: **there is no loader that reads it back into the database.** It is committed
and guarded by tests that read the file, but if the mirror ever does change, the CSV cannot
currently be used to restore the table.

---

## Remaining real gap: `adp_snapshots` history cannot be restored

`src/ingest_mfl_adp.py` has `export_snapshot_csv` and **no import counterpart.** The committed
`data/adp-snapshots/2026-07-26.csv` and `2026-07-28.csv` — ~478 rows of point-in-time ADP —
cannot be loaded back. A rebuild gets only the day's live pull (225 rows, against 451 in the
live DB).

The module's own docstring says *"the CSV is canonical, the DB a cache of it."* There is no code
that can rebuild that cache. Since MFL serves a rolling aggregate that cannot be backfilled,
this gap grows by one snapshot per day. **This is the only genuine remaining rebuild gap.**

Related, minor: re-running the capture on the same UTC day rewrites that day's CSV. Comparing
committed against regenerated for 2026-07-29, the ADP values are stable (`average_pick`,
`min_pick`, `max_pick` all unchanged) but `rank` differs on **8 of 225 rows** — every one an
exact tie on `average_pick` (Josh Allen / Bijan Robinson both 3.29; Hurts / Nico Collins both
31.29; Kelce / Houston both 82.8). The tie-break is unstable between runs, so the daily CSV is
not byte-reproducible from identical upstream data and the scheduled workflow will commit
spurious diffs.

---

## Cloud-specific findings (not fresh-machine problems)

**`github.com/dynastyprocess/data/raw/...` returns 403 inside any Claude Code session.**
`ingest_reference.py` fails on `ff_playerids`:

```
{"message":"GitHub access to this repository is not enabled for this session.
  Use add_repo to request access. ..."}
```

This is the session's GitHub repo-scoping, not upstream and not the egress policy —
`raw.githubusercontent.com` serves the identical file with a 200, and nflverse's
`releases/download/` URLs are unaffected (9 of 10 reference tables loaded fine). `add_repo`
cannot help: it rejects cross-owner adds, so no Claude session can reach a `dynastyprocess` URL.

nflreadpy 0.1.5 hardcodes the `github.com/.../raw/master/` form in `downloader.py:BASE_URLS`.
For the rehearsal that one base URL was repointed at `raw.githubusercontent.com` **in the scratch
venv only** — the repo was not modified. A normal cloud VM or GitHub Actions runner would follow
github.com's 302 to the same host and never see this.

**Consequence worth flagging:** `.github/workflows/adp-snapshot.yml` runs
`ingest_reference.py --only ff_playerids`. That works on GitHub Actions, but the same command
fails in a Claude cloud session — so the workflow cannot be debugged or dry-run from one.

**`tools/state.py` cannot run off Windows.** Line 30 hardcodes
`BACKEND_PYTHON = r"C:\Users\matth\miniconda3\envs\fantasyfootball\python.exe"`. Without
`--tests` it works; with `--tests` — the form CLAUDE.md's operating rules mandate for the
`CURRENT-STATE.md` build-state rows — it dies:

```
FileNotFoundError: [Errno 2] No such file or directory:
  'C:\\Users\\matth\\miniconda3\\envs\\fantasyfootball\\python.exe'
```

So the mandated write-back workflow is broken in cloud. `tools/handoffs.py sync`,
`tools/status_log.py sync` and `tools/founder_requests.py` all work fine and are idempotent.

**The PreToolUse safety hook does not run in cloud.** `.claude/settings.json:135` invokes the
hook through the same Windows interpreter. In a Linux container that command cannot spawn, so
`block_dangerous.py` — the thing `docs/environment.md` says is what actually stops dangerous
commands — is silently absent. Worth a deliberate decision rather than discovering it later.

`docs/environment.md` as a whole is Windows-only and misleading in cloud: no conda path, no
PreToolUse hook, no semicolon/chaining restriction (compound commands ran fine all session).

---

## Timings (measured, cold container)

| Phase | Step | Time |
|---|---|---|
| Setup | `git clone` | 2.0s |
| | `python3.12 -m venv` | 3.4s |
| | `pip install -r requirements.txt` | 26.6s |
| | `pip install pandas` (the missing dep) | 6.3s |
| Rebuild | 8 ingest steps (table above) | ~130s |
| Tests | `pytest` | 314.8s |
| | `npm ci` | 5.1s |
| | `npm test` | 40.2s |
| | **Total** | **~8m50s** |

`ingest_league_metrics.py` took 37.5s, not the "few minutes" the earlier doc budgeted — the
container is faster than the Windows box. Row counts matched documented figures exactly
(475,626 weekly stats; 49,391 / 12,468 / 57 identity; 27 league-season; 145+15=160 draft picks).

No drift was observed today in `contracts` (48,452) or `depth_charts_weekly` (865,329) — the
ingest log prints pre-dedup loaded counts (51,772 / 869,185), which is easy to misread as drift.

---

## Recommended next steps

| Priority | Action |
|---|---|
| 1 | Add `pandas` + `numpy` to `requirements.txt`. Blocks every fresh machine. |
| 2 | Add `.python-version` (3.12). Blocks every fresh machine with a 3.11 default. |
| 3 | Make `tools/state.py` resolve the interpreter via `sys.executable`. Unblocks mandated write-back in cloud. |
| 4 | Move `identity.py` last in the documented order, or guard its coverage report. |
| 5 | Add a CSV→DB loader to `ingest_mfl_adp.py`. The only remaining rebuild gap, and it grows daily. |
| 6 | Decide what replaces the PreToolUse safety hook in cloud. |
| 7 | Stabilise the ADP `rank` tie-break so the daily CSV is reproducible. |

Items 1–2 are one line each and are the whole difference between "a fresh machine works" and "a
fresh machine fails at the first command."

---

## Housekeeping

Scratch clone (`/tmp/.../scratchpad/cloudpath`, 1.6 GB) deleted. The real repo was never
modified during the rehearsal and this checkout has no `data/nfl.db` to touch. `docs/dashboard.html`
and `docs/roles-workflow-map.html` were not regenerated and are stale with respect to this session.
