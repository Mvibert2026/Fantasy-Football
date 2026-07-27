# Fable — ranking design mandate (session 3)

**SUPERSEDED BY `docs/fable-mandate-4-final-2026-07-27.md`.** Never ran standalone — folded into the
extended mandate's Priority 1. Do not run this separately.

**Read `docs/reviews/fable-consensus-anchoring-2026-07-27.md` first.** It established the premise for
this mandate: the shipped board is openly, structurally 100% consensus-derived — same positional rank
gives the same projection, so **player-level edge is structurally zero** — and the genuinely bottom-up
ranking does not exist yet. ADR-E is the plan for building it.

That review asked whether ADR-E survives a circularity attack. **Nobody has asked whether it is a good
model.** That is this mandate.

---

# PRIORITY 1 — will ADR-E actually produce edge, and is it the right design?

## Q1 · Where is the edge supposed to come from, and is that source real?

Read ADR-E and state, in your own words, **the specific mechanism by which this design is supposed to
beat a wisdom-of-crowds aggregate.** Then attack that mechanism.

Consensus is genuinely hard to beat on central tendency. The candidate edges worth evaluating
separately rather than hoping they aggregate:

- **Touchdown regression** — a 14-TD season anchors human perception, and TD rate regresses hard.
  Probably the most reliable single edge available. Does ADR-E capture it, and how aggressively?
- **Vacated opportunity** — targets, carries and red-zone touches leaving a team do not distribute the
  way consensus assumes.
- **Scheme and personnel turnover** — new coordinator, new quarterback, line change. Requires
  projecting rather than remembering, which is where humans are weak.
- **Age curves at the tails** — decline is not linear and consensus tends to be late.

For each: is it in ADR-E, is it measurable with data we have, and is it plausibly *mispriced* rather
than merely measurable? The bar is not "we can compute this" — it is "consensus does not already."
Most candidates fail that bar. Say which.

## Q2 · Is the architecture right?

The most robust finding in fantasy projection is that **opportunity is predictable and efficiency is
not.** Snap share, target share, carry share, route participation and red-zone usage persist year to
year; yards per target, yards per carry and above all touchdown rate regress hard.

Does ADR-E separate those into distinct stages, with regression strength **estimated rather than
assumed**? If not, should it? If it does something different, is the different thing better — say so
rather than defaulting to the conventional answer.

Also evaluate the layer above: **points = games played × points per game × usage ramp.** The project
has three founder requests (injuries with recovery ramp, suspensions, bye weeks) that are all
statements about the first factor and are not expressible until it is separated out. Does ADR-E have
that decomposition? If not, that is a design gap, not a feature request.

## Q3 · Is a distributional ranking the better route to beating consensus?

Consensus publishes **no uncertainty** — ECR is one number per player. A ranking that produces a
distribution (median plus a genuine interval, ideally P(top-N at position)) could beat consensus **on
decisions** without beating it on point rank, because draft decisions are made under uncertainty and
consensus supplies none.

Two players with identical ECR are not the same asset if one is a locked-role veteran and the other a
rookie splitting carries. And a well-calibrated interval is **testable on 26 seasons today**, with no
dependence on consensus history — which matters because the beat-consensus clock has not started.

Is this a better primary objective than point-rank accuracy? Argue it either way, but argue it.

## Q4 · What is the ceiling?

**State before you look at any result:** what fraction of season-to-season fantasy point variance is
plausibly explainable at all? Much of it is injury and touchdown luck, forecastable by nobody. A model
explaining 45% may be near the ceiling; treating that as failure against an imagined 80% would be a
misreading, and this project is prone to it.

## Q5 · What would you build instead?

If you were designing from scratch against the founder's goal — measurably better across draft prep,
the live draft, and in-season management — **what would the central abstraction be?** Say so even if
the answer is ADR-E. Especially then.

**Deliverable:** `docs/reviews/fable-ranking-design-2026-07-27.md` — a verdict on whether ADR-E can
produce edge, the named mechanisms ranked by plausibility, design changes with reasoning, and work
orders precise enough for a sonnet-tier agent.

---

# PRIORITY 2 — draft-day pre-mortem (only if Priority 1 is complete)

The draft is in a few weeks. It is **the one unrepeatable event in this project.** Everything else can
be redone.

Assume it is draft day and the session went badly. **Work backwards: what failed?** Not a risk
register of hypotheticals — a concrete list grounded in this repository's actual failure history and
current gaps.

Seeds, deliberately incomplete: suspension and injury tables stale (both unbuilt per the 2A review);
ADP snapshot too old to reflect draft-day behaviour; league settings wrong for the league actually
being drafted; the app reading a shadow data directory again; the database locked or mid-migration;
recompute too slow under a real clock; autopick misread as a manual pick; undo mis-applied; the wrong
league selected; the machine or the app dying mid-draft with no recovery path and no remote.

**Deliverable:** `docs/reviews/fable-draft-day-premortem-2026-07-27.md` — failures ranked by
(likelihood × damage), each with the cheapest thing that prevents or detects it, and a **printable
pre-draft checklist** the founder runs the morning of. That checklist is the point.

---

# Rules

- **Write only to `docs/reviews/`.** Do not modify `src/`, `frontend/`, `docs/CURRENT-STATE.md`, or
  anything under `docs/handoffs/`. No production code. No thread replies.
- **Do not unseal the holdout.**
- **Create `docs/reviews/FABLE-RANKING-2026-07-27.md` before any analysis**, containing the plan and
  `STATUS: STARTED`. Keep it current at every milestone. Same structure as the previous session's
  landing note: what is done and where, what is in flight, what was not reached, headline findings
  **stated in full**, ranked next steps, and what you would do with more budget.
- **Assume you may be cut off.** If you sense you are running short, stop and write. A recorded
  partial finding beats an unrecorded complete one.
- **You are hired to refute, not confirm.** Every document here is advocacy written by the people
  being evaluated. If ADR-E survives your attack, say so plainly.
