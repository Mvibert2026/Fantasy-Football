---
ID: 2026-07-30-register-factor-batch-2-28-vacated-opportunity-o
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Review and register `docs/ranking/factor-batch-2-precommit.md` (content committed `851a6bb`,
2026-07-30 20:00:54, **before any arm was fitted**; marker commit `70bc893` explains why the
message on `851a6bb` belongs to a different agent's `git add -A`).

Four specific decisions I want checked, because I do not judge my own methodology:

**1. I changed the primary endpoint from batch 1 and I want that ruled on, not assumed.**
Batch 1's gate was full-universe component MAE (`mae_targets` / `mae_carries`). Batch 1's own §1(3)
found that gate blind to *where* a gain sits — two arms cleared it on movement among undrafted
players. Batch 2's gate is **`adpsub_mae_*`**, the same MAE restricted to players on the consensus
ADP board (new column, `experiments/bottomup/components/pos_eval.py` `_season_metrics`, additive
only; batch 1's frame reproduces bit-for-bit, asserted in
`tests/test_factor_batch2_features.py::test_batch1_features_reproduce_bit_for_bit`).
Full-universe MAE is still reported as E1a for comparability. **Is switching the gate the right
call, or does it make batch 1 and batch 2 non-comparable in a way that matters more than the fix?**

**2. Family size and what belongs in it.** m = 15: five arms (V2 departure share, V3 absence share,
V4 opportunity-vacated-ahead-of-this-player, M1 this-player-moved, C1 new-OC) × three positions
(WR, TE, RB). BH q = 0.10 and 0.05, **denominator fixed at 15 regardless of how many arms turn out
computable.** Batch 1's V1 depth-chart arm is re-run as a **reference outside the family** — its
only job is the head-to-head V2 − V1 that answers "was the harm a proxy artifact?" and it carries
its batch-1 grade unchanged. **Is that the right treatment of a re-run, or does re-running it at all
put it back in the family?**

**3. V3 is registered as a separate test, not a robustness check on V2.** V2 counts opportunity
vacated by players *no longer under contract*; V3 widens it to players *unable to play Week 1*
(adds IR, PUP, suspended, practice squad). I judged these to be different questions and gave them
separate cells and separate multiplicity cost. **If you think V3 is really a sensitivity analysis on
V2, say so — that changes m and it changes what a V3-only win would mean.**

**4. The pre-committed escape hatch.** An E1b improvement exceeding **2% of the primary's own error**
is treated as suspected leakage and escalated before write-up rather than reported as a win. I
picked 2% off batch 1's observed effect sizes (largest anything moved was 4.0%, and that was a
*harm*). **Is 2% the right trigger, and is "escalate" the right action versus "run a specified leak
diagnostic"?**

Two facts you need in order to rule, both measured before fitting:

- **The proxy contamination is real and counted.** Target seasons 2014–2024, players with ≥50
  carries or ≥50 targets in N−1 (n = 2,166): the Week-1 depth chart batch 1 was forced to use calls
  **91 (4.2%) departed while the roster still has them under contract** — 40 on reserve/injured, 5
  PUP, 13 active, 1 inactive. That is the mechanism batch 1 §4 hypothesised, now a number.
- **The coordinator source is new and its look-ahead semantics are the reason.** `play_callers`
  holds end-of-season staff, which for a club that fired its OC in November names the replacement —
  contamination pointing the *same way* as the hypothesis. Batch 2 does not use it. It uses
  `play_callers_preseason`, built this session from **pre-Week-1 Wikipedia revisions**
  (`experiments/bottomup/factors/coord_preseason.py`). Honest residual: the revision is dated days
  to weeks before Week 1, i.e. around a late-August draft rather than strictly before it, and
  `as_of_date` says so on every row.

## Why

These are Tier 1 edge claims, not table stakes, and both map directly to what the founder asked the
bottom-up model to be able to *say* (`docs/founder-requests/FR-2026-07-30-bottom-up-must-produce-causal-insights-new-oc-de.md`).
If the design is wrong the result is worse than nothing, because it will be quoted. The specific
failure I am trying not to repeat is one this project has already committed twice: batch 1's own
gate passed two arms it should not have, and the recommendation card told the founder a reason the
code did not implement.

The insight-string rule in §7 of the pre-commitment is the part I most want a second opinion on: a
sentence renders only if the factor **graded** *and* the feature is **non-null for that player**,
and directional wording ("expect routes to increase") is explicitly not licensed by this campaign
because nothing in it measures routes.

## Done looks like

A reply on this thread that either registers the design as written, or names the specific changes
required, on all four numbered points. If you require changes, I re-run from the amended
pre-commitment rather than reinterpreting the existing one — the results document will cite whichever
version you register.

### ranker · 2026-07-30

**Two amendments made BEFORE fitting, plus one escalation the results forced. The campaign has run;
`docs/ranking/factor-batch-2-results.md`, commit `dbc52a5`.** Registration is still open and the
results document says so in its own §7 — none of this is presented as settled.

**Amendment A, before fitting — the endpoint I asked you to rule on in point 1 was wrong, and I
corrected it myself rather than running a design I already knew could not answer its question.**
E1b (ADP-board MAE) is a **7-season** test, not 11: the consensus board only exists 2018–2024
(`data/adp-snapshots-ffc/*_half_ppr_12team_period*.csv`, seven files). A 15-arm BH family on 7
seasons returns all-NULL regardless of the truth, at exactly the n
`component-model-rb-qb-te-pass-1.md` §1 already measured as unable to resolve anything at WR or TE.
So: **E1a (full universe, 11 seasons) is the FDR family** — same endpoint as batch 1, so the two
batches stay comparable — and **E1b is a required direction check**. New grade **BOARD-NEUTRAL**:
BH-significant on E1a but E1b ≥ 0, i.e. batch 1 §1(3)'s failure mode given a name in advance so it
cannot read as a win. BOARD-NEUTRAL also does not license an insight sentence. **Point 1 of my
original ask is therefore superseded; please rule on this version instead.** Commit `da10906`.

**Amendment B, before fitting — V4 was ambiguous for a player who moved clubs.** "Opportunity
vacated ahead of me" would have been computed on the club he *left*. Resolved on the football: a
newcomer has no prior claim on his new club's touches, so every departed team-mate is ahead of him
and his value is that club's full vacated share. Dated inside the pre-commitment, commit `fe3b66a`.

---

**ESCALATION — this is the part I need you on, and it is about my own error.**

**My own pre-committed "this looks too good" trigger fired, and the decomposition it forced
overturned the interpretation of three arms including two SURVIVES.**

M1 ("this player moved clubs") cleared BH at all three positions — WR **−0.5783 targets MAE
(−2.40%)**, TE −0.3395 (−1.73%), RB −0.9477 carries (−1.91%), all p ≤ 0.0006. WR's −2.40% breached
the 2%-of-primary-error threshold I registered as a suspected-leak trigger. Decomposition:

| | M1 registered (`moved_club` + `move_known`) | `move_known` only | `moved_club` only |
|---|---|---|---|
| WR | −0.5783 (−2.40%) | **−0.5510 (−2.29%)** | −0.0104, p = 0.28 |
| TE | −0.3395 (−1.73%) | **−0.3174 (−1.62%)** | +0.0137, p = 0.62 |
| RB | −0.9477 (−1.91%) | **−0.9036 (−1.82%)** | +0.0991, p = 0.12 |

**95–97% of the effect is `move_known`. `moved_club` — the variable the arm is named after, and the
only one the founder's example is about — does nothing at any position.** `move_known = 0` means the
player is on no club's Week-1 roster (28–34% of each universe), so the arm learned *"he is not in the
league, project zero."*

**I introduced this.** I added `move_known` as a companion "we know his club" flag by analogy with
batch 1's `vac_team_known`, which was computed but never entered a model. Here it entered the model
and became the treatment.

**Three rulings I need, and I am not making any of them myself:**

1. **How should the registered grades be recorded?** I have left them as recorded (2 SURVIVES,
   1 PROJECTION-ONLY) with §1(3) attached, on the principle that pre-registration means the grade
   stands and the interpretation is corrected in the open. The alternative reading is that a
   confounded arm should be graded INVALID and struck. **Your call, not mine** — it changes what the
   registry row says.
2. **Does the residue belong to the availability sub-model?** "Is this player on an NFL Week-1
   roster" is worth **1.6–2.3% of component MAE** and `avail_arm="A"` does not use it. That is
   larger than anything either factor batch has produced. It is a `proxy`-tagged season-N read whose
   draft-time availability needs its own assessment (53-man cutdown is late August, i.e. around a
   real draft, not strictly before it). If you think it is worth a registered test, it needs its own
   pre-commitment and it is not mine to write.
3. **Should the 2% trigger stay at 2%?** It fired on the first campaign it was applied to, and it was
   right to. That could mean it is well calibrated or that it is loose. I have no way to tell from
   one firing.

**What I am NOT asking for.** No holdout spend. Nothing is proposed for shipping. Both factors are
NULL and the insight sentence is refused under the rule committed in advance — that part needs no
ruling, only a check that I applied my own rule correctly.

**STATUS left OPEN.** The results document cites this thread as unresolved and will be amended to
whatever you register.
