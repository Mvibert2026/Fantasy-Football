---
ID: 021
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: D-002, D-003
---

## Ask
Implement ADR-B from `docs/adr-drafts/ADR-B-rank-correlation-aggregation.md`. Rewrite
`_rank_correlation()` to return a per-position mapping. **A scalar return type should be a lint
failure** — the ADR is deliberate that no aggregate may be computed, stored, or logged, on the basis
that a field which does not exist cannot be quoted.

## Why
The current function pools all positions before correlating, which manufactures correlation out of
between-position mean differences. A model with zero within-position skill still posts a healthy
number, because QBs outscore TEs. Within-position ordering is the only skill that matters at a draft.

Three specifics from the ADR that are easy to get wrong:
- **Kendall's τ_b as primary**, Spearman secondary. Do not switch primaries if they disagree — flag
  the position `unstable` instead.
- **No minimum-games-played filter, ever.** It is the canonical survivorship error here: it deletes
  precisely the outcomes the model failed to anticipate.
- Ranked players with no production score **zero and stay in the sample**. Realized producers outside
  the ranked set are excluded from τ but reported as a mandatory "misses" line.

## Done looks like
Per-position output with τ_b, Spearman, n, both depth cutoffs, permutation interval, and the misses
line. Tests including one asserting the scalar path is gone. Then update D-002 and D-003 in
`docs/decisions-needed.md` with what the real numbers turned out to be. Commit hash and test count.
