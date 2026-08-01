# Fable M2 — findings

Run started 2026-08-01 (end-of-week slot, before the Monday reset). Mandate:
`docs/fable-mandate-M2-2026-08-01.md`. Branch `claude/pm-agent-setup-gobxa0` from `908bd9f`.

## CONCLUSIONS SO FAR

**1 · The frame ruling (founder's question): he is right about the record.** "Can we beat
consensus" has been asked with an object capable of winning exactly **twice**, not ~90 times. The
~90 factor nulls answer a different question ("does feature X improve our own component model"),
mislabelled through six consecutive pre-commits as the §6.5 consensus bar. They carry near-zero
information about whether consensus is beatable — and the correction cuts both ways: it
resurrects no dead factor. Log §F1–F7.

**2 · M2-1, the finding the founder should read first: v1's deficit is located, and it is one
channel — projected games.** Measured on the frozen v1 panel with pre-registered diagnostics
(log §M2-1): substituting realised games at fixed per-game rates flips every losing cell to a
win (upper bound, not a target — it borrows outcome information); the excess rank error vs both
crowds concentrates in players who missed ≥4 weeks the prior season (86–131% of the market-panel
excess); v1's games projection has near-zero ordering skill on the board universe (r 0.12–0.24
with realised games) and is *worse than naive persistence* there on MAE. **The founder's
"consensus knows things v1 was never told" narrative is right in a specific, actionable form: what
consensus knows is who is going to play** — not diffuse camp-report magic across all channels. On
full-prior-season players at the market panel v1 is already at or better than parity.

**3 · v1's disagreements with the market are coin flips (0.46–0.51); with experts they lose
(0.34–0.41, p=0.0003), but depth-matching to draftable rows moves expert cells to 0.43–0.52.**
The decision-relevant statement: deviating from consensus on v1's advice is currently
value-neutral against the market at draftable depth, mildly value-destroying against experts at
QB/RB. A pre-registered repair candidate (v2-flatgames — delete the games channel) was **rejected
by its own adoption rule** (1 WIN, 2 HARM): the games model carries real information vs the
market while being far worse than the experts'. **Recommendation: repair, not ablate** — the
games prior must distinguish resolved absences from ongoing ones using pre-Week-1 status
(the Burrow/Hill defect class). Cost days, upper bounds measured. Log §M2-1-REC.

**4 · Holdout recommendation (per mandate, not a spend request): do not spend 2025 on v1 as it
stands.** It would confirm a loss already established seven ways on dev seasons. The right spend
is one confirmatory shot at the games-repaired v1.1 in late August, only if it shows dev-season
recovery first. If no repair lands, spend nothing: ship the consensus-derived board and put the
effort into availability + recommender. What is lost by spending now: the single confirmation
bullet this project gets, on a question that is not open.

## TOKENS USED

~270k of context consumed at this update (estimate from context size; no meter; ±20%).

## STATUS

| Section | State |
|---|---|
| Frame question (founder's) | **RULED** — log §F |
| M2-1 rankings | **DONE** — log §M2-1, recommendations §M2-1-REC |
| M2-2 availability | starting next |
| M2-3 recommender | not started |
| M2-4 campaign correction | not started (partial evidence already in F4) |
| M2-5 nulls: findings or symptoms | not started (frame ruling covers most) |
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
from the product — but the published strength of this claim is itself overstated, measured from
the committed CSVs this run: batch 7's material full-universe improvements degraded the board
**5 of 5**; batch 5's route family **4 of 4**; but batch 5's receiving-first-downs family improved
**both** universes at WR/TE/RB (5 of 10 batch-5 improvements were board-better). Combined:
**10 of 17, not "every."** The direction of strategist's fix (C2 endpoint from batch 8) survives;
the sentence "it is what a usage feature does by default" (batch 7 results, quoted in
CURRENT-STATE) does not — one family contradicts it and nobody had counted. Correction owed to
the batch-7 results doc's §, routed via PM.
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

### 2026-08-01 · M2-1 — results of the pre-registered diagnostics

Script: scratchpad `m2_diag.py` / `m2_v2.py` (logic recorded in this file; both operate read-only
on the committed `ranking_v1_v1_players.csv` + `ranking_v1_v1_season_metrics.csv`; 2025 absent
from the panel by construction).


**D0 — reproduction PASSED.** Max |ρ_mine − ρ_published| over all 44 cells: **2.45e-04** (my
Spearman uses a mean-product formula vs scipy's; the residual is tie-handling noise, far inside
the 0.005 gate). The v1 assembly (rookie pinning + veteran reorder) is faithfully replicated;
everything below inherits it.

**D1 — oracle games (realised games at v1's own fixed per-game rates), Δρ(arm − crowd):**

| cell | Δρ v1 | Δρ oracle-games |
|---|---|---|
| M-QB | −0.065 | **+0.383** |
| M-RB | −0.044 | **+0.208** |
| M-WR | +0.031 | **+0.254** |
| M-TE | −0.011 | **+0.277** |
| E-QB | −0.138 | **+0.158** |
| E-RB | −0.093 | **+0.135** |
| E-WR | −0.065 | **+0.118** |
| E-TE | +0.005 | **+0.207** |

**Read this correctly: the oracle is an upper bound that borrows the outcome's own factor
(points = ppg × games), exactly as fr136 §4 warned for its games oracle. It is NOT reachable.**
What it establishes is *location*: with the games channel bypassed there is no deficit anywhere —
so the deficit lives in that channel, not in rates/volume/TD/bonus.

**D1b — player-level attribution (exact d² decomposition of the Spearman deficit).** Share of the
v1-vs-crowd excess rank error from players with ≥4 missed weeks in season N−1: **M-QB +131%,
M-RB +86%, M-TE +117%** (shares >100% mean full-prior-season players contribute *negative* excess
— v1 is better than the crowd on them); M-WR total excess is negative (v1 ahead overall). Expert
panel: 54–63% from missed-time players who are 56–65% of that deeper universe — less
concentrated, still majority. **The Burrow signature at scale: v1's loss to the market is almost
entirely its handling of players coming off missed time.**

**D2 — disagreement-conditional win rate (8 graded cells, veteran-only pairs, season-block
bootstrap, seed 20260801):**

| cell | win rate | 95% CI | p | pairs |
|---|---|---|---|---|
| M-QB | 0.457 | [0.357, 0.562] | 0.44 | 370 |
| M-RB | 0.459 | [0.370, 0.540] | 0.34 | 1,770 |
| M-WR | 0.508 | [0.458, 0.572] | 0.76 | 2,272 |
| M-TE | 0.506 | [0.394, 0.620] | 0.90 | 176 |
| E-QB | **0.342** | [0.277, 0.415] | **0.0003** | 941 |
| E-RB | **0.360** | [0.323, 0.398] | **0.0003** | 5,205 |
| E-WR | **0.412** | [0.379, 0.436] | **0.0003** | 7,947 |
| E-TE | 0.507 | [0.471, 0.577] | 0.63 | 2,056 |

All-pairs sensitivity: same picture. The three E-cells at p=0.0003 (bootstrap floor) survive BH
at any campaign denominator this project could reach; graded **three significant LOSSES, five
NULL** in the manifest family. Under the pre-registered reading: against experts, v1's
disagreements are resolved *for the experts* — below the "v1 = consensus + noise" line, i.e.
worse than adding pure noise to ECR at QB/RB/WR full-depth. Against the market: coin flips.
Conviction does not rescue it against experts (gap≥10: E-RB 0.367, E-WR 0.415); against the
market it trends up with conviction (gap≥10: M-QB 0.557, M-WR 0.572, M-RB 0.521 — descriptive
only, not graded, confounded with the games channel).

**Depth-matched E-panel (descriptive):** restricting each expert board to the market's own
draftable depth moves E-QB 0.342→0.427, E-RB 0.360→0.435, E-WR 0.412→0.515, E-TE 0.507→0.485.
**Much of the expert edge over v1 lives in the deep board where no draft decision occurs.** At
draftable depth: modest losses at QB/RB, coin flips at WR/TE — consistent with the market panel.

**D2-oracle (games fixed): win rates jump to 0.68–0.80 everywhere, p=0.0003.** The disagreements
v1 loses are overwhelmingly games-driven disagreements.

**D3 — v2-flatgames (registered Amendment 1 before compute): REJECTED by its own rule.**
Per-cell paired Δ(Δρ), v2 − v1: M-QB +0.060 (p=0.078, NULL), **M-RB +0.036 (p=0.049, WIN)**,
M-WR −0.010 (NULL), M-TE +0.010 (NULL), **E-QB −0.033 (p=0.0003, HARM)**, **E-RB −0.043
(p=0.010, HARM)**, E-WR −0.018 (NULL), E-TE −0.017 (NULL). 1 WIN, 2 HARM → adoption rule
(≥2 WIN, 0 HARM) fails. The 0.5-shrink descriptive sensitivity sits between v1 and flat
everywhere — no free lunch on the shrinkage path either. **Deleting the games channel helps
against the market at RB/QB and hurts against experts at QB/RB: v1's games model carries real
information relative to the market's implied availability handling, and materially less than the
experts'.**

**Context measurements (descriptive):** on the board universe, veterans only, corr(proj_games,
realised games) is 0.12–0.24 by position, and proj_games MAE is **worse than naive `games_1`
persistence at all four positions** (e.g. QB 4.04 vs 3.19). The component docs' "beats naive
persistence on every component" was measured on the full universe; on the draft-relevant board
the games component inverts — **the games component is itself an instance of the campaign's own
full-universe-vs-board pathology (F4).**

### 2026-08-01 · M2-1-REC — what would make the bottom-up rankings better, in order

1. **Repair the games prior for resolved absences (v1.1). Days, not weeks.** The defect class the
   founder caught by eye (Burrow QB26, Taysom Hill +194) is the same one D1b measures at scale.
   The prior currently extrapolates season-N−1 absence into season N with no notion of whether
   the absence *resolved*. Pre-Week-1 status is legitimate §6.1 input ("through end of N−1 and
   preseason N"): `load_rosters_weekly(N)` week-1 `status` (RES/EXE), `load_injuries(N)` practice
   status. Caveat for `strategist`: week-1 status postdates a late-August draft by days — rule on
   the as-of alignment before anyone fits to it. Expected gain, bounded honestly: market-panel
   deficit → parity-to-small-positive (flat-games already reaches −0.006/−0.008 at QB/RB without
   *any* games info; a repaired prior keeps the real signal flat-games discards); the expert gap
   narrows but does not close — experts still know things (holdouts, camp roles) no status file
   carries.
2. **Evaluate at draftable depth, both panels, as the reported headline.** The full-ECR-board
   evaluation overstates the expert edge with rows no draft reaches. The sensitivity machinery
   exists (`ranking_v1_sensitivity.py`); make it the primary cut in v1.1's results.
3. **After the repair: one registered confirmatory test of the market-conviction gradient** (win
   rate at gap≥10 vs the market, currently 0.52–0.57 descriptive). If v1.1's high-conviction
   market disagreements clear 0.5 with a CI, that is the first affirmative §6.5-adjacent evidence
   this project will have produced — and the correct holdout spend follows it.
4. **Do not:** run more public-factor sweeps (F-ruling — the shovel was measuring itself; and the
   well being dry was never established either); ship flat-games (rejected by rule); blend ECR
   into v1's inputs (destroys the product's independence, `CLAUDE.md` §4); model rookies
   (eliminated channel); revisit variance/bonus (dead four ways, `CLAUDE.md` §7).
5. **September 7, said plainly:** "the best bottom-up rankings" as *demonstrated edge over both
   crowds* is **not earnable by 7 September** — the F5 power wall plus the current deficit make
   that arithmetic, not pessimism. What is earnable: a games-repaired v1.1 at measured parity
   with the market at draftable depth, whose deviations are measured non-harmful, carrying the
   league-specific cross-positional structure consensus does not price. That is a board worth
   sitting next to consensus on draft day. Claiming *better than the crowds* requires the holdout
   confirmation, and only after dev-season recovery.
