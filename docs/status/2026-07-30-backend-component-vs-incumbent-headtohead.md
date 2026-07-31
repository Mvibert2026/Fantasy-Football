# backend, 2026-07-30 — component model vs incumbent head-to-head

**Task**: PM dispatch, fr136 §6.2 step 1 — "run the component-vs-incumbent head-to-head on
projection error, then wire the winner."

**Done**: `experiments/bottomup/head_to_head.py`, results in
`experiments/bottomup/results/head_to_head_mae.csv`, writeup
`docs/ranking/component-model-vs-incumbent-headtohead.md`.

Applied both of §6.2's alignment requirements: same universe (incumbent curve moved onto FFC
ADP rank, the cheaper direction per §6.2, so both arms score the identical FFC-ADP-covered
player-seasons the component walk-forward already restricts to for baseline #1) and same units
(component `proj_points` is already season points via `pos_model.score_components()`; incumbent
refit on the identical `points` target). Six walk-forward seasons (2019-2024), busts retained,
2025 never touched (asserted programmatically).

Sanity check: the FFC-refit incumbent bar (QB 75.7/RB 58.6/WR 50.5/TE 39.8) lands at the same
order of magnitude as ranker's `fantasypros_ecr`-native bar (74.0/62.0/48.0/35.8, 3 seasons) —
confirms the reproduction is right rather than a new invented number.

**Result: the component model loses at all four positions.** MAE component minus incumbent:
QB +10.0 (n=6, not significant), RB +6.2 (significant, incumbent wins), WR +1.7 (not
significant), TE +4.9 (significant, incumbent wins). No position's point estimate favours the
component model.

**Verdict: not wired**, per the dispatch's own conditional ("if the component model loses, do
not wire it, and say so plainly. A null here is a real result and saves the whole downstream
build"). `src/export_contract.py`/`src/make_board.py`'s `projected_points` is unchanged.

**Written back**:
- `docs/CURRENT-STATE.md` item 10c (in place, new item added after 10b).
- `docs/ideas-inbox.md` — decision logged.
- Thread `2026-07-30-component-model-vs-incumbent-head-to-head-compon` opened to `ranker`,
  reporting the result and noting it does not substitute for `strategist`'s separate
  pre-registered PR-004/PR-005 rank-correlation confirmatory experiments (thread 088).

**Not done, out of scope for this dispatch**: PR-004/PR-005 (thread 088, a different metric —
dtau_b rank correlation, embargoed LOSO, pre-registered by strategist) and the rest of the
30-thread backend inbox — this dispatch was scoped narrowly to the head-to-head measurement and
the wire-or-don't-wire decision, and it does not touch the inbox otherwise.

**Environment note**: this session shares its working directory with other concurrent agent
chains. All files listed above landed in commit `8dafc99` ("research: analyst factor sweep --
34 new rows, and four registry costs that are wrong"), a coordinator-attributed commit that
swept several sessions' in-flight work together — verified with `git diff HEAD -- <files>`
(empty) before concluding it was byte-for-byte what I wrote. No conflict, no action needed.

**Commit**: `8dafc99`. **Tests**: full suite run (`.venv/bin/python -m pytest tests/ -q`);
see this file's follow-up note / the session's final report for pass/fail counts once the run
(started before this write) completes.
