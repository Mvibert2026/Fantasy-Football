# Fable mandates G — 2026-07-28

**Same rules as the F set.** Conclusion first. Read the repo freely; run read-only queries and the
existing test suite if useful. **Modify nothing** except your own output document and a session entry
in `docs/status.md`. No code changes, no builds, no git operations beyond reading history.

One mandate per session. Each writes one file under `docs/reviews/`.

## Standing context

Board is consensus-derived at player level; positional revaluation is the only current edge channel.
Three leagues, different scoring and team counts. Draft provisionally 30 August 2026 — 33 days out.
FR-007: every table stake must hold regardless of edge value, because a ranking with a real edge and
one catastrophic omission is worse than consensus — the founder cannot tell which rows are affected.

**The calibration prior.** Four of five registered prediction sets were materially wrong, all
over-crediting situation stories. Vacated opportunity and rookie draft capital are cleanly eliminated.
Treat PM-authored claims as advocacy, including anything in this file.

**Priority rule for the next 33 days: floor defects beat edge work.** If a mandate below turns out to
be edge work in disguise, say so and stop.

---

## G-A — Does the pick recommendation flip inside λ's confidence interval?
`docs/reviews/fable-lambda-sensitivity-2026-07-28.md`

The positional-need term is `N_t(p) = (share_t(p)/share_bar(p))^lambda` with **lambda = 0.352, SE
0.070, n = 160 across 10 clusters**. That is a 95% CI of roughly **[0.21, 0.49]**, and 10 clusters is
thin for cluster-robust inference.

This is the measured parameter the product's differentiator rests on, and nobody has asked the only
question that matters about it.

1. **Does the recommended pick change anywhere inside that CI?** Reconstruct realistic board states —
   early, middle (rounds 4–7, where the founder believes need bites hardest), and late — and check
   whether the top recommendation, or the top three, reorder as lambda moves across [0.21, 0.49]. If
   it does, that is a **floor defect under FR-007**, not a modelling refinement.
2. Where is the flip most likely — which round, which positional configuration? Name the conditions.
3. Is 10 clusters enough for the SE to mean what it appears to mean? Would a wild-cluster bootstrap
   change the interval materially? Recommend the cheapest defensible robustness check.
4. **Is lambda even a single global parameter?** It was fitted on some set of drafts. Positional-run
   dynamics differ with league size, scoring and roster shape. Applying one fitted behavioural
   parameter across a 12-team custom league, a 10-team Yahoo league and an ESPN league may be the
   same construction error as the playoff-weeks constant.
5. If the honest answer is "the CI is wide and we cannot narrow it before the draft," say what the
   product should *display* about its own uncertainty rather than what it should compute.

## G-B — Per-league constant sweep
`docs/reviews/fable-per-league-constants-2026-07-28.md`

Three leagues turned every global constant from a shortcut into a systematic bias. One has already
been caught: `playoff_weeks` is configured `(16, 17)` — exactly the verified Yahoo 10-team default —
while the PM has said 15–17, the modal 12-team custom structure. Both are plausibly right for
different leagues, so the constant is wrong by construction whichever value it holds.

**Find the rest, in the actual code.** This is a sweep, not an essay.

1. Grep for hard-coded numeric and string constants in scoring, replacement level, roster
   construction, the hazard model, bye handling and the export contract. For each, answer: **could a
   commissioner change this?** If yes, it is a per-league field.
2. Rank by expected damage. The PM's prior candidates, to verify rather than trust: the ADP feed
   itself (drafters pick off *their platform's* ranks, so one consensus ADP is a per-platform
   behavioural variable in disguise), lambda, league size and picks-between-turns, bench size, flex
   eligibility, IR slots, reception value, yardage-bonus stacking, INT penalty, waiver system, draft
   date, draft type.
3. For each confirmed offender: is it currently *wrong* for any of the three leagues, or merely
   *fragile*? Wrong-today items are defects; fragile items are debt.
4. Recommend the shape of the fix — per-league field, null default, required input — and the smallest
   change that stops new global constants being added.
5. **What is the blast radius if we ship with these unfixed?** Per league, name the boards or
   recommendations that would be silently wrong.

## G-C — Adversarial audit of the availability model
`docs/reviews/fable-availability-audit-2026-07-28.md`

The hazard model is the product's actual differentiator and the one thing the category does not ship.
It has never been adversarially reviewed. The ranking work has absorbed all the scrutiny.

1. **What does `h_j(X) = w_j(X) / Σ w_j(Y)` assume, and which assumptions are false in a real draft?**
   Independence between picks, stationarity across rounds, exchangeability of drafters, no reaction to
   what just happened. Name which are violated and how badly.
2. Where does its input ADP come from, how stale is it, and is staleness handled? A trailing average
   lags a moving target by construction.
3. **Is the model calibrated, and how would we know?** Calibrated survival-to-pick probability is the
   central claim. What evidence exists that a stated 30% actually happens 30% of the time? If none,
   that is the finding.
4. How does it behave in the tails — the top five picks, and the last rounds — where the sample thins?
5. What happens when the draft goes off-script: a reach, a run, an autopick, a paused clock? Does the
   model degrade gracefully or confidently mislead?
6. **The one experiment worth running on it before 30 August.** One. Chosen for the ratio.

## G-D — Draft-day pre-mortem refresh at T-33
`docs/reviews/fable-premortem-refresh-2026-07-28.md`

`docs/reviews/fable-draft-day-premortem-2026-07-27.md` was written before this week's work landed.
Re-run it against current reality rather than re-reading it.

1. Which named failures are now **closed**, with what evidence? Failure #1 (wrong scoring format) is
   reported fixed — verify that claim rather than accepting it.
2. Which are still **open**, and which have got *worse* since it was written? Three leagues instead of
   one is new scope the original did not contemplate.
3. **What failures does the original miss that are visible now?** The three-league situation, the
   allocator race, an agent fabricating a file rather than halting, an unattended job failing silently
   on a permission prompt and losing a day of unrecoverable data.
4. Re-rank by `probability × cost`, with the honest note that the original's probabilities were PM- and
   Fable-estimated and have not been scored against outcomes.
5. **The T-7 / T-1 / T-2h checklist: what changes?** Produce the amended checklist, not commentary on
   it. It is the artifact that gets printed.

## G-E — What do 614 tests actually protect?
`docs/reviews/fable-test-coverage-audit-2026-07-28.md`

Backend reports 614 passed / 0 failed; frontend 192 passed / 2 failed red-by-design. High counts have
repeatedly coexisted with real defects reaching the founder — every UI defect this project has found
came from a founder screenshot.

1. **Sample the suite. What proportion assert real behaviour versus restate the implementation?** Be
   specific and name examples.
2. Which of this week's actual defects would the suite have caught? The board silently emptying on a
   source swap, the suggester reopening on every pick, the freshness field computed but never
   exported, thread-ID collisions.
3. **What is untested that would be catastrophic on draft day?** Rank it.
4. The two red-by-design frontend failures: are they still legitimately red, or has the reason
   expired? A permanently-red test stops being information.
5. The backend suite takes 533 seconds. What is the smallest fast subset that would catch most
   regressions — the thing an agent can afford to run at every landing check rather than at closeout?

---

## Still unrun from the F set

`docs/fable-mandate-2026-07-28-short.md` — **F-B** (is ADP velocity testable before 30 August),
**F-C** (week-leverage weighting and the playoff-weeks discrepancy), **F-D** (should the handoff
system be rebuilt) and the standing interrupt audit.

A parallel Fable session without repo access has already answered F-B and F-C at a methodological
level; see `claude/fable-2026-07-28-three-reviews.md` in the project. **The repo-grounded versions are
still worth running, and should treat that document as a hypothesis to check rather than a finding to
inherit** — it was written blind to the code.
