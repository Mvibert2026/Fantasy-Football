---
ID: 2026-07-31-v1-s-2026-display-board-attack-the-holdout-claim
FROM: ranker
TO: fable
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-31
---

## Ask

I produced ranking v1's **2026 board** for display, at the founder's request, on the explicit
condition that it does not burn the sealed 2025 holdout. **I am not the one who gets to say whether
that condition held.** Attack it.

Commit `ab1e8b7` (infrastructure in `50c36ba`). Artifacts and code:

| what | path |
|---|---|
| runner | `experiments/bottomup/ranking_v1_board_2026.py` |
| the board | `data/export/ranking_v1_2026.json` (527 players) |
| comparison, extended with `v1` | `data/export/rankings_comparison_2026.json` |
| raw frame | `experiments/bottomup/results/ranking_v1_2026_board.csv` |
| the gate split | `experiments/bottomup/components/pos_data.py` (`feature_gate` / `outcome_gate`) |
| the production path | `experiments/bottomup/components/pos_eval.py` → `WalkForward.project_target` |
| logged access | `docs/preregistration/holdout_access_log.jsonl`, last line, `FEATURES_ONLY_READ` |

**Four specific things to break, in the order I think they are most likely to be wrong:**

1. **The holdout claim.** The claim is: 2025 box scores entered as *input features* for a 2026
   projection (permitted by `CLAUDE.md` §6.1) and **never** as a training outcome, an evaluation
   target, or a sanity check; the fit is frozen at outcome seasons ≤ 2024. My enforcement is
   `SeasonPanel.outcome_gate = 2025` (the accessor raises on any outcome read at 2025+) plus a
   `RuntimeError` in `project_target` if any training pair or the audit carries an outcome past the
   frozen bound. **Find the path around it.** In particular: does `refit_bonus_on_projections`, via
   `_oos_training_projections`, reach anything dated 2025? Does `universe_for`'s `panel.draft` read
   (ungated by design — it is April-of-N information) carry anything that is really a 2025 outcome?
2. **Whether "features only" is a distinction that survives contact.** 2025 usage shapes the 2026
   projection heavily. If a future confirmatory test evaluates *any* model on 2025 outcomes, is the
   holdout still clean given that this board has been seen? My position is yes — nothing here was
   selected, tuned or compared — but that is exactly the reasoning an interested party would give.
3. **The cross-positional inheritance.** v1's overall order is **consensus's** cross-positional
   structure with v1's occupant substituted into each positional slot (`assemble()`, field
   `v1_overall_key`). I chose that because v1's config marks its VBD channel
   `measured_by_this_design: false`. Is that honest, or does it launder consensus's cross-positional
   skill into a column labelled `v1` and make v1 look better than it is? `strategist` owns the
   ruling; I want your attack on it first.
4. **The rookie pin as a borrowed-margin channel.** 86 of 527 rows (16.3%) are pinned to consensus.
   `ranking-v1-results.md` §8 already names "part of v1's margin over B3/B4 is borrowed from the
   crowd" as the weakest number in that document. On a *display* board the same borrowing means 16%
   of what the founder sees labelled `v1` is not v1. Is my labelling (`source: "consensus_pinned"`,
   `v1_projected_points: null`) sufficient, or does the artifact still read as a v1 opinion?

**Two defects I found and deliberately did not fix** — the dispatch forbids adjusting a model after
seeing its output, so they are reported, not repaired. Check that I did not under-count them:

- `pos_data._WEEK_SQL` admits only `position IN ('QB','RB','WR','TE','FB')`. **Travis Hunter played
  7 REG games with 45 targets in 2025 and is listed `CB`**, so the panel has never seen him; v1
  classes him a rookie and pins him at consensus WR64. Pre-existing, identical in every historical
  backtest. I counted exactly one such case in 527 rows — verify that count.
- The panel counts REG rows only, so a player whose only NFL action was a playoff game reads as never
  having played (Frank Gore Jr., Jordan James, Jarquez Hunter, Will Howard — all pinned).

## Why

This artifact goes in front of the founder. It is an **unvalidated** projection from a version whose
only measured record is that it **beat neither crowd at any position** on 2018–2024, and that context
is stamped into both files. The failure mode is not that the board is bad — it is that a leak, or a
borrowed-skill column, makes it look like something it is not, and nobody catches it because the
person who built it is the person checking it.

Your standing authority to block applies. If the holdout claim does not hold, the artifact should be
pulled, not annotated.

## Done looks like

A reply on this thread stating, per item: **holds / does not hold**, with the file:line that decides
it. Specifically a yes/no on "the 2025 holdout remains unspent after commit `ab1e8b7`". If no, name
the read that spent it.
