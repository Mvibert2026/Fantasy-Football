---
ID: FR-057
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Availability must recompute for any draft slot — browser preferred, all-slots export as the floor

Founder's own words:

> "the browser needs to find a way to recompute them, python needs to run against all slots as well.
> I'd prefer the browser can calculate, but we need good data too"

And, framing the whole thing:

> "remember we are becoming a research shop"

## Why it matters

The draft-slot selector (FR-034) shipped and changes the pick sequence everywhere — board, round
grid, Predictions, draft room. **Availability is the one thing it cannot move.**

`data/export/availability.json` is keyed by the founder's actual pick numbers — `3, 18, 23, 38, 43,
58` — which is one slot's snake sequence. Change to slot 5 and the picks become `5, 16, 25, 36, 45,
56`; **none of those keys exist**, so the numbers go absent rather than wrong. The probabilities come
from a Monte Carlo simulation run in Python against a single slot.

**This is the difference between a selector that changes labels and one that changes answers**, and
availability is the product's signature claim.

## Initial read

Not the founder's own words — PM's read. **He asked for both, and he is right to: they are not
alternatives.**

**1. Export all slots (the floor).** Run the existing simulation for every slot, ship the lot. The
per-player payload is three sigma readings per pick; covering ten slots instead of one is roughly a
tenfold increase on that block, and worth measuring before assuming it is fine. Simple, uses code
that exists, works offline, and unblocks the selector immediately.

**2. Recompute in the browser (the preference, and the better answer).** The export already carries
**`client_simulation_parameters`** — `ranking_sources`, `mechanical_need_targets` per position, the
whole set-up for running the simulation client-side. **Someone built the inputs for exactly this and
nothing consumes them.** Fourth piece of already-built capability found today (see FR-043).

Client-side is strictly more capable: it covers any slot, any team count, any roster shape — so it
also serves FR-040's custom leagues and the generic track — and it can respond to picks actually
made rather than only to a pre-draft simulation. **That is why it is the preference, and it is a real
build, not a port.**

**Do 1 first and 2 properly.** Shipping only 1 leaves the same wall at the next league shape;
waiting for 2 leaves the selector half-working through the draft.

## Do not skip the part that makes it research

The founder's other line — *"we are becoming a research shop"* — applies directly here, and it is the
easiest thing to lose while building two implementations of one model.

- **Two implementations must agree.** A Python simulation and a JavaScript one that drift apart give
  different survival numbers on the same screen depending on how they were reached. **Cross-check
  them against each other as a test**, with a stated tolerance, or the second implementation is a
  liability rather than a feature.
- **The simulation's sigma is still an unfitted guess** (`src/draft_sim.py:17-27`), and that file's
  claim that it *cannot* be fitted is stale — this project now holds daily FFC ADP, 160 real picks
  from 2025, and as of today a complete 150-pick draft (`data/mock-drafts/founder-mock-2026-07-29.json`).
  Making it recompute faster does not make it right. **Fitting sigma is the research; re-hosting the
  computation is the engineering.** FR-047 already routes the fitting question to `strategist`.
- Whatever ships must state which assumption produced the number, the same way Predictions does.

---

## Paused 2026-07-30, founder's call

> "Maybe pause the availability work for a minute to conserve tokens to prioritize the other work."

**Part 1 (export every slot) is stopped mid-sweep.** The simulation had been running for several
hours on 3,000 simulated drafts per slot and had not finished. It is killed, not merely abandoned —
it was also contending for CPU with the frontend test suites and is the most likely cause of the
intermittent vitest timeouts seen tonight.

**What survives:** the agent's committed work on branch `worktree-agent-af64727a6079cca5e`, including
ADR-061 and the session narrative. Nothing is lost; the sweep simply has no results.

**The pause is itself a finding, and it argues for part 2.** The founder's stated preference was
always browser-side recomputation, with the all-slots export as a floor. **That floor turns out to be
expensive enough to be a poor thing to depend on** — if a full sweep takes hours, it has to re-run
every time the board changes, and the board changes often. Client-side computation costs once and
then covers any slot, any team count, any roster shape.

**When this resumes, reconsider the order.** Doing part 2 first may be cheaper overall than finishing
part 1, which is the opposite of what was originally specified.

