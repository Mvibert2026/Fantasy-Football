---
ID: 096
FROM: backend
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
Founder asked (verbatim): "so now we can also look at ADP vs Production and try to establish
patterns." Backend ran that analysis this session (Sonnet/default tier — this dispatch did not
name Opus/high-effort, flagging per operating-model rules rather than stopping to ask). Full
writeup: `docs/analysis/adp-vs-production-2026-07-30.md`. Script: `analysis/adp_vs_production.py`.
Raw output: `data/qa/adp-vs-production-2026-07-30.json`.

Please review, at Opus/high effort, before any of this reaches the ranking model:
1. The residual design (value-over-replacement against an overall cross-position ADP-rank-ordered
   curve, §1.2 of the writeup) — two prior design mistakes are documented in the writeup and the
   script's own module docstring (per-position curve tautology; raw-points-across-positions
   conflating position scarcity with market error); check whether a third remains.
2. Whether the round-conditional RB finding (§2, "position residual conditional on round bucket")
   is real signal or still partly a regression-to-the-mean artifact against a skewed value curve
   (§1.5's caveat) — this is the one result flagged MODERATE confidence and the most likely
   candidate to actually change ranker behavior.
3. Whether the young-WR/TE (age ≤23) result (Tier 2, +34.6 train / holds directionally both eras)
   is strong enough to become a pre-registered ranker hypothesis, and what the correct next test
   would be (draft-simulation-based evaluation per guardrails §6, not just list correlation).
4. The data-source caveat (§0): everything here runs on 12-team FFC mock ADP, 2018-2024, not this
   league's real 10-team ADP, which does not exist historically anywhere in this project. Confirm
   whether that gap alone should block using this as a ranker input regardless of the statistics.

## Why
No ADR was opened and no ranker code was touched this session, deliberately — per the dispatch's
own instruction not to duplicate the ranker's concurrent RB/QB/TE component-model work and per
CLAUDE.md SS8 (Statistician/Red-team gate methodology and completed milestones before they
advance). This thread is that gate. Until it closes, nothing in the writeup should be treated as
more than a pre-registered hypothesis for the ranker's next factor-testing pass.

## Done looks like
A reply in this thread stating, for each of the four review points above: agree / disagree, with
reasoning, and if disagreeing on point 1 or 2, whether the residual/curve design needs a rerun
before anything downstream trusts the numbers. STATUS set to RESOLVED by strategist once posted.
