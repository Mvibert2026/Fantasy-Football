# Source availability audit — research / aggregation (FR-001)

**Date:** 2026-07-26 · **Role:** researcher · **Thread:** [009](../handoffs/009-research-aggregation-audit.md)
**Scope:** audit only. No feature design, no UI proposal, no recommendation about what to build.

Confidence tags, used on every cell:

| Tag | Meaning |
|---|---|
| `[VERIFIED]` | Fetched directly from the source's own page or API this session |
| `[SNIPPET]` | Seen only in a search excerpt; the underlying page did not render |
| `[SECONDARY]` | Third-party reporting only |
| `[GAP]` | Could not establish. **Never** filled with a plausible substitute |

Two things this audit deliberately keeps apart, because they have different answers for almost
every source:

- **Fetch** — may we retrieve it at all (robots.txt, ToS anti-automation clauses, auth).
- **Display / redistribute** — may we show it to a user, cache it, or put it on a screen.

A source can be freely fetchable and still be undisplayable. Several here are exactly that.

---

## 1. Sample quality — read before the table

Fifteen nominal sources are **not fifteen independent findings.** They collapse into five legal
regimes, and the useful count is the number of regimes:

| Regime | Members | Effective n |
|---|---|---|
| A · Open data, CC-BY, display permitted with attribution | nflverse | **1** |
| B · Official API with an explicit tiered licence | FantasyPros, Yahoo | **2** |
| C · ToS expressly prohibits automated access | ESPN (Disney), Underdog, PFF, FootballGuys, Establish The Run | **1 decision, 5 sites** |
| D · robots.txt permissive, ToS bars reproduction/copying | CBS, 4for4, FantasyPros' own web pages | **1 decision, 3 sites** |
| E · ToS could not be retrieved → conservative default applies | FFC, RotoWire, Fantasy Life | **1 decision, 3 sites** |

**The subscription-analyst class (PFF, 4for4, FootballGuys, ETR, Fantasy Life) is one decision unit,
not five.** All are paywalled, all bar reproduction of their output, and none publishes a
self-serve API. Auditing a sixth would not change the answer. Stating that is more useful than
reporting five separate rows that agree — and they agree for a structural reason (their product
*is* the rankings, so licensing them away is against their interest), not by coincidence.

**Non-representativeness to flag even though it points the way we expected:** the two sources this
project already uses (nflverse, MFL) came out cleanest. That is partly selection — they were
adopted *because* earlier audits found them clean. It is not evidence that the field is generally
permissive. It is the same two sources passing the same test again.

---

## 2. The table

One row per source. Every cell tagged.

| Source | Documented API / feed + endpoint | Auth · limits · cost | robots.txt (fetching) | ToS — **fetch** | ToS — **display / redistribute** | Push or pull | Granularity | Cadence · history |
|---|---|---|---|---|---|---|---|---|
| **FantasyPros — official API** | `[VERIFIED]` A public API exists and is productised at `https://www.fantasypros.com/api-data/`. `[SNIPPET]` Base URL `https://api.fantasypros.com/public/v2/json`; key request at `secure.fantasypros.com/api-keys/request`. `[GAP]` Exact endpoint paths — `api.fantasypros.com/v2/docs` returns **HTTP 403** to unauthenticated fetch. `[SECONDARY]` Endpoint families: rankings, projections, players, news, injuries | `[VERIFIED]` API key in `x-api-key` header. Three tiers: **Free $0** — "All endpoints, sample data", "Generous daily call limit", licence **"Non-production use"**; **Premium $8.99/mo** (bundled with the HOF subscription) — production keys, "Personal & non-commercial apps", "higher rate limits"; **Commercial** — custom price, "Highest rate limits & custom SLA", "Historical data & bulk access". `[GAP]` Every numeric rate limit and any row cap — the page gives only qualitative wording | `[VERIFIED]` `www.fantasypros.com/robots.txt` disallows `/ajax/`, `/nfl/ranker/`, `/api/`, `/json/`, `/xml/`; `Crawl-delay: 5`; references `/llms.txt`. `/nfl/adp/` and `/nfl/rankings/` are **not** disallowed. `[GAP]` `api.fantasypros.com/robots.txt` → HTTP 403 | `[VERIFIED]` Terms of Use (`/about/legal/`) contains **no** anti-automation clause. Checked explicitly for "automated", "robot", "spider", "scrape", "framing", "systematic downloading" — none appear in any of its 32 sections. `[VERIFIED]` `/llms.txt` grants and forbids nothing | `[VERIFIED]` **This is where it bites.** "You agree not to sell, resell, reproduce, duplicate, copy or use for any commercial purposes any portion of this site, or use of or access to this site." `[VERIFIED]` Redistribution rights are a **Commercial-tier feature only**; Premium is expressly "personal and non-commercial". `[SNIPPET]` "You may not use the API data to build a product or service that directly competes with FantasyPros" | `[VERIFIED]` Pull only. No webhook or RSS documented | `[SECONDARY]` ECR overall + positional, tiers, projections, news, injury designations | `[GAP]` Documented refresh cadence. `[VERIFIED]` Historical/bulk access is gated to the Commercial tier, i.e. **not available on Free or Premium** |
| **FantasyPros ECR via nflverse mirror** *(the incumbent path)* | `[VERIFIED]` `nflreadpy.load_ff_rankings()` → `github.com/DynastyProcess/data`. Repo alive and scraping: latest commits `Automated FP scrape` **2026-07-24 03:40 UTC**, `Automated Player ID pipeline` 2026-07-24 05:32 UTC | `[VERIFIED]` None. Free, no login, GitHub-hosted parquet | `[VERIFIED]` GitHub raw/API access; no robots barrier encountered this session | `[VERIFIED]` Repo licence **GPL-3.0**, not archived, description "An open-data fantasy football repository" | `[VERIFIED]` GPL-3.0 covers the repository. **`[GAP]` whether it can convey display rights in FantasyPros-derived numbers — a mirror cannot grant rights its operator did not hold.** This is a live legal risk, not a formality: the underlying restriction is FantasyPros' "reproduce, duplicate, copy" clause above | `[VERIFIED]` Pull | `[SECONDARY]` ECR rank, best/worst, sd, position — already in `rankings` per ADR-024 | `[VERIFIED]` Scrape ran 2026-07-24. `[SECONDARY]` History back to 2020 via `type="all"`; project record says 2020's earliest snapshot is in-season and unusable |
| **Sleeper** | `[VERIFIED]` `https://docs.sleeper.com/`. Endpoints enumerated: `/v1/user/…`, `/v1/league/{id}` (+ `/rosters`, `/users`, `/matchups/{wk}`, `/transactions/{rnd}`, brackets, `/traded_picks`), `/v1/draft/{id}` and `/v1/draft/{id}/picks`, `/v1/players/nfl`, `/v1/players/nfl/trending/{add\|drop}`, `/v1/state/nfl` | `[VERIFIED]` No auth. Read-only. Free. "stay under 1000 API calls per minute, otherwise you risk being IP-blocked". Player DB ~5 MB, cache locally | `[GAP]` `robots.txt` not fetched this pass; the API is documented and openly public, which is the operative fact | `[VERIFIED]` API is public and documented, no auth. Attribution to Sleeper is *requested* for trending data | `[VERIFIED]` **Restrictive.** ToS grants a "limited, personal, revocable, non-transferable and non-exclusive" licence for "personal and non-commercial use" and forbids "rent, lease, lend, sell, **redistribute**, sublicense, copy … or otherwise inappropriately use the Services" | `[VERIFIED]` Pull | `[VERIFIED]` **No aggregate ADP or rankings endpoint exists** — re-confirmed, unchanged. Per-draft picks are available *if you already hold the `draft_id`*; there is no draft-discovery endpoint. Trending adds/drops is the only crowd signal | `[VERIFIED]` Player DB updates daily (per their caching note). `[GAP]` Historical snapshots — none offered; trending is a rolling window |
| **ESPN** (and therefore **NFL.com** from 2026) | `[SECONDARY]` No public documented fantasy API. The commonly used `lm-api-reads.fantasy.espn.com` host is undocumented and returned **HTTP 403** even for `robots.txt` this session `[VERIFIED]` | `[GAP]` Not established — no published developer programme found | `[VERIFIED]` `www.espn.com/robots.txt` blanket-disallows `anthropic-ai`, `GPTBot`, `CCBot`, `ChatGPT-User`, `Google-Extended`, `claritybot`, `Omgilibot`, `Omgili`, `FacebookBot`, `Bytespider` (`Disallow: /` each). `ClaudeBot` / `Claude-User` are **not** listed. Catch-all block does not name `/apis/` or `/fantasy/` | `[VERIFIED]` **Blocked.** Disney Terms of Use §2.B.x: "access, monitor, copy or extract the Disney Products using a robot, spider, script, or other automated means", expressly "including … for the purposes of creating or developing any AI Tool, data mining or web scraping". Recorded as blocked; **no ESPN content page was fetched this session** | `[VERIFIED]` **Blocked.** §2.A licence is "for your personal, noncommercial use only" and expressly excludes any "use, creation, development, modification, prompting, fine-tuning, training, testing, benchmarking or validation of any artificial intelligence or machine learning tool". §3.H: "we do not allow uses of the Disney Products … that are commercial or business-related" | n/a — blocked | n/a — blocked | n/a — blocked |
| **Yahoo** | `[VERIFIED]` Yahoo Fantasy Sports API still exists; **the developer portal moved** — `developer.yahoo.com/fantasysports/guide/` now **308-redirects** to `sports.yahoo.com/developer`. `[VERIFIED]` Documented resources: game, league, team, player, transaction, user. `[SNIPPET]` A `draft_analysis` sub-resource returning `average_pick`, `average_round`, `average_cost`, `percent_drafted` exists at `/fantasy/v2/player/{player_key}/draft_analysis` and game-wide at `/fantasy/v2/game/{game_id}/players;start={n}/draft_analysis`. `[GAP]` Not confirmed from Yahoo's own docs — the resource page I tried 404'd, and the portal's own resource list did not mention it | `[VERIFIED]` **OAuth 2.0**, plus agreement to an "API Access and Use Agreement". `[VERIFIED]` "Yahoo monitors API usage … we may temporarily throttle or limit access" — no published numeric limit. `[GAP]` Numeric rate limits. Cost: `[GAP]`, no price surfaced | `[VERIFIED]` `football.fantasysports.yahoo.com/robots.txt` **explicitly disallows `ClaudeBot`, `Claude-Web`, `anthropic-ai`**, plus GPTBot, CCBot, PerplexityBot, Diffbot, cohere-ai, huggingface and others. Also disallows `/F1/`, `/*/F1/`, `/LEAGUE/`, `/DRAFTCLIENT/`. Scraping the public `/f1/draftanalysis` page is therefore **blocked for this class of agent** — recorded as blocked, not routed around | `[VERIFIED]` The **API** is the sanctioned channel and OAuth is what CLAUDE.md §10 prefers. `[VERIFIED]` Developer ToU requires attribution per the Yahoo Developer Network Attribution Policy. `[SNIPPET]` "Fantasy data provided by Yahoo Fantasy" with a link back | `[VERIFIED]` Three clauses that bite hard: **(a)** must delete Yahoo user data "not explicitly identified as being storable indefinitely" within **24 hours** of obtaining it; **(b)** may not "derive income from the use or provision of the Yahoo APIs" without written permission; **(c)** may not "Use the Yahoo APIs in a product or service that competes with products or services offered by Yahoo". Yahoo ships a fantasy draft assistant. `[GAP]` Whether aggregate ADP counts as "Yahoo user data" under (a) — this determines whether ADP snapshots may be stored at all | `[VERIFIED]` Pull | `[SNIPPET]` `average_pick`, `average_round`, `average_cost`, `percent_drafted` — real market ADP, on a very large population | `[GAP]` Cadence and historical snapshot availability |
| **CBS Sports** | `[VERIFIED]` **No public API found**, but a **server-rendered ADP page exists**: `https://www.cbssports.com/fantasy/football/draft/averages/` with format in the path (`…/averages/ppr/both/h2h/all/`). Columns: Rank, Player + team + position, Trend, **Avg Pos**, **Hi/Lo**, **Pct**. 140+ rows visible; data in the HTML, not JS-only. No CSV/export link | `[VERIFIED]` No auth to view. Free | `[VERIFIED]` `www.cbssports.com/robots.txt` blocks **GPTBot** (`Disallow: /`) only among AI agents; `ClaudeBot`/`anthropic-ai` not named. Catch-all disallows `/data/*`, `/login*`, `/user*`, `/partners`, `/component/*`, `/2/`, `/*?*sortcol=*`, `/*?*sortdir=*`. **`/fantasy/` is not disallowed** | `[VERIFIED]` robots.txt does not forbid it. `[GAP]` Any *current* general ToU — the only general Terms of Service I could locate is dated "**Updated: February 4, 2005**" and contains **no** robots/scraping/data-mining clause | `[VERIFIED]` **Blocked by that same 2005 ToS**: "Copying or storing any part of the Service is expressly prohibited without prior written permission" and "You may not resell, lease, license, assign or redistribute the Service, in whole or in part, to any third party". Storing a snapshot is copying | `[VERIFIED]` Pull | `[VERIFIED]` Overall rank, average pick, hi/lo range, percent drafted, per scoring format | `[GAP]` Update cadence — no date or sample size stated on the page. `[GAP]` Historical snapshots |
| **NFL.com** | `[VERIFIED]` **Being retired.** ESPN Press Room, 2026-07-16: "Beginning this season, the NFL will no longer operate a season-long Fantasy Football game, with ESPN serving as the official Fantasy game of the NFL." Leagues migrate to ESPN; settings and history transfer where available. `[GAP]` A stated shutdown date for the NFL.com fantasy surface — the announcement gives none | `[GAP]` | `[VERIFIED]` `www.nfl.com/robots.txt` disallows `/_ctv/`, `/_fantasy-app/`, `/_libraries/`, `/_mobile-app/`, `/_mobileview/`, `/_phs/`, `/_sponsors/`, `/account/`, `/nfl-films-beta/`, `/search/`. No AI-crawler blocks. `/api/` not named. **`/_fantasy-app/` is disallowed** — i.e. the fantasy app paths specifically | `[VERIFIED]` The fantasy path is disallowed by robots.txt, and the successor platform is ESPN, whose ToU forbids automated access. Legacy value only, as the thread anticipated | `[VERIFIED]` Inherits Disney's terms going forward | n/a | `[GAP]` | `[GAP]` Whether any historical NFL.com ADP survives migration |
| **Underdog** | `[VERIFIED]` **Domain moved**: `underdogfantasy.com` 301-redirects to `www.underdogsports.com`; legal moved to `legal.underdogsports.com`. `[GAP]` No public documented ADP/rankings API or feed found | `[GAP]` | `[VERIFIED]` `underdogsports.com/robots.txt` contains **no `Disallow` lines at all** — only a `Sitemap:` line. Confirmed on two independent fetches | `[VERIFIED]` **Blocked by ToS despite the permissive robots.txt.** §6(ix) prohibits: "scrape, access, monitor, index, frame, link, or copy any content or information on the Services by accessing the Services in an automated way, using any robot, spider, scraper, web crawler, or using any method of access other than manually accessing the publicly-available portions … through a browser". §6(x) forbids bypassing access-limiting measures. Recorded as blocked; stopped | `[VERIFIED]` Blocked — see above; copying is named in the same clause | n/a — blocked | n/a — blocked | n/a — blocked |
| **MyFantasyLeague (MFL)** | `[VERIFIED]` `https://api.myfantasyleague.com/{year}/export?TYPE=adp&JSON=1`, documented at `/{year}/api_info?STATE=details&TYPE=adp`. Parameters: `PERIOD` (ALL, RECENT, DRAFT, JUNE, JULY, AUG1, AUG15, START, MID, PLAYOFF), `FCOUNT` (8/10/12/14/16), `IS_PPR` (0/1/−1), `IS_KEEPER` (N/K/R), `IS_MOCK` (0/1/−1), `CUTOFF`, `DETAILS` | `[VERIFIED]` No auth for export. Free. Optional `APIKEY` for restricted data. **Client registration gives ~2.5× the standard rate limit**; unregistered limits are per-IP; 429 on exceed. Guidance: space requests ~1 s apart, cache (player DB updates once daily), "**Don't retry failed requests**" | `[GAP]` `robots.txt` not fetched; the export API is documented and open, which is the operative fact | `[VERIFIED]` Documented public export. Forbidden uses named: "**Harvesting league and/or user data**", disrupting service, collecting user information without permission, and calling the API via JavaScript from external domains. Aggregate ADP is not league/user data, so the ADP export sits outside that prohibition on its face | `[GAP]` **No redistribution or display clause found either way.** Not permissive, not restrictive — genuinely absent from the API notes I could retrieve. Service is "offered as is, without any guarantees" and may change or vanish without warning | `[VERIFIED]` Pull | `[VERIFIED]` Average pick, min pick, max pick, selection frequency, per-format metadata, last-update timestamp | `[VERIFIED]` `PERIOD` gives **within-season snapshots** (JUNE / JULY / AUG1 / AUG15 …) but "This option is not valid for previous seasons" — so intra-season history is *current-season only*. `DETAILS=1` (which leagues fed the number) also "only works for the current season". Past seasons are retrievable as a single whole-season number via `/{year}/` |
| **Fantasy Football Calculator (FFC)** — **UNBLOCKED 2026-07-29, founder-confirmed, see note below table** | `[SECONDARY]` Has historical ADP back to 2007 (project record, ADR-018). `[VERIFIED]` No public API docs found; `/api/` is robots-disallowed | `[GAP]` | `[VERIFIED]` **Re-confirmed, unchanged:** `robots.txt` disallows `/api/`, `/ajax/`, `/ajax-v2/`, `/import/`, `/adp/csv/`, `/draft/`, `/rate-my-team/results/`, `/rankings/custom/`. **Nuance the project record misses:** only `/adp/csv/` is disallowed — the HTML ADP pages under `/adp/<format>` are **not** in the disallow list. **Independently re-confirmed again 2026-07-29 (data-ops session)**, same result: only `/adp/csv/`, `/api/`, `/ajax/`, `/ajax-v2/`, `/import/`, `/draft/`, `/rate-my-team/results/`, `/rankings/custom/` disallowed; `/adp/<format>/<teams>-team/all/<year>` clear | `[SUPERSEDED 2026-07-29]` ~~ToS could not be retrieved... treat as blocked~~ — **the founder contacted FFC directly and reported no restrictions on use** ("we hve no blocks from FFC, we can use as needed"), recorded in `docs/pm/MEMORY.md` §4 and `docs/founder-requests/FR-023-ffc-is-unblocked-founder-confirmed-no-restrictio.md`. This is broader than D-021's one-time historical-pull authorisation — recurring use is covered. Standing conditions: private single-user use only; rate-limit and cache (one fetch/day/format); never blend `adp_source` values | `[UNBLOCKED]` — see previous cell | `[SUPERSEDED]` was blocked; ingester built 2026-07-29 (ADR-054), `src/ingest_ffc_adp.py` | `[SECONDARY]` Overall + positional ADP, by league size and scoring, with sample counts. **Now captured daily** at 10-team non-PPR/half-PPR/PPR (`adp_source` = `ffc_non_ppr_10team`/`ffc_half_ppr_10team`/`ffc_ppr_10team`), `.github/workflows/adp-snapshot.yml` | `[SECONDARY]` History to 2007 (per project record, not re-verified this pass). **Backfill not yet pulled** — FFC exposes no as-of date for past seasons, so any historical pull must be labelled `is_retrospective_aggregate=1` (ADR-054) rather than treated as a preseason snapshot |
| **PFF** | `[GAP]` No public self-serve API found. `/api/partners/` exists but is robots-disallowed and partner-gated | `[GAP]` Subscription price not verified this pass | `[VERIFIED]` `www.pff.com/robots.txt` is short and permissive: disallows only `/partners/`, `/api/partners/`, `/amember/`, `/login*`, `/logout*`, `/join`. No AI-crawler blocks | `[VERIFIED]` **Blocked.** §1.5(h) prohibits "spiders, robots, scrapers, crawlers, avatars, browser extensions, data mining tools or the like" to extract PFF Data (public search engines excepted). §1.5(i) additionally forbids using such tools "for machine learning or training of artificial intelligence models or tools". Recorded as blocked; stopped | `[VERIFIED]` **Blocked, and unusually broadly.** §1.5(f) prohibits "bulk copy and/or distribute PFF Data … for use on third-party platforms, in podcasts, or for other editorial or commercial purposes". §1.6 forbids providing PFF Data "or other derivatives or synthetic versions" as "inputs or prompts to any generative artificial intelligence tools, machine learning tools … large language or natural language processing models or cloud-based AI services" — which would also bar feeding it to this project's own assistant | n/a — blocked | n/a — blocked | n/a — blocked |
| **4for4** | `[GAP]` No public API found | `[GAP]` Subscription price not verified. Content is paywalled | `[VERIFIED]` Long Drupal-era `robots.txt`. Relevant disallows: **`/adp_draft_planner*`**, `/idp/rankings*`, `*/rankings-tabs/*`, `/reports/redraft_cheat_sheet/*`, `/full-impact/*`, `/members/`, `*.pdf`, plus most paywalled tools. General `/rankings` pages are not named | `[VERIFIED]` No explicit anti-scraping clause in the Terms of Use — checked. The ADP tool is nonetheless robots-disallowed, so the specific asset of interest is off-limits | `[VERIFIED]` **Blocked.** "The 4for4 Forecasting Model and software contains trade secrets and unique insights. You may not reverse-engineer, disassemble, reproduce or redistribute its content **or output** without the prior written consent of Pieracle Inc." plus "may not be reproduced, duplicated, copied, sold or otherwise exploited" | `[GAP]` | `[SECONDARY]` Rankings, projections, ADP tool — paywalled | `[GAP]` |
| **FootballGuys** | `[GAP]` No public API found | `[GAP]` Paywalled | `[VERIFIED]` **No `robots.txt` at all** — HTTP 404 on both `www.footballguys.com/robots.txt` and `footballguys.com/robots.txt`. Crawling therefore unrestricted *by robots* | `[VERIFIED]` **Blocked by ToS.** §13 Prohibited Uses forbids "to spam, phish, pharm, pretext, **spider, crawl, or scrape**". Recorded as blocked; stopped. A clean example of robots.txt and ToS pointing opposite ways | `[VERIFIED]` **Blocked.** §1: the site "including photographs, analysis, information, logos and all associated material, may not be reproduced, duplicated, copied, sold or otherwise exploited for any purpose that is not expressly permitted by Sportsguys" | n/a — blocked | n/a — blocked | n/a — blocked |
| **Establish The Run** | `[VERIFIED]` No API. `[VERIFIED]` An RSS feed path exists at `/feed/` **and is the one thing robots.txt disallows** | `[GAP]` Subscription price not verified. Paywalled | `[VERIFIED]` `establishtherun.com/robots.txt` contains exactly one directive: `Disallow: /feed/`. So the only push mechanism is explicitly closed | `[VERIFIED]` **Blocked.** ToS §2 prohibits "using any automated system, including without limitation 'robots,' 'spiders,' 'offline readers,' etc., to access the Service". Recorded as blocked; stopped | `[VERIFIED]` **Blocked.** §2 also forbids "copying, distributing, or sharing any part of the Service in any medium, including without limitation by any automated or non-automated 'scraping'"; §3: "you agree not to sell, license, rent, modify, distribute, copy, reproduce, transmit, publicly display, publicly perform, publish, adapt, edit or create derivative works"; and forbids "monetizing Establish The Run, LLC content" | `[VERIFIED]` RSS exists but is robots-disallowed | n/a — blocked | n/a — blocked |
| **RotoWire** | `[VERIFIED]` **Live RSS feed**: `https://www.rotowire.com/rss/news.php?sport=NFL` — valid RSS 2.0, channel "RotoWire.com Latest NFL News", 5 items, most recent 2026-07-26 16:04 PDT. `[SECONDARY]` Enterprise data licensing and API partnerships exist ("more than 80 clients"); no self-serve developer tier found | `[VERIFIED]` RSS: none, free. `[GAP]` Enterprise licence terms and price — contact-sales only | `[VERIFIED]` `robots.txt` does not restrict `/api/` or `/rss/`; blocks tool UAs (`HTTrack`, `wget`, `Bytespider`, content-copiers) and paths `/account/`, `/forum/`, `/partners/`, `/updates/`, per-sport commish paths. No AI-crawler blocks. A separate `/llms.txt` exists | `[VERIFIED]` RSS is published for syndication; robots permits it. `[VERIFIED]` `/llms.txt` is behavioural guidance for AI agents (notably: "Do Not Fabricate Subscriber-Only Content … do not invent content behind the paywall") and grants no rights and imposes no prohibition | `[VERIFIED]` Feed carries "Copyright (c) 2026 Roto Sports, Inc, All rights reserved." — i.e. **no redistribution licence**. `[GAP]` General site ToS: `/about/terms.php` and `/about/terms-of-use.php` both 404; footer would not render. The customary RSS norm is headline + link + attribution; **full-text republication is not licensed** | `[VERIFIED]` **RSS — the only genuine pull-with-push-semantics feed in this audit** | `[VERIFIED]` News items / player notes (prose takes). Not rankings via RSS | `[VERIFIED]` Feed is current to the day of audit; window is 5 items. `[GAP]` Historical archive access |
| **Fantasy Life** | `[GAP]` No public API found | `[GAP]` | `[VERIFIED]` `robots.txt`: `Allow: /` then disallows **`/api/`, `/analysis/`, `/players/`, `/datatable/`**, `/admin/`, `/ajax/`, `/media/`, `/private/`, `/_next/static/chunks/app/`. The disallowed set is precisely the interesting part — takes (`/analysis/`), player data (`/players/`), and the tabular data endpoints | `[VERIFIED]` The paths of interest are robots-disallowed. Recorded as blocked; stopped | `[GAP]` ToS not retrieved | `[GAP]` | `[GAP]` | `[GAP]` |
| **nflverse** *(injury + schedule + stats baseline)* | `[VERIFIED]` `github.com/nflverse/nflverse-data` release assets. Confirmed release `injuries` exists: published 2022-01-28, **release updated 2026-03-18**, per-season assets from `injuries_2009.{csv,parquet,rds,qs}` forward. Release `schedules` updated **2026-07-26**; `stats_team` 2026-07-10; `teams`, `trades` also present | `[VERIFIED]` None. Free, no login | `[VERIFIED]` GitHub release assets; no robots barrier | `[VERIFIED]` Repo not archived, actively pushed (2026-07-01) | `[VERIFIED]` **Licence CC-BY-4.0 — display and redistribution permitted with attribution.** The only source in this audit where that is true. (CLAUDE.md §5 notes the FTN charting subset is CC-BY-SA; that subset is not what this row covers) | `[VERIFIED]` Pull, versioned release assets | `[VERIFIED]` Official NFL injury-report designations by season/week, back to 2009; schedules; team stats. **Not** rankings, not ADP, not takes | `[VERIFIED]` `injuries` last touched 2026-03-18 (offseason); `schedules` same-day. Full per-season history retained as separate assets — genuine historical snapshots |
| **Beat-reporter / social feeds** | `[VERIFIED]` The only license-clean, currently-verified feed of "what happened to a player" is nflverse `injuries` (row above) — official designations, not takes. `[VERIFIED]` RotoWire RSS is live for prose notes. `[GAP]` X/Twitter API tier, price, and terms — **not verified this pass; I am not going to state a number I did not fetch.** `[VERIFIED]` ETR `/feed/` robots-disallowed; Fantasy Life `/analysis/` robots-disallowed | see rows above | see rows above | see rows above | `[VERIFIED]` **Zero audited sources grant a licence to display third-party prose takes.** Every prose source found — RotoWire, ETR, 4for4, FootballGuys, PFF, ESPN — bars reproduction, in terms, in writing | `[VERIFIED]` RSS is the only push-shaped option, and two of the three RSS paths found are robots-disallowed | prose notes / official designations | see rows above |

---

## 3. What changed since the last audit — the highest-value findings

The thread asked for this specifically. Five things moved; two of them change what is possible.

**1. FantasyPros now runs a tiered public API, and "redistribution rights" is a named tier
feature.** `[VERIFIED]` Free = non-production, sample data. Premium = $8.99/mo, "personal &
non-commercial apps", production keys across rankings/projections/players/news/injuries.
Commercial = redistribution rights, historical and bulk access, custom price. This is **not** the
same object as D-000, which evaluated the *site subscription* (~$72/yr) and its 10-row API cap.
The consequence is clean and unpleasant: **the licence that permits displaying FantasyPros ECR to
anyone other than the founder is the Commercial tier, and its price is not public.** Private
single-user use is fine on the cheap paths; a public product is a sales conversation.

**2. Thread 005's stated reason for not scraping FantasyPros does not survive checking — but its
conclusion gets stronger, not weaker.** `[VERIFIED]` The Terms of Use contain no anti-automation
clause; I checked all 32 sections for "automated", "robot", "spider", "scrape", "framing" and
"systematic downloading" and none appear. The binding clause is instead *"You agree not to sell,
resell, reproduce, duplicate, copy or use for any commercial purposes any portion of this site."*
That restricts **reproduction and display**, which is the FR-001 half that matters, rather than
retrieval, which is the half thread 005 argued about. Do not correct this into "so we may scrape" —
the risk simply sits on the screen, not on the fetch.

**3. NFL Fantasy is being shut down and ESPN is the NFL's official fantasy game from this season.**
`[VERIFIED]` from ESPN Press Room, dated 2026-07-16: *"Beginning this season, the NFL will no longer
operate a season-long Fantasy Football game, with ESPN serving as the official Fantasy game of the
NFL."* The audit's practical consequence: NFL.com fantasy data does not merely lose value, it
**inherits Disney's Terms of Use**, which are the most restrictive in this entire audit — automated
access, commercial use, and AI use are each prohibited by name. Two candidate sources collapsed
into one hard block.

**4. Yahoo's developer surface moved and its fantasy host now blocks Claude agents by name.**
`[VERIFIED]` `developer.yahoo.com/fantasysports/guide/` → 308 → `sports.yahoo.com/developer`.
`[VERIFIED]` `football.fantasysports.yahoo.com/robots.txt` disallows `ClaudeBot`, `Claude-Web` and
`anthropic-ai` outright, so the public ADP page is off-limits to scraping by this class of agent —
recorded as blocked, not worked around. The OAuth API remains the sanctioned path and is the option
CLAUDE.md §10 prefers, but its ToU carries a **24-hour data-deletion requirement** and a
**no-competing-product clause**, and Yahoo ships a draft assistant. `[GAP]` whether aggregate ADP
counts as "Yahoo user data" under the deletion rule — that single unresolved question decides
whether Yahoo ADP snapshots can be stored at all, which is the entire point of storing them.

**5. Two smaller corrections to the project's own record.**
- `[VERIFIED]` **FFC's block is narrower than we have been saying.** Only `/adp/csv/` is disallowed;
  the HTML ADP pages at `/adp/<format>` are not in the disallow list. The blocker is now purely
  ToS — and FFC's ToS could not be retrieved (`/terms` 404s, the footer-linked
  `/terms-of-service` renders navigation only). So FFC stays blocked, but for a different and
  narrower reason than the record states, and the unblock path is unchanged: ask them.
- `[VERIFIED]` **A CBS ADP page exists that no prior audit catalogued** — server-rendered, 140+
  players, average pick + hi/lo + percent drafted, format-selectable by URL, and *not*
  robots-disallowed. It fails anyway, on a 2005-vintage ToS clause: "Copying or storing any part of
  the Service is expressly prohibited without prior written permission." Storing a dated snapshot is
  copying. Worth recording as *checked and rejected on ToS* rather than leaving it to be
  rediscovered.

**Also worth flagging to Data Ops, not a change but a live inconsistency:** `[VERIFIED]` MFL's own
API notes say "**Don't retry failed requests**", and `src/ingest_mfl_adp.py` retries on HTTP 429
with exponential backoff. The backoff is considerate in spirit and contrary to their written
guidance in letter. Separately, MFL offers **~2.5× higher rate limits to clients that register a
User-Agent** via their API Client Registration page, and this project has not registered — free
headroom, currently unclaimed.

---

## 4. Genuinely viable today

Three, and the honest ranking is by *licence clarity*, not by data quality.

**1. nflverse (`nflverse-data`, CC-BY-4.0).** `[VERIFIED]` The only source in the audit that
affirmatively permits display and redistribution, subject to attribution. Actively maintained
(`schedules` updated the day of this audit). Covers official injury designations back to 2009,
schedules, team stats. It contains **no rankings, no ADP, and no takes** — so it cannot carry FR-001
on its own, but anything it does carry can be shown without a licensing argument.

**2. MyFantasyLeague ADP.** `[VERIFIED]` Free, documented endpoint, no login, already ingested under
`adp_source='mfl_proxy'`, and the only *market* ADP in the audit that is both fetchable and not
contradicted by a written display prohibition — though "not prohibited" is `[GAP]`, not permission.
Its weakness is sample, not law: `totalDrafts` was 50 at last pull, per-player `draftsSelectedIn`
5–58, drawn from MFL hobbyists. Usable if and only if n and format metadata travel with the number.

**3. FantasyPros ECR — but you must pick a lane.** `[VERIFIED]` The existing DynastyProcess mirror
path is alive (FP scrape 2026-07-24) and costs nothing to fetch. Its problem is that a mirror cannot
grant display rights its operator never held, so *fetching* is settled and *displaying* is not. The
licence-clean route to the same numbers is the FantasyPros API Premium tier at $8.99/mo, which
authorises personal, non-commercial use — sufficient for a single-user private product, insufficient
the moment anyone else sees the screen. The founder's existing D-000 route (logged-in CSV export) has
the same shape: sanctioned retrieval, no display licence.

**Honourable mention, not a fourth:** RotoWire's RSS feed is verified live and is the only push-shaped
feed in the audit. It is `All rights reserved`, so it supports headline + link + attribution and
nothing more.

---

## 5. What a minimum viable comparison view could honestly show

Stated as a data-availability envelope, not a design. Using **only** the three sources above, a
per-player row can honestly carry:

| Column | Source | Honest caveat it must carry |
|---|---|---|
| Our rank / VBD | own pipeline | already governed by D-002/D-003 |
| FantasyPros ECR rank, plus best/worst spread and sd | FantasyPros (mirror for private use; API Premium for a licensed path) | one expert-consensus source, not a market; **not displayable to third parties under any tier below Commercial** |
| MFL proxy ADP: average pick, min, max | MFL export | `n` drafts behind the number, and the format filter used. Never labelled "ADP" without the `mfl_proxy` qualifier |
| Official injury designation, with `as_of_date` | nflverse `injuries` | CC-BY attribution; designation, not prognosis |

That is **two independent opinions plus one crowd-behaviour proxy plus one factual status field.**
It is a comparison view, which is the direction D-005's rigorous default already points, and it
cannot be turned into a blended consensus without inventing weights across sources of very
different quality — the same identifiability problem as D-001.

**The half of FR-001 that cannot be delivered at all, and should be said plainly rather than
designed around:** the "takes" half. `[VERIFIED]` Every prose source audited — RotoWire, ETR, 4for4,
FootballGuys, PFF, ESPN/Disney — prohibits reproduction of its content in writing. There is no
licensed way to show another analyst's opinion inside this product today. The available substitutes
are (a) headline + link + source name via RSS, which is customary practice and not a licence, and
(b) the official injury designations from nflverse, which are facts rather than takes. If the founder
wants third-party takes on a screen, that is a licensing purchase, not an engineering task.

---

## 6. Explicitly blocked — recorded and stopped, not routed around

Per the researcher standing rule. Each of these was abandoned at the point of discovering the block;
no data page behind any of them was fetched.

| Source | Blocked by | Mechanism |
|---|---|---|
| ESPN | ToS (Disney §2.B.x) + robots.txt (`anthropic-ai`) | Automated access, AI use, and commercial use each prohibited by name |
| Underdog | ToS §6(ix) | Explicit scrape/robot/crawler prohibition, despite a robots.txt with no rules |
| PFF | ToS §1.5(h)(i), §1.6 | Scraping, ML/AI use, and passing data to LLMs all prohibited |
| FootballGuys | ToS §13 | "spider, crawl, or scrape" — while having no robots.txt at all |
| Establish The Run | ToS §2/§3 + robots.txt `/feed/` | Automated access and copying prohibited; the RSS feed is the disallowed path |
| Yahoo (public web ADP page) | robots.txt | `ClaudeBot`, `Claude-Web`, `anthropic-ai` disallowed. The OAuth API is a separate, sanctioned channel |
| Fantasy Life | robots.txt | `/analysis/`, `/players/`, `/api/`, `/datatable/` disallowed |
| CBS | ToS (2005) | robots.txt permits the fetch; ToS prohibits copying or storing any part of the Service |
| FFC | ToS unretrievable → conservative default | Only `/adp/csv/` is robots-disallowed; ToS pages 404 or render navigation only |
| `api.fantasypros.com/v2/docs` | HTTP 403 | Endpoint list unobtainable without a key. Recorded as `[GAP]` |
| `lm-api-reads.fantasy.espn.com` | HTTP 403 on `robots.txt` | Undocumented host; also covered by Disney ToU |

---

## 7. Open gaps, listed so nobody fills them by accident

- FantasyPros API: every numeric rate limit, any row cap per tier, exact endpoint paths, and the
  Commercial tier price. Docs host 403s without a key.
- FantasyPros HOF annual price. `[VERIFIED]` $8.99/mo is what the page displays; whether the ~$72/yr
  figure in `CURRENT-STATE.md` is the annual-billing equivalent is **not** established.
- Yahoo: numeric rate limits; cost, if any; and whether aggregate ADP falls under the 24-hour
  user-data deletion rule.
- Yahoo `draft_analysis`: exists per third-party wrappers and one search excerpt; **not** confirmed
  from Yahoo's own current documentation.
- FFC: terms of service, in any retrievable form.
- RotoWire: general site terms; enterprise licence terms and price.
- CBS: any terms of use more recent than 2005; the ADP page's sample size and refresh cadence.
- Fantasy Life: terms of use.
- Subscription prices for PFF, 4for4, FootballGuys, ETR — not checked, because all four are blocked
  on redistribution regardless of price, which makes the price uninteresting.
- X/Twitter API tier, price, and terms for beat-reporter feeds. Not attempted this pass.
- Whether any historical NFL.com ADP survives the ESPN migration.

---

*Attribution note for anything built on the viable set: nflverse data is CC-BY-4.0 and requires
attribution; Sleeper requests attribution for trending data; Yahoo requires "Fantasy data provided
by Yahoo Fantasy" with a link back if that path is ever taken.*
