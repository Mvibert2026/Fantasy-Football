# Addendum to mandate M-1 — bottom-up rankings

**Written 2026-07-29, after M-1 itself.** The founder has confirmed bottom-up rankings are where he
wants Fable's effort spent. M-1 was written earlier the same day and several of its premises moved
before it ran. **Read this before M-1's questions; where the two disagree, this is newer.**

---

## What changed today

**1. The confirmatory experiment is now registered — twice — and has not been run.**
`docs/preregistration/PR-004-bottomup-core-confirmatory.md` (box-score features, deep sample) and
`PR-005-bottomup-usage-confirmatory.md` (V5 usage features, n=13), with separately fixed family
denominators so the winning arm cannot be chosen after the fact. Thread 083.

**The registered prediction across both is STOP.** PR-004 predicted to fail at all four positions;
PR-005's RB is the only live candidate. **Do not treat "it hasn't run" as "it might work."** The
person who wrote the protocol expects it to fail.

**2. The deep sample tests the weak model — this is the finding that should shape your answer.**
Targets are missing 2003–2008 (`experiments/bottomup/data.py:60` — air yards real from 2009 only).
So the usage features producing the model's entire measured edge **cannot be built across the deep
record**. Over 23 box-score folds the deep model is already at rough parity with prior-season rank:
**RB +0.023, WR +0.010**.

The founder's instinct that "25 years of data" rescues this is half right and half wrong, and the
half that is wrong matters: **25 years buys a powerful test of the weak model, not a rescue for the
strong one.** M-1 question 1 asks for the ceiling — answer it against that constraint, not against
the full record.

**3. Consensus history is five seasons, one sealed. Four usable.** The sign-test floor at n=4 is
p=0.125 — unreachable. **Any "beats consensus" claim is descriptive-only and cannot be earned**, and
descriptive evidence already on file has consensus ahead at every position.

**4. Historical market ADP is shallower than hoped and is the wrong shape.** FFC archives are
**12-team only** and the site silently serves the 12-team page for a 10-team request. Clean seasons
after a look-ahead gate: **non-PPR 13, half-PPR 7 (2018+)**. Westwood is half-PPR **10-team** — no
archived season matches it. A perfect 7-of-7 half-PPR sweep still fails multiple-comparisons
correction.

**5. A live methodology defect was found today at a different position, and it may generalise.**
The board's quarterback slope collapsed monotonically 2021→2025 (−67, −73, −59, −45, **−4**), while
`fit_rank_curves()` pools all seasons **flat**. The shipped premium is an average over a regime that
was disappearing. `CLAUDE.md` §6.4 warned about exactly this and the recency weighting it asks for
was never built. ADR-057.

**This is the question worth pressing:** if flat pooling is averaging away a regime change at
quarterback, **what is it doing to the bottom-up features at every other position?** Nobody has
checked. It was caught only because the founder thought a number looked wrong.

A second defect is pinned: the log-linear estimator is misspecified asymmetrically across positions
(RB/WR concave in log-rank at 2–2.6×, QB not at 0.9×). Both are deliberately unfixed, awaiting this
gate.

## What the founder has decided since M-1

- **ADP is not consensus** — no baseline swap to buy depth. Depth bought by measuring a different
  quantity is not depth.
- **He wants consensus as an *adjustment*, not a rival**, and eventually a head-to-head. **This
  conflicts with `CLAUDE.md` §4** (ranking sources never blended, so the independent view stays
  visible rather than silently converging on the market). Measuring a blend is registered; shipping
  one needs a spec amendment. **Say plainly whether you think that rule should hold.**

## What would be most useful from you

M-1's own questions stand. Weight them this way:

1. **Question 1 — the ceiling.** Now answerable more sharply, because the constraint is named: deep
   sample, weak features; strong features, 13 seasons. **Is there a version of this worth building at
   all**, or is the honest answer a consensus-derived board with an explicit disagreement flag?
2. **Question 3 — what data we do not have.** Still the most actionable section, and now sharper:
   collection that must start now to be usable later.
3. **The flat-pooling question above.** Not in M-1, and possibly more consequential than anything in
   it.
4. **Attack the registrations themselves.** They are written but unfrozen and unrun — the cheapest
   moment to find a flaw is before the first model call, not after.

**Apply the calibration prior to the registered STOP prediction too.** Four of five registered
prediction sets here were wrong. A confident prediction of failure is still a confident prediction.
