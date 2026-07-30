---
ID: FR-099
STATUS: ANSWERED
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Answer (backend, 2026-07-30)

Full writeup: `docs/analysis/consensus-vs-adp-2026-07-30.md`, code in
`analysis/consensus_vs_adp.py`. Pending `strategist` methodology review
(`docs/handoffs/NEW-consensus-vs-adp-methodology-review.md`).

**Coverage correction first:** the premise "five completed seasons (2021-2025) have both [ECR and
ADP]" is wrong — FFC ADP has no 2025 archive in any format. True overlap is **2021-2024, n=4**.
2025 is therefore never read; not holdout discipline, the data isn't there.

**Overall correlation:** tau_b 0.52-0.79 (mean 0.67) — strong but well short of the ~0.95 assumed
in this request; a real, sizeable disagreement subset exists (52% of matched players/season differ
by >1 round).

**On that disagreement subset: indistinguishable, use either.** Pooled ECR win rate 0.546, Wilson
CI [0.491, 0.600] — crosses 0.5. Per-season table shows real instability (0.474-0.652); the pooled
lean is carried almost entirely by one season (2023). **One real, not-yet-confirmed interaction
worth a future pre-registration:** early-draft disagreements (top ~5 rounds) favor ECR (0.595,
CI barely excludes 0.5) with ~5x the effect size of late-round disagreements, which are a coin
flip.

**Third-baseline add (ECR into the bottom-up-vs-consensus-ADP comparison):** assessed, not done —
requires re-running `ranker`-owned walk-forward infrastructure that's mid-review elsewhere. Logged
as follow-on, not attempted speculatively.

## Request
Is consensus or ADP the better baseline — and is bottom-up better than top-down?

Founder's own words:

> "isn't that also the spine that bottom up rankings need? is bottom up better than top down? I just
> want our own proprietary rankings equal to or better than consensus and/or adp, and evening knowing
> if consensus or adp is better is good insight"

## Why it matters

Three questions. The first is an observation and it is correct; the second is partly answered; the
third is untested and cheap.

### 1. "Isn't that also the spine that bottom up rankings need?" — yes

The factor-verdict registry (FR-098) is not just documentation for the Draft Guide. **It is the
specification of the bottom-up model.** A bottom-up ranking is precisely an assembly of factors that
each earned their place against a holdout. The list of factors marked `IN FORMULA` *is* the model.

That reframes FR-098 from a reporting task to a modelling one, and explains the current position:
the `IN FORMULA` set is close to empty, which is exactly why we do not beat consensus.

### 2. "Is bottom up better than top down?" — partly measured already

| Comparison | Result |
|---|---|
| Bottom-up component model vs. **naive persistence** (prior-season points ranked — a top-down baseline) | **Bottom-up wins decisively at every position.** SURVIVES. |
| Bottom-up component model vs. **consensus ADP** | Does not win at any position. RB is a real null; WR/QB/TE underpowered. |

So bottom-up beats the *weak* top-down baseline and loses to the *strong* one. The honest reading is
not "bottom-up is worse" — it is that consensus is a far stronger baseline than prior-season points,
and our component model currently sits between the two.

*Source: `docs/ranking/component-model-rb-qb-te-pass-1.md` §1–2.*

### 3. "Is consensus or ADP better?" — untested, and we have the data

**These are different things and the project has been conflating them.** Expert consensus (what
analysts say) and ADP (what drafters actually do) diverge, and `CLAUDE.md` §4 already anticipates the
distinction with a `ranking_source` enum (`proprietary` / `expert` / `league_adp` / `market_adp`).

Coverage confirmed in `nfl.db`:

| Source | Table | Coverage |
|---|---|---|
| Expert consensus | `rankings` (`fantasypros_ecr`) | 2021–2026, ~400–560 players/season |
| Market ADP | `ffc_adp_snapshots` | 12-team FFC archive |

**Five completed seasons (2021–2025) have both plus realised outcomes.** The comparison is directly
answerable and nobody has run it.

## Initial read — the design point that makes this test worth running

Not the founder's own words — PM's read.

**A naive overall comparison will fail, and not because there is nothing there.** ECR and ADP are
enormously correlated — likely ~0.95+. A rank-correlation contest across the whole board will be
dominated by their agreement, the difference will be tiny, and with five seasons it will be
underpowered. That is the same wall the model-vs-consensus test hit at three of four positions.

**The information is in the disagreements.** Restrict to players where ECR and ADP diverge
materially — say by more than a round — and ask which side realised outcomes favoured. That subset is
smaller but each observation is informative rather than redundant, which is what buys back power.

That framing also produces something directly usable at the draft: **a rule for what to do when the
experts and the room disagree about a player.** That is worth more than a scalar verdict on which
source is better overall, and it is available now rather than after the model improves.

**Explicit non-goal:** this does not require the bottom-up model to work. It is a measurement of two
external baselines against each other, and it is informative regardless of whether we ever beat
either.
