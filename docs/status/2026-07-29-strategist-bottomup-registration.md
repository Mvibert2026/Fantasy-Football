# 2026-07-29 · strategist · PR-004 bottom-up confirmatory registration

**Role:** strategist (Opus/high). **Shell:** none, by design — this session wrote a
pre-registration and could not, and did not, run any measurement.

## What was asked

Pre-register the one confirmatory bottom-up ranking experiment that has never been run
(ADR-E §9 / F-A §1's A0, "F-BOTTOMUP-CORE"), and commit the decision rule before anyone runs it.

## Premise challenged

The brief asserted *"the baseline that matters is consensus, not last-season rank."* Correct in
principle (`CLAUDE.md` §6.5), **not achievable with this data**, and the registration says so
rather than hedging. Consensus ECR coverage is 2021–2025; 2025 is the sealed holdout, leaving
n=4. The exact two-sided sign-test floor at n=4 is p=0.125 — unreachable at alpha=0.05 before
any correction, the same wall PR-003 documented. Consensus is registered as **descriptive
only** (no p-value, no CI, per ADR-B and ADR-C's exploratory-artifact rule), and the
registration states the consequence in full: **no outcome of PR-004 may be reported as an edge,
as beating the market, or as evidence our rankings beat consensus.** The descriptive evidence
already on file has consensus ahead of the V5 model at every position. A PASS licenses a
labelled, non-binding overlay at the passing position and nothing more.

Not a refusal. An accuracy claim against a stated naive baseline, scope-limited, is defensible
with the data in hand. What would be indefensible is running it and calling it an edge — so the
scope limit is registered where it cannot be relaxed after the number is seen.

## What was produced

| Artifact | Path |
|---|---|
| Registration (ADR-C nine-field confirmatory) | `docs/preregistration/PR-004-bottomup-core-confirmatory.md` |
| Family manifest (m=4, fixes the BH denominator) | `docs/preregistration/families/F-BOTTOMUP-CORE.yaml` |
| Handoff body, **unallocated** | `docs/reviews/PR-004-handoff-body-unallocated-2026-07-29.md` |
| Decision log | `docs/ideas-inbox.md`, 2026-07-29 strategist entry |

## The decision rule, in one place

Per position, six conjunctive criteria: mean dtau_b vs prior-season-points baseline **>= +0.04**;
positive in **>= 10 of 13** embargoed-LOSO folds; season-level bootstrap 95% CI excludes 0 **and**
the bootstrap p survives BH across m=4; points-per-game variant agrees in sign; no ADR-E §8
audit trigger; cross-process determinism from seed 20260729. Projected-points adoption
additionally requires mean dR2 > 0 at >= 10/13 folds.

**STOP: if neither RB nor WR clears, bottom-up is dead as a 2026 product input** — consensus-only
board, no overlay, no further configs before the draft, family closed. Three escape routes are
closed by name in §4 (lowering the floor, promoting a descriptive arm, re-running with different
knobs).

## Four judgement calls, made not asked

1. **Consensus refused as confirmatory baseline** (above).
2. **F-A's ordering inverted.** A0 runs *before* N-1/N-2. Choosing the frozen candidate after
   seeing N-1/N-2 is a `data_seen` selection step; amending PR-004 on it would irreversibly
   demote it to exploratory under ADR-C's one rule with teeth. V5 is frozen unconditionally;
   N-1/N-2 become post-hoc exploratory work that cannot change this verdict.
3. **QB run confirmatorily**, against F-A §2.3's "closed, not run", keeping ADR-E §9's declared
   m=4. Dropping the position we expect to fail would shrink the BH denominator by exactly the
   failing test. Strictly more conservative; costs nothing.
4. **Materiality floor +0.04 dtau_b**, derived from decision-relevance arithmetic (~23 pairwise
   inversions over a ~48-player universe ≈ one improved pick per draft) and deliberately set
   **above WR's exploratory point estimate of +0.036**. A threshold set beneath every estimate
   already seen is not a threshold.

## Calibration prior, applied

Four of five registered prediction sets across sessions 3–4 were materially wrong, every miss
over-crediting a situation story — and V5's advantage over V1 comes precisely from a situation
feature family. §5 registers the pessimistic reading: **modal outcome is STOP**; at most RB
clears; WR is predicted to fail on materiality even if it clears significance.

## The limitation that must survive into every downstream summary

**Selection contamination.** V5 was chosen from eight configurations evaluated on these same
folds (2012–2024). PR-004 does not measure V5 against data unseen by the selection process. It
measures, for the first time, what the effect looks like under a pre-registered rule with an
honest season-level CI, a fixed denominator, the ADR-E embargo, and a threshold that can fail.
It cannot establish out-of-sample skill for the configuration choice. Only the sealed 2025
unseal (n=1, one shot) or P-2026 (prospective) could.

## Not done, and why

- **Handoff thread not opened.** No Bash in this role by design, therefore no allocator access.
  Hand-typing or computing an ID was refused (collisions at threads 043/049/053, ADR-048). The
  body is staged with the exact `python tools/handoffs.py new --from strategist --to backend`
  command; whoever has a shell allocates, pastes, syncs, deletes the staging file.
- **`content_hash` left as `PENDING-FREEZE`.** Cannot compute sha256 without a shell.
  `compute_content_hash` redacts the field before hashing, so backend writing the real value in
  is the designed two-pass freeze; §9 spells out the four steps and makes them a prerequisite to
  running anything.
- **2025 holdout not unsealed and not authorised.** Irreversible, permanently closes the family,
  requires a named human approver in `UNSEAL_LOG.md`. That is an escalation, not an agent call.
- **No measurement of any kind run.** That is the role working as intended.
