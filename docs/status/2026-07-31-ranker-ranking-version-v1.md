# 2026-07-31 · ranker · ranking version v1, assembled and tested end to end

**Dispatch:** assemble a ranking version and test it end to end — "the single measurement that
answers the founder's question." Founder, same day: *"let's make sure we do whatever testing is
needed to help us build a competitive independent model too."*

## What happened, in order

1. Read the three named documents and `CLAUDE.md` §6.5 as amended today (four baselines, both
   crowds). Confirmed against `docs/preregistration/` that **the lagged-YPC → RB volume wire has no
   registration** and excluded it, per the dispatch.
2. **Wrote and committed the pre-commitment first** (`5ffbbef`) — panels, baselines, endpoint, FDR
   family, power rule, and the numeric definition of "competitive" — before the runner existed.
   Mid-task the coordinator relayed the founder's holdout ruling (now `CLAUDE.md` §6.3: the holdout
   does not open until `fable` has run); added §2.7a recording it as a hard gate **and** the rule
   that an ambiguous result is reported as ambiguous, never as "needs the holdout."
3. Built `experiments/bottomup/components/ecr_baseline.py` — **§6.5 baseline #2 had never had a
   loader**; the whole factor campaign's "consensus" was market ADP.
4. Built `experiments/bottomup/ranking_v1.py` and ran it. **First run returned an entirely NaN
   expert panel.** Cause: `pd.DataFrame(columns=[...])` gives object-dtype columns, concatenating the
   empty 2018–2020 ECR seasons promoted `season` to object, and every downstream merge matched zero
   rows while looking healthy. Fixed, and guarded with a match-count assertion.
5. Ran the primary, then three labelled post-hoc sensitivities.
6. Opened `strategist` and `fable` threads. Nothing merged to `src/`.

## The result

**v1 beats neither crowd at any position.** It beats prior-season points and the positional-tier
heuristic decisively at RB and WR. Against expert consensus it loses at QB/RB/WR with BH-significant
intervals; the QB and RB losses survive depth-matching. Parity at WR against both crowds — and parity
is not edge.

**The number that makes this a real test:** v1 correlates with consensus at ρ 0.537–0.712 on the
market board and moves players a mean of 2.4–8.8 places. The shipped board's figure is 0.972 across
the top 100. This is the first object in the project that can actually disagree about a player. It
disagrees, and it is worse.

Full tables: `docs/ranking/ranking-v1-results.md`.

## Two things I got wrong, recorded because they are the useful part

**The MDE rule I pre-registered is contrast-specific and wrong at one cell.** I defined the minimum
detectable effect as the CI half-width of a *baseline-vs-baseline* proxy contrast, so that computing
it could not be peeking. It tracks the direct half-width within 0.01 at seven of eight cells and
understates it by **2× at panel-M QB** (0.085 vs 0.170). Accepting the correction makes my own result
*less* conclusive — panel-M QB becomes CANNOT ANSWER rather than a loss — which is why it went to
`strategist` rather than into a quiet edit.

**I predicted in advance that QB and TE would trip the power rule in panel M.** TE did. QB did not,
and then QB turned out to be the one cell where the rule itself fails. Prediction recorded before the
run; half right.

## Decisions taken (logged in `docs/ideas-inbox.md`, not escalated)

- **Only pre-committed feature blocks enter v1** — admits table stakes #7/#8, puts #6 in a declared
  secondary, excludes #5 (arms D/E are post-hoc by their own source comment) and the lagged-YPC wire.
- **Rookies pinned in rank space**, changed before the first run; git history proves the ordering.
- **`extra_universe_fn` on `WalkForward`**, default `None`, so the expert board could define a
  universe without duplicating the audited harness. Believed inert; `fable` asked to verify.
- **Depth-matched panel E labelled post-hoc** and kept out of the verdict, precisely because it flips
  WR from a significant loss to parity.

## What this does not settle

It does not establish that consensus is unbeatable — Ruling 3.4 refuses that and nothing here
supports it. It does not test the cross-positional channel, which is the shipped board's entire
current content. It does not answer QB or TE on the market board. And it is **one version**: snap
counts (2013+), NGS (2016+), PBP-derived red-zone/xFP, and per-position recency weighting are all
present in `data/nfl.db` and untouched by any model.

## Files

`docs/ranking/ranking-v1-precommit.md` · `docs/ranking/ranking-v1-results.md` ·
`experiments/bottomup/ranking_versions/v1.json` · `experiments/bottomup/ranking_v1.py` ·
`experiments/bottomup/ranking_v1_sensitivity.py` ·
`experiments/bottomup/components/ecr_baseline.py` · `experiments/bottomup/results/ranking_v1_*.csv`

Commits: `5ffbbef` (pre-commitment), `e29e955` (runner + ECR baseline), `77618af` (results).
Tests: 17 passed, 4 skipped on the component-harness selection after the `pos_eval` change.
