---
ID: FR-101
STATUS: ANSWERED
SOURCE: coordinator relay, 2026-07-30 ranker session
RAISED: 2026-07-30
---

**NUMBER IS PROBABLY WRONG AND IS THE TOOL'S, NOT MINE.** `tools/founder_requests.py new` allocates
on creation and this worktree (`agent-a2668c91115660701`) only carries FR-001..FR-071, while FR-072
through at least FR-095 already exist on branches it does not have. Whoever merges should renumber
both this and FR-072-rank-positions-by-volatility-per-roster-slot. Same failure mode
`tools/handoffs.py check` is currently red on for threads 093/094 and ADR-054/055.

## Request — founder's own words

> "why not use points for volatility, you have an average, and the curve has a shape with tails that
> should naturally figure this out for you"

## Why it matters

He is describing the exceedance-curve machinery already in the component model, and he is right that
it is the correct mechanism. The problem is that it does not currently do what he assumes.
`experiments/bottomup/components/pos_model.py:300`:

```python
def _bonus_design(ypg):
    return np.column_stack([np.ones(len(ypg)), np.log1p(np.clip(ypg, 0, None))])
```

P(a game clears the threshold) is a function of **mean yards per game and nothing else**. Two players
at 60 yards a game get identical bonus expectations whether their weekly lines are 60/60/60 or
20/20/140. The tail shape is inferred from the average, never measured. Same in `wr_model.py:281`.

`CLAUDE.md` §7 asserts the stacking bonuses "reward ceiling outcomes over floor, which should
influence how variance is valued in rankings." That second clause is only operational if tail shape
carries information the mean does not.

## Status

**Answered in the same session, and the answer is no.** `docs/ranking/fr086-volatility.md` §3.
Code `experiments/volatility/exceedance_dispersion.py`. Raw
`data/qa/fr086-exceedance-dispersion-2026-07-30.json`.

Adding the player's own prior-season measured yardage dispersion to that design matrix is **NULL at
every threshold, in every family, at every shrinkage level from k=0 to k=16.** Expected-bonus-points
MAE, walk-forward: rec 0.8072 → 0.8093, rush 0.9679 → 0.9719, pass 1.7694 → 1.7669. Two of eleven
results clear zero and both point the **wrong** way.

The setting was deliberately the most favourable one that exists — both arms were given the player's
*realised* mean ypg, where in production the mean is a projection and noisier. If it does not help
there it cannot help in the pipeline.

This is a **different question** from PR-002 (is "spike-week player" a persistent category?
between-player, categorical, 0 of 36 survived BH) and from component-model pass 1 §6.1 (does the
residual clearance rate persist? same idea, but the instrument is a count of ~10 threshold crossings
a season). This one uses the full game-level yardage distribution and is the lowest-noise of the
three. All three agree.

The league **does** pay for ceiling, and the amount is measured: a high-volatility WR earns **+0.94
bonus points a season** more than a low-volatility WR at the same scoring level (SURVIVES).

**Open, and escalated to `strategist` rather than decided:** whether `CLAUDE.md` §7's second clause
should now be amended to say the ceiling premium is real, under one point per season, and not
exploitable beyond what a mean-based projection already captures. That is an edit to the standing
spec and the operating rules put it outside `ranker`'s authority.
