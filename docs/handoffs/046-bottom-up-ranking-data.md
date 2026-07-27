---
ID: 046
FROM: pm
TO: data-ops, strategist
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: bottom-up ranking framework
---

## Correction to a framing I have been repeating, and it matters

I have said several times that a proprietary ranking cannot be validated until ~2029. **That is only
true of one claim, and I have been applying it to two.**

- **"Our ranking beats consensus."** Requires consensus history to compare against. That exists only
  for 2021–2025, one season held out, so n=4 and the minimum attainable p is 0.0625 before any
  correction. Genuinely dead until more seasons accumulate.
- **"Our projections are accurate."** Requires only projected-versus-actual outcomes. That data goes
  back to **1999**. Twenty-six seasons. This is measurable *today*, with real confidence intervals,
  and it is not close to the significance floor.

Those are different questions and only the first is blocked. A bottom-up model can be built and its
accuracy honestly validated now. Alpha remains unclaimable. The founder's position — build a
respectable bottom-up ranking, do not wait — is correct, and my caution was misapplied.

The existing rank-to-points curve explains **16–27% of variance** (R² 0.158–0.266 by position). That is
the bar to beat, and beating it is an accuracy question, not an alpha question.

## Ask — ingest the feature data, prioritised

Analysts build bottom-up projections from usage and opportunity, and their aggregate is decent. The
method is not mysterious: project volume, project efficiency, convert to points. It needs features.

**Tier 1 — volume and opportunity. The core of any bottom-up projection.**
- Snap counts and snap share
- Target share, carry share, route participation
- Red-zone and goal-line usage
- Air yards and aDOT

**Tier 2 — context.**
- Team pace, plays per game, pass/run rate over expected
- Offensive line and defensive quality faced
- Vegas team totals and spreads where obtainable

**Tier 3 — stability and situation.**
- Historical week-to-week volatility per player
- Age curves by position
- Depth-chart role — **known blocker: the source ends at 2024**, so this cannot inform 2026 from
  nflverse. Report whether any alternative exists rather than assuming not.

For every source: how far back it goes, where it is missing, and where it is present-but-unreliable.

## The caveat that is real — regime change, not sample size

"More data is better" holds within a regime and fails across one. The NFL of 1999 is not the NFL of
2026: passing rates, pace, target concentration and positional scoring have all moved. A model fitted
across 26 undifferentiated seasons may be confidently wrong about 2026.

The project already anticipated this — `src/regimes.py` exists. So the requirement is not "ingest
everything and fit"; it is **ingest everything, and let the regime work decide what is in-sample.**

Known quality holes to carry forward:
- **Targets and air yards are unreliable 2003–2008** — present in the data but effectively zero. Any
  feature built on them must refuse those seasons rather than treat them as observed zeros.
- Depth charts end 2024.

## For `strategist`

Once the inventory exists, specify the framework: which features, what the target variable is (season
points? per-game? volume then efficiency separately?), how to validate accuracy on 26 seasons, how to
handle regime, and the pre-committed threshold at which the bottom-up rank replaces or supplements the
consensus-derived board.

Framework and validation plan first, defended, then build. That sequencing is unchanged — but the
reason for it is discipline, not a data ceiling, and the ceiling I cited does not apply here.

## Done looks like

`data-ops`: a source inventory in `docs/research/` — per feature, availability by season, quality
caveats, ingestion cost. Then ingest Tier 1.
`strategist`: the framework ADR, with accuracy validation designed against 26 seasons and the
beats-consensus question explicitly deferred and labelled as a separate claim.
