# Component model vs. incumbent `projected_points` — the head-to-head nobody had run

**Backend, 2026-07-30.** `docs/ranking/fr136-q1-bottom-up-assessment.md` §6.2, step 1 of the
build plan: measure the component models against the *incumbent*, on the metric the product
actually displays — projection error in season points — not against ADP/prior-points/heuristic
baselines, and not on rank correlation. Nobody had run this. It is now run.

Reproduce: `.venv/bin/python -m experiments.bottomup.head_to_head`, main checkout,
branch `claude/pm-agent-setup-gobxa0`. Script: `experiments/bottomup/head_to_head.py`.
Raw output: `experiments/bottomup/results/head_to_head_mae.csv`.

## Alignment (§6.2's two non-negotiable requirements)

**(a) Same universe.** Both arms are scored on the identical ADP-covered player-seasons —
FFC half-PPR 12-team ADP, 2018–2024 — the same "adpsub" universe the component walk-forward
already restricts to for its baseline #1 comparisons. Moving the incumbent (rather than forcing
FFC coverage onto `fantasypros_ecr`) is the cheaper direction, as §6.2 anticipated, and it is
what yields **six** evaluation seasons (2019–2024) instead of the shipped curve's three
(2022–2024) — one prior FFC season is enough to fit a 2-parameter curve.

**(b) Same output units.** The component model's `proj_points` is already full **season
points, bonuses included**, produced by `pos_model.score_components()` under this league's
exact ruleset (`experiments/bottomup/components/pos_model.py:453-455`, `LEAGUE_SCORING`). The
incumbent's curve — `a + b·ln(positional market rank)`, walk-forward, refit each season on
strictly prior seasons only — is reproduced here on the same target: `points`, scored via
`src/scoring.score_offensive_game` and summed over the season. No new model on either side;
this is arithmetic on two objects that already exist.

**Sanity check that the reproduction is right, not a new number invented for this pass.** The
incumbent bar ranker measured on its native universe (`fantasypros_ecr`, 2022–2024) was
QB 74.0 · RB 62.0 · WR 48.0 · TE 35.8. The same object, refit here on FFC ADP rank over six
seasons, lands at QB 75.7 · RB 58.6 · WR 50.5 · TE 39.8 — same order of magnitude at every
position, as expected for the same curve family moved to a different (but overlapping-era)
consensus source. This is the expected result of an alignment move, not a discrepancy.

2025 is never read by either arm (`FIRST, LAST = 2014, 2024` unchanged; asserted in the script).

## Result — mean MAE, season points, walk-forward, busts retained

| position | seasons | n (mean/season) | incumbent MAE | component MAE | Δ (component − incumbent) |
|---|---|---|---|---|---|
| QB | 6 (2019–2024) | ~21 | **75.7** | 85.7 | +10.0 |
| RB | 6 (2019–2024) | ~53 | **58.6** | 64.8 | +6.2 |
| WR | 6 (2019–2024) | ~58 | **50.5** | 52.2 | +1.7 |
| TE | 6 (2019–2024) | ~16 | **39.8** | 44.7 | +4.9 |

Season-block bootstrap (4,000 reps, paired difference component − incumbent, negative =
component wins):

| position | Δ | 95% CI | verdict |
|---|---|---|---|
| QB | +10.04 | [−3.84, +20.70] | does not clear 0 — directionally worse, underpowered at n=6 |
| RB | +6.18 | [+0.92, +11.07] | **incumbent clears 0 — component loses, significant** |
| WR | +1.65 | [−0.87, +4.04] | does not clear 0 — directionally worse, underpowered |
| TE | +4.86 | [+3.77, +6.47] | **incumbent clears 0 — component loses, significant** |

**The component model does not beat the incumbent at any of the four positions.** Two losses
are statistically significant on this design (RB, TE); the other two (QB, WR) are directionally
worse but the six-season bootstrap cannot resolve them from zero. There is no position where
the point estimate favours wiring the component model as `projected_points`.

## Verdict: do not wire

Per the mandate's own conditional — *"If the component model loses, do not wire it, and say so
plainly. A null here is a real result and saves the whole downstream build."* — it loses.
**`projected_points` stays a function of consensus rank, not the player.** This is consistent
with, and now directly measures, what §1.4 of `fr136-q1-bottom-up-assessment.md` already found
against the *market* (RB negative, others not clearing) — the component models were never shown
to beat a rank-based baseline on rank correlation either, and now the same holds on projection
error against the specific object that ships.

**What this does and does not settle.** This is a single, non-pre-registered comparison — six
seasons, four positions, no multiplicity correction, walk-forward but not the embargoed-LOSO
design `strategist`'s PR-004/PR-005 registrations use for the confirmatory rank-correlation
question (thread 088). It answers exactly the question it was asked — does the shipped
component projection beat the shipped incumbent on projection error, same universe, same units
— and the answer is no, cleanly enough at RB and TE that a different six seasons would need to
move the estimate by several points to flip the sign. It says nothing new about the deeper
rank-correlation confirmatory question PR-004/PR-005 are separately answering.

**Why the component model likely loses here even though it beats naive persistence on every
component (`component-model-*-pass-1.md` §4).** Beating last season's raw total is a low bar a
consensus-informed curve also clears trivially (consensus itself encodes last season's
performance). The incumbent's curve is fit directly on this season's own market-anticipated
rank order, which already prices in exactly the injuries, role changes, and depth-chart shifts
the component model has to infer bottom-up from stale lagged features. The component model's
edge channel (§4 of fr136, the oracle ladder) is real and large, but this measurement shows the
project has not yet captured enough of it to clear a curve fit to the market's own forward-
looking read.

## Action taken

- **Not wired.** `src/export_contract.py` / `src/make_board.py`'s `projected_points` is
  unchanged — still `a + b·ln(consensus positional rank)`, the object §1.1 of
  `fr136-q1-bottom-up-assessment.md` already characterised.
- Logged in `docs/ideas-inbox.md`.
- Thread opened to `ranker`/`strategist` reporting the verdict, since it was the gating item
  for §6a.5 item 1 ("wire the component models into the board") in the build plan.
