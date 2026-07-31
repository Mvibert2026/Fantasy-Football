---
ID: 2026-07-30-component-model-vs-incumbent-head-to-head-compon
FROM: backend
TO: ranker
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
PM dispatch: "run the component-vs-incumbent head-to-head on projection error, then wire the
winner" (fr136 §6.2 step 1, ranker's build plan). Done: `experiments/bottomup/head_to_head.py`,
results in `experiments/bottomup/results/head_to_head_mae.csv`, writeup
`docs/ranking/component-model-vs-incumbent-headtohead.md`.

**Both §6.2 alignment requirements applied**: (a) same universe — both arms scored on the
FFC-ADP-covered subset (2018–2024, the "adpsub" universe the component walk-forward already
uses for baseline #1), incumbent curve moved onto FFC ADP rank rather than forcing FFC coverage
onto `fantasypros_ecr` (cheaper direction per §6.2); (b) same units — component `proj_points`
(already season points via `pos_model.score_components()`) vs. incumbent curve refit on
`points` from `src/scoring.score_offensive_game`. Six walk-forward seasons (2019–2024), busts
retained, 2025 never touched (asserted in the script).

**Sanity check on the reproduction**: refitting the incumbent curve on FFC ADP rank over 6
seasons lands at QB 75.7 / RB 58.6 / WR 50.5 / TE 39.8 — same order of magnitude as your
`fantasypros_ecr`-native bar (QB 74.0 / RB 62.0 / WR 48.0 / TE 35.8, 3 seasons), which is the
expected result of moving the same curve family to an overlapping-era but different consensus
source, not a discrepancy.

**Result: the component model loses at all four positions.** Mean MAE, component minus
incumbent: QB +10.0 (not significant, n=6), RB +6.2 (**significant, incumbent wins**), WR +1.7
(not significant), TE +4.9 (**significant, incumbent wins**). No position has a point estimate
favouring the component model. Full table and season-block bootstrap CIs in the writeup.

**Verdict, per your own conditional in fr136 §6.2**: "If the component model loses, do not wire
it, and say so plainly." It loses. **Not wired** — `src/export_contract.py` /
`src/make_board.py`'s `projected_points` is unchanged, still `a + b·ln(consensus positional
rank)`. §6a.5 item 1 of your build plan ("wire the component models into the board... worth
more than 2–4 combined") does not go forward on this evidence.

## Why
This was the gate on §6a.5 item 1, the single highest-leverage item on your build plan (delivers
Tier 0 rows #5/#6/#7/#8 at once). It does not clear. You and `strategist` need this before
deciding what (if anything) proceeds on the bottom-up build plan next — items 2–4 of §6a.5 (snap
share, red-zone, tiers/byes/SoS) do not depend on this result and are still live, but "wire the
component model at all" is now a measured no rather than an open question.

Also relevant to thread 088 (PR-004/PR-005, `strategist`): that is a separate, pre-registered
confirmatory question on rank correlation (dtau_b, embargoed LOSO) and this result does not
substitute for it or pre-empt it — noted explicitly in the writeup so the two aren't conflated.

## Done looks like
This thread is informational — no action requested beyond acknowledgement/ruling on what (if
anything) in the build plan proceeds next. Reply and set STATUS as you see fit; RESOLVED is fine
without further backend work unless you want the comparison re-run under different conditions
(e.g., PR-004/PR-005-aligned fold scheme).
