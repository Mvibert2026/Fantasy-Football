# Fantasy Football Assistant — Project Spec

This file is the standing law of the project. Read it before acting. If a request conflicts
with something here, say so before proceeding — do not silently re-decide settled questions.

---

## 1. What this is

A personalized, end-to-end fantasy football assistant. Draft prep, draft-day support, and
in-season management, driven by a proprietary ranking model that improves year over year.

**Current scope: single user, local only.** No auth, no hosting, no multi-tenancy.

**Eventual scope (design for it, do not build it yet):** public, multi-user, multi-provider
(Yahoo / ESPN / Sleeper), per-user league settings and strategy sessions.

The distinction matters for build decisions. When a choice costs nothing now and preserves the
future path, take it (e.g. multi-user schema shape, provider adapter pattern). When it costs
real time or complexity now, defer it and note it in `docs/deferred.md`.

---

## 2. Phase 1 scope — the only thing being built right now

**A backtesting harness and a versioned, tunable ranking algorithm.**

Not the draft tool. Not the in-season tool. Not the league ADP model. Those come later and are
explicitly out of scope until Phase 1 passes its gates.

Phase 1 is done when: given a candidate ranking configuration, the system can answer
*"if I had ranked players this way going into season N, how would it have performed against
what actually happened — and did it beat the market?"*

### The founder's bar — this outranks everything else in the backlog

> "If I don't have those three things in place, I don't want to use the tool for my real draft."

1. The best **bottom-up rankings**
2. The best **availability prediction**
3. The best **suggested-pick model** — his roster, opponents' rosters, availability, live

**These are this-season questions.** A previous PM framed them as off-season design work and was
overruled in those words. Do not re-frame them.

**Ordering, and a correction the founder made the same day — 2026-07-31.** PM first wrote these as a
strict chain, *rankings → availability → recommender*, with both later stages blocked on the first.
**That is half wrong, and the wrong half matters.**

- **Availability is not blocked on our rankings.** It predicts *drafter behaviour*, so its inputs are
  what drafters actually use — **ADP and expert consensus** — not our proprietary view. Both are in
  the database and current. Founder's words: *"Availability can be done with ADP and consensus. Both
  probably impact drafters."* Building it against our own board would model opponents as drafting off
  a ranking they have never seen.
- **The recommender takes a ranking as a *parameter*, not a prerequisite.** Founder: *"could use any
  rankings as inputs to the decision engine which would consider who may be at the next pick and my
  own roster construction."* It can run on consensus, ADP, or ours — which is exactly what the four
  selectable sources (ADR-068) exist to allow.
- **What a wrong ranking actually corrupts** is the recommender's *value* judgement — the
  opportunity-cost term is value over a fallback. It does not corrupt availability, and it does not
  block either model from being built and tested.

So the three can proceed **in parallel**, and only the recommender's value term depends on ranking
quality. As of 2026-07-31 the shipped board's within-position ordering is identical to consensus, so
that dependency is a live risk for the recommender specifically — not a reason to stall the other two.

Availability's own inputs, in the founder's order: **ADP, then how the draft has actually fallen,
then opponents' needs.** The middle one is what justifies simulating at all — with ADP plus
per-player dispersion the unconditional marginal is nearly closed-form.

### 2a. The bar is absolute quality, not edge — founder's ruling, 2026-08-01

> "Aka independent of consensus. Create the best draft rankings we can that could be easily applied
> to different league scorings by updating points. Our bar is not consensus. It's how good can our
> rankings be. When we think they are as good as they'll get (any and all components in it that need
> to be), then we can test vs the other three models like consensus, consensus adjusted and ADP etc."

This resolves the frame problem Fable ruled on the day before (`docs/fable/M2-findings.md` §F1–F7):
"can we beat consensus" was being asked of an object *derived from* consensus, which is close to
structurally incapable of returning a win.

**Three things follow, and they are binding.**

1. **Consensus is not an input.** The ranking is built from player-level projections, not by
   re-scoring someone else's order. The shipped board today is consensus re-scored — within-position
   identical to consensus, deviating only cross-positionally — and that is the thing being replaced,
   not extended.
2. **Consensus is not the development signal.** During build, measure *absolute* quality against
   realised outcomes. The four-baseline comparison in §6.5 is a **release gate run once at the end**,
   not a per-arm steering metric. An arm that improves absolute quality is an improvement even if the
   gap to consensus does not move.
3. **Projections output stat lines, not points.** Volume, efficiency and games per player; fantasy
   points are then computed by applying a league's scoring config (§7) to those stat lines, and
   replacement levels by applying its roster shape. **Changing league scoring must re-score and
   re-rank without re-fitting anything.**

**Why (1) and (3) are the same requirement.** A board whose within-position order comes from
consensus *cannot* respond to league scoring, because consensus was produced for a generic 12-team
full-PPR room. Half-PPR, the stacking yardage bonuses, and 10-team replacement levels cannot reach
the ordering through a consensus-derived board at all. Scoring portability is therefore not a
nice-to-have bolted on later — it is only achievable by building independently in the first place.

**Deviation from consensus is a diagnostic, not an objective — founder's clarification, 2026-08-01.**

> "Don't take that bar literally. But we need to be respectable. If we have too many major
> differences from consensus it's probably a red flag."

This does **not** reopen (2) above. The distinction is load-bearing and both halves bind:

- **Never a penalty to minimize.** Scoring the model on closeness to consensus rebuilds a
  consensus-derived board by the back door and kills scoring portability with it (see below).
- **Always a flag to investigate.** A board that disagrees violently and cannot say *why* has a bug.
  Every large deviation should have a stated reason; the ones that do not are the queue.

**This method has a 2-for-2 record here already, both times found by the founder by eye:** Taysom
Hill (ours 25, consensus 171) and Burrow at QB26 — both real defects in the games channel, not real
disagreements. The requirement is therefore an explained-deviation report, not a deviation budget.

**Rookies are a separate population and must be modelled separately — founder's ruling, 2026-08-01.**

> "Rookies need to be treated differently. It's just a fact. Would be a mistake to let them or the
> veterans ruin the others model."

**The mechanism, so this is not treated as a preference.** Every lag feature a veteran projection
rests on — prior-season volume, efficiency, games, snap share, injury history — is *structurally
absent* for a rookie, not merely missing at random. A joint fit therefore teaches the model that
absent prior-season production implies a low projection, which is trivially true for rookies and true
for a completely different reason than it is for a veteran. The corruption runs both ways: rookies
drag the veteran coefficients, and veteran-derived coefficients misprice rookies.

**Required:** separate fits, or at minimum a rookie indicator with **full interaction** on every lag
feature — never a shared slope. Rookie projections are driven by draft capital, athletic profile,
landing spot and depth-chart role, not by lag features that do not exist. Availability is the sharpest
case: a rookie has **no injury history at all**, so the availability model cannot use its veteran form.

**What we have for it:** `draft_picks` (1980–2026, 12,927 rows) is already read by the core panel
builder. **`combine` (2000–2026, 8,968 rows — forty, bench, vertical, broad jump, cone, shuttle,
height, weight) is NOT** read by any projection model, only by side experiments. Fable's own v2 build
log records rookies as "crude" and a board-veteran level bias of ~−2.6 games, so this is a known
live weakness, not a hypothetical.

**The hard part, named in advance so it is not discovered late.** v1's rate projections are already
at or better than market parity; its entire measured deficit sits in one channel — **projected
games** (Fable M2-1). That is also the channel where consensus's advantage is real: what consensus
knows that we do not is *who is going to play*. Independence therefore stands or falls on building
our own answer to player availability from injury history, age, workload and pre-Week-1 status.
Distinct from *draft* availability (§2's question 2) despite the shared word — do not conflate them.

---

## 3. Build order

Do not skip ahead. Each step is gated (see §8).

| # | Component | Output |
|---|---|---|
| 1 | Data ingestion | Historical NFL data cached locally in SQLite |
| 2 | Scoring engine | Raw stats → fantasy points under *this league's* scoring rules |
| 3 | Backtest harness | Evaluate any ranking config against historical outcomes |
| 4 | Ranking algorithm v1 | Simple, transparent, versioned weighted model |
| 5 | Factor testing | Work through the test registry, measuring each factor's real contribution |

Steps 1–3 are infrastructure and can be built now. Step 4 depends on the factor list in
`docs/test-registry.md`. Step 5 is iterative and never really "finishes."

---

## 4. Architecture

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python | Matches the data/analysis workload |
| API layer | FastAPI | Free path to a real API when this goes multi-user |
| Database | SQLite (local file) | Zero config; schema ports to Postgres cleanly |
| Data frames | pandas or polars | Whichever the ingestion library returns natively; don't convert gratuitously |
| Providers | Adapter pattern behind a generic interface | Adding ESPN/Sleeper later = a new adapter, not a rewrite |
| Secrets | `.env`, gitignored, never committed | Same pattern scales to per-user secrets later |
| Config | Ranking weights live in versioned config files, **never hardcoded** | Every model version must be reproducible and comparable |

### Schema principles

- **Model as multi-user from day one.** Tables carry `user_id` / `league_id` even though there
  is exactly one of each right now. Costs nothing; avoids a migration later.
- **`coach_id` is a first-class dimension, not just `team_id`.** Coordinators change teams.
  Tendency signals must follow the person, or they break the moment someone moves.
- **Ranking sources stay separate, never blended.** A `ranking_source` enum
  (`proprietary` / `expert` / `league_adp` / `market_adp`) — so our model's independent view
  is always visible against consensus rather than silently converging toward it.
- **Every time-sensitive record carries an `as_of_date`.** Critical for ADP, injury status,
  depth charts, and odds. Without it, look-ahead bias is unavoidable (see §6).
- **Store a `season_weight` / recency-adjustment field from the start.** Trend regimes shift;
  flat historical averaging is a known failure mode.
- **Projections are stored as stat lines, never as fantasy points** (§2a, 2026-08-01). Volume,
  efficiency and games per player; points are derived by applying a league's scoring config, and
  ranks by applying its roster shape to get replacement levels. A projection table with a `points`
  column and no stat columns has silently hardcoded one league's rules into the model and cannot be
  ported by changing config — which is the whole requirement.

### Core tables (starting shape, expect refinement)

```
users, leagues, league_scoring_settings
players, player_weekly_stats, player_season_stats
teams, team_weekly_stats
coaches, coaching_staff_seasons          -- coach_id, team, role, season
odds_snapshots                            -- win totals, spreads, implied totals, props; as_of_date
adp_snapshots                             -- source, player, adp, as_of_date
ranking_versions                          -- config blob + metadata, immutable once run
ranking_outputs                           -- version_id, season, player, rank, score
backtest_results                          -- version_id, season, metrics, baseline comparison
outcome_feedback                          -- projected vs. actual delta; the YoY learning loop
```

---

## 5. Data sources

| Source | Covers | Access |
|---|---|---|
| **nflverse** (`nflreadpy`, or `nfl_data_py`) | Play-by-play back to 1999, weekly/seasonal player stats, rosters, snap counts, draft picks, schedules. Most Tier 0/Tier 1 factors derive from this: target share, snap share, red-zone usage, air yards, aDOT, WOPR, PROE, TD rate, xFP inputs. | Free, no login |
| **Coaching staff history** | Coach/coordinator identity, role, team, tenure. **Not in nflverse.** Needed for the `coach_id` join. | Pro Football Reference coaching pages or equivalent — verify licensing/scraping terms before building |
| **Vegas odds** | Season win totals, implied team totals, game spreads, player props | Free odds source — evaluate options at build time |
| **ADP (multi-source)** | FFC, Yahoo, ESPN, Sleeper, Underdog | Separate per-site scrape; no unified API |
| **Route data** | Routes run, route participation rate | Not directly in nflverse — needs NGS or a documented proxy calculation. Flag clearly if proxied. |

**Licensing:** nflverse data is broadly CC-BY (FTN charting subset is CC-BY-SA and requires
attribution). Respect attribution requirements.

**Scraped sources — founder's ruling, 2026-08-01, superseding "check terms before building the
scraper, not after":**

> "Stop worrying about terms. I will worry about them. It's all personal use. Just get the data."

**Do not review, report on, or stall an ingest over terms of service.** The founder has taken that
decision and the liability; this is a single-user personal-use project. An agent that returns a
partial ingest whose missing half is "I paused to check the terms" has not done the task. This
paragraph exists so the ruling is not re-litigated by the next agent who reads this section.

Still binding, and unrelated to terms: **no credentials in code** (§10), no paid or trial-gated
tiers (a budget constraint — the founder has declined to pay), and **`as_of_date` on every
time-sensitive row** (§6.1). A scraped value carrying a reconstructed or current date silently
creates look-ahead and is worse than no data at all.

---

## 6. Statistical guardrails

**These are not optional and not negotiable. A model that violates them is worse than no model,
because it produces confident, wrong answers.**

### 6.1 Look-ahead bias — the primary threat

Backtesting rankings means using *only* information that existed before Week 1 of the target
season. nflverse hands you the entire season at once, which makes this extremely easy to get
wrong.

- Ranking inputs for season N may use data through the end of season N−1 and preseason N only.
- ADP, injury designations, depth charts, and odds must be pulled by `as_of_date`, matched to
  a realistic pre-draft date — not their final or current values.
- Any transformation touching target-season data is a bug, not a judgment call.
- **The harness must enforce this structurally** (a data-access layer that refuses to serve
  post-cutoff rows), not by convention or code review.

### 6.2 Survivorship bias

The player universe for season N must be defined *before* season N — e.g. all players inside a
pre-season ADP threshold, or on an active roster at Week 1. Building it from "players who
scored fantasy points that year" silently deletes every bust and inflates measured performance.

### 6.3 Overfitting and multiple comparisons

Roughly 200–300 fantasy-relevant players per season, heavily autocorrelated across years
(the same players recur), against ~30+ candidate factors. This is a textbook overfitting setup.

- Hold out seasons. Tune on training seasons only; touch the holdout once.
- **The sealed 2025 holdout does not open until fable has run. Founder's ruling, 2026-07-31.**
  It can be spent exactly once, and spending it before adversarial review means spending it on
  whatever the project believed at the time. Any agent that thinks a result warrants the holdout
  **stops and escalates to the founder** — no agent opens it on its own authority, including on a
  result it considers decisive. Every access is logged in
  `docs/preregistration/holdout_access_log.jsonl`.
- Testing ~30 factors at p<0.05 yields ~1.5 false positives by chance. Correct for it, or
  treat single-factor "significance" as a hypothesis rather than a finding.
- Prefer simple, transparent, few-parameter models. **Start with weighted/regression
  approaches — not ML.** Escalate only if backtesting demonstrates the simple model is
  leaving real signal on the table. "We should use machine learning" is not a finding.
- Every added parameter must earn its place against a holdout, not against training fit.

### 6.4 Non-stationarity / regime change

The NFL is not a stationary system. Rule changes, personnel-package trends, and pass-rate
shifts mean older seasons may be actively misleading rather than merely less relevant.

- **How far back to weight is an empirical question, not an assumption.** Test whether adding
  older seasons improves or degrades holdout performance, per position.
- Distinguish "where is this trend in its cycle" from "what is the long-run average." Model
  trend *direction* explicitly rather than treating a 3-year average as a stable baseline.

### 6.5 The baseline rule

**Any ranking version must be measured against baselines, and the headline result is the
comparison — never the raw accuracy number.**

Required baselines:
1. **Market ADP** — what drafters actually did
2. **Expert consensus** — what analysts said (FantasyPros ECR)
3. Prior-season fantasy points, ranked
4. Simple positional-tier heuristic

**Baselines 1 and 2 are both required — founder's ruling, 2026-07-31.** This file previously named
only market ADP while `docs/statistical-guardrails.md` §5 named only expert consensus, and the two
were used interchangeably for a full campaign. **They are different crowds.** Market ADP is the
empirical distribution of drafter behaviour; expert consensus is analyst opinion, and it is what the
shipped board and the availability model actually run on. A version can beat one and lose to the
other, and which it beat is the finding.

If a version does not beat **both** on a holdout season, it has no edge, regardless of how good its
correlation looks in isolation. Report it as a failure and say so plainly. If it beats one and not
the other, report exactly that — not the flattering half.

**Scope, ruled 2026-07-31:** §6.5 binds a *ranking version*. A single feature tested inside one
component of an unshipped model is not a ranking version and is not bound by it — that
misapplication ran through seven factor batches, labelling an arm-vs-primary-model comparison as the
consensus bar.

**When it fires, ruled 2026-08-01 (see §2a):** §6.5 is a **release gate, run once when a ranking
version is declared finished** — not a steering metric consulted per arm during development. Build
against absolute quality measured on realised outcomes; run the four baselines at the end. This does
not weaken the rule: a version that fails §6.5 still has no edge and must be reported as a failure,
in exactly the terms above. It changes only *when* the question is asked, so that development is not
implicitly optimising toward the very benchmark it is supposed to be independent of. The
overfitting protection during development is the sealed holdout (§6.3), not the consensus gap —
the consensus gap never provided that protection and was not doing so.

### 6.6 Evaluation metrics

Rank correlation with actual finish is the starting metric, but it is a proxy. The decision-
relevant question is whether the ranking produces better *rosters*, not better *lists*. Note
this gap explicitly in results; move toward draft-simulation-based evaluation when the harness
supports it.

**Three objects, three metrics — founder's architecture, 2026-08-01. Do not evaluate one with
another's metric.**

> "It seems we need to evaluate each position individually. And then you cross rank. Rankings may be
> different than a draft board which considers vbd. Then the next step is strategy because VBD can't
> account for availability."

| # | Deliverable | The question it answers | Correct metric |
|---|---|---|---|
| 1 | **Positional rankings** | Who is better, *within* a position? | Rank correlation **within position** vs realised finish |
| 2 | **Projected-points ranking (pooled)** | Who will score the most fantasy points this season? | **Pooled** rank correlation vs realised points — valid *for this object* |
| 3 | **Draft board** | What is each player worth *across* positions, for drafting? | Roster quality — **not** rank correlation |
| 4 | **Strategy / pick recommendation** | Who should I take *at this pick*? | Simulated roster outcomes under an opponent model |

**These are separate deliverables, each with standalone value — founder, 2026-08-01: *"It has value
in its own [right]. We probably have multiple deliverables."*** Do not treat 2 as a failed 3, or 3 as
a failed 4. They map onto the founder's three questions in §2, and the layering is why those can be
built in parallel: the board takes a ranking as input, and strategy takes a board plus an
availability model.

**The error this corrects, which PM committed on 2026-08-01 and should not recur — and note the
correction is about *labelling*, not about the statistic.** A pooled cross-positional Spearman
(v2 0.607 against consensus 0.743) was reported as v2's headline **ranking** quality. That number is
a perfectly valid measure of deliverable **2**; it is simply not a measure of deliverable **1**, and
it is not a measure of **3** either — the pooled target is dominated by position, so it rewards
matching the raw points leaderboard rather than draft value.

**PM then over-corrected**, calling the pooled statistic invalid. It is not. **Report both: pooled for
the projected-points ranking, per-position for the positional rankings, and never present one as the
other.**

**Why the third layer cannot be judged on either of the first two.** VBD is a value *stock* — points
over replacement if the season goes as projected. A pick is a *policy*: value now minus what the
pick forgoes later, which depends on who survives to your next pick. **VBD cannot account for
availability**, so a board is never a pick order, and presenting one as the other is the category
error the recommender's hardcoded −25 QB penalty was patching over (see `docs/fable/M2-findings.md`
§M2-3).

---

## 7. League settings

Half-PPR with yardage bonuses. **Verified against the live Yahoo platform 2026-07-27** (league
"Westwood", ID 154693, primary league — see ADR-052, `tests/fixtures/league_scoring_live.json`).
Matches value-for-value. Yardage bonuses confirmed to **stack** at thresholds (a player crossing
multiple thresholds gets all applicable bonuses, not just the highest one).

| Category | Value |
|---|---|
| Passing yards | 25 yds/pt; +1 @ 300, +1.5 @ 350, +2 @ 400 |
| Passing TD | 4 |
| Interception | −2 |
| Rushing yards | 10 yds/pt; +1 @ 100, +1.5 @ 150, +2 @ 200 |
| Rushing TD | 6 |
| Receptions | 0.5 |
| Receiving yards | 10 yds/pt; +1 @ 100, +1.5 @ 150, +2 @ 200 |
| Receiving TD | 6 |
| Return TD | 6 |
| 2-point conversion | 2 |
| Fumble lost | −2 |
| Offensive fumble return TD | 6 |

**Structural constraints:** 4-team playoff, weeks 16–17, no reseeding — confirmed 2026-07-27
against the live platform and matches `league_config.py`'s `playoff_weeks=(16,17)` exactly (see
ADR-052). A slow start is unusually costly — this is a real constraint the model should account
for, not a preference.

**Known gaps — RESOLVED for the primary league, 2026-07-27 (ADR-052):** 10 teams. Roster shape 1
QB / 3 WR / 2 RB / 1 TE / 2 FLEX (W-R-T) / 1 DEF, 6 bench, 1 IR. Both are required inputs for
tier and replacement-level calculations. (Two other leagues exist with different scoring/team
counts, still unconfirmed — see `docs/founder-requests.md` FR-012.)

Do not silently drop the yardage bonuses when implementing the scoring engine — they are real points
and the engine must compute them.

**Retired 2026-07-30, founder's decision.** This section previously claimed the bonuses "reward
ceiling outcomes over floor, which should influence how variance is valued in rankings." The
arithmetic was never in doubt; the *operational* claim is dead, on four independent measurements:

| Instrument | Result |
|---|---|
| WR ceiling ablation | Perfect foresight of every WR's bonus points would improve rank correlation by **+0.026**. That is the hard ceiling on the whole idea; the model built to capture it got +0.0002. |
| RB stacking-bonus transfer | Worth 0.57%–2.39% of realised points; moves **three players by three or more rank positions across 4,792 player-seasons.** |
| Per-player dispersion in the exceedance curve | NULL at every threshold, family and shrinkage — with both arms given the *realised* mean, the most favourable setting available. |
| Skewness and kurtosis (the founder's own proposed mechanism) | Fails upstream: shape does not persist year to year, six of six NULL. Empirical-Bayes τ̂² driven to **exactly zero** — no between-player variance in true shape beyond sampling noise. An oracle arm using the target season's own shape makes bonus error *worse*. |

**Do not re-derive a variance preference from the bonus structure.** It has been tested four ways,
including at its most favourable setting, and there is nothing there. Sources:
`docs/ranking/component-model-wr-pass-1.md` §6.2, `component-model-rb-qb-te-pass-1.md` §6,
`fr086-volatility.md` §3.4, and `docs/strategic-insights.md` §5b.

---

## 8. Agents and gates

The goal is low human touch with real checkpoints — not zero oversight. Bad assumptions
compound silently; the gates exist to catch them without requiring the user to review every step.

The roster is the agent definitions in `.claude/agents/`. That directory is the source of truth for
each role's pinned model and effort; this table says what each is *for*.

| Agent | Role | Model |
|---|---|---|
| **pm** | Sequencing, dispatch, merges, the founder's interface | Opus |
| **ranker** | The proprietary bottom-up ranking — the product's core | Opus |
| **strategist** | Methodology, formula specs, pre-registration. **No database access, deliberately** | Opus |
| **researcher** | External verification, competitive analysis, source audits | Opus |
| **fable** | Adversarial review on a separate weekly budget | Fable |
| **frontend** | The React app | Sonnet |
| **backend** | Python, exports, tests, statistics | Sonnet |
| **librarian** | What is true, where it lives, what was already decided | Sonnet |
| **data-ops** | Capture, ingestion, snapshots | Sonnet |
| **verifier** | Checks a finished branch against the dispatch that produced it. Read-only | Sonnet |
| **operator** | Owns "is the live site current and correct" — the seam no specialist owns. Read-only | Sonnet |

**Gates run at checkpoints, not continuously.** Every build task ends with **verifier**. Every
methodology decision and every completed milestone ends with **strategist + fable**. **operator**
runs at session start, after any merge, and before the founder is told anything is live.

**fable has standing authority to block.** If it identifies a leakage or bias problem, the work does
not advance until resolved. Its mandate explicitly includes flagging over-engineering — building
infrastructure with no current consumer is a finding, not a virtue.

**Neither verifier nor operator may fix what it finds.** Both are read-only by design. An agent that
edits what it just reviewed is reviewing its own work, which is the arrangement the gate exists to
prevent. Findings go back to the owning role as threads.

**Escalate to the user when:** a gate fails twice on the same issue, a decision changes anything
in this file, scope expands beyond Phase 1, or a result looks too good (that is usually leakage,
not skill).

---

## 9. Model routing

| Work | Model |
|---|---|
| Mechanical: data pulls, cleaning, file ops, formatting | Haiku |
| Default build work: implementation, debugging, tests | Sonnet |
| Architecture, statistical methodology, model design, red-teaming | Opus |

Do not default to the largest model. Do not use a small model for methodology. When a task's
tier is ambiguous, say which tier you think it is and why before starting.

---

## 10. Security and hygiene

- No credentials in code, ever. `.env` only, gitignored.
- Prefer official OAuth over browser automation for provider access. Storing a real account
  password for scripted login is a last resort, not a parallel path — it creates a credential
  liability, is brittle, and may violate provider terms.
- Local SQLite file is not committed to version control.
- Respect source licensing and attribution requirements (§5).

---

## 11. Working style

- Concise by default. A few steps at a time, not exhaustive lists.
- Tables over repeated paragraphs for comparisons.
- State confidence. Do not fill gaps with plausible-sounding invention.
- If a premise is wrong, say so before answering.
- Flag bias risk in decision-making, including the user's own priors and the model's.
- Football claims must be grounded in verifiable data from the pipeline, not intuition or
  received wisdom. "Everyone knows X" is a hypothesis to test.

---

## 12. Companion docs

| File | Contents |
|---|---|
| `docs/CODE-MAP.md` | Where things live, answered with `file:line`: how a board is built, where league config enters and where it is bypassed, what the availability model takes and what is hardcoded, what is in the export contract and who reads each field, and what the acceptance harness vs. the mock capture each verify. For giving accurate instructions about the code without reading all of it |
| `docs/can-we-rebuild-the-database.md` | Whether `data/nfl.db` can be rebuilt from the repo plus public sources — measured, not estimated. Yes for 99.3% in ~4 minutes; the three artifacts that could not be are now committed (thread 080). Read before assuming any table can be regenerated |
| `docs/environment.md` | **Read before running any command.** The Windows/conda interpreter path, the PreToolUse hook's block list and its known semicolon false positive, why permission allowlists are not the thing stopping you, commit-message quoting, and the worktree DB and screenshot gotchas. Every fact in it was rediscovered the hard way by an earlier agent |
| `docs/test-registry.md` | The tiered factor list (Tier 0 table stakes / Tier 1 analytics / Tier 2 league-specific), with effort, expected edge, data source, and status per item |
| `docs/deferred.md` | Deliberately postponed decisions and why |
| `docs/decisions.md` | Architecture decision log — what changed, when, and the reasoning |
| `docs/status.md` | **Frozen 2026-07-28**, historical archive only. New session narratives: `docs/status/` (one dated file per session, `tools/status_log.py sync` generates `docs/status/INDEX.md`) |
| `docs/statistical-guardrails.md` | Methodology reference expanding §6 into concrete, checkable procedures. Read before running any backtest; every backtest report must state which checks were applied |
| `docs/product-explanations.md` | Why the product behaves the way it does, in founder-facing language, one idea per entry, each tagged with the surface it would appear on (tour / tooltip / hover). Append to it whenever a session explains a behaviour in chat — chat is discarded, this is not. Source content for the eventual in-app product tour and tooltips (FR-119; **do not build the tour**, the founder deferred it) |
| `docs/factor-ledger.md` | **Every factor considered, with disposition and reason** — 92 rows as of 2026-07-31. This is the multiple-comparisons denominator, written down: without it "we tested N factors" is unverifiable. Check it before testing anything, so a dispositioned factor is not re-run |
| `docs/ranking/factor-campaign-manifest/` | One file per factor batch, sharded so concurrent agents cannot clobber each other. The campaign-level `M` lives here — corrections are computed against the **campaign**, never the batch, or every local correction is defensible while the campaign is not |
| `docs/design/reference-screenshots/` | Standing screenshots of every key surface, regenerated on merge, at two widths in both themes. Design has read access and no running app — this is how it sees current reality instead of speccing against whatever capture someone remembered to take |
| `docs/assistant-context.md` | Curated, current-state-only summary for the in-app assistant's "why" questions. One paragraph per settled decision, no history, no superseded numbers. Edited in place when an ADR supersedes something in it — never appended to. The assistant must read this instead of `decisions.md`/`test-registry.md`, both of which contain figures later entries overwrote |

Keep this file lean. When a section outgrows a paragraph or two, move it to a companion doc and
link it here. An overloaded spec file gets ignored, which defeats its purpose.

## Agent operating rules

### Read at session start, in this order
1. `docs/CURRENT-STATE.md` — canonical project state. Trust this.
2. `docs/environment.md` — how to run commands here without stalling. Read this before your
   first shell call, not after it fails.
3. `docs/operating-model.md` — your role, effort tier, and evidence standards.
4. `docs/founder-requests.md` (archive, frozen 2026-07-28) plus
   `docs/founder-requests/INDEX.md` (everything raised since) — the standing backlog of what the
   founder has asked for.
5. `docs/handoffs/OPEN.md` — your inbox. Open every thread where `TO:` includes your role and
   `STATUS:` is `OPEN` or `BLOCKED-ON-YOU`.
6. Only the specific ADR or doc your task names.

**Do not read `docs/status.md` or `docs/status/` for current state.** `docs/status.md` is a frozen
append-only historical log containing superseded figures stated in the same voice as current
ones — three conflicting "current state" headers and roughly fifteen internal contradictions.
`docs/status/` (its successor) is the same kind of log, just sharded. Read either to learn what
happened, never to learn what is true. Same hazard `docs/assistant-context.md` describes for
`decisions.md`.

### Dispatch, do not absorb
For each thread, use the Task tool to dispatch the agent named in its `TO:` field. Do not work
threads in your own context. Each agent carries pinned `model` and `effort` — `strategist` is
Opus/high, `data-ops` is Sonnet/low — and working in-session discards that, running cheap work
expensively and expensive work cheaply.

### Inter-agent communication
All of it goes through `docs/handoffs/`. Protocol in `docs/handoffs/README.md`. Never rely on a
human to relay a message between agents — assume no human is in the loop.

**Thread IDs, FR IDs, and ADR numbers are never hand-typed.** New threads/FRs are
`YYYY-MM-DD-slug.md`, allocated by `tools/handoffs.py new`/`sync` (`tools/founder_requests.py` for
FRs) with no shared counter — collisions on new items are structurally near-impossible (ADR-064).
Existing `NNN`-numbered threads/FRs keep their numbers forever, never renamed. ADR numbers still
come from `tools/handoffs.py adr next` only — hand-computed numbering caused ADR-048's collision;
full protocol in `docs/handoffs/README.md`.

- Need something from another role? Open a thread. Specify it fully; a half-specified ask costs a
  full session, not a minute.
- Touched a thread? Append a reply and update its `STATUS:`, even if the reply is "no action taken,
  because X." A thread with no reply is indistinguishable from a thread nobody opened.
- Update `docs/handoffs/OPEN.md` in the same session you change a status.
- Only the `TO:` role may set `STATUS: RESOLVED`.

### Capture what the founder says — every session, no exceptions
If the founder expresses a want, a constraint, a preference, or a "wouldn't it be good if" in your
session, record it before you finish: `python tools/founder_requests.py new --raised-by "<where>"
--subject "..."` (see `docs/founder-requests/README.md`). Do not judge whether it is important
enough, and do not wait for it to be formally specced. `docs/founder-requests.md` is frozen
(archive only, do not append there) — new requests get their own numbered file so status updates
later don't collide with another session's. Chat transcripts are invisible to every other agent
and are discarded — a request that never reaches one of these files has, as far as this project is
concerned, never been made.

### Write back, every session
- Update `docs/CURRENT-STATE.md` **in place** — replace stale lines, never append a new section.
  The "Build state" table's machine-measured rows come from `python tools/state.py --apply`
  (`--tests` to also run the suites); don't hand-type those, or the next `--apply` silently
  overwrites your edit. The rows above the markers, and everything outside "## Build state", stay
  hand-edited, one session at a time.
- Write the session narrative to `docs/status/YYYY-MM-DD-role-slug.md` (new file, never an edit to
  another session's), then `python tools/status_log.py sync` to regenerate
  `docs/status/INDEX.md`. `docs/status.md` is frozen — do not append there.
- New decision → an ADR in `docs/decisions.md`.
- Contract schema change → bump the version **and** open a handoff thread to `frontend`.
- **PM only: sweep dead agent worktrees before ending a session.** Each costs ~0.9–1.0 GB and
  nothing removes them automatically; 49 of them filled the disk to 100% on 2026-07-30 and cost a
  running agent real time. Merge first, then remove — procedure in `docs/environment.md` §4b.

### Completion reporting
Report commit hash and test count. Not prose summaries.

**UI and visual work is never "done" on your own report.** State it as "built, pending screenshot
verification," and attach a screenshot. A fully green test suite has already coexisted with an
entirely missing screen in this project, because no test asserted the screen existed.

### Dashboards
`docs/dashboard.html` and `docs/roles-workflow-map.html` are point-in-time snapshots, not live
systems. If you materially change project state, either regenerate them or note in your reply that
they are stale. Better: replace `dashboard.html` with a generator script that reads
`CURRENT-STATE.md` and `handoffs/OPEN.md`, so it can never drift.
