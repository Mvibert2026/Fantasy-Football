# Yahoo's in-draft assistant — what the Westwood room actually sees

**Date:** 2026-07-29 · **Role:** researcher · **Scope:** research only. Nothing was built, no
ingestion code was written, no data was collected.

**Standing block honoured, stated up front.** Yahoo has explicit written prohibitions on automated
collection (`docs/pm/MEMORY.md` §4; `docs/research/source-audit-2026-07.md` §6). That block was not
lifted by the 2026-07-29 FFC authorisation, which is FFC-specific. **No Yahoo scraper was built,
tested, or designed. No Yahoo fantasy page was fetched.** See §1 for the fetch-by-fetch record.

Confidence tags, used on every factual claim:

| Tag | Meaning |
|---|---|
| `[VERIFIED]` | I fetched it directly from the source's own page or API this session and read it |
| `[SNIPPET]` | Seen only in a search excerpt or a search tool's synthesis; the page did not render for me |
| `[SECONDARY]` | Third-party reporting or third-party documentation only |
| `[GAP]` | Could not establish. **Never** filled with a plausible substitute |
| `[ANALYSIS]` | My own reasoning from tagged facts, labelled so it is never mistaken for a fetched claim |

---

## 0. Conclusion, first

**Does this change what the project should treat as the behaviour-predicting ADP source?**

The founder's insight is **structurally correct and is now better specified than he stated it** — but
it is **not directly actionable**, and the honest answer is that the specific numbers Yahoo puts on
his league-mates' screens are **not legitimately obtainable by this project through any automated
route**. That is a finding, not a failure. Four parts:

**1. "The Yahoo board" is not one number. It is at least three, computed differently.** This is the
single most useful correction to the founder's framing. `[SNIPPET]` Yahoo distinguishes a **Default
Rank** ("Rank") computed from *your league's* scoring settings; an **Expert Rank** computed from
*Yahoo's default* scoring, not yours; and a platform-wide **ADP** from real Yahoo drafts. Which of
the three a given drafter anchors on changes what you would need to model. Treating them as one
object would reproduce exactly the blending error `src/ingest_mfl_adp.py`'s docstring exists to
prevent.

**2. The likely exploitable gap is narrower than expected on one axis and wider on another.**
`[SNIPPET]` Yahoo's default football scoring is already half-PPR (0.5/reception), so Westwood is
*not* anchored to a full-PPR room the way a generic PPR ADP source would imply. `[SNIPPET]` But
Yahoo's default settings do **not** include the milestone yardage bonuses, and `[SNIPPET]` Expert
Rank — which `[SNIPPET]` also drives autopick — is computed against those defaults. Westwood's
distinguishing feature is precisely its **stacking** yardage bonuses. `[GAP]` **Whether Yahoo's
league-scoring-aware Default Rank actually prices bonus thresholds at all is unestablished, and it
is the highest-value single unknown in this document.** `[ANALYSIS]` It is a hard thing to do
correctly: a threshold bonus is a nonlinear function of a player's *per-game* yardage distribution,
not of a season total, so a projection engine that only produces season totals cannot price it
without simulating games. If Yahoo does not, then every drafter in the room — including the ones
reading Yahoo's league-aware "Rank" — is looking at numbers that systematically under-price ceiling
outcomes in a league that pays for them. That is exactly the class of edge this project exists to
find. **Do not act on it until the gap is closed** (see §8 for how).

**3. Exactly one Yahoo number is obtainable within the rules, and it is the behavioural one.**
`[SECONDARY]` The official OAuth Fantasy Sports API exposes a `draft_analysis` sub-resource
returning `average_pick`, `average_round`, `average_cost`, `percent_drafted` — real ADP from real
Yahoo drafts. `CLAUDE.md` §10 prefers exactly this channel over browser automation. It is the right
shape for the founder's question, because what predicts his room is what Yahoo drafters *did*, not
what a ranking list said. **Three unresolved blockers stop it being a green light** (§4): the
audit-recorded 24-hour user-data deletion clause, the no-competing-product clause, and `[GAP]`
whether the figure can be filtered to 10-team half-PPR at all. It is a founder decision, not an
agent one.

**4. Nothing else is obtainable. Plan around that.** The displayed rank list, the tier treatment,
the Draft Scout recommendation, and the per-league Default Rank ordering have **no sanctioned
programmatic export**. `[VERIFIED]` The one well-known community tool in this space imports a custom
list *into* Yahoo; it does not export Yahoo's list out. The only route to those numbers is the
founder manually capturing his own screen — the same route that produced the project's only
half-PPR-native ranking input and the 2025 draft fixture.

**Therefore, concretely:**

- **Do not swap `mfl_proxy` for anything.** Nothing found here is a drop-in replacement, and the
  per-platform no-blending rule means a Yahoo source would be a *new* `adp_source`, never a merge.
- **The Yahoo-anchoring effect should be recorded as a named, signed, unmeasured source of
  uncertainty in the availability model**, not silently ignored and not quantified with an invented
  number. `[ANALYSIS]` Its sign is at least partly predictable: the free-tier default surface and
  the autopick fallback both order by Yahoo's own list, so availability error should be *larger* for
  players where Yahoo's ordering diverges most from the project's board, and the room should be
  expected to over-draft Yahoo-favoured players relative to a generic-market ADP prior.
- **The one cheap, legal, high-value action is a founder screenshot** of his own league's Pre-Draft
  Rankings page before the 7 September draft (§5). It costs him minutes and it is the only way this
  project will ever see the actual ordering the room is shown.

---

## 1. Access constraints — what I could and could not fetch

This section is load-bearing, because it caps the confidence of everything below it.

| Host | robots.txt status | Consequence |
|---|---|---|
| `help.yahoo.com` | `[VERIFIED]` Names `anthropic-ai`, `Claude-Web`, `ClaudeBot`, each `Disallow: /` | **Blocked.** Yahoo's own help documentation — the primary source for what the product does — is off-limits. Not fetched |
| `sports.yahoo.com` | `[VERIFIED]` Same three Anthropic agents, each `Disallow: /` | **Blocked.** This also swallows the developer portal, since `developer.yahoo.com/fantasysports/guide/` `[VERIFIED]` 308-redirects here. Not fetched |
| `www.aol.com` | `[VERIFIED]` Same three, each `Disallow: /`. (`Claude-User` not named) | **Blocked.** AOL mirrors Yahoo Sports articles, so the obvious workaround is itself blocked. Not fetched |
| `football.fantasysports.yahoo.com` | `[VERIFIED]` in the prior audit: `ClaudeBot`, `Claude-Web`, `anthropic-ai` disallowed; `/DRAFTCLIENT/` disallowed | **Blocked.** Not fetched, not attempted |
| `developer.yahoo.com` | `[VERIFIED]` Only `User-agent: *` with specific paths; **no AI-agent blocks** | Technically fetchable, but the fantasy guide redirects off-host to a blocked host. Dead end |
| `legal.yahoo.com` | `[VERIFIED]` `robots.txt` returns HTTP 404 | Not pursued; the API terms were `[VERIFIED]` by the prior audit and I did not re-verify |
| `www.fantasylife.com` | `[VERIFIED]` `/articles/` is **not** disallowed; `/analysis/`, `/players/`, `/api/`, `/datatable/` are | **Deliberately not fetched.** The prior audit recorded Fantasy Life as blocked and its ToS as `[GAP]`; I chose consistency with the recorded block over exploiting a path-level loophole. Flagged rather than resolved alone |
| `www.fantasypointcalculators.com`, `support.fantasypros.com`, `ftnfantasy.com` | — | `[VERIFIED]` HTTP 403 on fetch. **No Bash tool in this session**, so I could not run the proxy status check `docs/environment.md`/the env note describe; I cannot say whether these 403s were origin-side or proxy-side. Recorded as unretrieved, not as blocked |
| `sjdm.org` (open-access JDM paper on draft decision-making) | — | `[VERIFIED]` HTTP 503. Unretrieved |
| `www.draftsharks.com` | `[VERIFIED]` `User-agent: *`, `Disallow:` (nothing disallowed) | Fetchable; the ADP page body did not render for me. Unretrieved content |
| `rdrr.io`, `y-fantasy-node-docs.vercel.app`, `yahoo-fantasy-api.readthedocs.io`, `github.com` | — | `[VERIFIED]` Fetched successfully. These third-party API wrappers are the backbone of §4 |

**The consequence, stated plainly: every claim in this document about Yahoo's *product* is
`[SNIPPET]` or `[SECONDARY]` at best. There is no `[VERIFIED]` claim about the Yahoo draft room
anywhere below, and there cannot be one from an agent of this class.**

**A second, sharper caveat on `[SNIPPET]` in this document.** Most of these snippets are not raw
search excerpts — they are the search tool's own *synthesis* over excerpts, i.e. a model paraphrase
of a page neither of us rendered. That is weaker than a normal `[SNIPPET]`. Where a claim was
reproduced consistently across independent search queries I say so, because repetition raises my
confidence somewhat — but **it does not upgrade the tag**, since all the queries drew on the same
one or two underlying Yahoo help pages.

---

## 2. Q1 — What a drafter literally sees on the clock

`[SNIPPET]` The free Yahoo draft room presents, at minimum:

| Element | What it is | Tag |
|---|---|---|
| **Ranked available-player list** | "The players who are projected to be the best are listed at the top." Position tabs and a tab for players drafted by each team | `[SNIPPET]` |
| **Sortable columns** | Sortable "by average draft position or expert rank"; a toggle between **projected stats** and **last season's stats** | `[SNIPPET]` |
| **Queue / watch list** | Star players to build a personal queue. **"When a player is queued, that means he is your default pick if you run out of time on the clock"** | `[SNIPPET]` |
| **Autopick fallback** | If the clock expires with an empty queue, the pick is made from Yahoo's ranking. `[SNIPPET]` **"Expert Rank determines autopick rankings for drafts"** | `[SNIPPET]` |
| **Draft timer, roster status, drafted-players view** | Standard draft-room furniture | `[SNIPPET]` |
| **Draft Central "Position Ranks" tab** | A pre-draft surface at `/f1/draft?dktab=position_ranks` | `[SNIPPET]` — URL seen in search results only; page not fetched |

**Draft Scout — the actual "assistant", and it is paywalled during real drafts.** `[SNIPPET]` Draft
Scout "analyzes your fantasy league's draft in real time to suggest the top available players to add
the most projected value to your team," updating "based on your current roster and league settings."
`[SNIPPET]` Its metric is **VOLS — Value Over Last expected Starter**: a player's projected points
minus the projected points of the last player at that position expected to start in your league.
`[SNIPPET]` It is **free in mock drafts and subscriber-only in real drafts**, under Yahoo Fantasy
Plus, `[SNIPPET]` priced around $2.92/month billed annually.

`[ANALYSIS]` Three things follow, and they matter more than the feature list:

1. **The modal free drafter does not get a recommendation engine.** He gets a *sorted list* plus ADP
   and expert-rank columns. So "what the room sees" is predominantly an **ordering**, not an
   assistant's pick suggestion. That is good news for modelling: an ordering is a much simpler
   behavioural anchor than a roster-aware recommender, and it is stable across the draft rather than
   path-dependent on each manager's roster.
2. **Draft Scout is roster-aware and therefore path-dependent.** For whichever managers do pay, their
   deviations from ADP will correlate with their own roster construction, not with a fixed list.
   `[GAP]` How many in Westwood pay for Fantasy Plus is unknown and unknowable to this project.
3. **VOLS is conceptually the same family as this project's replacement-level VBD** (`RB30 / WR40 /
   TE10 / QB10` per `CURRENT-STATE.md`). `[ANALYSIS]` If Draft Scout is in the room, the project's
   positional-revaluation edge — which `docs/pm/MEMORY.md` §1 names as the board's *only* edge
   channel — is partially competed away for those managers, because they are running a
   replacement-level calculation too. Worth knowing before claiming positional revaluation as a
   differentiator against this specific room.

**Not established:** `[GAP]` whether the free draft room shows **tiers**, a **positional-need
prompt**, or a **live draft grade**. I found no credible statement either way and did not fetch the
draft client. Do not assume any of the three.

---

## 3. Q2 — What rankings it draws on, and for what scoring format

This is the crux, and the answer has a sharp internal structure.

`[SNIPPET]` Yahoo exposes several distinct rank types (reproduced consistently across four
independent search queries, all tracing to Yahoo help article SLN6287, which is robots-blocked to me
and was not fetched):

| Rank type | How it is computed | Scoring basis | Tag |
|---|---|---|---|
| **Default Rank** ("Rank") — the pre-draft ordering | "Based on the total projected categories according to your league's scoring settings"; explicitly "does not take position into consideration" | **Your league's settings** | `[SNIPPET]` |
| **Expert Rank** | Yahoo analysts' view of the season. **"Expert Rank determines autopick rankings for drafts"** | **Yahoo's default scoring, not yours** — "(1/2 point per reception in football...)" | `[SNIPPET]` |
| **Composite Expert Rank** | Average of Yahoo Fantasy analysts plus partner RotoWire | Presumably default scoring | `[SNIPPET]` |
| **Position Rank** | Player vs. others at his position | `[GAP]` | `[SNIPPET]` |
| **ADP** | "Actual draft trends from real leagues on Yahoo's platform" | All Yahoo leagues, overwhelmingly default settings | `[SNIPPET]` |

**Yahoo's default football scoring is half-PPR.** `[SNIPPET]` 0.5 points per reception is Yahoo's
default and the most common setting in Yahoo public leagues. `[VERIFIED]` This is corroborated
in-repo, independently of the web: `data/leagues/ethans_expert_league.json` — the founder's *second*
Yahoo league, recorded as running "Yahoo default scoring" — carries `receptions: 0.5`,
`passing_yards.per: 25`, `passing_td: 4`, `interception: -1`, `rushing_yards.per: 10`,
`receiving_yards.per: 10`, both TD types 6, `fumbles_lost: -2`, and **empty `bonuses: []` arrays on
all three yardage categories**.

`[ANALYSIS]` **That in-repo file is the cleanest available specification of the gap between Yahoo
generic and Westwood**, and it is verified data rather than a web claim. Diffing it against
`CLAUDE.md` §7:

| Category | Yahoo default (per `ethans_expert_league.json`) | Westwood | Direction of the gap |
|---|---|---|---|
| Receptions | 0.5 | 0.5 | **None.** Yahoo's anchor is already half-PPR |
| Yardage bonuses | **None** | +1/+1.5/+2 at three thresholds each for pass/rush/rec, **stacking** | **The entire wedge.** Yahoo's anchor under-prices ceiling |
| Interception | −1 | −2 | Yahoo's anchor slightly over-prices volume QBs |
| Kicker | Starter slot | **No kicker** | Roster shape, not scoring |
| Flex | 1 | **2** | Yahoo's anchor under-prices flex-eligible depth |

**The consequential unknown.** `[SNIPPET]` Yahoo's player *projections* are described as "designed
for use in leagues using Yahoo default scoring," and `[SNIPPET]` milestone bonuses (100-yard
rushing, 300-yard passing) are not in the default settings though commissioners may add them.
`[ANALYSIS]` These two claims sit in tension with "Default Rank is based on your league's scoring
settings": re-summing a *season-total* projection through custom per-point rates is easy, but a
**threshold bonus cannot be computed from a season total at all** — it needs the per-game
distribution. So one of three things is true, and I could not determine which:

- (a) Yahoo simulates per-game distributions and prices the bonuses correctly;
- (b) Yahoo applies linear scoring settings only and silently ignores bonus settings in Default Rank;
- (c) Yahoo applies some approximation.

`[GAP]` **Which one is true.** If (b) — which `[ANALYSIS]` I consider the most likely on
engineering-cost grounds, but that is a prior, not evidence — then **every screen in the Westwood
draft room, including the league-aware one, under-prices exactly the ceiling outcomes Westwood pays
for**, and `CLAUDE.md` §7's remark that "the yardage bonuses matter more than they look" becomes a
directly exploitable, room-specific edge rather than a modelling note. **Do not build on this until
it is confirmed.** §8 says how to confirm it cheaply and legally.

---

## 4. Q3 — Does Yahoo publish ADP or ranks through a sanctioned channel?

**Yes for ADP, via the official OAuth API. Probably not for the displayed rank list.**

**`draft_analysis` is real.** The prior audit had this as `[SNIPPET]`/unconfirmed. It is now
`[SECONDARY]` **confirmed on three mutually independent third-party sources fetched this session**:

- `[SECONDARY]` Node wrapper docs (`y-fantasy-node-docs.vercel.app`, fetched): the `draft_analysis`
  object contains exactly four fields — `average_pick` (example `"44.7"`), `average_round`
  (`"4.6"`), `average_cost` (`"23.4"`), `percent_drafted` (`"1.00"`).
- `[SECONDARY]` R wrapper `YFAR` reference (`rdrr.io`, fetched): *"Yahoo drafts are accompanied by
  ADP's and this function returns them. Values return include average_pick, average_round,
  average_cost and percent drafted."* Its `key` argument accepts **"a vector of game, league, or
  player keys"**.
- `[SECONDARY]` `YFAR`'s Yahoo API guide vignette (fetched): documents `draft_analysis` as a player
  sub-resource — *"Average pick, Average round and Percent Drafted"* — at
  `/fantasy/v2/player/{player_key}/draft_analysis`, and indicates it is reachable with a global
  player key (`{game_key}.p.{player_id}`) **without league context**.

**What that means, and where it stops:**

- `[SECONDARY]` A **game-level** call gives Yahoo platform-wide ADP — actual Yahoo drafter behaviour
  across all Yahoo leagues. `[ANALYSIS]` This is a genuinely better behavioural instrument for the
  founder's question than any expert-consensus list, because it measures picks, not opinions.
- `[SECONDARY]` A **league-level** key is also accepted, which `[ANALYSIS]` raises the possibility
  of ADP scoped to a specific league — but `[GAP]` I could not establish what a league-scoped
  `draft_analysis` actually returns for a league that has not drafted yet, nor whether it is
  meaningful for a 10-manager league.
- `[GAP]` **Whether platform-wide ADP can be filtered by scoring format or league size at all.**
  Nothing in any of the three sources mentions a format or `FCOUNT`-equivalent parameter. This is the
  same problem `docs/pm/MEMORY.md` §4 flags for the MFL capture, and it would be worse here: MFL at
  least lets you pin `FCOUNT=10`. `[ANALYSIS]` Unfiltered Yahoo ADP is a blend across every Yahoo
  league shape, dominated by 10- and 12-team default-scoring public leagues.

**Rankings, as opposed to ADP.** `[SECONDARY]` The players collection supports
`sort=` with values `{stat_id} | NAME | OR (overall rank) | AR (actual rank) | PTS (fantasy
points)`, but the `YFAR` guide records `sort` as **league-context only**. `[ANALYSIS]` So a call
against the founder's own Westwood league key *could* return players in Yahoo's overall-rank order
as computed for that league — plausibly the very ordering the room is shown. **`[GAP]` The semantics
of `OR` are not established from Yahoo's own documentation** — whether it is the pre-draft Default
Rank, a season-to-date rank, or something else. Do not assume. `[SECONDARY]` Separately, the
`yahoo_fantasy_api` Python wrapper documents no rankings, ADP, or draft-analysis method at all, only
`draft_results`, `player_details`, `player_stats`, `percent_owned`, `free_agents`, `taken_players` —
so tooling coverage of the ADP path is thinner than the ADP path's existence implies.

**The three blockers, and why this is a founder decision.** All three carry over from the prior
audit's `[VERIFIED]` reading of Yahoo's developer terms; **I did not re-verify them this session**
and flag that explicitly:

1. `[VERIFIED — prior audit, not re-verified]` Yahoo user data "not explicitly identified as being
   storable indefinitely" must be deleted **within 24 hours**. `[GAP]` **Whether aggregate ADP counts
   as "Yahoo user data" is still unresolved, and it decides whether a dated Yahoo ADP snapshot may be
   stored at all.** For a project whose entire ADP strategy rests on point-in-time snapshots being
   permanently unrecoverable if missed, an unresolved 24-hour deletion clause is not a detail — it is
   the whole question.
2. `[VERIFIED — prior audit, not re-verified]` No deriving income from the APIs without written
   permission. Currently satisfied (private, single-user), void on any second user — the same
   condition already attached to D-020/D-021.
3. `[VERIFIED — prior audit, not re-verified]` May not be used in a product competing with Yahoo's
   own. **Yahoo ships a draft assistant (Draft Scout, §2). This project is a draft assistant.**
   `[ANALYSIS]` That clause is squarely on point and is not something an agent should reason its way
   past. It is a founder call, and arguably a lawyer's.

`[ANALYSIS]` Blockers 1 and 3 together mean the OAuth path is **not** the clean "sanctioned channel"
that `CLAUDE.md` §10's preference might suggest at first glance. §10 prefers OAuth *over browser
automation*; it does not make an OAuth path automatically permissible.

---

## 5. Q4 — What the founder can get himself, manually

He is a league member with a logged-in browser. Realistically available to him, no automation:

| Artifact | Where | Effort | Value | Tag |
|---|---|---|---|---|
| **His league's Pre-Draft Rankings page** — Yahoo's own ordering under Westwood's settings, in the "List of Players" column | Draft → Pre-Draft Rankings → "Edit My Pre-Draft Player Rankings" | Minutes. Screenshots, or select-and-copy if the list is plain DOM text | **Highest.** This is literally the ordering the room's default surface presents. Nothing else in this document substitutes for it | `[SNIPPET]` page exists and is editable/orderable |
| **The public Draft Analysis / ADP page** (`/f1/draftanalysis`) — average pick, % drafted | Public Yahoo fantasy page | Minutes per capture | High, and it is the *behavioural* number. But platform-wide, not Westwood-specific | `[SNIPPET]` |
| **Draft Central "Position Ranks" tab** | `/f1/draft?dktab=position_ranks` | Minutes | Medium — positional ordering | `[SNIPPET]` |
| **Draft Scout / VOLS output in a free mock draft** | Mock draft lobby | ~20–30 min per mock | Medium-high: `[SNIPPET]` Draft Scout is **free in mocks**, so he can see the paid assistant's actual recommendations without subscribing. `[SNIPPET]` Fantasy Plus also offers "Instant Mock Drafts" tailored to his league settings | `[SNIPPET]` |
| **Yahoo's published printable Top-300 / cheat sheet** | Yahoo Sports article, republished by SI and others | Minutes | Medium — but this is an *editorial* list, and `[ANALYSIS]` it is not necessarily the same object as the in-product Default Rank. Do not conflate them | `[SNIPPET]` |
| **Post-draft: the actual draft results** | His league's draft results page | Minutes | High, but arrives too late to inform the 7 September draft — it is *calibration* input, not draft-day input | `[ANALYSIS]` |

**What is not available that route.** `[VERIFIED]` I checked the best-known community tool in this
space, the `hgoodman/yahoo-pre-draft` Chrome extension: it **imports** a custom cheat sheet *into*
Yahoo's pre-draft interface — *"copy and paste player names from your custom cheatsheet and load them
into the Yahoo pre-draft interface"* — and does not export Yahoo's own ranking out. `[ANALYSIS]` The
ecosystem's tooling flows one way, into Yahoo. There is no known export path, which is consistent
with Yahoo not wanting one.

**Cost, honestly stated.** `[ANALYSIS]` A single screenshot pass of the Pre-Draft Rankings page and
the Draft Analysis page is perhaps 10–20 minutes of founder time, and it is **the same acquisition
pattern that produced the two artifacts `docs/pm/MEMORY.md` §4 names as existing only on his
machine**: the 2025 draft transcription and the half-PPR FantasyPros export. That precedent cuts both
ways and should be said: it works, and it also produces an artifact that is unreproducible and must
be committed immediately or it is lost. If this is done, **commit the raw capture the same day**,
alongside `data/raw/founder-export/`.

**One caveat on transcription.** `[ANALYSIS]` The 2025 draft transcription (n=160) went through a
quarantine table and is the sole basis for `DEFAULT_LAMBDA`. A hand-transcribed Yahoo top-200 would
carry the same error surface. If it is done, capture the screenshots as the archival artifact and
treat any typed transcription as derived, exactly as the existing fixture does.

---

## 6. Q5 — How much of the room plausibly drafts off Yahoo's suggestions

**There is no good evidence, and I am not going to estimate it.** `[GAP]`

What I searched for and did not find: `[GAP]` any Yahoo-published or third-party usage statistic on
autopick rates, queue usage, Fantasy Plus attach rate, or the share of picks matching the platform's
displayed ordering. `[GAP]` Any academic measurement of anchoring on a platform's displayed list —
the one relevant open-access paper I found (*Drafting strategies in fantasy football*, Judgment and
Decision Making) returned HTTP 503 and was not read, so I cannot say whether it addresses this at all.

**What is structurally true instead, and is more useful than a percentage:**

- `[SNIPPET]` **The floor on anchoring is not zero, it is mechanical.** A queued player is the
  default pick when the clock expires, and when the queue is empty, autopick draws on Expert Rank.
  Any timed-out pick is a Yahoo-ordered pick by construction, regardless of that manager's
  intentions. `[GAP]` How often that happens in this league.
- `[SNIPPET]` **The paid assistant is not the default experience.** Draft Scout is subscriber-only in
  real drafts. `[ANALYSIS]` So the plausible modal free drafter is anchored on an *ordering plus ADP
  columns*, not on a roster-aware recommendation — which is the simpler and more tractable modelling
  target of the two.
- `[SNIPPET]` **Yahoo itself markets the gap.** Yahoo publishes an article titled *"Fantasy Football
  Cheat Sheet: Finding draft values based on Yahoo default rankings"*, and the surrounding coverage
  frames default rankings as inefficient and something to leverage against opponents who use them as
  their research. `[ANALYSIS]` A platform publishing "here is how to beat our own default list"
  presupposes that a meaningful share of its users draft off that list. That is an inference about
  Yahoo's beliefs, not a measurement of behaviour, and it should not be converted into a number.
- `[SNIPPET]`/`[SECONDARY]` Platform-level scale figures surfaced (a "7 million users" figure; a
  Sensor Tower August 2025 MAU split of ESPN 48% / Sleeper 33% / Yahoo 18%). **These do not answer
  the question asked.** They are platform popularity, not in-draft behaviour, and applying them to a
  10-person room would be a category error. Recorded only so nobody re-finds them and mistakes them
  for an answer.

**Sample-quality note, which is the useful part here.** The founder's own read — "some will have
their own boards (Kione Sanders for sure), others will rely at least for ideas on the Yahoo board" —
is **the best evidence available on this specific question, and its n is 1 observer over ~9
observed managers, self-reported, unblinded, and from an interested party.** `[ANALYSIS]` It is also
almost certainly better than any external statistic would be, because the question is about *this
room*, and no external source is about this room. The right move is to record his read as what it is
— a named, dated, single-observer prior — rather than either discarding it for lacking rigour or
laundering it into a percentage. If he can label each of the nine managers as
`own-board / mixed / platform-default / unknown` from memory before the draft, that is a real,
cheap, pre-registered observation that can be checked against the actual pick sequence afterwards.
**That is worth more than anything else in this section**, and it must be captured *before* the
draft or it is contaminated by hindsight.

---

## 7. Sample quality of this research

Fifteen-odd sources consulted collapse into far fewer independent units, and saying so is the point:

| Unit | Members | Effective n |
|---|---|---|
| **Yahoo's own product documentation** | help.yahoo.com SLN6287 and siblings, sports.yahoo.com articles, AOL mirrors | **1, and I could not read any of it.** Every §2/§3 claim traces back through search synthesis to essentially one or two Yahoo help pages. Four "independent" searches agreeing is four reads of the same page, not four sources |
| **Third-party Yahoo API wrappers** | `YFAR` (R), node wrapper docs, `yahoo_fantasy_api` (Python), Postman collection | **2–3 genuinely independent.** They agree on `draft_analysis`'s four fields, which is real corroboration. They also all reverse-engineered from the same undocumented-to-me Yahoo surface, so a shared error is possible |
| **Fantasy-media commentary on Yahoo ADP** | FantasyLife, FantasyLabs, FTN, RotoWire, DraftSharks | **1 decision unit, 0 fetched.** All are selling the same product — "beat Yahoo's default list" — which makes them structurally motivated to assert that the list is beatable. None was read this session |
| **In-repo corroboration** | `data/leagues/ethans_expert_league.json` | **1, and it is the only `[VERIFIED]` scoring evidence in this document** |

**Non-representativeness to flag even though it points the way we expected:** the one hard,
verifiable fact I obtained about Yahoo's default scoring came from **inside this repo**, not from the
web. That is convenient and it agrees with the web snippets — which is exactly when it deserves
scrutiny. The in-repo file is a transcription of *one* Yahoo league's settings, made by this project,
and its provenance chain (a screenshot, transcribed, with a founder override already applied to the
team count per `CURRENT-STATE.md`) is not independent of this project's own assumptions. It is
strong evidence that Yahoo default football scoring is half-PPR with no yardage bonuses. It is
**not** evidence about how Yahoo computes ranks.

---

## 8. Gaps, listed so nobody fills them by accident

1. `[GAP]` **Whether Yahoo's Default Rank prices bonus-threshold scoring settings.** The highest-value
   unknown here. **Cheap legal test available:** the founder opens his league's Pre-Draft Rankings
   page and checks whether the ordering differs from a Yahoo-default league he also belongs to
   (Ethan's Expert, Yahoo 834236, same 10 teams, no bonuses). If the two orderings are identical,
   answer (b) — Yahoo ignores the bonuses — and the edge is real. Minutes of his time, no automation,
   no ToS question. **This is the single recommended follow-up.**
2. `[GAP]` Whether the free Yahoo draft room shows tiers, positional-need prompts, or a live draft
   grade.
3. `[GAP]` Whether Yahoo's `draft_analysis` ADP can be filtered by scoring format or league size.
4. `[GAP]` Whether aggregate ADP falls under Yahoo's 24-hour user-data deletion clause. Unchanged
   from the prior audit; still decides whether Yahoo ADP snapshots are storable at all.
5. `[GAP]` The semantics of the API's `sort=OR` ("overall rank") — whether it is the pre-draft
   Default Rank.
6. `[GAP]` What a league-scoped `draft_analysis` returns for a league that has not yet drafted.
7. `[GAP]` Any usage statistic on autopick rate, queue usage, or Fantasy Plus attach rate.
8. `[GAP]` Whether Yahoo's published printable Top-300 is the same list as the in-product Default
   Rank.
9. `[GAP]` Whether the FantasyPros browser extension's Yahoo integration implies anything about the
   Yahoo draft client's DOM — its support article returned HTTP 403 and I could not determine whether
   that was origin or proxy.
10. `[GAP]` Yahoo Fantasy Plus's exact 2026 price. `[SNIPPET]` ~$2.92/month billed annually is what a
    search synthesis reported; no pricing page was read.

---

## 9. What this implies for the project, stated as options not decisions

`[ANALYSIS]` throughout this section.

1. **Keep `mfl_proxy` exactly as it is.** Nothing found is a replacement. The per-platform
   no-blending rule in `src/ingest_mfl_adp.py` is *reinforced* by this research, not challenged: the
   founder's insight is precisely that platform identity is a behavioural variable, and Yahoo's
   internal three-way split between Default Rank, Expert Rank, and ADP shows the variable is even
   finer-grained than `adp_source` currently models.
2. **Record Yahoo anchoring as a named, unmeasured uncertainty in the availability model** — with its
   sign, which is partly knowable (§0), and without a magnitude, which is not. Silently ignoring it
   is the failure mode to avoid; inventing a coefficient is the other one.
3. **Escalate the OAuth `draft_analysis` question to the founder as a decision**, not to an agent as
   a task. It needs answers on the deletion clause and the competing-product clause before any code
   exists. If he wants it pursued, the next step is *reading the API terms*, not writing a client.
4. **Ask for the two screenshots** (§5, §8 item 1). Lowest cost, highest information, zero ToS
   exposure, and it directly tests the exploitable hypothesis.
5. **Ask him to write down his per-manager anchoring read before 7 September** (§6). It is
   pre-registration in the sense `docs/statistical-guardrails.md` means it, and it is worthless after
   the fact.

**Note for the PM, since I could not do it myself:** the founder's verbatim observation quoted in the
task is a founder-expressed want and, per the agent operating rules in `CLAUDE.md`, needs capturing
via `python tools/founder_requests.py new`. **No Bash tool was available in this session**, so I
could neither run that tool nor commit these files. Someone with a shell must do both.

---

*Sources consulted are listed inline with their tags. No Yahoo-owned page was fetched; every
Yahoo-hosted host examined blocks this class of agent by name in robots.txt, and that block was
honoured rather than routed around.*
