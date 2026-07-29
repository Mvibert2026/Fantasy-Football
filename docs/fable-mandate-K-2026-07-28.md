# Fable mandates K — 2026-07-28

Lettered **K** deliberately: Fable's own overfitting series already uses H1–H4, and this project has
lost a day to identifier collisions twice this week.

**Rules as before.** Conclusion first. Read the repo freely; run read-only queries and existing tests.
**Modify nothing** except your own output document and a session entry in `docs/status.md`. One
mandate per session, one file each under `docs/reviews/`.

**Read `claude/session-record-2026-07-27-28.md` first.** It carries the corrections, including several
that falsify premises in earlier Fable output.

---

## K-A — Should λ drive the recommendation, or should the claim be dropped?
`docs/reviews/fable-lambda-decision-2026-07-28.md`

**The PM is deliberately not framing this mandate, because the PM authored the claim now in question
and has already propagated it into the charter, the explainer, the dashboard and every summary given
to the founder this week. Treat any PM framing you encounter as advocacy for option 1.**

The facts, from your own G-A run, and nothing more:

- The shipped RECOMMENDED card (`frontend/ui/data/recommendation.ts:16`) and the shipped survival
  number (`frontend/ui/data/liveAvailability.ts:30`) are **λ-free**.
- They run on five hard-coded constants — **+8 / +18 / −25 and −0.62 / −1.25** — never fitted to
  anything.
- λ = 0.352 (CI [0.21, 0.49], one draft, one league, need confounded with round) steers only
  sim-strategy comparisons and an unwired Mock Lab path.
- Wiring λ in would introduce top-1 flips in ~2.5% of decision states inside the CI, concentrated in
  rounds 4–7. The founder's own slot-3 states do not flip.
- Availability is calibrated on **0 of ~30 drafts**.

Answer, in this order:

1. **Where did the five constants come from?** Git history, comments, ADRs. Were they reasoned,
   inherited, or invented? If nobody can say, that is the finding.
2. **Is the heuristic actually worse?** Compare the two paths on the 160 replayed 2025 states. A
   measured parameter with a wide CI from a single league is not automatically superior to a
   hand-tuned constant that a knowledgeable person chose. Say which wins and on what evidence.
3. **Is this a false binary?** Consider: ship the heuristic, display λ's disagreement as a
   second opinion, and let the divergence itself become the calibration signal once mocks start.
4. **What would honest product copy say under each option?** Write the actual sentence. The current
   description is false and must be replaced regardless of which path is chosen.
5. **What is the cost of doing nothing before 30 August?** The app behaves consistently today. Is this
   a floor defect under FR-007, or a documentation defect wearing a floor defect's clothes?

## K-B — Does the remaining path actually fit before 30 August?
`docs/reviews/fable-schedule-feasibility-2026-07-28.md`

Nobody has checked. It is 28 July. Roughly 13 of your 40 work orders are closed. Two hard stops exist
— the 22 August confirmatory-run deadline and the 20-config LOSO cap with 8 spent — and the
critical-path item for the first (H3, prereg gate wiring, ~1 backend session) is **NOT STARTED**.

1. Build the actual dependency graph of what remains. What is genuinely serialised, what can run in
   parallel, and where is the true critical path?
2. **Mock drafts are now understood to be the only calibration source for availability, and the
   founder is the only detector of UI defects.** Both mean founder wall-clock, not agent time. How
   much of his time does the remaining plan actually require, and does it fit alongside a job and a
   life?
3. Board freeze on 22 August was your recommendation. Working backwards from it, what must be true on
   15 August and on 8 August?
4. **What is the realistic failure mode of this schedule?** Not the optimistic path — the one where
   something slips. Which slip is most likely and what does it cascade into?
5. If the plan does not fit, say so plainly and say what gets cut. Do not compress estimates to make
   it fit.

## K-C — Quantify the only honest consensus-relative claim
`docs/reviews/fable-scoring-translation-2026-07-28.md`

Your F-A run concluded that the strongest claim available before the season is not a modelling claim
at all: **our board prices Westwood's exact scoring — half-PPR with stacking yardage bonuses,
10 teams, measured replacement levels — and format-generic consensus ADP does not.** Arithmetic, not
modelling. Nobody has quantified it.

1. Re-score recent seasons under Westwood's actual rules and count **how many players inside the
   draftable range move by a full round or more** versus generic half-PPR consensus. Report the
   number, the players, and the direction.
2. **Which positions does the stacking bonus structure systematically advantage?** Bonuses that stack
   fatten the right tail; say whose tail.
3. Is the effect large enough to be worth a claim, or is it a handful of players nobody was deciding
   between anyway? **Be willing to conclude it is small.**
4. Does the same analysis produce anything for the Yahoo league, which runs default scoring — or is
   that board genuinely indistinguishable from consensus, and should the product say so?
5. **How should this be surfaced?** If a player moves two rounds because of scoring, the founder should
   see *why*, not just a different number. Specify the display.

## K-D — The kill list
`docs/reviews/fable-kill-list-2026-07-28.md`

**The bias in this project is additive. Nothing has ever been removed.** You observed it about the
process checks; it is equally true of features, threads, docs and model ambitions. Thirty-two days
out, subtraction is the cheapest available speed.

1. **What should we stop building?** Name specific items from the 40 work orders, the founder-request
   list, the ideas inbox and the open threads. Include the ones the founder is enthusiastic about if
   they do not earn their place — say so directly, he has asked to be told when he is wrong.
2. **What should we delete outright?** Code, tests, docs, threads. The dead byte-identical Python tree
   under `frontend/src/` was one instance; there will be others. A permanently-red test and a
   never-read document both cost attention.
3. **What should be deliberately shipped broken or absent, with an honest null instead?** The product's
   null vocabulary is unusually good (`—`, `<1%`, `0%`, `not yet`, `·`). Where is an honest "not yet"
   strictly better than a rushed implementation?
4. **What process should be cut?** Apply your own cost test to the two-tier closeout, the mailbox
   checks, the review-item log, the defect register and the interrupt count. Any that has not yet
   caught something should be named.
5. For each kill, state what would have to become true to revive it. **A kill with a revival condition
   is a decision; a kill without one is an argument waiting to be relitigated.**

---

## Already run — do not repeat

**F-A** (bottom-up next tests) and **G-A** (λ sensitivity), both repo-grounded, in `docs/reviews/`.

**Blind runs without repo access**, in the project docs: F-B (ADP velocity testability), F-C
(week-leverage and playoff weeks), and the interrupt audit. **Treat those as hypotheses, not
findings** — F-C's central premise, that Westwood is a 12-team custom league, has already been
falsified by the founder. It is a 10-team Yahoo league.

## Still awaiting a run

**F-B, F-C, F-D** repo-grounded (`docs/fable-mandate-2026-07-28-short.md`) · **G-B** per-league
constant sweep, **G-C** availability-model audit, **G-D** pre-mortem refresh at T-33, **G-E**
test-coverage audit (`docs/fable-mandate-G-2026-07-28.md`).

**G-B is now urgent** — G-A confirmed its first instances: `TARGET`/`EPS`/`SHARE_BAR`/`POSITIONS`
hard-coded to primary-league-2025, under which League 2's kicker slot is unrepresentable.
