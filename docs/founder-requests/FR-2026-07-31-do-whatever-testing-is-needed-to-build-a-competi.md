---
ID: FR-2026-07-31-do-whatever-testing-is-needed-to-build-a-competi
STATUS: IN-PROGRESS
SOURCE: chat, 2026-07-31, relayed via pm dispatch to ranker
RAISED: 2026-07-31
---

## Request

Founder's own words, verbatim:

> "let's make sure we do whatever testing is needed to help us build a competitive independent
> model too."

## Why it matters

It authorises the testing budget for the bottom-up model *as a model*, not as a stream of
single-feature ablations. Until today every one of ~90 registered tests in the factor campaign was
one feature inside one component of an **unshipped** model, and no ranking version had ever been
assembled or measured. The word that does the work is **"independent"**: the shipped board correlates
with consensus at ρ 0.972 across the top 100 and holds no player-level opinion at all, so it is not
an independent model in any sense the founder would recognise.

Read alongside the same day's ruling that made both crowds required (`CLAUDE.md` §6.5) and the
holdout gate (`CLAUDE.md` §6.3, "we won't unlock the holdout until after fable has a chance to run"),
this sets the standard: independent, measured against both crowds, and not confirmed on the holdout
until adversarial review has run.

## Initial read

*Not the founder's words — ranker's read.*

**Acted on the same day.** Ranking version **v1** was assembled and tested end to end
(`docs/ranking/ranking-v1-results.md`, pre-commitment `docs/ranking/ranking-v1-precommit.md` at
commit `5ffbbef`, config `experiments/bottomup/ranking_versions/v1.json`).

**"Independent" — achieved.** v1 correlates with consensus at ρ 0.537–0.712 on the market board and
moves players a mean of 2.4–8.8 places (max 53). It is the first object in this project that can
disagree about a player.

**"Competitive" — not yet, and the number is on the record.** v1 beats prior-season points and the
positional-tier heuristic decisively at RB and WR. It beats **neither crowd at any position**: it
loses to expert consensus at QB/RB/WR with BH-significant intervals, and sits at parity with both
crowds at WR. Parity is not edge.

**What this FR still authorises, in priority order.** Four feature blocks are named, present in
`data/nfl.db`, and untouched by any model: snap counts (2013+), NGS (2016+), PBP-derived red-zone and
xFP, and per-position recency weighting. Each is one pre-registered factor against v1 as the
incumbent, registered by `strategist` before running. That is the honest reading of "whatever testing
is needed" — v1 is a first version, not a verdict on the approach.

**What it does not authorise:** spending the 2025 holdout. §6.3 gates it on `fable`, and v1 is not
frozen.
