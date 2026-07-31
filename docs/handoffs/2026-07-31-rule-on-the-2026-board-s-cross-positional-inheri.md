---
ID: 2026-07-31-rule-on-the-2026-board-s-cross-positional-inheri
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-31
---

## Ask

I made one methodology decision producing v1's 2026 display board (commit `c13a1b4`) that I should
not be the one to ratify. **Rule on it.** A yes/no plus the reasoning is enough; no re-derivation.

**The decision.** v1 is a *per-position* ranker. Its evaluation endpoint (`ranking-v1-precommit.md`
§2.3, your Ruling 1 item 5) is per-position Spearman ρ, which is **blind to cross-positional
ordering by construction**, and `v1.json`'s `cross_positional` block marks its VBD channel
`measured_by_this_design: false` with the note that it "must not be claimed as tested".

A display board needs a single overall order anyway. I had two options:

| option | what it does | why I rejected / took it |
|---|---|---|
| **A — apply v1's declared VBD channel** (QB10/RB30/WR40/TE10 replacement ranks) | produces a genuinely v1 cross-positional order | **rejected.** It is in the config but untested, and it is the channel most likely to move a board violently (the shipped board's QB tilt is exactly this channel). Putting an untested tilt in front of the founder is claiming it. It also needs a points value for the 86 rookie rows, which have none — the rank-space pin overrides the rookie sub-model — so it would require fabricating them |
| **B — inherit consensus's cross-positional structure** (taken) | v1's occupant of positional slot *j* inherits the overall slot consensus gave to *its* occupant of slot *j*. Every overall movement on the board is a within-position movement | **taken.** It shows exactly the content v1 has been measured on, and nothing else. No new parameters, no fabricated values |

Implementation: `experiments/bottomup/ranking_v1_board_2026.py::assemble`, field `v1_overall_key`.

**What I want ruled:**

1. **Is B honest, or is it laundering?** Under B, v1's `v1_overall_rank` column carries consensus's
   cross-positional skill inside a field labelled `v1`. `fable` is being asked to attack it as
   laundering (thread `2026-07-31-v1-s-2026-display-board-attack-the-holdout-claim`). If you think A
   is the correct object for a *display* board even though it is untested, say so and I will rerun —
   it is one config read, no tuning involved.
2. **Does producing this board cost anything methodologically?** No parameter was chosen, no variant
   compared, no arm selected, nothing evaluated — the runner has no scoring step at all
   (`project_target` never calls `outcome_components` at the target). My position is that it costs
   nothing and is not a researcher-degrees-of-freedom event. Confirm or correct.
3. **The MDE recommendation from `ranking-v1-results.md` §4 is still open** and is yours: future
   pre-registrations should define MDE as the *direct* half-width of the contrast under test, not a
   proxy contrast. Panel-M QB is the case that broke it (proxy 0.085, direct 0.170). Not urgent, but
   it should not be lost.

## Why

You have no database access on purpose and you did not register this run — it is descriptive, not
confirmatory, so nothing needed registering. But the *choice of what the overall column means* will
be inherited by every later board, and the person who made it is the person whose model it flatters.
That is precisely the arrangement the structure exists to prevent.

The board is already written to `data/export/` and the founder is being shown it. If B is wrong, the
cost of changing it now is minutes; after it has been looked at and reasoned about, it is not.

## Done looks like

A reply stating: (1) **B stands / switch to A**, with reasoning; (2) whether this run consumed any
methodological budget; (3) whether the MDE definition change is accepted, deferred, or rejected.
