# Time-series and as-of-date data audit — 2026-07

**Thread:** [057](../handoffs/057-timeseries-data-audit.md) · **Role:** researcher · **Date:** 2026-07-27

Confidence tags used throughout, per `docs/operating-model.md`:
`[VERIFIED]` fetched from the source's own page/API · `[SNIPPET]` seen only in a search excerpt ·
`[SECONDARY]` third-party reporting only · `[MODAL-SAMPLED]` derived from real instances ·
`[GAP]` could not establish · `[BLOCKED]` fetch refused; recorded and stopped, not routed around.

**Session constraint, stated up front:** this session had no shell and no Python. Every finding below
comes from HTTP fetches of source APIs and files. Nothing was computed against `nfl.db`. Where the
thread asked for a row count that requires the database, the answer is `[GAP]` with the exact query
specified for `data-ops` — not an estimate.

---

## 0. Headline

| Question | Answer |
|---|---|
| Are nflverse injury tables point-in-time or retroactively revised? | **POINT-IN-TIME at weekly granularity. Confidence HIGH.** Backtests using them do **not** leak the future. Six-link evidence chain in §2.4 — builder source code (§2.2b), a full 15-season archive census (§2.2), and real row timestamps (§2.3). One residual: two small byte-deltas whose content I could not diff, bounded at ≤0.03% of two seasons and structurally unable to touch 2009–2021. |
| Is that the biggest problem with the injury data? | **No.** The bigger problem is that the source **died after the 2024 season**. §2.5. |
| Should forward ADP snapshotting start now? | **Yes, today.** §1. |
| Free structured source for suspensions? | **None obtainable.** Two candidates returned HTTP 403 on `robots.txt`; a third is prohibited by ToS. Hand-maintained table required. §4. |
| Which Addendum 2 directions survive? | Three of four, one of them re-scoped. §6. |

---

## 1. ADP — forward snapshot fallback

*(The historical-harvest and Sleeper sub-items were struck from this thread by the reconciliation
pass and belong to [055](../handoffs/055-ffc-adp-history-harvest.md) and
[054](../handoffs/054-ftn-and-sleeper-harvest.md) § 2. Not re-answered here.)*

**Recommendation: start the forward snapshot immediately.** Not because the historical question is
settled — it isn't, it's 055's — but because the two are independent. A snapshot not taken on
2026-07-27 can never be taken. `docs/CURRENT-STATE.md` already lists this as open item #2 and calls it
"unrecoverable if delayed"; nothing in this audit softens that.

**Fantasy Football Calculator `robots.txt`** `[VERIFIED]` (fetched 2026-07-27):

```
User-agent: *
Disallow: /api/
Disallow: /ajax/
Disallow: /ajax-v2/
Disallow: /import/
Disallow: /adp/csv/
Disallow: /draft/
Disallow: /rate-my-team/results/
Disallow: /rankings/custom/

Sitemap: https://fantasyfootballcalculator.com/sitemap.xml
```

This independently confirms the premise D-021 was decided on: the **CSV path (`/adp/csv/`) and the
API are disallowed; the HTML `/adp/` pages are not**. The D-021 constraints (HTML only, ≤1 req/sec,
cached, honest User-Agent) are consistent with this file.

**Fetch vs. redistribute:** robots.txt governs crawling only. FFC's own terms of use were **not**
fetched this session — `[GAP]`. Under D-021 the product is private and founder-only, so
redistribution does not arise today; it becomes a live question the moment a second human sees the
output, and D-021 already says it is void at that point.

**Second free forward series, at no extra cost:** Sleeper's `/v1/players/nfl` carries a `search_rank`
field alongside the injury fields in §5. Snapshotting it daily gives a second, independent
draft-sentiment series from the same job. `[VERIFIED]` — field list fetched from `docs.sleeper.com`.

**Not started by me.** Ingestion is `data-ops`' file boundary; this section is a recommendation, not
an action.

---

## 2. nflverse injuries — the question that actually matters

### 2.1 What exists

`[VERIFIED]` — GitHub Releases API, `nflverse/nflverse-data`, release tag `injuries`.

Per-season assets `injuries_{YYYY}` in `.csv`, `.parquet`, `.rds`, `.qs` (plus `.csv.gz` from 2023).
**Seasons present: 2009–2025.**

**Schema, 2009–2024** — header read verbatim from `injuries_2015.csv` and `injuries_2022.csv`; the
two are byte-identical strings `[VERIFIED]`:

```
season,game_type,team,week,gsis_id,position,full_name,first_name,last_name,
report_primary_injury,report_secondary_injury,report_status,
practice_primary_injury,practice_secondary_injury,practice_status,date_modified
```

**Schema, 2025 — different** `[VERIFIED]`, header read verbatim from `injuries_2025.csv`:

```
season,season_type,game_type,team,week,gsis_id,position,full_name,first_name,last_name,
report_primary_injury,report_secondary_injury,report_status,
practice_primary_injury,practice_secondary_injury,practice_status
```

Gains `season_type`. **Loses `date_modified`.** This confirms the note in `docs/CURRENT-STATE.md`
("2025 has no `date_modified` column upstream yet") — and corrects the word *yet*: see §2.5.

Observed values `[MODAL-SAMPLED]` from real rows:
- `report_status` — `Out`, `Questionable`, `Doubtful`, empty.
- `practice_status` — `Did Not Participate In Practice`, `Limited Participation in Practice`,
  `Full Participation in Practice`, empty.
- `practice_primary_injury` carries the non-injury sentinel `Not injury related - resting player`.
- **Parser hazard, real:** `injuries_2022.csv`, ARI week 4, Kelvin Beachum, contains the typo
  `Did Not Participation In Practice`. Any ingest that maps `practice_status` to an enum by exact
  match will silently drop or quarantine rows like this. Worth a targeted assertion.

### 2.2 The distribution layer: are published files rewritten?

Every asset's `created_at` equals its `updated_at`. On GitHub an asset cannot be patched in place —
re-publishing replaces it and resets `created_at` — so this timestamp is **the date of the file's
most recent write**. `[VERIFIED]`:

| Season | Last written | Elapsed since |
|---|---|---|
| 2009–2020 | 2022-07-26 | ~4.0 years |
| 2021 | 2022-08-31 | ~3.9 years |
| 2022 | 2023-08-31 | ~2.9 years |
| 2023 | 2024-09-04 | ~1.9 years |
| 2024 | 2025-02-13 | ~1.4 years |
| 2025 | 2026-03-18 | ~0.4 years |

That alone does not prove content stability, because a re-upload resets the clock. So I diffed
against **`nflverse/nflverse-data-archives`** — a sibling repo that snapshots every nflverse release
on a schedule ("At 15:15 on Thursdays every week in Sep - Jan; at 15:15 on the 15th day of each month
from Feb -> Aug", `[VERIFIED]` from `.github/workflows/run_archive.yaml`). 97 dated archive tags
exist, `archive-2023-04-15` through `archive-2026-07-15`.

**Byte-size census of `injuries_*.rds`, three points in time, 3.3 years apart** `[VERIFIED]`:

| Season | archive-2023-04-15 | archive-2024-06-15 | live 2026-07-27 | Verdict |
|---|---|---|---|---|
| 2009 | 84,620 | 84,620 | 84,620 | stable |
| 2010 | 90,893 | 90,893 | 90,893 | stable |
| 2011 | 97,843 | 97,843 | 97,843 | stable |
| 2012 | 106,024 | 106,024 | 106,024 | stable |
| 2013 | 98,857 | 98,857 | 98,857 | stable |
| 2014 | 99,950 | 99,950 | 99,950 | stable |
| 2015 | 103,453 | 103,453 | 103,453 | stable |
| 2016 | 98,101 | 98,101 | 98,101 | stable |
| 2017 | 99,519 | 99,519 | 99,519 | stable |
| 2018 | 98,212 | 98,212 | 98,212 | stable |
| 2019 | 104,317 | 104,317 | 104,317 | stable |
| 2020 | 111,429 | 111,429 | 111,429 | stable |
| 2021 | 112,850 | 112,850 | 112,850 | stable |
| **2022** | **113,405** | **113,416** | 113,416 | **CHANGED**, +11 bytes, on 2023-08-31 |
| **2023** | (absent) | **113,409** | **113,447** | **CHANGED**, +38 bytes, on 2024-09-04 |

Read that carefully, because it is the finding:

- **Thirteen completed seasons (2009–2021) are byte-identical across a 3.3-year window.** nflverse
  does not sweep back and rewrite closed seasons.
- **Two seasons were rewritten exactly once each**, roughly 8–12 months after the season ended,
  coinciding with the start of the following season. The deltas are +11 and +38 bytes in a
  ~113 KB compressed file — of order 0.01–0.03%.
- What changed is `[GAP]`. A size fingerprint cannot distinguish "two rows appended" from "three
  field values edited". See §2.6 for the exact diff to run.
- Sample quality: this is a **full census** of the seasons available, not a sample. Fifteen files,
  every season present in the archive. That is the good case.
- Caveat: identical size is strong but not conclusive evidence of identical content. A same-length
  substitution (`Q` → `O` in `report_status`) would be invisible to this test. Hash comparison is
  the honest closing move, specified in §2.6.

### 2.2b The mechanism: what the builder source code actually does

The size census tells you *that* files are stable. The builder tells you *why*, and it is the
strongest evidence in this audit because it is not inference from artefacts — it is the code.

The injuries builder is **not** in `nflverse-data`. It lives in **`nflverse/nflverse-rosters`**
(`exec/update-injuries.R`, driven by `.github/workflows/update_injuries.yaml`). All `[VERIFIED]`,
quoted verbatim from `raw.githubusercontent.com`:

```r
scrape_ir <- function(year, week, game_type) {
  h <- httr::handle("https://www.nfl.info")
  ...
      path = glue::glue(
        "/nfldataexchange/dataexchange.asmx/getInjuryData?lseason={year}&lweek={week}&lseasontype={game_type}"
      ),
      httr::authenticate(Sys.getenv("NFLDX_USERNAME", "media"), Sys.getenv("NFLDX_PASSWORD", "media")),
```

Four things fall out of this, each of which independently supports the verdict:

1. **The endpoint is keyed by `(lseason, lweek, lseasontype)`.** You do not request "the injury
   report"; you request *week 3 of 2015*. The unit of retrieval is the week, which is why the data
   has the shape it has.
2. **`date_modified` is passed through from the NFL's own record, not synthesized at pull time.**
   Verbatim from the same file:
   `date_modified = lubridate::as_datetime(ModifiedDt, format = "%s")`.
   `ModifiedDt` is an epoch timestamp emitted by the NFL Data Exchange. This is what makes the §2.3
   test valid: if nflverse stamped rows at fetch time, every row in `injuries_2022.csv` would read
   `2023-08-31` (its rebuild date). They read September 2022.
3. **Only the most recent season is rebuilt.** The live call at the end of the script is
   `build_ir(nflreadr:::most_recent_season())`; the full-history rebuild
   `# build_ir(2009:nflreadr:::most_recent_season())` **is commented out** `[VERIFIED]`. This is
   the exact mechanism behind the census in §2.2 — 2009–2021 frozen, one rewrite of whichever
   season was "most recent" at the time.
4. **The scheduled job is disabled.** `update_injuries.yaml` is `workflow_dispatch` only; the
   `'0 7 * * *'` daily cron is commented out `[VERIFIED]`. That explains the one-bulk-write-per-season
   pattern and why nothing appeared in-season for 2025.

**Licence / access, and a warning.** The upstream is the **NFL Data Exchange** — a credentialed feed
at `www.nfl.info`, using HTTP Basic auth from `NFLDX_USERNAME` / `NFLDX_PASSWORD`. It is not a public
API. The code carries the fallback defaults `"media"` / `"media"`.

> **Do not use those credentials.** They are a third party's access, not ours; using them would be
> unauthorised access to a credentialed system, and no part of this project should call that
> endpoint. Recorded here so a future session recognises it and does not "helpfully" try it.

This also explains §2.5: nflverse's injury source "dying after the 2024 season" means their NFLDX
access lapsed. It is not a scraper we could fix.

### 2.3 The semantic layer: does a week-3 row reflect week 3?

The distribution test above says *the file* isn't rewritten. It does not say *the rows* were
contemporaneous when first written. `date_modified` answers that, and I read real rows.

`[VERIFIED]` — rows reproduced verbatim from the release CSVs:

**`injuries_2015.csv`** (2015 week 1 ran Sep 10–14; week 3 ran Sep 24–28):

| Week | Player | `date_modified` |
|---|---|---|
| 1 | Ifeanyi Momah (ARI) | `2015-09-09T14:14:17Z` |
| 1 | Mike Iupati (ARI) | `2015-09-11T13:06:02Z` |
| 1 | Michael Floyd (ARI) | `2015-09-11T13:05:52Z` |
| 3 | J.J. Nelson (ARI) | `2015-09-25T13:15:48Z` |
| 3 | Andre Ellington (ARI) | `2015-09-25T13:15:55Z` |
| 3 | Mike Iupati (ARI) | `2015-09-25T13:16:01Z` |

**`injuries_2022.csv`** (2022 week 1 ran Sep 8–12; week 2 Sep 15–19; week 4 Sep 29–Oct 3):

| Week | Player | `date_modified` |
|---|---|---|
| 1 | Rodney Hudson (ARI) | `2022-09-07T21:10:03Z` |
| 1 | Aaron Brewer (ARI) | `2022-09-09T19:55:06Z` |
| 1 | Markus Golden (ARI) | `2022-09-09T19:55:29Z` |
| 2 | Kelvin Beachum (ARI) | `2022-09-14T21:34:51Z` |
| 2 | Rodney Hudson (ARI) | `2022-09-14T21:35:19Z` |
| 2 | Zach Ertz (ARI) | `2022-09-16T20:02:30Z` |
| 4 | Kelvin Beachum (ARI) | `2022-09-28T19:09:34Z` |
| 4 | Zach Ertz (ARI) | `2022-09-28T19:09:58Z` |
| 4 | James Conner (ARI) | `2022-09-30T18:00:19Z` |

Every timestamp falls inside its own game week — on the Wednesday or the Friday, which are the NFL
injury-report filing days. Not one row carries a later-season or later-year stamp.

The strongest single data point: **`injuries_2022.csv` was rewritten on 2023-08-31, and its rows
still carry September-2022 timestamps.** The re-pull did not restamp. Asked directly whether any row
in the readable portion carried a `date_modified` of 2023 or later, the answer was **none seen**.

### 2.4 Verdict

> **POINT-IN-TIME, at weekly granularity. Confidence: HIGH.**
> nflverse injury rows for 2009–2024 reflect what was filed during their own game week. Backtests
> that use them are not fiction, and the bottom-up prototype's games-played work is not leaking the
> future through this table.

**The evidence chain, so a future session can audit the verdict rather than inherit it:**

| # | Claim | Evidence | Tag |
|---|---|---|---|
| 1 | `date_modified` is the NFL's own record-modification time, not nflverse's fetch time | `date_modified = lubridate::as_datetime(ModifiedDt, format = "%s")` in `exec/update-injuries.R` | `[VERIFIED]` source |
| 2 | Retrieval is keyed by week — you ask for week 3 and get week 3 | `getInjuryData?lseason=&lweek=&lseasontype=` | `[VERIFIED]` source |
| 3 | Only the most-recent season is ever rebuilt | live `build_ir(most_recent_season())`; full rebuild commented out | `[VERIFIED]` source |
| 4 | Sampled rows carry timestamps inside their own game week | 15 rows, 2 seasons, §2.3 | `[VERIFIED]` data |
| 5 | A file re-pulled 8 months later still carries the original timestamps | `injuries_2022.csv`, rebuilt 2023-08-31, rows read September 2022 | `[VERIFIED]` data |
| 6 | 13 of 15 season files are byte-identical over 3.3 years | archive census, §2.2 | `[VERIFIED]` full census |

Claim 5 is the one that actually settles it. If the NFL's upstream records for 2022 had been amended
with later knowledge, the 2023 re-pull would have brought the amended `ModifiedDt` values with it.
It didn't.

**What I could not close, stated precisely** — so nobody re-runs it:

- **The +11 and +38 byte deltas remain uncharacterised.** I could not obtain a byte-level content
  diff. Ruled out this session: (a) `nflverse-data-archives` stores **only `.rds`** — verified in
  `R/archive.R`, `file_type = ".rds"` — which is compressed binary and unreadable without a shell;
  (b) **Wayback Machine is not fetchable by this tool** (`Claude Code is unable to fetch from
  web.archive.org`), so no archived CSV copy was reachable; (c) no shell, so no hashing, no
  decompression, no row-level diff; (d) `nflverse-data`'s `NEWS.md`, `README.md` and `nflreadr`'s
  changelog contain **no revision/backfill policy statement at all** — checked, all three, nothing;
  (e) no third-party repo with a vendored dated copy of `injuries_20XX.csv` surfaced in search.
- Bound on the unknown: ≤ ~0.03% of two seasons' files, and by claim 3 it cannot touch 2009–2021.
- Given claim 3, the 2023-08-31 rewrite of the 2022 file was a routine `most_recent_season()` refresh
  (the 2023 season had not yet started), i.e. a re-pull of 2022's weeks from NFLDX. Combined with
  claim 5, the most likely content is **rows added** — plausibly late-filed or postseason rows
  carrying their own in-season timestamps — rather than rows amended. That last sentence is an
  **inference, not a finding**, and is labelled as such.

Three caveats that must travel with the verdict, none of which overturn it:

1. **Weekly, not daily.** There is one row per player-week carrying its *last* update. The Wed →
   Thu → Fri practice progression is collapsed. You cannot reconstruct "what did I know on Thursday
   of week 8"; you get "what was true by the last filing of week 8". For pre-draft ranking backtests
   (season N−1 data → season N ranking) this is irrelevant. For in-season Thursday start/sit
   simulation it is a real look-ahead of up to ~48 hours and must not be waved through.
2. **A narrow late-correction window on the most recent completed season.** Seasons 2022 and 2023
   each received one small rewrite around the start of the *following* season. A backtest drafting
   in August of year N reads a season N−1 file that may not have received that rewrite yet. Magnitude
   ~0.01–0.03% of the file. It does not invalidate anything; it should be characterised once (§2.6)
   rather than assumed to be zero.
3. **Sample quality, stated honestly.** The row-level test is 15 rows across 2 seasons, and because
   the files are team-sorted, every row is Arizona. That is *not* a representative sample of rows.
   It is, however, a test of a **pipeline-level mechanism** — whether `date_modified` tracks the
   week — and a mechanism either holds globally or it doesn't. It cannot detect *sparse* retroactive
   edits elsewhere in the file. The census in §2.2 is the check that covers that, and it is clean for
   13 of 15 seasons.

**Consequence for existing work:** the ingestion described in `docs/CURRENT-STATE.md` — "historical
injury reports 2010–2024 with enforced `as_of_date` (`injuries` table, `src/ingest_reference.py`)" —
rests on a sound foundation. The bottom-up prototype's games-played work is not leaking the future
through this table. That is the answer the thread was most afraid of, and it came back clean.

### 2.5 The problem the thread did not ask about, which is worse

`[VERIFIED]` — `https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html#injury-data`,
verbatim:

> "Our data source died after the 2024 season. **At the moment, there is no 2025 data** and there is
> no ETA yet as to when we will be able to make injury data available again."

Corroborated by `nflverse/nflverse-data` issue **#75** ("[BUG] Injuries not loading", opened
2025-09-06, closed the same day by maintainer `tanho63` pointing at exactly that anchor)
`[VERIFIED]`. Two commenters on that issue describe rolling their own scrapers of team sites and
`nfl.com/injuries`.

An `injuries_2025.csv` nevertheless exists, uploaded 2026-03-18, 695,623 bytes. It is **not** the
same product:

- no `date_modified` → **no `as_of_date` is derivable → 2025 injury rows cannot be used
  point-in-time at all**;
- different schema (`season_type` added);
- **the last rows in the file are week 4** `[VERIFIED]` — the file reproduced ends at
  `2025,REG,REG,LA,4,...`. Whether any week > 4 exists elsewhere in the file is `[GAP]` (a
  small-model read of a 680 KB CSV cannot be trusted for an aggregate), but the file being
  ~695 KB against 2024's ~817 KB is consistent with substantial truncation.

**Can we capture it ourselves going forward? From NFL.com, no.** `[BLOCKED]`

- `https://www.nfl.com/robots.txt` `[VERIFIED]`: `/injuries/` is **not** disallowed.
- `https://www.nfl.com/legal/terms/` `[VERIFIED]`, verbatim: *"Systematic retrieval of data or other
  content from the Services, whether to create or compile, directly or indirectly, a collection,
  compilation, database, or directory, is prohibited absent our express prior written consent."*
  And: *"You may use the Services solely for your own individual non-commercial and informational
  purposes only."*

This is the fetch-vs-redistribute distinction landing on the unhelpful side. robots.txt permits the
crawl; the ToS prohibits the thing we would do with it, which is compile a database. **Recorded as
blocked. Not routed around.** The lawful forward path is Sleeper (§5), whose documentation actively
invites a once-daily pull.

### 2.6 Open checks for `data-ops` — specified, not hand-waved

1. **Close the size-fingerprint caveat with a hash.** Download and `sha256` these two pairs:
   - `https://github.com/nflverse/nflverse-data-archives/releases/download/archive-2023-04-15/injuries_injuries_2022.rds`
     vs `https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2022.rds`
   - `https://github.com/nflverse/nflverse-data-archives/releases/download/archive-2024-06-15/injuries_injuries_2023.rds`
     vs the current `injuries_2023.rds`.
   Then row-diff the two 2022 frames: report **rows added**, **rows removed**, and **cells changed
   with `date_modified` unchanged**. That third number is the only one that would threaten the
   verdict; if it is zero, the verdict hardens from "point-in-time with caveats" to "point-in-time".
   Also confirm 2009–2021 hash-stability on two or three spot seasons.
2. **Confirm the week-1 coverage hole.** Issue **#5** (2022-07-26, `load_injuries` missing week 1
   regular-season data for 2009–2019) was closed as `not_planned` **five minutes** after the
   2022-07-26 asset rebuild `[VERIFIED]` — ambiguous between "fixed by that rebuild" and "declined".
   Run `SELECT season, week, COUNT(*) FROM injuries WHERE week=1 GROUP BY season` against the local
   DB and settle it. If week 1 is genuinely absent for 2009–2019, every "games missed" figure derived
   from those seasons is biased and the ramp curve loses its most important week.
3. **Row granularity.** Confirm `SELECT season, week, gsis_id, COUNT(*) ... HAVING COUNT(*) > 1` is
   empty. The sampled rows are consistent with one row per player-week, but that was not proven.
4. **Enum hardening.** Assert the `practice_status` parser handles `Did Not Participation In
   Practice` (real, in 2022) without dropping the row.

---

## 3. Games played, snap share, route participation, return-from-injury

### 3.1 Snap counts

`[VERIFIED]` — release tag `snap_counts`, `.parquet` assets:

| Fact | Value |
|---|---|
| Seasons present | 2012–2024. **No 2025 file in the returned listing.** |
| Effective span | **2013–2024.** `snap_counts_2012.parquet` is **4,561 bytes** against ~210 KB for every later season — 2012 is effectively empty. |
| Last written | **All thirteen files: 2025-10-06.** |
| Source | Pro Football Reference `[VERIFIED]` from `nflreadr` function title and schedule doc |
| Documented cadence | "every day at 0, 6, 12, 18 UTC during the season", availability "dependent on Pro Football Reference's publishing schedule" `[VERIFIED]` |
| Point-in-time? | **No — wholesale retroactive regeneration.** Every historical season was rewritten on one day. |

The absence of a 2025 file is `[SNIPPET]`-grade rather than `[VERIFIED]` — a listing returned by a
summarising fetch could truncate. It matters enough to re-check directly.

**Is the retroactive regeneration a leakage problem?** Much less than for injuries, and the
distinction is worth stating rather than treating all revision as equal. Snap counts are *box-score
facts about a completed game*. A revised snap count changes a historical measurement; it does not
inject knowledge of the future into a pre-draft feature, because CLAUDE.md §6.1 already permits full
use of season N−1 completed data. What is lost is the ability to reconstruct "what the snap count
*said* in week 5" — which no design in Addendum 2 requires. **Second-order. Note it, don't block on
it.**

### 3.2 Participation — and routes

`[VERIFIED]` — release tag `pbp_participation`, `.parquet` assets:

| Season | Size | Last written |
|---|---|---|
| 2016–2022 | ~2.85–3.08 MB each | 2023-12-19 (frozen since) |
| 2023–2024 | ~4.64–4.70 MB | 2025-09-04 |
| 2025 | 4.74 MB | 2026-02-10 |

**Source discontinuity, and it is not cosmetic** `[VERIFIED]` from the schedule doc: pre-2023
participation came from **NFL Next Gen Stats**, "before that source ended mid-season"; 2023 onward
comes from **FTN**. The file sizes jump ~55% at the boundary, consistent with a different schema.
Treating 2016–2022 and 2023–2025 as one homogeneous series is a modelling error waiting to happen.
Whether the FTN-era files retain the NGS-era field names is `[GAP]` — not verified.

Also `[VERIFIED]`: participation "publishes only after post-season completion, without updates during
regular play". Useless in-season, fine for backtesting.

**Routes run does not exist as a field.** Participation gives on-field player lists per play. A
"routes run" figure derived from it counts blocking backs and in-line tight ends as route-runners.
Per CLAUDE.md §5 this must be labelled a **proxy**, explicitly, wherever it surfaces. `[VERIFIED]`
by the absence of any routes field from the nflreadr function inventory and injuries/participation
dictionaries.

### 3.3 Games active/inactive

`[VERIFIED]` — release tag `weekly_rosters`, assets `roster_weekly_{YYYY}.csv`, 7.9–16.6 MB each.
Earliest **2002**. The listing I received was truncated at 2018; the true upper bound is `[GAP]`
(nflreadr documents 2002-onward). Historical files written 2023-09-06 and 2023-09-13.

The `status` field is documented as "Roster status: describes things like Active, Inactive, Injured
Reserve, Practice Squad etc", with a companion `status_description_abbr` = "A code corresponding to a
particular NFL status" `[VERIFIED]` from the nflreadr rosters dictionary. **Note:** that dictionary
covers `load_rosters` (seasonal); the weekly-rosters dictionary was not fetched, so field-for-field
equivalence is `[GAP]`.

### 3.4 Return-from-injury case count — `[GAP]`, and deliberately left as one

The thread asks how many usable pre/post-injury cases exist. **I cannot compute this without database
access, and I am not going to produce a plausible number.**

What I *can* establish is the hard bound the spans impose `[VERIFIED]`:

| Requirement | Constraint | Usable seasons |
|---|---|---|
| Injury status with a real `as_of_date` | 2010–2024 (2009 undated at source; 2025 has no `date_modified`) | 15 |
| ∩ snap share | snap counts effectively 2013–2024 | **12** |
| ∩ route participation proxy | participation 2016–2025, with an NGS/FTN break at 2023 | **9**, in two incompatible halves (2016–2022, 2023–2024) |

Exact query for `data-ops`, and **report all three numbers, not just the first**:

```sql
-- a case = a player who has >=2 consecutive weeks with report_status='Out'
--          followed by >=1 week active with snaps > 0, and >=4 pre-injury weeks with snaps > 0
SELECT COUNT(*)                    AS cases,
       COUNT(DISTINCT gsis_id)     AS distinct_players,
       COUNT(DISTINCT report_primary_injury || '|' || position) AS type_position_cells
FROM  <derived return_events view>
WHERE season BETWEEN 2013 AND 2024;
```

**Why the third number is the one that decides the design.** A count of cases overstates independence
badly here: the same players recur (a fragile RB contributes four "cases"), and the same injury type
recurs. `type_position_cells` is the real n for a **by-injury-type** ramp curve. My prior, stated as a
prior and not a finding, is that a by-type-by-position curve will be underpowered and the honest
output will be a single aggregate ramp with per-position intercepts. But that is a hypothesis for
`data-ops` to kill or confirm with the query above, not something to assume — and it is exactly the
kind of "fifteen leagues, three decision units" situation where the case count flatters the sample.

---

## 4. Suspensions — no free structured source. Hand-maintained.

Every candidate, and what happened:

| Candidate | Result |
|---|---|
| nflverse | **No suspension dataset.** All 23 `load_*` functions enumerated from the nflreadr reference index `[VERIFIED]`; nothing covers suspensions. `load_contracts` (OverTheCap) is the nearest and does not. |
| ProSportsTransactions.com | `https://www.prosportstransactions.com/robots.txt` → **HTTP 403**. Cannot even establish the crawl policy. `[BLOCKED]` — recorded, stopped. |
| Spotrac (has a fines-and-suspensions page) | `https://www.spotrac.com/robots.txt` → **HTTP 403**. `[BLOCKED]` — recorded, stopped. |
| NFL.com | ToS prohibits systematic retrieval into a database (§2.5, verbatim). `[BLOCKED]` |
| Wikipedia | No dedicated structured NFL suspension list surfaced. Per-season articles carry prose mentions. `[GAP]` / not usable as structured input. |
| Paid (SportsDataIO et al.) | Exists, out of scope — no subscription decision has been made. `[SNIPPET]` |

**Plainly, as the thread asked: the suspension table must be hand-maintained.** There is no
automated path that this session could reach lawfully.

There is one possible partial reprieve worth a cheap check rather than a research session: weekly
rosters carry `status` / `status_description_abbr`, and the documented description ends in "etc"
(§3.3). If the NFL status codes include a suspended designation, **historical** suspensions become
derivable for backtesting — though never *forward-looking* ones, since a suspension announced in July
does not appear on a roster until the season starts. Whether those codes include suspension is
`[GAP]`. Check: `SELECT DISTINCT status, status_description_abbr FROM <weekly rosters>` — one query.

### Proposed schema — smallest thing that is correct

```
suspensions
  suspension_id             INTEGER PK
  user_id, league_id                        -- multi-user shape per CLAUDE.md §4
  gsis_id                   TEXT NULL       -- NULL for undrafted/pre-debut; name is then the key
  player_name_raw           TEXT NOT NULL
  season                    INTEGER NOT NULL
  games_suspended_announced INTEGER NOT NULL
  games_suspended_current   INTEGER NOT NULL   -- after appeal; equals _announced until resolved
  appeal_status             TEXT NOT NULL      -- announced | pending_appeal | upheld | reduced
                                               -- | overturned | served
  effective_week_start      INTEGER NULL
  effective_week_end        INTEGER NULL
  counts_preseason_games    BOOLEAN NOT NULL   -- preseason games often do not count toward the term
  announced_date            DATE NOT NULL
  appeal_resolved_date      DATE NULL
  source_url                TEXT NOT NULL      -- mandatory, not optional
  entered_by                TEXT NOT NULL
  current_as_of             DATE NOT NULL      -- the field the thread specifically asked for
```

**Rules that make this safe rather than dangerous:**

1. **The deduction must read `games_suspended_current`, never `games_suspended_announced`.** The
   thread's warning is the right one: offseason announcements are frequently reduced on appeal, and a
   table capturing only the announcement systematically overstates the deduction. Keeping both columns
   and never collapsing them is what makes the overstatement visible instead of silent.
2. **A blocking test on staleness, not a note.** Fail the build if
   `MIN(current_as_of) < date('now', '-7 days')` while any board export is regenerated inside the
   draft window. The thread is right that a four-week-old table is worse than no table.
3. **Surface the date in the UI, not in a footnote.** "Suspensions as of 2026-08-14" on the board
   itself. Same reasoning as D-003's structural treatment of unproven ordering.
4. **A row with `appeal_status='announced'` and `announced_date` more than 30 days old is a test
   failure**, not a warning — it means nobody checked whether the appeal resolved.

Backtesting note, so nobody is surprised later: **validating the suspension deduction historically
also requires a hand-entered historical table.** There is no free structured history either. This is
acceptable precisely because the claim here is a *correctness guarantee*, not a statistical edge —
a handful of hand-entered historical cases is enough to test that the arithmetic is right, and no
amount of data would make it an "edge" anyway. Do not let this quietly turn into a modelling project;
`docs/ideas-inbox.md` already records that suspension *probability* modelling was DECLINED for lack
of positive cases, and that decision should stand.

---

## 5. News and transactions

| Source | Structured | Span / history | Latency (documented) | Point-in-time | Licence / access |
|---|---|---|---|---|---|
| **Sleeper `/v1/players/nfl`** `[VERIFIED]` | JSON, ~5 MB | **Current state only — no history** | Docs: "use this call sparingly, intended only to be used once per day at most" | Only if *we* snapshot it daily. Then genuinely PIT. | Free, no auth. Docs explicitly say "save this information on your own servers". Redistribution terms `[GAP]`. |
| **nflverse depth charts** `[VERIFIED]` | parquet/csv | year-round | "every day at 7AM UTC throughout the year" | **Post-2024 rows carry ISO8601 timestamps instead of week buckets — genuinely PIT from 2025.** Pre-2025 week-bucketed. | CC-BY (nflverse) |
| **nflverse rosters** `[VERIFIED]` | parquet/csv | 2002+ | "every day at 7AM UTC" | Snapshot-overwritten; weekly rosters retain week granularity | CC-BY |
| **nflverse schedules/games** `[VERIFIED]` | parquet/csv | 1999+ | "every 5 minutes during the season" | n/a | CC-BY |
| **nflverse snap counts** `[VERIFIED]` | parquet | 2013–2024 | 4×/day in season, gated by PFR | No (§3.1) | PFR-derived; PFR terms `[GAP]` |
| **RotoWire RSS** | already known to the project | — | **`[GAP]` — not measured this session** | — | `[GAP]` |
| **NFL.com** | — | — | — | — | **`[BLOCKED]` — ToS, §2.5** |
| **ProSportsTransactions / Spotrac** | — | — | — | — | **`[BLOCKED]` — 403 on robots.txt** |

Two things worth pulling out of that table:

- **Sleeper is the replacement for the dead injury feed**, not a nice-to-have. It carries
  `injury_status`, `injury_start_date`, `practice_participation`, `depth_chart_position`,
  `depth_chart_order` — all `[VERIFIED]` from `docs.sleeper.com` — for free, without auth, from a
  source whose own documentation invites a daily pull. It has **zero history**, so its value is
  entirely a function of when snapshotting starts. Same argument as ADP in §1, same urgency, same
  job.
- **Depth charts became point-in-time in 2025.** `docs/CURRENT-STATE.md` lists `RB_HANDCUFF` as
  blocked because "depth charts end 2024". Given the schedule doc explicitly describes a post-2024
  change to ISO8601-timestamped rows, that line may be stale — worth one check by whoever owns it.
  I did not fetch the `depth_charts` release to confirm the latest season present: `[GAP]`.

**Latency was not measured empirically for any source.** Every figure above is the *documented*
cadence, which is an upper bound on freshness, not an observation. Measuring real RotoWire and
Sleeper lag against a known event is a half-hour job for `data-ops` and would be worth doing before
anyone designs around it.

---

## 6. Recommendation — which Addendum 2 directions are supported

**First, a documentation problem that has to be said out loud.**
`docs/fable-mandate-2026-07-27.md` **contains no section called "Addendum 2."** Its Priority 2 has
sub-sections 2A–2D, and they are about table stakes, consensus anchoring, the ~2029 claim, and
overfitting — not injuries, suspensions, ADP drift, or ramps. Four documents cite "Addendum 2" as if
it were readable: this thread (twice, including a specific "§ 2C correction"),
`docs/handoffs/058-draft-board-design-gap.md` line 127, `docs/handoffs/059-on-deck-recommendations.md`
line 142, and `docs/ideas-inbox.md` line 41. **It is not in the named file.** `[GAP]` — either it
lives somewhere unnamed or it was never committed. Someone should resolve that; four downstream
threads are hanging off a citation that does not resolve.

I therefore evaluated against the four directions those four citations *describe*, reconstructed from
`docs/ideas-inbox.md` lines 40–44, `docs/founder-requests.md` lines 297–300, and
`docs/adr-drafts/ADR-E-bottom-up-projection-framework.md` §A1.1. If Addendum 2 turns out to say
something else, this section needs redoing.

| # | Direction | Verdict |
|---|---|---|
| **D4** | **Week-indexed projection vector** — `points = games played × points per game × usage ramp`, with the ramp defaulting to 1 | **SUPPORTED. Build it first.** It needs only games played and weekly stats, both fully available across the whole span, and it is the primitive the other three hang off. Nothing in this audit constrains it. |
| **D2** | **Suspensions as a deterministic games-played deduction** | **SUPPORTED — but the data is hand-maintained, and that is a permanent condition, not a temporary one.** The arithmetic is trivial and the correctness guarantee is real. Ship it *with* the `current_as_of` staleness test in §4, or do not ship it: a stale table is worse than an absent one, and this is the one place in the audit where absence genuinely beats staleness. |
| **D3** | **ADP drift / news-hype toward draft date** | **SUPPORTED GOING FORWARD ONLY, and only if snapshotting starts today.** Nothing historical is in hand (the historical question belongs to 055). Every day of delay is a day of series permanently missing. Lowest intellectual interest, highest urgency in this thread. |
| **D1** | **Injury duration and recovery usage ramp** | **RE-SCOPE, and drop the interesting version.** See below. |

### D1, in full, because it is the one that changes

The thread expected the injury data to fail on look-ahead bias. **It didn't.** It failed on something
more mundane and more fatal: **the feed stops at 2024.**

- Fitting a ramp curve on 2013–2024 is fine — the data is point-in-time and the guardrails hold.
- **Applying it to the 2026 season is not**, because to apply a return-from-injury ramp you must know
  who is returning from what, and nflverse cannot tell you that for 2025 or 2026. The 2025 file has
  no `date_modified`, a changed schema, and appears to stop around week 4.
- Snap counts, the other required input, show no 2025 file in the release listing.
- And the by-injury-type version is underpowered before it starts (§3.4).

So the honest scope is: **an aggregate post-return usage ramp, per position, fitted on 2013–2024,
applied only when a return date arrives from a live source we can lawfully obtain — which means
Sleeper's daily `injury_status` snapshots, not nflverse.** That makes D1 *depend on* D3's snapshotting
discipline rather than on nflverse at all. If the daily Sleeper snapshot job does not exist, D1 has no
input and should not be specced.

**Drop:** the by-injury-type ramp, and any design that assumes nflverse will supply current-season
injury status.

### The single sentence to carry out of this audit

The injury data passed the leakage test and failed the availability test — and since every plan in
this backlog was worrying about the first, the second is the one that will actually bite.

---

## Appendix — sources fetched

All fetched 2026-07-27.

| URL | Result |
|---|---|
| `api.github.com/repos/nflverse/nflverse-data/releases/tags/injuries` | 200 — asset census |
| `api.github.com/repos/nflverse/nflverse-data/releases/tags/snap_counts` | 200 |
| `api.github.com/repos/nflverse/nflverse-data/releases/tags/pbp_participation` | 200 |
| `api.github.com/repos/nflverse/nflverse-data/releases/tags/weekly_rosters` | 200 (listing truncated) |
| `api.github.com/repos/nflverse/nflverse-data-archives/tags?per_page=100` | 200 — 97 archive tags |
| `.../nflverse-data-archives/releases/tags/archive-2023-04-15` | 200 |
| `.../nflverse-data-archives/releases/tags/archive-2024-06-15` | 200 |
| `.../nflverse-data-archives/releases/tags/archive-2025-06-15`, `-2025-12-25`, `-2026-07-15` | 200, no injuries assets returned — possible response truncation, not treated as evidence |
| `github.com/.../releases/download/injuries/injuries_2015.csv` | 200 via redirect — rows read |
| `github.com/.../releases/download/injuries/injuries_2022.csv` | 200 via redirect — rows read |
| `github.com/.../releases/download/injuries/injuries_2025.csv` | 200 via redirect — header + rows read |
| `nflreadr.nflverse.com/articles/dictionary_injuries.html` | 200 |
| `nflreadr.nflverse.com/articles/nflverse_data_schedule.html` | 200 |
| `nflreadr.nflverse.com/reference/index.html` | 200 |
| `nflreadr.nflverse.com/reference/load_injuries.html` | 200 |
| `raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_rosters.csv` | 200 |
| `api.github.com/repos/nflverse/nflverse-data/issues/5`, `/33/comments`, `/75`, `/75/comments` | 200 |
| `raw.githubusercontent.com/nflverse/nflverse-data/master/.github/workflows/run_archive.yaml` | 200 |
| `raw.githubusercontent.com/nflverse/nflverse-data/master/R/archive.R` | 200 — archive is `.rds` only |
| `raw.githubusercontent.com/nflverse/nflverse-data/master/dev/reupload_assets.R` | 200 — `pbp`-only reformat, does not regenerate data |
| `raw.githubusercontent.com/nflverse/nflverse-data/master/NEWS.md`, `README.md` | 200 — **no revision policy stated** |
| `nflreadr.nflverse.com/news/index.html` | 200 — **no revision policy stated** |
| `api.github.com/repos/nflverse/nflverse-rosters/contents/{,R,exec,.github/workflows}` | 200 — located the builder |
| `raw.githubusercontent.com/nflverse/nflverse-rosters/master/exec/update-injuries.R` | 200 — **the decisive source** |
| `raw.githubusercontent.com/nflverse/nflverse-rosters/master/.github/workflows/update_injuries.yaml` | 200 — cron disabled |
| `web.archive.org/cdx/...` (archived copy of `injuries_2022.csv`) | **Not fetchable by this tool** — avenue ruled out, not skipped |
| `docs.sleeper.com` | 200 |
| `fantasyfootballcalculator.com/robots.txt` | 200 |
| `www.nfl.com/robots.txt` | 200 |
| `www.nfl.com/legal/terms/` | 200 |
| `www.prosportstransactions.com/robots.txt` | **403 — BLOCKED, stopped** |
| `www.spotrac.com/robots.txt` | **403 — BLOCKED, stopped** |

**Attribution:** nflverse data is CC-BY; the FTN charting subset (which now underlies participation
from 2023) is CC-BY-SA and requires share-alike treatment of derivatives. Per CLAUDE.md §5.
