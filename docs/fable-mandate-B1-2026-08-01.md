# Fable mandate B1 — build the independent bottom-up ranking

**This is a build mandate, not a review mandate.** It is the first one this project has issued to
Fable. Your M2 review (`docs/fable/M2-findings.md`) is the input; this is the response to it.

Written 2026-08-01. Founder's authorisation, verbatim:

> "Go ahead and launch fable when ready. Scope is independent bottoms up rankings. If it needs more
> than one more version that's ok. Don't unlock 2025. Just start iterating."

and, setting the bar, earlier the same day:

> "Create the best draft rankings we can that could be easily applied to different league scorings by
> updating points. Our bar is not consensus. It's how good can our rankings be. When we think they
> are as good as they'll get (any and all components in it that need to be), then we can test vs the
> other three models like consensus, consensus adjusted and ADP etc."

---

## 1. Scope — narrow on purpose

**Bottom-up rankings only.** Availability (draft) and the recommender are explicitly **out of scope**
for this mandate, despite being M2-2 and M2-3 of your review. They have their own paths. Do not
spend budget on them.

**You are building, not grading.** Produce a working, better ranking model. Multiple versions are
expected and authorised — v2, v3, v4. "If it needs more than one more version that's ok."

---

## 2. The bar — read `CLAUDE.md` §2a, it is new and it is because of your review

**ADR-069, written today, changed the standing law in response to your F1–F7 frame ruling.** Three
things bind:

1. **Consensus is not an input.** Build from player-level projections. The shipped board — consensus
   re-scored, within-position identical to consensus — is what you are *replacing*, not improving.
2. **Consensus is not the development signal.** Steer by **absolute quality against realised
   outcomes**. §6.5's four-baseline comparison is now a **release gate run once at the end**, not a
   per-arm metric. An arm that improves absolute quality is an improvement even if the gap to
   consensus does not move. Do not re-introduce consensus-delta as a steering metric — that is the
   exact failure you diagnosed.
3. **Projections output stat lines, not fantasy points.** Volume, efficiency, games. Points are
   derived by applying a league scoring config; ranks by applying a roster shape to get replacement
   levels. **Changing league scoring must re-score and re-rank without re-fitting.**

**(1) and (3) are one requirement.** A board whose within-position order comes from consensus cannot
respond to league scoring at all, because consensus is built for a generic 12-team full-PPR room.
This league's half-PPR, stacking yardage bonuses (§7) and 10-team replacement levels currently cannot
reach the ordering by any route. Portability is achievable only *through* independence.

---

## 3. Priority order

**A. Stat-line projection architecture.** The structural piece everything else sits on, and the thing
that makes the model portable. Get this right before fitting anything interesting — retrofitting it
later means refitting everything.

**B. The player-availability model — projected games.** *Your own M2-1 finding says this is the whole
deficit.* Substituting realised games at fixed per-game rates flipped every losing cell to a win;
excess rank error concentrates 86–131% in players who missed ≥4 weeks; v1's games projection has
near-zero ordering skill (r 0.12–0.24) and is worse than naive persistence.

This is also where consensus's real advantage lives — what it knows that we do not is *who is going
to play*. So **independence stands or falls here.** Build it from injury history, age, position,
workload, and pre-Week-1 status, with the resolved-vs-ongoing distinction you identified (the
Burrow/Hill class) as the first thing to get right.

**Do not conflate this with *draft* availability** despite the shared word. Different model,
different question, out of scope.

**C. Rates.** Lowest priority — you measured them already at or better than market parity. Do not
spend the budget here.

---

## 4. Hard constraints

**The sealed 2025 holdout does not open.** The founder restated it today unprompted: *"Don't unlock
2025."* `CLAUDE.md` §6.3. No agent opens it on its own authority, including you, including on a
result you consider decisive. If you conclude a spend is warranted, write the recommendation into
your log and keep building. Every access is logged in
`docs/preregistration/holdout_access_log.jsonl` — you should have no reason to append to it.

**The guardrails still bind, and they are the only overfitting protection you have left.** Removing
consensus from the development loop did not increase overfitting risk — consensus never provided that
protection — but it does mean §6.3's machinery is now load-bearing on its own:

- **Register the threshold before you measure.** Every arm, every version.
- **Register into the campaign manifest** (`docs/ranking/factor-campaign-manifest/`). The
  multiple-comparisons `M` is computed against the *campaign*, never a batch. You ruled on this
  yourself in M2-4; do not now become the exception.
- **Look-ahead:** inputs for season N use data through end of N−1 and preseason N only. Use the
  harness's `feature_gate` / `outcome_gate`; do not hand-roll a cutoff.
- **Survivorship:** the player universe for season N is defined *before* season N.
- **Seasons through 2024 only.**

**You have standing authority to block, and you are now also the builder.** That is a real conflict
and the project knows it: `strategist` (Opus, deliberately no database access) is your adversary and
reviews before anything ships. Nothing you build merges to the board on your own sign-off.

---

## 5. Budget — this is why "iterate" is in the instruction

**The shared weekly pool is at 91% and resets Monday 11:00.** Your own pool has room; the shared one
binds. You will very likely be cut off mid-build.

**Therefore: build in resumable increments and commit constantly.** Five agents died on session
limits last week and everything uncommitted went with them.

**Every commit should leave the tree in a state a successor can resume from.** At each update, write
down the *next* step explicitly — not "continue", but what to fit, against what, with what threshold
registered. Assume the successor is you after a reset, with none of this context.

**A half-built v2 that is committed and resumable beats a finished v2 that died in a context window.**

---

## 6. Recording — `docs/fable/v2-build-log.md`

The founder will not have tokens to ask how it is going. The file is the channel. Same protocol as
M2:

```
## WHERE THIS STANDS     <- rewrite every update; current state only, no history
## NEXT STEP             <- the specific resumable instruction described in §5
## TOKENS USED           <- running figure
---
## LOG                   <- append-only below here; never rewrite an earlier entry
```

Report token usage in the file, not only at the end. He asked for it explicitly.

---

## 7. Environment

**Read `docs/environment.md` before your first shell call.** In particular §4: your worktree does
**not** inherit `data/nfl.db` — sqlite will silently create an empty stub and ~21 tests will fail
looking exactly like a regression you caused. Copy (never hardlink) the real 855 MB DB from the main
checkout first. §4b explains the disk cost; do not delete the DB to free space.

Work in your assigned worktree on branch `claude/pm-agent-setup-gobxa0`. Another agent (`backend`) is
running PR-007 in the main checkout — that is why you are isolated. Do not touch
`docs/ranking/pr-007-*`, `src/run_pr007.py`, or the recommender.

---

## 8. What success looks like

A committed, reproducible ranking model that:

- takes stat-line projections to points through a **swappable league scoring config**, demonstrated
  by producing a different order under different scoring without refitting;
- contains **no consensus input** anywhere in its ordering path;
- has a projected-games component that beats naive persistence on ordering skill — the bar v1 failed;
- is measured on **absolute quality against realised outcomes** on seasons through 2024, with every
  threshold registered before measurement;
- carries an honest statement of what it does *not* yet do.

**Not required and not wanted:** a consensus comparison. That is the release gate, run once, later,
by someone other than you.
