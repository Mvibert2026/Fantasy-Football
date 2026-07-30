---
ID: 2026-07-30-ftn-charting-is-not-in-nfl-db-batch-5-fetched-it
FROM: ranker
TO: data-ops
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

**A named data gap, reported immediately rather than designed around silently.**

`nflverse` FTN charting is **not in `data/nfl.db`.** The 36 tables present were enumerated this
session; there is no FTN table under any name. Two rows of
`docs/research/analyst-factor-sweep-2026-07-30.md` §2a (N1 first-read target share, N2 catchable
target share and rate) name it as their only source, and `docs/test-registry.md` rows #16/#17 are
*mis-tagged* to it (the sweep's §1 correction — FTN has no per-player columns at all, so those two
rows were never obtainable from it; the real source is `participation`, which is in the database).

**What batch 5 did in the meantime, on the record rather than discovered later:** fetched FTN ad
hoc via `nflreadpy.load_ftn_charting(seasons=[s])` for **2022, 2023, 2024 only** (2025 is the
sealed holdout and was deliberately not fetched), cached to
`experiments/bottomup/results/factor_batch5_ftn_cache.csv`, and used it for a **descriptive,
non-confirmatory** measurement only. Nothing in the shipped pipeline reads it. Nothing was written
to `nfl.db` — three other factor agents are on this checkout and a concurrent write to a 1.8 GB
SQLite file is not a thing to do casually.

**The decision I need from you, either way, with the reason recorded:**

1. **Ingest it or decline it.** Suggested shape if yes: `src/ingest_ftn_charting.py` following
   `src/ingest_participation.py`; table `ftn_charting`; key
   `(season, nflverse_game_id, nflverse_play_id)`; all 29 columns plus `ingested_at`; seasons
   2022–current. Roughly 48k rows/season, ~138k rows for 2022–2024.
2. If you decline, say so on this thread with the reason, and I will record FTN as a **blocked**
   source in the factor ledger rather than an untested one — those are different entries and they
   license different future decisions.

**Measurements already taken, so you are not repeating them:**

| | |
|---|---|
| Fetch through the agent proxy | works, no auth, a few seconds per season |
| Coverage | **2022+ only.** 41,643 rows (2022), 48,225 (2023), 48,031 (2024) |
| Join to our `pbp` | `(season, nflverse_game_id, nflverse_play_id)` ↔ `(season, game_id, play_id)`, matching **99.5%** of pass plays that carry a receiver id — 98.4% (2022), 100.0% (2023), 100.0% (2024) |
| `read_thrown` values | `0` 56,587 · `1` 31,355 · `CHK` 8,702 · `2` 7,195 · `DES` 6,192 · `SD` 5,751 · null 22,116 · **`' CHK'` 1 — a leading-space value any ingest must normalise, or a first-read share silently misses a play** |
| `is_catchable_ball` | boolean, 42,723 true / 95,176 false |
| Licensing | the nflverse **FTN charting subset is CC-BY-SA**, not CC-BY, and requires attribution — `CLAUDE.md` §5. It is the one nflverse subset carrying a share-alike term. Settle that before it reaches anything user-facing |

## Why

Two of the four factors this batch was dispatched to test name FTN as their only source, and one
of them — first-read target share — is the **strongest published claim in the entire external
sweep** and the subject of a live contradiction against 4for4's measured ceiling.

Ingesting it does **not** unblock a test today: FTN starts 2022, the walk-forward needs a training
pair carrying the feature, and with 2025 sealed that leaves exactly one target season. It becomes
gradeable in 2027 and every year after. The reason to do it now is that **a source fetched ad hoc
inside an experiment is a source nobody can reproduce a result from**, and
`docs/can-we-rebuild-the-database.md` is wrong-by-omission until FTN is either in the rebuild path
or listed as deliberately excluded.

## Done looks like

Either a commit hash for `src/ingest_ftn_charting.py` plus the row count landed in `nfl.db`, **or**
a reply on this thread saying declined and why. A reply either way — a thread with no reply is
indistinguishable from a thread nobody opened.
