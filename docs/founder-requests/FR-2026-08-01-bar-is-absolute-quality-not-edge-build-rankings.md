---
ID: FR-2026-08-01-bar-is-absolute-quality-not-edge-build-rankings
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Bar is absolute quality not edge: build rankings independent of consensus, portable across league scoring

Founder's own words, chat 2026-08-01, the day after Fable's M2 review ruled that the campaign's
measurement frame was asking a question it could not answer in the affirmative:

> "Aka independent of consensus. Create the best draft rankings we can that could be easily applied
> to different league scorings by updating points. Our bar is not consensus. It's how good can our
> rankings be. When we think they are as good as they'll get (any and all components in it that need
> to be), then we can test vs the other three models like consensus, consensus adjusted and ADP etc."

## Why it matters

**This is a change to the standing law, not a work item.** Written into `CLAUDE.md` as new **§2a**,
with a scope amendment to **§6.5** (when the baseline gate fires) and a new schema principle in
**§4** (projections stored as stat lines, never as points). Recorded here as the source.

It resolves the frame problem Fable ruled on in `docs/fable/M2-findings.md` §F1-F7: "can we beat
consensus" was being asked of an object *derived from* consensus, which is close to structurally
incapable of returning a win. ~90 factor nulls carry far less information than they appeared to.
The founder's answer is not a better test -- it is to stop deriving from consensus and stop steering
by it.

## Initial read

**Three binding consequences, all now in §2a:**

1. **Consensus is not an input.** Built from player-level projections, not by re-scoring someone
   else's order. The shipped board is consensus re-scored -- within-position *identical* to
   consensus, deviating only cross-positionally via four slopes and four replacement ranks. It is
   replaced, not extended.
2. **Consensus is not the development signal.** Absolute quality against realised outcomes steers
   the build; §6.5's four baselines become a **release gate run once at the end**. §6.5 is not
   weakened -- a version failing it still has no edge and is still reported as a failure. Only the
   *timing* changed.
3. **Projections output stat lines, not points.** Points = scoring config applied to stat lines;
   ranks = roster shape applied to get replacement levels. Changing league scoring must re-score and
   re-rank **without re-fitting**.

**The argument PM gave the founder that strengthens his own case:** (1) and (3) are the *same*
requirement, not two. A board whose within-position order comes from consensus cannot respond to
league scoring at all, because consensus is produced for a generic 12-team full-PPR room -- so
half-PPR, the stacking yardage bonuses, and 10-team replacement levels cannot reach the ordering
today by any route. Scoring portability is not bolted on after independence; it is only achievable
*through* it. This also means the request is not optional polish: the current board structurally
cannot do the thing he asked for.

**The hard part, named in advance.** v1's rate projections are already at or better than market
parity. Its entire measured deficit is one channel -- **projected games** (Fable M2-1) -- which is
also precisely where consensus's real advantage lies: it knows who is going to play. So independence
stands or falls on building our own player-availability model from injury history, age, workload and
pre-Week-1 status (resolved vs ongoing absence -- the Burrow/Hill defect class). **Distinct from
*draft* availability despite the shared word; do not conflate them.**

**Statistical note.** Removing the consensus comparison from the development loop does not increase
overfitting risk, because the consensus gap never provided overfitting protection. The protection is
and remains the sealed 2025 holdout (§6.3) plus registered thresholds and the campaign-level `M`.
Recorded so this is not later mistaken for a loosening of the guardrails.

**Sequencing.** This becomes the core of Monday's Fable builder mandate (see
`FR-2026-08-01-turn-the-keys-over-to-fable-to-build-the-next-bo`), dispatched on the fresh weekly
pool. Priority order inside it: stat-line projection architecture, then the player-availability
model, then rates. PR-007 (recommendation constants) is unaffected and continues.
