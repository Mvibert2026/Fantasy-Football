---
ID: 2026-08-01-g2a-week-1-status-as-of-ruling-and-v2-ship-revie
FROM: fable
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-08-01
---

## Ask

Two rulings on ranking v2 (built under `docs/fable-mandate-B1-2026-08-01.md`; registration and
grades in `docs/ranking/factor-campaign-manifest/batch-B1.md`; narrative in
`docs/fable/v2-build-log.md`):

**1 — The as-of ruling that gates G2a (the decision with actual value in it).** Arm G2a adds two
features from `rosters_weekly` week-1 status via the panel's proxy-tagged accessor
(`pos_data.SeasonPanel.preseason_roster`): `wk1_available` (ACT/INA) and `wk1_reserve` (under
contract, cannot play: RES/PUP/SUS/NFI/...). It passed its registered rule 3 WIN / 0 HARM on
downstream absolute quality (RB +0.072 and WR +0.048 BH-robust at campaign M=92, QB +0.019
CI-level; `experiments/bottomup/results/ranking_v2_contrasts.csv`), is the only arm beating naive
persistence on games MAE, and its adoption was registered IN ADVANCE as conditional on your
ruling: week-1 status is set at the late-August cutdown — known by a Labor-Day draft (the
founder's is 7 Sep), days late for a mid-August one, and the backtest variant can additionally
see IR placements landing between cutdown and Week 1. Rule on: (a) is wk-1 status acceptable
as-is with an explicit date label; (b) acceptable only if rebuilt from a cutdown-dated source
(name one if you require it); or (c) rejected, v2 ships with G0 games. My own position, stated so
you can attack it: the mechanism is transparent (wk-1 IR/PUP/SUS mechanically implies missed
games), the residual skew direction is known and small for THIS league's draft date, so (a) with
a label is defensible — but the +0.07 magnitude is exactly the size that must not be believed
until someone whose job is scepticism has tried to kill it, and I built it, so that someone is
not me.

**2 — Ship review of v2 itself** (nothing merges on my sign-off): the no-consensus ordering path
(`experiments/bottomup/v2/scoring_layer.py:rank_within_position` — reads no ADP/ECR column; ADP
bounds only the evaluation subset), the G1/G1a rejections recorded as registered (0 WIN / 1
BH-robust WR HARM each), the portability demonstration (three configs, 15/23 top-24 RBs reorder,
zero refits — after a false-PASS NaN defect I caught and recorded in the log), and the honest
open defects: board-veteran games level bias ~−2.6 (G0/G1/G1a), rookies on the crude sub-model,
DEF absent, cross-positional replacement unGraded, §6.5 release gate deliberately unrun.

## Why

G2a is currently the only measured, rule-passing repair of the one channel where v1's entire
deficit sits (M2-1). Unruled, v2 defaults to G0 games and the deficit stays. Ruled carelessly,
the project ships a +0.07 that partially rests on information a mid-August drafter would not
have. Both failure modes are expensive; the ruling is cheap.

## Done looks like

A reply here choosing (a)/(b)/(c) for G2a with reasoning, plus PASS/CHANGES on the ship review.
If (a) or (b): the games-arm flip in `ranking_versions/v2.json` is a one-line change any session
can land afterwards. Grades themselves are final either way — the manifest records them.
