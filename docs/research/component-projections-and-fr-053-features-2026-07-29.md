# Component projections: where they exist, on what licence — and the three FR-053 features

**Date:** 2026-07-29 · **Role:** researcher · **Scope:** research only. Nothing was built. No code, no
ingestion, no scraper, no data stored.

**Commissioned by:** FR-053 (`docs/founder-requests/FR-053-yahoo-draft-room-reference-capture-features-to-c.md`),
which records the first direct observation of a competitor mid-draft this project has ever had — five
founder screenshots of a live Yahoo draft room. Two asks routed to `researcher`:

- **A.** Where can per-player component projections be sourced, and on what licence? *(the unblocking
  question for FR-040 — worth more than the rest combined)*
- **B.** Are the three missing features worth having? *(evidence, not preference)*

**Builds on, does not re-derive:** `docs/research/competitive-ux-2026-07-29.md` (thread 086) and
`docs/research/competitor-recommendation-audit-2026-07.md` (thread 061). Where a fact is already
established there it is cited, not re-fetched.

| Tag | Meaning |
|---|---|
| `[VERIFIED]` | I fetched the page or endpoint this session and read it. For a vendor's own page this verifies **that they publish the claim** |
| `[SNIPPET]` | Seen only in a search excerpt or the search tool's synthesis; the page did not render or was not fetchable |
| `[SECONDARY]` | Third-party reporting only |
| `[GAP]` | Could not establish. Never filled with a plausible substitute |
| `[IN-REPO]` | Measured from this repository this session, with a file path |
| `[ANALYSIS]` | My own reasoning over tagged facts, labelled so it is never mistaken for a fetched claim |

---

## 0. Conclusion, first

### A. The one-sentence answer

**Component-level fantasy projections are freely and immediately obtainable for the founder's personal
use — but there is no free, openly licensed component projection set that this project may serve from
a public website.** Every published component set I found is either *personal-use-only* or behind a
*commercial licence negotiated by sales call*. That is the whole finding, and it splits FR-040's
"definitively dead" verdict in half rather than reversing it.

| | Local / personal tool | The live public site (`fantasy-football.soft-water-e755.workers.dev`) |
|---|---|---|
| Component projections available today, free | **Yes** — Sleeper's public endpoint, 2026 season, current `[VERIFIED]` | **No** — Sleeper ToS §9.2 forbids redistribution `[VERIFIED]` |
| Component projections available today, cheap | **Yes** — FantasyPros API Premium, $8.99/mo, explicit *personal-use licence* `[VERIFIED]` | **No** — that tier is "Personal & non-commercial apps" only `[VERIFIED]` |
| Component projections available for a public product | — | **Only by** (a) FantasyPros Commercial tier / PFF / SportsDataIO, price by sales call, or (b) building our own from nflverse (CC-BY-4.0) |

**So FR-040's blocker was never "components don't exist." It was "we host this publicly."** The
constraint moved from a data problem to a product-shape and licensing decision, which is the
founder's call, not a research finding.

### B. The three features, in one line each

| Feature | Verdict | Strength of evidence |
|---|---|---|
| **"Your turn — Nth pick" divider in the ranked list** | Cheap, but the case is *internal*, not competitive — and as a hard line it makes a deterministic claim about a probabilistic quantity | **`[GAP]` on user demand.** Nothing found either way |
| **Selectable projection source** | **Do not build.** The evidence points the other way, and Yahoo's own default contradicts its own feature | **Strongest evidence in this pass** — a 12-season, 11-source MAE study `[VERIFIED]`, plus Yahoo's default being a *consensus* `[SNIPPET]` |
| **ADP trend over a recent window** | Build it as an *availability* input, not as a *value* signal — and it needs **no new source or licence** | One `[VERIFIED]` vendor caveat against the value reading; `[IN-REPO]` evidence the data is already ours |

### Two live licensing exposures found while answering A — escalating, not resolving

Both are contradictions between a documented condition and the project's documented current state. I
am flagging them and stopping, per the standing rule.

1. **`board.json` is served publicly and carries FantasyPros-derived values.** Every board row
   exports `consensus_rank` (`src/export_contract.py:347`) and the header names
   `board_source`/`consensus_source` as `fantasypros_csv_2026draft`
   (`src/export_contract.py:435-441`), sourced from a founder-downloaded FantasyPros "ALL Rankings"
   CSV (`src/ingest_fantasypros_csv.py:1-15`) `[IN-REPO]`. FantasyPros' Terms of Use state: *"Except
   for a single copy made for personal use only, you may not copy, reproduce, modify, republish,
   upload, post, transmit, or distribute any documents or information from this site in any form or
   by any means without prior written permission."* `[VERIFIED]` `docs/CURRENT-STATE.md` records the
   app as live on the internet, public by explicit founder choice.
2. **FR-023's FFC permission carries a condition the project may have already crossed.** Its own
   text: *"Scoped to **private use by one person**. Void if the product ever reaches a second human,
   alongside D-020 and D-021."* `[IN-REPO]` The app is public.

Neither is mine to decide. Both belong to PM, and (1) plausibly belongs to the founder, since he is
the one who chose public hosting with the exposure trade stated to him.

---

## 1. Access record — what I could and could not reach

Load-bearing: it caps the confidence of everything below.

| Host / endpoint | Status | Consequence |
|---|---|---|
| `www.fantasypros.com` (robots, `/about/legal/`, `/nfl/projections/wr.php`, `/api-data/`) | `[VERIFIED]` robots: `User-agent: *`, `Disallow: /ajax/ /nfl/ranker/ /mlb/ranker/ /nba/ranker/ /api/ /json/ /xml/`, `Crawl-delay: 5`. Projections pages **not** disallowed | **Fetched.** Richest licensing source in this pass |
| `partnershq.fantasypros.com/faq` | Fetched; contains no licensing detail | Terms are per-partner, by email |
| `api.sleeper.com` (robots + `/projections/nfl/{season}`) | `[VERIFIED]` robots.txt is entirely commented out — nothing disallowed | **Fetched.** The single most important technical finding |
| `docs.sleeper.com` | `[VERIFIED]` | **Fetched.** No projections endpoint is documented |
| `support.sleeper.com/.../terms-of-use` | `[VERIFIED]` for §9.2 (verbatim); **§11.1 truncated by the fetch tool** | §9.2 quoted below. §11.1's exact anti-scraping wording is a `[GAP]` |
| `fantasy.nfl.com` (robots + `/research/projections`) | `[VERIFIED]` robots allows `/research/projections` | **Fetched once, for assessment.** Then stopped — see ToS below |
| `www.nfl.com/legal/terms/` | `[VERIFIED]` | **Systematic retrieval prohibited. Recorded as blocked; not routed around** |
| `ffopportunity.ffverse.com`, `nflreadr.nflverse.com/reference`, `github.com/nflverse/nflverse-data` | `[VERIFIED]` | **Fetched** |
| `github.com/FantasyFootballAnalytics/ffanalytics` + raw `DESCRIPTION` | `[VERIFIED]` | **Fetched** |
| `fantasyfootballanalytics.net` (two accuracy studies) | `[VERIFIED]` | **Fetched.** Best evidence in section B |
| `www.pff.com/news/license-our-player-projections` | `[VERIFIED]` | **Fetched** |
| `sportsdata.io/fantasy-sports-api` | `[VERIFIED]` that the page is silent on licence terms | **Fetched**, unhelpful on terms |
| `www.rotowire.com` (ADP article) | `[VERIFIED]`; `/about/api.php` 404s | **Fetched** the article; no API/licensing page found |
| `fantasyfootballcalculator.com/robots.txt` | `[VERIFIED]`: disallows `/api/`, `/ajax/`, `/ajax-v2/`, `/import/`, `/adp/csv/`, `/draft/`, `/rate-my-team/results/`, `/rankings/custom/` | **Fetched.** Relevant: our ingester uses `/adp/{fmt}/{teams}-team/all/{period}`, which is **not** disallowed (`src/ingest_ffc_adp.py:182`) `[IN-REPO]` |
| `api.fantasynerds.com/docs/nfl`, `www.fantasynerds.com` | **HTTP 403 to this fetcher**, both | **Not fetched.** Fantasy Nerds is a `[GAP]` |
| `www.mysportsfeeds.com/data-feeds/api-docs` | Page rendered navigation only | **Unretrieved content.** `[GAP]` |
| Every Yahoo-owned host (`sports.yahoo.com`, `help.yahoo.com`, `football.fantasysports.yahoo.com`) | **Standing block** (robots `Disallow: /` by agent name, per `docs/research/yahoo-draft-assistant-2026-07-29.md`) | **Not attempted.** All Yahoo claims here are `[SNIPPET]` from search-result synthesis |
| `espn.com`, `cbssports.com` | **Standing blocks** | **Not attempted** |
| `www.reddit.com` | **Refused by the tool** in thread 086; not retried | **Blocked.** Still the largest voice-of-customer hole |

**Fetching vs. redistributing, answered separately throughout.** Section 2's verdict table has two
distinct columns for exactly this reason, because for this project the answer differs *by column for
every single candidate*. Nothing in this document is a competitor's data proposed for storage or
display; the only numeric values quoted from any source are the two FantasyPros example rows and one
Sleeper stat block, reproduced solely as evidence of *what shape* the data is.

---

## 2. Question A — component projections: sources and licences

### 2.1 The distinction the dispatch asked for, stated first

| Kind | What it is | Candidates |
|---|---|---|
| **Published as components** | Someone else already forecasts receptions / yards / TDs / fumbles per player, and publishes those numbers | Sleeper (Rotowire), FantasyPros, NFL.com, PFF, SportsDataIO, Draft Sharks, Footballguys, Rotowire |
| **We could decompose** | Nobody hands us components; we build a forecasting model that produces them | nflverse raw data + our own model. **This is us building a projection system**, which is a different and much larger thing than an ingestion |

**nflverse belongs entirely in the second row, and this is the first thing to be clear about.**

### 2.2 nflverse publishes no forward-looking projections — including `load_ff_opportunity()`

`nflreadr`'s reference index lists 30 `load_*` functions. **None loads a forward-looking projection
for a future season** `[VERIFIED]`. `load_ff_rankings()` loads rankings; `load_ff_opportunity()` loads
*Expected Fantasy Points*.

`ffopportunity` is **retrospective, not predictive** `[VERIFIED]`. It applies an xgboost model to
nflverse play-by-play to answer *"how many points would the average player score given this
situation and opportunity"* — for plays that have already happened. It emits 159 variables including
`pass_yards_gained_exp`, `rec_yards_gained_exp`, `rush_yards_gained_exp`, `pass_touchdown_exp`,
`rec_touchdown_exp`, `rush_touchdown_exp`. Models trained on public nflverse data **2006–2020**.

`[ANALYSIS]` So it is genuinely a **component-level model** — but of the *conversion* step
(opportunity → expected stat line), not of the *opportunity* step. To get a 2026 projection you would
still have to forecast 2026 targets, carries and snaps yourself, then run them through it. That is
the larger project. What ffopportunity does give you, cheaply and legally, is a **component-level
backtest substrate**: expected stat lines for 2006–2025 that can be re-scored under any scoring
format, which is directly useful to Phase 1's harness even if no forward projection is ever built.

**Licence, and there is a trap here** `[VERIFIED]`:

| Artifact | Licence | Consequence |
|---|---|---|
| `nflverse-data` releases (pbp, player stats, rosters, snaps) | **CC-BY-4.0** | Attribution only. Redistribution and commercial use permitted. **The only route in this document that is clean for a public product** |
| `ffopportunity` code | GPL-3 | Only matters if we vendor the code |
| `ffopportunity` **data and models** | **CC-BY-SA 4.0** | **ShareAlike is viral.** A derived dataset built on it may have to be released under CC-BY-SA too |

`[ANALYSIS]` That asymmetry is worth designing around and is easy to miss: building component
projections from **raw nflverse pbp/player stats** carries attribution only; building them on top of
**ffopportunity's pre-fitted model** drags ShareAlike into whatever we produce. Same ecosystem, two
different licences. This mirrors `CLAUDE.md` §5's existing note that the FTN charting subset is
CC-BY-SA while the rest is CC-BY.

### 2.3 The verdict table — fetching and redistributing answered separately

| Source | Components published? | May we fetch? | May we display to third parties? | Cost |
|---|---|---|---|---|
| **Sleeper** (undocumented `/projections/`) | **Yes, full, current 2026** `[VERIFIED]` | Robots permit it `[VERIFIED]`; endpoint is undocumented, so **not** covered by the docs' own invitation to programmatic access | **No.** ToS §9.2 grants a *"personal and non-commercial"* licence and forbids redistribution `[VERIFIED]` | Free |
| **FantasyPros API — Free tier** | *"sample data"*, *"Non-production use"* `[VERIFIED]` | Yes | No | $0 |
| **FantasyPros API — Premium** | Yes: *"Rankings, projections, players, news & injuries"*, *"full stat lines"* `[VERIFIED]` | Yes | **No.** *"Personal-use license"*, *"Personal & non-commercial apps"* `[VERIFIED]` | **$8.99/mo**, bundled with HOF |
| **FantasyPros API — Commercial** | Yes | Yes | **Yes** — *"Commercial license & redistribution rights"* `[VERIFIED]` | **Custom**, "Talk to sales" |
| **FantasyPros web pages** (`/nfl/projections/*.php`) | **Yes** — columns `Player, REC, YDS, TDS, ATT, YDS, TDS, FL, FPTS` `[VERIFIED]`; not robots-disallowed, `Crawl-delay: 5` | Arguably — *"a single copy made for personal use only"* `[VERIFIED]` | **No** — same clause forbids republication `[VERIFIED]` | $0 |
| **NFL.com** (`fantasy.nfl.com/research/projections`) | **Yes, and the column set is an unusually good match to this league**: `Yds, TD, Int, Yds, TD, Rec, Yds, TD, TD(ret), FumTD, 2PT, Lost, Points` `[VERIFIED]` | **No — ToS blocks it.** *"Systematic retrieval of data or other content … is prohibited absent our express prior written consent"* `[VERIFIED]` | No | $0 |
| **PFF** | Yes — *"NFL player projection feed"*, CSV or XML, all fantasy-relevant categories, QB/RB/WR/TE/K/DST/IDP, kick and punt return, weekly + rest-of-season `[VERIFIED]` | Licence only | Licence only | Contact sales |
| **SportsDataIO / BAKER** | Yes — *"projected individual stats across all skill positions and scoring categories"* `[VERIFIED]` | Free trial offered | Page is **silent** on terms `[VERIFIED]` — a `[GAP]`, not a permission | Contact sales |
| **Rotowire (direct)** | Yes (it is the provider behind Sleeper's feed `[VERIFIED]`) | `[GAP]` — no API/licensing page found; `/about/api.php` 404s | `[GAP]` | `[GAP]` |
| **Fantasy Nerds** | `[GAP]` — **403 to this fetcher**, twice | `[GAP]` | `[GAP]` | `[GAP]` |
| **MySportsFeeds** | `[GAP]` — docs did not render | `[GAP]` | `[GAP]` | `[GAP]` |
| **Fantasy Football Data Pros** | Projections exist but are **2020 only** and *"based off ESPN's projections"*; *"Copyright 2020. All rights reserved."* `[VERIFIED]` | Free, no auth | Not stated; derived from a standing-blocked source | Free |
| **`hvpkod/NFL-Data`** (GitHub) | Yes — but it is *"extracted from Fantasy.NFL.com"*, MIT-licensed **repo** `[VERIFIED]` | — | **No.** `[ANALYSIS]` An MIT licence on a repository cannot grant rights its author never held. Third-party repackaging does not launder a source's terms | Free |
| **`ffanalytics`** (R, GPL) | It is a *scraper*, not a dataset: CBS, ESPN, FantasyPros, FantasySharks, FFToday, NumberFire, NFL, RTSports, WalterFootball `[VERIFIED]` | — | **No.** `[ANALYSIS]` Running it would breach several sources at once — ESPN and CBS are standing blocks here, NFL.com and FantasyPros forbid it in terms. **An open-source scraper is not a licence** | Free |
| **nflverse raw** (`load_pbp`, `load_player_stats`) | **No projections at all** `[VERIFIED]` | Yes | **Yes**, CC-BY-4.0, attribution required | Free |

### 2.4 The Sleeper finding, in detail — because it is the most actionable and the most conditional

`https://api.sleeper.com/projections/nfl/2026?season_type=regular&position[]=QB&order_by=ppr` returned
**151 QB rows** for season **2026**, `last_modified` in late July 2026 `[VERIFIED]`. A QB `stats`
object carries `pass_att, pass_cmp, pass_yd, pass_td, pass_int, pass_fd, cmp_pct, rush_att, rush_yd,
rush_fd, gp` plus `pts_std / pts_half_ppr / pts_ppr` and twelve `adp_*` variants. A WR object carries
`rec, rec_yd, rec_td, rec_fd, rush_att, rush_yd, rush_fd, fum_lost, gp, bonus_rec_wr`, reception
distance buckets (`rec_0_4 … rec_40p`), and the same points and ADP fields.

Three things follow, and the third is the one that matters.

1. `[ANALYSIS]` **The component coverage is close to sufficient for this league.** `CLAUDE.md` §7
   needs passing/rushing/receiving yards, TDs, INT, receptions, fumbles lost, return TD, 2-point
   conversions, and offensive fumble return TD. Sleeper's feed covers all of the high-mass ones and
   **`gp` — a projected games-played number**, which this project's availability work would otherwise
   have to invent. Return TDs and 2-pointers do not appear; NFL.com's column set does carry them,
   and NFL.com is ToS-blocked.
2. `[VERIFIED]` **The provider is Rotowire** (`"company": "rotowire"` on every record). So there are
   **two rights-holders**, not one: Sleeper's terms plus whatever Rotowire licensed to Sleeper. Any
   permission conversation would have to reach both.
3. `[VERIFIED]` **Sleeper ToS §9.2, verbatim, is decisive for the public site:** *"We grant you a
   limited, personal, revocable, non-transferable and non-exclusive right and license to access and
   use the Services … for your personal and non-commercial use … Except as expressly permitted
   herein, you must not, nor enable any other person to, rent, lease, lend, sell, redistribute,
   sublicense, copy, reverse engineer, decompile, translate, modify, rent, use as a service bureau,
   distribute copies of, adapt, create derivative works based on, or otherwise inappropriately use
   the Services."*

`[ANALYSIS]` There is a real tension inside Sleeper's own position, and it should be named rather
than resolved in our favour: they publish a documented, unauthenticated HTTP API, tell developers to
*"stay under 1000 API calls per minute"* and to *"save this information on your own servers"*
`[VERIFIED]` — which is an explicit invitation to programmatic access — while §9.2 licenses use as
personal and non-commercial only. The reconciliation that best fits both is: **programmatic fetching
is sanctioned; redistribution is not.** Note also that `/projections/` is *not* in the documented API,
so it does not even benefit from that invitation, and can change or disappear without notice.

`[GAP]` The exact wording of §11.1's prohibited-conduct list — the clause that would say plainly
whether automated collection is itself forbidden — **was truncated by the fetch tool and I could not
read it.** I am not going to characterise a clause I did not see.

### 2.5 Where Yahoo's own numbers come from — and why that closes the "just use theirs" idea

`[SNIPPET]` (search-result synthesis only; **every Yahoo host is a standing block and none was
fetched**): Yahoo states it has partnered with *"BAKER Predictive Engine, FTN, THE BLITZ, Rotowire and
more"* to produce *consensus* projections, and that **Fantasy Plus subscribers can select their
preferred projection model** while free users get the blended consensus.

`[VERIFIED as PFF's claim]` PFF's own licensing page names **Yahoo! Fantasy Football** among the
customers of its projection feed.

`[ANALYSIS]` So the 93.9 receptions on the founder's screenshot is the output of a stack of
**commercially licensed feeds**. There is no free route to that specific provenance, and there is no
version of "use Yahoo's numbers" that is both technically possible (Yahoo is blocked to us) and
permitted. The reachable equivalents are the same vendors, priced directly.

### 2.6 What I would say if asked "so what should we do" — framed as options, not a recommendation

Money is the founder's call and I am not recommending a spend. Three routes exist and they are not
mutually exclusive:

| Route | Unblocks | Cost | Legal for the public site? |
|---|---|---|---|
| **Personal-use ingestion** (Sleeper free, or FantasyPros Premium $8.99/mo) | Full custom scoring **computed locally**, backtesting of any scoring format, this league's stacking bonuses | £0–$8.99/mo | **No.** Would require the site to stop serving derived component values, or to go back to being local |
| **Commercial licence** (FantasyPros Commercial / PFF / SportsDataIO) | Everything, including the public site and any future multi-user version (`CLAUDE.md` §1) | Unknown, sales-call pricing `[GAP]` | Yes |
| **Build our own** from nflverse CC-BY-4.0 | Everything, plus it is the only route that is *ours* and the only one with no counterparty | Large — it is a projection system, i.e. `CLAUDE.md` build-order step 4/5 done properly | Yes, with attribution |

`[ANALYSIS]` One observation that is not a recommendation: routes 1 and 3 are complementary rather
than competing. A licensed component set that may not be *redistributed* may still be used
**privately as a validation target** for a home-grown model — which is exactly the baseline
comparison `CLAUDE.md` §6.5 already mandates, and it needs no public exposure at all.

---

## 3. Question B — are the three features worth having?

**Standing caution honoured:** "Yahoo has it" is not evidence. Thread 086 found the reverse for the
ESPN recommendation feed, which users explicitly asked to have removed `[SECONDARY]`.

### 3.1 The "YOUR TURN — 14TH PICK" divider in the ranked list

**User-demand evidence: `[GAP]`. I found none, in either direction, and I am reporting the absence
rather than reasoning from plausibility.** Searches for the interaction returned app-store listings
and vendor feature pages; the one third-party draft-software feature comparison I could fetch
(`draftkick.com`, six tools across ranks / board / rosters / standings / dashboard) **does not mention
the feature at all** `[VERIFIED]`.

What *is* established:

- `[SNIPPET]`, prior work (thread 061): FantasyPros ships the probabilistic version — **Pick
  Predictor**, *"the odds a player is taken before your next pick"* by simulation over multi-source
  ADP, opponent roster needs and picks remaining — and **gates it behind premium**. Draft Sharks
  sells an equivalent. `[ANALYSIS]` Two vendors monetising the question is weak commercial evidence
  that it is valued; it is not evidence that a *divider* is the right rendering of it.
- `[IN-REPO]` This project already computes survival probability to the next pick. The divider is
  therefore **not a new capability — it is a cheaper rendering of one we have**, and one this project
  answers better than a line can.

`[ANALYSIS]` **The design constraint nobody has stated, and it is the reason I would not ship it as
drawn.** A hard line asserts *"everything above is gone."* The truth is a probability that decays
smoothly across dozens of rows. Drawing a line converts a calibrated distribution into a binary
claim — precisely the unearned confidence `CLAUDE.md` §11 forbids, and the same failure mode thread
086 identified in composite scores. If it is built, it should be a **band** (*"picks 12–19 are the
uncertain zone"*) or a labelled line (*"~50% of these are gone by your pick"*), not a rule.

**Net:** worth having as a *display of the availability model*, not as a copy of Yahoo. The case for
it is internal and honest; there is no external demand evidence, and saying so is the useful part.

### 3.2 Selectable projection source — the evidence says no, and it is the strongest evidence in this pass

`[VERIFIED]` **Fantasy Football Analytics has run an annual projection-accuracy study across 2014–2025
NFL seasons, 11 sources** (CBS, ESPN, FFA Average, FFA Weighted, FFToday, FantasyPros, FantasySharks,
NFL, NumberFire, RTSports, WalterFootball), scored by **MAE** with supplementary R² and mean error.
Two verbatim findings:

> *"The average of sources is more accurate than individual sources. This remains true and is perhaps
> the most robust finding in our analysis, consistent with the principle of the wisdom of the crowd."*

> *"FFA Average outperformed individual sources in 69% of head-to-head comparisons across all
> positions and seasons."*

`[VERIFIED]` And individual sources are **not stably good**: CBS ranked first for QB projections in
2019, then sixth in 2021, second in 2022, seventh in 2023. Their companion post makes the same point
about ESPN — best QB projections in 2016–17, last in recent years.

`[SNIPPET]` **Yahoo's own product contradicts its own feature.** Yahoo's free default is a
*consensus* of multiple licensed providers, marketed by Yahoo as the more accurate thing; the
source-switcher the founder saw is a **Fantasy Plus paid** control. (Yahoo hosts not fetched.)

`[VERIFIED]`, prior work (thread 086): Draft Sharks' choice is instructive and different — they show
**three numbers simultaneously** per player (their baseline, a 38-site consensus, and a ceiling/floor
pair) rather than a switcher. And Draft Sharks' self-criticism, quoted in thread 086: *"The extensive
amount of features and data might be overwhelming."*

`[ANALYSIS]` **A switcher asks the user to make a choice they have no basis for making, and it throws
away the one thing multiple sources are actually good for.** If this project ever holds more than one
component set, the evidence says: average them, and render the **spread between them** — which is the
same object as thread 086's top-ranked recommendation (uncertainty on the row, *"not distinguishable
from ranks X–Y"*). One display, two findings, no new control. A switcher converts a
variance-reduction opportunity into a UI decision.

**Secondary and independent reason to decline:** every additional source is an additional licence
(§2.3). A switcher multiplies the licensing surface by the number of options.

**Net: do not build a projection-source switcher.** Build an aggregate, and show its disagreement.

### 3.3 ADP trend over a recent window

**Against reading it as a value signal — from the vendor that sells the data** `[VERIFIED]`, RotoWire:

> *"Fantasy football ADP is solely a measure of how a player's perceived value is trending. These
> changes will oftentimes not match up with a player's updated RotoWire fantasy football
> projections."*

`[GAP]` **No empirical study of the predictive value of short-window ADP movement was found.** Every
search returned weekly risers-and-fallers content — 4for4, RotoWire, Fantasy Life, STACKED — i.e. the
category publishes the *feature* constantly and the *evidence* never. Fantasy Life is a recorded block
and was not fetched.

**For building it — and this is the decisive practical point** `[IN-REPO]`: **it needs no new source
and no new licence.** The daily ADP capture is already running off-machine via GitHub Actions;
`data/adp-snapshots/` holds `2026-07-26.csv`, `2026-07-28.csv`, `2026-07-29.csv` today. A rolling
7-day window becomes computable within days, and the founder's draft is 7 September — so by draft day
this project would hold roughly six weeks of its own daily ADP history. Yahoo charges for "Last 7 Days
ADP"; we would be computing it from data we already own, under permissions we already have.

`[ANALYSIS]` **The framing that makes it honest.** ADP velocity is a **market-behaviour** signal, not
a **value** signal — RotoWire says so explicitly, and thread 078 already named "pick-level ADP
velocity" as an *availability* input. Used to answer *"will he still be there at my pick"* it is
measuring exactly the right thing. Used to answer *"is he good"* it is measuring hype, and the vendor
selling it says so.

**Net: build it, scoped to availability.** Low cost, zero new licence, honest framing available. Do
not surface it as a value or recommendation signal.

---

## 4. Sample quality — read this before quoting anything above

### Section A: twelve sources, but an effective n of three

The candidate list looks broad. It is not. Every source collapses into one of three **licence
regimes**, and the regime — not the vendor — is what determines the answer:

| Regime | Members | Effective n |
|---|---|---|
| Open data, **no forward projections** | nflverse (+ ffopportunity) | **1** |
| Component projections published, **personal-use only** | Sleeper/Rotowire, FantasyPros web + Premium API, NFL.com | **3 vendors, 1 answer.** Every one permits personal fetching and forbids third-party display |
| Component projections, **commercial licence by sales call** | FantasyPros Commercial, PFF, SportsDataIO, Rotowire direct | **4 vendors, 1 answer,** and **all four prices are `[GAP]`** |

**The count that matters is zero:** sources found that publish component projections under a licence
permitting redistribution. `[ANALYSIS]` That is a strong negative result and I would not expect more
searching to change it — the reason is structural, not coverage. Projections are the product these
companies sell; a free redistributable one would undercut the whole category.

**Flag: three named candidates were unreachable and their absence is not evidence they are unsuitable.**
Fantasy Nerds 403'd twice, MySportsFeeds did not render, Rotowire has no findable licensing page. Any
of them could carry terms more permissive than the seven I did read.

### Section B: no user voice at all, and the best study has a conflict of interest

- **Zero voice-of-customer evidence in this entire pass.** Reddit remains refused by the tool
  (thread 086 recorded it; not retried). App Store review text was not re-mined. All three verdicts
  rest on vendor documents, one vendor-run study, and one vendor caveat. `[GAP]`
- **The FFA accuracy study is run by the maintainers of `ffanalytics`, whose product *is* the
  aggregate.** They benchmarked their own average against everyone else's and their average won.
  That is structurally the same conflict thread 086 flagged for the Draft Sharks competitor
  comparison, and **it agrees with what I expected before looking, which is exactly when it deserves
  most scrutiny.** Two things partly rescue it: the mechanism is unsurprising on priors (averaging
  independent estimates reduces variance), and Yahoo — a competitor with no stake in FFA — reaches the
  same conclusion by shipping a consensus as its free default. Quote it as *"the vendor of the
  aggregate says the aggregate wins, and a large independent platform behaves as if that is true"*,
  never as a neutral referee's verdict.
- **Still zero behavioural observation of any competitor under a real clock by this project's agents.**
  FR-053's screenshots are the first such observation in the project's history and they came from the
  founder, not from research. That asymmetry is worth noticing: **the founder can see things no agent
  here can**, and five screenshots produced more competitive fact than two full research passes.

---

## 5. Gaps — listed so nobody fills them by accident

1. `[GAP]` **Sleeper ToS §11.1's prohibited-conduct list.** Truncated by the fetch tool. It is the
   clause that would say whether automated collection is itself forbidden, independent of §9.2's
   redistribution ban.
2. `[GAP]` **Every commercial price.** FantasyPros Commercial, PFF, SportsDataIO and Rotowire all
   quote by sales call. No number is knowable without an email, and I have not sent one.
3. `[GAP]` **Fantasy Nerds** — 403 to this fetcher on both `api.fantasynerds.com/docs/nfl` and
   `www.fantasynerds.com`. Historically a low-cost API with projections; terms unknown.
4. `[GAP]` **MySportsFeeds** — docs page rendered navigation only. Historically had a
   personal/non-commercial free tier; unconfirmed.
5. `[GAP]` **Rotowire's own licensing terms**, despite Rotowire being the provider behind the best
   free feed found. `/about/api.php` 404s and no equivalent page surfaced.
6. `[GAP]` **Whether Sleeper's `/projections/` endpoint is stable.** It is undocumented. It could be
   removed or authenticated tomorrow with no notice and no breach on their part.
7. `[GAP]` **Any user demand evidence for the "your turn" divider.** Nothing found in either
   direction.
8. `[GAP]` **Any empirical study of short-window ADP movement's predictive value.** The category
   publishes the feature weekly and the evidence never.
9. `[GAP]` **Whether Yahoo's free-tier projections are the consensus or a single provider**, and what
   exactly its player card is showing. Yahoo is blocked; §2.5 is search synthesis only.
10. `[GAP]` **All Reddit voice-of-customer**, unchanged from thread 086 and not closable by this
    agent class.
11. `[GAP]` **What FantasyPros' Free API tier's "sample data" actually contains.** If it happens to
    include real component projections at low volume, the personal-use route gets cheaper still.

---

## Sources

Fetched this session (`[VERIFIED]`):
[FantasyPros robots.txt](https://www.fantasypros.com/robots.txt) ·
[FantasyPros Terms of Use](https://www.fantasypros.com/about/legal/) ·
[FantasyPros WR projections](https://www.fantasypros.com/nfl/projections/wr.php?week=draft) ·
[FantasyPros API tiers](https://www.fantasypros.com/api-data/) ·
[FantasyPros Partners FAQ](https://partnershq.fantasypros.com/faq) ·
[Sleeper API docs](https://docs.sleeper.com/) ·
[api.sleeper.com robots.txt](https://api.sleeper.com/robots.txt) ·
[Sleeper 2026 QB projections endpoint](https://api.sleeper.com/projections/nfl/2026?season_type=regular&position[]=QB&order_by=ppr) ·
[Sleeper Terms of Use](https://support.sleeper.com/en/articles/5486620-terms-of-use) ·
[fantasy.nfl.com robots.txt](https://fantasy.nfl.com/robots.txt) ·
[NFL.com Terms & Conditions](https://www.nfl.com/legal/terms/) ·
[ffopportunity](https://ffopportunity.ffverse.com/) ·
[nflreadr function reference](https://nflreadr.nflverse.com/reference/index.html) ·
[nflverse-data](https://github.com/nflverse/nflverse-data) ·
[ffanalytics](https://github.com/FantasyFootballAnalytics/ffanalytics) ·
[FFA — Which projections are most accurate](https://fantasyfootballanalytics.net/which-projections-are-most-accurate) ·
[FFA — 2024 accuracy study](https://fantasyfootballanalytics.net/2024/12/which-fantasy-football-projections-are-most-accurate.html) ·
[PFF — License our player projections](https://www.pff.com/news/license-our-player-projections) ·
[SportsDataIO fantasy API](https://sportsdata.io/fantasy-sports-api) ·
[RotoWire — ADP risers and fallers](https://www.rotowire.com/football/article/fantasy-football-adp-risers-fallers-before-draft-115205) ·
[Fantasy Football Calculator robots.txt](https://fantasyfootballcalculator.com/robots.txt) ·
[hvpkod/NFL-Data](https://github.com/hvpkod/NFL-Data) ·
[Fantasy Football Data Pros API](https://www.fantasyfootballdatapros.com/our_api) ·
[DraftKick — draft software feature comparison](https://draftkick.com/blog/fantasy-draft-software-feature-comparison/)

Blocked, refused or unreachable — recorded, not routed around:
every Yahoo host (robots, by agent name) · `espn.com` (standing block) · `cbssports.com` (standing
block) · `www.reddit.com` (tool refusal, thread 086) · `www.nfl.com` **ToS-blocked for systematic
retrieval** after a single assessment fetch · `api.fantasynerds.com` and `www.fantasynerds.com`
(HTTP 403) · `www.mysportsfeeds.com/data-feeds/api-docs` (content did not render) ·
`www.rotowire.com/about/api.php` (404) · `www.fantasylife.com` (prior audit's recorded block,
honoured for consistency)

Prior in-repo work built on rather than re-derived:
`docs/research/competitive-ux-2026-07-29.md` (thread 086) ·
`docs/research/competitor-recommendation-audit-2026-07.md` (thread 061) ·
`docs/research/yahoo-draft-assistant-2026-07-29.md` · `docs/founder-requests/FR-040`, `FR-023`,
`FR-053` · `src/make_board.py`, `src/export_contract.py`, `src/ingest_fantasypros_csv.py`,
`src/ingest_ffc_adp.py`
