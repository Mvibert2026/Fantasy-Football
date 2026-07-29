# Historical preseason market ADP — what is obtainable, how far back, in what formats

**Researcher, 2026-07-29.** All FFC figures below were read from the source's own rendered pages
today. Every claim carries a confidence tag. Where a number could not be established it is left as
`[GAP]` and the probe that would close it is named.

---

## 1. Conclusion first

**Yes. A source exists that lifts the market-baseline comparison out of the n=4 trap, and it is
obtainable within the rules — but not back to 2009, and not in the primary league's exact format.**

| | Seasons with a genuine, date-bounded preseason sample | Usable after removing the sealed 2025 holdout |
|---|---|---|
| **FFC non-PPR, 12-team** | 2010, 2013–2024 (**13**) | **13** (FFC has no 2025 archive at all) |
| **FFC half-PPR, 12-team** | 2018–2024 (**7**) | **7** |
| **FFC PPR, 12-team** | 2010 verified; 2011–2024 not probed | `[GAP]` |
| Expert-consensus ECR (current in-repo) | 2021–2024 (**4**) | 4 |

**The decisive fact:** for every archived season that carries data, FFC's ADP page states its own
sample window verbatim — *"Data from 1535 fantasy football mock drafts between September 6, 2010 and
September 8, 2010."* `[VERIFIED]` That is a **bounded draft-date range**, not a stamp of today's
date, and in 13 of 18 archived non-PPR seasons the range **ends before that season's Week 1**. FFC is
therefore structurally unlike MyFantasyLeague, whose response is an accumulated aggregate stamped
with today and cannot be bounded at all.

**Three things this does not do, stated up front:**

1. **It does not rescue PR-004.** See §7. PR-004 is registered and frozen; adding a market-ADP
   confirmatory arm is a different test requiring a new registration id, per PR-004 §4 exit 3.
2. **It does not give the primary league's format.** FFC's *archive* is **12-team only** — 10-team
   and 14-team URLs silently serve the 12-team page (§4). Westwood is half-PPR **10-team**. The
   closest archived proxy is half-PPR 12-team, n=7.
3. **It is n=13 by season and n=1 by market.** Thirteen draws from one site's mock-draft pool are
   not thirteen independent markets (§6).

---

## 2. The central question: preseason snapshot or retrospective aggregate?

**Answer: a genuine, date-bounded preseason sample for most years — verifiable per year, and it
fails the check for a minority of years.** `[VERIFIED]`

Mechanism, as far as it can be established from the outside: FFC's ADP page always displays a
**rolling recent window** of drafts, not the whole period. Today's live 2026 page reads *"Data from
1187 fantasy football mock drafts between July 24, 2026 and July 29, 2026"* `[VERIFIED]` — a ~5-day
window, and that exact string is what `data/adp-snapshots-ffc/2026-07-29_half_ppr.csv` already
carries in its `sample_window` / `total_drafts_in_sample` columns `[VERIFIED, local]`. For a past
season the "most recent" drafts are frozen at whenever drafting activity for that period stopped —
which, for redraft leagues, is the day before kickoff.

That is a mechanism, not a guarantee, so **it must be checked per season rather than assumed.** The
check is one comparison: `window_end < Week 1 kickoff of that season`. Applied below, it rejects
2007, 2008, 2009 and 2011 outright and flags 2012 as marginal.

**Residual uncertainty, named rather than papered over.** The sentence is FFC's own description of
its sample; we cannot read their server code to confirm the displayed window is exactly the sample
bound rather than the min/max of a wider set. `[GAP]` **The probe that would settle it costs
nothing and needs no new fetching:** the repo now captures FFC daily. If `total_drafts_in_sample`
and `sample_window` roll forward together day over day in `data/adp-snapshots-ffc/`, the sentence
describes the sample. Two weeks of existing capture answers it.

**Compare to the known-bad case.** MFL serves historical periods but stamps every response with
today's date and returns the accumulated aggregate (2021 → 2,322 drafts), so a past-season pull
includes drafts run after any realistic draft date — recorded in `CURRENT-STATE.md` open item 2 and
`docs/pm/MEMORY.md` §4. FFC does not have this failure mode **for years that pass the window
check**, and has exactly this failure mode for 2007–2009, where the window runs to June 2010.

---

## 3. The year grid — non-PPR, 12-team

All rows `[VERIFIED]` (page heading and "Data from" sentence read from
`https://fantasyfootballcalculator.com/adp/standard/12-team/all/<year>` on 2026-07-29). Kickoff
dates `[SECONDARY]` — from search results, **not** from a primary schedule source; see the note
below the table.

| Season | Drafts in sample | Stated draft-date window | Week 1 kickoff | Look-ahead gate |
|---|---|---|---|---|
| 2007 | 998 | Aug 29 2007 → **Jun 20 2010** | Sep 6 2007 | **FAIL** |
| 2008 | 2612 | Aug 30 2008 → **Jun 20 2010** | Sep 4 2008 | **FAIL** |
| 2009 | 1325 | Sep 7 2009 → **Jun 20 2010** | Sep 10 2009 | **FAIL** |
| 2010 | 1535 | Sep 6 → Sep 8 2010 | Sep 9 2010 | PASS |
| 2011 | 1144 | Sep 7 → **Sep 9** 2011 | **Sep 8** 2011 | **FAIL** |
| 2012 | 507 | Sep 4 → **Sep 5** 2012 | **Sep 5** 2012 | **MARGINAL — same day** |
| 2013 | 992 | Sep 2 → Sep 4 2013 | Sep 5 2013 | PASS |
| 2014 | 752 | Aug 31 → Sep 1 2014 | Sep 4 2014 | PASS |
| 2015 | 822 | Sep 6 → Sep 9 2015 | Sep 10 2015 | PASS |
| 2016 | 701 | Sep 1 → Sep 2 2016 | Sep 8 2016 | PASS |
| 2017 | 1384 | Sep 1 → Sep 4 2017 | Sep 7 2017 | PASS |
| 2018 | 1698 | Aug 28 → Sep 4 2018 | Sep 6 2018 | PASS |
| 2019 | 696 | Sep 2 → Sep 4 2019 | Sep 5 2019 | PASS |
| 2020 | 2667 | Aug 25 → Sep 1 2020 | Sep 10 2020 | PASS |
| 2021 | 2656 | Aug 28 → Sep 1 2021 | Sep 9 2021 | PASS |
| 2022 | 2112 | Aug 31 → Sep 4 2022 | Sep 8 2022 | PASS |
| 2023 | 1104 | Aug 30 → Sep 1 2023 | Sep 7 2023 | PASS |
| 2024 | 742 | Aug 30 → Sep 1 2024 | Sep 5 2024 | PASS |
| 2025 | — | **no archive served** (falls back to the empty default shell) | — | N/A |

**13 PASS. Do not use 2007–2009 or 2011 as a preseason board.** They are exactly the look-ahead
failure `CLAUDE.md` §6.1 describes, and the 2007/2008/2009 windows all terminating on the identical
date (June 20, 2010) looks like an FFC data-migration artifact rather than real drafting behaviour.

**On the kickoff dates.** These are `[SECONDARY]` and should not be trusted as the production gate.
`nfl.db` already holds nflverse `schedules`; the gate should be computed as
`min(gameday) for season N` from that table, which makes it `[VERIFIED]` and automatic. Two rows
turn on a single day (2011 FAIL, 2012 MARGINAL), so the source of the kickoff date is load-bearing.

---

## 4. Format and team size — the constraint that matters most

### Half-PPR, 12-team `[VERIFIED]`

| Season | Drafts | Window | Kickoff `[SECONDARY]` | Gate |
|---|---|---|---|---|
| 2015, 2016, 2017 | — | **no half-PPR archive** | — | N/A |
| 2018 | 2414 | Aug 28 → Sep 4 2018 | Sep 6 | PASS |
| 2019 | 984 | Sep 2 → Sep 4 2019 | Sep 5 | PASS |
| 2020 | 1059 | Aug 30 → Sep 1 2020 | Sep 10 | PASS |
| 2021 | 3949 | Aug 29 → Sep 1 2021 | Sep 9 | PASS |
| 2022 | 1107 | Sep 3 → Sep 4 2022 | Sep 8 | PASS |
| 2023 | 4576 | Aug 28 → Sep 1 2023 | Sep 7 | PASS |
| 2024 | 906 | Aug 31 → Sep 1 2024 | Sep 5 | PASS |
| 2025 | — | **no archive served** | — | N/A |

**Half-PPR history starts in 2018 and gives 7 usable seasons.** It is a genuinely separate sample,
not a re-scoring of the non-PPR board: 2018 half-PPR draws on 2414 drafts while 2018 non-PPR draws
on 1698 `[VERIFIED]`.

### The archive is 12-team only — and it does not tell you

`[VERIFIED]`, four independent observations. Requesting an archived season at a team size FFC does
not hold returns **HTTP 200 with the 12-team page**, and only the `<h1>` reveals it:

| Requested URL | Heading actually served |
|---|---|
| `/adp/half-ppr/10-team/all/2018` | "Half-PPR Average Draft Position (2018), **12 Teams** All Players" |
| `/adp/half-ppr/10-team/all/2021` | "...(2021), **12 Teams**..." |
| `/adp/half-ppr/10-team/all/2022` | "...(2022), **12 Teams**..." |
| `/adp/half-ppr/14-team/all/2021` | "...(2021), **12 Teams**..." |
| `/adp/standard/10-team/all/2015` | "Non-PPR ... (2015), **12 Teams**..." — same 822 drafts as the 12-team URL |

A missing **format**-year behaves differently again: `/adp/half-ppr/12-team/all/2016` and
`/adp/ppr/12-team/all/2007` both return the site's **empty default shell**, headed "Non-PPR ...,
10 Teams", with **zero player rows** and a nonsense window sentence reading *"Data from 100 fantasy
football mock drafts between July 29, 2026 and July 29, 2026"* `[VERIFIED]`.

**The current season is unaffected** — `/adp/half-ppr/10-team/all/2026` correctly serves a 10-team
half-PPR board `[VERIFIED]`, which is what the daily capture is already getting.

### Depth per year

`[GAP] on exact row counts.` WebFetch's markdown conversion demonstrably drops rows — a full dump of
the 2010 table returned 25 monotonically-increasing rows containing no running backs at all, which
cannot be a real ADP table. **Do not quote a row count from this document.**

What *can* be stated: the largest "Overall" ADP value on each page `[VERIFIED]` runs 156.8 (2012),
161.4 (2016), 169.2 (PPR 2010), 169.6 (2019), 170.6 (2010), 171.1 (2013), 171.4 (2015), 173.6
(2023), 173.7 (2018 half-PPR), 174.9 (2020 half-PPR), 179.4 (2024 half-PPR), 209 (2021 half-PPR).
Every archived year therefore extends to roughly pick 155–210, i.e. the full draftable universe of a
12-team league, not a top-100 stub. The early years are shallower than the recent ones, but not
thin.

**The probe that closes this gap:** save one page's raw HTML and run the repo's own
`src/ingest_ffc_adp.py::parse_adp_table()` over it — the parser already exists and is fixture-
testable. That needs a shell, which this session did not have.

**One data-quality artifact worth knowing.** The 2016 archive page labels the Raiders defense "Las
Vegas Defense" `[VERIFIED]` — a 2020-onward name applied to a 2016 row. The archive is rendered by
joining historical ADP rows against a *current* player/team table. The ADP values are the datum and
are unaffected, but do not trust team labels on archived rows, and expect identity resolution to be
against present-day names.

---

## 5. Rules: fetching versus redistributing — answered separately

**Fetching: permitted.**
- `robots.txt` re-read today `[VERIFIED]`, verbatim disallow list: `/api/`, `/ajax/`, `/ajax-v2/`,
  `/import/`, `/adp/csv/`, `/draft/`, `/rate-my-team/results/`, `/rankings/custom/`. The path used
  here — `/adp/<format>/<teams>-team/all/<year>` — is **not** disallowed. The JSON API and the CSV
  export **are**, and must not be used.
- The founder contacted FFC directly and reported no restrictions `[SECONDARY]` — his words, via
  `docs/founder-requests/FR-023` and `docs/pm/MEMORY.md` §4. I have no way to verify the exchange
  itself; it is a founder report, not a published term.

**Redistributing / displaying to third parties: `[GAP]`, and it is now urgent.**
- FFC's Terms of Service **could not be retrieved again today**: `/terms` returns HTTP 404, and the
  footer-linked `/terms-of-service` renders navigation and footer only, with no body text
  `[VERIFIED]`. This exactly reproduces the July audit's finding
  (`docs/research/source-audit-2026-07.md` §5, regime E).
- `web.archive.org` is **blocked from this environment** ("Claude Code is unable to fetch from
  web.archive.org"). **Recorded as blocked; not routed around.**
- "Use as needed" answers *use*. It does not answer *republication*. Every recorded FFC
  authorisation (FR-023, MEMORY §4, D-021) is explicitly scoped to **private use by one person and
  void if the product reaches a second human.**

> **ESCALATION — this is not an ADP question.** `docs/CURRENT-STATE.md` records that the app is
> **live and public on the internet** as of 2026-07-29 (`fantasy-football.soft-water-e755.workers.dev`,
> public by explicit founder choice). Every source authorisation this project relies on — FFC
> (FR-023), FantasyPros (D-020), D-021 — carries the same voiding condition: *private, personal,
> founder-only*. A publicly reachable URL serving `board.json` is prima facie in tension with all
> three. I am not resolving this; it is a founder decision with a licensing consequence, and
> Cloudflare Access reportedly gates the site in ten minutes without touching the build.

**Other sources, against the same two questions:**

| Source | History | Fetch | Redistribute | Verdict |
|---|---|---|---|---|
| **FFC** | 2010–2024 non-PPR, 2018–2024 half-PPR (12-team) | Permitted (robots + founder ask) | `[GAP]` — ToS unretrievable | **The answer, for private use** |
| **FantasyPros ADP** `?year=YYYY` | Page titled "Half PPR Leagues 2015" renders for a 2015 request `[VERIFIED]`; table is JS-rendered so content unconfirmed `[GAP]` | Manual, human-paced only (MEMORY §4) | Barred — audit regime D | Not viable for a 15-season backfill |
| **MyFantasyLeague** | 1999–2013+ | Permitted | — | **Wrong shape.** Accumulated aggregate, today-stamped, cannot be date-bounded |
| **ESPN / Yahoo / CBS** | — | **Prohibited**, not lifted | Prohibited | Do not attempt |
| **Wayback Machine** | Would give true point-in-time captures | **Blocked from this environment** | — | Recorded blocked, stopped |
| nflverse / nflreadr | — | — | — | No ADP product found; `load_ff_rankings` is rankings, not ADP. `[GAP]` — not confirmed against nflreadr's own reference index |

---

## 6. Sample quality — read this before quoting "n=13"

**Thirteen seasons is n=13 in time and n=1 in market.** Every season comes from the same site's
drafter pool. This is not thirteen independent measurements of "the market"; it is one market
observed thirteen times. A finding that our ranking beats FFC ADP is a finding about FFC's mock
drafters, and generalises to Yahoo/ESPN/Sleeper drafters only by assumption.

Four further quality caveats, all `[VERIFIED]` from the pages themselves:

1. **These are mock drafts, not real leagues.** FFC's own sentence says "fantasy football mock
   drafts" on every page. Mock drafters are a self-selected, engaged population; Westwood's nine
   league mates are not.
2. **Precision varies ~9x across seasons.** Sample sizes run 507 (2012) to 4576 (2023 half-PPR).
   Treating each season-fold as equally precise is wrong; the fold-level standard errors are not
   comparable.
3. **The format nearest the primary league does not exist historically.** Half-PPR **10-team** has
   zero archived seasons. Non-PPR 12-team (n=13) and half-PPR 12-team (n=7) bracket Westwood but
   match neither — different replacement levels, different positional scarcity.
4. **The window is the last 2–8 days before kickoff.** That is a strength for this project
   specifically — Westwood drafts Mon 7 Sept 2026, squarely inside that window — but it means the
   captured board is a *late* preseason board, not a July or August one. Anything about ADP drift
   across the summer cannot be studied from the archive.

### What the n actually buys, arithmetically

The exact two-sided sign-test floor, `2 × (1/2)^n`:

| n | Floor p | vs α=0.05 | vs BH first rank at m=4 (α/m = 0.0125) |
|---|---|---|---|
| 4 (current ECR) | 0.125 | unreachable | unreachable |
| 7 (half-PPR) | 0.0156 | reachable | **fails — 0.0156 > 0.0125** |
| 8 | 0.0078 | reachable | passes |
| 13 (non-PPR) | 0.000244 | reachable | passes comfortably |

**Read this carefully.** At n=7 half-PPR, a *perfect* 7-of-7 sweep still would not survive
Benjamini-Hochberg at the first rank if the family is m=4 positions. Half-PPR alone does **not**
buy a four-position confirmatory test. Non-PPR at n=13 does. A test declared over fewer positions
(m=2, RB and WR) has a first-rank threshold of 0.025 and half-PPR's n=7 clears it. That choice must
be made **before** the run and registered, not after seeing which one works.

Note also that the sign test is a floor diagnostic. The project's mandated instrument is a
season-level bootstrap (guardrails §7); a percentile bootstrap over 7 fold-level differences is
coarse and over 4 is close to meaningless, which is the real reason n=4 fails.

---

## 7. Premise challenge: this does not un-limit PR-004

The brief says *"if genuine preseason market ADP is obtainable, the confirmatory test becomes
possible."* True for **a** confirmatory test; false for **PR-004**.

- PR-004 is registered, its consensus arm is declared `secondary` and `descriptive-only`, and §4
  exit 3 pre-closes the move: *"Re-run it with the rookie-inclusive universe / un-embargoed folds /
  a different seed. Each is a different test and requires a new PR id, which increments `m` and
  re-triggers BH across the whole family."* Swapping in a new baseline is at least as much a
  different test as those.
- ADR-C's rule is harder still: amending a registration after data is seen **irreversibly demotes
  it to exploratory**.

**The honest path is a new confirmatory registration** — market ADP as the B0 baseline, folds drawn
from the FFC-clean seasons, `m` declared before the run, BH recomputed across the family. That is
strictly better than PR-004's current position, because `CLAUDE.md` §6.5 names *"consensus market
ADP"* as baseline #1 and expert ECR was only ever a substitute for it. **PR-004 should still run as
registered.** Nothing here changes its verdict, and pausing it to wait for an ADP backfill would
trade a run that can happen for one that is not yet scoped.

Second premise correction: PR-004's *primary* arm (vs. prior-season points) already has 13 folds. It
was never in an n=4 trap. Only the **market-comparison headline** `CLAUDE.md` §6.5 demands was.

---

## 8. Defects found in `src/ingest_ffc_adp.py` — reported, not fixed

Research-only mandate; no code was changed. All three are `[VERIFIED]` against the module as
committed and the live pages.

1. **The docstring's central claim is false.** Lines 51–62 state *"FFC does not expose an as-of date
   for historical years, and there is no way to confirm the sample was drafted before that season's
   Week 1."* Every archived year that carries data states an explicit bounded draft-date range, and
   **the module's own `parse_sample_window()` already extracts it** (it is what populates
   `sample_window` in today's committed CSVs). The conservative default was safe, but it is
   discarding evidence the module itself parses.
2. **`is_retrospective_aggregate` is set by a calendar test, not an evidence test.**
   `capture_one_format()` computes `is_retro = period != current_year`. It should be derived from
   the parsed window against `min(gameday)` for that season in nflverse `schedules` — which would
   correctly pass 2013–2024 and correctly refuse 2007–2009, 2011 and 2012.
3. **A historical pull would be mislabelled.** `store_adp()` writes `teams` and `fmt` from the CLI
   arguments, never from the page. Because FFC silently serves the 12-team page for a 10-team
   archive request, `--period 2021 --teams 10 --format-key half_ppr` would write rows tagged
   `ffc_half_ppr_10team` containing **12-team** data. Fix: parse the `<h1>`, assert format/year/team
   count match the request, refuse on mismatch. (The absent-format case is already safe — the empty
   shell yields zero rows and the existing `RuntimeError` fires.)

---

## 9. The founder's "back to 2009" half-memory

Three candidate sources, all labelled as leads:

1. **FFC itself.** Its ADP selector offers **2007 through 2026** `[VERIFIED, page navigation]` and
   describes itself as a "20-year span of historical data" `[VERIFIED]`. A 2009 page exists and
   renders. This is by far the most likely match for the memory — and the finding here is precisely
   that the pre-2010 years are **not usable as preseason boards** despite existing.
2. **MyFantasyLeague, 1999 onward.** `FantasyFootballAnalytics/FantasyFootballAnalyticsR`'s
   `Historical ADP.R` carries `years <- 1999:2013` against MFL `[VERIFIED via the file on GitHub]`,
   with the note that the XML must be downloaded manually. If that project committed the resulting
   per-year files, they would be *someone else's* point-in-time captures — a genuinely interesting
   lead. **Unconfirmed:** I did not verify that such files are committed, what licence they carry,
   or whether they are preseason-bounded. `[GAP]`
3. **A Wayback capture of an ADP page.** Would be a true point-in-time snapshot with a real as-of
   date. **Blocked from this environment; not pursued.**

---

## 10. Recommended next steps, in priority order

1. **Decide the public-app / private-use-authorisation conflict** (§5 escalation). This gates
   everything, not just ADP.
2. **Fix the three ingester defects** (§8) before any historical pull. Pulling first and labelling
   later is how contamination enters silently.
3. **Backfill 2013–2024 non-PPR 12-team and 2018–2024 half-PPR 12-team**, one request per
   season-format, cached, rate-limited — 19 requests total, one time. Store the parsed
   `sample_window` and `total_drafts_in_sample` on **every** row and make the Week-1 gate a hard
   refusal, not a flag.
4. **Register a new confirmatory test** with market ADP as the baseline. Declare `m` and the format
   arm before looking at anything (§6's table shows why the choice cannot be made afterwards).
5. **Re-check whether a 2025 FFC archive appears.** All three formats currently return the empty
   shell for 2025 `[VERIFIED]`. If it never appears, the sealed 2025 holdout will have **no FFC
   market baseline**, and that cannot be captured retroactively.
6. **Run the two-week rolling-window check** on the committed daily FFC CSVs to close the §2
   residual gap at zero fetch cost.

---

## Sources

- [Fantasy Football Calculator — robots.txt](https://fantasyfootballcalculator.com/robots.txt)
- [FFC ADP, non-PPR 12-team, 2010](https://fantasyfootballcalculator.com/adp/standard/12-team/all/2010)
  (and the same path for 2007–2009, 2011–2024)
- [FFC ADP, half-PPR 12-team, 2018](https://fantasyfootballcalculator.com/adp/half-ppr/12-team/all/2018)
  (and the same path for 2015–2017, 2019–2025)
- [FFC ADP, half-PPR 10-team, 2026 (current)](https://fantasyfootballcalculator.com/adp/half-ppr/10-team/all/2026)
- [FFC ADP index](https://fantasyfootballcalculator.com/adp)
- [FFC Terms of Service (renders navigation only)](https://fantasyfootballcalculator.com/terms-of-service)
- [FantasyPros — Half PPR ADP, year=2015](https://www.fantasypros.com/nfl/adp/half-point-ppr-overall.php?year=2015)
- [FantasyFootballAnalyticsR — Historical ADP.R](https://github.com/FantasyFootballAnalytics/FantasyFootballAnalyticsR/blob/master/R%20Scripts/Historical/Historical%20ADP.R)
- [nflreadr package reference](https://nflreadr.nflverse.com/reference/index.html)
</content>
</invoke>
