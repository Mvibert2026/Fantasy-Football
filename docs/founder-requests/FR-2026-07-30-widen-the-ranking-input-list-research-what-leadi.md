---
ID: FR-2026-07-30-widen-the-ranking-input-list
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH — feeds question 1, the founder's stated first priority
NEEDS: researcher (discovery), then ranker (prioritisation), then the test campaign
---

## Request

Founder's own words:

> "Don't be too narrow with scope of rankings. There are so many potential inputs. Researcher
> probably can look what leading analysts do and say and add those to the list of things to test."

## He is right, and the distinction that makes him right is worth stating

**Breadth costs nothing at hypothesis generation and everything at testing.**

- **Generating candidates is free.** A factor nobody thought of cannot be tested. `docs/test-registry.md`
  is a list somebody wrote down once; its boundary is an artifact of who was in the room, not of what
  predicts fantasy points. Widening it has no statistical cost at all.
- **Testing them is where the cost lands.** CLAUDE.md §6.3: ~30 factors at p<0.05 yields ~1.5 false
  positives by chance, and the exposure is at the **campaign** level, not per test. Doubling the
  candidate list doubles that exposure *if everything gets tested*.

So the correct response to "don't be narrow" is **generate widely, then prioritise ruthlessly and
test few**. Those are not in tension; treating them as one decision is what makes them look like it.

The founder is asking for the first half. The second half is ranker's, and the campaign design
(FR-134) already carries the requirement that every item names its falsifier and its baseline before
anything runs.

## Why this is well-timed

Ranker's Q1 assessment found the shipped board is **within-position identical to consensus** — its
entire deviation is cross-positional. A board that reproduces consensus ordering within position has,
by construction, no proprietary input doing any work inside a position. The gap is not a weighting
problem. **It is an inputs problem**, which is exactly what the founder has just pointed at.

It also found four Tier-1 factors marked unbuildable are simply unfetched — play-by-play 2009–2025 is
20.4 seconds and 15.2 MB. So the near-term constraint on breadth is not data availability either.

## Scope of the research

What leading analysts actually use, sourced rather than recalled. Named practitioners and shops,
what each claims predicts, and — critically — whether the claim is backed by anything public or is
assertion. A factor list is only useful if each entry carries where it came from and how strong that
provenance is.
