# Connecting to Yahoo and ESPN leagues — is the API path actually closed?

**Date:** 2026-07-30 · **Role:** researcher · **Answers:** `docs/founder-requests/FR-062-yahoo-league-connection-if-no-api-access-what-ar.md`

**Scope: research only.** Nothing was built. No OAuth app was registered, no token was obtained, no
Yahoo or ESPN host was fetched, no credential of any kind was handled.

Confidence tags, on every factual claim:

| Tag | Meaning |
|---|---|
| `[VERIFIED]` | I fetched the page/file this session and read it |
| `[SNIPPET]` | Seen only in a search excerpt or the search tool's synthesis; the page did not render for me |
| `[SECONDARY]` | Third-party reporting or third-party documentation only |
| `[GAP]` | Could not establish. **Never** filled with a plausible substitute |
| `[ANALYSIS]` | My reasoning over tagged facts, labelled so it is never mistaken for a fetched claim |

---

## 0. The answer, first

**The founder's question assumes the API might be unavailable. That assumption is mostly wrong, and
the parts of it that are right are not the parts he expected.**

**1. Yahoo's Fantasy Sports API exists, is live, and self-serve app registration appears to be
open.** `[VERIFIED]` Five independent third-party SDKs — Python (`yfpy` v17.0.0, released
2025-09-14), Python (`yahoo_fantasy_api`), Python (`yahoofantasy`), Node (`yahoo-fantasy-sports-api`),
R (`YFAR`) — all document the same registration path: log into the Yahoo account that holds your
leagues, go to `https://developer.yahoo.com/apps/create/`, pick **Installed Application**, set a
redirect URI of `https://localhost:<port>`, tick **Fantasy Sports → Read**, and the page immediately
shows a Client ID and Client Secret. Concrete steps in §2. **He should stop worrying about this and
spend five minutes testing it** (§2.4 gives the exact test, which also validates against data this
repo already holds).

**2. The one genuine ambiguity is which door he walks through, and it is worth naming precisely.**
There are two Yahoo surfaces and they behave differently. `[SNIPPET]` The **Yahoo Sports Developer
Portal** (`sports.yahoo.com/developer/`) describes a gated flow — "provide information about your
organization, your product, and use case(s)", "Yahoo will review your application and reach out with
any follow-up questions. If you're approved, we'll follow up with next steps." `[SECONDARY]` The
**self-serve app creator** (`developer.yahoo.com/apps/create/`) hands over credentials immediately
with no review, which is what every SDK instructs. `[VERIFIED — prior audit]` The old fantasy
developer *guide* at `developer.yahoo.com/fantasysports/guide/` now 308-redirects into the gated
portal. `[GAP]` **Whether a brand-new self-serve app still returns 200s against the Fantasy Sports
API in 2026, or now needs portal approval, is the single decisive unknown in this document.** It is
also the cheapest to close: it is one app registration and one HTTP call.

**3. Documentation degraded; the API did not.** `[VERIFIED]` An unofficial mirror at
`yahoofantasysportsapidocs.readthedocs.io` describes itself as "a copy of the archived documentation"
from Yahoo's original guide, "no longer maintained online despite the REST API remaining active."
`[ANALYSIS]` This is almost certainly the source of the founder's worry — the docs vanishing looks
identical, from outside, to the API being withdrawn. It is not the same thing.

**4. What it reaches is more than expected, and it includes the thing this project has been typing in
by hand.** `[SECONDARY]` `league/{key}/settings` returns `stat_categories`, `stat_modifiers`,
`roster_positions`, `num_playoff_teams`, `playoff_start_week`, `uses_playoff_reseeding`, `max_teams`,
`draft_type` — and `yfpy`'s data model carries a `Stat.bonuses` field backed by a `Bonus` class with
exactly two attributes, **`points` and `target`**. `[ANALYSIS]` That is the shape of a yardage-bonus
threshold. **If it populates, Westwood's stacking bonuses — the league's distinguishing feature, and
currently transcribed from a screenshot — are readable from Yahoo's own source of truth**, and
FR-012 (two unconfirmed leagues) closes in one call. That is the highest concrete payoff here and it
has nothing to do with drafting.

**5. Live draft state: probably yes for reading, definitely no for picking — and the "yes" rests on
one source.** `[VERIFIED]` The `yahoo_fantasy_api` docstring says, verbatim: *"If this is called
during the draft this includes the players that have been drafted thus far. For auction style drafts,
it does not include the player currently being nominated."* `[ANALYSIS]` That specificity reads like
observed behaviour, not aspiration. But **n = 1**: no second wrapper mentions in-progress drafts, the
Node wrapper's docs show only a completed `"draft_status": "postdraft"` example, and Yahoo's own docs
are offline. `[GAP]` Polling latency, and whether Yahoo throttles a client polling every few seconds
for three hours. `[SECONDARY]` **You cannot make a pick through the API** — roster transactions are
POSTable, draft picks are not. §3.3 says how to settle the read question for free in a mock draft.

**6. ESPN is a different answer and it is a clean no.** `[SECONDARY]` No public API, no developer
programme, no OAuth. The only working route is the undocumented `lm-api-reads.fantasy.espn.com` host
authenticated with `espn_s2` and `SWID` cookies copied by hand out of a logged-in browser —
`[VERIFIED]` ffscrapr's own vignette says of obtaining them programmatically: *"This cannot be done
programmatically at this time."* `[SECONDARY]` A maintainer discussion records that ESPN "introduced
additional recapcha authentication so now it's impossible to get access to private leagues using the
userid and pass." `[VERIFIED — prior audit]` And Disney's Terms of Use §2.B.x prohibits accessing the
products "using a robot, spider, script, or other automated means", expressly "including … for the
purposes of creating or developing any AI Tool". **So on ESPN the only mechanism that works is the
one the terms forbid by name.** That is the honest answer, and it does not improve with effort.

**7. The username-and-password fallback is not the fallback he thinks it is.** Not because of
squeamishness — because of what it buys. `[ANALYSIS]` On Yahoo it buys nothing OAuth doesn't already
give, while adding a stored password, a brittle login flow, and a terms problem. On ESPN it is
reportedly blocked by recaptcha anyway, so the honest cost is "build a browser automation, maintain
it, and still fail on draft night." Full costing in §5, with the terms clause quoted as far as this
session's constraints allowed.

**8. The clause that actually constrains this product is not about passwords at all. It is
retention.** `[VERIFIED — prior audit, not re-verified]` Yahoo's developer terms require deletion of
Yahoo user data "not explicitly identified as being storable indefinitely" within **24 hours**.
`[SNIPPET]` The storable-indefinitely list is reported to be **GUID and authenticated token value
only** — everything else must be re-requested each time. `[ANALYSIS]` If that holds, a Yahoo-connected
league feature must be **fetch-on-demand and discard**, not "ingest my league into `nfl.db`." That is
compatible with a draft-day assistant. It is not compatible with the project's normal habits. And
`[VERIFIED — prior audit]` the no-competing-product clause plus a publicly-deployed draft assistant
(`CURRENT-STATE.md`: the app is live on the open internet) is a founder-and-possibly-lawyer question,
not an agent one. §6 separates fetching from retaining from displaying, because they have three
different answers.

**9. One premise in the request is contradicted inside the repo, and it changes who this affects.**
FR-062 states "All three of his leagues are on Yahoo or ESPN." `[VERIFIED]` `FR-052` says the
opposite in the founder's own correction: *"the third entry in that dropdown is not one of his three
leagues — ignore it. **Not all three leagues are Yahoo.** … **His third league remains
uncaptured**."* `[ANALYSIS]` So the confirmed inventory is **two Yahoo leagues** (Westwood 154693,
Ethan's Expert 834236) and **one league of unknown platform**. That matters here because the answer
is entirely platform-dependent: `[VERIFIED — prior audit]` if the third is on **Sleeper**, its API is
public, documented at `docs.sleeper.com`, **needs no auth at all**, and exposes
`/v1/league/{id}` + `/rosters` + `/users` + `/draft/{id}/picks` — a strictly easier problem than
either platform in this document. Recorded rather than resolved; establishing the third league's
platform is a one-question ask of the founder and is a prerequisite to scoping any of this.
**Also flagged:** FR-052's own filename slug ("third-league-identified-as-yahoo…") contradicts its
corrected body. A future reader skimming filenames will get this wrong.

---

## 1. Access constraints — what capped the confidence of everything below

| Host | Status this session | Consequence |
|---|---|---|
| Any `*.yahoo.com` host | **Not attempted.** Dispatch instruction: do not fetch Yahoo hosts. Consistent with the standing recorded block (`docs/research/source-audit-2026-07.md` §6: `football.fantasysports.yahoo.com` disallows `ClaudeBot`, `Claude-Web`, `anthropic-ai`) | **No claim in this document about Yahoo's own pages is `[VERIFIED]`.** The registration flow, the portal's approval language, and the ToS clause text are all `[SNIPPET]` or `[SECONDARY]` |
| Any ESPN / Disney host | **Not attempted**, same instruction and the same recorded block | ESPN capability claims are `[SECONDARY]` from community libraries only |
| `support.fantasypros.com` | `[VERIFIED]` **HTTP 403** on two separate articles | Unretrieved. Identical to the prior audit's result. **No Bash tool in this session**, so I could not run the proxy status check `docs/environment.md` describes and cannot say whether the 403 was origin-side or proxy-side. Recorded as unretrieved, **not** as blocked |
| `web.archive.org` | `[VERIFIED]` The fetch tool refused outright: "Claude Code is unable to fetch from web.archive.org" | The obvious route to a Yahoo ToS mirror is closed. Recorded, not routed around |
| `reddit.com`, `stackoverflow.com` | `[VERIFIED]` Search tool refused both domains by name | The two best places to find a developer saying "I tried this last week and it worked/didn't" are unavailable. **This is the largest single hole in §2's freshness evidence** |
| `github.com`, `raw.githubusercontent.com`, `pypi.org`, `rdrr.io`, `readthedocs.io`, `y-fantasy-node-docs.vercel.app`, `ffscrapr.ffverse.com` | `[VERIFIED]` Fetched successfully | These are the entire evidentiary backbone of this document |

**Stated plainly: this is an audit of Yahoo's API conducted without reading a single word Yahoo
wrote.** Everything below is third parties describing Yahoo's surface, plus search snippets. Where
that matters most — the approval question, the ToS clause — I say so at the claim.

---

## 2. Q1 + Q2 — Is the Yahoo API available, and what does registration actually require?

### 2.1 The evidence that it is open

`[VERIFIED]` `yfpy` (the most-used Python wrapper) shipped **v17.0.0 on 2025-09-14** and its README
still carries live registration instructions. `[SNIPPET]` The API is described as powering "real-time
fantasy data across Football, Baseball, Basketball, and Hockey", "the same fantasy experiences used by
millions of fans each season". `[VERIFIED]` The unofficial docs mirror exists precisely because the
REST API outlived its documentation.

`[ANALYSIS]` A wrapper ecosystem this alive, maintained into late 2025, is strong circumstantial
evidence the API works. It is **not** evidence that a *newly registered* app in 2026 gets access —
every one of those maintainers registered years ago. That distinction is the whole of §2.3.

### 2.2 The concrete steps

`[VERIFIED]` from `yfpy`'s README (fetched from GitHub), corroborated `[VERIFIED]` by `yahoofantasy`'s
PyPI page and `[SNIPPET]` by search:

1. **Log in to the Yahoo account that holds the leagues.** `[VERIFIED]` yfpy: *"Log in to a Yahoo
   account with access to whatever fantasy leagues from which you wish to retrieve data."* For the
   founder that is the account holding Westwood (154693) and Ethan's Expert (834236).
2. **Go to `https://developer.yahoo.com/apps/create/`.**
3. **Application Name:** anything.
4. **Application Type:** `[VERIFIED]` **"Installed Application"** — yfpy names this explicitly; a
   search snippet independently repeats it. This is the choice that matters; picking "Web
   Application" changes the redirect handling.
5. **Redirect URI:** `[VERIFIED]` yfpy says `https://localhost:8080`; `[VERIFIED]` `yahoofantasy` says
   *"Set up your Yahoo application to have a callback/redirect URI of `https://localhost:8000`"* and
   notes the port is customisable. `[ANALYSIS]` Both are HTTPS + localhost — treat HTTPS as required
   and the port as free. `[SNIPPET]` `oob` (out-of-band, manual code paste) is described as available
   for testing; **not corroborated by either SDK**, so do not rely on it.
6. **API Permissions:** `[SNIPPET]` tick **Fantasy Sports**, then in the accordion that opens
   underneath it, leave **Read** selected. Read is sufficient for everything in §3 except roster
   writes.
7. **Create App.** `[VERIFIED]` yfpy: the app page then displays *"a 'Client ID' and a 'Client
   Secret'"*.
8. **First run:** `[VERIFIED]` yfpy: *"a browser window will open up asking you to allow your app to
   access your Yahoo fantasy sports data. You MUST hit allow, and then copy the verification code that
   pops up into the command line prompt."*

**Cost:** `[GAP]` No price appears on any source, and no SDK mentions payment. The prior audit also
recorded cost as `[GAP]`. **This is a gap, not a "free" — do not write "free" anywhere on the back of
this document.**

**Token lifetimes:** `[SECONDARY]` The Node wrapper's README: *"if you set this and the token expires
(lasts an hour) then the token will automatically refresh"*; `[SECONDARY]` an independent MCP-server
README: tokens *"expire hourly"*. `[SNIPPET]` One search synthesis claimed "6 minutes" — **it
contradicts two better sources and is recorded as unreliable, not averaged in.** Refresh tokens are
used to mint new access tokens; `[GAP]` refresh-token lifetime.

**Rate limits:** `[VERIFIED — prior audit]` Yahoo publishes no numeric limit, only *"Yahoo monitors
API usage … we may temporarily throttle or limit access."* `[SECONDARY]` One third-party project
states *"Yahoo allows 1000 requests/hour"* and self-imposes a 900/hour ceiling. `[SECONDARY]` A Node
wrapper issue records that Yahoo blocks for a short period, keyed on the registered app ID, when
request volume is too high. `[ANALYSIS]` Plan against ~1000/hour per app as an unconfirmed working
assumption, and note this interacts directly with §3.3's polling question.

### 2.3 The ambiguity that is worth stating rather than resolving

`[SNIPPET]` The Yahoo Sports Developer Portal says access requires agreeing to an **API Access and Use
Agreement** and — in language reproduced twice across independent searches — *"provide information
about your organization, your product, and your use case(s)"*, with *"Yahoo will review your
application and reach out with any follow-up questions."*

`[SECONDARY]` Every SDK's instructions describe no review at all: create app, receive credentials,
authorise, call.

`[ANALYSIS]` Three readings are consistent with the evidence and I cannot distinguish them:

- (a) The portal describes a **commercial/partner** tier; the self-serve app path remains open for
  individuals and is what the SDKs use.
- (b) The portal is the **new front door for everyone** and self-serve apps registered today no longer
  get Fantasy Sports scope.
- (c) Both work, and the portal is a marketing surface layered over an unchanged self-serve flow.

`[GAP]` **Which one is true.** I could not close it without fetching Yahoo hosts, and the two sources
that would have settled it from outside — Reddit and Stack Overflow — were refused by the search tool.
**(a) is my prior on the shape of the language, but that is a prior, not evidence, and it must not be
reported as a finding.**

### 2.4 The five-minute test that closes the gap — and validates against data this repo already holds

`[ANALYSIS]` The founder does not need research to answer this; he needs one attempt. Suggested order,
because each step fails informatively:

1. Register the app per §2.2. **If Fantasy Sports → Read is not offered, or the app creator refuses,
   reading (b) is true and the fallback question becomes live.** Otherwise continue.
2. Authorise once and list his own leagues. `[SECONDARY]` The `users;use_login=1/games/leagues`
   collection is the documented way to discover league keys; the key format is
   `{game_key}.l.{league_id}`, so Westwood is `{game_key}.l.154693`. `[GAP]` The 2026 NFL `game_key`
   — do not guess it, the discovery call returns it.
3. Call `league/{key}/settings`. **Compare the returned scoring against `CLAUDE.md` §7.** This is a
   free correctness audit of a table that was verified by eye against a screenshot in ADR-052.
4. Call `league/{key}/draftresults` **for the 2025 season** and diff against the project's existing
   hand-transcribed 2025 Westwood draft (n=160, the sole basis for `DEFAULT_LAMBDA`). `[ANALYSIS]`
   **This is the single best test in this document**: it exercises auth, league key, and the exact
   endpoint a live draft would use, and it independently checks a hand transcription the availability
   model currently depends on. Either it matches — auth works and the transcription is validated — or
   it doesn't, and one of two things this project believes is wrong.

---

## 3. Q3 — What the API can reach

All `[SECONDARY]` unless marked: these are third-party wrappers and an archived-docs mirror
describing Yahoo's surface. Yahoo's own current documentation was not read by anyone in this session.

### 3.1 League configuration — the highest-value, least-glamorous item

`[VERIFIED]` (fetched `yfpy/models.py`) the `Settings` model's attributes, verbatim:

> `cant_cut_list, divisions, draft_pick_time, draft_time, draft_together, draft_type,
> has_multiweek_championship, has_playoff_consolation_games, invite_permission, is_auction_draft,
> league_premium_features, max_teams, num_playoff_consolation_teams, num_playoff_teams,
> persistent_url, pickem_enabled, player_pool, playoff_start_week, post_draft_players,
> roster_positions, scoring_type, sendbird_channel_url, stat_categories, stat_modifiers,
> trade_end_date, trade_ratify_type, trade_reject_time, uses_faab, uses_fractional_points,
> uses_lock_eliminated_teams, uses_median_score, uses_negative_points, uses_playoff,
> uses_playoff_reseeding, waiver_rule, waiver_time, waiver_type`

And, `[VERIFIED]` from the same file:

> `Stat`: `abbr, bonuses, display_name, enabled, group, is_excluded_from_display,
> is_only_display_stat, name, position_type, position_types, sort_order, stat_id,
> stat_position_types, value`
>
> `Bonus`: `points, target`
>
> `RosterPosition`: `abbreviation, count, display_name, is_bench, is_starting_position, position,
> position_type`

`[ANALYSIS]` Mapped against what `CLAUDE.md` §7 records as hand-verified or missing:

| `CLAUDE.md` §7 item | API field that would supply it |
|---|---|
| Half-PPR reception value, per-yard rates, TD values | `stat_modifiers` → `Stat.value` per `stat_id` |
| **Stacking yardage bonuses (+1/+1.5/+2 at three thresholds each)** | **`Stat.bonuses` → `Bonus.target` / `Bonus.points`** |
| 10 teams | `max_teams` |
| Roster shape 1QB/3WR/2RB/1TE/2FLEX/1DEF, 6 bench, 1 IR | `roster_positions` (`position`, `count`, `is_bench`, `is_starting_position`) |
| Playoff weeks 16–17, 4 teams, **no reseeding** | `playoff_start_week`, `num_playoff_teams`, **`uses_playoff_reseeding`** |
| FR-012's two unconfirmed leagues | the same call, against their league keys |

`[SNIPPET]` Yahoo's own help material states bonus points are cumulative — *"a player earning 250
yards rushing would receive all bonuses"* — which independently corroborates ADR-052's live-platform
finding that Westwood's bonuses stack. `[ANALYSIS]` Two independent confirmations of the stacking
rule is worth having; ADR-052 rested on one screenshot session.

**`[GAP]`** Whether `Stat.bonuses` actually populates for a football league with commissioner-set
bonuses, or is a baseball-era field that returns empty. The model's existence is evidence Yahoo emits
it *somewhere*. It is not proof it emits it here. One call settles it.

### 3.2 Rosters, players, transactions, draft results

`[VERIFIED]` (fetched readthedocs for `yahoo_fantasy_api`, plus `yfpy` models):

| Capability | Method / endpoint | Notes |
|---|---|---|
| Draft results | `league/{key}/draftresults` `[VERIFIED]` URI pattern from the archived-docs mirror | `DraftResult`: `cost, pick, round, team_key, player_key` |
| Rosters | `Team.roster(week, day)` | Per-team, per-week |
| Taken / free agents / waivers | `taken_players()`, `free_agents(position)`, `waivers(position)` | |
| Player detail + stats | `player_details()`, `player_stats()` by season/week/date range | |
| Standings, matchups, transactions | `standings()`, `matchups(week)`, `transactions(...)` | |
| Ownership | `percent_owned(player_ids)` | |
| **Writes** | `add_player`, `drop_player`, `claim_player(faab)`, `propose_trade`, `accept_trade`, `change_positions` | Requires Write scope, not Read |
| Platform ADP | `player/{player_key}/draft_analysis` → `average_pick`, `average_round`, `average_cost`, `percent_drafted` | Carried from `docs/research/yahoo-draft-assistant-2026-07-29.md`; **unchanged, still gated on the §6 questions** |

### 3.3 Live draft state — say it explicitly, in both directions

**Reading picks as they happen: probably yes, on one source.**

`[VERIFIED]` (fetched the raw source of `spilchen/yahoo_fantasy_api`) — the `draft_results` docstring,
in full:

> ```
> Get the results of the league's draft
>
> This will return details about each pick made in the draft.  For
> auction style drafts it includes the auction price paid for the
> player.
>
> The players are returned as player IDs.  Use the player_details() API
> to find more specifics on the player.
>
> If this is called for a league that has not yet done a draft then it
> will return an empty list.
>
> If this is called during the draft this includes the players that have
> been drafted thus far.  For auction style drafts, it does not include
> the player currently being nominated.
> ```

`[ANALYSIS]` The auction caveat is the tell. Nobody writes "it does not include the player currently
being nominated" from a specification; that is someone who watched it happen. I rate this claim high
for a single source.

**But it is a single source, and here is what is not established:**

- `[GAP]` **Latency.** How long after a pick is made in Yahoo's draft client does it appear in
  `draftresults`? Unknown. In a 10-team draft with a short clock, a 30-second lag is the difference
  between an assistant and a scoreboard.
- `[GAP]` **Whether Yahoo tolerates the polling.** §2.2's unconfirmed ~1000 requests/hour would allow
  a poll every 4 seconds for an hour, but a throttle keyed on app ID mid-draft is a failure at the
  worst possible moment.
- `[SNIPPET]` The Node wrapper's docs show only a completed draft (`"draft_status": "postdraft"`) and
  say nothing about in-progress drafts. `[SNIPPET]` `predraft` and `postdraft` are attested as
  `draft_status` values; **`drafting` is not attested by any source I read** — a search synthesis
  called it logical, which is exactly the kind of plausible invention this document refuses to make.
  `[GAP]` The full value set.
- `[SNIPPET]` FantasyPros' own help material states *"Yahoo leagues cannot usually be connected to the
  Draft Wizard until 30 minutes before your draft begins"* — `[ANALYSIS]` consistent with league draft
  resources only becoming addressable near draft time, but it is one snippet about a competitor's
  product, not about the API.

**Writing a pick: no.** `[SECONDARY]` No wrapper in any language documents a draft-pick write. Roster
transactions are POSTable to the transactions collection; draft picks are not. `[ANALYSIS]` This is an
argument from absence across five independent libraries, which is reasonably strong but is not the
same as a documented prohibition. Consequence: **an assistant can advise, and the founder clicks.** It
cannot auto-draft through the API.

**How to settle the read question for free:** `[ANALYSIS]` Yahoo mock drafts are free and repeatable
(established in the prior Yahoo research). Join one, and while it runs, poll
`league/{key}/draftresults` every ~5 seconds and log timestamps against the picks. Twenty minutes
converts the highest-value `[GAP]` in this document — including the latency number — into a
`[VERIFIED]`. `[GAP]` Whether a mock draft produces a league key discoverable through
`users;use_login=1`; if not, the same test runs against the real draft, at higher stakes.

**A sample-quality warning I want on the record, because the answer agrees with what we wanted.** The
live-draft "yes" is: one docstring, undated, in one library, unconfirmed by the four other wrappers,
about an API whose own documentation is offline. It arrived pointing the direction that would make
this product most interesting. **That is exactly the configuration in which to demand the mock-draft
test before anyone plans around it.**

---

## 4. Q4 — ESPN

`[SECONDARY]` unless marked.

| Question | Answer |
|---|---|
| Official public API? | **No.** `[VERIFIED — prior audit]` No public documented fantasy API; the community host `lm-api-reads.fantasy.espn.com` is undocumented and returned HTTP 403 even for `robots.txt` |
| Developer programme / OAuth? | `[GAP]` None found. No registration surface, no scopes, no tokens |
| What do people actually use? | Cookie replay. `[VERIFIED]` ffscrapr's vignette: two values copied by hand from a logged-in browser — `ESPN_S2` *"often over 250 characters long"* and `SWID` *"about 38 characters long including the curly brackets"* — found under devtools → Storage/Application → Cookies for `fantasy.espn.com` |
| Can those be obtained programmatically? | `[VERIFIED]` ffscrapr: *"This cannot be done programmatically at this time."* `[SECONDARY]` The `espn-api` maintainer, asked whether a login flow could gather them: *"It is probably possible, but it would likely require using selenium or some browser then grab the cookies associated with it"* — and called that out of scope as *"much more heavy weight than a python library"* |
| Does username+password work? | `[SECONDARY]` Reported no: ESPN *"introduced additional recapcha authentication so now it's impossible to get access to private leagues using the userid and pass."* No follow-up in that discussion reports overcoming it. `[ANALYSIS]` Single-source and undated, but it is the only direct evidence either way and it points the same way as the maintainer's "you'd need Selenium" |
| Do the cookies expire? | `[SECONDARY]` They *"remain the same through different sessions."* `[GAP]` Actual expiry. `[SECONDARY]` A Chrome extension to extract them was released 2025-08-20, which `[ANALYSIS]` implies people re-extract often enough for it to be worth building |
| What can be read once authenticated? | `[VERIFIED]` (fetched `espn_api/football/settings.py`) `Settings` parses `scoring_format` (stat id, points, override, labels) from `scoringSettings.scoringItems`, and `position_slot_counts` from `rosterSettings.lineupSlotCounts`. `[SECONDARY]` The wiki lists `League, Team, Player, Pick, Settings, Matchup, Activity, BoxScore, BoxPlayer` — rosters, free agents, draft picks, box scores, power rankings, recent activity |
| Live draft? | `[GAP]` Nothing found either way. The `Pick` class exists; whether it populates mid-draft is unestablished and I found no source that tried |
| Terms | `[VERIFIED — prior audit]` Disney ToU **§2.B.x** prohibits "access, monitor, copy or extract the Disney Products using a robot, spider, script, or other automated means", expressly "including … for the purposes of creating or developing any AI Tool, data mining or web scraping". **§2.A** licences the products "for your personal, noncommercial use only" and expressly excludes any "use, creation, development, modification, prompting, fine-tuning, training, testing, benchmarking or validation of any artificial intelligence or machine learning tool". **§3.H**: "we do not allow uses of the Disney Products … that are commercial or business-related" |

`[ANALYSIS]` **The ESPN answer is structurally different from Yahoo's and should not be blended with
it.** On Yahoo there is a sanctioned channel whose terms have specific, checkable constraints. On
ESPN there is no sanctioned channel at all: the working mechanism is cookie replay by an automated
client, which §2.B.x names, and this project is an AI tool, which §2.A names twice. Reporting "we can
connect to ESPN because a Python library exists" would be true about the mechanism and false about
whether it is permitted. **If any of the founder's three leagues is on ESPN, that league's settings
are a manual-entry problem, not an integration problem** — unless he decides otherwise, which is his
call and not a technical question.

---

## 5. Q5 — The fallback, honestly costed

### 5.1 What the terms say

**The clause the brief asked for, with its confidence stated exactly.** `[SNIPPET]` Yahoo's Terms of
Service, under a section titled "Use of the Services", reproduced identically across two independent
searches:

> "…any automated process to access or use the Services or any process, whether automated or manual,
> to capture data or content from any Service for any reason."

**I did not render that page** — `legal.yahoo.com` was not fetched, per this session's instruction —
so this is `[SNIPPET]`, not `[VERIFIED]`, and it is a fragment rather than a full sentence with its
lead-in. **Do not quote it as verbatim in anything founder-facing without confirming it.** The
document is at `https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html` and the founder can read
it in a browser in under a minute — which is the right way to close this, since the constraint here is
mine, not his.

**Three routes to a non-Yahoo copy were tried and all three failed, recorded so nobody assumes I
didn't look.** `[VERIFIED]` `web.archive.org` — fetch tool refuses the domain outright.
`[VERIFIED]` `tosdr.org` — HTTP 404 on search; service ID 288 turned out to be Weebly, not Yahoo.
`[VERIFIED]` A genuine non-Yahoo reproduction **does** exist and is fetchable —
`https://www.law.uh.edu/faculty/gvetter/classes/InternetLaw.Spring2009/YahooTerms.pdf`, a University
of Houston Law Center course copy — but it downloaded as a 47 KB PDF that could not be rendered in
this container (`pdftoppm` absent, and no shell to install it). **A session with a shell can extract
that clause in one command.** Note it is a **2009** copy: useful for establishing that the clause is
long-standing, useless for establishing the *current* wording, and it must be dated wherever it is
quoted.

`[ANALYSIS]` Two things about that fragment, if it is accurate. First, it reaches **manual** capture
too ("whether automated or manual"), which is broader than a pure anti-bot clause and would, read
literally, also cover the screenshot-transcription route this project has already used twice.
Second, nothing in it turns on *whose* account is being accessed — there is no visible carve-out for
a user automating access to his own data. `[GAP]` Whether a carve-out exists elsewhere in the
document.

**Related documents nobody in this project has read, listed so they are not assumed away:**

| Document | URL | Status |
|---|---|---|
| Yahoo Terms of Service (consumer) | `legal.yahoo.com/us/en/yahoo/terms/otos/index.html` | `[SNIPPET]` fragment only, above |
| **Yahoo Fantasy Sports APIs: Terms of Use** | `legal.yahoo.com/us/en/yahoo/terms/product-atos/fantasysportsapi/index.html` | `[GAP]` **Never read by anyone on this project.** This is the fantasy-*specific* API terms document and it is distinct from the general developer terms the prior audit read. It should be the first thing read if the API path is pursued |
| Yahoo Developer API Terms of Use | `legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html` | `[VERIFIED — prior audit]`, three clauses in §6 |
| Yahoo Sports Fantasy Football Additional ToS | `legal.yahoo.com/us/en/yahoo/terms/product-atos/fantasy-football/general/` | `[GAP]` Contents unknown |

### 5.2 The three costs, filled in with what was actually found

`CLAUDE.md` §10's three reasons, with evidence rather than assertion:

| Cost | What this session establishes |
|---|---|
| **Credential liability** | Unchanged and not researchable — a stored Yahoo password is reusable everywhere that password is reused; an OAuth token is scoped to Fantasy Sports Read and revocable from the account page. `[ANALYSIS]` The asymmetry is the point: the OAuth path's worst case is "someone reads my fantasy league"; the password path's worst case is "someone has my Yahoo account", which for most people is also their email recovery |
| **Brittleness** | `[SECONDARY]` ESPN is the natural experiment and it already failed: recaptcha reportedly ended password-based access there, and the community's answer is a browser extension, not a script. `[GAP]` Yahoo's specific login defences (2FA, device verification, captcha) were **not** established — I have no evidence about them and will not infer them from ESPN's |
| **Terms** | §5.1. `[SNIPPET]` The clause reaches automated access generally, with no visible own-account carve-out |

### 5.3 What the fallback would actually have to be, and what it buys

`[ANALYSIS]`, clearly labelled:

- **On Yahoo**, if OAuth is open (§2.3 reading (a) or (c)), a credential path buys **nothing** — the
  same league settings, rosters, and draft results come out of the sanctioned channel. It would be
  paying all three costs for zero additional capability.
- **On Yahoo**, if OAuth is genuinely closed (reading (b)), the fallback is browser automation
  driving a logged-in session — and it lands on `football.fantasysports.yahoo.com`, whose `robots.txt`
  `[VERIFIED — prior audit]` disallows `/F1/`, `/LEAGUE/` and `/DRAFTCLIENT/` outright. **The draft
  client path is specifically disallowed.** So the fallback's most valuable target is also its most
  clearly blocked one.
- **On ESPN**, the realistic path is not a password at all — it is copying two cookies by hand once
  and pasting them into a config, which is what the entire community does. `[ANALYSIS]` That is
  materially *less* bad than a stored password on the credential-liability axis (a cookie is scoped
  and expirable), and materially *worse* on the terms axis, because §2.B.x and §2.A both name it.
  These are different trades and collapsing them into "the fallback" hides that.
- **The option nobody listed, which is currently what the product does:** manual entry. `[ANALYSIS]`
  For *league settings*, this is a one-time cost per league, already paid for Westwood and Ethan's
  Expert, and it carries zero terms exposure. The API's advantage there is correctness and FR-012, not
  labour. For *live draft picks*, manual entry is what the draft-room screen already implements, and
  it degrades gracefully when an integration would fail. **The gap the API closes is not "we can't do
  this" — it is "we do it by hand and might mistype."**

---

## 6. Fetching vs. retaining vs. displaying — three different answers

This is the section that decides whether Yahoo is viable for a *product* or only for the founder's
own machine, and the three questions have three different answers.

| | Yahoo (OAuth) | ESPN (cookies) |
|---|---|---|
| **May I fetch?** | `[VERIFIED — prior audit]` Yes, via the sanctioned OAuth channel, with the user's own authorisation, subject to the API Access and Use Agreement | `[VERIFIED — prior audit]` **No.** Disney ToU §2.B.x names automated access; there is no sanctioned channel to use instead |
| **May I retain?** | `[VERIFIED — prior audit]` Yahoo user data "not explicitly identified as being storable indefinitely" must be deleted **within 24 hours**. `[SNIPPET]` The storable-indefinitely set is reported as **GUID and authenticated token value only**, with everything else re-requested each time. `[GAP]` Whether that list is accurate and complete — **this is the question that decides the whole feature's shape** | n/a — blocked upstream |
| **May I display to a third party?** | `[VERIFIED — prior audit]` Three clauses bite: **(a)** the 24-hour deletion rule; **(b)** no "derive income from the use or provision of the Yahoo APIs" without written permission; **(c)** may not "Use the Yahoo APIs in a product or service that competes with products or services offered by Yahoo." `[SNIPPET]` Attribution "Fantasy data provided by Yahoo Fantasy" with a link back is required | n/a — blocked upstream |

`[ANALYSIS]` **Three consequences worth stating plainly.**

1. **The retention rule, if the GUID-and-token reading is right, forbids the obvious design.** "Sync
   my league into `nfl.db`" is exactly the pattern the clause prohibits. The compliant design is
   fetch-at-session-start, hold in memory, discard — which is *fine* for a draft-day assistant and
   *fatal* for "the app knows my league history." Nobody should build the first thinking it is the
   second.
2. **Clause (c) is not hypothetical for this project any more.** `CURRENT-STATE.md` records the app as
   live on the open internet by explicit founder choice. Yahoo ships Draft Scout, a draft assistant.
   This is a draft assistant. `[ANALYSIS]` A private single-user tool and a publicly-reachable one are
   different postures under that clause, and the project has moved from the first to the second since
   the clause was last considered. **This is a founder decision and arguably a lawyer's; it is not an
   agent call and I am not making it.**
3. **This is the same fault line the FFC/FantasyPros authorisations sit on.** `docs/ideas-inbox.md`
   already records that every one of those is scoped "private use by one person, void if the product
   reaches a second human", against an app that is now publicly reachable. **Yahoo would be the third
   source on that list.** Whatever ruling settles the existing two should settle this one, and it
   should be one ruling, not three.

---

## 7. How FantasyPros does it — and why it is two mechanisms, not one

The founder-request cites FantasyPros' one-click "Sync Your League" as proof the integration is
achievable. It is — but the evidence says they use **two different mechanisms for two different
jobs**, and conflating them would mis-scope any build here.

**`[VERIFIED]` Every FantasyPros support article I tried returned HTTP 403.** Everything below is
`[SNIPPET]` from search results over those articles' titles and excerpts. Their own words were not
read.

| Job | Mechanism | Tag |
|---|---|---|
| **League sync** (settings, rosters, teams) | OAuth. "Click Continue to authorize access to your Yahoo fantasy sports profile… log into the Yahoo account that is associated with the league." Then "If you encounter a prompt requesting authentication access to your account, please grant it" | `[SNIPPET]` |
| **Live draft sync** (picks as they happen) | **A browser extension inside the user's own draft room** — not API polling. Requires installing the FantasyPros Chrome extension and setting Chrome to allow third-party cookies. It "provides pick-by-pick expert advice in your Yahoo, ESPN, or NFL.com fantasy draft room" and "allows you to make your picks without leaving the draft room" | `[SNIPPET]` |
| **Auto-pick backstop** ("Co-Pilot") | ESPN-specific; drafts their top suggestion when 10 seconds remain on the clock | `[SNIPPET]` |
| Timing constraint | "Yahoo leagues cannot usually be connected to the Draft Wizard until 30 minutes before your draft begins" | `[SNIPPET]` |

`[ANALYSIS]` Four readings, in descending confidence:

1. **The extension exists because the DOM is where the picks are, in real time, on all three
   platforms at once.** One extension covers Yahoo, ESPN and NFL.com; three API integrations would
   not, since ESPN has no API to integrate with. That alone explains the choice without needing the
   Yahoo API to be inadequate.
2. **It also explains the pick-*placing* capability.** §3.3 found no draft-pick write endpoint. An
   extension sitting in the draft room can click; an API client cannot. Co-Pilot is only buildable
   the extension way.
3. **It is therefore weak evidence — not strong — that Yahoo's API cannot serve live picks.** They had
   independent reasons to choose the extension. Do not read their architecture as a verdict on §3.3.
4. **What it is good evidence for:** the OAuth league-sync half is a solved, shipped, consumer-grade
   integration that a major vendor runs at scale. `[ANALYSIS]` For the half of FR-062 that actually
   matters most day-to-day — the app knowing his league settings — the achievability question is
   answered.

`[GAP]` Whether FantasyPros holds a commercial Yahoo agreement that an individual developer would not.
`[ANALYSIS]` Given §6's clauses (b) and (c) and the fact that FantasyPros is a paid product, it is
reasonably likely they do — **so "FantasyPros does it" is not by itself evidence that the same thing
is permitted for this project.** Same mechanism, possibly different licence.

---

## 8. Sample quality — the count that matters

Sixteen nominal sources collapse into far fewer independent units:

| Unit | Members | Effective n |
|---|---|---|
| **Yahoo's own documentation** | none | **0.** Not one Yahoo-authored word was read this session. The archived-docs mirror is a *copy* of a guide Yahoo stopped maintaining, so even it is not current Yahoo |
| **Yahoo API wrappers** | `yfpy`, `yahoo_fantasy_api`, `yahoofantasy`, `yahoo-fantasy-sports-api` (Node) + its docs site, `YFAR` (R) | **~3 genuinely independent.** They agree on registration, on `settings`/`draftresults` shapes, and on hourly tokens — real corroboration. But all reverse-engineered the same undocumented surface and several cite each other, so a shared error is possible. **For the live-draft claim specifically the effective n is 1** |
| **Yahoo terms** | `[SNIPPET]` consumer ToS fragment + `[VERIFIED — prior audit]` developer ToU | **1, and not re-verified.** The fantasy-specific API ToU has never been read by anyone here |
| **ESPN libraries** | `espn-api` (Python) + its wiki/discussions, `ffscrapr` (R), `mkreiser` (JS) | **2.** ffscrapr and espn-api agree independently on the cookie method and on "not obtainable programmatically" |
| **FantasyPros** | 5–6 support articles | **1, and 0 fetched.** All one vendor's help centre, all 403 |
| **Registration freshness** | — | **0 dated first-hand reports.** Reddit and Stack Overflow were refused by the search tool. The freshest hard evidence is yfpy's 2025-09-14 release, which tells you the *library* is maintained, not that a *new* app gets access |

**Non-representativeness to flag even though it points the way we hoped:** the strongest pro-API
findings — live draft reads, bonus-threshold exposure — each rest on a **single artefact**
(`yahoo_fantasy_api`'s docstring; `yfpy`'s `Bonus` class). Both are code, not observations. A model
class in a wrapper proves the author saw the field once, in some sport, in some year. Neither is a
measurement of what Westwood's league key returns in 2026. **Both are one API call away from being
`[VERIFIED]`, and until that call is made they should carry their tags into every downstream
document.**

---

## 9. Gaps, listed so nobody fills them by accident

1. `[GAP]` **Whether a newly-registered self-serve Yahoo app gets working Fantasy Sports API access in
   2026**, or whether the `sports.yahoo.com/developer` review gate now applies to everyone. **Highest
   value, cheapest to close, and it is the founder's actual question.**
2. `[GAP]` **Live-draft polling latency**, and whether Yahoo throttles a client polling through a
   draft. The free mock-draft test in §3.3 closes both at once.
3. `[GAP]` The full `draft_status` value set. `predraft` and `postdraft` are attested; **`drafting` is
   not attested by any source I read.**
4. `[GAP]` Whether `Stat.bonuses` populates for a football league with commissioner-set yardage
   bonuses.
5. `[GAP]` The exact, complete list of Yahoo data "explicitly identified as being storable
   indefinitely." `[SNIPPET]` says GUID + authenticated token value. **This decides the shape of any
   league-connection feature and it is currently a snippet.**
6. `[GAP]` The **Yahoo Fantasy Sports APIs: Terms of Use** — the fantasy-specific document. Never read
   by this project.
7. `[GAP]` The full verbatim sentence and section number of the consumer-ToS automated-access clause;
   §5.1 has a fragment only. **Closeable without touching a Yahoo host** — §5.1 names a fetchable
   non-Yahoo PDF reproduction that this container could not render for want of `pdftoppm`.
8. `[GAP]` Whether Yahoo's ToS contains any carve-out for a user automating access to his own account.
9. `[GAP]` Any price for Yahoo API access. **Do not write "free."**
10. `[GAP]` Yahoo's numeric rate limits. `[SECONDARY]` ~1000/hour from one third-party project only.
11. `[GAP]` Refresh-token lifetime.
12. `[GAP]` Whether ESPN's `Pick` data populates during a live draft.
13. `[GAP]` ESPN cookie expiry.
14. `[GAP]` Whether FantasyPros holds a commercial Yahoo licence an individual would not.
15. `[GAP]` Yahoo's login-flow defences (2FA, captcha, device verification) — **not** inferred from
    ESPN's.
16. `[GAP]` Whether a Yahoo mock draft creates a league key discoverable via `users;use_login=1`.

---

## 10. What this implies, stated as options not decisions

`[ANALYSIS]` throughout.

1. **Do the §2.4 test before any other decision.** It is one app registration plus four HTTP calls,
   and it collapses gaps 1, 4 and most of the founder's question. The 2025-draft-results diff also
   audits a hand transcription the availability model depends on — the test pays for itself even if
   the answer is no.
2. **If it works, the first thing to build is not draft-day.** It is `league/{key}/settings` against
   all three leagues, which closes FR-012, independently re-verifies `CLAUDE.md` §7, and touches no
   live-draft uncertainty at all. Highest value, lowest risk, and it is the thing that has been typed
   in by hand twice.
3. **Do not design a Yahoo league cache until gap 5 is closed.** If the 24-hour rule reads the way
   `[SNIPPET]` reports, fetch-on-demand is the only compliant shape, and discovering that after
   building a table is the expensive order.
4. **Treat the public-hosting question as one ruling covering FFC, FantasyPros and Yahoo together.**
   It is already open for the first two (`docs/ideas-inbox.md`, thread 092 item 2). Yahoo joins the
   same list under clause (c), and answering it three times separately will produce three different
   answers.
5. **Record ESPN as having no compliant automated path, and stop re-costing it.** The mechanism is
   known, works, and is named in the terms it violates. If a league is on ESPN, its settings are
   manual entry unless the founder rules otherwise — which is his call to make explicitly, once,
   rather than something to rediscover every time it comes up.
6. **The password question, answered directly for him:** technically it is probably possible on
   Yahoo and reportedly is not on ESPN — and on Yahoo it would buy nothing that OAuth does not already
   give, while costing a stored password, a login flow that breaks silently, and a clause that on its
   face covers it. **The interesting finding is not that the fallback is bad. It is that the thing he
   was worried about losing does not appear to be lost.**

---

*Sources are tagged inline. No Yahoo or ESPN host was fetched. `web.archive.org`, `reddit.com` and
`stackoverflow.com` were refused by the tools and are recorded as unavailable rather than routed
around; `support.fantasypros.com` returned HTTP 403 and is recorded as unretrieved, since without a
shell I could not determine whether the 403 was origin-side or proxy-side.*
