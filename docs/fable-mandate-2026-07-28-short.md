# Fable mandate — 2026-07-28, short window

**Budget: small. Assume you may be cut off.** Write your conclusion first, evidence second. A
half-finished document with the answer at the top is useful; a complete argument with the answer at
the bottom is not.

**No code changes. No builds. Analysis, design and pre-registration only.** Reading the repo is fine.

**Output:** one file per mandate under `docs/reviews/`, named as stated. If you only get through one,
do F-A.

---

## Standing context you must apply

**The calibration prior.** Across sessions 3–4, four of five registered prediction sets were
materially wrong, all in the same direction: over-crediting situation stories. Vacated opportunity
and rookie draft capital are both cleanly eliminated as consensus-gap channels. The PM's hypotheses
come from that same family — treat them as advocacy.

**Where things stand.** Board is consensus-derived at player level; edge channel is positional
revaluation only. Bottom-up prototype beats last-season-rank at RB (Δτ +0.041) and WR (+0.043),
loses QB, unproven TE. QB modelling is closed — six configurations failed, do not reopen it.
Three leagues, different scoring and team counts. Draft provisionally 30 August 2026.

---

## F-A — The next registered test set for bottom-up rankings
`docs/reviews/fable-bottomup-next-tests-2026-07-28.md`

The RB and WR wins are real but small, and they are wins over *last-season rank*, not over consensus.
Design what gets tested next.

Required:

1. **State the falsification condition for bottom-up as a whole.** What result, at what point, means
   we stop and ship consensus? Name it now, before we are invested. This is the most valuable
   paragraph in the document.
2. **Pre-register the next hypothesis set** — prediction, direction, magnitude, and what would refute
   it — *before* any run. Rank by expected information per unit of compute, not by how interesting
   they are.
3. **TE is unproven, not failed.** Is it worth a run, or is the position too low-variance to matter
   in a 10–12 team league?
4. **Weighting.** How should component weights be derived rather than assumed? If the honest answer
   is "we do not have enough data to fit them," say that and specify the defensible default.
5. **What is the smallest thing that would let us claim, honestly, that our rankings beat consensus
   at anything?** Not "would be nice" — the smallest defensible claim.

## F-B — Is ADP velocity testable before 30 August?
`docs/reviews/fable-adp-velocity-testability-2026-07-28.md`

The founder wants to see who is climbing and who is fading, and to use it. Two distinct claims, and
they must not be conflated:

- **Velocity → draft position.** "Rising ADP means he goes earlier than his current ADP implies."
  This is a hazard-model input and is our actual business.
- **Velocity → performance.** "The hot player is overvalued; buy the faller." A value claim, and it
  is squarely in the family that has been wrong four times out of five.

Answer:

1. Can either be validated before the draft? Our harvested FFC history is **seasonal aggregate ADP,
   not dated snapshots.** Daily capture starts today, 33 days out.
2. If validation is impossible, say so plainly and specify what may still be *displayed* as
   description with no predictive claim attached.
3. Is a within-2026 test on 33 daily points worth anything, or is that self-deception?
4. What would we need to have started collecting, and when, to answer this properly next year?

## F-C — Week-leverage weighting, and the playoff-weeks discrepancy
`docs/reviews/fable-week-leverage-2026-07-28.md`

Config says playoff weeks are (16, 17). The PM has repeatedly said 15–17. **Nobody has resolved
this, and it feeds at least three calculations.** Resolve it, then generalise:

1. Which is correct for each of the three leagues? If it differs by league, the constant is wrong by
   construction.
2. Should week-leverage weighting be derived from league structure, or is a flat weighting more
   honest given what we can measure?
3. Bye-week cost: the PM proposed a formula. It is from the same over-crediting family. Is
   bye-week collision worth modelling at all, or is it a rounding error next to draft-position error?

## F-D — Should the handoff system be rebuilt?
See `claude/sprint-closeout.md`, section "This week, additionally", item B — the full framing, the
measured failure table, and the five objections you are asked to press are already written there.
Do not re-derive them.

`docs/reviews/fable-backlog-architecture-2026-07-28.md`

New evidence since it was written, and it strengthens the case: **two isolated worktrees each
allocated thread ID 073 on the same night**, both following the rules correctly. Atomic allocation
only protects a single working tree. Registered as thread 076, unfixed.

## Standing — the interrupt audit
Data now exists in `docs/status.md` for 2026-07-27/28: 1 permission prompt, 2 judgment questions
(both decided-and-logged), 1 genuine escalation. Classify, name the largest category, and give the
single change with the best ratio. Include the counter-question: the founder personally caught a
false sync-bug claim, two wrong thread closures, and an over-broad archive instruction. Say what
replaces him as error detector before recommending his removal.
