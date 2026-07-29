# 2026-07-29 — `ranker` — bottom-up pass 2: where the TE mispricing can be spent (FR-039)

**Scope.** FR-039, the founder's narrowing of the pass-1 TE finding into a draft-strategy claim:
*if we aren't taking TE or QB early, find an underrated TE at late-round ADP.* Three questions —
where in the ADP distribution the mispricing sits, whether late TE hits are forecastable, and
whether the Kraft example represents a recurring pattern. Absorbed the previously queued TE arm on
`snap_counts` rather than running it beside.

**Posture: exploratory.** Nothing registered, nothing corrected for multiplicity, nothing shipped.
The one confirmatory test worth running is an *ask* in thread 087 and was deliberately not run.

## What was measured

Universe frozen pre-season from the FantasyPros ECR preseason list (`is_preseason_final=1`,
late-August `as_of_date`), 2021–2024, 344 TE player-seasons. Never-played TEs scored 0 and
retained. 2025 outcomes never read.

- **Hit rate by pre-draft band is steeply front-loaded with no late bump** — TE1-3 66.7%
  [39.1, 86.2] down to TE11-16 4.2% [0.7, 20.2].
- **5 of the 7 top-6 TE seasons that came from pre-draft TE11+ were outside the 150 picks of a
  10-team draft** — waiver adds, not late-round picks. In the actual last four rounds (ECR
  111–150) the top-6 rate is 7.4% [2.1, 23.4].
- **Consensus error scale is flat across the TE draft range** (residual RMSE 45.9 → 43.4) where RB
  falls 104.7 → 61.2. New, unexplained, logged to `ideas-inbox.md`.
- **A TE at overall ECR 75–113 costs the same VBD as a WR at the same pick** (−12.2 vs −12.2) and
  buys a 25.0% [10.2, 49.5] top-6 shot. One such pick beats three darts at ECR 111–150 (20.6%).
- **Forecastability is near-nil.** Of 11 pre-draft signals only consensus rank (0.649 [0.56, 0.74])
  and the panel's most optimistic expert (0.692 [0.61, 0.78]) exclude a coin flip, and both are the
  market restated. Expert disagreement killed (0.487/0.500/0.432). Snap-share proxy not supported
  at TE11+ (0.630 [0.36, 0.89]).
- **Kraft was consensus TE11 at overall ECR 105 going into 2025**, off a TE9 2024 — a mid-round TE,
  not a late-round unknown. Pattern test 2021–2024: Kraft-type 1.9% [0.5, 6.6] vs 2.5% [1.1, 5.8]
  for other late TEs. No advantage.

## Two methodological corrections made mid-pass

1. **Rank statistics were initially pooled across seasons**, which compares a 2021 player to a 2024
   player. Rebuilt so every rank-based statistic is computed inside a season and then averaged. The
   pooled version was discarded, not reported.
2. **Band sensitivity in the AUC table.** Running the late band to the end of the consensus list
   (TE41-95) moves the AUCs to 0.826 / 0.860 / 0.629 / 0.555 / 0.803 — every killed signal appears
   to work. The denominator does all the work. Recorded in the report as a trap, because the
   flattering version is what an unconstrained analysis produces by default.

## Escalated rather than celebrated

TE1-3 produced exactly two top-6 tight ends in each of the four seasons (2, 2, 2, 2) — a 3.9%
coincidence under its own base rate. Not believed to be leakage (pre-draft input, realised
outcome, no path between them) but the regularity must not be read as precision.

## Data gap, now binding

**There is no ADP history in `nfl.db` at all** — `adp_snapshots` and `ffc_adp_snapshots` are
2026-only. The only pre-draft market history is FantasyPros ECR, 4 usable seasons. Every
"late-round" claim in this pass uses ECR rank as a draft-cost proxy, calibrated on the one
overlapping season (2026: TE median ADP − ECR **+12**, IQR [+4, +16], n=18). The proxy error runs
*against* the founder's hypothesis, not for it. Thread 055 is the fix and was replied to.

## Artifacts

| | |
|---|---|
| Report | `docs/ranking/bottom-up-research-pass-2.md` |
| Code (runs, reproduces every headline figure) | `experiments/bottomup/pass2_te_adp.py` |
| Registration ask | thread **087** → `strategist` (stopping condition committed in advance) |
| Data escalation | thread **055** → `data-ops`, replied |
| Founder answer | `FR-039`, status → ANSWERED, replied on-thread |
| Leads logged | 4 entries in `docs/ideas-inbox.md` |

Commits: `e0d6299`, `68cde7f`, `7497477`, `b109100`.
