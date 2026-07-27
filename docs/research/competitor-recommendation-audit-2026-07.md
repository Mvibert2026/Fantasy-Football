# Competitor recommendation audit — FantasyPros Draft Wizard and peers

**Thread:** 061 · **Role:** researcher · **Date:** 2026-07-27
**Scope:** what FantasyPros' recommendation percentage actually is, and whether availability-aware
recommendation is a real differentiator for this project.

---

## VERDICT (one sentence, as asked)

**The decisive experiment was not run — I had no browser and no session credentials — but the
question it was meant to answer is resolved anyway by FantasyPros' own documentation: the
percentage the founder saw is "Expert Voting," an expert-consensus vote share that is explicitly
*not* availability-aware, while FantasyPros separately ships a premium feature called "Pick
Predictor" that computes, by simulation, the odds a player survives to your next pick — so the
specific number the founder pointed at is not our competitor, but the feature sitting one tab over
from it is.**

**Consequence for the thesis, stated plainly: the differentiator as written in this repo is
materially weaker than the repo claims.** Detail in §7. Do not read the verdict's first clause as
a reprieve.

---

## 0. What I could and could not do, before anything else

This is the most important methodological disclosure in the document, because the thread's priority-1
experiment is the one thing I did not do.

| Capability the thread assumed | Actually available to me | Consequence |
|---|---|---|
| Manual, human-paced use of Draft Wizard with the founder's free-tier login | **No.** This session has no browser automation tool, no interactive session, and was given no credentials. | Experiments 1–7 **not run**. |
| Ability to POST / hold session state (required to construct two mocks with identical boards and different pick distances) | **No.** The only web tool is a stateless GET that renders a page to markdown. | Experiment 1 structurally impossible here, not merely inconvenient. |
| Shell / git | **No Bash tool in this session.** | Could not pull, branch, commit, or push. See §9. |

**Everything below is documentary and marketing evidence, not behavioural evidence.** The thread
correctly said "behaviour is the evidence." I did not obtain behavioural evidence. I have tagged
every claim accordingly and I have not simulated, estimated, or reconstructed a single observed
value.

### Sample quality, not just sample size

- **Behavioural sample: n = 0.** Not "small." Zero.
- **Documentary sample on FantasyPros: effectively n = 1 source.** Every FantasyPros mechanism claim
  below traces to one origin — their Zendesk help centre — reached through *one* channel (search-engine
  snippets), because the pages themselves 403'd me. Five separate searches returning consistent text
  is not five sources; it is one source retrieved five times. Treat it as a single point of failure.
- **Additional degradation:** the search tool returns a *model-written summary* of the snippets, not
  raw snippet text. So there is a paraphrase layer between me and their words. Where I use quotation
  marks below for FantasyPros help content, I am quoting the summary, and it may not be their literal
  wording. This is why nothing FantasyPros-related is tagged `[VERIFIED]`.
- **Competitor sample is SEO-biased.** The peer tools I found (DraftMilk, DraftKick, Razzball War
  Room, The Solver) are the ones that rank for "draft assistant availability probability." Vendors
  who build this and do not market it are invisible to my method. **This biases my competitor count
  downward**, which means §7's conclusion is, if anything, understated.

---

## 1. Access and licensing posture (fetching vs. redistributing — answered separately)

| Question | Answer | Confidence |
|---|---|---|
| `www.fantasypros.com/robots.txt` | `User-agent: *` with `Disallow: /ajax/`, `/nfl/ranker/`, `/mlb/ranker/`, `/nba/ranker/`, `/api/`, `/json/`, `/xml/`; `Crawl-delay: 5`; sitemap + `/llms.txt` declared | `[VERIFIED]` — fetched the file |
| `draftwizard.fantasypros.com/robots.txt` | `User-agent: * / Allow: /` and a separate `User-agent: GPTBot / Disallow: /` | `[VERIFIED]` — fetched the file |
| Is programmatic probing of the recommendation backend permitted? | **No — blocked.** The recommendation data is served from `/api/`, `/ajax/`, `/json/`, all `Disallow`ed. | `[VERIFIED]` |
| `support.fantasypros.com` article fetches | **HTTP 403 to my fetcher** on every article attempted. | `[VERIFIED]` |

**Action taken on both blocks: recorded and stopped.** I did not probe any disallowed path, and I did
not route around the 403 via a cache, proxy, text-extraction relay, or alternate user agent. The cost
of that decision is visible throughout this document as `[SNIPPET]` tags where `[VERIFIED]` would
otherwise sit. That is the correct trade.

**Fetching vs. redistributing, stated separately as required:**

- *Fetching for personal use* — manual human use of Draft Wizard under the founder's account is
  governed by their ToS, not robots.txt, and is what the thread authorised. Unchanged by this audit.
- *Redistributing / re-deriving* — reproducing their percentages inside this project's product is a
  separate and stricter question, and the thread already forbids it. **Nothing here changes D-020**;
  I did not reopen it. The findings below are design intelligence, not data inputs.

---

## 2. What the founder's percentage actually is

The thread's framing assumed one percentage. **There are at least three distinct numeric objects in
Draft Wizard**, and conflating them is exactly how a thesis gets falsely confirmed or falsely
refuted. Separating them is the core finding of this audit.

| # | Object | What FantasyPros says it is | Availability-aware? | Roster-aware? | Confidence |
|---|---|---|---|---|---|
| A | **Expert Voting %** — the default view in the player queue; highest is highlighted green | Tells you, *"all other things being equal,"* whom the experts they monitor would take among the players **in your queue**; each expert's Overall Rankings are used to determine that expert's vote | **No** — "all other things being equal" is doing exactly this work | **No** — their own docs say so explicitly (see row B) | `[SNIPPET]` |
| B | **"Top Lift" / "Biggest Boost"** green alert | The player expected to give the largest boost to your team given your current roster's strengths and weaknesses. Their docs state a player *"can be denoted as the Top Lift player and have an expert voting percentage lower than other suggested players, because Top Lift takes into account your current roster and team needs, whereas expert voting suggests who the experts like best without considering your roster and team needs."* | No | **Yes** | `[SNIPPET]` |
| C | **Pick Predictor** — its own tab | The odds a player is taken before your next pick, obtained by *running simulations across all cheat sheets in their database including multi-source ADP*, taking into account players already gone, **opponents' roster needs**, and **how many picks remain before your turn**. Toggleable to 1, 2, or 3 rounds out. Premium. | **Yes — explicitly and by construction** | Opponent-roster-aware | `[SNIPPET]` |

**Row B's quoted sentence is the single most valuable line in this audit.** It is FantasyPros
publicly documenting that their headline percentage ignores your roster, and shipping a second,
differently-named indicator that does not — and pre-explaining to users why the two disagree. That
is both the answer to the founder's question and, in §8, the best thing here worth stealing.

**Caveat on row B, flagged rather than smoothed over:** the "statistical boost … in each category"
phrasing is rotisserie-category language, native to fantasy baseball/basketball, not football. The
Draft Wizard help centre is shared across sports and the article I hit may be the sport-generic or
baseball-oriented one. Whether an equivalent roster-aware alert exists in the *football* Draft
Assistant with the same semantics is **`[GAP]`** — I could not confirm it and will not assume it.

### Answering the thread's binary directly

The thread posed two possibilities with opposite consequences. **The evidence says the answer is
"both, in different features," which the thread's binary did not admit.**

- The percentage the founder described — "a percentage of who it would pick" — matches **A**, Expert
  Voting, which is a **consensus/value score with no survival modelling**. `[SNIPPET]`
- But FantasyPros **does** ship survival modelling, as **C**, and describes it in terms nearly
  identical to this project's own differentiator language. `[SNIPPET]`

Narrowly, the founder's specific observation is confirmed: that number is not availability-aware.
Broadly, the reassurance that would normally follow does not hold, because the capability exists in
the same product.

---

## 3. Experiments 1–7: status

Recorded individually so a future session with browser access can pick up exactly where this stopped.
**No setup, no observed output, no implication is recorded for any of these, because none were run.**

| # | Experiment | Status | What documentary evidence predicts (a hypothesis to test, *not* a result) |
|---|---|---|---|
| 1 | Vary picks-until-next-turn, hold board constant | **NOT RUN** `[GAP]` | Expert Voting % unchanged; Pick Predictor odds change sharply. Queue *ordering* — unknown, and this is the real open question. |
| 2 | Vary roster, hold board constant | **NOT RUN** `[GAP]` | Expert Voting % unchanged (docs say roster is ignored); Top Lift target changes — *if* Top Lift exists in football. |
| 3 | Vary scoring (std / half / full PPR) | **NOT RUN** `[GAP]` | Their docs claim custom scoring propagates into both Simulator and Assistant. Unverified; worth testing because "reorders a static list" is the cheap implementation and is common. |
| 4 | Do percentages sum to 100? | **NOT RUN** `[GAP]` | A *vote share among the players in your queue* should sum to ~100 over the queue and should **change when you add or remove a queue member with no draft-state change at all.** That last is a sharper, cheaper diagnostic than summing — run it first. |
| 5 | Determinism | **NOT RUN** `[GAP]` | Expert Voting should be deterministic (fixed rankings). Pick Predictor is simulation-based, so **small run-to-run jitter would be expected and is not evidence of anything wrong.** |
| 6 | Bye-week / stacking collision | **NOT RUN** `[GAP]` | No FantasyPros documentation found mentioning bye weeks in recommendation. **Thread 059's registered prediction that the effect is small is neither supported nor contradicted here.** |
| 7 | Edge cases (suspended / injured / rookie) | **NOT RUN** `[GAP]` | Nothing found. |

**Nothing in the right-hand column may be cited as a finding.** It exists so the next session can
pre-register expectations before looking, which is the only way experiment 1 stays honest once
someone is motivated by the answer.

---

## 4. What FantasyPros publishes about the method (their claim, not fact)

All `[SNIPPET]`, all via search summaries of 403'd help pages, all tagged as **their claim**:

- The queue is built from *"your personal cheat sheet, team needs and position scarcity."* Note the
  tension with §2 row A: the *queue construction* is claimed to consider team needs, while the
  *Expert Voting percentage displayed on that queue* explicitly does not. **These are different
  layers and it would be easy to misattribute one to the other** — a further reason experiment 1
  must record ordering and percentage as two separate observations.
- Expert Voting is computed from each expert's **Overall Rankings**, not from projections.
- Pick Predictor uses **simulation over multi-source ADP and all cheat sheets in their database**,
  with opponent roster needs and picks-until-your-turn as inputs.
- Custom league scoring is claimed to be honoured in both Simulator and Assistant.
- Two Draft Assistant variants exist, gated to MVP/HOF/GOAT tiers. **The founder's free tier may not
  expose Pick Predictor at all**, which is the most likely reason this capability was invisible until
  now, and a live risk to running experiment 1 — check tier access before scheduling the session.

---

## 5. Peer tools — one line each

| Tool | Characterisation | Availability-odds? | Confidence |
|---|---|---|---|
| **FantasyPros Draft Wizard** | Consensus-expert queue + separate simulation-based availability tab, premium-gated | **Yes** (Pick Predictor) | `[SNIPPET]` |
| **DraftMilk** | Football-only draft assistant, $14.99 one-off / $29.99 season, free tier included | **Yes — see §6** | `[VERIFIED]` (page fetched) |
| **Razzball War Room** | Credited by a rival vendor as the one tool clearly implementing probability-of-future-availability | Yes | `[SECONDARY]` — rival's characterisation, not checked at source |
| **DraftKick** | Live-sync assistant claiming to predict when players will be available for upcoming picks | Claimed yes | `[SNIPPET]` |
| **The Solver** | Underdog/DraftKings best-ball ranker. Explicitly scoped *against* this: *"won't draft for you. It answers the only question that matters on the clock: 'Who's the best pick right now?'"* | **No — and deliberately so** | `[VERIFIED]` (page fetched) |
| **Footballguys Draft Dominator** | Long-standing desktop assistant with live sync to Sleeper/MFL | Unknown | `[SNIPPET]` |
| **Sleeper (native)** | Draft board gives context on opponent moves, real-time ADP, AI mock opponents. **No native per-pick recommendation found.** | Not found | `[GAP]` — absence of evidence via one search; I did not reach Sleeper's own docs |
| **ESPN / Yahoo (native)** | **Could not establish.** Searches returned draft-strategy journalism, not product documentation. | Unknown | `[GAP]` |

**The Sleeper/ESPN/Yahoo row is a genuine gap and I am not going to soften it.** "No native
recommendation found" is a statement about my search, not about their products. Anyone planning
around "the platforms don't do this" needs that checked properly first.

---

## 6. DraftMilk — the finding that actually threatens the thesis

Fetched directly from their own site, so `[VERIFIED]` **as published claims** — I have verified that
they *say* this, not that it *works*. The distinction matters and I am not blurring it.

- *"percentage chance each player is still on the board at your next pick"* — with a worked example,
  *"47% at your next pick."*
- *"Roster-aware verdicts: value, urgency, need, and bye conflicts"*
- *"Every recommendation shows its reasoning — no black boxes"*
- Free tier: top 15 per position, 2 leagues, 1 mock with the live assistant. Pro: **$14.99 once.**
- Football-only; PPR, half-PPR, superflex, keeper, auction.

Read that list against this repo's differentiator statement. It is **value + urgency + roster need +
bye conflicts + survival percentage to your next pick + stated reasoning** — which is not a
neighbouring product, it is a near-restatement of this project's pitch, shipping today, at fifteen
dollars, with a free tier.

**What this does not establish, and I will not pretend otherwise:** whether their percentage is
*calibrated*. Nothing on that page claims calibration, no methodology is published, and I have run
no behavioural test. It could be an uncalibrated ADP heuristic wearing a percent sign — which is
precisely the state this project is in today (`CURRENT-STATE.md`: 1 of ~30 mocks logged, "an honest
estimate, not a validated probability"). **Neither party has demonstrated calibration.** That
symmetry is the entire remaining argument in §7, and it is a thinner argument than the repo's
current language implies.

---

## 7. Honest assessment of the differentiator

**The claim "availability-aware recommendation is our differentiator" does not survive contact with
this evidence, and should be rewritten rather than defended.**

What the evidence supports, in descending order of confidence:

1. **Availability modelling is not an empty niche.** At least two vendors (FantasyPros Pick
   Predictor, DraftMilk) and probably four ship a probability-a-player-lasts-to-your-next-pick
   number. One rival vendor's own comparison names a *third* (Razzball War Room) and says the idea
   *"is a great idea"* deserving refinement — i.e. the concept is known, implemented, and openly
   discussed in this market. `[VERIFIED]` for the DraftKick article's existence and content;
   `[SECONDARY]` for its claims about Razzball.
2. **"Competitors just rank players" is false as a general statement** and should be struck from every
   doc that says it. It is true of The Solver, which says so itself. It is not true of FantasyPros.
3. **The narrow version of the founder's observation stands:** the *headline* percentage in Draft
   Wizard is expert consensus and ignores your roster and your pick distance. A user looking at the
   default view is not being shown availability. `[SNIPPET]`

What is left that is genuinely defensible — and it is narrower than the current framing:

- **Integration, not capability.** FantasyPros splits value (Expert Voting), fit (Top Lift), and
  survival (Pick Predictor) into three separately-named indicators the user must mentally combine,
  with the survival one paywalled. This project computes a single decision-relevant quantity — the
  cost in survival odds of taking a player now. **That is an integration and presentation claim, not
  a "nobody else models availability" claim.** DraftMilk's "value, urgency, need, and bye conflicts"
  language suggests they integrate too, so even this is contested.
- **Calibration, *if and only if* it is ever achieved.** No competitor found publishes calibration
  evidence. This project has a pre-registered decision rule, a blind arm, and a Brier/calibration
  harness specified — which is a real and unusual asset. But it currently has **1 of ~30 mocks
  logged.** *"We will be calibrated"* is not a differentiator; it is a plan. Until that number moves,
  this project and DraftMilk are making the same unevidenced claim, and DraftMilk is making it to
  paying customers.
- **League-specific scoring fidelity.** Yardage bonuses, this league's exact rules, a 4-team
  no-reseed playoff. Plausibly real, **untested against competitors here** — FantasyPros claims
  custom-scoring propagation and experiment 3 exists precisely to test it. `[GAP]`

**Recommended wording change** — proposed for the strategist/PM, not adopted by me:

> ~~"Competitors rank players; we tell you what taking one costs you."~~
> "Competitors that model availability keep it in a separate, usually paywalled tab and publish no
> calibration evidence. We integrate availability into a single recommendation and hold ourselves to
> a pre-registered calibration standard — a standard we have not yet met."

That is less exciting and considerably more defensible, and it has the advantage of being true today.

---

## 8. What their UI does that ours does not

Worth adopting; all `[SNIPPET]` on mechanism, and none require reproducing any FantasyPros number.

1. **Name each number, and give each name its own explanation.** Every indicator has a dedicated
   help article: *"What are the Expert Voting Percentages?"*, *"What is the Pick Predictor?"*, *"What
   does the green Top Lift alert indicate?"* The founder's complaint that "it doesn't explain why" is
   fair about the *draft room UI* — but the explanation exists, it is just one hop away instead of
   in-place. **The adoptable lesson is the taxonomy discipline, not the help centre.**
2. **Pre-explain component disagreement.** They ship a documented answer to *"why is Top Lift
   recommending someone with a lower Expert Voting %?"* — i.e. they anticipated that their components
   disagree and treated the disagreement as informative rather than as a bug to hide. **This project
   blends marginal value, need (λ = 0.352) and positional run (δ = 0.10) into one number and can
   currently show a user no such decomposition.** Surfacing "ranked 4th on raw value, 1st once your
   roster and their likely picks are accounted for" is a direct, cheap, high-value port.
3. **A horizon control.** Pick Predictor toggles 1 / 2 / 3 rounds out. This project's availability is
   framed at "next pick." A horizon selector costs little and turns a single number into a shape.
4. **Basis switching in the queue** — re-rank by overall, by position, or by stat category. Lets the
   user interrogate the recommendation instead of accepting it.
5. **A visual singleton.** Exactly one player is highlighted green. Unambiguous under time pressure —
   worth remembering against the temptation to display ten near-equal scores in a draft room.

**Where this project can legitimately beat them:** they explain *what each number is* but not *why
this player, in this draft, right now.* Point 2 is the wedge — component decomposition at the moment
of the recommendation is the thing none of the documentation suggests any competitor does in-place.

---

## 9. Handoff — what the next session must do

**This audit is incomplete in its most important part and must not be closed as if it were not.**

Priority 1 — **run experiment 1**, needing: a browser-capable session, the founder's login, and a
check that the tier exposes Pick Predictor. Record ordering *and* percentage separately (§4). Record
the Expert Voting % **and** the Pick Predictor odds across the 2-picks-away and 20-picks-away
conditions; the interesting result is whether the *queue ordering* moves, since we already expect the
two percentages to behave differently.

Priority 2 — experiment 4's sharper form: change only the queue membership, change nothing about
draft state, see whether the percentages move. If they do, it is a vote share over the queue and
comparing it to our per-player scores is a category error.

Priority 3 — close the Sleeper / ESPN / Yahoo `[GAP]` at source documentation.

**Repo-state disclosure:** this session had no shell. I could not pull `origin/main`, create the
`researcher/061-competitor-audit` branch, commit, or push. This file and the thread reply are written
to the worktree only and **are uncommitted**. Whoever picks this up must handle the branch and commit
themselves, and should re-pull first in case a concurrent session has moved `main`.

---

## Sources

- [FantasyPros robots.txt](https://www.fantasypros.com/robots.txt) · [Draft Wizard robots.txt](https://draftwizard.fantasypros.com/robots.txt)
- [What are the Draft Wizard Expert Voting Percentages?](https://support.fantasypros.com/hc/en-us/articles/115001352248-What-are-the-Draft-Wizard-Expert-Voting-Percentages) (403 — snippet only)
- [What is the Pick Predictor?](https://support.fantasypros.com/hc/en-us/articles/115001315067-What-is-the-Pick-Predictor) (403 — snippet only)
- [What is the Draft Assistant?](https://support.fantasypros.com/hc/en-us/articles/115001308567-What-is-the-Draft-Assistant) (403 — snippet only)
- [How does the draft simulator suggest players for me to pick?](https://support.fantasypros.com/hc/en-us/articles/115001305067-How-does-the-draft-simulator-suggest-players-for-me-to-pick) (403 — snippet only)
- [What does the green "Top Lift" alert indicate?](https://support.fantasypros.com/hc/en-us/articles/115001314967-What-does-the-green-Top-Lift-alert-in-the-player-queue-indicate-) (403 — snippet only)
- [Draft Wizard Draft Assistant product page](https://draftwizard.fantasypros.com/football/draft-assistant/) (fetched; thin)
- [DraftMilk](https://www.draftmilk.com/) (fetched) · [The Solver Draft Assistant](https://thesolver.com/draft-assistant) (fetched)
- [DraftKick — Fantasy Draft Software Feature Comparison](https://draftkick.com/blog/fantasy-draft-software-feature-comparison/) (fetched)
- [Sleeper — unique features](https://support.sleeper.com/en/articles/1951583-what-are-sleeper-s-unique-features) (snippet only)
