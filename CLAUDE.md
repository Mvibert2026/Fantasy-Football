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
attribution). Respect attribution requirements. For scraped sources, check terms before
building the scraper, not after.

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
1. Consensus market ADP
2. Prior-season fantasy points, ranked
3. Simple positional-tier heuristic

If a version does not beat consensus ADP on a holdout season, it has no edge, regardless of
how good its correlation looks in isolation. Report it as a failure and say so plainly.

### 6.6 Evaluation metrics

Rank correlation with actual finish is the starting metric, but it is a proxy. The decision-
relevant question is whether the ranking produces better *rosters*, not better *lists*. Note
this gap explicitly in results; move toward draft-simulation-based evaluation when the harness
supports it.

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
