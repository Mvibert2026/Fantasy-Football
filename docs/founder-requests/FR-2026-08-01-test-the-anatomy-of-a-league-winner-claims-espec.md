---
ID: FR-2026-07-31-league-winner-anatomy
STATUS: NEW — registered for testing, deliberately not adjudicated
SOURCE: PM session 2026-07-31, founder chat
RAISED: 2026-07-31
PRIORITY: MEDIUM-HIGH — one arm is cheap and converges with an independent finding
NEEDS: ranker (test), researcher (verify the source properly)
---

## Request

The founder shared *"2026 Anatomy of a League Winner"*, Ryan Heath, Fantasy Points
(`https://www.fantasypoints.com/nfl/articles/2026/anatomy-of-a-league-winner`) and asked whether there
is truth in it.

**He then asked explicitly that it be registered for testing rather than answered.** PM had begun
adjudicating it from a fetched summary; that was the wrong move and this file replaces it.

## Status of what is written below

**Everything here is UNVERIFIED and comes from a small-model summary of the page, not the full
article.** No claim in this file has been read at source by anyone on this project. Treat every number
as `[SNIPPET]` until a researcher reaches the original.

## Claims as extracted, to be checked at source first

| Claim | As extracted |
|---|---|
| RB share of league-winners | ~39% of league-winners against 25% of lineup spots — 1.55× expected |
| WR / QB / TE multiples | WR 1.23×; QB and TE ~0.87–0.94× |
| RB value over replacement | ~1.3× that of WR |
| **QB rushing gate** | **"Every single one" of league-winning QBs had ≥55 rush attempts** |
| Window | 2017–2025, nine seasons; a "since 2021" five-season subset for advanced metrics |
| Format | ESPN default — 10-team, **full PPR**, 4 playoff teams |
| "League-winner" definition | Appears on playoff rosters in **≥55% of ESPN leagues** |

## Why the QB arm is worth testing rather than filing

**It converges with an independent finding of our own.** `docs/research/analyst-factor-sweep-2026-07-30.md`
found QB rushing attempts to be the strongest single QB predictor measured anywhere in the sweep —
0.576 to next-season FPG, with the top nine most predictive QB stats all measuring rushing and the
first pure passing metric appearing tenth. Two independent routes to the same signal.

**And it is a functional form this project has never tested.** All ~90 registered tests to date used a
single global linear weight. "≥55 carries or the season does not happen" is a **gate**, the same shape
as the founder's high-carry-threshold question (`FR-2026-07-30-rb-workload-hangover`). If gates work
where weights do not, that is a finding about model shape rather than about quarterbacks.

Batch 3 already tested QB rushing **as a weight** — arm A1, ablation, EARNS-ITS-PLACE at QB. The gate
version is a different test and is not a re-run.

## Things that must be established before any of it is adopted

- **Format.** ESPN default is full PPR; this league is half-PPR with yardage bonuses. RB-versus-WR
  value is format-sensitive.
- **Whether the metric is normalised against losing rosters.** "Appears on ≥55% of playoff rosters"
  can partly measure draft popularity rather than value — a universally-drafted player appears on
  almost every roster of both kinds. The summary says it "integrates acquisition cost," which may
  address this. Unverified.
- **Survivorship.** A league-winner analysis is conditioned on the outcome by construction. This
  project has measured the published literature's survivorship premium at **0.06–0.09 of correlation,
  always flattering the publisher** (`analyst-factor-sweep-2026-07-30.md` §0).
- **This publisher's track record here is mixed and measured.** Heath's first-read target share, at a
  published 0.79, **did not reproduce** — 0.637 under his own survivor filter, 0.607 on our frozen
  universe (`factor-batch-5-results.md`). Fantasy Points also contradicts itself between two articles
  on designed-target value. Not grounds for dismissal; grounds for testing rather than adopting.

## Ledger

Add as rows to `docs/factor-ledger.md` with disposition **untested**, so the campaign denominator
counts them. Do not mark anything dispositioned on the strength of a summary.
