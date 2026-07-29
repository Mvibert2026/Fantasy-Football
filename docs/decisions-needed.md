# Decisions needed from the founder

**Standing rule: rigour is the default, and silence is consent to it.**

Every entry below states the rigorous option and the cost of taking it. If the founder says nothing,
agents take the rigorous option and proceed — no one blocks waiting for an answer. The founder
intervenes only to *loosen*. That inverts the usual escalation cost: being unavailable produces the
conservative outcome rather than a stall.

Agents: when you hit a decision, add it here rather than deciding silently or asking in chat. State
the rigorous default explicitly, because that is what will happen if nobody replies. Never loosen a
default on your own authority — "the founder would probably be fine with it" is exactly the reasoning
this file exists to prevent.

**Status values:** `OPEN` (awaiting, default will be taken) · `DEFAULTED` (default taken, still
reversible) · `DECIDED` (founder answered) · `LOCKED` (acted on, expensive to reverse)

**This file is canonical for decision status.** `docs/decisions.md` is the append-only historical
log of *why* — a reading hazard for "what's true now" per `docs/assistant-context.md`. When an entry
here flips to `DECIDED`/`CLOSED`/`LOCKED` and that changes product behaviour, reflect it in
`docs/CURRENT-STATE.md`/`docs/assistant-context.md` too, so the three documents can't silently
diverge.

---

## D-001 · `NEED_ADJUSTMENT_SCALE` — delete, or keep tuning it?
**Status:** OPEN · **Raised by:** strategist, ADR-A · **Needed before:** Backend implements ADR-A

**Rigorous default:** delete the parameter, or convert it to a bounded constraint. Do not adopt 10.0
and do not fit a value.

**Why.** The parameter enters the product only through an `argmax`, so the objective is piecewise
constant in it — data can never select a point value, only an interval of behaviour. Any reported
figure like "9.4" would be fabricated precision. Separately, the superiority test that would justify
*any* value cannot clear multiple-comparisons correction on 4 seasons: minimum attainable p is 0.0625
with a single test at infinite effect size. It needs ~9 usable seasons, i.e. roughly 2029.

**Cost of rigour.** If the need term genuinely helps and the constraint bound undershoots, points are
left on the table. This is undetectable with current data.

**To loosen:** say so, and 10.0 stays with an `ARBITRARY` provenance tag visible in the methodology
surface. It will not be presented as measured.

---

## D-002 · Retract past rank-correlation figures, or annotate them?
**Status:** OPEN · **Raised by:** strategist, ADR-B · **Needed before:** Backend rewrites `_rank_correlation`

**Rigorous default:** retract. Remove them from docs rather than adjusting them.

**Why.** The current function pools all positions before correlating, which manufactures correlation
from between-position mean differences. A model with *zero* within-position skill — ordering players
randomly inside each position — still posts a healthy pooled number, because QBs outscore TEs. Within-
position ordering is the only skill that matters at a draft. The figures do not measure a weaker
version of the right thing; they measure a different thing.

**Cost of rigour.** Losing the only correlation numbers currently on record, with nothing to replace
them until the rewrite lands.

**To loosen:** keep them with a prominent "pooled, not comparable" warning. Not recommended — the
project's own experience is that warnings on stale numbers get read past.

---

## D-003 · Show ranks for positions where ordering skill is unproven?
**Status:** OPEN · **Raised by:** strategist, ADR-B · **Needed before:** Frontend implements the band table

**Rigorous default:** positions whose measured ordering skill is indistinguishable from noise show
**tiers only, no rank number**. On current samples that likely means TE, QB, and DEF, since at n≈20
the confidence interval spans roughly ±0.32 and will frequently contain zero.

**Why.** Showing a precise rank the data cannot support is the exact false-precision failure the
competitive research identifies in rivals. The product's differentiation is honest uncertainty; a
rank number that means nothing contradicts it directly.

**Cost of rigour.** A visible product downgrade. Three of five positions lose their rank column, and
users will notice.

**To loosen:** show ranks everywhere with the correlation and sample size disclosed on the column
header. Defensible, and closer to what competitors do.

---

## D-004 · `delta = 0.10` ships unvalidated — accept, or set to zero now?
**Status:** DEFAULTED (currently shipping at 0.10, flagged) · **Needed before:** the draft

**Rigorous default:** leave it at 0.10 **only** if it is visibly flagged as an unvalidated prior, and
honour the existing pre-registered rule — if the need+run model does not beat marginal-only on Brier
across ≥30 conforming mocks, set it to zero.

**Why.** The pre-registered rule already exists and was written before any data was seen. Honouring it
is the whole point of pre-registration. But note the binding practical fact: with 1 of ~30 mocks
logged, the test will not run before this season's draft, so 0.10 ships untested either way.

**Cost of rigour.** None if flagged. The risk is drift — an unvalidated constant quietly becoming
"the value we use" through familiarity.

**To loosen:** nothing to loosen. The alternative is setting it to zero now, which is *more*
conservative, not less — and would discard a plausible effect on no evidence.

---

## D-005 · The research section — aggregate, or compare?
**Status:** OPEN · **Raised by:** FR-001 · **Needed before:** the feature is specced

**Rigorous default:** **comparison** — show each source side by side and let the user decide. Do not
compute a blended consensus.

**Why.** Two reasons converge. The voice-of-customer work found the upvoted sentiment explicitly
against blind deference to an aggregate and in favour of forming your own view. And a computed blend
requires defending a weighting scheme across sources of very different quality — a free parameter with
no way to validate it, which is the same identifiability problem as D-001.

**Cost of rigour.** More screen space, more user effort. A single blended number is easier to consume.

**To loosen:** ship a blend, but it must show its weights and let them be inspected.

---

## D-006 · Is the 853 MB database tracked in git?
**Status:** OPEN · **Needed:** now — it worsens with every commit

**Rigorous default:** verify with `git check-ignore -v data/nfl.db`. If it is tracked, stop committing
it immediately and plan a history rewrite deliberately rather than in a hurry.

**Why.** Git stores a full copy of a binary file on every commit where it changed. At 853 MB the
repository becomes unusable quickly, and — since there is no remote — a botched history rewrite has no
backup to recover from.

**Cost of rigour.** Ten minutes to check. A rewrite, if needed, is a careful hour.

**To loosen:** nothing here is loosenable. This is either true or it isn't.

---

## D-007 · A git remote as backup?
**Status:** OPEN · **Needed:** before the draft

**Rigorous default:** create a private remote. Not for agent coordination — that is solved — but
because the entire project currently exists on exactly one disk, and several destructive git commands
are one typo away from unrecoverable.

**Why.** It is also the precondition for loosening permissions further. Broad auto-approval is
defensible with a remote as a backstop and hard to defend without one.

**Cost of rigour.** Free, roughly fifteen minutes, and D-006 must be resolved first — pushing an
853 MB tracked database is its own problem.

**To loosen:** an external drive backup instead. Weaker, but not nothing.

---

## D-008 · Recompute blocking behaviour in Settings
**Status:** OPEN · **Raised by:** the Settings editor design session · **Needed before:** Frontend builds it

**Rigorous default:** hard-block the interface for the ~60-second recompute, with staged progress.

**Why.** Principle #3 forbids any number showing a partially-updated value. Letting users navigate
during a recompute means marking every affected number stale everywhere, and a single missed spot is
a silent violation of the principle. Blocking makes correctness structural rather than dependent on
exhaustive coverage.

**Cost of rigour.** A 60-second wall. Genuinely annoying, and it will be the most-complained-about
interaction in the product.

**To loosen:** allow navigation with a global stale treatment. Requires an audit proving every
affected surface honours it — that audit is the real cost, not the design work.

---

---

## D-009 · Does the engine come before the interface this season?
**Status:** DECIDED — 2026-07-26 · **Outcome:** deadline pressure removed by the founder

**Decision.** The founder has stated the draft deadline is no longer a constraint. That resolves this
in the direction the rigorous default argued *against*: with no hard date, the case for rushing
interface completion disappears, and the engine work FR-005 describes can be sequenced on merit
rather than on the calendar.

**What changes:**
- Draft-slot simulation (P3-4) is no longer gated behind "finish the screens first."
- Mock collection is still urgent, but for a different reason — mocks cannot be collected
  retroactively and preseason mock lobbies thin out after the draft window regardless of whether we
  care about this year's draft. The chain 002 → 025 → Mock Lab UI keeps its priority.
- The "five weeks" framing should be removed from planning documents. It is no longer true and it
  distorts sequencing.

**What does not change.** Every rigour default in this file stands. Removing a deadline removes an
excuse for shortcuts; it does not license any.

**Still open, and now the real question:** with time no longer scarce, what *is* the binding
constraint? Current answer: data volume and founder attention, in that order. Worth putting to Fable
as part of candidate 3, reframed — not "engine or interface before the draft" but "what should this
project optimise for now that it is not optimising for a date."

---

## D-009-ORIG (superseded) · Does the engine come before the interface this season?
**Status:** SUPERSEDED · **Raised by:** FR-005 · **Needed before:** the next sprint is scoped

**Rigorous default:** finish the interface gaps first (Opponents tab, rosters endpoint), and build
simulation capability second.

**Why that is the conservative choice.** The draft is roughly five weeks away. An app with missing
screens is a concrete, certain failure on draft day. Simulation capability is high-value but
open-ended, and an unfinished simulation layer helps nobody in September.

**Why you might loosen it.** FR-005 says the engine *is* the product. Draft-mechanics questions are
answerable to tight intervals right now, because they resample at the draft level rather than the
season level — unlike every season-outcome question, which is blocked until ~2029. That is the one
place rigour currently produces answers instead of refusals, and it is unclaimed by any competitor.
A case exists for building it before polishing screens.

**Cost of rigour.** The engine work slips past this season, and the first real draft runs on an app
that is complete but analytically thin.

**To loosen:** say so, and I re-scope the sprint around draft-slot simulation, accepting that the
Opponents tab may not exist for this year's draft.

---

## D-010 · Block scoring edits during a live draft?
**Status:** OPEN · **Raised by:** Design, Settings editor · **Needed before:** Frontend builds it

**Rigorous default:** block them, and show the reason rather than greying the control silently.

**Why.** A scoring change invalidates every projection, replacement level, ranking and availability
figure. Doing that mid-draft means the board a user is actively picking from changes underneath them
during a ~60-second window when Principle #3 forbids showing partial results. Design's reference
implementation blocks it and recommends blocking.

**Cost of rigour.** A user who genuinely mis-entered their scoring rules is stuck with wrong numbers
for the whole draft. That is a real scenario and it will feel awful.

**To loosen:** allow it behind an explicit confirmation that states what will happen. Design's own
framing is that this trades flexibility for trust.

---

## D-011 · Auto-apply a finished recompute if the tab closes mid-job?
**Status:** OPEN · **Raised by:** Design, Settings editor · **Needed before:** Frontend builds it

**Rigorous default:** do not auto-apply. Hold the result and apply on the user's next visit, with
their confirmation.

**Why.** Design's reasoning, which I agree with: ambush is worse than staleness. A user who returns
to find every number silently changed has lost the thread of what they did, and the product's whole
proposition is that numbers are traceable and never change under you unannounced.

**Cost of rigour.** A completed 60-second computation sits unapplied. The user waits again, or at
least clicks again, for work already done.

**To loosen:** auto-apply with a persistent, dismissable notice saying what changed and when. Weaker,
but not unreasonable.

---

## D-012 · User edits again while a recompute is running
**Status:** OPEN · **Raised by:** Design, Settings editor · **Needed before:** Frontend builds it

**Rigorous default:** auto-restart the job and tell the user plainly that it restarted.

**Why.** The alternatives are worse: queueing two jobs risks applying them out of order, and blocking
edits during a 60-second window is hostile when the user is likely fixing a mistake they just spotted.
Restarting is the only option that cannot produce a wrong final state.

**Cost of rigour.** The clock resets. A user making three quick edits waits three times.

**Depends on:** thread 015, question on `superseded` — the server needs that response for this to work.

---

## D-013 · Who can edit league settings?
**Status:** OPEN · **Raised by:** Design, Settings editor · **No recommendation from Design**

**Rigorous default:** single editor — the league owner — until there is a reason otherwise.

**Why.** Design explicitly declined to recommend here, correctly: it is a permissions question, not a
design one, and it changes the design materially. Multiple editors means the pending-change banner
needs an actor name, and the whole flow needs a concurrency story that has not been designed. Starting
single-editor keeps the design honest and defers complexity that may never be needed — this is a
10-team home league, and the product is currently personal-use.

**Cost of rigour.** If co-commissioners turn out to matter, this is a rebuild of the flow rather than
an addition.

**To loosen:** say so early. This is the one decision here that is expensive to change later, because
it is structural rather than behavioural.

---

## D-014 · Reverse the LLM-renderer deferral?
**Status:** SUPERSEDED — 2026-07-28 · **The 2026-07-26 approval below is withdrawn. Both threads
it authorized — 032 (dev-mode Haiku assistant) and 033 (query-interface spec) — are PAUSED per the
founder's 2026-07-27 instruction on thread 050 ("Threads 032 and 033 are explicitly paused by the
founder — do not pick them up"), reaffirmed 2026-07-28. Thread 050's instruction stands; this
entry's "DECIDED" status below no longer authorizes anyone to act on either thread.** This entry
and thread 050 previously contradicted each other (this said "approved, spec via 033"; 050 said
"paused, do not pick up") — the founder resolved the contradiction 2026-07-28 in favor of the
pause. See the thread 050 reply for the mirror of this note.

**Original 2026-07-26 entry, preserved for the record, no longer authoritative — see status line
above:**

**What the founder asked for:** "a very futuristic chatbot there, especially if it can see the back
end to answer the questions."

**What is approved:** an LLM **query interface** — the model selects which typed tool to call against
real data, and reports what came back. Spec first via thread 033, build after.

**What remains deferred:** the LLM **narrator** — a model that receives facts and writes prose
interpreting them. The code's own warning stands: it will produce fluent, confident, causal sentences
whether the data supports them or not.

**Why this is not a fudge.** These are different systems with opposite risk profiles. A narrator
decides what facts *mean*, so its errors are invisible and persuasive. A query interface decides only
what to *look up*; the database decides what is true, and provenance is structural rather than
promised. The query interface is arguably the strictest implementation of Principle #1 in the product
— the model has no way to obtain a number except through a named field.

**The line that must hold:** no interpolation between retrieved facts. Reporting `p_survive = 0.33`
from `availability.json` is fine. "Player X is undervalued" is not — and not merely because it is
unsupported, but because the board computes no player-level opinion at all
(`evaluative_adjustment` is always null, by design).

**Still open:** whether to build after the ADR lands. That is a fresh decision with a cost dimension
attached — this is the first component with a per-interaction API cost.


---

## D-015 · Is the 30-mock target per league, or global?
**Status:** OPEN · **Raised by:** Design, Mock Lab · **Needed before:** the progress affordance is built

**Rigorous default:** **per league configuration.** The availability model's behaviour depends on
league size, scoring, and roster shape, so 30 mocks spread across a 10-team half-PPR and a 12-team
full-PPR validate neither.

**Cost of rigour.** Brutal. It means the 24-config matrix would each need their own 30, which is never
happening. In practice it means calibration is claimed for **one** configuration — the founder's own
league — and explicitly not claimed elsewhere.

**To loosen:** treat 30 as global and state the configuration mix alongside any calibration claim.
Weaker, but honest if the mix is disclosed.

---

## D-016 · Do other users' mocks count toward the target?
**Status:** OPEN · **Raised by:** Design, Mock Lab · **Design recommends:** keep personal primary

**Rigorous default:** personal mocks are primary; others' are stored but pooled separately and never
silently merged.

**Why.** A mock logged by someone else may come from a different room, a different platform, and a
different level of care in entry. Pooling them inflates n while degrading the thing n is for. Design
reached the same conclusion independently.

**Cost of rigour.** Reaching 30 stays slow, because it stays one person's work.

---

## D-017 · Are partial mocks acceptable?
**Status:** OPEN · **Raised by:** Design, Mock Lab · **Design recommends:** accept, with `rounds_logged`

**Rigorous default:** accept them, recorded with `rounds_logged`, and weight or filter at analysis time
rather than at entry.

**Why.** Availability predictions are most interesting in early rounds anyway, and a user who abandons
at round 8 has still produced eight rounds of real evidence. Rejecting partials discards data and
punishes the exact behaviour we are trying to make easy. Design's recommendation is right.

**The catch to specify:** partial mocks are not missing at random — people abandon when a draft gets
boring or lopsided, which may correlate with the outcomes being predicted. Record the field, and treat
"can partials be pooled" as a separate question for the analysis stage rather than assuming yes.


## D-018 · Take the model's own prediction off the Mock Lab entry screen?
**Status:** DEFAULTED · **Raised by:** strategist, ADR-D (thread 034) · **Needed before:** Frontend builds the entry surface

**Rigorous default:** yes. During entry the shortlist is the **top five available by frozen board
rank**, in board order, with **no probabilities shown**. A randomised 10 of 30 mocks show no shortlist
at all (typeahead only). Review and calibration screens are unchanged.

**Why.** Presenting the hazard model's own answer as the cheapest thing to record creates a feedback
loop between the estimator and its own data collection. The design praised one direction of that loop —
better calibration makes logging faster — but it is a single arrow: cheaper logging also makes the model
look better calibrated. The resulting error is *differential* (correlated with the quantity measured),
so it biases toward the claim and cannot be bounded from the contaminated data. At a 5% substitution
rate it moves a bucket by ~3.3 points against a stated ±6 half-width.

**Cost of rigour.** A number comes off a screen. Board-rank top-5 covers fewer picks than the hazard
model's, so a few percent more picks need typing — measurable after the fact, since the hazard top-5 is
still stored. The 10 blind mocks cost roughly **30 extra minutes across the entire programme**, and the
headline calibration interval widens from a contaminated ±6 to an honest ±14 or so.

**To loosen:** restore the hazard-model shortlist with probabilities. Then the absolute calibration
claim ("when it says 33%, it happens a third of the time") is not defensible from this data at any
sample size, and only the relative claim — hazard beats its baseline — survives.

**Trigger for a later, real founder call:** after 6 mocks, if board-rank top-5 coverage is more than 10
points below the hazard model's counterfactual coverage, a new entry is raised here with the measured
minutes-per-mock cost attached. Not askable now — there is no number yet.

---

## D-019 · Widen the Mock Lab evidence ladder from ±6 to ±8–10?
**Status:** DEFAULTED · **Raised by:** strategist, ADR-D · **Needed before:** Frontend builds the progress affordance

**Rigorous default:** widen it. Every interval in Mock Lab is computed with a mock-level design effect,
or by mock-level bootstrap.

**Why.** `MOCK-LAB-SPEC.md` §5 states the ladder is "the real 95% Wilson half-width at that sample
size." Wilson assumes independent Bernoulli trials, and picks within a mock are not independent — same
drafters, same board trajectory, same session, same fatigue state. With ~32 picks per bucket per mock
the design effect `1+(m−1)ρ` is 1.62 at ρ=0.02 and 2.55 at ρ=0.05, so the true half-width is 1.3–1.6×
wider. The honest figure at 30 mocks is **±8 to ±10 points**.

**Cost of rigour.** The one affordance designed to make the grind feel worthwhile gets visibly worse:
every rung of the ladder moves the wrong way, and 30 mocks buys less than the screen currently promises.

**To loosen:** nothing defensible. Shipping ±6 is the same false-precision failure this project
criticises in competitors' composite scores, on the product's own headline claim.

---

## D-020 · Which FantasyPros licence does the research section need?
**Status:** OPEN · **Raised by:** researcher, thread 009 audit · **Needed before:** FR-001 is specced

**Rigorous default:** build nothing that *displays* a third-party ranking beyond what the current
licence permits. Concretely: FantasyPros ECR may be used for our own computation and shown to the
founder alone; it does not go on any surface another person can see until a licence covering that
exists.

**Why this is a new decision and not D-000 again.** D-000 priced the *site subscription* and
correctly chose the logged-in CSV export. The audit found something D-000 did not evaluate:
FantasyPros now sells a tiered **API** licence, and **"redistribution rights" is a named feature of
the Commercial tier only** `[VERIFIED]`. Free is non-production/sample data. Premium is $8.99/mo and
expressly "personal & non-commercial". So retrieval has three cheap legal routes and display to a
third party has exactly one, whose price is not public. The same shape holds for the CSV export the
founder already uses: sanctioned retrieval, no display licence.

**Cost of rigour.** FR-001's comparison view ships showing our own numbers, MFL proxy ADP, and
nflverse injury designations — and for anyone other than the founder, an ECR column that cannot be
rendered. That is a visibly thinner screen than the feature request implies.

**To loosen:** two separable asks, and they should not be bundled. (a) *Stay private:* confirm the
product remains single-user, in which case Premium at $8.99/mo is sufficient and the question is
$108/yr, not a negotiation. (b) *Go public:* authorise a Commercial-tier sales conversation with
FantasyPros. Only (b) unblocks showing ECR to another human.

**Related and unanswerable by us:** displaying third-party *prose takes* — the other half of FR-001 —
is prohibited in writing by every source audited. That is a purchase, not a build. See
`docs/research/source-audit-2026-07.md` §5.

---

## Resolved

| ID | Decision | Outcome |
|---|---|---|
| D-000 | FantasyPros paid tier | **DECIDED** — no purchase. Use the logged-in CSV export; no scraper will be written. *(Scope note, 2026-07-26: this decided the site subscription. The API licence tiers are a separate question — see D-020.)* |
| D-021 | Fantasy Football Calculator ADP history | **DECIDED 2026-07-27 — LOOSEN.** Founder authorised harvesting FFC ADP history back to 2007 for private use. See below. |

---

## D-021 · Fantasy Football Calculator — decided, loosen

**Founder decision, 2026-07-27:** *"Yes get the ADP back to 2007 it's ok being loose. This is personal
use. Just get it."*

**What the rigorous default would have said.** Stay blocked. FFC's `/robots.txt` disallows
`/adp/csv/`, and their Terms of Service page returns 404 — under FR-004, terms that cannot be read
are treated as prohibitive.

**Why the founder overrode it, and why that is defensible.** The objection here is materially weaker
than the ones blocking ESPN, Yahoo and CBS, which carry *explicit written* prohibitions on automated
collection. FFC has no such clause — it has an unreadable one. The tool is single-user, private, and
displays nothing to a third party. FR-004 makes rigour the default; it does not make it absolute, and
this is exactly the case it invited the founder to loosen.

**Binding constraints that remain.** The HTML pages at `/adp/<format>` are *not* robots-disallowed;
`/adp/csv/` is. Use the HTML endpoints. Rate-limit conservatively (≤1 request/sec), identify the
client honestly, cache locally and pull each season-format once — never on a schedule. Data is for
model input and backtesting only. **If the product ever ships to a second human, this decision is
void and must be re-taken.** Recorded as a founder override of a PM default, not as a finding that
the default was wrong.

**Executing thread:** `docs/handoffs/055-ffc-adp-history-harvest.md`

---

# Founder decision round — 2026-07-27

Six decisions settled in one sitting. Recorded here in full; the resolved table above is the index.

## D-003 · RESOLVED — show ranks, structurally flagged

**Founder decision:** show rank numbers at TE/QB/DEF, with the unproven status made visible.

**Departure from the rigorous default,** which was tiers-only. Accepted: a thinner board at three
positions is a real usability cost on draft day, and the founder is the only user and knows the
caveat.

**Implementation constraint — this is the part that matters.** A footnote or legend is not
sufficient. Flags are ignored under a draft clock; that is the known failure mode and the reason the
rigorous default existed. The unproven status must be **structural**: the rank number itself rendered
in a visibly distinct treatment at those positions, unmissable without reading anything. Frontend to
spec it against the design system rather than inventing a marker.

**Re-evaluate** when per-position n rises materially above ~20. This is a decision about current
sample size, not a permanent product choice.

## D-015 / D-016 · RESOLVED — harvested drafts count, tagged, both numbers reported

**Founder decision:** calibrate against harvested drafts *and* own drafts, showing both numbers
side by side rather than one blended figure.

**What this requires, and it is not optional:** two separately-computed calibration estimates, each
labelled by population, displayed together with the gap between them visible. The harvested estimate
is the working number; the own-drafts estimate is the one that matters and it will be noisy for a
long time. **The two must never be averaged.**

**The bias being accepted, stated plainly so it is not forgotten:** FFC mock drafters are not the
founder's league. They are more aggressive on rookies, have no keeper dynamics, and abandon drafts
partway. The convergence (or divergence) between the two numbers as real drafts accumulate is itself
the most informative output of this design — if they track each other, harvested drafts are a valid
proxy and the calibration problem is solved cheaply. If they diverge, we have learned something
important that a blended number would have concealed.

**D-016 follows:** other users' drafts are stored in the harvested pool, tagged by source, never
silently merged into the personal pool.

## D-017 · DEFAULTED — partial mocks accepted with `rounds_logged`

Unchanged from the rigorous default. Accept them, record `rounds_logged`, filter or weight at
analysis time rather than at entry. Newly relevant: harvested FFC drafts will include abandoned
mocks, so this field is now load-bearing rather than a nicety.

## D-001 / D-004 · RESOLVED — delete the knob, keep the bump with its kill switch

**Founder deferred to the rigorous default** after the implications were explained in draft-day terms.

- **`NEED_ADJUSTMENT_SCALE`: delete.** Do not adopt 10.0, do not fit a value. The need effect is
  already measured as `lambda = 0.352`; a second unmeasured multiplier stacked on a measured effect is
  the precise mechanism by which a model gets tuned to its author's expectations and becomes
  unfalsifiable. If a bounded constraint is genuinely needed for numerical stability, that is a
  different thing and must be argued as such.
- **`delta = 0.10`: keep, visibly flagged as an unvalidated prior**, and honour the existing
  pre-registered rule — if need+run does not beat marginal-only on Brier, it goes to zero
  automatically without a further decision. Zeroing it now was considered and rejected: run behaviour
  in drafts is real and well documented, so a hard zero is cleaner but likely less accurate.

## D-007 · DEFERRED by founder — revisit before the draft

**Founder decision:** leave it for now. He intends to set up GitLab once the tree is clean, and will
attempt to resolve the flagged GitHub account first.

**Risk restated once, then dropped.** The project exists on one disk. The exposure is not disk
failure, it is the destructive git commands agents run routinely — a bad reset or rebase is currently
unrecoverable. Repo is 11.5 MiB with the database untracked, so setup is minutes whenever he wants it.
**PM will raise this exactly once more, before the draft.** Not to be re-raised in the interim.

## Closed without founder input — standing positions already answered them

| ID | Resolution |
|---|---|
| D-006 | **CLOSED.** Empirically resolved: `nfl.db` is not tracked, `.gitignore` covers it, repo is 11.5 MiB. No history rewrite needed. |
| D-013 | **MOOT.** Single-user tool; the founder is the only editor. Re-opens if the product ever ships to a second human. |
| D-020 | **CLOSED — no licence needed.** The founder has stated the tool is private, personal, and displayed to nobody. FantasyPros ECR may be used for our own computation and shown to him. Re-opens on any second user, alongside D-021. |

---

# New — raised 2026-07-27, unanswered

## D-023 · A mixed-source board — bottom-up at some positions, the old curve at others?
**Status:** OPEN · **Raised by:** strategist, ADR-E (thread 048) · **Needed before:** Backend ships any bottom-up projection

*(Numbered from D-023: `D-022` was claimed the same day by the concurrent backend session for the
2025-in-exports holdout question — see `status.md`, thread 052 entry.)*

**Rigorous default:** adopt the bottom-up projection **per position independently**, only where it beat
the refit baseline out-of-sample, and **name the source on each board row**. Positions that did not
clear the bar keep the ADR-016 rank-derived curve.

**Why.** Forcing one global adopt/reject either discards signal at the positions where it was
demonstrated, or ships unearned signal at the positions where it was not — and which of the two
happened would be invisible in the output. Per-position adoption is the only version where the claim
attached to each row is true of that row.

**Cost of rigour.** The board is heterogeneous. Two rows with the same `projected_points` were produced
by different methods with different error characteristics, and cross-positional VBD comparisons
inherit that. It also adds a per-row provenance field to the export contract and a visible marker in
the UI.

**To loosen:** say so, and the board uses one method everywhere — but then the weaker positions carry a
projection whose accuracy was never demonstrated, presented identically to the ones where it was.

---

## D-024 · The live latency budget for simulation lookahead
**Status:** OPEN · **Raised by:** strategist, ADR-F (thread 045) · **Needed before:** Backend sizes the simulation and decides which degraded rung is the live default

**Rigorous default:** 2.0 s p95 from "opponent's pick entered" to "card updated," and **the card always
names the mode that produced its number** — including at full quality. No silent degradation.

**Why 2.0 s and not the pick clock.** The binding constraint is not the clock; it is that a user
reading a card mid-draft will not wait, and a stale card is worse than a simpler one. Two founder
inputs would sharpen this and only he has them: **the actual pick clock in the league**, and whether he
would rather have a slower, fuller answer or a faster, explicitly-degraded one.

**Cost of rigour.** A mode line on the card is visual noise on every pick, and a tight budget may force
the lookahead down to a re-ranker of the VBD top-5 rather than an independent search.

**To loosen:** say so, and the budget widens or the mode line moves into a tooltip. Note that silent
degradation is *not* on offer as a loosening — a product whose central claim is rigour cannot have an
invisible quality switch, and a user comparing this round's degraded number to last round's full one
would not know they are different quantities.
