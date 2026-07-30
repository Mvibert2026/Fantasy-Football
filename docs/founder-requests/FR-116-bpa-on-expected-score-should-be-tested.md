---
ID: FR-116
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
BPA on expected score should be tested as an arm

Founder's own words:

> "BPA on expected score probbaly should be tested too"

## Why it matters / PM's read

Currently tested: `bpa_consensus` (take the highest-consensus player). **Not tested: BPA on our own
expected score.** That is a different arm — it uses our projections rather than the market's ordering.

This matters because `bpa_consensus` **beat the VBD arm** in the FR-085 run (+24.1 realistic points,
+0.046 P(playoff), MARGINAL). Whether that is "consensus is a better ordering" or "any BPA beats our
VBD implementation" is unresolved, and a BPA-on-expected-score arm separates the two.
