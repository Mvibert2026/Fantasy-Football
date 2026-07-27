# Fable — rankings integrity mandate (2026-07-27, session 2)

**SUPERSEDED BY `docs/fable-mandate-4-final-2026-07-27.md`.** Never ran — its questions were already
covered by session 1. Do not run this; do not spend budget re-answering it.

**A parallel session is running the workflow mandate
(`docs/fable-mandate-2026-07-27.md`). That is not your work. Do not read it, do not comment on it,
do not touch anything it touches.**

**Your file boundary:** write only to `docs/reviews/`, and only to files named
`fable-rankings-*.md`. Do not modify `src/`, `frontend/`, `docs/CURRENT-STATE.md`, or anything under
`docs/handoffs/`. Do not create or reply to threads. Do not unseal the holdout — if your work would
benefit from seeing it, that is precisely why you cannot.

---

## The question

**Are this project's ranking and validation claims actually what it says they are?**

Three sub-questions. They are one investigation: each asks whether a stated claim survives contact
with the code.

You are hired to **refute, not confirm**. Every document in this repo is advocacy written by the
people being evaluated — the PM's most of all. Cite file and line. Where evidence is absent, write
"unresolved" rather than filling the gap. If a claim survives your attack, say so plainly; a red team
that always finds something is not a red team.

---

## Q1 · Is the ranking secretly consensus-anchored? **(start here — it gates the other two)**

The stated ambition is a bottom-up ranking built from opportunity, usage and efficiency, comparable
*against* the market rather than derived from it. **Test whether that is what exists.**

Hunt **circularity** — consensus or ADP leaking into an input presented as independent:

- Consensus rank as a feature, a prior, a tiebreak, a sort order, or a missing-value fallback.
- **Player-universe selection driven by ADP.** If the candidate pool is "inside consensus top 200,"
  the ranking is conditioned on consensus even when the scoring is not. Most likely leak, least
  likely to be noticed.
- Replacement level or positional scarcity derived from where players *go* rather than what they
  *produce*. Note the recorded replacement levels are RB30 / WR40 / TE10 / QB10 — establish how those
  were actually derived.
- Hand-tuned constants chosen because output "looked right" against a ranking the tuner had seen.
  Hardest to detect, most likely present. Find the magic numbers and check what they were in earlier
  commits.

**Why this gates everything:** a consensus-anchored model has errors *correlated with consensus
errors*, so it structurally cannot identify where the market is wrong — the only place edge exists. It
can be more accurate than consensus and still useless for beating it. If the answer here is
"anchored," Q2 and Q3 are about the wrong object and you should say so rather than completing them.

**Verdict:** genuinely bottom-up / anchored at these points / cannot determine from the repo.

## Q2 · The 2028-vs-2029 question, now formally CONTESTED

`docs/CURRENT-STATE.md` marks this **CONTESTED** rather than resolved — correctly, because two
documents disagree and nobody established which is right. Resolve it.

The claim on record: consensus history exists only from 2021, so n≈4–5 seasons, and a season-level
sign test has a p-floor of 0.0625 — beating consensus cannot reach significance regardless of model
quality. An older statement (ADR-026) says the season-level bootstrap floor sits above the
Benjamini-Hochberg threshold, closing alpha detection until ~2028.

**Establish whether these are the same argument with different arithmetic, or two different
arguments that have been conflated.** That distinction matters more than the date.

Then attack the conclusion itself:

- **The resampling unit may not be the season.** A paired comparison of our error against consensus
  error at the *player-season* level is ~1500 paired observations. The binding constraint is
  within-season correlation — clustering at G≈5. Wild cluster bootstrap at G=5 is unreliable, which
  is **materially different from impossible**.
- **Effect size is being ignored.** Beating consensus in 5 of 5 seasons by a wide margin is
  decision-relevant even when it is not publication-significant. This project is not publishing; it
  is deciding whether to trust a draft board.
- **Subsetting buys no independence.** Reject "5 seasons × 6 positions = 30". **Check whether anything
  in the repo already makes that error** — that would be a live defect, not a hypothetical.
- Is there a defensible bar *below* significance the project should report instead of staying silent?
  Silence about a real edge is also a failure.

**Verdict:** the claim is correct / over-conservative, and here is a test runnable now /
under-conservative, and even the accuracy claim is weaker than stated. Give a date and the reasoning
behind it.

## Q3 · Accumulated overfitting exposure

Pre-registration (ADR-C, thread 020) is recent. **Everything built before it was not pre-registered.**

Estimate the garden-of-forking-paths exposure against the 26 seasons: how many model variants,
feature choices, functional forms and hyperparameters were tried against the same history with no
multiplicity denominator? An order of magnitude with reasoning is more useful than a precise number
you cannot support.

Then the harder question: **does the pre-registration machinery actually bind?** A holdout requiring
a signed unseal entry is a guardrail only if the seal cannot be worked around. **Try to find the way
around it.** Report whether you found one.

Also relevant: two parameters were decided on 2026-07-27 (see `docs/decisions-needed.md`) —
`NEED_ADJUSTMENT_SCALE` deleted, `delta = 0.10` retained flagged with a pre-registered kill rule.
Confirm the kill rule is real and mechanical rather than aspirational.

---

## Reporting protocol

**Assume you may be cut off at any moment.** Budget is finite and expires tonight. Analysis held in
your context when capacity runs out is worth nothing.

**Create `docs/reviews/fable-rankings-2026-07-27.md` before any analysis**, containing only the plan
and `STATUS: STARTED`. Then keep it current at every milestone.

```
STATUS: STARTED | IN PROGRESS | COMPLETE | STOPPED — <where and why>

## Verdicts so far
<Q1/Q2/Q3, each with its verdict or "not reached">

## Headline findings
<stated in full here, not as pointers — if the founder reads only
 this section he should get the value>

## Next steps
<ranked, concrete, actionable without further analysis from you>

## What I would do with more budget
```

If you sense you are running short mid-question, **stop and write**. A recorded partial finding beats
an unrecorded complete one. `STOPPED — halfway through Q2, no conclusion` is a good outcome. A note
implying more completeness than exists is the only unacceptable one.
