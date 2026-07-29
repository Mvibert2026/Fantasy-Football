# Sourcing the three unbuilt inputs — Vegas odds, coaching staff, route participation

**Date:** 2026-07-29 · **Role:** researcher · **Scope:** research only. No ingestion, no scraper,
no build.

Confidence tags on every claim: `[VERIFIED]` fetched from the source's own page/API this session ·
`[SNIPPET]` seen only in a search excerpt · `[SECONDARY]` third-party reporting · `[GAP]` could not
establish. **No `[GAP]` in this document has been filled with a plausible number.**

Two questions kept separate throughout, because they have different answers for almost every source:
**fetch** (may we retrieve it) and **display / redistribute** (may we show it to anyone else).

---

## 0. Premise check — read before the conclusions

Three things in the dispatch needed testing against the repo before I acted on them.

**(a) "All three have never been built" — CONFIRMED.** `docs/deferred.md` states `coach_id`,
`odds_snapshots` and `adp_snapshots` "remain unbuilt". No `spread_line`, `total_line`, `over_odds`,
`moneyline`, `home_coach` or `away_coach` string appears anywhere in `src/` — grepped the whole repo,
the only hits are two prose mentions in `docs/`. There is no odds table, no coach table, and no
route feature. The premise holds.

**(b) "Vegas odds are probably the highest-value missing input" — CONTRADICTED BY THE REPO. Flagged,
not resolved.** `docs/test-registry.md` places Vegas win totals and implied team totals at **#11, in
Tier 0**, with expected edge **"Low"** — and Tier 0 is defined in that file as "Everyone has these.
Not having them is a loss; having them is not an edge." The same registry rates **#17 route
participation rate "High"** and **#29 coordinator continuity "High"** (bolded). So the repo's own
prioritisation is the reverse of the dispatch's on expected edge.

That is a contradiction between the task framing and a written project document, and per the standing
rules I have not resolved it alone. I did the research on all three as asked — the ordering dispute
does not change what is obtainable — but **I have not adopted "highest-value" as a fact, and §5's
recommendation is decided on the evidence gathered here rather than on the dispatch's ordering.**
The two claims are reconcilable: odds may well be the *cheapest* input and still the *lowest-edge*
one. Cheapness is a legitimate reason to do something first; it is not the same claim.

**(c) One citation slip, minor.** The dispatch attributes the MyFantasyLeague retrospective-aggregate
trap to `CLAUDE.md` §6.1. §6.1 states the general look-ahead rule; the MFL-specific finding lives in
`docs/CURRENT-STATE.md` open item 2 and `docs/pm/MEMORY.md` §4. Noted so the citation does not
propagate.

**(d) What I could not do here, stated so it is not mistaken for a choice.** This session ran in a
cloud container with **no shell tool at all** — read, write, grep, glob and web fetch only. So there
is **zero `[MODAL-SAMPLED]` evidence in this document**: I could not run `nflreadpy`, could not query
`data/nfl.db`, and could not call any API that needs a key. Everything below is documentation and
page evidence. Several `[GAP]`s marked here are one Python query away for anyone with a shell, and I
say which.

---

## 1. Conclusions first

| Input | Obtainable? | Terms (fetch / display) | Cost | How far back |
|---|---|---|---|---|
| **Vegas — game spreads, totals, moneylines** | **Yes, already inside a library this repo imports** | CC-BY-4.0 · fetch **and** display permitted with attribution | **$0** | 1999 → present `[SNIPPET]` |
| **Vegas — implied team totals** | **Yes — arithmetic from the two above, not a separate source** | as above | **$0** | as above |
| **Vegas — point-in-time intraday snapshots** | Yes, paid | The Odds API · fetch + in-app display permitted; raw-feed redistribution prohibited | **$30/month** | **2020-06-06 only** |
| **Vegas — season win totals** | Yes, free, with a date-provenance problem | covers.com · fetch permitted (no anti-automation clause, robots open); **display/redistribution prohibited** | **$0** | 1999 → 2026 `[VERIFIED]` |
| **Coaching staff — head coach** | Already available, already known | nflverse CC-BY-4.0 · display permitted | **$0** | 1999 → 2026 (per repo record) |
| **Coaching staff — coordinators** | **Yes — Wikipedia, via an official API. This is the new finding.** | CC BY-SA 4.0 · fetch **and** display permitted, attribution + share-alike | **$0** | ~1946 → 2024 `[VERIFIED]` |
| **Route participation — direct** | **No free source. Paid source blocked for automation** | Fantasy Points ToS forbids spiders/scrapers/data-mining · manual human-paced use only | **`[GAP]`** — price not retrievable | n/a |
| **Route participation — proxy** | Yes, derivable, with a named position-correlated bias | nflverse participation, CC-BY-SA 4.0 | **$0** | **2016 → 2024 only** |

**Recommendation: pursue coaching staff first.** Reasoning in §5.

---

## 2. Vegas odds

### 2.1 Game spreads and totals are not a sourcing problem — they are already a dependency

`nflreadpy.load_schedules()` returns Lee Sharpe's games file, which carries betting columns. From
the nflreadr schedules dictionary, verbatim `[VERIFIED]`:

| Field | Dictionary text |
|---|---|
| `spread_line` | "The spread line for the game. A positive number means the home team was favored by that many points, a negative number means the away team was favored by that many points. This lines up with the result column." |
| `total_line` | "The total line for the game." |
| `away_moneyline` | "Odds for away team to win the game." |
| `home_moneyline` | "Odds for home team to win the game." |
| `over_odds` | "Odds that total score of game would be over the total_ine." *(typo is in the source)* |
| `under_odds` | "Odds that total score of game would be under the total_line." |
| `away_spread_odds` | "Odds for away team to cover the spread." |
| `home_spread_odds` | "Odds for home team to cover the spread." |

`[SNIPPET]` The games file begins with the 1999 season. `[GAP]` Which season each *betting* column
first becomes non-null — that is not the same question as when the file starts, and no documentation
states it. **This is measurable in one query** by anyone with a shell:
`SELECT season, COUNT(spread_line), COUNT(home_moneyline) FROM load_schedules() GROUP BY season`.
I could not run it (§0d).

`[VERIFIED]` Licence: nflverse data is CC-BY-4.0 — per `docs/research/source-audit-2026-07.md`, the
only source in this project's entire audit that affirmatively permits **display and redistribution**
subject to attribution.

**Implied team total needs no new source.** It is arithmetic on the two columns already present:

```
favourite_implied_total  = total_line / 2 + |spread_line| / 2
underdog_implied_total   = total_line / 2 - |spread_line| / 2
```

`CLAUDE.md` §5 names "implied team totals" as a thing to source. At game level it is a derived
column, not an acquisition.

### 2.2 The one gap that decides look-ahead safety — and why it bites less than it looks

`[GAP]` **Whether `spread_line` / `total_line` are opening lines, closing lines, or something else
is not documented anywhere I could reach.** The dictionary says only "The spread line for the game."
No sportsbook is named, no timestamp column exists, and `nfldata`'s own `DATASETS.md` and README
carry no provenance note. This is the single most important unanswered question about the free odds
path and I could not close it.

Where it bites and where it does not, stated precisely because the distinction is the whole point:

- **Does not bite for the project's stated backtest rule.** `CLAUDE.md` §6.1 permits season-N ranking
  inputs to use data "through the end of season N−1 and preseason N only." Every season N−1 game line
  predates the season-N cutoff *whether it is an opening or a closing line*. So prior-season
  aggregate offensive-environment features (mean implied team total, mean total, mean spread) are
  safe to build on this today, at zero cost, with no provenance answer.
- **Does bite** the moment anyone uses season-N game lines to rank for season N. If they are closing
  lines they encode information from the days before kickoff. The harness is supposed to refuse this
  structurally regardless (§6.1), so the correct control is the access layer, not the provenance
  answer.
- **Does bite** for any in-season weekly feature, which is out of Phase 1 scope anyway.

### 2.3 The Odds API — the paid point-in-time option, game lines only

All `[VERIFIED]` from the-odds-api.com's own pages this session.

| | |
|---|---|
| Historical coverage | "Historical odds data is available from June 6th 2020, with snapshots taken at 10 minute intervals." 5-minute intervals from September 2022 |
| Are these genuine point-in-time snapshots? | **Yes.** Timestamped snapshots at fixed intervals, with `date` parameters and navigation fields for traversing history — not a settled line reassembled afterwards. This is exactly the property the dispatch asked about |
| Markets covered historically | Featured markets (h2h, spreads, totals, outrights) across the whole period; player props and alternate lines only after 2023-05-03 |
| Access | "This endpoint is only available on paid usage plans." Historical requests charge **10× the standard credit rate** |
| Pricing | Free **$0** / 500 credits per month — **historical excluded**. **$30/mo** / 20,000 credits. **$59/mo** / 100,000. **$119/mo** / 5,000,000. **$249/mo** / 15,000,000 |
| Terms — fetch and in-app display | *Permitted, including commercially:* "We support and encourage the use of our data in websites, mobile apps, dashboards, analytical tools, and other user-facing applications, including commercial use, provided our data is not the primary product being sold or redistributed" |
| Terms — redistribution | *Prohibited:* "Do not resell, repackage, or redistribute our data as a standalone data product. This includes, but is not limited to, offering our data through your own API, data feed, downloadable files, or any other format intended to serve as a source of raw data for others" |

**Two things this does not do, and both matter.**

1. `[VERIFIED]` **It has no NFL season win totals market.** Its American-football sport keys are
   `americanfootball_nfl`, `americanfootball_nfl_preseason`, `americanfootball_nfl_super_bowl_winner`,
   `americanfootball_cfl`, `americanfootball_ncaaf`, `americanfootball_ncaaf_championship_winner`,
   `americanfootball_ufl`. There is no team-win-total key or market. **Do not buy this expecting the
   win totals `CLAUDE.md` §5 names first.**
2. It starts 2020-06-06. Seasons 1999–2019 are unreachable through it at any price.

**Where it is the right answer:** it is the only odds source found whose terms permit showing the
data to a third party inside an application. If this project ever ships to a second human, the free
covers.com path dies and this one survives.

### 2.4 Season win totals — free, deep, and with a real date-provenance problem

SportsOddsHistory now redirects to `covers.com/sportsoddshistory/` (301, `[VERIFIED]`; owned by CS
Media Limited).

`[VERIFIED]` The archive index at `/sportsoddshistory/nfl-odds/` links **preseason win totals pages
for every season 1999 → 2026**, at `/sportsoddshistory/nfl-win/?y=<year>&sa=nfl&t=win`.

Two season pages fetched directly:

| Season | Teams | Columns | As-of date on page |
|---|---|---|---|
| 2020 | 32 | Team · Win Total · Over Odds · Under Odds · Week bet settled · Actual Wins · Result | **"As of September 10, 2020"** |
| 2012 | 32 | identical | **none** |

**Sample-quality finding, and it is the decisive one for this source.** n = 2 of 28 seasons, and the
two disagree on the thing that determines usability. The 2020 page dates its lines to the eve of
Week 1 — a legitimate preseason snapshot. The 2012 page carries no date at all. **Date provenance is
therefore inconsistent across the archive and cannot be assumed from a single spot-check.** Neither
page names a sportsbook. `[GAP]` Whether the undated seasons are opening lines, consensus lines, or
end-of-preseason lines. Any ingest must record per-season whether an as-of date was present and
refuse to treat undated seasons as dated ones — the same discipline ADR-054 already applies to FFC
historical pulls with `is_retrospective_aggregate`.

**Terms.**

- `[VERIFIED]` `www.sportsoddshistory.com/robots.txt`: `User-agent: *` / `Disallow:` — nothing
  disallowed.
- `[VERIFIED]` `www.covers.com/robots.txt`: no AI-crawler blocks (no ClaudeBot, Claude-User,
  anthropic-ai, GPTBot or CCBot entries). 40+ disallowed paths, none covering `/sportsoddshistory/`.
- `[VERIFIED]` `www.covers.com/terms` — **no anti-automation clause.** No mention of robots, spiders,
  scrapers, crawlers, or data mining. But the reproduction clause is broad and in capitals:
  > "EXCEPT AS EXPRESSLY AUTHORIZED BY COVERS.COM, OR ADVERTISERS, YOU AGREE NOT TO REPRODUCE,
  > REPUBLISH, UPLOAD POST, TRANSMIT, DISTRIBUTE, COPY, PUBLICLY DISPLAY OR OTHERWISE USE ANY CONTENT
  > OR ANY DERIVATIVE WORKS BASED ON THE WEBSITE, SERVICES, CONTENT OR THE SOFTWARE, IN WHOLE OR IN
  > PART."

  and, permitting personal retrieval:
  > "you may download certain Content and Services available on the Website to a single personal
  > computing device for your use and entertainment. However, you may not distribute, modify,
  > republish, or publicly display any of the Content or Services unless you have the prior written
  > permission of Covers.com"

**Verdict: fetch permitted, display prohibited.** Structurally identical to the FantasyPros position
already recorded in D-020 — fine for a private single-user tool and for backtesting, void the moment
a second person sees a screen. Rate-limit and cache regardless.

---

## 3. Coaching staff history

### 3.1 Pro Football Reference — re-verified today, still blocked

`CLAUDE.md` §5 names PFR and instructs verification before building. Done, this session:

- `[VERIFIED]` `https://www.pro-football-reference.com/robots.txt` → **HTTP 403 Forbidden.**
- `[VERIFIED]` `https://www.sports-reference.com/data_use.html` → **HTTP 403 Forbidden.**

Unchanged from the 2026-07-25 finding in `docs/data-availability.md` §7.9. The crawl policy and the
data-use policy are both unreadable programmatically, so **the conservative default applies and no
permission can be inferred.** Recorded as blocked and stopped. No scraper considered, no alternate
user-agent tried, no cached copy sought. `[GAP]` Whether Sports Reference sells a data licence and at
what price — the page that would say so is the one returning 403.

### 3.2 Does a permissively-licensed dataset already carry it? No for coordinators

- `[VERIFIED]` `nfldata`'s `DATASETS.md` lists nine datasets: Draft Picks, Draft Values, Games,
  Colors, Logos, Rosters, Standings, Teams, Trades. **No coaching dataset.** The only coaching fields
  anywhere are on Games: `home_coach` / `away_coach` = "Name of the head coach of the home/away team."
- `[VERIFIED]` nflreadpy's full loader list (23 functions) contains no coach, coordinator or staff
  loader.

So the repo's existing record is correct and unchanged: **head coach yes, 1999–2026 via schedules;
coordinators no.** `docs/test-registry.md` #29/#30 stay gated on that basis — and #29b (head-coach
continuity) remains the separate, weaker, buildable-today hypothesis it was already logged as.

### 3.3 The finding: Wikipedia carries coordinator-level staff per team-season, under a licence
better than anything else in this project

`[VERIFIED]`, via the MediaWiki API (`en.wikipedia.org/w/api.php`):

- `Template:NFL final staff` is transcluded on **more than 1,062 mainspace articles** — 554 returned
  in a first `list=embeddedin&eilimit=500` batch, 508 in the second, and a continue token was still
  present after both, so 1,062 is a **floor, not a total.**
- Titles visible in those batches span **"1946 San Francisco 49ers season"** through **"2024 Atlanta
  Falcons season"**.
- The template sits in a `==Staff==` section on team-season articles and names coordinators.
  Verified on two articles by pulling the section wikitext directly:

| Article | Head coach | Offensive coordinator | Defensive coordinator |
|---|---|---|---|
| 2019 Atlanta Falcons season | Dan Quinn (infobox) | **Dirk Koetter** | none listed — only "Defensive passing game coordinator/secondary – Jerome Henderson" |
| 2024 Atlanta Falcons season | — | **Zac Robinson** | **Jimmy Lake** |

  The 2019 absence is a real-world fact (Dan Quinn called the defence himself), not a data hole —
  which is itself the useful warning: this source will produce legitimate nulls that a naive ingest
  will mistake for missing data.

**Terms — and this is the best licensing position of any source in the whole project.**
`[VERIFIED]` Wikimedia Foundation Terms of Use:

- API use is permitted, conditionally: "By using our APIs, you agree to abide by all applicable
  policies governing the use of the APIs, which include but are not limited to the User-Agent Policy,
  the Robot Policy, and the API:Etiquette." Prohibited is automation that is "abusive or disruptive"
  or places "an undue burden on an API."
- Text is licensed **CC BY-SA 4.0** (and GFDL), and reuse requires attributing the authors.

**Fetch: permitted, with a descriptive User-Agent and polite rate limiting. Display: permitted, with
attribution and share-alike.** That makes coordinator history the only one of the three inputs in
this document that could legally appear on a screen shown to a second human.

**Sample quality — read this before costing a build.** I checked **two articles, both the same
franchise (Atlanta), 2019 and 2024.** That is an n of one franchise, and it is not a representative
sample of 32 teams × 28 modern seasons. The 1,062+ transclusion count proves the *template* is used
broadly; it does **not** prove that every team-season article has a Staff section, nor that the OC
field is populated wherever the template appears. `[GAP]` **Per-team-per-season population rate.**
A build must measure that first and quarantine misses rather than assume coverage — the pattern
`rankings_quarantine` already establishes in this codebase.

**A look-ahead hazard named in the template itself.** It is `NFL final staff` — the staff at the
*end* of the season. For a preseason ranking input you want the coordinator hired in the offseason
before the season. In any season with a mid-year firing, the "final" name is post-cutoff information,
and Wikipedia carries no `as_of_date` on it. `CLAUDE.md`'s schema principle that "every time-sensitive
record carries an `as_of_date`" cannot be satisfied from the rendered article alone. Two honest
options, both unattempted and both uncosted here: restrict to team-seasons with no in-season change
(detectable, since in-season changes are usually noted in prose), or reconstruct the start-of-season
name from article revision history via the API. `[GAP]` The cost and reliability of the revision-
history route.

`[GAP]` No other permissively-licensed coordinator dataset was found. Searching surfaced only
per-person biography articles and **"List of current NFL offensive coordinators"** / **"List of
current NFL defensive coordinators"** (`[VERIFIED]` these pages exist via API search) — current
season only, no history.

---

## 4. Route participation

### 4.1 The record is still accurate: nflverse has no routes-run column

`[VERIFIED]`, from nflreadr's own reference and dictionary pages:

- `load_participation` covers **2016 onward**. "Participation data prior to 2023 is from NFL NGS.
  Participation data from 2023 onwards is courtesy of FTN." The NGS feed "died during the 2023
  season." FTN data is "provided **after all post-season games are completed**. It does not update
  during the season!"
- Licence **CC-BY-SA 4.0**, attribution "FTN Data via nflverse" (2023+) or "NFL NextGenStats via
  nflverse" (2022 and earlier).
- `[SECONDARY]`/`[SNIPPET]` 2023 and 2024 are now present; 2025 will not exist until after the 2025
  season concludes. Sourced from the nflverse maintainer's own post and the changelog as reported in
  search results; I did not render either page. **Effective usable window today: 2016–2024, nine
  seasons.**

**The `route` field is not what its name implies.** Dictionary text, verbatim `[VERIFIED]`:

> **route:** "A string indicating the route the primary receiver on a play took. Has the following
> possible values: 'CORNER', 'DEEP OUT', 'GO', 'HITCH/CURL', 'IN/DIG', 'POST', 'QUICK OUT', 'SCREEN',
> 'SHALLOW CROSS/DRAG', 'SLANT', 'SWING', 'TEXAS/ANGLE', 'WHEEL'."

One value per play, describing the *targeted* receiver only. It cannot tell you which players ran
routes. What can be used is:

> **offense_players:** "A list of every offensive player on the field for the play, by gsis_id"

`[VERIFIED]` `load_ftn_charting` (2022+) is play-level formation/personnel/pressure charting. This
was already checked column-by-column in `docs/research/tier1-usage-source-inventory-2026-07.md` §2
and found to carry **no per-player route field**; nothing in nflreadr's current documentation
contradicts that. `[GAP]` Whether the FTN-sourced participation years (2023+) populate `route` at all,
or with the same vocabulary as the NGS years — the dictionary describes one schema and the source
changed underneath it.

### 4.2 The defensible proxy, stated so it can be flagged as one

```
pass_play_participation_rate(player, team, season)
    = (# team dropback plays where player's gsis_id ∈ offense_players)
    / (total team dropback plays)
```

**What it actually measures: share of team pass plays spent on the field. Not routes run.** The two
diverge for precisely the population the feature exists to separate — a running back kept in for pass
protection and a tight end who chips and stays in are both on the field and neither ran a route. The
bias is therefore **systematic and position-correlated, not noise**: it overstates route
participation for blocking-heavy RBs and inline TEs, and is close to exact for outside receivers.

Conditions any use must carry, per this project's own proxy rule:

1. Name the column `route_participation_proxy`, never `route_participation_rate`.
2. Record the bias direction with it, not just the word "proxy".
3. Window is **2016–2024**. Nine seasons — and a source change at 2023 (NGS → FTN) is a regime break
   *inside* the window, so a factor built across it is not measuring one instrument.
4. Derivation cost is real: `offense_players` is a list column requiring an explode-and-join against
   player identity, per play, across nine seasons. It is a build task, not a column read.

**A cheaper substitute already in the database.** `snap_counts.offense_pct` covers **2013–2025** and
is already ingested (`docs/research/tier1-usage-source-inventory-2026-07.md` §1, 324,611 rows). It is
coarser — all offensive snaps, not pass snaps — but it is longer, present today, and answers most of
what registry #17 says the feature is for ("distinguishes starters from rotational"). Whether pass-
play participation beats total snap share for that specific question is an empirical test, and it is
cheap to run once, before committing to the participation derivation.

### 4.3 Direct route data exists commercially and is blocked for automated collection

**Fantasy Points Data Suite.** `[SECONDARY]` (search excerpt; the product page at
`/nfl/data-suite` returned 404) — advertises routes and break depths for every eligible player on
every pass play, plus routes run by alignment (wide / slot / inline / backfield). That is exactly the
missing input, in the shape the registry wants.

`[VERIFIED]` Its Terms & Conditions prohibit automated collection outright:

> "except as may be the result of standard search engine or Internet browser usage, use, launch,
> develop or distribute any automated system, including without limitation, any spider, robot, cheat
> utility, scraper, or offline reader"

> "systematically retrieve data or other content from the Site to create or compile, directly or
> indirectly, a collection, compilation, database, or directory"

> "engaging in any data mining, data harvesting, data extracting or any other similar activity in
> relation to the Site"

**Same regime as FantasyPros: manual, human-paced, in-browser use only. No harvesting, no bulk
collection, no scripted export.** Recorded as blocked for automation and stopped.

`[GAP]` **Price.** `/plans` renders its prices client-side and returned only "Loading Subscription
Plans"; `/why-subscribe` names "Premium" and "Standard" without figures; `/nfl/data-suite` 404'd.
`[SNIPPET]` The only structural fact retrievable: NFL Data Suite subscriptions run **April 1 to
March 31** with auto-renewal on April 1. I am not going to state a dollar figure I did not fetch —
the founder should read it off the page in a browser, which their terms permit and which takes a
minute.

### 4.4 A live lead that belongs to an existing thread, not this one

`docs/handoffs/054-ftn-and-sleeper-harvest.md` records that **the founder already holds an FTN
subscription and nobody has audited what it provides.** FTN is the upstream supplier of nflverse's
2023+ participation data. Whether his existing subscription already grants per-player route data, and
whether it grants API or bulk export at all, is precisely thread 054's question. **I have not
duplicated it here.** If route participation is pursued, 054 is the cheaper first move than any new
purchase.

---

## 5. Recommendation — pursue coaching staff history first

Not Vegas odds. Three reasons, in order of weight.

**1. Vegas game lines are not a sourcing problem, so there is nothing to "pursue."** They already sit
inside `nflreadpy`, a library this repo imports today, at $0, under the one licence in this project
that permits display. The remaining work is ingestion and a derived column, not acquisition — and
ingestion is out of my scope. The only genuinely missing odds *product* is season win totals, and
`docs/test-registry.md` rates that Tier 0, edge **Low**. Spending the next block of effort there
would be buying the cheapest thing, not the most valuable one.

**2. Coaching staff is the one where a real block has just been legitimately bypassed — not routed
around.** PFR is 403 and stays 403; I did not attempt to circumvent it. Wikipedia's API is a
different, sanctioned source with a *better* licence than anything else this project holds, covering
coordinators from the 1940s to 2024. It makes `coach_id` — a first-class dimension `CLAUDE.md` §4
reserved and which is currently unusable — usable for the first time, and it ungates two registry
items rated edge **High** (#29 coordinator continuity, #30 first-time play-callers). Nothing else in
this document unblocks a High-rated item.

**3. Route participation is last, and its real unlock is a subscription the founder already owns.**
The only free path is a proxy with a known position-correlated bias over nine seasons containing an
instrument change; a cheaper substitute (`snap_counts.offense_pct`, 2013–2025) is already in the
database and should be tested against it before the derivation is built. The direct source is blocked
for automation at any price. Thread 054 is the right next step, not new sourcing.

### The founder decisions that need a number

| Want | Cost | Fetch | Display to a second person |
|---|---|---|---|
| Game spreads / totals / moneylines, 1999→present | **$0** | permitted | **permitted** (CC-BY-4.0, attribution) |
| Implied team totals (game level) | **$0** | derived, no source needed | as above |
| Season win totals, 1999→2026 | **$0** | permitted (robots open, no anti-automation clause) | **prohibited** (covers.com reproduction clause) |
| Point-in-time game-line snapshots, 2020-06-06→present | **$30 / month** (The Odds API 20K plan; historical requests cost 10× credits, so budget accordingly) | permitted | **permitted in-app**; raw redistribution prohibited |
| Coordinator history, ~1946→2024 | **$0** | permitted (User-Agent + rate limits) | **permitted** (CC BY-SA 4.0, attribution + share-alike) |
| Routes run, direct per-player | **`[GAP]` — not retrievable programmatically** | **prohibited for automation** | not established |

None of the $0 rows needs a credential, so none is blocked by cloud-session constraints.

---

## 6. Open gaps, listed so nobody fills them by accident

- **Whether nflverse `spread_line` / `total_line` are opening or closing lines**, and which
  sportsbook. Undocumented in the dictionary, `DATASETS.md`, and the README.
- **Which season each nflverse betting column first becomes non-null.** Measurable in one query;
  I had no shell.
- **Whether covers.com's win-total pages carry an as-of date for seasons other than 2020.** 2012 does
  not. n = 2 of 28 checked.
- **Which sportsbook covers.com's win totals come from.** Not stated on either page fetched.
- **Per-team-per-season population rate of `Template:NFL final staff`** across 32 teams × 28 modern
  seasons. Transclusion floor is 1,062; the distribution is unknown.
- **Cost and reliability of recovering start-of-season coordinators from Wikipedia revision history**
  rather than the "final staff" end-state.
- **Whether Sports Reference sells a data licence, and its price.** The page that would say so 403s.
- **Whether FTN-sourced participation years (2023+) populate `route`,** and with what vocabulary.
- **Fantasy Points Data Suite price.** Client-side rendered; not retrievable by fetch.
- **Whether the founder's existing FTN subscription includes per-player routes** — thread 054,
  deliberately not answered here.

---

*Attribution obligations for anything built on the recommended set: nflverse data is CC-BY-4.0 and
requires attribution; nflverse participation data is CC-BY-SA 4.0 and must be credited to "FTN Data
via nflverse" (2023+) or "NFL NextGenStats via nflverse" (2022 and earlier); Wikipedia text is
CC BY-SA 4.0 and requires author attribution and share-alike.*
