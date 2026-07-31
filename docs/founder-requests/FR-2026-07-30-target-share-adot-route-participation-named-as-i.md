---
ID: FR-2026-07-30-target-share-adot-route-participation
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH — names concrete inputs for question 1
NEEDS: ranker, data-ops (route data)
---

## Request

> "It wouldn't surprise me if our board is close to consensus either. We need our own bottoms up
> proprietary though.
>
> The target share AdDOT route participation etc is inportant."

## On "not surprised the board is close to consensus"

Fair, and consensus is genuinely hard to beat — `CLAUDE.md` §6.5 exists because of that. But the
measurement says something narrower and more actionable than "close": within position the board is
**identical**, per-position τ_b delta exactly 0.000000 across 12 of 12 position-seasons. Not close —
the same ordering. That is not the expected difficulty of beating consensus; it is the absence of any
player-level input at all.

## His three factors, against what has actually been measured

**These are three different situations and collapsing them would lose real information.**

| Factor | Registry | Status — measured, not assumed |
|---|---|---|
| **Target share** (prior-year target/touch share) | Tier 0 **#8** | `SPEC`. **Never wired.** A table stake, unimplemented |
| **Target share *stability* YoY** | Tier 1 **#13** | **NULL** — no ranking effect anywhere. But see below, this did **not** test his factor |
| **Opportunity share** | Tier 1 **#20** | **NULL at RB**; **at WR it earns its place** — removing it costs +0.196 targets MAE on the ADP board |
| **Air yards / aDOT** | Tier 1 **#14** | `NEW`, **never run** |
| **Route participation rate** | Tier 1 **#17** | `NEW`, **never run**, and flagged High edge — the highest-rated unrun row in Tier 1 |
| **WOPR** (target share + air yards) | Tier 1 **#15** | `NEW`, never run. Derived from two of the three he named |

### The distinction that matters most

**#13's NULL is not a verdict on target share.** It tested whether the *year-over-year stability* of
target share adds signal **beyond** target share itself. It does not. That is a finding about a
second-order transformation, not about the factor the founder named.

Target share itself is **Tier 0 #8, unimplemented**, and the closest thing to a direct test — #20 at
WR — is **positive and measured**: +0.196 targets MAE on the ADP board. His instinct has supporting
evidence, not contradicting evidence, and reading #13 as a kill would be a real error.

That same run also measured YoY persistence of target share: **WR +0.652 [+0.624, +0.680]**, TE
+0.632, RB +0.548 — role-tier persistence, just below snap share's +0.707. A factor that persists at
0.65 is exactly the kind that belongs in a prior-year-input model.

## Route participation — the one with a data problem

`CLAUDE.md` §5 flags it: **not directly in nflverse.** It needs NGS or a documented proxy, and the
spec's own standing instruction is to *flag clearly if proxied*.

Two facts make this tractable now:

- **NGS 2016+ is already in `data/nfl.db` and is untouched by any model** (ranker's inventory today).
- Play-by-play 2009–2025 is landing now via data-ops — 816,856 rows, 20.4 seconds measured.

So the honest position is: route participation is computable as a **proxy**, from data we now hold,
and must be labelled as a proxy wherever it appears. It is not blocked; it is unbuilt and requires an
honesty label.

## What this does not settle

Whether any of them **beats the baseline** is a Tier 1 edge claim and carries §6.3's multiplicity
exposure. Target share as a Tier 0 table stake goes in on construction grounds; aDOT, route
participation and WOPR are edge claims and must earn their place against a holdout, with the
campaign-level correction applied.
