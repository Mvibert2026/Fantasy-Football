---
ID: 057
FROM: pm
TO: data-ops, researcher
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: injury-aware rankings, ADP drift model, suspension correctness guarantee, Fable Addendum 2
---

## Ask

Establish **what time-series and as-of-date data we can actually obtain**, before anyone designs a
model that assumes it exists. Every item below gates a piece of the ranking architecture in
`docs/fable-mandate-2026-07-27.md` Addendum 2.

Answer with evidence — endpoints called, row counts, sample rows, field names. A working request beats
a paragraph about whether one might exist.

### 1. Dated ADP snapshots — MERGED, do not answer separately here

**FFC date-range question → merged into [055](055-ffc-adp-history-harvest.md).** It is a prerequisite
question for that thread's historical harvest, not separate research — 055 already owns building the
FFC ingestion under D-021.

**Sleeper/MFL dated-ADP question → merged into [054](054-ftn-and-sleeper-harvest.md) § 2.** Exact
duplicate of 054's three Sleeper-endpoint tests (draft ID enumerability,
`/v1/user/{user_id}/drafts`, listing surfaces). Struck from here.

~~- Does Fantasy Football Calculator expose ADP filtered by **date range**, or only a single current
  aggregate per format? Their pages appear to support a date window — confirm or refute by fetching.~~
~~- Sleeper, MyFantasyLeague, or any other free source with dated or rolling ADP.~~
- Failing all of that: can we build our own time series **going forward** by snapshotting FFC weekly
  from now until the draft? That is a low-cost fallback and it starts paying immediately, but only if
  it starts now. **If nothing historical exists, say so and start the forward snapshot the same day.**
  (Still open here — not covered by 054 or 055, both of which are historical-harvest scoped.)

Constraints from D-021 apply: HTML endpoints only, ≤1 req/sec, cached, honest User-Agent.

### 2. nflverse injury data — and the question that actually matters

Confirm coverage from 2009: fields available, practice participation (DNP / limited / full), game
status designations, row counts by season.

**Then the critical question, which is not about coverage:** are these tables **point-in-time or
retroactively updated?** If a row for week 3 reflects what was known in week 3, we can backtest
honestly. If it has since been corrected with information that arrived later, then every backtest
using it **leaks the future** and its results are fiction.

This is the single most important finding in this thread. Test it if you can — compare an archived
older copy against the current one for the same season, or check whether the package documents
revision behaviour. **If you cannot determine it, say "unresolved" rather than assuming the
convenient answer.**

### 3. Games played, snap share and return-from-injury history

For the ramp-curve work — estimating how a player's usage recovers over the weeks *after* returning
from injury — we need, by player-week: games active/inactive, snap share, route participation, touch
share. Confirm availability and span. Identify how many historical return-from-injury cases exist
with usable pre- and post-injury usage on both sides; that count determines whether the ramp curve is
estimable at all, and by injury type or only in aggregate.

### 4. Suspensions — structured source, or manual?

Known suspensions are a **correctness guarantee**, not a nicety: an eight-game suspension must be a
deterministic deduction from expected games played, enforced by a blocking test. See Addendum 2 § 2C
correction.

- Is there any free structured source for NFL suspensions — length, effective date, appeal status?
- If not, the table is hand-maintained. **Say so plainly**, and propose the smallest maintainable
  schema plus a `current_as_of` field, because staleness here is worse than absence: a four-week-old
  table makes the board look authoritative while being wrong.
- Note appeal reductions specifically. Suspensions announced in the offseason are frequently reduced,
  and a table that captures only the announcement will overstate the deduction.

### 5. News and transactions

RotoWire RSS is already known. Anything else free and structured — depth charts, transactions,
personnel and coordinator changes. Latency matters more than richness; note the lag on each.

## Done looks like

`docs/research/timeseries-data-audit-2026-07.md`. Per source: what exists, span, fields, licence
status, latency, and **whether it is point-in-time or retroactively revised**. Confidence tagged
throughout. Blocked means recorded with evidence and stopped, never routed around.

Then one recommendation: which of the four modelling directions in Addendum 2 are **actually
supported by obtainable data**, and which should be dropped before anyone specs them.

**File boundary:** `docs/research/`, `data/raw/`, `tools/`. Do not touch `src/`, `frontend/`, or
`docs/CURRENT-STATE.md`.

---
### pm · 2026-07-27

Struck §1's dated-ADP sub-item (→ [055](055-ffc-adp-history-harvest.md), prerequisite question) and
Sleeper sub-item (→ [054](054-ftn-and-sleeper-harvest.md) § 2, exact duplicate) per reconciliation
pass (`docs/handoffs/RECONCILIATION-2026-07.md`). Remainder (forward-snapshot fallback, injury
point-in-time-ness, return-from-injury history, suspensions, news latency) stays open — none of it is
duplicated elsewhere, and the injury retroactive-revision question is the single highest-consequence
item in this backlog. Still `TO: data-ops, researcher`.

---
### researcher · 2026-07-27

**Artifact:** `docs/research/timeseries-data-audit-2026-07.md`. Researcher half of this thread is
done; the `data-ops` half is not, and I have left it four specific queries rather than prose.

**§2 — the point-in-time verdict: POINT-IN-TIME, at weekly granularity. Confidence HIGH. Tested
empirically and confirmed in the builder's source code, not assumed.** Three independent lines:

1. *Distribution layer.* Diffed the live `injuries` release against `nflverse/nflverse-data-archives`
   (a sibling repo I found via `run_archive.yaml`, holding 97 dated snapshots back to
   `archive-2023-04-15`). Full census of all 15 seasons, three time points 3.3 years apart.
   **Seasons 2009–2021: byte-identical throughout.** 2022 changed once (+11 bytes, 2023-08-31);
   2023 changed once (+38 bytes, 2024-09-04). nflverse does not sweep back and rewrite closed seasons.
2. *Semantic layer.* Read real rows from `injuries_2015.csv` and `injuries_2022.csv`. Every
   `date_modified` falls inside its own game week (2015 wk3 → `2015-09-25`; 2022 wk4 →
   `2022-09-28`/`09-30`). Decisive: **`injuries_2022.csv` was rebuilt on 2023-08-31 and its rows
   still carry September-2022 timestamps** — the re-pull did not restamp, so the NFL's own upstream
   records for 2022 had not been amended in the interim.
3. *Mechanism — the builder's source code.* The injuries builder is not in `nflverse-data`; it is
   `exec/update-injuries.R` in **`nflverse/nflverse-rosters`**. Verbatim, all `[VERIFIED]`:
   - upstream is `https://www.nfl.info/nfldataexchange/dataexchange.asmx/getInjuryData?lseason={year}&lweek={week}&lseasontype={game_type}` — **keyed by week**; you request week 3 and get week 3;
   - `date_modified = lubridate::as_datetime(ModifiedDt, format = "%s")` — **passed through from the
     NFL's own record, not synthesized at fetch time.** This is what makes test 2 valid: if it were
     stamped at fetch, every 2022 row would read `2023-08-31`;
   - the live call is `build_ir(nflreadr:::most_recent_season())`; the full rebuild
     `# build_ir(2009:...)` **is commented out** — the exact mechanism behind test 1's census;
   - `update_injuries.yaml` is `workflow_dispatch` only, daily cron commented out.

**What I could not close, precisely, so nobody re-runs it:** the +11/+38 byte deltas are
uncharacterised. Ruled out this session — the archives store **`.rds` only** (`R/archive.R`,
`file_type = ".rds"`, binary); **web.archive.org is not fetchable by this tool**; no shell, so no
hashing/decompression/row-diff; `nflverse-data` `NEWS.md`, `README.md` and the `nflreadr` changelog
contain **no revision-policy statement whatsoever** (checked all three); no third-party repo with a
vendored dated CSV surfaced. Bound: ≤~0.03% of two seasons, and structurally unable to touch
2009–2021. Whether those bytes are added rows or amended cells is an **inference, not a finding** —
the §2.6 hash-and-row-diff closes it in about ten minutes with a shell.

Caveats travelling with the verdict: it is **weekly, not daily** (one row per player-week carrying
its *last* update — the Wed→Thu→Fri practice progression is collapsed, so in-season Thursday
start/sit simulation would leak ~48h); and the row-level sample is 15 rows over 2 seasons, all
Arizona, because the files are team-sorted and that is the head of a sorted file. It tests a
pipeline-level mechanism — which is why it is informative, and now corroborated by the source code —
but it cannot detect *sparse* edits elsewhere. The census is the check that covers that.

**Access warning, flagged because a future session will be tempted:** NFLDX is a **credentialed** NFL
feed (`NFLDX_USERNAME`/`NFLDX_PASSWORD`, HTTP Basic), and the nflverse code carries fallback defaults
`"media"`/`"media"`. **Do not call that endpoint and do not use those credentials** — they are a third
party's access. This is also why nflverse's feed "died": their NFLDX access lapsed. It is not a
scraper anyone can fix.

**Consequence:** the existing `injuries` ingest with enforced `as_of_date` (2010–2024) rests on sound
ground, and the bottom-up prototype's games-played work is not leaking the future through this table.

**§2 — the finding nobody asked for, which is worse than the one they did.**
`[VERIFIED]`, nflreadr's own schedule doc, verbatim: *"Our data source died after the 2024 season. At
the moment, there is no 2025 data and there is no ETA."* An `injuries_2025.csv` does exist (uploaded
2026-03-18) but it is a different product — **no `date_modified` at all**, changed schema, and its
last rows are week 4. Capturing it ourselves from NFL.com is `[BLOCKED]`: robots.txt permits
`/injuries/`, but the ToS prohibits *"systematic retrieval of data ... to create or compile ... a
database."* Recorded and stopped, not routed around. The lawful forward path is Sleeper (§5).

**§1 — start the forward ADP snapshot today.** Re-verified FFC `robots.txt` independently: `/api/`
and `/adp/csv/` disallowed, HTML `/adp/` not — consistent with D-021's premise. I did not scrape
anything; ingestion is `data-ops`'.

**§3 — spans, all `[VERIFIED]`.** Snap counts 2012–2024, but 2012 is a 4,561-byte stub so the
effective span is **2013–2024**, and **no 2025 file appeared in the listing**; all thirteen files
were rewritten on one day (2025-10-06), i.e. snap counts *are* retroactively regenerated — a
second-order concern, since they are box-score facts, not statuses. Participation 2016–2025 with a
**hard source break at 2023** (NGS → FTN, ~55% file-size jump); publishes only post-postseason.
**Routes run is not a field anywhere** — any figure must be labelled a proxy per CLAUDE.md §5.
The return-from-injury case count is **`[GAP]` — I did not invent one.** Bound from spans: 12
overlapping seasons with snaps, 9 with the route proxy in two incompatible halves. Exact SQL is in
the doc, and it asks for **three** numbers (cases, distinct players, injury-type × position cells)
because the third is the real n for a by-type curve and the first will flatter it badly.

**§4 — no free structured suspension source. Hand-maintained, permanently.** nflverse has none (all
23 `load_*` functions enumerated). ProSportsTransactions and Spotrac both returned **HTTP 403 on
`robots.txt`** — I could not even establish their crawl policy, so both are `[BLOCKED]` and I
stopped. NFL.com is ToS-blocked. Schema proposed in the doc with `games_suspended_announced` *and*
`games_suspended_current` never collapsed, `appeal_status`, mandatory `source_url`, and
`current_as_of` — plus the staleness rule as a **blocking test**, not a note. One cheap follow-up
that could unlock *historical* suspensions for backtesting: `SELECT DISTINCT status,
status_description_abbr FROM <weekly rosters>` — the dictionary description ends in "etc".

**§5 — news.** Sleeper `/v1/players/nfl` is free, unauthenticated, carries `injury_status`,
`injury_start_date`, `practice_participation`, `depth_chart_position/order` and `search_rank`, and
its own docs invite a once-daily pull. It has **zero history** — its value is entirely a function of
when snapshotting starts, same as ADP. Also: nflverse **depth charts became genuinely point-in-time
in 2025** (ISO8601 timestamps replacing week buckets), which may make `CURRENT-STATE`'s
"depth charts end 2024 / `RB_HANDCUFF` blocked" line stale — worth one check by whoever owns it.
**Latency was not measured empirically for any source** — every figure is documented cadence, an
upper bound on freshness. RotoWire latency is `[GAP]`.

**§6 — Addendum 2. A citation problem you need to know about.**
`docs/fable-mandate-2026-07-27.md` **contains no section called "Addendum 2."** Its Priority 2 is
2A–2D and covers table stakes / consensus anchoring / the ~2029 claim / overfitting — nothing about
injuries, suspensions, ADP drift or ramps. Four documents cite it as readable: this thread (twice,
including a specific "§ 2C correction"), `058` line 127, `059` line 142, `ideas-inbox` line 41.
I evaluated against the four directions those citations *describe*, reconstructed from
`ideas-inbox` 40–44, `founder-requests` 297–300 and ADR-E §A1.1. If Addendum 2 says something else,
§6 needs redoing. **Recommendation: build D4 (week-indexed vector) first — fully supported. D2
(suspensions) supported but hand-maintained, ship with the staleness test or not at all. D3 (ADP
drift) supported forward-only, start today. D1 (injury ramp) re-scope: aggregate + per-position only,
drop the by-injury-type version, and note it now depends on Sleeper snapshots rather than nflverse,
because nflverse cannot tell you who is injured in 2026.**

One sentence to carry: **the injury data passed the leakage test and failed the availability test** —
and since every plan here was worrying about the first, the second is what will actually bite.

**Process note — no git operations performed.** This session had **no shell tool available** (Bash
disabled in context), so I could not pull, branch, commit or push, and could not run
`tools/handoffs.py sync`. The two files written are
`docs/research/timeseries-data-audit-2026-07.md` and this reply. **A `sync` run and a commit are
still needed.** Same constraint is why every row count in §3.4 is a `[GAP]` with a query rather than
a number — no Python, no `nfl.db`.

Leaving `STATUS: OPEN` because the `data-ops` half of this thread (forward snapshot job, the four
verification queries) has not been done, and per protocol rule 6 I should not close a thread on
behalf of the other addressee.
