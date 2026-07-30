# Fable mandate M — the three model questions
2026-07-29

Lettered **M** to avoid colliding with the existing F, G, K and H series.

**Rules as before.** Conclusion first. Read the repo freely; run read-only queries and existing tests.
**Modify nothing** except your own output documents and a session log entry. One mandate per session.

**Read `docs/CORRECTIONS-2026-07-28.md` first** — it carries corrections that falsify premises in
earlier Fable output.

---

## The framing, and the PM got it wrong first — read this carefully

The PM initially framed these as off-season design questions and split every answer into
"before 7 September" versus "the real answer." **The founder rejected that framing outright:**

> "NO, they are this season questions, we will finish all these items quickly, I am working much
> faster than Fable, just stop worrying about time honestly."
>
> **"If I don't have those three things in place, I don't want to use the tool for my real draft."**

So the bar is not "what would be nice by September." The bar is: **these three are the conditions
under which the founder will trust this tool in a live draft on 7 September.** If they are not good
enough, he uses something else, and the project has no purpose this season.

**Design for that. Not for the ideal off-season version, and not for a hedged minimum.**

Two things follow:

- **Do not pace your recommendations to a deadline.** Build capacity is not the constraint the PM
  assumed it was. Scope by what is *right*, and note where something genuinely cannot be known in
  time — which is different from being merely hard.
- **Say plainly if a claim cannot be earned by 7 September.** The founder has asked repeatedly to be
  told when he is wrong. A calibration curve with ten drafts behind it is not the same as one with
  a hundred, and if that gap is unbridgeable, the honest answer is what the app should *say* rather
  than what it should compute.

The six standing priorities — the app not lying, mode switching, injuries and roster status, mock
drafts and their recording, on-the-clock usability, the daily capture — remain the correctness floor
and are not in tension with this. **The floor is necessary; these three are why the thing exists.**

---

## What is already established — do not re-derive

- The shipped board is **consensus-derived at player level**. Its only edge channel is positional
  revaluation.
- The shipped recommendation card and survival number are **λ-free**, running on five hard-coded
  constants (+8 / +18 / −25 and −0.62 / −1.25) never fitted to anything. λ = 0.352 steers only sim
  comparisons and an unwired path. **Whether to wire it in or drop the claim is mandate K-A, unrun.**
- λ's interval is roughly [0.21, 0.49] from one draft, one league, need confounded with round. Pairs
  bootstrap and leave-one-cluster-out jackknife both reproduce it — **the uncertainty is population,
  not sample.**
- Bottom-up beats last-season-rank at RB (+0.041) and WR (+0.043), loses QB (closed after six failed
  configurations), TE unrun. **No confidence interval has ever been computed on those wins.**
- **Availability is calibrated on 0 of ~30 drafts.** No evidence exists that a stated 30% happens 30%
  of the time.
- Vacated opportunity and rookie draft capital are **cleanly eliminated** as consensus-gap channels.
- **Four of five registered prediction sets were materially wrong, all over-crediting situation
  stories.** Apply this to yourself.

## New constraints the founder established, 2026-07-29

- **Westwood: Yahoo, 10 teams, custom half-PPR with stacking yardage bonuses.** Roster: QB, WR×3,
  RB×2, TE, two W/R/T flex, DEF, six bench, IR. **No kicker.** Playoffs weeks 16–17. Drafts Mon 7 Sep.
- **Two flex slots are new as of last season.** There is **no usable Westwood draft history** — the
  founder does not have past results, and one season under the current shape would be uninformative
  anyway.
- Mock drafts will come from **Yahoo rooms with standard scoring and standard roster shape**, joined
  by the founder and autodrafted. Real human opponents; mismatched scoring and roster shape.
- Kickers: **consensus-only list, excluded from the combined board.** The model need not represent them.

---

# M-1 — How do we build the best bottom-up rankings possible?
`docs/reviews/fable-M1-bottom-up-design-2026-07-29.md`

**Before answering, note that your own F-A run recommended timeboxing this and deprioritising it in
favour of the availability model regardless of outcome. If you still believe that, say so first and
answer the question anyway.**

1. What is the ceiling? Given walk-forward validation, no pooling, and an effective sample of seasons
   rather than players, **what is the best a bottom-up model could plausibly achieve** against
   consensus — not against last-season rank? Put a number on it or explain why you cannot.
2. Where does the remaining signal actually live? Prior work says 2009+ usage tier, not model
   capacity. Is that still your read?
3. **What data do we not have that we would need?** Be specific and say when collection would have to
   start. This is the most actionable section — some of it may need to start now even if the modelling
   waits.
4. What is the smallest honest claim, and what evidence would license it?
5. **What has to be true for the founder to trust these rankings on 7 September?** Name the evidence,
   not the effort. If the honest answer is that bottom-up rankings cannot be trusted this season and
   the board should ship consensus-derived with an explicit disagreement flag, **say that** — it is a
   legitimate answer and the founder would rather hear it than discover it in the draft.

# M-2 — How do we build the best availability prediction model possible?
`docs/reviews/fable-M2-availability-design-2026-07-29.md`

This is the product's actual differentiator and the category ships nothing like it. It has also never
been adversarially reviewed — see the unrun G-C mandate, and fold it into this one rather than
duplicating.

1. **What does the current hazard formulation assume, and which assumptions are false in a real
   draft?** Independence between picks, stationarity across rounds, exchangeability of drafters, no
   reaction to what just happened. Name which are violated and how badly.
2. **Calibration is the whole claim and there is none.** Design the calibration procedure: what gets
   recorded, what the reliability curve looks like, how many drafts before it means anything, and what
   we say on screen before then.
3. **The mock-draft mismatch is the interesting problem.** Yahoo rooms are standard scoring, standard
   roster shape. Westwood is three receivers plus two flex and no kicker, so demand for receivers and
   flex-eligible backs is structurally higher and every drafter in the room responds to it.
   - Which part of what a mock teaches is **behavioural** (how drafters act relative to the rankings
     they read) and therefore transfers?
   - Which part is **structural** (how much demand exists per position) and must come from config?
   - **Does the current model actually separate those two?** Check the code. Hardcoded `TARGET`,
     `SHARE_BAR` and `POSITIONS` suggest structural assumptions are frozen rather than configured.
   - With **no league history**, the structural correction cannot be measured. Is there an honest way
     to derive it, or should it be declared unvalidated and surfaced as uncertainty?
4. Behaviour in the tails — the first five picks and the last rounds, where the sample thins.
5. Off-script drafts: reaches, runs, autopicks, a paused clock. Degrade gracefully or mislead
   confidently?
6. **What makes the survival numbers trustworthy enough to act on by 7 September**, given ten to
   twelve autodrafted mocks and no league history? Be concrete about how much calibration data buys
   how much confidence. If the honest answer is that the numbers will be indicative rather than
   calibrated, **say so and specify exactly what the app should display** — a well-labelled indicative
   number is usable; a false precise one is not.
7. **More mocks are available than the PM assumed.** The founder can join Yahoo rooms and autodraft,
   costing minutes rather than an evening each. **How many would actually be enough, and does the
   answer change if they are cheap?** The earlier target of ten to twelve was set against a cost
   assumption that no longer holds.

# M-3 — How do we build the best suggested-pick model possible?
`docs/reviews/fable-M3-recommendation-design-2026-07-29.md`

The hardest of the three and the one closest to what the founder actually experiences. It must account
for his roster construction, opponents' roster construction, and availability — **dynamically, during
the draft.**

1. **Start from the decision, not the model.** What is the quantity being maximised at a pick? Expected
   season points is the obvious answer and probably the wrong one, since leagues are won by
   championship probability, not by total points. Is the difference material at draft time, or does it
   compress to nothing before the season starts?
2. **Opportunity cost as the organising principle.** Competitive research found FantasyPros surfaces
   its headline recommendation as a *vote share among expert rankings* that, by their own
   documentation, ignores roster needs entirely — and buries the roster-aware signal as a secondary
   badge that can contradict it. Value-over-next-available exists in their product but as an optional
   column. **Is "what does taking him cost you" the right primary surface, and what exactly does it
   compute?**
3. **Opponents' roster construction.** How much does modelling what other teams still need actually
   improve the recommendation, versus modelling only the pick sequence? Quantify if you can. This is
   the most expensive input and it may not earn its cost.
4. **The dynamic requirement.** Every pick changes the state. What must recompute, what can be cached,
   and what is the honest latency budget when the founder is on the clock?
5. **The λ question, and do not answer it here.** Mandate K-A owns whether the measured need term or
   the five unfitted constants should drive the recommendation. Say what M-3's design implies for that
   decision, but do not settle it — the PM authored the claim under review and is not permitted to
   frame it.
6. **What does the founder see?** A number with no explanation is what the competition ships and what
   users complain about. Specify the display: the recommendation, its uncertainty, the alternatives,
   and the reason — in a form readable in the seconds available on the clock.
7. **What does the founder need to see on 7 September to act on a recommendation under a clock?**
   Not the minimum viable change — the thing that would make him trust it. And say what would make it
   *worse* than what ships today, since the current surface at least behaves consistently.

---

# The cross-cutting question — answer it in whichever document you write first

**These three are the founder's conditions for using the tool at all. Which is furthest from being
met, and what is the shortest honest path to meeting it?**

Then the harder one: **is there a version of "these three in place" that is achievable and honest, or
does one of them require evidence that cannot exist by 7 September?** If the latter, name which, say
what the app should claim instead, and say whether a well-labelled indicative version clears the
founder's bar or falls short of it.

He has asked repeatedly to be told when he is wrong. This is the question where enthusiasm beats
evidence unless someone names it — including his enthusiasm, and including the PM's.

---

## M4 — Consistency. Added 2026-07-30 at the founder's direction.

His words, after catching the recommender suggesting a player it had just explained was *more*
likely to still be available later:

> "just odd recommendation model is suggestiong things that don't agree with other findings, we need
> consistency, again, this is what fable will need to tear into"

**This section is not about the inverted pick logic.** That defect is already traced (ranker) and a
correct rule is being specified (strategist) — see
`docs/founder-requests/FR-2026-07-30-recommendation-logic-is-inverted-it-prefers-the.md`. Do not
re-derive it and do not spend the mandate on it.

**It is about the class.** The product contradicted itself on one screen, in its own voice: the
assistant told the founder that reaching for a quarterback in the first three rounds was the single
most costly strategy this project has tested — negative in all 12 scenarios, worst case −115.4
points — while the recommender was recommending exactly that. Two surfaces, same product, opposite
answers, and nothing anywhere noticed.

### The hypothesis to attack

**Findings live in markdown; the model lives in code; nothing connects them.** Measured results are
written into `docs/`, ADRs and thread replies, and then the model is free to contradict every one of
them, because no test asserts that a finding is respected.

Attack that framing as well as the tool. It is PM's hypothesis, it is convenient, and a convenient
structural explanation is exactly the kind of thing this mandate exists to disbelieve. Possibilities
worth taking seriously: the findings may be narrower than their summaries; two findings may
genuinely conflict and the recommender picked one; or the "contradiction" may be an artifact of the
assistant paraphrasing a result it retrieved rather than a real inconsistency.

### Specific things to check

1. **Read the early-QB result at source**, not via the assistant's summary. How many scenarios, what
   league shape, what pick range, what confidence? Establish whether pick 18 is genuinely inside its
   support or whether the assistant overreached.
2. **Enumerate what the recommender actually encodes** versus what this project has measured. The
   four candidates on file: early-QB cost; the dead variance-preference (CLAUDE.md §7, tested four
   ways); archetype fall-through frequency; and H1 NULL on ADP accuracy, measured 2026-07-30.
3. **Ask whether "consistency" is even the right goal.** A model forced to obey every prior finding
   cannot learn that one was wrong. What is the honest version — a hard constraint, a flagged
   warning, or a test that fails only when a *live* recommendation contradicts a *holdout-validated*
   result? The founder asked for consistency; the right answer may be narrower than his word.
4. **The three defects in the same screenshot** — the garbled self-correcting sentence shipped to
   production, and two different availability numbers for the same player on one screen. Are these
   the same root cause as the inconsistency, or three unrelated failures that happened to co-occur?

### The bar

This is question 3 of his three model questions, observed failing in the surface he would use on
7 September. Treat it accordingly.
