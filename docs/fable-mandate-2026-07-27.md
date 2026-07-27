# Fable — session mandate, 2026-07-27

**SUPERSEDED BY `docs/fable-mandate-4-final-2026-07-27.md`.** Kept as the historical record of what
session 1 was actually asked — do not work from this document.

**Supersedes every prior Fable brief.** Earlier mandates covering rankings, statistical validity and
product design are **withdrawn**. Work this document only.

You have a real budget and it expires. **Spend it.** Working to the end of the capacity on the
priorities below is the correct behaviour; stopping early to be economical is not. But finish what
you start — a completed Priority 1 beats a partial 1 plus a partial 2.

---

# PRIORITY 1 — bulletproof the parallel workflow (do this first, and completely)

## The question

**How do we run many agents in parallel on this repository, faster than we do now, without them
destroying each other's work or corrupting the coordination system they depend on?**

## The standard you are judged against

> "These systems are supposed to be enablers, not bottlenecks and take effort away from product work."
> "We want to work faster without breaking things." — the founder

**You are increasing throughput, not adding controls.** A proposal that is safer and slower has
failed. Every recommendation must carry: the specific failure it prevents (cited from the evidence
below, not hypothetical), its honest cost, and why nothing cheaper would do. Prefer a behaviour change
to a mechanism, a convention to a tool, and a structural impossibility to a check.

**Recommend deletions.** A review that returns only additions has not understood the assignment.

## Evidence — failures that actually happened here

1. **Two ID allocators, one namespace.** The PM writes threads over a device bridge; agents write
   directly. Both pick the next ID from what they can see. A collision occurred at `053`, caught by
   luck.
2. **Silent overwrite risk.** A forced bridge write to a colliding ID destroys an agent's thread with
   no duplicate-ID error — the file simply stops existing.
3. **Contradictory instructions in one round.** Thread 049 asked to remove randomised suggester
   ordering while RETROFIT-5 asked to add it. Caught by an orchestrator escalating rather than
   resolving — correct, and luck.
4. **"Resolved" means an agent said so.** Thread 051 closed against behaviour that still failed. The
   founder found it broken and reported it twice. No acceptance step exists between self-report and
   green status.
5. **The PM reported cached files as current.** Staged copies of `OPEN.md` and `CURRENT-STATE.md`
   returned day-old content with fresh timestamps. The PM asserted a sync bug and a stale state file
   that did not exist and wrote two threads on that basis. The founder caught it. **The project's
   narrator was wrong about the repository.**
6. **Two views of the same data.** The application once silently read a shadow export directory —
   committed, eighteen hours stale, one league config instead of twenty-five. No error raised.
7. **Shared documents are the contention point, not source files.** Nine agents ran; `src/`
   boundaries held perfectly, two nearly collided on `CURRENT-STATE.md`.
8. **Scope inflation on coordination work.** A state-file verification consumed 100k tokens because
   the PM specified "verify every line against the working tree."
9. **Duplicate threads.** The mailbox went 42 → 64 in a day with at least eight overlapping pairs,
   most created by the PM in one session.
10. **A scope correction raced a completing task.** A narrowed instruction reached an agent as it
    finished; it delivered the original scope and reported success without disclosing the race. Not
    disobedience — but **in-flight scope changes have no defined semantics**, and that matters when
    many agents run at once.

## The system as it stands

- **Repo-as-message-bus.** `docs/handoffs/` holds numbered threads with `FROM`/`TO`/`STATUS`, a "done
  looks like", and a stated **file boundary**. `tools/handoffs.py` regenerates an index and fails on
  duplicate IDs, unaddressed threads, resolved-without-reply, and staleness.
- **Parallelism by file boundary**, assigned by the PM, enforced by instruction rather than mechanism.
- **Pinned model/effort** per agent in `.claude/agents/*.md`. The strategist is denied `Bash`, so it
  structurally cannot query the database — the model for what a real constraint looks like.
- **One-thread-at-a-time closeout.** Batching failed twice.
- **No git remote. One disk. No worktree or branch isolation** — every agent works in the same
  checkout concurrently.

Correct this description if any of it is wrong; that would itself be a finding.

## What to answer

**A · Where does it break, and at what N?** Nine agents have run. What is the binding constraint at
twenty — shared documents, the ID namespace, the single checkout, PM sequencing capacity, or something
unlisted? Name the ceiling and the cheapest thing that raises it.

**B · What should be structurally impossible rather than detected?** The strategist's missing `Bash`
is the model. Two candidates to evaluate — and reject if the cost is wrong:

- **Single ID allocator.** Nobody picks a number; threads are written by slug and the tooling assigns
  the next free ID atomically at sync. Kills 1 and 2.
- **Worktree or branch isolation per agent.** Concurrent writes cannot destroy each other, and
  boundary violations surface as merge conflicts rather than silent loss. Kills 2 and 7, and might
  make PM file-boundary assignment unnecessary — *removing* PM work rather than adding process.

**C · Is a directory of markdown files the right substrate?** The hard requirement is that no human
relays messages between agents. Given that, is there something better?

**D · What replaces "an agent said it was done"?** Failure 4 reaches the founder directly. What is the
cheapest acceptance signal that would have caught 051, and does it generalise beyond UI work?

**E · Is the PM a bottleneck, a single point of failure, or both?** It allocates IDs, writes threads,
sequences rounds, decides what counts as verified, and authors the documents claiming the system
works — and has been demonstrably wrong about the repository. **Treat its documents as advocacy.**
Would fewer, larger threads do? Should agents open more of their own work? What of the PM's job should
be mechanical?

**F · In-flight scope changes.** Failure 10. What are the semantics when an instruction changes
mid-task? Cheapest workable answer.

**G · Recovery.** No remote, one disk, agents running destructive git commands. Parallelism multiplies
blast radius. Minimum that makes a bad round recoverable, and is it cheaper than the loss?

**H · What currently costs throughput for no safety benefit?** Controls that exist because someone
worried, not because something failed.

## Deliverable

`docs/reviews/fable-workflow-2026-07-27.md`

- **One sentence at the top:** the highest-leverage change and what it buys.
- **A ranked table:** change · failure prevented (by number) · cost · throughput effect · type
  (mechanism / convention / deletion).
- **Explicitly accepted risks** — what you judged not worth preventing, and why.
- **Work orders** precise enough for a sonnet-tier agent to execute without further judgement. Do not
  implement anything yourself.
- **A stated ceiling:** how many agents this supports after your changes, and what breaks next.

---

# PRIORITY 2 — only after 1 is complete and delivered

Take these in order. **Do not start one you cannot finish.** Each is a separate file under
`docs/reviews/`.

## 2A · Table-stakes inventory

Standing founder instruction **FR-007**: *"I don't care if it's table stakes, not edge. By definition,
we need all the table stakes covered."*

Produce the exhaustive list of things any credible fantasy ranking must get right, each marked
verified / not-verified / unknown, with a work order for each unverified item. Verification means an
**executable check**, not an assurance that someone looked.

Seed list, deliberately incomplete — **produce the real one:** bye weeks current; known suspensions
deducted with appeal status; injured and season-ending players reflected; retired, holdout and
non-rostered players removed or flagged; offseason team changes and depth charts correct; position
eligibility including position changes; rookies present without silent dependence on prior-season
stats; **name collisions and suffix handling** (the classic silent-corruption bug — thread 052's
join-key failure was the same family); team abbreviation changes across 26 seasons; scoring settings
actually matching the league; IR and practice-squad designations.

**Rationale to keep in view:** edge is worthless if the floor leaks. A ranking with a real 5% edge and
one catastrophic omission is *worse* than consensus, because the founder cannot tell which rows are
affected and therefore cannot trust any of them.

## 2B · Is the ranking secretly consensus-anchored?

The stated ambition is a bottom-up ranking comparable *against* the market rather than derived from
it. Test whether that is what exists. Hunt circularity: consensus or ADP as a feature, prior,
tiebreak, sort order or missing-value fallback; **player-universe selection driven by ADP** (most
likely leak, least likely noticed); replacement level derived from where players go rather than what
they produce; hand-tuned constants chosen because output "looked right".

A consensus-anchored model has errors correlated with consensus errors, so it cannot find where the
market is wrong — the only place edge exists. It can be more accurate than consensus and still useless
for beating it.

## 2C · Is "beating consensus is unclaimable until ~2029" correct?

The PM's standing claim, shaping the roadmap. On record: consensus history exists only from 2021, so
n≈4–5 seasons and a season-level sign test has a p-floor of 0.0625.

What that may get wrong: the resampling unit may not be the season — paired error comparison at
player-season level is ~1500 observations, with within-season correlation meaning clustering at G≈5;
wild cluster bootstrap at G=5 is unreliable, which is **materially different from impossible**. Effect
size is being ignored — beating consensus 5 of 5 by a wide margin is decision-relevant even when not
significant, and this project is not publishing. Subsetting buys no independence; reject "5 seasons ×
6 positions = 30" and check whether the repo already makes that error.

## 2D · Overfitting exposure

Pre-registration (ADR-C, thread 020) is recent; everything before it was not pre-registered. Estimate
the forking-paths exposure against the 26 seasons. Then the harder question: **does the
pre-registration machinery actually bind?** A holdout requiring a signed unseal is a guardrail only if
the seal cannot be worked around. Check whether it can.

---

# Rules for the whole session

- **Do not unseal the holdout.** If your work would benefit from seeing it, that is precisely why you
  cannot.
- **Do not write production code.** Findings and work orders only.
- **Do not modify** `src/`, `frontend/`, `docs/CURRENT-STATE.md`, or any file under `docs/handoffs/`.
  Threads are the PM's and agents are mid-flight.
- **Cite file and line.** Where evidence is absent, write "unresolved" rather than filling the gap.
- **You are hired to refute, not confirm.** Every document in this repo is advocacy written by the
  people being evaluated, the PM's most of all. If the honest finding is that something survives your
  attack, say so plainly — a red team that always finds something is not a red team.

---

# REPORTING PROTOCOL — read before starting work

**Assume you may be cut off at any moment.** The budget is finite and expires tonight. A brilliant
analysis held in your context when capacity runs out is worth nothing. Everything below exists to
make sure the founder gets whatever you managed, not only what you finished.

## The landing note

**`docs/reviews/FABLE-2026-07-27.md` is the single place the founder and the PM look.** Nothing else
needs to be found.

**Create it before you do any analysis.** Its first version should contain only the plan and
`STATUS: STARTED`. Then keep it current.

Required structure, maintained throughout:

```
# Fable session — 2026-07-27

STATUS: STARTED | IN PROGRESS | COMPLETE | STOPPED — <where and why>
LAST UPDATED: <time or milestone>

## What I have done
<one line per completed item, each naming the file it was written to>

## What I was doing when this was last updated
<the in-flight item, and how far into it>

## What I did not reach
<remaining items, in the order I would have taken them>

## Headline findings
<the two or three things that matter most, stated in full here —
 not a pointer to another file. If the founder reads only this
 section, he should get the value.>

## Next steps for the project
<ranked, concrete, each one actionable without further analysis
 from you. Say who should do it and roughly what it costs.>

## What I would do with more budget
<the single most promising thing you did not have time for>
```

## Write incrementally — this is the rule that matters most

- **Update the landing note after every milestone**, not at the end. Milestone means: a section of
  Priority 1 answered, or a Priority 2 item completed.
- **Write each finding to its file as soon as it is complete.** Never accumulate output intending to
  write it all later.
- **Headline findings go in the landing note in full**, duplicated from wherever else they live. The
  founder should never have to open a second file to learn the important thing.
- If you are partway through an item and sense you are running short, **stop and write** rather than
  pushing for completeness. A recorded partial finding beats an unrecorded complete one.

## Where you may and may not write

- **Write:** `docs/reviews/` only.
- **Do not write:** `src/`, `frontend/`, `docs/CURRENT-STATE.md`, or anything under `docs/handoffs/`.
  Agents are mid-flight and the mailbox belongs to the PM. **Your landing note is your handoff** — the
  PM will convert your work orders into threads. Do not create threads yourself, and do not reply in
  existing ones.

## Be honest about how far you got

`STOPPED — halfway through question E, no conclusion reached` is a good outcome, recorded. Silence, or
a landing note that implies more completeness than exists, is the one failure that would make this
session worse than not running it. The project's whole discipline is refusing to overstate; that
applies to your own progress report.
