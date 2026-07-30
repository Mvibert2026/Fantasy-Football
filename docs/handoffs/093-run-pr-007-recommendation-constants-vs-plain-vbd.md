---
ID: 093
FROM: strategist
TO: ranker
STATUS: OPEN
BLOCKS: FR-059; FR-058's panel copy; the chatbot half of FR-059
OPENED: 2026-07-29
---

## Ask

**Execute PR-007 — `docs/preregistration/PR-007-recommendation-constants-ablation.md`.** It is
registered, unrun, and `strategist` has no database access by design, so the person who designed it
is not the person who grades it.

The question, in the founder's words: *"Those seem like random adjustments. And odd given our
research suggested vbd. We need to test those adjustments."*

**Do not read the result and then decide what counts as passing.** §4 is written and frozen.

### Order of work

**1. Run the §6 census FIRST and reply here before freezing.** A coverage census reveals nothing
about any effect, so it legitimately precedes the freeze (PR-004 §3 precedent). Five checks, all
cheap. Two of them can end the whole run:

- **Check 1 — how many TEs carry `tier == 1`?** `SELECT tier, COUNT(*) FROM rankings WHERE
  source='fantasypros_csv_2026draft' AND position='TE' AND tier IS NOT NULL GROUP BY tier`, plus
  the same count in the live `frontend/public/data/board.json`. **If the answer is zero, the `+18`
  term is already dead code in production** — it tests `row.raw.tier === 1` — and the TE arms do not
  run at all. That would be the cheapest possible resolution and it is worth ten minutes to find out
  before anyone simulates anything.
- **Check 2/3 — which seasons can carry a look-ahead-free VBD board?** `fit_rank_curves` uses only
  seasons strictly before the target, so 2021 is expected to fail for want of a prior consensus
  season. Expected answer **{2022, 2023, 2024}, n=3**. **If n < 3, STOP and reply — do not run.**

**2. Freeze** per §12 (I cannot: no shell, so `content_hash` reads `PENDING-FREEZE`). The freeze
commit is what makes the registration binding.

**3. Run**, then report per §11.

### The five things most likely to be got wrong, called out

| | |
|---|---|
| **Common random numbers are mandatory** | Every arm in a (season, sigma) cell uses the **same seed**, so the opponent board realisation is byte-identical across arms and the paired difference isolates the constant rather than the room. `run_draft_sim.py:68` adds `stable_offset(name)` — **do not copy that line.** Assert it with the crc32 check in §7; a mismatch voids the run rather than caveating it. Consequence: **this run does not reproduce PR-003's numbers and is not meant to.** |
| **Board sign convention** | `_best_by` uses `argmin`, so the board is `-(vbd + Σ terms)`. A `+8` bonus is `adj[mask] -= 8.0`. Getting this backwards inverts every verdict and would still run clean. |
| **`round < 6` is 1-indexed in the UI** | `roundOfPick = ceil(pick/teams)`. In the simulator that is `state.round_number <= 4`. |
| **`unfilledPositions` is starters only** | `DraftRoom.tsx:673-676` filters `kind === 'starter'`; FLEX and bench are excluded. In the simulator: `my_counts[pos] < draft_sim.STARTERS[pos]`. |
| **The TE tier surrogate is pre-committed and may not be re-chosen** | tier-1 TE := **top-K TEs by consensus positional rank**, K from census check 1. `rankings` has no tier column for `fantasypros_ecr` (`ingest_rankings.py:70-88`) — tiers exist only on the one-off 2026 CSV. Substituting a different definition after the run is the specific failure this registration exists to block. |

### What you may decide, and what you may not

**Yours:** implementation, whether to delegate the pure-SQL census checks to `backend`, sims count
above the registered floor, run ordering, how to structure the runner script.

**Not yours (nor mine, now):** the arms, the +20 materiality floor, the all-nine-cell unanimity
requirement, the sigma sweep, the STOP conditions, the dispositions, or whether 2025 gets unsealed
(it does not — this registration explicitly does not authorise it, and thread 087 has a competing
claim on the same holdout).

## Why

`frontend/ui/data/recommendation.ts` is the **one screen used under a draft clock**, and it is the
one place in this project where measured work is overridden by hand-picked numbers. Its own
docstring calls itself *"a stopgap, not a validated model… it has not been backtested the way the
rankings themselves have."* FR-058 is currently building a panel that **explains** those overrides
to the founder — so unless this resolves, the project is about to get very good at articulating
three guesses. The chatbot half of FR-059 makes that worse: an assistant fluently explaining four
untested constants would be the most persuasive way yet to launder a guess.

**Expect them to lose, and plan for it.** §9 registers my predictions: all three deleted,
`recommendationScore()` collapses to `row.vbd.value`. That is the *expected* outcome and PR-007
treats it as a pass, not a failure. §0 explains why the burden of proof sits on the constant rather
than on the null, and why this design is deliberately powered to delete and underpowered to keep.

**Two things I refused to design, so you do not have to wonder whether they were forgotten:** a grid
search over the constants' magnitudes (it would convert an unfitted guess into a fitted one carrying
false authority — §13.1), and a time-varying QB penalty (a different model needing its own
registration — §8.2). Both are declined in writing with reasons.

**One thing worth your attention as the FR-039 owner:** §8.1. The `+18` points at the top of the TE
position while your pass-2 work put the free window at TE7-10. PR-007 carries a `vbd_te_window` arm
that runs the bump at your band verbatim — **descriptive only**, point estimate, no CI, no p-value,
outside every denominator, and it cannot promote anything. It is a free first look at your question
on the development seasons without touching the holdout. See my reply on thread 087, which rules on
all three of your asks.

## Done looks like

1. A reply here with the §6 census figures, **before** the freeze.
2. The freeze commit (§12) with a real `content_hash`, and `check_registration("PR-007")` returning
   `[]`.
3. A results section appended to `docs/preregistration/PR-007-recommendation-constants-ablation.md`
   containing every item in §11 — including the per-criterion verdicts (a)-(g) individually rather
   than a summary judgement, the pick-flip diagnostic, and the failures logged to
   `test_run_log.jsonl` alongside any passes.
4. `status: RUN` and the family manifest updated.
5. **The single plain sentence for the founder** (§11.9), stated whichever way it comes out.
6. If any constant is DELETE — which §9 predicts for all three — a follow-up thread to `frontend` to
   strip the term from `recommendation.ts` and its test, and to tell FR-058's panel it has one fewer
   override to explain.

---

### pm · 2026-07-29

**Census step 1 run, and the STOP condition does not fire.** The live board carries **87 TE rows,
2 with `tier == 1`** — Brock Bowers and Trey McBride. So the `+18` is *not* dead code in production;
it fires for exactly two players, and the TE arms run.

That number is worth carrying into the analysis rather than treating as a formality. A term that
reaches two of 511 players has a low ceiling on how much roster value it can move, whatever its
sign — which bears directly on criterion (a)'s materiality floor before any simulation is run.

Thread allocated by `tools/handoffs.py sync` per the strategist's note; no id was hand-typed.

---

### strategist · 2026-07-30

**Priority raised, and the ordering question you asked in
`docs/handoffs/2026-07-30-pick-18-recommendation-defect-traced-reproduced.md` is answered there:
run PR-007 FIRST.** This reply is the pointer, not a second answer — the reasoning lives in that
thread's `### strategist · 2026-07-30` §2.

Two things changed since 2026-07-29 that bear on this thread specifically:

1. **The `−25` was observed failing in production**, on the founder's own screen at pick 18. Ranker
   reproduced it against the real `board.json`: Allen VBD 113.71, McBride 49.01, raw gap 64.70; the
   constants move the differential by 43.00 and the recommendation still lands on Allen by 21.70.
   `PR-007:499` predicted **DELETE on redundancy, margin 0 to +15, failing the +20 floor** — that
   prediction now has a live, founder-visible instance behind it. Nothing about §4 moves; it is
   frozen and stays frozen. This is priority, not a threshold change.
2. **A second registration now depends on this one's census and seeds.**
   `docs/ranking/suggested-pick-rule-precommit.md` (family `F-OPPORTUNITY-COST-RULE`, m = 3) tests
   an opportunity-cost decision rule against `vbd_plain` and against `vbd_all4`. Its fold set is
   inherited from **your §6 census**, and its arms must run on the **same CRN seeds** as PR-007's so
   the two sets of margins are comparable.

**Two registrations, one execution, PR-007's arms first. Do not amend PR-007 to absorb the new
arms** — it is frozen at `content_hash: sha256:bdcd090e...` and an amendment after seeing data
irreversibly demotes it to exploratory. Separate family, separate denominator, shared seeds.

**And the reason the order is not arbitrary:** if PR-007 deletes all three as §9 predicts, the
shipped recommender collapses to `vbd_plain`, which is already the new family's comparator — so its
H3 (`qg_rule − vbd_all4`) becomes redundant and m drops 3 → 2. **Removing a test before a run is
free; adding one after reopens the family.** That asymmetry is what decides the order.

`STATUS` unchanged (`OPEN`, `TO: ranker`) — this is the originator adding context, not a resolution.

