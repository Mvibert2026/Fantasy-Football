---
ID: FR-2026-08-01-turn-the-keys-over-to-fable-to-build-the-next-bo
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Turn the keys over to Fable to build the next bottom-up ranking model, with cheaper agents running the tests

Founder's own words, chat 2026-08-01:

> "Should we send fable out to create our next bottoms up rankings model and have cheaper agents
> test it? We have most of the data and did a lot of the leg work. Can we turn the keys over to
> fable to make us a bottoms up rankings the best it can? Free rein to try and test whatever it
> wants?"

## Why it matters

Bottom-up rankings is the **first** of the founder's three "must be true" questions and the one he
has said most directly he wants moved: *"We need our bottoms up ranking to be better."* Ranking v1
currently loses to expert consensus at QB (-0.138), RB (-0.093) and WR (-0.065), all
BH-significant.

This request also proposes a change to how the project is organised, not just what it works on --
so it needs an ADR-grade answer, not just a dispatch.

## Initial read

**PM's recommendation to the founder was yes, with one structural condition.**

**The condition: Fable is the gate.** `CLAUDE.md` §8 gives it standing authority to block, and the
project's own rule -- the one that makes `verifier` and `operator` read-only -- is that an agent
does not review its own work. If Fable builds ranking v2, the most important artifact in the
product is built by the single agent nobody checks.

**Proposed fix, cheap to implement:** `strategist` becomes the adversary for Fable's build.
Strategist is Opus/high effort and **deliberately has no database access**, which is precisely the
property wanted in a reviewer of a model that was fit to the database. Division:

| Role | Job |
|---|---|
| `fable` | Designs and builds v2. Free rein on what to try |
| `strategist` | Adversary -- methodology, pre-registration, grading discipline |
| `backend` / `ranker` | Run the tests (Sonnet) |
| `verifier` | Checks the finished branch against the dispatch (Sonnet, read-only) |

**The founder's instinct about cheap agents running the tests is correct** and matches `CLAUDE.md`
§9 routing: Opus for model design and statistical methodology, Sonnet for implementation and test
execution.

**On "free rein":** PM endorsed free rein on *what to try* without reservation, and held the line
on *how it grades*. ~200-300 fantasy-relevant players per season, heavily autocorrelated across
years, against 30+ candidate factors is the textbook overfitting setup (§6.3). Thresholds
registered before measurement and the campaign-level `M` continuing to count are the only reason a
win would carry information.

**Evidence Fable will hold that line unsupervised, which is part of why PM recommended handing it
the keys:** during M2 it built a candidate v2 (`v2-flatgames`), pre-registered the adoption rule
*before* computing it, and then **rejected its own model** when the result came back 1 WIN / 2
HARM. Unprompted, and against its own interest in having produced something.

**Sequencing and budget.** At the time of the request the shared weekly pool was 88% consumed
(Fable's own pool 17%, but it draws on both, so the shared pool binds); reset Monday 11:00. There
is no room for a real build run before then. Plan communicated to the founder: write the builder
mandate now while it is cheap, dispatch Fable Monday on a fresh pool so it can build rather than
be cut off mid-fit.

**The #1 item for that mandate regardless of what else Fable chooses:** the projected-games
repair -- distinguishing *resolved* absences from *ongoing* ones using pre-Week-1 status (the
Burrow/Hill defect class). Fable's M2-1 located v1's entire deficit in that one channel:
substituting realised games at fixed per-game rates flips every losing cell to a win. That figure
is an **upper bound, not a target** -- it borrows outcome information -- but it establishes the
deficit is one channel rather than diffuse.

**Open decision for the founder:** whether this arrangement becomes standing (an ADR changing
Fable's role from reviewer-only to builder-with-an-adversary) or is a one-off for ranking v2.
