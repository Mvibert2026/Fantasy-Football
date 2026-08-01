# Fable M2 — findings

Run started 2026-08-01 (end-of-week slot, before the Monday reset). Mandate:
`docs/fable-mandate-M2-2026-08-01.md`. Branch `claude/pm-agent-setup-gobxa0` from `908bd9f`.

## CONCLUSIONS SO FAR

**1 · The frame ruling (founder's question): he is right about the record, and the honest count
is this — "can we beat consensus" has been asked with an object capable of winning exactly twice,
not ~90 times.** The ~90 factor nulls are real answers to a different question ("does feature X
improve our own component model"), mislabelled through six consecutive pre-commits as the §6.5
consensus bar. They carry near-zero information about whether consensus is beatable. But the
correction cuts both ways: it does not resurrect a single dead factor. Full ruling in the log,
§F1–F7.

**2 · The right frame** (short form): §6.5 unchanged as the gate; component MAE demoted to
engineering diagnostic (strategist's rename — endorse, still unapplied); C2 universe as endpoint
(endorse); and add a **disagreement-conditional win rate** as the working progress metric —
pre-registered below and computed this run — because full-board per-position ρ vs the crowd is
power-walled at 3 of 4 positions (7 seasons cannot distinguish market ADP from a three-line
heuristic at QB/WR/TE) and no amount of model quality fixes that.

## TOKENS USED

~150k of context consumed at this update (estimate from context size; no meter available; ±20%).

## STATUS

| Section | State |
|---|---|
| Frame question (founder's) | **RULED** — log §F |
| M2-1 rankings | IN PROGRESS — diagnostics pre-registered, computing next |
| M2-2 availability | not started |
| M2-3 recommender | not started |
| M2-4 campaign correction | not started |
| M2-5 nulls: findings or symptoms | not started |
| M2-6 the clean PR-009 result | not started |

---

## LOG

### 2026-08-01 · run start

Timing verified: Saturday before the Monday 11:00 reset — the designed end-of-week slot, not a
mid-week dispatch. Shared pool was 88% consumed at dispatch; plan is frame question → M2-1 → M2-2
→ M2-3 → M2-4/5/6, committing after each, stopping cleanly when the pool runs out rather than
starting a section that cannot finish.

### 2026-08-01 · F — The frame ruling

**The founder's sentence:** *"Part of it is clearly we've only been measuring if better than
consensus for an adjusted model."* Ruled on before attacking any individual result, as instructed.
Everything below was verified against the primary artifacts this run — precommit texts, the eval
code, and the committed results CSVs — not inherited from the write-ups.

**F1 · What the ~90 tests actually measured — verified in the precommits and `pos_eval.py`.**
Every batch's FDR endpoint (`E1a`) is out-of-sample MAE of one component (carries, targets,
attempts…) on the full universe, arm vs the batch's own primary model. `E1b` is the same on the
ADP-board universe. `E2` is ADP-board Spearman, **arm − primary**. Consensus appears in none of
these. The only §6.5-shaped number in the campaign (`E4`, model − market ADP) appears in one batch
of seven. Meanwhile all six precommits label `E2` "the bar that matters" — batch 1 citing
`CLAUDE.md` §6.5 explicitly (`factor-batch-1-precommit.md:53`) — so the campaign *reported itself*
as running the consensus bar while running self-referential component tests. Strategist's Ruling 1
(`ADR-DRAFT-edge-vs-absolute-quality.md`) already established this mechanically; I verified the
label in all six precommits and the endpoint definitions independently. **Confirmed, and the
founder's sentence is the correct plain-English statement of it.**

**F2 · What the vs-consensus record actually contains.** Three objects have ever been compared to
a crowd:

| object | comparison | result | can it win? |
|---|---|---|---|
| Shipped board (consensus re-scored) | τ_b within position | 0.000000, 12/12 cells | **No — structurally.** Within-position order identical to consensus by construction |
| Shipped board | `starter_vbd` cross-positional, ADR-025 | +84.9 dev-mean, sign-test p = 1.0 | Capable but **unpowered by design** — 3 dev seasons, sign-test floor 0.25. Market-ADP baseline never enabled; tier baseline never run against the board |
| Component models (pass 1, `E4`) | Spearman vs market ADP | RB **−0.052** (the one position with power), 3 positions unresolvable | Yes — first real ask |
| v1 (2026-07-31) | full §6.5, both crowds | loses/parity everywhere | Yes — second real ask, and the first with a genuinely independent ordering (ρ 0.54–0.71 vs consensus) |

So the honest denominator for "attempts to beat consensus with something that could" is **2**, and
both were fitted from the same feature family. Everything else was either an object that could not
win (the adjusted board, within-position) or a test that was not asking (batches 1–7).

**F3 · What the ~90 nulls still legitimately mean — the correction must not over-run.** The nulls
are real, competently produced answers to: *"given prior-year volume/share, age, and availability,
does public feature X detectably improve component prediction at n≈7–13 seasons?"* Answer, ~90
times: no. That licenses "these features add nothing **to this model's components**." It does not
license "the external factor well is dry" (PM belief #1 — unsupported, the consensus question was
never asked), and equally it does not license "the factors might still work against the right bar"
(PM belief #3's over-application — a feature whose information is already in the model by another
route, e.g. batch 7's N18 RESTATEMENT at R² = 0.90, stays dead under any bar). The frame correction
changes what the nulls *mean*, not whether any factor *works*.

**F4 · Two measured defects in the frame beyond the labels.** (a) The FDR endpoint pointed away
from the product: batches 5 and 7 found every full-universe improvement degrading the ADP board —
three batches, three positions, four sources (I re-verified the sign pattern from the committed
results CSVs, see D0 below). Strategist has moved the endpoint to C2 from batch 8 — endorsed.
(b) MAE's median-seeking pathology (improvable by shrinkage that destroys ordering) was ruled on
for the projection metric and never applied to the campaign's own endpoint — meaning even the
component-level "wins" (lagged YPC, explosive rush) are not yet known to be ordering
improvements.

**F5 · The power wall is the deepest structural fact, and no frame fixes it by relabelling.**
Measured (`component-model-rb-qb-te-pass-1.md` §1, re-stated in the ADR draft): seven seasons
cannot distinguish market ADP from a three-line heuristic at QB, WR, TE. Only RB has power. So
"beat the crowd significantly, per position, on full-board rank correlation" was never reachable
at three of four positions **regardless of model quality**. Any frame that keeps season-level ρ as
its unit of evidence inherits this wall. The ways out: (i) more seasons — capped by §6.4
non-stationarity; (ii) a unit of analysis with more effective n — pairwise disagreements, below;
(iii) different questions — cross-positional structure, availability, recommender, where the crowd
does not compete.

**F6 · The right frame, stated for the founder.** Keep §6.5 exactly as is — it is the gate a
*version* must pass before anyone drafts on it. Between versions, progress is measured by:
(1) the **disagreement-conditional win rate** (pre-registered below): among player pairs where v1
and the crowd order oppositely, how often is v1's side right? This is paired, has effective n in
the hundreds per season instead of 1 per season, and is the decision-relevant quantity — the only
actionable output of a proprietary board is its deviations from consensus. If we cannot win our
deviations, the correct board **is** consensus. (2) Component diagnostics (renamed C1/C2/R1/M1 per
strategist — apply the rename; it has not landed anywhere). A "we beat consensus" claim remains
reserved to §6.5 on a ranking version.

**F7 · Consequence for the founder's three questions.** The rankings question is not "keep testing
factors until one clears consensus" — F5 says that road is power-walled and F2 says it was barely
ever walked. It is: fix v1's identified defects (availability sub-model first — the Burrow/Hill
defect), then ask whether v1's *disagreements* with consensus carry positive value, and ship
deviations only where that is demonstrated. Availability and the recommender do not wait on any of
this (founder's own ruling 2026-07-31 — they run on ADP/consensus).

### 2026-08-01 · Pre-registration of M2-1 diagnostics (before any number is computed)

Registered here and in `docs/ranking/factor-campaign-manifest/batch-M2.md` (committed together,
this commit precedes the compute). Both run on the committed
`experiments/bottomup/results/ranking_v1_v1_players.csv` — the frozen v1 panel, no refit, no
selection, 2025 untouched (panel is 2018–2024).

**D0 (verification, no grade):** reproduce v1's published per-cell Δρ from the committed per-player
panel (assembly: rookies pinned to crowd slot, veterans by `proj_points`) to ≤0.005 tolerance;
re-verify the batch-5/7 "full-universe improvement degrades the board" sign pattern from the
committed batch results CSVs. If reproduction fails, everything downstream stops and the failure is
the finding.

**D1 (availability-channel decomposition — estimation, no hypothesis grade).** Replace v1's games
projection with realised games at fixed per-game rates: `oracle_pts = proj_points ×
games / max(proj_games, 1)`, crowd arms unchanged, same universes and assembly as v1's published
evaluation. Report per cell (panel × position): Δρ(v1) → Δρ(v1-oracle-games), share of the deficit
closed. Split the deficit by prior-season missed time (`missed_wks_1 ≥ 4` vs `< 4`): mean rank
error contribution per group. **Registered prediction (so the result can surprise): if the
founder's "consensus knows recovery timelines/roles" story is the explanation, oracle games closes
the majority of the ECR deficit at QB/RB and the deficit concentrates in the missed-time group.**
Caveat registered up front: proportional scaling approximates the bonus channel (bonus points are
per-game calibrated); stated wherever quoted.

**D2 (disagreement-conditional win rate — graded, 8 cells).** On each panel × position C2
universe, all player pairs (i, j) where v1's assembled order and the crowd's order disagree.
v1 "wins" a pair if its preferred player scored ≥ the other's realised points (ties in points — both
zero — excluded). Primary statistic: pooled win rate across seasons, **veteran-only pairs**
(neither member rookie-pinned, so no crowd information inside v1's side of the pair); all-pairs
reported as sensitivity. Uncertainty: season-block bootstrap (4,000 reps, seed 20260801) on the
pooled rate. Grade per cell: NULL unless the 95% CI excludes 0.50; 8 cells enter the campaign
family (manifest batch-M2, m = 8), BH within the campaign at grading. Descriptive strata (no
grade): win rate by v1's conviction (v1 rank gap ≥ 3 / ≥ 5 / ≥ 10). **Interpretation registered in
advance:** under "v1 = consensus + noise," inverted pairs resolve for the crowd and the rate falls
below 0.50; 0.50 is genuine-parity-of-information; above 0.50 means v1's deviations carry value
even though full-board ρ loses — these readings are fixed now so the number cannot be renarrated
after it is seen.
