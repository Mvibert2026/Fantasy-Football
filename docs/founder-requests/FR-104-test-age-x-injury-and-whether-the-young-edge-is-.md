---
ID: FR-104
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Test age × injury — and whether the "young WR/TE" edge is really an availability effect

Founder's own words:

> "did you test injury vs age?"

## What has and has not been tested

**Separately: yes. Together: no.**

| Tested | Where | Result |
|---|---|---|
| Age (main effect) | `docs/analysis/adp-vs-production-2026-07-30.md` §Tier 2 | Young WR/TE (≤23) beat ADP by ~35 VBD pts/season, both eras. **MARGINAL** |
| Age × **position** | same | Robust direction, noisy magnitude |
| Prior-season games missed (main effect) | same, line 199 | **NULL** vs ADP mispricing — not significant, sign order not monotonic, flips between eras |
| Prior games, de-trended vs consensus | `docs/ranking/bottom-up-research-pass-1.md` §4.4 | WR **+0.170** — "consensus over-rates wide receivers coming off a partial season." Recorded at half weight, r² ≈ 0.03 |
| **Age × injury interaction** | — | **Never tested** |

## The question underneath, which is the valuable one

**Is the young-WR/TE edge actually an availability effect wearing a costume?**

Younger players get hurt less, therefore play more games, therefore score more total points. If that
is the mechanism, "young" is not a talent signal at all — it is a durability proxy, and it should be
modelled as games-played rather than as age. That changes what we would do with it.

This is testable directly: decompose the young-player VBD advantage into a **games-played component**
and a **points-per-game component**. If it is all games, the finding is about availability. If it is
all rate, age is telling us something about production the market misses. If it splits, say how.

## A conflict this should also resolve

Two of our own results point opposite ways on age at WR:

- `adp-vs-production` §Tier 2: young WR/TE **beat** their ADP.
- `bottom-up-research-pass-1` §4.4: age at WR is **−0.083** against de-trended consensus — i.e. mildly
  the other way.

Different baselines (ADP vs. consensus), different metrics (VBD vs. de-trended residual), different
windows. Not necessarily contradictory, but nobody has reconciled them, and the ledger should not
carry both as if they agree.

## Initial read

Not the founder's own words — PM's read.

**Do not read this as "find the age–injury link."** The most likely honest outcome is that injury
history remains null (it was null on its own, and `bottom-up-research-pass-1` separately found
prior-two-season games predicts target-season games at only r = 0.09–0.18 — availability is
near-unforecastable). If so, the interaction almost certainly has nothing in it either, and the
decomposition is still worth running because it tells us **what the age finding actually is**.

Sample discipline matters more than usual: an interaction test slices an already-marginal main effect
into smaller cells. State cell sizes, use Wilson intervals, and treat anything that only appears in
the interaction as a hypothesis.
