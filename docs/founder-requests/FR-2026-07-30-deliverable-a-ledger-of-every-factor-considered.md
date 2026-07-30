---
ID: FR-2026-07-30-factor-ledger
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH — a named end-state deliverable
NEEDS: librarian
---

## Request

> "What I'll want at the end is a list of every factor we considered. Whether it was included or not
> and why. I hope the considerations are 100 or more but you don't have to anchor to that"

## What this is

**A standing deliverable, not a report.** The list of everything considered — with the disposition and
the reason attached to each row — is the artifact that makes the model defensible. A ranking whose
inputs can be justified one by one, *including the rejections*, is a different product from one that
merely works.

It is also the honest form of `CLAUDE.md` §6.3. Multiple-comparisons exposure is only auditable if the
denominator is written down. **A ledger of everything considered IS the denominator.** Without it,
"we tested 30 factors" is a claim nobody can check.

## Required per row

- The factor, defined precisely enough to compute
- **Disposition**: included / excluded / untested / blocked / rejected-with-evidence
- **The reason**, and for anything measured, the number and its interval — not a verdict word
- **Provenance**: internal hypothesis, registry, or external source with its tag
- Whether it was ever actually run, which is different from having a status

## Why "100 or more" is plausible

Sources already in the repo, before anything new is added:

| Source | Rows |
|---|---|
| `docs/test-registry.md` Tiers 0/1/2 | ~32 |
| `docs/test-registry.md` Tier 5 (rejected) | rejections already carry reasons |
| Analyst sweep 2026-07-30 | **34 new** (N1–N34), plus 8 definition-only |
| Component model feature sets | age, shares, injury, depth-chart arms |
| `factor-batch-1-results.md` | measured NULLs and harms |
| Yardage-bonus variance work | four independent instruments, all NULL |

The founder's number is reachable without padding, which matters — **a padded ledger is worse than a
short one**, because it inflates the multiplicity denominator with things nobody considered.

## The distinction the ledger must preserve

**"Untested" and "rejected" are different, and today produced examples of both being confused.**
Registry #13 measured NULL on target-share *stability* and is easy to misread as a verdict on target
share itself. #28's harm was a proxy artifact, not a finding about vacated opportunity. The ledger
must make a row's *scope* explicit enough that its result cannot be over-read.
