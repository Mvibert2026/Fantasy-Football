# 2026-07-29 — researcher — Yahoo in-draft assistant

**Role:** researcher · **Type:** research only, no build, no ingestion, no data collection
**Output:** `docs/research/yahoo-draft-assistant-2026-07-29.md`

## Task

Answer five questions about Yahoo's in-draft assistant: what a drafter sees on the clock, what
rankings it draws on and under what scoring format, whether ADP/ranks are obtainable through the
official OAuth API, what the founder can get manually as a league member, and how much of his room
plausibly anchors on the platform's suggestions.

## Premise check

Checked the instruction against the repo before acting, as required. It holds:

- `docs/pm/MEMORY.md` §4 records ESPN / Yahoo / CBS as having "explicit written prohibitions on
  automated collection." Not lifted.
- The 2026-07-29 FFC unblock is FFC-specific in the same section and does not extend to Yahoo.
- The task's characterisation of `src/ingest_mfl_adp.py`'s docstring is accurate — it does state
  that "drafters pick off their own platform's displayed ranks, so ADP is a per-platform
  behavioural variable" and that platforms must never be blended.

No contradiction found. Proceeded.

## Boundary honoured

Every Yahoo-owned host examined names `anthropic-ai`, `Claude-Web` and `ClaudeBot` with
`Disallow: /` — `help.yahoo.com`, `sports.yahoo.com`, `www.aol.com` (which mirrors Yahoo Sports
articles), and `football.fantasysports.yahoo.com` per the prior audit. `developer.yahoo.com` has no
AI-agent block but its fantasy guide 308-redirects to the blocked `sports.yahoo.com/developer`.

**No Yahoo fantasy page was fetched. No scraper was built, tested or designed.** Yahoo's own product
and developer documentation is therefore unreadable by this agent class, which caps every claim
about the Yahoo product at `[SNIPPET]` or `[SECONDARY]`. There is no `[VERIFIED]` claim about the
Yahoo draft room in the report, and there cannot be one from here.

Also deliberately did **not** fetch a Fantasy Life article whose path (`/articles/`) is outside that
site's robots disallow list, because the prior audit records Fantasy Life as blocked and its ToS as
`[GAP]`. Chose consistency with the recorded block over a path-level loophole; flagged in the report
rather than resolved unilaterally.

## Findings, in one paragraph each

**The founder's insight is correct and under-specified.** "The Yahoo board" is at least three
different numbers: a **Default Rank** computed from the league's own scoring settings, an **Expert
Rank** computed from Yahoo's *default* scoring which also drives autopick, and a platform-wide
**ADP**. Which one a drafter anchors on changes the model. Treating them as one object would
reproduce the exact blending error `ingest_mfl_adp.py` exists to prevent.

**The scoring gap is narrower on receptions and wider on bonuses than expected.** Yahoo's default
football scoring is already half-PPR — corroborated `[VERIFIED]` in-repo from
`data/leagues/ethans_expert_league.json`, which carries `receptions: 0.5` and empty `bonuses: []`
arrays on all three yardage categories. So Westwood's wedge against the room's anchor is not PPR
format; it is the **stacking yardage bonuses**, plus INT −2 vs −1, no kicker, and two flex.

**The highest-value open question is a `[GAP]` and I left it as one.** Whether Yahoo's
league-scoring-aware Default Rank actually prices bonus thresholds is unestablished. A threshold
bonus is a nonlinear function of a per-game distribution and cannot be computed from a season-total
projection, so there is a real chance Yahoo ignores bonus settings entirely — in which case the whole
room, including the league-aware surface, under-prices ceiling in a league that pays for it. That is
directly exploitable and is **not** to be acted on until confirmed. A cheap legal test exists: the
founder compares his Pre-Draft Rankings ordering in Westwood against the same page in Ethan's Expert
(also Yahoo, also 10 teams, no bonuses). Identical orderings would answer it.

**One Yahoo number is obtainable within the rules, and it is the behavioural one.** `draft_analysis`
(`average_pick`, `average_round`, `average_cost`, `percent_drafted`) is confirmed `[SECONDARY]` on
three mutually independent third-party API wrappers fetched this session — upgrading the prior
audit's unconfirmed `[SNIPPET]`. It is real Yahoo drafter behaviour, and OAuth is the channel
`CLAUDE.md` §10 prefers. Three blockers stop it being a green light: the 24-hour user-data deletion
clause (`[GAP]` whether aggregate ADP falls under it — this decides whether snapshots are storable at
all), the no-competing-product clause (Yahoo ships a draft assistant; so does this project), and
`[GAP]` whether the figure can be filtered to 10-team half-PPR. Founder decision, not an agent one.

**Draft Scout is paywalled during real drafts**, free only in mocks. So the modal free drafter is
anchored on an *ordering plus ADP columns*, not a roster-aware recommender — a simpler and more
tractable modelling target. Its metric, VOLS (Value Over Last expected Starter), is the same family
as this project's replacement-level VBD, which means positional revaluation — per `docs/pm/MEMORY.md`
§1 the board's only edge channel — is partially competed away against any manager who pays.

**Q5 is a `[GAP]` and I did not fill it.** No usage statistic on autopick rates, queue usage or
Fantasy Plus attach rate was found. Platform MAU-share figures surfaced and are recorded only so
nobody mistakes them for an answer — they are platform popularity, not in-draft behaviour, and
applying them to a 10-person room is a category error. The genuinely useful observation is that the
founder's own read is n=1 observer over ~9 managers, and is still the best evidence that exists about
*this room*; the recommendation is that he label each manager `own-board / mixed / platform-default /
unknown` **before** 7 September, which makes it a checkable pre-registration rather than hindsight.

## Sample quality

The ~15 sources consulted collapse into roughly four independent units. All §2/§3 claims about
Yahoo's rank types trace back through search synthesis to one or two Yahoo help pages — four
agreeing searches are four reads of the same page, not four sources. The fantasy-media commentary
class (FantasyLife, FantasyLabs, FTN, RotoWire, DraftSharks) is one decision unit and is structurally
motivated to assert that Yahoo's list is beatable; none was read. The only `[VERIFIED]` scoring
evidence came from inside this repo, which is convenient and agrees with the web — flagged as exactly
when it deserves scrutiny, since its provenance is not independent of this project's own assumptions.

An additional caveat recorded in the report: most `[SNIPPET]` items here are the search tool's own
*synthesis* over excerpts, i.e. a model paraphrase of a page neither of us rendered. That is weaker
than a normal `[SNIPPET]` and is stated as such.

## Environment notes

- **No Bash tool in this session.** Tools available were Read, Write, Edit, Glob, Grep, WebSearch,
  WebFetch only. Consequences: **the two files written could not be committed**, and the founder's
  verbatim observation quoted in the task could not be captured via
  `python tools/founder_requests.py new` as the agent operating rules require. Both need someone with
  a shell.
- Three fetches returned HTTP 403 (`fantasypointcalculators.com`, `support.fantasypros.com`,
  `ftnfantasy.com`) and one returned 503 (`sjdm.org`). Without a shell I could not run the proxy
  status check `docs/environment.md` and the environment notes describe, so I could not determine
  origin-side vs. proxy-side. Recorded as unretrieved, **not** as blocked.
- `docs/environment.md` is written for the founder's Windows machine (conda interpreter path,
  `PreToolUse` hook). Neither applies in this cloud container.

## Files written

- `docs/research/yahoo-draft-assistant-2026-07-29.md` (the deliverable)
- `docs/status/2026-07-29-researcher-yahoo-assistant.md` (this file)

Nothing else was modified, per instruction. No handoff thread was opened or replied to — the task
named none, and the three threads standing open to `researcher` (054, 057, 070) are unrelated to it
and were deliberately not absorbed into this session.
