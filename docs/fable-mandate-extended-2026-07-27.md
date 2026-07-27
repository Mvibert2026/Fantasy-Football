# Fable — extended mandate, 2026-07-27 (session 2)

**SUPERSEDED BY `docs/fable-mandate-4-final-2026-07-27.md`.** This ran; do not re-run it — read the
final mandate for what comes next.

**Supersedes** `docs/fable-mandate-2-rankings-2026-07-27.md` (never run — its questions were covered
by session 1) and `docs/fable-mandate-3-ranking-design.md` (folded in below as Priority 1).

## Read first, do not redo

Session 1 already delivered, in `docs/reviews/`:

- `fable-workflow-2026-07-27.md` — parallel workflow, work orders W1–W10
- `fable-table-stakes-2026-07-27.md` — 20-item floor inventory, T1–T10
- `fable-consensus-anchoring-2026-07-27.md` — the board is openly 100% consensus-derived
- `fable-consensus-claim-2026-07-27.md` — the 2028/2029 claim, S1–S3
- `fable-overfitting-2026-07-27.md` — forking paths and holdout bindingness, H1–H4

**Read the anchoring review before anything else.** It establishes this mandate's premise: the shipped
board gives every player at the same positional rank the same projection, so **player-level edge is
structurally zero**, and the genuinely bottom-up ranking does not exist yet. ADR-E is the plan for it.

Do not repeat session 1's analysis. Build on it.

---

## Standing rules

- **Write only to `docs/reviews/`.** Do not modify `src/`, `frontend/`, `docs/CURRENT-STATE.md`, or
  anything under `docs/handoffs/`. No production code. No thread replies. Do not unseal the holdout.
- **You are hired to refute, not confirm.** Every document in this repo is advocacy written by the
  people being evaluated — the PM's most of all. Cite file and line. Where evidence is absent, write
  "unresolved" rather than filling the gap. If something survives your attack, say so plainly.
- **Work the priorities in order. Finish what you start.** A completed Priority 2 beats a partial 2
  plus a partial 3.
- **You have substantial budget. Spend it.** Stopping early to be economical is not the goal.

## Reporting protocol

**Create `docs/reviews/FABLE-EXT-2026-07-27.md` before any analysis**, containing only the plan and
`STATUS: STARTED`. Then keep it current at every milestone — assume you may be cut off at any moment.

```
STATUS: STARTED | IN PROGRESS | COMPLETE | STOPPED — <where and why>
LAST UPDATED: <milestone>

## What I have done          <one line each, naming the file>
## What I was doing          <in-flight item, how far>
## What I did not reach      <remaining, in the order I'd take them>
## Headline findings         <stated IN FULL here, not as pointers>
## Next steps                <ranked, concrete, actionable without me>
## What I would do with more budget
```

Write each finding to its file as soon as it is complete. Never accumulate output intending to write
it later. If you sense you are running short mid-item, **stop and write.**
`STOPPED — halfway through P2 Q3, no conclusion` is a good outcome recorded. A note implying more
completeness than exists is the only unacceptable one.

---

# PRIORITY 1 — will ADR-E actually produce edge?

Session 1 asked whether ADR-E survives a circularity attack. **Nobody has asked whether it is a good
model.** This is the largest gap in the project: the differentiator does not exist yet, and this is
the design that is supposed to become it.

**Q1 · Where is the edge supposed to come from, and is that source real?** State, in your own words,
the specific mechanism by which this design beats a wisdom-of-crowds aggregate. Then attack it.
Evaluate these separately rather than hoping they aggregate — for each, say whether ADR-E captures
it, whether we have the data, and crucially whether it is plausibly **mispriced** rather than merely
measurable. The bar is not "we can compute this," it is "consensus does not already."

- **Touchdown regression** — a 14-TD season anchors human perception; TD rate regresses hard.
  Probably the most reliable single edge available.
- **Vacated opportunity** — departing targets, carries and red-zone touches do not redistribute the
  way consensus assumes.
- **Scheme and personnel turnover** — new coordinator, quarterback, line. Requires projecting rather
  than remembering, where humans are weak.
- **Age curves at the tails** — decline is not linear and consensus is late.

**Q2 · Is the architecture right?** The most robust finding in fantasy projection is that
**opportunity is predictable and efficiency is not** — snap share, target share, carry share, route
participation and red-zone usage persist; yards per target, yards per carry and above all touchdown
rate regress hard. Does ADR-E separate these into distinct stages with regression strength
**estimated rather than assumed**? If it does something different, is the different thing better —
argue it rather than defaulting to convention.

Also the layer above: **points = games played × points per game × usage ramp.** Three founder
requests (injury duration with recovery ramp, suspensions, bye weeks) are all statements about the
first factor and are not expressible until it is separated out. Does ADR-E have that decomposition?
If not, that is a design gap, not a feature request.

**Q3 · Is a distributional ranking the better objective?** Consensus publishes **no uncertainty** —
ECR is one number per player. A ranking producing a distribution (median, a genuine interval, ideally
P(top-N at position)) could beat consensus **on decisions** without beating it on point rank, because
draft decisions are made under uncertainty and consensus supplies none. Two players with identical
ECR are not the same asset if one is a locked-role veteran and the other a rookie splitting carries.
And calibration is **testable on 26 seasons today**, with no dependence on consensus history — which
matters because session 1 found the beat-consensus clock has not started. Argue it either way.

**Q4 · What is the ceiling?** State *before* looking at any result: what fraction of season-to-season
fantasy variance is plausibly explainable at all? Much is injury and touchdown luck, forecastable by
nobody. A model explaining 45% may be near the ceiling; treating that as failure against an imagined
80% is a misreading this project is prone to.

**Q5 · What would you build instead?** Designing from scratch against the founder's goal — measurably
better across draft prep, live draft and in-season — what is the central abstraction? Say so even if
the answer is ADR-E. Especially then.

→ `docs/reviews/fable-ranking-design-2026-07-27.md`, with work orders.

---

# PRIORITY 2 — the in-season half of the product

**Half the founder's stated goal, and there is not one thread on it.**

The engine is a hazard model over a pick sequence — a draft-time availability engine. The goal spans
draft prep, the live draft, **and in-season management.**

- Inventory what exists per phase, from the code, not the roadmap. The PM's untested prior: ~85% live
  draft, draft prep served incidentally by rankings, in-season essentially absent.
- Are waiver priority, start/sit, trade valuation and playoff-odds-aware risk **expressible in this
  engine**, or do they need a different core? They are not "who survives to my next pick." Answering
  now is cheap; answering after in-season work is bolted onto the draft engine is not.
- Is the data layer general enough, or shaped around draft-time snapshots?
- **Week-weighting is the shared primitive.** Championships are decided in weeks 15–17, so a player
  missing weeks 1–8 loses low-leverage games. The same weighting serves suspension valuation, bye-week
  cost, and in-season start/sit. Is it anywhere? If not, specify it once.

**Verdict:** the architecture extends / extends with named modifications / in-season needs a separate
engine and the current design will fight it.

→ `docs/reviews/fable-in-season-2026-07-27.md`, with work orders.

---

# PRIORITY 3 — draft-day pre-mortem

The draft is weeks away and is **the one unrepeatable event in this project.** Everything else can be
redone.

Assume it is draft day and it went badly. **Work backwards: what failed?** Not hypotheticals — failures
grounded in this repository's actual history and current gaps. Seeds, deliberately incomplete:
suspension and roster-status tables unbuilt (2A review); ADP snapshot too stale to reflect draft-day
behaviour; the wrong league selected, or settings wrong for the league being drafted; the app reading
a shadow data directory again; database locked or mid-migration; recompute too slow under a real
clock; autopick misread as a manual pick; undo mis-applied; the machine or app dying mid-draft with no
remote and no recovery path.

→ `docs/reviews/fable-draft-day-premortem-2026-07-27.md`: failures ranked by likelihood × damage, each
with the cheapest prevention or detection, plus a **printable morning-of checklist.** The checklist is
the point.

---

# PRIORITY 4 — the acceptance harness (your own nomination)

Session 1's "what I would do with more budget" was: make the thread-063 trigger-table pattern
executable — a scripted founder-loop smoke check that drives the dev server, commits picks, asserts
the suggester stays shut, and screenshots the board, run at the end of every frontend round.

**Design it.** It addresses the single most persistent failure in the project: the founder is the
regression sensor, and the PM cannot see the running application. Every dependency reportedly already
exists in the repo or its permissions.

Specify the harness, what it asserts, how failures are reported, and how it plugs into round closeout
so it is standing rather than ad hoc.

→ `docs/reviews/fable-acceptance-harness-2026-07-27.md`, with work orders.

---

# PRIORITY 5 — the draft-time assistant's honesty constraint (only if budget remains)

FR-006 wants a conversational partner during the live draft — argue about "why not the other guy?"
and "what if I wait a round?"

**The failure mode to design against:** a fluent model with access to real probabilities will happily
produce persuasive justifications that are not the engine's actual reasoning. That would defeat the
traceability discipline everything else rests on, and do it convincingly.

Design the constraint system: how does an assistant surface only computed quantities and never
generate a rationale the engine did not produce? Is that enforceable structurally, or only by
convention? If only by convention, say so — that changes whether the feature should be built.

→ `docs/reviews/fable-assistant-constraint-2026-07-27.md`.

---

# BUILD AUTHORISATION — added 2026-07-27

**You may write code**, under the isolation rules below. This supersedes the "no production code" line
in the standing rules. Everything else there still holds.

## Isolation — non-negotiable

**Work in your own git worktree on your own branch. Never merge. Never touch `master`.**

You established in session 1 that worktrees already exist under `.claude/worktrees/` and that one
branch holds finished work nobody can see. Use the same mechanism, and do not repeat that failure —
your landing note must make anything you build *impossible to miss*.

- Create a branch named `fable/ext-2026-07-27`.
- Other agents may be running against `master` right now. Concurrent writes to the same files are the
  exact silent-overwrite class you documented. **Isolation is what makes this authorisation safe** —
  without it, it would not be granted.
- **Do not merge, rebase onto master, or open anything on master.** The founder or PM decides what
  lands.

## What you may build

**Additive work only** — things that can be deleted cleanly and cannot change existing behaviour:

- **T2–T10 table-stakes checks.** Best candidate by far. They are tests: they cannot break behaviour,
  and running them tells us which floor items are actually broken today rather than merely
  unverified. **Report what they find** — a failing check is a finding, not a build error.
- **H1–H4** — the log-audit test, `load_season` rename, pre-registration gate wiring, connect-allowlist
  test. Small, self-contained, and they close the "seal binds against accident only" gap.
- **The acceptance harness (Priority 4).** Do not merely design it — **build it.** Driving the dev
  server, committing picks, asserting the suggester stays shut per thread 063's trigger table,
  screenshotting the board. It was your own highest-value nomination and it is new tooling in new
  files, so it carries no collision risk.
- **W1/W2 slug allocation and the PM outbox**, on your branch only. Note that the PM's announced
  "allocate from ≥100" rule is broken exactly as you diagnosed; build the real fix rather than that.

## What you may not build

- **Anything that changes existing production behaviour** — `make_board.py`, the ingest path, the
  export contract, the hazard model, anything under `frontend/`. Those need review and a founder in
  the loop. Design changes to them belong in your review documents, not in code.
- **Anything under `docs/handoffs/`.** Agents are live in that directory.
- **`tools/handoffs.py` on master.** On your branch is fine; it is the coordination substrate and
  merging it while agents run is how the system eats itself.
- **T1 (half-PPR ECR pull).** Highest-value fix in the project, and precisely why it is not yours to
  do unsupervised — it changes every number the founder sees, and the existing fix is sitting in an
  unmerged branch that needs a human integration decision first.

## Sequencing

**Analysis before building.** Priorities 1–3 are worth more than any code you would write, and they
are the things only you can do. Build after them, or interleave building into Priority 4 where it
belongs — but do not start on code before Priority 1 is delivered.

## Report

Add a **`## What I built`** section to the landing note:

- The branch name and how to see it — `git log fable/ext-2026-07-27` and the diff command. Assume the
  reader does not know the branch exists.
- Every file added or changed, one line each.
- **What the new checks actually found.** This is the most valuable output of the build phase; a
  table-stakes check that fails is a live defect discovered.
- Test results — run them.
- **A merge assessment per item:** safe to merge as-is / needs review because X / do not merge, built
  for illustration only.
- Anything you started and did not finish, named explicitly so it is not mistaken for complete.

**Silent non-delivery is the failure to avoid.** You found finished work invisible on an unmerged
branch. Do not become the second instance.

---

## BUILD — the headline item: a working bottom-up ranking prototype

Founder request: *"I'd love it to start creating a bottoms-up ranking, running tests etc."*

**Do this.** It is additive by definition — a new model in new files, backtested — so it changes
nothing the founder currently sees and carries no collision risk on your branch. Build it immediately
after Priority 1's design verdict, before Priorities 2–5.

**The point is not a finished production ranking.** It is a validated prototype with honest numbers,
so that for the first time the project knows whether a bottom-up model can beat anything at all.

### Discipline — this is the difference between a real result and an overfitting machine

Twenty-six seasons plus a large budget plus an optimiser will find something whether or not anything
is there. These are not optional.

- **Register the metric before you fit anything.** Within position always — cross-position rank
  correlation is invalid (thread 021). **Draft-weighted** — RB2 vs RB6 is worth the season, WR88 vs
  WR93 is worth nothing. State the weighting scheme and do not change it afterwards.
- **Walk-forward by season.** Train to year *t*, predict *t+1*, advance. Nothing fitted on data
  postdating what it predicts — including feature normalisation and replacement levels.
- **Report per-season results, never pooled.** A pooled average hides a model that worked in four
  seasons and failed in eight. The per-season series *is* the finding.
- **Dumb baselines are mandatory:** last season's points, last season's positional rank, position
  average, and a volume-only model. **If it cannot clearly beat last-season-rank, nothing else you
  report matters.** Most published projection systems quietly fail this. Report it first.
- **Also baseline against the current consensus board** — that is what it must eventually replace.
- **Log every variant you try**, including ones abandoned in thirty seconds. That log is the
  multiplicity denominator. Report how many models you effectively evaluated and what it does to the
  honest interpretation of your best result.
- **Intervals, bootstrapped at season level.** 26 seasons is 26 clusters — workable, and far better
  than the G≈5 that blocks the consensus comparison.
- **State your expected ceiling before seeing any result** (Priority 1 Q4). Much of fantasy variance
  is injury and touchdown luck and is forecastable by nobody.
- **Survivorship, handled explicitly.** A projection right about points-per-game and wrong about games
  played is wrong for fantasy. State how you handle missed time, players who never played, and rookies
  with no history. Evaluating only on full seasons is the easiest way to manufacture a result that
  will not replicate.
- **Do not unseal the holdout.** If the prototype would benefit from seeing it, that is precisely why
  you cannot. Use walk-forward on the non-holdout years.
- **Two-stage, per Q2:** project opportunity, then convert with regressed efficiency, regression
  strength **estimated not assumed**. Touchdown rate regressed hardest.

### What to report

In the landing note, in full — not as a pointer:

- **Per-season results against every baseline**, with intervals. Including the seasons where it lost.
- **The variant count and honest multiplicity denominator.**
- **Whether it beats last-season-rank.** One line. This is the question.
- **What is doing the work** — which features carry the signal, and whether that matches the
  mechanisms you ranked in Q1. If a feature you predicted would matter does not, say so; a failed
  prediction registered in advance is worth more than a good score.
- **The single most promising direction you did not have time to try.**

**A validated mediocre model with honest numbers is worth more than an impressive one whose
provenance nobody can reconstruct.** If the honest finding is "bottom-up does not beat
last-season-rank on this data," that is a genuinely valuable result and it should be reported as
plainly as a success would be.
