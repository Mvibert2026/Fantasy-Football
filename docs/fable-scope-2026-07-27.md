# Fable — red-team brief (2026-07-27)

**SUPERSEDED BY `docs/fable-mandate-4-final-2026-07-27.md`.** Superseded twice over by later mandates.
Kept for historical record only.

You are an outside consultant hired to **refute**, not confirm. Assume every document in this repo is
advocacy written by the people being evaluated — including `CURRENT-STATE.md`, `operating-model.md`,
and the PM's reasoning inside the handoff threads. Cite file and line. Where the evidence is absent,
write "unresolved" rather than filling the gap.

**The founder's actual goal**, which is the yardstick for everything below: *be measurably better at
fantasy football across the whole season — draft prep, the live draft, and in-season management —
on the strength of his own rankings.* Improving on consensus is one route. **Beating it outright is
the better one.** Judge the project against that, not against its own roadmap.

---

## Order of work — this matters

Answer in the order given. **Design fit first, niche validity second.** A perfect answer to a
parameter question is worthless if the system is aimed at the wrong target, and finding that out on
question nine wastes the review.

Do a **breadth-first pass across all of Part A before going deep on anything.** A hedged verdict on
every Part A question beats an exhaustive verdict on one. Then Part B in order, then Part C with
whatever remains. If you are running short, stop and deliver, naming what you did not reach. A partial
review that says so is finished. A truncated deep dive is not.

**Output:** one file, `docs/reviews/fable-2026-07-27.md`. Do not write to `src/`, `frontend/`, or
`docs/CURRENT-STATE.md`. Do not write code, refactor, or open threads — findings only; the PM converts
findings into work.

**Two things required at the top of your output:**

1. One sentence naming the most damaging *true* thing you found. If the project survives the attack,
   say so plainly — a red team that always finds something is not a red team.
2. **A founder-decision list.** Anything you find that only the founder can settle, written in plain
   language with the trade-off stated and your recommendation. Do not route these through the PM's
   framing; the PM may be the reason they are unresolved.

---

# PART A — is the system designed for the right problem?

## A1 · Does the model design fit the goal?

The core machinery is a hazard model over a pick sequence: each remaining player gets a weight, the
probability a player goes next is that weight over the sum, and a need term
`N_t(p) = (share_t(p)/share_bar(p))^lambda` adjusts for what each manager already holds.

That is a **draft-time availability engine**. The founder's goal is broader. Ask the uncomfortable
question: **is availability the right central abstraction, or is it the thing that happened to get
built first?**

Specifically:

- What decisions does the engine actually support, and what fraction of the founder's season do they
  cover? Draft prep is arguably served as a side effect of rankings; in-season is not obviously served
  at all.
- Are the in-season decisions — waiver priority, start/sit, trade valuation, playoff-odds-aware risk —
  expressible in this engine, or do they need a different core? They are not "who survives to my next
  pick." Answering this now is cheap; answering it after in-season work is bolted onto the draft engine
  is not.
- Is the **data layer** general enough to serve both, or is it shaped around draft-time snapshots?
- If you were designing this from scratch against the founder's stated goal, **what would the central
  abstraction be?** Say so even if the answer is "the same one." Especially then.

**Verdict:** the design fits / it fits with named modifications / the centre of gravity is wrong.

## A2 · Is the communication and automation architecture good — and can you do better?

The system: one human talks only to the PM. The PM writes numbered thread files into
`docs/handoffs/`, each with `FROM`/`TO`/`STATUS`, a "done looks like", and a file boundary. Specialist
agents read the mailbox, work, commit, reply in-thread, mark resolved. `tools/handoffs.py` regenerates
the index and fails on duplicate IDs, unaddressed threads, resolved-without-reply, and staleness.
Model and effort are pinned per agent in `.claude/agents/*.md`. The strategist is denied `Bash` so it
cannot query the database.

Evaluate it honestly, and **propose something better if you have it.** This is not a rhetorical
invitation — the founder wants the best answer, not validation of the current one.

- **Does the repo-as-message-bus actually work, or does it look like it works?** Evidence: threads
  reopened after resolution, work redone because two agents disagreed, contradictions between threads
  issued in the same round, findings recorded in one doc and contradicted in another, documentation
  churn with no matching code change. **Estimate the rework rate.**
- **Is the PM adding value or adding ceremony?** The PM writes the threads, sequences the rounds, and
  also authors the documents claiming the system works. Those documents are advocacy. Judge them as
  such. Would fewer, larger threads produce the same result at lower cost?
- **Are the mechanical constraints real?** The strategist's missing `Bash` is the strongest one. Are
  there others that are stated as rules but not enforced — and could they be made mechanical? Which
  currently-stated rule is most likely being quietly violated?
- **Is the model/effort assignment right?** Backend runs sonnet/low at the highest volume; frontend
  runs sonnet/high; strategist and researcher run opus/high. Is anything mis-tiered in either
  direction — paying opus rates for mechanical work, or running low effort on judgement work?
- **What is the automation gap?** What does the founder still do by hand that a script or a hook could
  do? Standing request FR-002 says his involvement should fall over time. Is it falling?
- **What breaks at scale?** Nine agents ran in one round. What fails at twenty? Shared documents have
  already been identified as the contention point rather than source files — is that the real limit or
  a symptom?

**Verdict:** the architecture is sound / sound with named fixes / here is a materially better design.

## A3 · Are the rankings actually bottom-up, or consensus wearing a costume?

The ambition is a proprietary ranking built from first principles — opportunity, usage, efficiency —
comparable *against* the market rather than derived from it. Test whether that is what exists.

The failure mode to hunt is **circularity**: consensus or ADP leaking into an input presented as
independent. Candidate paths, non-exhaustive — find the ones nobody has listed:

- Consensus rank used as a feature, a prior, a tiebreak, a sort order, or a fallback when a projection
  is missing.
- **Player universe selection driven by ADP.** If the candidate pool is "inside consensus top 200,"
  the ranking is conditioned on consensus even when the scoring is not.
- Replacement-level or positional-scarcity baselines derived from where players *go* rather than what
  they *produce*.
- Hand-tuned constants chosen because the output "looked right" against a ranking the tuner had seen.
  Hardest to detect, most likely to be present. Find the magic numbers and check what they were in
  earlier commits.

**Why this outranks the statistics:** a consensus-anchored model has errors *correlated with consensus
errors*, so it cannot identify where the market is systematically wrong — which is the only place edge
comes from. It can be more accurate than consensus and still useless for beating it.

**Verdict:** genuinely bottom-up / anchored at these points / cannot determine from the repo.

## A4 · Is "beating consensus is unclaimable until ~2029" true, or PM over-conservatism?

This is the PM's own standing claim and it is shaping the roadmap. If it is wrong it costs three
years. Attack it directly.

The argument on record: consensus history exists only from 2021, so n≈4–5 seasons, and a season-level
sign test has a p-floor of 0.0625 — it cannot reach significance however good the model is.

What that argument may be getting wrong:

- **The resampling unit may not be the season.** Paired error comparison at the *player-season* level
  is ~1500 paired observations. The binding constraint is within-season correlation, i.e. clustered
  inference at G≈5. Wild cluster bootstrap at G=5 is unreliable — but unreliable is a materially
  different claim from impossible.
- **Effect size is being ignored.** Beating consensus in 5 of 5 seasons by a wide margin is
  decision-relevant even when it is not publication-significant. This project is not publishing; it is
  deciding whether to trust a draft board.
- **Subsetting does not buy independence.** Do not accept "5 seasons × 6 positions = 30." Check
  whether anything already in the repo makes that error.
- Conversely — is there a defensible bar *below* significance the project should be reporting instead
  of staying silent? Silence about a real edge is also a failure.

**Verdict:** the 2029 claim is correct / over-conservative, and here is the test runnable now /
under-conservative, and even the accuracy claim is weaker than stated.

## A5 · Is the code structure sound?

Structural, not stylistic.

- **Coupling and boundaries.** Where does the dependency graph go wrong? Is there a module everything
  imports that should not exist?
- **Is the data contract load-bearing or ceremonial?** It has been bumped repeatedly. Does anything
  actually fail when a consumer reads an unexpected version, or is the version a comment?
- **Single source of truth for player identity?** Thread 052 shipped exports that could not join to
  players. Symptom or structure — is there more than one crosswalk, or one that is not authoritative?
- **What breaks on a fifth league or an unanticipated scoring format?** Settings was hardcoded to one
  league until recently.
- **Is the test suite load-bearing or decorative?** 487 passing is a number, not evidence. Sample them.
  What fraction assert real behaviour versus assert a function returns something? Would the suite catch
  the `percent()` sub-0.5% defect *class* today, or only that instance?

**Verdict:** sound / sound with named weak points / carries a structural problem that compounds.

---

# PART B — validity of what has been measured

## B1 · Is `lambda = 0.352` supportable, or noise dressed as a measurement?

Reported as n=160 across 10 clusters, SE 0.070 — an interval excluding zero, which is the entire basis
for claiming need moves picks. What is the effective sample size once clustering is handled honestly?
Are those 160 independent in any meaningful sense, or 10 drafts of within-draft correlation counted as
160? Was the functional form chosen before or after seeing the data — and can you tell from the repo?
If post hoc, the SE is understated.

## B2 · How much overfitting exposure has accumulated against the 26 seasons?

Pre-registration (ADR-C, thread 020) is recent. Everything before it was not pre-registered. Estimate
the forking-paths exposure: how many variants, features, functional forms and hyperparameters were
tried against the same history with no multiplicity denominator? Then the harder question — **does the
pre-registration machinery actually bind?** A holdout requiring a signed unseal is a guardrail only if
the seal cannot be worked around. Check whether it can.

## B3 · Does the accuracy-versus-consensus separation hold in the code?

Find where it leaks: a backtest with consensus-derived inputs reporting accuracy, a metric quietly
benchmarked against ADP, a string implying market-beating. Thread 021's cross-position rank
correlation is known — find the ones nobody has.

## B4 · Do the five null states survive database to screen?

`—` / `<1%` / `0%` / `not yet` / `·` are five distinct claims; one collapse was already found in
`percent()`. Trace two fields end to end — ingestion, export, contract, component. A null honest in the
database and lossy in the export is the same defect somewhere less visible.

## B5 · Is the new FFC ADP data going to be used correctly?

Thread 055 harvests Fantasy Football Calculator ADP back to 2007. It is **mock-draft data from
self-selected users** — a biased sample of a related population, not ground truth for the founder's
league. The thread says so. Check that nothing downstream is positioned to silently treat it as the
reference standard simply because it is the only long history available.

---

# PART C — efficiency and the unasked question

## C1 · Where is the real bottleneck?

Not micro-optimisation. Is anything in the live-draft recompute path going to fail under a real draft
clock? Is "no part-applied recomputes" enforced or merely stated?

## C2 · What is missing that nobody has asked about?

Not on any list, not in `decisions-needed.md`. The question the project has not thought to ask itself.
Given the founder's goal spans the whole season, look hardest at the parts of that season nobody has
written a thread about.
