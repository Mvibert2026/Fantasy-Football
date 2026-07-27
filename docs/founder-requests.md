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
