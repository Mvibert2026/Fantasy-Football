# Founder requests — the standing backlog

**Every agent, in every surface, must append here.** If the founder says anything in a Claude Code
session, in the Cowork chat, or to Design that expresses a want, a constraint, a preference, or a
"wouldn't it be good if" — it gets an entry here before that session ends. Do not judge whether it
is important enough. Do not wait for it to be formally specced.

The reason is simple: chat transcripts are invisible to every other agent and are discarded. A
request made in a Backend session that never reaches this file has, from the project's point of
view, never been made. Every agent reads this file at session start, so an entry here is common
knowledge across the whole team.

**Append only.** Never delete an entry. Change its `Status` and add a `Resolution` line. A request
the founder made and we decided against is a decision worth keeping — it stops the same question
being re-litigated in six weeks by an agent with no memory of it.

**Status values:** `NEW` · `SCOPING` · `SPECCED` (has an ADR or spec) · `IN PROGRESS` ·
`SHIPPED` · `DECLINED` (with reasoning) · `DEFERRED` (with unblock condition)

---

## FR-001 — Research / aggregation section

**Raised:** 2026-07-26, Cowork chat · **Status:** `SCOPING` · **Thread:** [009](handoffs/009-research-aggregation-audit.md)

> "we need a research section (probably part of prep and maybe inseason) that allows you to see
> other public rankings or takes, anything we can aggregate"

**As stated:** a place in the product — Prep mode primarily, possibly Season mode too — surfacing
other public rankings and takes, aggregated.

**Initial read (mine, not the founder's):** this is closely adjacent to two things already in the
roadmap and should not be built as a separate silo. Fable scope item 5 is a multi-consensus
benchmark layer (FantasyPros ECR, Sleeper consensus, the league's own historical ADP, real 2025
draft results, all as distinct datapoints). Fable item 6 is newsfeed aggregation. FR-001 reads as
the **user-facing surface** of those two, which are currently specced as backend capabilities with
no UI attached.

That framing matters for sequencing: the honest order is source audit → what can we legally and
technically aggregate → then design the surface. Designing the screen first would produce a
beautiful mock of data we may have no right to display.

**Known constraints that will shape it** — these are established facts, not guesses:
- FFC's `robots.txt` disallows `/api/`, `/ajax/`, `/adp/csv/`. Not scrapeable.
- FantasyPros free tier caps at 10 rows per response with broken pagination.
- Sleeper and Underdog expose no public aggregate ADP.
- MFL ADP works but samples ~50 hobbyist mocks — usable, must never be presented as this league's
  own tendency.
- Redistributing another service's rankings has licensing implications the project has deliberately
  not examined yet (currently private-use only). This becomes load-bearing the moment the product
  is public.

**Open question for the founder, not yet answered:** is the goal *aggregation* (a computed
consensus across sources) or *comparison* (see what each source says, side by side, and decide for
yourself)? The Reddit voice-of-customer work points hard at comparison — the upvoted sentiment was
explicitly against blind deference to an aggregate, and in favour of forming your own opinion. Those
are different products with different data requirements.

**Audit result, 2026-07-26 (researcher, thread 009 → `docs/research/source-audit-2026-07.md`).**
Two of the "established facts" above need correcting, and one new founder decision falls out.
- *FFC "not scrapeable"* — narrower than stated. Only `/adp/csv/` is robots-disallowed; the HTML ADP
  pages are not. FFC stays blocked, but on unretrievable ToS rather than on robots.txt.
- *FantasyPros* — the 10-row cap describes the old free API. FantasyPros now sells tiered API
  licences, and **redistribution rights exist only on the Commercial tier** (price not public);
  Premium is $8.99/mo and expressly personal/non-commercial. New entry **D-020** in
  `docs/decisions-needed.md`.
- *The "takes" half of this request cannot be built from any audited source.* Every prose source —
  RotoWire, ETR, 4for4, FootballGuys, PFF, ESPN — prohibits reproduction of its content in writing.
  Third-party takes on a screen is a licensing purchase, not an engineering task.

---

## FR-002 — Reduce founder involvement over time

**Raised:** 2026-07-26, Cowork chat · **Status:** `IN PROGRESS`

> "Ideally I have to be less and less involved"

Standing directive, not a feature. It reframes every process decision: prefer the option that
removes a future founder touchpoint, even at higher one-time setup cost.

Concretely this is why the repo mailbox exists rather than the founder relaying messages, why
`tools/handoffs.py check` is wired into the test suite rather than trusted to habit, and why the
fidelity harness (thread 007) is worth building rather than continuing to rely on manual screenshot
review.

**Irreducible founder touchpoints** — things no agent can do, which should stay short and rare:
budget decisions, taste and judgment calls, interactive auth (`/design-login`), connecting folders,
and physically running mock drafts. Everything else should be migrating away from the founder.

---

**Addendum, 2026-07-27 (Fable extended-mandate session, captured per FR-003):** the founder,
before going to sleep, said: *"you are allowed to run what you need to instead of ask me each
time"* and *"I want you to do a lot of work without needing human intervention, don't let me
stop you from doing what you were told."* Read as a session-scoped grant of overnight autonomy
and a reaffirmation of FR-002's direction: when the founder is away, agents proceed under
standing authorization rather than blocking on permission — within each mandate's own written
isolation rules, which the same session kept fully in force (branch-only code, no master
writes).

## FR-003 — All founder statements become common knowledge

**Raised:** 2026-07-26, Cowork chat · **Status:** `SHIPPED`

> "I want anything I say here or in the Coding chats to be common knowledge"

**Resolution:** this file, plus a rule in `CLAUDE.md` requiring every session to read it at start
and append to it at end. Enforcement is social rather than mechanical for now — if it slips, the
next lever is a checklist item in the mailbox health check.

---

## FR-004 — Rigour is the default; escalate rather than loosen

**Raised:** 2026-07-26, Cowork chat · **Status:** `SHIPPED`

> "make sure every decision is made with absolute rigor in mind, I will tell you to loosen if it's
> too restrictive, let me know where and when you need those decisions"

Standing directive governing every judgment call in the project.

**The rule.** When a decision has a rigorous option and a convenient one, take the rigorous one and
record it in `docs/decisions-needed.md` with the rigorous default stated explicitly. Do not block
waiting for an answer, and do not loosen on your own authority. The founder intervenes only to
loosen.

**Why this shape.** It inverts the usual escalation cost. Normally an unavailable decision-maker
produces a stall or a quiet shortcut; here, silence produces the conservative outcome. That makes the
founder's absence safe rather than expensive, which is the point of FR-002.

**What it forbids specifically.** Reasoning of the form "the founder would probably be fine with
this." That inference is precisely what the register exists to prevent — it is how a project's
standards erode without anyone deciding to lower them.

**Where it lives:** `docs/decisions-needed.md`, read at session start alongside `CURRENT-STATE.md`.

---

## FR-005 — The analysis engine IS the product

**Raised:** 2026-07-26, Cowork chat · **Status:** `NEW` — reframes the roadmap, needs sequencing work

> "statistical and mathematical and strategic rigor is what sets us apart - the ability to test
> theories and scenarios, we need to be a big time data and analysis shop as well, it's an engine"

Founder directive on identity, not a feature request. It changes how existing work should be
prioritised.

**What it reframes.** The project has been treating the backtest and simulation machinery as
supporting infrastructure for a draft app. This says the reverse: the engine is the asset, and the
draft interface is one thing the engine drives. Under that reading, several items currently filed as
"gaps" are actually the core asset being underbuilt:

- `backtest.py` has no bootstrap confidence intervals anywhere. Its point estimates are, in the
  project's own words, close to meaningless.
  **Correction, 2026-07-27 (backend, thread 019):** this claim is stale. Season-level bootstrap
  CIs (`bootstrap_season_ci`, `paired_bootstrap_delta_ci`) were built in an earlier session
  (ADR-021/ADR-028) and every reported metric already carries an interval and its n. Thread 019
  asked for this build and was closed as already-satisfied rather than re-implemented. What
  remains true from this bullet: at n=4-5 seasons every interval is `degenerate=True` and wide —
  the honesty problem this bullet raises is real, just already surfaced by the existing code
  rather than absent from it.
- `_rank_correlation` pools positions, so it can report healthy numbers for a model with zero real
  skill.
- There is no draft-slot simulation metric, so no strategy question can currently be answered
  properly (this is the same missing layer as P3-4 and the #44 finding).
- Every test is bespoke. There is no harness for "pose a question, run it, get an answer with error
  bars" — which is precisely the capability this directive names.

**The tension to hold, stated plainly.** Rigour plus thin data produces mostly refusals. Alpha
detection is closed until ~2028. `NEED_ADJUSTMENT_SCALE` is unidentifiable. Beating consensus cannot
be claimed from four seasons. An engine that mostly answers "not yet knowable" is honest but not
differentiating on its own.

**The way through — worth reading carefully, it changes what to build.** The power problem is not
uniform across question types. It depends entirely on the resampling unit.

- **Season-outcome questions** ("does our rank beat consensus", "is there alpha") resample at the
  *season* level. n = 4. Minimum attainable p ≈ 0.0625 before any correction. Structurally
  unanswerable now, and no amount of compute changes it.
- **Draft-mechanics questions** ("what does a 15-pick gap cost", "how does slot 3 differ from slot
  8", "when does a positional run actually start") resample at the *draft* level, and drafts can be
  simulated in unlimited quantity. These are answerable to tight intervals **today**.

So the engine's near-term output should be simulation-based scenario answers, not
predict-the-season claims. That is also where the product's competitive gap sits — nobody ships
calibrated draft-mechanics analysis — and it does not require waiting until 2029.

**Implied sequencing change.** Draft-slot simulation (currently P3-4, deferred as "a bigger lift")
moves up. It is the single capability that converts rigour from a constraint into an output. Bootstrap
CIs and the per-position correlation fix are prerequisites, not chores.

**Not yet decided:** whether this justifies pulling simulation work ahead of the Opponents tab and
other interface gaps before this season's draft. That is a founder call — see
`docs/decisions-needed.md`.

---

## FR-006 · A conversational partner during the live draft

**Raised:** 2026-07-27. **Status:** captured, not scheduled. Founder explicitly said not to build it
now.

> "I wonder if it makes sense to hook up a model to talk to during the draft about my draft and
> strategy, I'd like that, we don't need to build it out now, but that's how I think I want it to
> work."

**What this actually is, and why it is not the same as the existing chatbot.** D-014 already reversed
the LLM-renderer deferral and put a Haiku-backed assistant in the app for the founder to interrogate
the back end while learning what is broken. That is a **debugging surface**. FR-006 is a different
product: a **strategy interlocutor during a live draft**, under a clock, that knows the board state,
the founder's roster, the survival probabilities, and the opponents' needs — and can be argued with.

**Why this is architecturally significant rather than a feature request.** The current engine answers
*"who should I take?"* with a ranked list and a probability. A conversational partner has to answer
*"why not the other guy?"*, *"what happens if I wait a round?"*, and *"who's about to get squeezed at
my position?"* — which are counterfactual and multi-step. Those are questions about the *simulation*,
not the current board. It likely needs the lookahead work (thread 045) to be real, and it needs the
recommendation to already carry its reasoning (thread 049) rather than having a model invent a
rationale after the fact.

**The failure mode to design against, stated now so it is not discovered later.** A chatty model with
access to real probabilities will happily produce fluent justifications that are not the model's
actual reasoning. That is the single most dangerous thing this project could ship — it would defeat
the traceability discipline that everything else is built on, and it would do so persuasively. The
constraint should be that the assistant may **only** surface computed quantities and may not generate
a rationale the engine did not produce. Establish that before the feature is scoped, not during.

**Dependencies:** 045 (lookahead), 049 (reasoned recommendation), 027/028 (opponents and predictions
surfaces). Not startable before those.

---

## FR-007 · Cover every table stake, regardless of edge value

**Raised:** 2026-07-27. **Status:** standing principle, effective immediately.

> "I don't care if it's table stakes, not edge. By definition, we need all the table stakes covered."

**Context.** The PM had characterised known-suspension handling as "table stakes, not alpha" and
suggested it should not count toward the project's edge case. The founder rejected the implied
prioritisation.

**The principle.** Correctness floor comes before edge, unconditionally. It is not a trade-off to be
weighed per feature.

**Why this is stronger than it sounds, and why the PM was wrong.** Edge is worthless if the floor
leaks. A ranking with a real 5% edge plus one catastrophic omission is *worse than consensus*, because
the founder cannot tell which rows are affected and therefore cannot trust any of them. Table-stakes
failures do not average out the way modelling error does — they are concentrated on individual
players and severe. One suspended player ranked as a full-season starter discredits all 300 rows, and
reasonably so.

**Operational consequence.** A **table-stakes inventory** is now a required deliverable — the
exhaustive list of things any credible ranking must get right, each with verified / not-verified /
unknown status. Verification means an **executable check in the test suite**, not an assurance that
someone looked. Items that cannot be re-verified after the next data refresh are not covered.

This gates the edge work: no result from the proprietary ranking effort is worth reporting until the
floor items are verified or explicitly listed as known gaps.

**Specified in:** `docs/fable-mandate-2026-07-27.md` § 2C, Part 5.

---

## FR-008 · Move thinking out of the clock window

**Raised:** 2026-07-27. **Status:** active — specified in `docs/handoffs/059-on-deck-recommendations.md`.

> "Some of the 'on the clock' information and potential recommendations and considerations at my pick
> would be nice instead of only on my pick. I'd like to be able to review those recommendations ahead
> of time under less pressure."

**The general principle, which extends past the originating feature.** The founder wants to do his
reasoning in the fourteen picks *before* his turn, not in the ninety seconds *of* it. Any feature
that shifts cognitive load out of the clock window is worth more than its apparent size, and any
feature that adds load inside it should be justified against this.

**The design consequence that makes it non-trivial.** A recommendation for a future pick cannot be
the same object as a recommendation at that pick — the intervening picks have not happened. The
honest form is **conditional**: a small decision tree over the likely board states, built from the
survival model the product already computes. Showing the current recommendation early would be
answering a question that has not been asked yet.

**Why it matters strategically.** It converts the survival model from a number into a plan, and it is
the object FR-006's draft-time chatbot needs in order to answer *"what happens if I wait a round?"*
without inventing a rationale. Build order therefore runs FR-008 → FR-006, not the reverse.

---

## FR-009 · The projection must know WHICH weeks, not just how many

**Raised:** 2026-07-27 (Fable session 4 mandate). **Status:** specified — ADR-E amendment E-A1
(on branch `fable/ext-2026-07-27`), sonnet work orders R3-A/R3-B ready.

> "Redefine the projection output as a week-indexed vector rather than a season aggregate.
> Points = games played x points per game x usage ramp. [N3] is one primitive serving
> suspension valuation (games 1–N missed are the LOW-leverage ones; championships are weeks
> 15–17), bye cost, and in-season start/sit. Specify it once, name every consumer."

Three consumers were blocked on the shape during Fable's absence: T4's suspension
games-adjustment, bye-week cost, N3's leverage weights. All three now read from E-A1 §A1.
One verification rider captured with it: the founder's "weeks 15–17" vs `league_config.py`'s
`playoff_weeks=(16,17)` — check on the live platform during the T2 visit (one minute).

## FR-010 · Registration-before-code as the deliverable standard

**Raised:** 2026-07-27 (Fable session 4 mandate). **Status:** standing.

> "Register the prediction BEFORE fitting, and commit the registration before the experiment
> code exists... If you cannot finish the run, LAND THE REGISTRATION ANYWAY so a sonnet agent
> can execute it in your absence. A registered, unexecuted experiment is a complete
> deliverable; an unregistered finished one is not."

The founder has now stated this as the project's definition of done for experiments, not just
a methodology preference. Applied to V7 this session (registered `5af349e`, code after,
falsified honestly). Any agent running an experiment in this repo owes the registration
commit first.

## FR-011 · Draft date — readiness target, not the real date, and it's provisional

**Raised:** 2026-07-27, Claude Code (PM session). **Status:** `SPECCED`.

> "Draft date: 30 August 2026, provisional. T-7d = 23 August. Anchor the pre-mortem checklist
> to it. Mark provisional so it can move."

**Resolved during this session, do not re-litigate without new founder input:** the screenshots
in `docs/screenshots/League Settings *.png` show the Westwood (Yahoo, primary) league's actual
scheduled draft is **2026-09-07**, not 2026-08-30. Asked directly; founder's answer: *"let's just
use August 30th to make sure everything is ready then"* — 2026-08-30 is a deliberate **readiness
buffer target**, not a claim about when any league actually drafts. Do not treat the two dates as
a contradiction to resolve; they are different things (target-ready-by vs. actual-draft-date) and
both are true. T-7d = 2026-08-23 anchors the pre-mortem checklist. The other two leagues' (see
FR-012) actual draft dates are still unknown.

---

## FR-012 · Three real leagues, not one — T1 must pull consensus per scoring format

**Raised:** 2026-07-27, Claude Code (PM session). **Status:** `SCOPING` — blocked on founder
data for leagues 2 and 3. **Thread:** [067](handoffs/067-t1-multiformat-consensus-rescope.md).

> "MULTIPLE DRAFTS, and this changes T1's scope. Three leagues: Primary: custom scoring,
> current config. Yahoo: different scoring, different team count. ESPN: different scoring,
> different team count. T1 must pull consensus per scoring format, not just half-PPR, and the
> board must build per league with team count carried through — replacement levels move with
> roster count. Coordinate with the multi-league thread rather than opening new work."

**Clarified this session, in order, because the first framing was wrong:** the founder dropped
Yahoo league-settings screenshots (`docs/screenshots/League Settings 2-5.png`, `League Info
1.png`) that turned out to match CLAUDE.md §7's documented scoring exactly, for a 10-team league
named "Westwood." Asked directly rather than assumed: **Westwood is the primary league** (just
Yahoo-hosted) — it is not a separate "Yahoo, different scoring" league. Asked a follow-up because
that changed the count: it is still **three leagues total** — Westwood (Yahoo, primary, 10 teams,
scoring now confirmed), **a second, distinct Yahoo league** (different scoring, different team
count, no data yet), and **an ESPN league** (~12 or 14 teams, founder unsure which, different
scoring, no data yet).

**What this resolves for free:** CLAUDE.md §7's "known gaps — league size not yet confirmed" is
answered for the primary league: **10 teams**, roster shape QB/WR/WR/WR/RB/RB/TE/W-R-T/W-R-T/DEF
+ 6 bench + 1 IR, per `League Settings 4.png`. Backend session closing T2 (see FR-013) is updating
CLAUDE.md and CURRENT-STATE.md with this.

**What this does not resolve:** leagues 2 and 3's scoring/team-count/roster data. No agent can
synthesize this — it needs the same two screenshots Westwood provided (league-settings page +
scoring table), from the founder, for each of the other two leagues.

**Update, same day:** founder supplied league 2's data (`docs/screenshots/Yahoo League 2
settings*.png`) — "Ethan's Expert League," Yahoo, 12 teams, offline draft, **no yardage bonus
tiers** (a real scoring difference from Westwood, not just team count), INT at Yahoo's default
-1, and a Kicker starter slot Westwood doesn't have. Full transcription in thread 067's reply.
Founder explicitly said ESPN (league 3) is "not ready just yet" — thread 067 is unblocked for
league 2 and proceeding without waiting on ESPN.

**Correction, same day:** *"Ethan's expert league may likely only end up being 10 people, treat
it as a 10 person league unless otherwise directed."* The screenshot's "Max Teams: 12" is the
platform's configured slot count, not a confirmed roster of 12 real participants — the founder
expects it to fill to 10. Building/replacement-levels should use **10**, not 12, until the
founder says otherwise. This is a founder override of a measured screenshot value, not a
correction of a transcription error — keep both facts on record (screenshot says 12, founder
directs treating it as 10) rather than quietly overwriting one with the other.

**Cost, stated per the founder's own instruction to say what it costs:** T1 was budgeted 1
sonnet-session-unit for one format (half-PPR, matches Westwood — no rework needed there). Adding
leagues 2/3 is roughly **+1 to +1.5 session-units**, and carries a hard data ceiling: FantasyPros
only exposes STD/HALF/PPR presets, not arbitrary custom scoring. Each of leagues 2/3 gets matched
to its *closest* preset with the divergence explicitly flagged (which knobs differ, by how much)
— never silently presented as that league's true consensus. Full spec and dependency on the
founder's screenshots: thread 067.

---

## FR-013 · Yardage bonuses VERIFIED to stack — T2 closed

**Raised:** 2026-07-27, Claude Code (PM session). **Status:** `SHIPPED`.

> "VERIFIED: yardage bonuses STACK at thresholds. Founder confirmed from the live platform page
> today. The existing >= loop in scoring.py is correct. Record the verification with today's
> date in decisions.md and close T2's open question. Founder has Yahoo screenshots for the
> fixture."

**Resolution:** the screenshots are `docs/screenshots/League Settings 2-5.png` (Westwood/Yahoo,
primary league) — the same ones that resolved FR-012's team-count question. Backend session
dispatched this turn to: transcribe the scoring table into `tests/fixtures/league_scoring_live.json`,
assert it against `scoring.LEAGUE`, and record an ADR in `decisions.md` closing T2 with today's
date. One honesty note carried into that ADR: the screenshot shows the threshold *tiers*, not a
worked example proving additive stacking — the stacking determination itself rests on the
founder's direct platform verification, not on something visible in the settings page. That
distinction should be stated in the ADR, not glossed over.

---

## FR-014 · Recurring injury and suspension feed, full NFL

**Raised:** 2026-07-27, Claude Code (PM session). **Status:** `SPECCED`. **Thread:**
[070](handoffs/070-recurring-injury-suspension-feed.md).

> "NEW: recurring injury and suspension feed, full NFL. Injuries: automatable from nflverse
> (2009+, includes practice participation). Build the recurring pull. Suspensions: no reliable
> structured source. Maintained watchlist plus a weekly researcher web sweep. Do not build a
> probability model — known suspensions only, deterministic games deduction. Both feed
> E[games_played] per ADR-E Amendment E-A1. Make it recurring, not one-off. State the cadence."

**Resolution:** dispatched as thread 070 to `data-ops` + `researcher`. Cadence specified in the
thread: injuries pulled weekly in-season (nflverse practice reports move week to week);
suspensions get a weekly researcher sweep on the same cycle so both land in the same
`as_of_date` window. Explicitly **not** a probability model — a hand-maintained watchlist with
`current_as_of`, feeding E[games_played] as a deterministic deduction, per the founder's own
instruction and consistent with [[FR-007]] (table stakes are unconditional, not traded against
edge). Cross-references thread 057 (still open) to avoid re-litigating whether a structured
suspension source exists if that thread already answered it.

---
## FR-015 · Crosswalk before board rewire — sequencing directive on thread 053

**Raised:** 2026-07-27, Claude Code (PM/orchestration session). **Status:** `IN PROGRESS`.
**Thread:** [053](handoffs/053-founder-csv-ingestion.md).

> "Do not rewire make_board.py yet. Fix the crosswalk first. 78 skill players from the Half-PPR
> CSV failed to resolve, including 2026 rookies who may go in the first few rounds. Rewiring the
> board onto the new source before those resolve makes them invisible — worse than the
> wrong-format board they'd replace, because a missing player gives no signal at all."

**The reasoning, worth keeping attached to the rule.** A visibly-wrong-format board still shows
every player, so the founder can mentally discount it. A board silently missing 78 names —
including rookies who could go round 1-3 — gives zero signal on those players and no visible cue
that anything is wrong. Founder judged the second failure mode strictly worse than the first,
which is why sequencing (crosswalk fix before rewire) matters more than speed here.

**Explicit instruction on method:** no silent fuzzy matching on the crosswalk refresh. If fuzzy
matching is used at all, it must be gated at a stated threshold and every match logged. Anything
still unresolved after the refresh gets reported by name, not dropped quietly.

**Explicit exclusion:** the 32 quarantined DST/defense rows are **structural, not a bug** — no
individual `gsis_id` exists for team defenses by construction (same permanent gap
`src/ingest_rankings.py` already documents). Leave them quarantined; they are not part of this
fix.

**Sequence directed:**
1. Refresh the player-ID crosswalk against the 78 unresolved skill/K names from thread 053's
   ingestion (`rankings_quarantine` table, `source='fantasypros_csv_2026draft'`).
2. Only then rewire `make_board.py` onto `fantasypros_csv_2026draft`.
3. Rebuild and confirm: total player count, that the 2026 rookie class is present on the board,
   and that the app header shows the new source and scoring format.

---

## FR-015 · Fix the crosswalk before rewiring the board onto the new CSV source

**Raised:** 2026-07-27 (founder directive, relayed via Claude Code session to `data-ops`).
**Status:** DONE — see `docs/handoffs/053-founder-csv-ingestion.md` data-ops reply, 2026-07-27.

> "Do not rewire make_board.py yet. Fix the crosswalk first. 78 skill players from the Half-PPR
> CSV failed to resolve, including 2026 rookies who may go in the first few rounds. Rewiring the
> board onto the new source before those resolve makes them invisible — worse than the
> wrong-format board they'd replace, because a missing player gives no signal at all."

Resolved 72/78 via a `nflreadpy.load_players()` supplement to the existing `load_ff_playerids()`
crosswalk (rookies present in the former, missing from the static latter snapshot) plus one
hand-verified nickname alias (Hollywood Brown -> Marquise Brown, explicitly logged, not fuzzy
matching). 5 named players remain genuinely unresolved (Tommy Myers, Devonte Boyd, Matt Hibner,
Graig Cooper, Desmond Reid) — absent from every source checked, most likely undrafted rookies not
yet on a roster snapshot. `make_board.py` rewire is still blocked on backend pickup, but the
crosswalk half of the block this directive named is resolved.

---

## FR-016 · The "refresh data" popover could not be cleared

**Raised:** 2026-07-27 (founder, relayed into this round's frontend task rather than a direct
Claude Code session — capturing it here now since it had not reached this file yet, per the
capture-every-session rule).
**Status:** SHIPPED — see the frontend workstream-C session, 2026-07-27
(`frontend/ui/components/RefreshData.tsx`, `frontend/ui/lib/dismiss.ts`).

The founder reported that the "Refresh data" popover in the top bar (`frontend/ui/components/
RefreshData.tsx`) would not clear. Root cause: the popover only ever closed via its own in-panel
"Dismiss" button — no click-outside, no Escape — so the two ordinary ways a person tries to get
rid of a floating message both silently did nothing. Fixed, and the whole app audited for the same
gap class (two more real instances found and fixed: `PlayerDetail.tsx`'s side sheet was missing
Escape despite its close button being labelled "esc"; `AssistantDock.tsx`'s expanded panel had
neither). 11 new enumerated tests, one per surface. See `docs/status.md`'s 2026-07-27 workstream-C
entry for full detail.

---

## FR-017 · Draft day runs on the dev server only; make autoSync failure visible in-app

**Raised:** 2026-07-28 (founder mandate for the overnight frontend chain, threads 069/073).
**Status:** OPEN — checklist half done (pre-mortem T-1d and T-2h sections updated,
2026-07-28); the in-app failure surface is unbuilt.

Two connected directives:

1. **Run the app via the dev server on draft day. Do NOT use `vite preview` or a built dist
   bundle.** Auto-sync of `data/export/` -> `frontend/public/data/` runs only as dev-server
   middleware (`frontend/server/autoSync.ts`); a built bundle snapshots its data at build time
   and will silently serve a stale board. Captured as checklist items in
   `docs/reviews/fable-draft-day-premortem-2026-07-27.md` (T-1d and T-2h).
2. **autoSync currently fails open with a console-only error. Make that failure visible in-app
   before 30 August.** Until it lands, the checklist's manual fallback is keeping the browser
   console open. This is frontend work with a hard date; it was NOT built in the 069/073
   session (out of that mandate's scope) and needs its own pickup.
