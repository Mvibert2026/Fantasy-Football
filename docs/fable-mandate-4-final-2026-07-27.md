# Fable — final session before a week-long gap (2026-07-27)

**This is the last Fable session for approximately one week.** Everything you leave behind has to
carry the project without you. That constraint shapes the ordering below: the plan comes before the
build, because a brilliant experiment nobody can follow up on is worth less than a mediocre one with
a week of sequenced work behind it.

## Read first

Your own session-2 output — `docs/reviews/FABLE-EXT-2026-07-27.md` and the five reviews beside it.
Everything here builds on them. **Continue on the existing branch `fable/ext-2026-07-27`** (worktree
`.claude/worktrees/fable-ext`); it is still unmerged and master is still untouched. Do not merge.

## Standing rules

Reviews to `docs/reviews/`; code to the branch only. Do not touch `src/` on master, `frontend/` on
master, `docs/CURRENT-STATE.md`, or anything under `docs/handoffs/`. **Do not unseal the holdout** —
your own H1 finding makes that rule sharper, not softer. Cite file and line; write "unresolved"
rather than filling gaps. You are hired to refute, including your own prior conclusions — you already
overturned session 1's holdout clean bill, and that was the system working.

Keep `docs/reviews/FABLE-EXT-2026-07-27.md` current, or start a session-3 log beside it. Assume you
may be cut off; write incrementally.

---

# PRIORITY 0 — the one-week action plan · **write this first, before any analysis**

`docs/reviews/ACTION-PLAN-2026-08.md`. This is the deliverable that must exist even if nothing else
does.

The project has roughly **forty outstanding work orders** across your five reviews — W1–W10, T1–T10,
R1–R7, N1–N5, H1–H4, C1–C3 — plus a thread backlog of 64, a draft in late August, and a PM whose
judgment you have been asked to treat as advocacy. **Sequence it.**

What the plan must contain:

- **A dependency-ordered sequence** for the coming week, day by day or batch by batch. Which items
  unblock which. What can run in parallel given the collision constraints you documented, and what
  must be serialised.
- **An owner per item** — backend, frontend, data-ops, researcher, librarian, PM, or founder — and a
  rough cost. Anything a sonnet-tier agent can execute must be written so it can be, without you.
- **The critical path to draft day.** Which items are draft-blocking (T1, T5, T4-interim, T2 by your
  own pre-mortem) and which are not. If something must happen this week or the draft is compromised,
  say it in a sentence a tired founder reads correctly at midnight.
- **A founder decision list** — every choice only he can make, in plain language, with the trade-off
  and your recommendation. Do not route these through the PM's framing.
- **Explicit deprioritisations.** What should *not* be done this week, and why. A plan that includes
  everything is not a plan.
- **Failure branches.** For the three or four items most likely to go wrong, what the fallback is —
  so nobody stalls waiting for you.
- **What needs you when you return**, held rather than attempted badly in your absence.

Write it as a document the founder can act on alone. Assume the PM may be wrong.

---

# PRIORITY 1 — R1: vacated opportunity, the experiment you nominated

Your session-2 finding: the model beats last-season-rank at RB and WR but loses to consensus
everywhere, and **the shape of that gap is diagnostic** — worst at QB (−0.223) and RB (−0.110), near
zero at WR (−0.033) and TE (−0.001). You read that fingerprint as missing *situation information*.

**Test it.** Build vacated-opportunity features into the prototype and rerun the registered
walk-forward. This is the single experiment that converts your diagnosis into a measurement.

- **Register the prediction before fitting**, in the same discipline as session 2: expected direction,
  expected magnitude, and which positions should improve if the diagnosis is right. Your own
  fingerprint predicts the gain concentrates at RB and QB and is near zero at WR/TE — **say so in
  advance**, because a confirmed prediction registered ahead of time is worth far more than a good
  score found afterwards.
- **Log every variant**, continuing the existing count. Session 2's credibility came from 2
  configurations and an 8-cell denominator stated honestly; do not spend that.
- Report per-season, never pooled. Same baselines. Same metric. Do not change the objective mid-flight
  — if the registered metric turns out to be wrong, say so and stop rather than substituting a kinder
  one.
- **State up front what result would falsify the diagnosis**, and report honestly if it does. "Vacated
  opportunity does not close the consensus gap" is a valuable finding and eliminates the leading
  hypothesis; treating it as a disappointment would be a misreading.

---

# PRIORITY 2 — the QB arm

QB is where the model is worst (Δτ −0.108, VBD-capture −0.224, 3/13 folds) and where the consensus
gap is widest. Two things to establish:

1. **Why does it lose?** The PM's untested hypothesis: quarterback scoring is dominated by passing
   volume, which is highly team-stable, so last-season-rank is an unusually strong baseline and the
   usage features add variance without signal. Confirm, refute, or replace that explanation.
2. **Build the QB-specific arm** keeping prior-season points as a feature, per your own nomination.

Then the product question, which nobody has answered: **should the board be a position-hybrid?**
Bottom-up at RB/WR/TE, consensus or last-season-rank at QB, is defensible today on measured evidence
and better than either pure approach. Say whether you agree, and what the honest way to present a
mixed-provenance board would be — the traceability principle applies, and a board where different
rows come from different models must say so.

---

# PRIORITY 3 — H3, if budget remains

Pre-registration gate entrypoint wiring. Your own sequencing: it must precede ADR-E's first
confirmatory run, and that run is much closer than it was this morning. You estimated a full session;
if you cannot finish it, leave it clean and unstarted rather than half-wired, and say so.

---

# BEFORE YOU STOP

**Return to `ACTION-PLAN-2026-08.md` and update it** with everything this session changed — new
findings, new work orders, anything the R1 result reorders. The plan is the last thing you touch as
well as the first.

Then, in the landing note: the branch, the commits, what the new code found, test results, a per-item
merge assessment, and anything started and unfinished named explicitly.

**Silent non-delivery is the failure to avoid.** You found finished work invisible on an unmerged
branch and named it; do not become the second instance.
