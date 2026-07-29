# Competitive UX — what draft tools do well, badly, and not at all

**Date:** 2026-07-29 · **Role:** researcher · **Scope:** research only. Nothing was built. No code,
no ingestion, no design artifact.

**Commissioned by:** the founder's question — *"features of other apps out there to see if we want to
include them, or looking at good UI/UX features"* — ahead of a possible frontend overhaul he has not
committed to. Multi-league and multi-slot treated as requirements throughout, per FR-034.

| Tag | Meaning |
|---|---|
| `[VERIFIED]` | I fetched the page this session and read it. For a vendor's own marketing page this verifies **that they publish the claim**, not that the feature works |
| `[SNIPPET]` | Seen only in a search excerpt or the search tool's synthesis; the page did not render |
| `[SECONDARY]` | Third-party reporting only |
| `[GAP]` | Could not establish. Never filled with a plausible substitute |
| `[ANALYSIS]` | My own reasoning over tagged facts, labelled so it is never mistaken for a fetched claim |

---

## 0. Conclusion, first

### The three worth stealing

**1. Publish the uncertainty you already compute, at the point of decision — Draft Sharks proves a
paying market tolerates it.** `[VERIFIED]` Their Injury Guide expresses risk as a probability, gives
a continuous "projected games missed," and ships **"80% and 95% confidence prediction limit
references displayed alongside individual player projections."** It publishes its own error —
*"the mean absolute error is 1.610; meaning, on average, our predictions are off by about a game and
a half"* — plus ROC-AUC 0.809, R² 0.401, and a binned calibration check showing *"the higher our
predicted probability of injury the higher the actual rate of injury for the group is."*
`[VERIFIED]` Separately, their draft product shows **three projection numbers per player** — their
baseline, a consensus of 38 other sites, and a ceiling/floor pair. `[ANALYSIS]` This project already
computes `vbd_lo`/`vbd_hi` and ships `adp_min_pick`/`adp_max_pick`, and the ideas-inbox already
records that *"Josh Allen's CI [57.0, 155.2] overlaps 29 of the top 40 players"* while the point
estimate is what gets read. Draft Sharks is the existence proof that the honest version is
shippable. The specific steal is **not** "add error bars" — it is *"not distinguishable from ranks
X–Y"* rendered on the row, next to the rank, in the same visual weight as the rank.

**2. Practising from a different draft slot is a first-class prep loop, not a settings screen.**
`[VERIFIED]` FantasyPros' own guidance: *"Draft from a specific slot if your draft order is already
set, or select at random each time to prepare to draft from every pick."* The randomise-the-slot
option is the interesting half — it reframes slot from *a configuration value you set once* into
*a thing you rehearse across*. `[ANALYSIS]` FR-034 asks for a slot control; this says the control is
worth less than the loop around it. For a founder with three leagues and three different slots, the
prep question is not "what is my board at slot 3" but "which of my picks are fragile across slots."

**3. Model your actual league-mates, not a generic opponent.** `[VERIFIED]` FantasyPros ships
**Draft Intel** — *"Discover key insights and pattern for your league-mates"* — and feeds it into
mock bots so a mock *"feels like you're drafting against your real league mates."* `[VERIFIED]` They
also let you *"update the Position Values to force the bots to overvalue or undervalue specific
positions"* and customise bot logic via a "Draft Against" setting. `[ANALYSIS]` This project holds
160 real picks from the 2025 Westwood draft and currently spends them entirely on calibrating
`DEFAULT_LAMBDA`. `docs/test-registry.md`'s own known-gaps list says every backtest *assumes
opponents draft to ADP with noise*. Nine named humans with one observed draft each is a thin sample —
but it is the *right* sample, and it is already on disk.

### The three worth avoiding

**1. Do not spend an overhaul on air.** `[SECONDARY]` ESPN's 2025 redesign is the category's
cautionary tale and the complaints are specifically about density, not taste: *"Font is atrocious and
it is so zoomed in, can barely see any of the roster"*; *"Everything just blends together"*; *"The
only reason people chose to use ESPN over any other app is because the interface was cleaner."* This
repo's design brief already names ESPN 2025 for exactly this reason — the new evidence is the
verbatim user language, which is sharper than the paraphrase we were working from.

**2. Do not build a "recommended / trending players" feed.** `[SECONDARY]` The same ESPN backlash
names it directly: *"the 'trending up' and 'recommended players' has to go. Owners need to do their
own research."* `[ANALYSIS]` This is the sharpest voice-of-customer finding in the pass, because it
is the one place users rejected *added intelligence* rather than lost information. The lesson is not
"users hate recommendations" — FantasyPros and Draft Sharks sell them successfully — it is that an
**unrequested, un-sourced, ambient recommendation** reads as the platform interfering. A
recommendation that shows its derivation is a different object from a feed that asserts.

**3. Do not build live platform sync.** `[SNIPPET]` FantasyPros maintains dedicated help articles
titled *"My Draft Assistant crashed, won't load or there was a server error during my draft. What do
I do?"* and *"'Waiting for draft sync...' error message — how to fix during a live draft (ESPN,
Yahoo, Sleeper, etc.)"*; ESPN sync requires a Chrome extension. `[VERIFIED as their claim]` A rival
vendor's comparison says of Footballguys: *"Technology can be buggy at times, particularly during
drafts. That includes syncing issues, and overall app stability at busy draft times."* `[ANALYSIS]`
Sync is the category's single most reliable failure mode, it fails at the exact moment the product
matters, and for this project it is **also** ToS-blocked on Yahoo, ESPN and CBS. Manual entry is
already built and already keyboard-driven (thread 036); it should be positioned as the design, not
as the fallback.

### Does any of this change the case for an overhaul?

**No — it weakens it, and I think that is the useful answer.** `[ANALYSIS]`

The prior competitive UX pass (cited in `docs/design-handoff/HANDOFF-NOTES.md`) already concluded
*"the fix is token-level, not a redesign,"* scored our visual polish 5/10 and light mode 4/10, and
that work then **shipped** — two type roles, elevation surfaces, radius discipline, accent
discipline, colourblind redundancy. Nothing I found this session contradicts that conclusion, and the
ESPN case says the marginal return on visual investment in this category is *negative* past a
threshold we appear to have crossed.

What the evidence does support is a **scoped structural change**, which is a different project from
an overhaul:

| | Change | Why the evidence supports it |
|---|---|---|
| 1 | League and draft slot become selectable first-class state, with a rehearse-across-slots loop | FR-034; FantasyPros' randomise-slot guidance `[VERIFIED]`; three leagues today |
| 2 | Uncertainty surfaced on the row, not in a detail sheet | Draft Sharks' confidence limits `[VERIFIED]`; our own overlapping-CI finding |
| 3 | Three or four on-the-clock affordances (see §3.1) | Convergent across FanDraft, Draft Sharks, Sleeper `[VERIFIED]` |

**Cost asymmetry, stated plainly.** An overhaul re-opens every screen and re-incurs the porting risk
this project has already been burned by once — `docs/operating-model.md` records a 38K-character
spec port that hit a hard stop at ~97% usage *and self-reported inaccurately*. Items 1–3 above are
additive and independently shippable. If the founder wants an overhaul anyway, the honest framing is
that it is a **preference**, not a finding, and it should be recorded as one.

---

## 0.5 Premise challenges — three, none blocking

Raised before acting, per the dispatch's instruction. None is a contradiction that warrants halting;
all three should be visible to whoever reads this.

**(a) The prior work is not where the dispatch says, and one piece of it does not exist in the repo
at all.** The thread-061 competitor audit is at `docs/research/competitor-recommendation-audit-2026-07.md`,
not `docs/reviews/`. More importantly: `docs/operating-model.md`'s budget table logs a completed
**"Competitive UX + platform + Reddit research"** pass, and at least six documents cite its
conclusions (`docs/design-handoff/HANDOFF-NOTES.md` §"What changed this round",
`docs/design-handoff/README.md` Addendum 3, `docs/handoffs/030`, `docs/handoffs/047`,
`docs/adr-drafts/ADR-A`, `docs/screenshot-checklist.html`). **The artifact itself is not in the
repository** — I searched the whole tree including every agent worktree. So "build on it, do not
re-derive it" is only partly executable: I can build on the conclusions as *quoted by the documents
that consumed them*, which is what §0 does, but I cannot see its evidence, its tags, or its gaps.
`[ANALYSIS]` This is the second time this project has bought the same research twice, and it is a
librarian-class problem, not a researcher-class one.

**(b) A frontend overhaul is outside written Phase 1 scope.** `CLAUDE.md` §2 says Phase 1 is the
backtest harness and ranking algorithm, and *"Not the draft tool"*; §8 requires escalation when scope
expands beyond Phase 1. The draft tool exists and is live anyway, so the spec and reality already
disagree — that is a pre-existing condition, not something this dispatch created. FR-034 has already
flagged the adjacent version of it (*"That is a change to the standing spec and should be made
deliberately rather than drifted into"*). **Research is safe; committing to an overhaul is the
escalation point, and it needs a CLAUDE.md amendment rather than a sprint.**

**(c) Multi-league is not a contradiction with `CLAUDE.md` §1.** §1 says *single user, local only*.
One founder with three leagues is still one user, and §4 already mandates `league_id` on every table.
League 2 is built. Nothing here needs re-deciding. (`local only` is separately already false — the
app is on the internet — and `CURRENT-STATE.md` records that as a founder decision.)

---

## 1. Access record — what I could and could not fetch

Load-bearing, because it caps the confidence of everything below.

| Host | Status | Consequence |
|---|---|---|
| `sleeper.com`, `support.sleeper.com` | `[VERIFIED]` `User-Agent: * / Allow: /`; support disallows only 3 admin paths, `Crawl-delay: 1` | **Fetched.** Sleeper is the only major platform whose own product documentation I could read |
| `draftwizard.fantasypros.com` | `[VERIFIED]` in thread 061: `Allow: /` (GPTBot blocked, not this agent) | **Fetched** |
| `blog.fantasypros.com` | `[VERIFIED]` allows all but `/ghost/`, `/email/`, `/members/api/`, `/r/`, `/webmentions/`, `/.ghost/` | **Fetched** |
| `support.fantasypros.com` | `[VERIFIED]` in thread 061: HTTP 403 to this fetcher | **Not fetched.** Everything about Multi-League Assistant is `[SNIPPET]` |
| `www.draftsharks.com` | `[VERIFIED]` `User-agent: *`, `Disallow:` (nothing) | **Fetched** — the richest source in this pass |
| `www.fandraft.com`, `www.stackedfantasy.com`, `borischen.co` | Fetched without incident | **Fetched** |
| `apps.apple.com` | Fetched | **Fetched.** User reviews on Apple's own platform, not the vendor's |
| `www.reddit.com` | **Refused by the tool**: *"Claude Code is unable to fetch from www.reddit.com"* | **Blocked. Recorded and stopped.** No cache, no proxy, no alternate reader. Every Reddit-flavoured claim below is `[SNIPPET]` via search synthesis at best, and mostly absent |
| `espn.com` / `support.espn.com` | Standing block (automated collection prohibited) | **Not attempted.** ESPN product behaviour is `[SECONDARY]` only |
| Every Yahoo-owned host | `[VERIFIED]` in `docs/research/yahoo-draft-assistant-2026-07-29.md`: `ClaudeBot`/`Claude-Web`/`anthropic-ai` each `Disallow: /` | **Not attempted** |
| `cbssports.com` | Standing block (2005 ToS: *"Copying or storing any part of the Service is expressly prohibited"*, per thread 009) | **Not attempted** |
| `forums.footballguys.com` | Recorded blocked (robots) in thread 009's audit | **Not fetched**, though a relevant thread surfaced in search |
| `www.fantasylife.com` | `/articles/` is not disallowed, but the prior audit recorded Fantasy Life as blocked | **Deliberately not fetched** — same consistency choice the Yahoo audit made. A tiers article of theirs surfaced and was left unread |
| `www.17lands.com` | `[VERIFIED]` robots allows the pages I wanted; **the FAQ rendered as the single string "17Lands.com"** | Unretrieved content, not blocked. Their uncertainty treatment is `[SNIPPET]` |
| `underdogfantasy.com` | 301 → `underdogsports.com`; robots.txt content could not be established | **Not fetched.** Underdog claims are `[SNIPPET]`/`[SECONDARY]` |
| `play.google.com` | Page returned navigation chrome only | Unretrieved content |
| `footballabsurdity.com/beersheets/` | Fetched; page carries only *"BeerSheets are coming by training camp"* plus download links | **`[GAP]` on what a BeerSheet contains.** I did not download the PDF |

**Fetching vs. redistributing, answered separately as required.** Everything in this document is
*design intelligence*: descriptions of interactions and published claims. **No competitor's data is
proposed for ingestion, storage, or display.** The distinction matters here in one direction only —
several vendors' ToS prohibit reproducing their *content*; none of them can prohibit us from noticing
that a timer is the only thing on screen that moves. No numeric value from any competitor appears in
this document as a candidate product input.

---

## 2. Sample quality — read this before reading the findings

**Effective n is much smaller than the source count.**

| Unit | Members | Effective n |
|---|---|---|
| **Vendor self-description** | Draft Sharks, FantasyPros, STACKED, FanDraft, Sleeper support | **5, but all one *kind*.** Every one is the vendor describing its own product. Not one behavioural observation of a tool under a real clock appears in this document |
| **Vendor-authored competitor comparison** | `draftsharks.com/kb/best-fantasy-football-app` | **1, and structurally conflicted.** It is a competitor grading competitors while selling against them. Its criticisms of Footballguys/Sleeper/FFPC are the most quotable material in the pass and the least trustworthy. Tagged `[SECONDARY]` and attributed by name every time |
| **Voice of customer** | SI (ESPN backlash), PFN (outage), Apple App Store review text | **2–3 weak units.** Reddit — the single richest VoC source in this category — was **refused by the tool**. The App Store surfaces a handful of reviews chosen by Apple, skewed positive by construction (ESPN 4.8/1.9M, FantasyPros 4.8/80K, Sleeper 4.7/250K) |
| **Independent methodology exemplars** | Boris Chen, 17Lands | **2, one of which did not render** |

**Three non-representativeness flags, including where the sample agrees with what we expected:**

1. **The ESPN density finding is exactly what this repo already believes, which is when it deserves
   the most scrutiny.** `docs/design-brief.md` §4 already names ESPN 2025. I went looking for it and
   found it. The verbatim quotes are real `[SECONDARY]`, but I did not find a *disconfirming* source
   and I did not look as hard for one. A fair reading is that this is corroboration, not
   independent evidence.
2. **I found no behavioural evidence at all.** Thread 061 said the same and it is still true: nobody
   in this project has watched any competitor tool run under a real clock. Everything about
   on-the-clock behaviour below is a vendor's description of its own product.
3. **The App Store review sets are curated by Apple and cannot be treated as a survey.** Where a
   review is quoted below I have flagged where I could not tell a genuine user review apart from
   release-notes or editorial text on the same page.

---

## 3. Q1 — what the good ones actually do well

### 3.1 Under the clock

`[ANALYSIS]` Four mechanisms recur, and they are all about **removing decisions rather than adding
information**.

**(a) Exactly one thing moves, and it is the clock.** `[VERIFIED]` FanDraft — a product whose entire
job is the draft-room display — ships *"On-the-clock presentation announcing the team currently
drafting,"* *"Live on-deck & up-next ordering,"* a *"Fully customizable"* timer you can
*"start/pause at any time, and audible alerts,"* and a *"Streaming ticker … a live news crawl of all
of the latest picks."* `[ANALYSIS]` Notice the division of labour: the **timer** owns motion, the
**ticker** owns novelty, and the board owns state. Three separate channels, none of them competing
for the same attention. A single "everything updates" board violates this by making every change
equally urgent.

**(b) Your turn is announced before it arrives.** `[VERIFIED]` FanDraft's *"on-deck & up-next"* is
the mechanism. `[ANALYSIS]` This is the interaction thread 059 (on-deck recommendations, open to
backend+frontend) is already reaching for, and the competitive evidence is that the *display* of it
is a solved, conventional pattern — the hard part is only the computation.

**(c) The default pick is pre-committed, so an expired clock is never a disaster.** `[VERIFIED]`
Sleeper: the Draft Queue *"is a feature that is available to you during and leading up to your
league's draft"* and *"in case you cannot be present for your pick, or your timer runs out, the CPU
will autopick from your queue."* `[SNIPPET]` Yahoo's equivalent (per
`docs/research/yahoo-draft-assistant-2026-07-29.md`): *"When a player is queued, that means he is
your default pick if you run out of time on the clock."* `[ANALYSIS]` The queue is doing double duty
— it is a shortlist *and* an insurance policy — and the second role is what makes people maintain it.
This project's Queue/Watchlist panel exists; whether it carries the "this is what happens if you do
nothing" semantics is a design question worth asking explicitly.

**(d) Recompute is instant and bounded to a small number.** `[VERIFIED as their claim]` Draft
Sharks: *"The Draft War Room does it in less than a second. Every time a player is drafted,"* and the
output is *"Top 5 draft recommendations — plus a wealth of other useful info."* `[ANALYSIS]` Five,
not fifty and not one. Thread 061 already noted FantasyPros' opposite choice — a single green
highlighted player — and called it *"unambiguous under time pressure."* Both are defensible; what
neither does is show twenty near-equal scores. **The relevant open item here is thread 060
(draft-time compute architecture): a sub-second budget is the industry's stated bar, and this
project's availability model has never been timed against it.** `[GAP]` What this project's
recompute actually costs per pick is not measured anywhere I could find.

**(e) Mistakes are cheap.** `[VERIFIED]` Sleeper's headline draft feature is *"unlimited pick
changes, pauses, and undos."* `[VERIFIED]` FantasyPros: *"Redo mock draft picks on the fly to see
which draft strategies work best."* `[ANALYSIS]` Undo is already built here (Backspace on an empty
field, thread 036) and was implemented event-sourced (ADR-046 / thread 040 amendment). That is ahead
of the category; it is worth making the affordance visible rather than only discoverable.

**What nobody does that would help under a clock, and I looked:** `[GAP]` I found no product that
shows *how long you have been deliberating* or that changes its display as the clock runs down
(e.g. collapsing from five candidates to one at ten seconds). If it exists, my method did not surface
it.

### 3.2 Density

**The best density idea in the category is structural, not typographic: make the board a grid, and
let the grid be the opponent model.**

`[VERIFIED]` Sleeper's own explanation of why they built it that way: they designed the interface
*"to be a board so you can easily see when position runs are happening and the positional needs of
your opponents,"* and it *"can be cast to your big screen with the option of dark mode as well."*
`[VERIFIED as their claim]` Draft Sharks describes the same object as *"the Draft Log & Grid,"*
showing your league's draft order, every team's selections in real time, and other teams' roster
needs. `[SNIPPET]` ESPN added a "Draft Board" view for the same reason — *"an easy way to view all
picks for all teams in one view."*

`[ANALYSIS]` The grid is dense in a way a list cannot be, because it encodes **three variables in a
2-D layout for free**: who picked (column), when (row), and what position (colour). A list of picks
carries the same data in more space and answers *"is there a run on"* far worse. This project has an
Opponents tab built on roster cards; a snake grid is a different and complementary object, and I did
not find one in the design handoff's screen list. `[VERIFIED]` The physical-draft-board convention it
imitates — *"a color-coded peel-and-stick label goes up on the board by position"* — is the reason
it reads instantly to anyone who has drafted in a room.

`[VERIFIED]` **The counter-case is Sleeper itself, and it is the most useful negative finding in the
pass.** Sleeper is the category's design darling (4.7 / 250K ratings; *"There's no clunky interface
or random ads slowing you down"*) and its information layer is thin: *"It's almost impossible to find
simple things like the waiver wire order, and other basic things that are essential"*; *"Little to no
player outlooks, rarely game recaps."* `[VERIFIED]` And it *"cannot hold custom rankings at all"* —
their own support page: *"Unfortunately, there is no direct method or feature to allow you to upload
or create pre-draft rankings … This is something we hope to build in the future."*

`[ANALYSIS]` So the category's two poles are **ESPN, which had density and spent it on air**, and
**Sleeper, which has beautiful chrome and never had the density.** This project's stated position —
*"premium means better organised, not roomier"* — is a third position that neither occupies. That is
a genuine differentiation opportunity and it argues *against* an aesthetic overhaul, because the
aesthetic pole is taken and is not where the complaints are.

**Tiers as a density device.** `[SNIPPET]` The category's own argument for tiers is not that they are
prettier but that *"a ranking set forces you to choose who is better between Jefferson and Reagor,
whereas tiers place them in a similar cohort. Rankings imply precision that does not exist. Tiers
embrace that uncertainty,"* and that they *"show you where the cliffs are."* `[VERIFIED]`
FantasyPros' Cheat Sheet Creator sells exactly this: *"Combine rankings from 100+ experts into one
cheat sheet with tiers, notes and sleepers."* This project already ships position-scoped tier bands
(thread 058) — the finding is that **tiers are the category's accepted uncertainty display**, which
matters for §3.3.

### 3.3 Uncertainty — someone does do it, and does it better than us

The dispatch anticipated that nobody does this. **That is wrong, and the exception is instructive.**

`[VERIFIED]` **Draft Sharks publishes calibration evidence for a shipped consumer feature.** From
their Injury Guide's methodology page:

- risk expressed as a **probability** (chance of an injury costing at least half a game) and a
  **continuous expected games missed**;
- **"80% and 95% confidence prediction limit references" displayed alongside individual player
  projections**;
- self-reported error: *"the mean absolute error is 1.610; meaning, on average, our predictions are
  off by about a game and a half"*;
- out-of-sample validation on 385 player-seasons: ROC-AUC **0.809**, log-loss **0.542**, R² **0.401**;
- a binned reliability check: *"the higher our predicted probability of injury the higher the actual
  rate of injury for the group is."*

`[ANALYSIS]` Thread 061 concluded *"no competitor found publishes calibration evidence"* and named
pre-registered calibration as this project's remaining defensible asset. **That conclusion needs
narrowing.** It is still true of *availability* modelling, where nobody publishes anything. It is now
false as a general statement: at least one vendor publishes out-of-sample metrics and a calibration
plot for a different prediction, and sells subscriptions on top of it. The differentiator is
narrower than 061 left it and should be restated as *"pre-registered calibration of the availability
model specifically"* — a claim this project still cannot make, at 1 of ~30 mocks.

`[VERIFIED as their claim]` Draft Sharks also shows **three projections per player — baseline,
38-site consensus, and ceiling/floor** — which is a range display sitting on the primary decision
surface rather than in a methodology page.

**Second exemplar, outside fantasy football entirely.** `[VERIFIED]` Boris Chen's tiers, free and
public since roughly 2013, run *"select expert ranking data from FantasyPros.com … into a statistical
clustering algorithm called a Gaussian mixture model. The algorithm finds players who are ranked
similarly and discovers natural tiers within the data."* The user-facing instruction is the part
worth stealing verbatim: **"When choosing between players of the same tier, flip a coin or go with
your gut. If experts are 50/50, there's no wrong choice."** `[ANALYSIS]` That single sentence does
what a confidence interval does, in language, at the moment of the decision, with no chart. It is the
cheapest uncertainty affordance found in this pass. `[GAP]` The visual form of his charts — whether
each player is drawn with a horizontal error bar spanning the expert-rank range — **could not be
established**: the output is a PNG (`fftiers/out/weekly-QB.png`) which my tools cannot read, the
GitHub README did not render, and I will not describe a chart I have not seen.

**Third, weaker.** `[SNIPPET]` 17Lands (Magic: the Gathering draft analytics, the closest structural
analogue outside sport) suppresses rather than annotates: *"When the sample size is too small to
determine the win rate … no values are displayed,"* and its letter grades are *"bands of 0.33
standard deviations"* from a centred mean. `[VERIFIED]` Their FAQ page rendered as the single string
"17Lands.com", so this is not corroborated at source.

**Where the mainstream sits.** `[GAP]`/`[ANALYSIS]` I found no evidence that ESPN, Yahoo, Sleeper or
Underdog display any uncertainty on any player anywhere. For Yahoo and ESPN I am blocked and cannot
check, so this is absence of evidence. For Sleeper, whose docs I *could* read, no ranges, tiers,
projections spread, or confidence treatment appears anywhere in the draft documentation — and they
do not ship custom rankings at all.

`[ANALYSIS]` **Net finding: uncertainty display is rare but not absent, it is commercially survivable
where it appears, and this project's specific version of it — probability-as-frequency, two numbers
never one — remains unmatched by anything I found.** The ten-dot frequency array is, as far as this
pass can tell, the single most differentiated UI element in the product. It should be defended in any
overhaul, not re-styled.

### 3.4 Multi-league and multi-slot

**Multi-slot.** `[VERIFIED]` FantasyPros' simulator: *"Draft from a specific slot if your draft order
is already set, or select at random each time to prepare to draft from every pick."* `[VERIFIED]`
The bots are configurable two ways — a "Draft Against" logic setting, and Position Values you can
*"force … to overvalue or undervalue specific positions."* `[ANALYSIS]` The design lesson is that
slot lives in the **pre-draft setup sheet next to teams and scoring**, not in an app-level settings
screen — it is a property of *this rehearsal*, not of *your account*. FR-034 is currently written as
"a control and the recompute path"; the competitive evidence says put it where the mock is
configured and make randomising it one click.

**Multi-league.** `[SNIPPET]` FantasyPros gates a **Multi-League Assistant** behind its MVP tier
specifically for users *"in 3 or more leagues"*, giving *"an overview of which players you have
rostered and on which teams/leagues"*, cross-league free-agent search, and an Auto-Pilot for lineups.
`[VERIFIED]` Their App Store page carries the text *"The ability to go through 3 different leagues in
one app is honestly game changing"* — I could not reliably distinguish user review from editorial
copy on that page and flag it rather than lean on it. `[VERIFIED]` STACKED sells *"Sync your teams
from ESPN, Yahoo, Sleeper, and more"* with *"weekly emails … personalized to every league."*

`[VERIFIED]` Sleeper's split is the cleanest primitive found and **this project already adopted it**
(it is in `docs/design-handoff/README.md` Addendum 3): the **Draft Queue is league-scoped and
draft-scoped**, the **Watch List is account-wide** — *"Watchlist is account-wide which means your
tracked players will be visible on all leagues, not for each league."* `[ANALYSIS]` That is the
correct generalisation of every multi-league question: for each piece of state, decide whether it
belongs to the account or to the league, and say so on screen. Board, slot, roster, queue → league.
Watchlist, notes, model version, preferences → account.

`[SECONDARY — a competitor's characterisation of Sleeper, not verified against Sleeper]` Draft Sharks
reports that Sleeper users find it hard to manage the *"compressed view for users with more than one
league."* `[ANALYSIS]` Worth one thing only: the multi-league failure mode in this category is
*cramming*, not *switching*. Nobody appears to have solved "show me the same player's standing across
my three leagues at once," and `[GAP]` I found no product that does it for a *draft* rather than for
in-season rosters.

---

## 4. Q2 — what they do badly, from customers rather than marketing

**Caveat first: this section is the weakest in the document.** Reddit was refused by the tool and it
is the category's main VoC channel. What follows is App Store review text, two news articles, and one
conflicted vendor comparison.

| # | Failure | Evidence | Tag |
|---|---|---|---|
| 1 | **Redesigning away information.** *"Font is atrocious and it is so zoomed in, can barely see any of the roster"* · *"Everything just blends together"* · *"The only reason people chose to use ESPN over any other app is because the interface was cleaner"* · *"this new update is a disgrace"* | SI, 2025-08-05 | `[SECONDARY]` |
| 2 | **Ambient recommendations users did not ask for.** *"the 'trending up' and 'recommended players' has to go. Owners need to do their own research"* | SI, 2025-08-05 | `[SECONDARY]` |
| 3 | **Failing at the moment of use.** ESPN's app stopped showing live scores during Week 15 of the fantasy playoffs, thousands of Down Detector reports: *"ESPN Fantasy not working during the fantasy playoffs, nice"* | Pro Football Network, 2025-12-11 | `[SECONDARY]` |
| 4 | **Draft sync breaking mid-draft.** Vendor help articles exist specifically for *"My Draft Assistant crashed … during my draft"* and *"'Waiting for draft sync…' error message — how to fix during a live draft"* | FantasyPros support article titles, via search | `[SNIPPET]` |
| 5 | **Slowness and mis-taps under pressure.** NFL Fantasy app reported *"super slow"*, player research *"takes ages"*, and taps intended as scrolls *"switch players instead of scrolling down"* | search synthesis | `[SNIPPET]` |
| 6 | **Beautiful and hollow.** Sleeper: *"almost impossible to find simple things like the waiver wire order, and other basic things that are essential"*; *"Little to no player outlooks"*; a commissioner regretting migrating a league because it *"taken away all of the fun things that made me want to bring my main league here"* | Apple App Store page for Sleeper | `[VERIFIED]` (that the text is on the page) |
| 7 | **Feature volume as its own defect.** *"The extensive amount of features and data might be overwhelming"* — said about Draft Sharks, by Draft Sharks | draftsharks.com | `[VERIFIED]` (self-criticism, so unusually credible) |
| 8 | **Headline number that ignores your roster.** FantasyPros' Expert Voting % is a vote share that *"suggests who the experts like best without considering your roster and team needs"*, with the roster-aware signal shipped as a separate badge that can disagree with it | thread 061 | `[SNIPPET]`, prior work |
| 9 | **Survival odds behind a paywall.** Pick Predictor is premium-gated; the free default view shows no availability at all | thread 061 | `[SNIPPET]`, prior work |

`[ANALYSIS]` Rows 3, 4 and 5 are one failure wearing three costumes: **the product is least available
exactly when it is most needed.** For a static-hosted app serving JSON, that is a solvable problem
and mostly already solved — which is an argument for making it *visible* (an explicit "working from
data captured at HH:MM, no network needed" state) rather than for building anything.

`[GAP]` **What I could not establish:** whether users complain about draft *assistants* specifically
(as opposed to platforms), what they say about recommendation quality, and whether anyone has
articulated wanting uncertainty. My searches for that returned vendor marketing every time. Reddit
would answer it and Reddit is blocked to this agent.

---

## 5. Q3 — what exists that this project has not considered at all

Three genuine ones. I am naming them in confidence order, and I would not stretch to a fourth.

### 5.1 An agent-facing surface instead of an in-app chatbot — `[VERIFIED]`, and this is the big one

STACKED ships **STACKED MCP**, a hosted Model Context Protocol endpoint at
`https://www.stackedfantasy.com/api/mcp` that *"turns Codex, Claude, and ChatGPT into a fantasy
football AI tool that can analyze rosters, recommend trades and waivers, optimize lineups, evaluate
offers, and pull live market data."* Twenty tools. *"Sessions are authenticated, subscriber-scoped,
and read-only. The assistant can retrieve fantasy context and generate recommendations, but it never
gets shared credentials or account-control permissions."* Explicit guardrails: never submits lineups
or trades, never changes settings, never sees credentials, always scoped to the authorising
subscriber. OAuth setup guides for all three clients.

`[ANALYSIS]` **Why this matters more here than anywhere else in the document.** This project
deliberately deferred the LLM prose renderer over hallucination risk, with the reasoning written into
the code, and `docs/operating-model.md` lists the assistant guardrail redesign as an unresolved
standing thread. An MCP surface **dissolves that trade-off instead of resolving it**: the model stays
outside the product, the product ships only facts and derivations through typed tools, and the
hallucination risk moves to a client the founder already runs. It also fits this project's shape
almost too well — the export contract is already a versioned, typed, field-named artifact (`1.14.0`),
which is 80% of what an MCP tool schema is.

`[ANALYSIS]` **Do not read this as a recommendation to build it.** It is out of Phase 1 scope, it has
no current consumer, and "build infrastructure with no consumer" is explicitly a red-team finding in
`CLAUDE.md` §8. Record it as an option that changes the *assistant* decision, not as work.

### 5.2 League-mate tendency modelling from your own league's history — `[VERIFIED]`

FantasyPros' **Draft Intel**: *"Discover key insights and pattern for your league-mates"*, fed into
mock bots so the mock *"feels like you're drafting against your real league mates."*

`[ANALYSIS]` This project has all three ingredients and has never combined them: 160 real picks from
the 2025 Westwood draft (now committed, thread 080), an Opponents tab, and a documented known gap
that *every backtest assumes opponents draft to ADP with noise*. `docs/research/yahoo-draft-assistant-2026-07-29.md`
§6 already proposed the pre-registered version — the founder labelling each of nine managers
`own-board / mixed / platform-default / unknown` **before** the 7 September draft. Draft Intel is the
same idea productised, which is evidence the shape is sound rather than exotic. The honest constraint
is sample: one observed draft per manager. **Nine humans × one draft is n=9 at best and arguably n=1
draft**, and a per-manager tendency estimate off that is decoration unless it is explicitly reported
as such.

### 5.3 The product as the *second* screen — `[VERIFIED]`

`[VERIFIED]` Sleeper's board *"can be cast to your big screen"*. `[VERIFIED]` FanDraft exists solely
to be the room's display: *"Export the board to a TV or projector and your whole league watches picks
roll in like the real NFL Draft"*, with walk-up songs, team logos, a ticker and audible alerts.

`[ANALYSIS]` Every screen spec in `docs/design-handoff/screens/` assumes this app is the screen the
user is looking at. On draft day it will not be — the founder's draft happens in Yahoo's room, and
this tool sits beside it, on a second device or a second window, competing for glances. That changes
concrete things: what must be legible at a glance versus on inspection, whether the layout survives a
half-width window, whether anything requires the app to have focus, and whether a pick entered in
Yahoo can reach this app without sync (it cannot — manual entry is the design, per §0). **Nothing in
the repo addresses the two-screen case**, and it is a framing gap rather than a feature gap, which is
why it is worth naming.

### Two more, offered honestly as weaker

- **Offline / degraded mode as a stated feature.** `[SNIPPET]` A real segment sells on it — DraftKick
  runs as an installed desktop app, CBS's Draft Kit works *"without an internet connection"*,
  SnapRankr advertises *"100% Offline … works fully offline after loading once"* plus CSV
  export/import for backup. `[ANALYSIS]` This project's hosted build is static files plus JSON, so
  offline is nearly free; the missing piece is *saying so* and having a printable fallback.
  `[GAP]` What a BeerSheet-style one-page draft sheet actually contains — I could not retrieve one.
- **Auction geometry.** `[VERIFIED]` FanDraft and FantasyPros both ship separate auction surfaces
  (live budgets, remaining cash, high bid, nomination order; a Salary Cap Calculator and Simulator).
  The design handoff already flagged this as open question 6. `[GAP]` Whether any of the founder's
  three leagues is an auction is not recorded anywhere I could find — worth one question before any
  more design work assumes snake.

**And one honest negative:** I did not find a fourth category. The rest of what the market ships —
draft grades, projected standings, cheat-sheet creators, keeper sync, salary-cap tools, news feeds —
is either already in this project's backlog or in §6 as something not to build.

---

## 6. Q4 — what to deliberately not build

Short, specific to this product, and reasoned from the evidence above rather than from a backlog.

| Don't build | Why, specifically |
|---|---|
| **Live platform sync** | ToS-blocked on Yahoo/ESPN/CBS, and it is the category's most common in-draft failure `[SNIPPET]`. Manual entry already exists and is keyboard-driven. Position it as the design |
| **A "trending / recommended players" feed** | The one feature users explicitly asked ESPN to remove `[SECONDARY]`. A recommendation that shows its derivation is a different object and is fine |
| **Draft grades and projected standings** | `[VERIFIED]` FantasyPros ships both. They are a post-hoc single number over a system this project cannot yet validate at n=1 mock; publishing a grade would be exactly the unearned confidence `CLAUDE.md` §11 forbids. The founder-useful version is a *counterfactual review* — "at pick 43 the model preferred Y" — which is cheap and honest |
| **A composite 0–100 "player score"** | The category's standard false-precision move; `docs/adr-drafts/ADR-A` already names Fantasy Points' prospect composite as the cautionary case. It is worse here, because a blended score hides the decomposition §8 of thread 061 identified as the actual wedge |
| **In-app conversational assistant as a primary surface** | Hallucination risk is already the stated reason for deferral, and §5.1 shows a route that avoids the trade entirely. Keep the dock as a dock |
| **Phone-first / responsive rework** | Already deferred (FR-025), and `docs/operating-model.md` records ~a third of an expensive frontend run spent on phone layouts the founder then pulled. Density is the product; a 390px board is a different product |
| **A visual overhaul** | §0. The evidence says the marginal return is negative past where we already are, and the porting risk is measured, not hypothetical |
| **Multi-sport, keeper/dynasty, salary cap, auction** | No stated need in any of the three leagues (`[GAP]` — nobody has asked); each is a separate screen, not a variant |

---

## 7. What a designer could act on tomorrow

Ordered by (value ÷ cost), all traceable to a tagged finding above. **None of these requires an
overhaul; all of them are compatible with one.**

1. **Put "not distinguishable from ranks X–Y" on the board row**, in the rank cell's own visual
   weight, driven by the `vbd_lo`/`vbd_hi` already exported. Draft Sharks precedent (§3.3); our own
   Josh Allen CI case. This is the single highest-value item in the document.
2. **A verbal uncertainty line, Boris Chen style**, wherever two candidates are inside each other's
   interval: *"these are a coin flip on our numbers."* One sentence, no chart, no new field.
3. **Slot selection in the prep setup block, with a "random slot" option**, and a rehearsal loop
   around it. FantasyPros precedent (§3.4); closes the actionable half of FR-034.
4. **State ownership labelled on screen** — league-scoped vs. account-scoped, Sleeper's split
   (§3.4). Cheapest possible answer to "make multi-league not feel like a settings chore."
5. **A snake grid view of the draft** (team × round, colour = position), as a peer of the Opponents
   tab rather than a replacement. §3.2 — this is where positional runs become visible without being
   computed.
6. **On-deck state before your pick**, and an explicit "if the clock expires, this is your pick"
   line on the queue. §3.1(b)(c); overlaps open thread 059.
7. **A reach indicator** — "N picks ahead of ADP" — now cheap: `board.json` carries `adp`,
   `adp_min_pick`, `adp_max_pick`, `adp_selected_pct` and `adp_source` at contract 1.14.0 (thread
   082). FantasyPros ships the same affordance `[VERIFIED]`. **Constraint from thread 082: never
   render the number without its `adp_source` label, and only 144 of 510 rows have one** — the other
   366 need a real null state, not a blank.
8. **Bound the on-the-clock recompute and say what the bound is.** Draft Sharks publishes
   "less than a second" `[VERIFIED as their claim]`; this project has never measured its own. Feeds
   open thread 060.
9. **Make the degraded state a designed state**: "working from data captured at HH:MM · no network
   required." §4 rows 3–5, §5.

---

## 8. Gaps — listed so nobody fills them by accident

1. `[GAP]` **The prior competitive UX research artifact is not in this repository.** Six documents
   cite it. See §0.5(a). Whoever finds it should commit it; it may contain half of §3 already.
2. `[GAP]` **All Reddit voice-of-customer.** The tool refused `www.reddit.com`. This is the biggest
   single hole in §4 and it is not closable by this agent class.
3. `[GAP]` **Any behavioural observation of any competitor under a real clock.** Still zero, same as
   thread 061. Every on-the-clock claim here is a vendor describing itself.
4. `[GAP]` **The visual form of Boris Chen's tier charts** — whether players carry error bars over
   the expert-rank range. The output is a PNG my tools cannot read.
5. `[GAP]` **Whether ESPN, Yahoo, Sleeper or Underdog display uncertainty anywhere.** Blocked for
   ESPN/Yahoo; absent from Sleeper's readable docs; Underdog not fetched.
6. `[GAP]` **What this project's own per-pick recompute costs.** Not measured anywhere.
7. `[GAP]` **Whether any of the founder's three leagues is an auction, and what the other two
   leagues' draft slots are.** League 2's `user_draft_slot` is recorded as a placeholder; league 3
   has no config at all.
8. `[GAP]` **What a BeerSheet-style printed draft sheet contains.** Page carries only download links.
9. `[GAP]` **17Lands' actual uncertainty UI.** FAQ rendered as a single string.
10. `[GAP]` **Whether users anywhere ask for uncertainty display.** Every search returned marketing.
    This is the gap that would most change the confidence of §0's recommendation #1 — the case for it
    currently rests on one vendor's commercial survival plus this project's own principles, **not on
    any evidence that users want it.** Say so when quoting §0.

---

## Sources

Fetched this session (`[VERIFIED]`):
[Sleeper robots.txt](https://sleeper.com/robots.txt) ·
[Sleeper support robots.txt](https://support.sleeper.com/robots.txt) ·
[Sleeper — unique features](https://support.sleeper.com/en/articles/1951583-what-are-sleeper-s-unique-features) ·
[Sleeper — Watch List vs. Draft Queue](https://support.sleeper.com/en/articles/3989685-watch-list-vs-draft-queue) ·
[Sleeper — Can I set pre-draft rankings?](https://support.sleeper.com/en/articles/4268342-can-i-set-pre-draft-rankings) ·
[Sleeper on the App Store](https://apps.apple.com/us/app/sleeper-fantasy-sports/id987367543) ·
[Draft Sharks — Inside the Draft War Room](https://www.draftsharks.com/league/mvp/inside) ·
[Draft Sharks — dynamic cheat sheet](https://www.draftsharks.com/kb/fantasy-football-cheat-sheet) ·
[Draft Sharks — Injury Guide methodology](https://www.draftsharks.com/injury-predictor/about) ·
[Draft Sharks — best fantasy football apps](https://www.draftsharks.com/kb/best-fantasy-football-app) *(vendor-authored competitor comparison — treat as `[SECONDARY]`)* ·
[FantasyPros Draft Wizard — draft software](https://draftwizard.fantasypros.com/football/draft-software/) ·
[FantasyPros Draft Wizard — draft tools](https://draftwizard.fantasypros.com/football/draft-tools/) ·
[FantasyPros blog — making the most of the Mock Draft Simulator](https://blog.fantasypros.com/08-22-2023-making-the-most-of-the-mock-draft-simulator/) ·
[FantasyPros on the App Store](https://apps.apple.com/us/app/fantasypros-fantasy-advice/id1141119371) ·
[STACKED](https://www.stackedfantasy.com/) · [STACKED MCP](https://www.stackedfantasy.com/mcp) ·
[FanDraft](https://www.fandraft.com/) · [Boris Chen — data, math, etc.](http://borischen.co/) ·
[ESPN Fantasy on the App Store](https://apps.apple.com/us/app/espn-fantasy-sports-more/id555376968?see-all=reviews&platform=iphone) ·
[17Lands robots.txt](https://www.17lands.com/robots.txt) ·
[blog.fantasypros.com robots.txt](https://blog.fantasypros.com/robots.txt)

Third-party reporting (`[SECONDARY]`):
[SI — ESPN updated their fantasy football app and players are livid (2025-08-05)](https://www.si.com/nfl/espn-updated-fantasy-football-app-players-livid-reactions) ·
[Pro Football Network — what's wrong with ESPN's fantasy app (2025-12-11)](https://www.profootballnetwork.com/wrong-espn-fantasy-football-app-calls-mount-fans-frustration/)

Blocked or unretrieved, recorded and not routed around:
`www.reddit.com` (tool refusal) · `espn.com` / `support.espn.com` (standing block) · every
Yahoo-owned host (robots, by agent name) · `cbssports.com` (ToS) · `forums.footballguys.com`
(robots, per thread 009) · `www.fantasylife.com` (prior audit's recorded block, honoured for
consistency) · `support.fantasypros.com` (HTTP 403) · `underdogfantasy.com` (robots not
established) · `play.google.com` (content did not render) · `17lands.com/faq` (content did not
render) · `footballabsurdity.com/beersheets/` (no descriptive content)

Prior in-repo work built on rather than re-derived:
`docs/research/competitor-recommendation-audit-2026-07.md` (thread 061) ·
`docs/research/yahoo-draft-assistant-2026-07-29.md` · `docs/research/source-audit-2026-07.md`
(thread 009) · `docs/design-handoff/HANDOFF-NOTES.md` and `README.md` Addendum 3 (which quote the
missing competitive UX pass) · `docs/design-brief.md` · `docs/founder-requests/FR-034` ·
`docs/handoffs/082`
