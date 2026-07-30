# HANDOFF — ranker, RB/QB/TE component model (FR-072)

Branch `worktree-agent-ab3387738c3dfd2a8`, pushed. Commits: `5f8efc1` (pre-commitment),
`018bdf9` (all code + all results).

## Done and verified by running

All four positions modelled, all runs executed, every number below came out of a real run.

- **Shared harness**, `experiments/bottomup/components/`: `pos_data.py`, `pos_features.py`,
  `pos_model.py`, `pos_eval.py`, drivers `run_position.py` / `run_variants.py` /
  `run_availability.py`. `wr_data.py` and `run_wr.py` untouched — pass 1 still reproduces
  (+0.0481 vs ADP, verified this session).
- **Pre-commitment committed before any result existed**:
  `docs/ranking/component-model-multipos-precommit.md`.
- **Look-ahead audit passes at every position** (assert in each run: max feature cutoff and max
  outcome season both strictly below target; zero outcome reads at target). 2025 never opened.
- **Survivorship**: zero-game players retained — RB 336/1441, QB 214/869, TE 219/1041.

### Headline, model minus consensus ADP (Spearman, season-block bootstrap, n=7 seasons)

| pos | vs ADP | 95% CI | power check: ADP − B3 heuristic |
|---|---|---|---|
| WR | +0.051 | [−0.011, +0.129] | +0.043 [−0.032, +0.126] — no power |
| RB | **−0.052** | [−0.126, +0.038] | **+0.134 [+0.043, +0.223] — HAS power** |
| QB | −0.069 | [−0.255, +0.104] | +0.038 [−0.039, +0.137] — no power |
| TE | −0.024 | [−0.182, +0.123] | +0.058 [−0.055, +0.224] — no power |

**No position beats consensus. RB is the meaningful null** — the design can detect ADP's edge over
the heuristic there, and the model still does not have one.

Component projections beat naive persistence decisively at every position (e.g. RB rush yards
−35.1 [−45.9, −24.0]; QB pass yards −63.7 [−99.6, −27.8]).

### The availability defect — tested, and the WR pass 1 recommendation does not survive

Five arms × four positions, all run (`run_availability.py`, output in
`experiments/bottomup/results/availability_arms_metrics.csv`).

- Arm B (injury report) improves availability MAE **at WR only** (−0.150 [−0.254, −0.068] on the
  returning-from-absent class). Fixes A.J. Green 2020 from 0.91 → 9.09 projected games (actual 16).
- **Arm B improves the ranking at no position.** WR ADP-board −0.007 [−0.022, +0.009]; at TE it
  actively hurts, −0.028 [−0.057, −0.001].
- **Data-quality finding that reframes the whole thing:** the injury report accounts for 26–35% of
  short absences and **2.5–4.8% of absences of nine games or more**, because season-ending IR drops
  a player off the weekly report. Verified by hand: Dak Prescott has zero injury rows for 2020.
- Arms D/E (weekly depth chart, covers 36–97% of the same weeks) were added **post-hoc** and also
  fail; the depth chart marks IR players as off-roster, which misinforms.

### Other measured results
- Stacking bonus is worth 0.57% (TE) to 2.39% (QB) of realised points; oracle ceiling +0.026 (WR),
  +0.027 (RB), +0.030 (TE), +0.043 (QB) ρ on the ADP board. **The WR pass's caveat that its null
  "does not transfer to RB" was wrong — I measured RB and it transfers.**
- QB rushing share of points rises +0.755 pct-pt/season [+0.583, +0.926]; the model tracks it, lag
  +0.176 [−0.105, +0.456] does **not** clear zero.
- QB passing-bonus calibration ratio drifts +0.043/season [+0.003, +0.084] — the one place a
  recency-weighting fix has demonstrated need.
- Secondary variants (reported, not selected on): RB opportunity-share +0.0085 [+0.0032, +0.0137]
  full universe, null on ADP board; QB deep 2002+ sample degrades component MAE; TE WR-pooling
  changes nothing (+0.0007).

## Half-done — exactly where I stopped

1. **`docs/ranking/component-model-rb-qb-te-pass-1.md` is NOT WRITTEN.** This is the main
   deliverable and the single next step. Everything it needs is in
   `/tmp/claude-0/.../scratchpad/run_{RB,QB,TE,WR,avail,variants}.txt` and in
   `experiments/bottomup/results/*.csv` (committed). Re-runnable end to end.
2. **Multiplicity is not yet stated in any artifact.** Roughly 170 interval tests were run. ~8.5
   false "CLEARS 0" are expected by chance. Results with a CI endpoint near zero — RB arm B MAE
   −0.051, RB arm D ρ −0.0015, QB arm D ADP ρ +0.0082, TE arm B ρ −0.028 — **must be labelled as
   not surviving that discount.** Do not quote them as findings.
3. **Two handoff threads not yet opened**: (a) to `data-ops`, asking for
   `nflreadpy.load_rosters_weekly()` ingestion — it carries `status` ∈ {ACT, RES, INA, PUP, DEV,
   CUT, RSN/SUS, RET}, goes back to at least 2002, and is the only source found that marks both
   season-ending IR *and* suspension. Verified: Michael Thomas 2021 shows RES × 17 weeks where the
   injuries table has zero rows. (b) reply on thread 094 to `strategist` reporting that the
   availability factor it was asked to register is now measured and null on ranking, so the
   registration should probably be redirected.
4. `docs/CURRENT-STATE.md` and `docs/status/` not yet updated. No ADR written.

## Verified vs assumed

- **Verified by running**: every number above; the look-ahead audit; survivorship counts; injury and
  depth-chart coverage percentages; the WR pass 1 reproduction.
- **Assumed, not verified**: that `depth_charts_weekly`'s `depth_team == '1'` means first on the
  positional depth chart (the `pos_rank` column is 100% NULL, so `depth_team` is the only usable
  rank field). Low risk — arms D/E fail anyway.
- **Known limitation, stated in the pre-commitment before it was hit**: suspension files no injury
  report, so arm B cannot see it. Confirmed by DeAndre Hopkins 2023 getting *worse* under arm B.

## Nothing is left half-applied

No shared code outside `experiments/bottomup/components/` was touched. `src/` untouched. The new
modules are additive — nothing existing imports them, so `run_wr.py` and the shipped pipeline are
unaffected. Safe to leave exactly as is.
