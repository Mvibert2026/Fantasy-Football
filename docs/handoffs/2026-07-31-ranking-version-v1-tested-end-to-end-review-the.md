---
ID: 2026-07-31-ranking-version-v1-tested-end-to-end-review-the
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: any confirmatory registration of a bottom-up ranking; whether the depth-matched sensitivity is admissible
OPENED: 2026-07-31
---

## Ask

**A ranking version has been assembled and tested end to end for the first time.** Your Ruling 3.4(3)
said the proposition "our model does not beat consensus" had never been tested with a model. It has
now. Four things need your ruling, and I have deliberately not resolved any of them myself.

Artifacts:

- Pre-commitment `docs/ranking/ranking-v1-precommit.md`, committed at **`5ffbbef`**, before the
  runner existed and before any v1 number was computed.
- Config blob `experiments/bottomup/ranking_versions/v1.json`, sha256 `ab15cb93467b4f3f…`.
- Results `docs/ranking/ranking-v1-results.md`.
- Code `experiments/bottomup/ranking_v1.py`, `…/ranking_v1_sensitivity.py`,
  `experiments/bottomup/components/ecr_baseline.py`.
- Raw `experiments/bottomup/results/ranking_v1_*.csv`.

**Q1 — the pre-registered MDE rule is wrong and I want it replaced, not patched.**
§2.5 of the pre-commitment defined the minimum detectable effect as the 95% bootstrap CI half-width
of a **baseline-vs-baseline** contrast (`b1_market_adp − b3w_wavg_ppg`), threshold 0.10 ρ, so that
computing it could not be peeking. At seven of eight cells it tracks the direct half-width within
0.01. **At panel-M QB it reports 0.085 while the actual v1-vs-market contrast has a half-width of
0.170 — a 2× understatement.** The proxy bounds the contrast it is computed on, not the contrast
under test. My proposed replacement: define MDE as the direct half-width of the contrast under test,
estimated from the *baseline arms'* season-to-season variance (still no v1 quantity, still not
peeking). **Your call, not mine** — and if you accept it, it changes panel-M QB's verdict from
`LOSES (pt est below parity floor)` to `CANNOT ANSWER`.

**Q2 — is §5's depth-matched sensitivity admissible, or is it post-hoc rescue?**
Panel E's pre-registered universe is the full ECR board (147–202 players per position), ~3× the
market board's draftable depth. Your Ruling 1 item 5 made `C2` — the *draft-relevant* universe — the
FDR endpoint. I re-ran panel E restricted to the depth the market itself declares draftable (top *N*
of ECR where *N* = the count FFC's ADP board covers at that position that season — externally
determined, not chosen by me). **It matters:** WR flips from −0.065 [−0.102, −0.041] (significant
loss) to +0.050 [−0.065, +0.204] (parity). QB and RB stay losses. I have reported it as **post-hoc
and labelled**, and the §7 verdict is taken from the pre-registered result. I want a ruling on
whether it is admissible at all, because the argument that it is *closer* to what `C2` means is
exactly the argument a motivated analyst would make.

**Q3 — the primary family and the BH correction.**
`F-RANKING-V1`, 8 tests (4 positions × 2 crowds), BH q = 0.10, three rejections all in the
*harmful* direction. Non-crowd baselines (B3 prior points, B4 tier heuristic) were held out of the
family as descriptive. Is that the right family boundary, and does `M_campaign` need to rise by 8 or
by 1 (v1 is one version, tested once, against a pre-declared baseline set)?

**Q4 — what a confirmatory registration of a ranking version should look like, if one is ever
warranted.** I am **not** requesting one now and **not** requesting the holdout. v1 is not frozen —
four named feature blocks are untested (snap counts 2013+, NGS 2016+, PBP-derived, recency
weighting). I want the *shape* of the registration on record before a version exists that deserves
it, so it cannot be written to fit a result.

## Why

Three of the four questions above are places where a ranker ruling on his own work would be exactly
the failure the structure exists to prevent, and Q1 is a case where the honest answer makes my own
result *less* conclusive rather than more. If Q1 and Q2 are left to me they will drift toward
whichever reading flatters the model.

Q3 and Q4 block the campaign: batch 8 needs a family boundary, and a bottom-up confirmatory
registration has been outstanding since thread 094 with nothing queued to spend the holdout on.

## Done looks like

A reply on this thread with: (1) accept/reject the MDE replacement, and the resulting verdict for
panel-M QB; (2) admissible / not admissible on the depth-matched sensitivity, with the reasoning
recorded so it binds future passes; (3) the family boundary and the `M_campaign` increment; (4) a
sketch of the confirmatory design, or an explicit "not yet, and here is the precondition."

## Context you should not have to re-derive

**The headline, so you are not reading the results doc cold.** v1 beats both trivial §6.5 baselines
decisively at RB and WR. **It beats neither crowd at any position.** It loses to expert consensus at
QB/RB/WR with BH-significant intervals; parity at WR against both crowds. Parity is not edge and the
results doc says so. Holdout 2025 was never read, per `CLAUDE.md` §6.3 as ruled today.

**The number that makes this a real test rather than a tautology:** v1 correlates with consensus at
**ρ 0.537–0.712** on the market board and moves players a mean of 2.4–8.8 places (max 53). The
shipped board correlates with consensus at **0.972** across the top 100. This is the first object in
the project that can actually disagree about a player — and it disagrees, and it is worse.
