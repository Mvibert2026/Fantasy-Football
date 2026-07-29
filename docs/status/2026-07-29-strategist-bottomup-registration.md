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

---

# REVISION, same day, before freeze — the founder challenged the premise and was right

PR-004 landed as **thread 083**. The founder then made two corrections, both accepted, and a
third request. The registration was **revised in place** — legitimate because `content_hash` was
never frozen and no data was seen, so there is nothing to amend and no ADR-C demotion is
triggered. Recording it as an `amendments:` entry would have misrepresented a never-frozen file
as a peeked-at one.

## What he said, and what it changed

1. **"Market ADP is not consensus rankings — people use consensus rankings, not ADP."**
   Accepted without qualification. No baseline swap to ADP, not even to buy FFC's deeper
   history. **Depth bought by measuring a different quantity is not depth.**
2. **"We have 25 years of data to build our bottom-up rankings from, independent of
   consensus."** Structurally correct and it exposes a real error in my first draft: **I let the
   weak question's n cap the strong one.** Bottom-up needs player stats to build and actual
   finishes to score; both go back decades. Consensus history is needed for exactly one
   question — did we beat the experts.
3. **"Then we test our bottom up r squared against consensus and consensus adjusted for what we
   do have for now."** Folded in as PR-004 §11, descriptive only.

## The finding the revision surfaced, which neither of us had

`experiments/bottomup/data.py:60`:

```
TARGET_RELIABLE = lambda s: (1999 <= s <= 2002) or (s >= 2009)   # air yards real 2009+ only
```

**Targets are missing 2003–2008.** The usage features that produce the model's entire measured
edge cannot be built across the deep record. So:

> **The deep sample buys power. The deep model is the weak one.** 25 years of stats does not
> rescue the strong model; it gives a powerful test of the weak one.

Hence two registrations rather than one, with separately fixed denominators so the winning arm
cannot be chosen after the fact:

| | PR-004 `F-BOTTOMUP-CORE` m=4 | PR-005 `F-BOTTOMUP-USAGE` m=4 |
|---|---|---|
| Model | box-score long arm | V5, the shipping candidate |
| Folds | measured by census, expected ~2000–2024 | 2012–2024, n=13 |
| Trade | power, weak model | strong model, short sample |

BH within each family across its own m=4 (ADR-E §10). Across-family FWER is not controlled and
the registration says so; the compensating discipline is that STOP requires **both** to fail.

## Usable span: measured, not asserted

I have no database access and refused to assert a number. PR-004 §3 specifies the census
precisely (per-season coverage of every field `src/scoring.py`'s `LEAGUE` consumes, with
two-point conversions and return TDs checked explicitly as the likely binding fields) and
pre-commits the fold set as a formula, `FOLDS = { s : S_min + L ≤ s ≤ 2024, s ≠ 2025 }`.

**Prediction on the record: n≈25, folds ~2000–2024.** `run.py:10`'s current 2002 start is a
*walk-forward* warm-up artifact ("needs >=2 training pairs"); embargoed LOSO has no warm-up
cost, so the switch should recover the folds walk-forward spent. If so the founder's "25 years"
is close to exactly right and the current 23 was a fold-scheme artifact, not a data limit.
Pre-committed: **if n < 15, STOP without running.** A coverage census reveals nothing about any
effect, so it may legitimately precede the freeze.

## Two instructions I declined, with reasons

- **Recomputing the +0.04 materiality floor against the real n.** Power and materiality are
  different quantities. n governs detectability; it says nothing about how large an effect must
  be to matter. The floor is decision-relevance arithmetic (~23 pairwise inversions over a
  48-player universe ≈ one improved pick per draft), identical at n=13 and n=25. Lowering it
  because the sample deepened is lowering the bar for the same benefit. **What did change is the
  meaning of the ≥75% fold rule**, now tabulated: sign p≈0.092 at n=13 (weaker than α=0.05),
  ≈0.007 at n=25 (stricter). ADR-E's 75% kept unchanged; the stringency is now visible instead
  of implicit.
- **Reporting a positional-tier heuristic as CLAUDE.md §6.5's third baseline.** Subtracting
  replacement level is a monotone transform *within position*, and tau-b is invariant under
  monotone transforms — its tau equals B1's by construction. It would be reporting B1 twice.
  B2 is instead a three-season equal-weight average, genuinely distinct, and is criterion (h).

## The three-way comparison, handled rather than glossed

- **R² is his language and it is answered in his language**, not silently swapped. Where it is
  defensible: nested comparison, variance in actual points, single position. Where it is not:
  season-points R² is already **negative** at QB (−0.13) and TE (−0.85), so an R²-only reading
  calls the model useless at TE while tau says its ordering improves. Both are printed side by
  side at every position.
- **Non-independence handled by construction.** The blend *contains* consensus, so in-sample
  `R²(consensus+bottom-up) ≥ R²(consensus)` is a mechanical identity — three numbers side by
  side would guarantee the blend "wins" and mean nothing. Registered instead as **one nested
  question per position**: out-of-sample **ΔR²_oos**, weights fit on the other three seasons and
  rotated, which can be negative. Never a three-way leaderboard. Registered asymmetry: at n=4 a
  strongly negative value is informative, a positive one says almost nothing.

## Escalations, not resolved here

- **`CLAUDE.md` §4 says "Ranking sources stay separate, never blended."** The founder's
  preferred product shape is a blend. Measuring one descriptively is not shipping one, and §11
  only measures — but **shipping it requires a §4 amendment, which is his decision.** Middle
  path put on the record: consensus adjusts display and confidence (labelled overlay,
  disagreement flags) rather than being averaged into a score.
- **Successor question PR-006** (consensus as adjustment rather than rival) recorded as future
  work with its own registration, explicitly not folded into PR-004/005, n-limited to January
  2027 at the earliest.

## Kept unchanged

The decision rule committed in advance; the STOP condition with its three exits closed by name;
the calibration prior applied against my own registered predictions (**modal outcome across
both files is STOP**); the selection-contamination caveat that must survive into every
downstream summary; and the refusal to authorise a 2025 unseal.
