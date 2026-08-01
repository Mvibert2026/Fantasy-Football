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

**5 · M2-2 availability: do not switch the opponent model to FFC ADP — the estimand argument
conflates units with population.** H1 measured ECR ahead of FFC ADP at predicting real rooms (2 of
3 mocks, mean −1.27 picks), M0 failed its gate (FFC's `times_drafted` is 6.4% of its own implied
denominator), and the rooms the founder drafts in are Yahoo rooms anchored on Yahoo's expert-ish
default list — so "ADP measures the quantity in picks" is true of *FFC's* room, not his. The
pre-registered "switch proceeds on estimand grounds even if NULL" rule made the accuracy
measurement decision-irrelevant before it ran; that is commitment, not calibration. Keep the
estimand *frame* (pick-space, dispersion-aware), feed it the empirically best central tendency
(the board beat everything in 3 of 3 rooms, descriptively), and calibrate sigma through the
simulator against the logged rooms (M3, unrun, highest-value cheap measurement in this area —
its pre-committed direction implies every top-80 availability number is currently too hedged).
Also: availability being identical across the UI's selectable board sources is **correct
behaviour, mislabelled as a gap** — opponents do not change because the user changed lenses. Log
§M2-2.

**6 · M2-3 recommender: the two "contradictory" findings are both right, about different
quantities, and the board is being read as something it is not.** Season VBD is a value *stock*
(points over replacement if the season goes as projected); a pick recommendation is a *policy*
(value now minus what the pick forgoes later). Allen can genuinely be the #6 season value AND
taking a QB in rounds 1–3 can genuinely cost −115 points (PR-003, 12/12 cells) — because QB value
is cheaply available later (the QB premium collapsed −67→−4) while pick-6 RB/WR value is not.
The category error is presenting a season-value order as a pick order; the −25 constant is a
hand patch over exactly that error. **Spec: score = VBD − E[best same-position VBD at your next
pick], with the expectation from the calibrated availability model — and this must be registered
and simulated before shipping, because PR-008 already measured a VONA variant with a crude
scarcity input LOSING to plain VBD by ~−106 to −126.** Opportunity-cost logic is only as good as
the survival model under it, which is why the founder's build order (availability before
recommender) is correct. Interim: run PR-007 as registered — it is the founder's own direct ask
("we need to test those adjustments"), it has sat unrun for three days while ~90 factor tests
ran, and it is powered to delete. Log §M2-3.

**7 · M2-4/5/6 in one paragraph each.** *Campaign correction (M2-4):* the manifest device worked
where applied (batch 6 self-caught, conservative direction) — but "the campaign" as cited (~90
tests) has never been one corrected family: batches 1–3's 62 tests are excluded by C2's own
no-retroactive rule, and the implemented procedure (each batch ranking only its own p-values
against the shared M=80) is *more conservative* than a true pooled BH — under pooled BH at the
campaign's own floor, 7 cells clear, all of them already-recognised ablations/baselines/
PROJECTION-ONLY arms plus one MARGINAL (TE first-downs-per-target) that dies again at the honest
full denominator (M≈118). **No suppressed edge, no false survivor — conclusions are robust to the
procedure defect, which is why this is a finding and not a block.** *Nulls (M2-5):* the ~90 nulls
are real findings at the component level — the instrument demonstrably detects effects of the
size that matters (it caught its own artifacts at 2× treatment size) — and symptoms only of the
wrong *question* (F-ruling); the backtest.py zero-VBD defect lives in `src/`, not in the
experiments harness that produced the nulls, so it contaminates none of them. The three
coverage-flag stories collapse into one mechanism: batch 7's time-dummy explanation subsumes
batch 5's "coverage artifact" (same source, same geometry — `participation` starts 2016, inside
every training window), and batch 3's NGS-separation VOID has the same geometry (NGS starts
2016). All VOID verdicts stand; the *mechanism* sentence changes; the fix is batch 7's (restrict
the training window, not the target window). *PR-009 (M2-6):* zero-POOR is **real for expert ECR
and rule geometry for market ADP.** Against ECR the heuristic genuinely never wins a cell (0 of
16 negative gaps). Against market ADP the crowd's gap is *negative in 13 of 28 cells* (46%) —
never outside a noise band whose median half-width is **±0.26**, twice the fixed +0.134 STRONG
threshold, and one STRONG cell sits *inside its own band*. "Consensus routinely beats the
heuristic and never measurably loses" over-reads the market half; the symmetric statement is
"5 up-band, 0 down-band, 23 unresolved." Same power wall as F5, seen from the other side.

**8 · The founder's three questions and 7 September, consolidated.** (1) *Best bottom-up
rankings:* demonstrated edge over both crowds — **not earnable**; a games-repaired v1.1 at
measured market parity with non-harmful deviations — earnable. (2) *Best availability:*
calibrated-to-Westwood — **not earnable** (first Westwood data arrives draft day); fitted to N
logged Yahoo rooms with honest labels — earnable in days (M3 + closed-form prep mode). (3) *Best
suggested-pick:* a recommender demonstrably beating plain VBD — earnable only if PR-007 → M3 →
registered VONA test all run clean, in that order; an honest VBD recommender with no unfitted
constants — earnable in under a week. **What still requires the founder:** the holdout decision
(§4); the §6.5 baseline-crowd escalation strategist filed (ADR-draft §2.4); and detection — he
remains the only sensor that has caught live product defects (Burrow, the inverted card), and
nothing built this week replaces him. The substitute detector is the acceptance harness plus the
registered-test discipline, and it has caught exactly one defect unaided. Do not remove him yet.

## TOKENS USED

~450k of context consumed at this update (estimate from context size; no meter; ±20%).

## STATUS

| Section | State |
|---|---|
| Frame question (founder's) | **RULED** — log §F |
| M2-1 rankings | **DONE** — log §M2-1, recommendations §M2-1-REC |
| M2-2 availability | **DONE** — log §M2-2 |
| M2-3 recommender | **DONE** — log §M2-3 |
| M2-4 campaign correction | **DONE** — log §M2-4 |
| M2-5 nulls: findings or symptoms | **DONE** — log §M2-5 |
| M2-6 the clean PR-009 result | **DONE** — log §M2-6 |

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

### 2026-08-01 · M2-2 — availability: the two mandate questions, answered

Evidence base: thread `2026-07-30-availability-adp-measurements-m0-m5` (M0 FAILED its gate, M1/H1
NULL, M2–M5 unrun), the precommit `availability-opponent-model-precommit.md`, and the code
re-verified this run (`draft_sim.py:120` `CONSENSUS_RANK_SOURCE="fantasypros_ecr"`, `:319`
`NEED_ADJUSTMENT_SCALE=10.0` hardcoded, `availability.py:239` one shared noise draw per player per
simulated draft, sigma sweep 5/10/20 with the module docstring itself calling it uncalibrated).

**Q1 — "adopt ADP on estimand grounds despite the accuracy NULL": rationalised, in the specific
sense that the decision was structured so the measurement could not move it.** The precommit's own
rule reads: "If NULL, the switch still proceeds on estimand grounds." A decision rule that
proceeds identically under CONFIRMED and NULL is not using the test — the test existed to gate
*claims*, not the decision, and that asymmetry was written in before the data arrived. On the
merits the estimand argument is half right and the wrong half is load-bearing:

- Right: the opponent model needs a *pick distribution* — central tendency in pick units plus
  dispersion. ECR ranks are ordinal opinion with neither.
- Wrong: "ADP measures the quantity" ignores *whose* picks. The estimand is "pick distribution in
  the founder's Yahoo 10-team rooms." FFC ADP estimates FFC's own mock-room population. Yahoo
  rooms are anchored on Yahoo's default (expert-shaped) list — and H1's direction is exactly what
  that mechanism predicts: ECR beat FFC ADP at predicting real Yahoo rooms in 2 of 3 mocks (mean
  gap −1.27 picks in ECR's favour), and the half-PPR board beat all five candidates in all three
  rooms (descriptive, n=3). Units are not population. **Ruling: keep the estimand frame, reject
  the source switch.** The central tendency should be whatever best predicts the observed target
  rooms — currently the incumbent (with the board as the promotable candidate once more rooms are
  logged) — and the label on every availability number should carry the population caveat
  (Yahoo mock rooms ≠ Westwood; Westwood calibration count is 0 of ~30).

Dispersion separately: M0's failure means FFC `times_drafted` supports no per-player n, so the
per-player dispersion half stays dead regardless of source. The mocks themselves are the honest
dispersion source: per-round MAE 1.12 / 3.66 / 8.22 picks (rounds 1–3) is a measured dispersion
curve, and M3 — fitting the simulator's lambda to reproduce it — is the single highest-value
unrun measurement in this whole area. Its pre-registered direction (lambda_hat < 10) implies the
shipped 5/10/20 sweep systematically over-hedges the top 80, i.e. **every availability
probability the founder sees for draftable players is currently pushed toward 0.5 by an admitted
guess.** That is worth a founder sentence when it is fixed, and the fix is a script and three
logged rooms, not a data acquisition.

**Q2 — the founder's factorisation (ADP → how the draft has fallen → opponents' needs): endorsed
as an information ordering, and it exposes the simulator's actual value honestly.** With a pick
distribution per player and no conditioning, the prep-mode marginal is closed-form (M5's point:
`P(survives pick p) = 1 − F_i(p)`); ADR-061 measured 628 s of Monte Carlo per league to
approximate arithmetic. "How the draft has fallen" is conditioning — mostly truncation
(who is gone), also nearly closed-form. The only term that genuinely requires simulation is
**opponents' needs**, which is precisely the least-validated object in the product: need scale
hardcoded at 10.0 (D-001 decided, unimplemented), lambda = 0.352 fitted on one hand-transcribed
draft with need confounded with round, interval [0.21, 0.50] that "more resampling will not
narrow." So: **prep-mode availability should be closed-form** (and FR-128's 24 empty leagues
become arithmetic); **the simulator earns its keep only in live mode**, where truncation-plus-need
interact — and its need term needs Westwood data that starts existing in September. "Mostly
theatre outside live draft state" is the correct description of the current prep-mode Monte
Carlo, with the caveat that M5's tolerance check (mean ≤ 0.02, max ≤ 0.05) should be run before
the swap, exactly as specified, because the removal mechanics could yet surprise.

**A reframe worth recording: the "availability ignores the selected ranking source" gap is not a
gap.** Post-ADR-068 every `board*.json` carries identical availability blocks across the four
selectable sources, reported as an audited defect. Availability is a property of the *room*, not
of the user's lens — opponents do not re-rank because the founder toggled his view. The real
defect in the founder's 73-of-80 diagnosis is the *user's own* BPA pick running on `fantasypros_ecr`
instead of his selected board (`strategy_bpa`), which is a one-line source split (the thread's
code-fact #1), not a reason to rewire opponent behaviour. Recommendation: fix the BPA half, keep
the opponent half source-independent, and say so in the UI label.

**M2-2 recommendations, in order:** (1) run M3 lambda calibration on the three logged rooms —
cheap, changes every displayed availability number, converts "a guess" to "fitted to N rooms";
(2) run M5 and swap prep-mode to closed-form if it passes — fixes FR-128 by arithmetic;
(3) split `strategy_bpa`'s source from the opponent model's (assertion, not comment);
(4) do not switch the opponent central tendency to FFC ADP; re-test candidates per logged mock as
rooms accumulate, per-mock, never pooled; (5) the dispersion ladder is mocks → M3, never
`times_drafted` until FFC documents it. **September 7: availability at "calibrated to his real
league" is not earnable (0 Westwood drafts exist, the first arrives that day); availability at
"fitted to N observed Yahoo rooms with the population caveat labelled" is earnable in days.**

### 2026-08-01 · M2-3 — the recommender: adjudication and specification

Verified this run: `recommendation.ts` ordering is `vbd + 8·unfilled_need + 18·tier1_te −
25·early_qb`, availability appears nowhere in the ordering path (survival is display-side);
PR-007 (the constants ablation the founder asked for on 2026-07-29) is registered, frozen — and
has **zero entries in `test_run_log.jsonl`**: never run. PR-003 ran 2026-07-25 (early-QB −115.4
[−176.3, −54.4] at σ=10 from slot 3, negative 12/12; elite-TE-early −96.1, negative 12/12).
PR-008 ran 2026-07-30: gap-aware vs gap-blind VONA NULL on outcome, 100% decision divergence —
and its third finding is the important one here: **the VONA formulation tested (share-based
scarcity estimate) underperformed plain VBD by −106.4 [−182.4, −54.3] (σ=10) and −126.0
[−214.5, −69.2] (σ=20)**, CIs excluding zero, not BH-surviving at n=4 but directionally
consistent.

**Q — can the board's Allen-at-6 and PR-003's early-QB-costs-115 both be right? Yes, and the
resolution dissolves the "contradiction."** They measure different objects:

| object | question it answers | Allen |
|---|---|---|
| Board VBD (stock) | if the season goes as projected, points over a static replacement level | legitimately top-6: he outscores QB10-replacement by more than pick-6 RB/WRs outscore theirs |
| Draft policy (flow) | what does spending *this pick* here cost across the whole draft | taking QB in rounds 1–3 costs ~115 points, because QB8-QB12 are nearly free later (QB curve slope −67→−4) while pick-6 RB/WR value is gone by round 3 |

A static replacement level prices players against *end-of-draft* replacement; a pick prices
against *what you can still get at your next turn*. Presenting the season-value order as a pick
order is the category error; the −25 is a hand patch over it, and — contra PR-007 §8.2's
"probably redundant" premise — it patches in the *correct measured direction*: fr136 §2 measured
the shipped board *lifting* elite QBs ~+20 places vs consensus (Allen +20, Lamar +20), not
suppressing them. Deleting the −25 without fixing the underlying error would make the
recommender *more* QB-forward in rounds 1–5, the exact direction PR-003 measured as the costliest
tested. **PR-007's §9 prediction table should be read with that premise correction attached; the
design itself is unaffected (it measures rather than assumes).**

**The specification** (what the ordering rule should be):

```
score(i) = VBD(i) − E[ max VBD among same-position players available at my next pick ]
```

- The expectation comes from the availability model's per-player survival probabilities — after
  M2-2's M3 calibration, and closed-form in prep mode, so this is arithmetic, not simulation.
- Need enters through what it actually is: the marginal starter slot changes *which* VBD is
  decision-relevant (your second QB is worth ~nothing; your third WR is a starter in this
  league). `_legal_mask` already enforces the hard floor; the +8 flat bonus is superseded by
  slot-marginal VBD rather than deleted-and-forgotten.
- The +18 tier-1 TE constant points at the top of the position while the project's own evidence
  (elite_te_early −96.1 12/12; the TE7–10 mispricing window) points at the middle. Its
  disposition belongs to PR-007 as registered.

**The caution, from the project's own measurement:** PR-008 is direct evidence that
opportunity-cost reasoning with a *bad* survival input is worse than no opportunity-cost
reasoning at all — reaching on phantom scarcity. So the spec above is a *registered-test
candidate*, not a shipping instruction: it ships only after beating plain VBD in the same
paired-simulation harness (new PR, m accounted, same +20-point materiality floor PR-003/007 use).
If it cannot beat plain VBD with calibrated survival, plain VBD is the recommender and that is a
fine, honest product.

**Order of operations for the 37 days:** (1) run PR-007 as registered — days, answers the
founder's direct ask, powered to delete; expected outcome collapses the panel to VBD order.
(2) M3 λ calibration (M2-2) → closed-form survival. (3) Register and run the VONA-with-calibrated-
survival arm against plain VBD. (4) Product surface: stop presenting the overall board order as a
pick order — either label it season value or show the opportunity-adjusted pick score once (3)
lands. The recommendation card's honesty fixes (2026-07-30) already stopped the card *narrating*
availability it does not use; step (3) is what makes it actually use it.

**September 7:** a recommender that *demonstrably beats plain VBD* is earnable only if (1)–(3)
run clean on the first pass — tight but real. A recommender that is *honest* (VBD order, no
unfitted constants, correctly-labelled availability) is earnable in under a week and is already
strictly better than what ships.

### 2026-08-01 · M2-4 — did the campaign-level correction actually happen?

**Verified from the manifest files and the committed per-batch CSVs (not the write-ups).**
Manifest holds batches 5 (m=17), 6 (m=23), 7 (m=16) → Σ=56, floor 80 binds. Batch 6's
self-caught late registration is accurately recorded in its own manifest file, with breaking-m
per arm — the device worked, one grade moved, conservative direction. **Three structural facts
the write-ups do not state:**

1. **Batches 1–3 (23 + 15 + 24 = 62 tests) are outside the family by C2's explicit
   "no retroactive re-grading" rule.** So the "~90-test campaign" has never had a single unified
   multiplicity treatment; the floor-80 was a patch covering the manifest-era batches only.
2. **The implemented procedure is not BH over the family.** Each batch ranks only its own
   p-values against M=80; a rank cannot exceed the batch's own m, so the effective threshold is
   far stricter than pooled BH at the same M. Pooled BH over the 57 p-values I could extract
   (batches 3/5/7; 1/2/6 use different CSV schemas) at the campaign's own M=80 passes **7 cells**:
   the QB-rush ablation (already EARNS-ITS-PLACE), three BASELINE-WORSE cells (B2r per-game at
   WR/TE/QB), both explosive-rush PROJECTION-ONLY arms and the QB-rush→passing arm — and **one
   grade that would improve: batch 5's TE first-downs-per-target (p=0.00837, MARGINAL), which is
   also the family my F4 re-count found improving both universes.** At the honest full
   denominator (M≈118 with batches 1–3 counted; ≈134 with my 16) the pooled threshold tightens to
   p≤0.0025/0.0011 and only the ablation, one baseline cell, and explosive-rush survive — all
   already recognised.
3. **Net: no suppressed edge and no false survivor either way.** The conclusions are robust to
   the correction's defects. Recorded as a defect anyway, because next time the campaign might
   not be lucky: per-batch-at-shared-M is conservative (power lost on a power-starved campaign),
   and an uncorrected 62-test remainder is exposure in the other direction.

**Recommendation:** strategist folds a one-page campaign-closure note into the manifest README:
the family's final composition, one pooled BH pass over every extractable p at the final M, and
the statement that batches 1–3 sit outside it by rule. Not a re-grade — a record.

### 2026-08-01 · M2-5 — are the nulls findings or symptoms?

**Findings, at the component level; symptoms only of the wrong question.** Three specifics:

1. **The backtest defect does not touch them.** The zero-stat-player VBD bug lived in
   `src/backtest.py` (ADR-066); the ~90 nulls ran in `experiments/bottomup` on component MAE and
   board Spearman — a disjoint code path. Its own re-run showed board figures unchanged. The
   "symptom" hypothesis via that defect is dead.
2. **The instrument has demonstrated power at the effect sizes that matter.** It detected the QB
   rushing ablation (+14.4%, p=4e-6), lagged YPC (−1.9%), and its own coverage-flag artifacts at
   215% of treatment size. A harness that detects its artifacts that clearly is not underpowered
   for effects of that size; the nulls mean "no effect ≥ ~1–2% of component error," which is a
   finding. What it cannot see is the crowd question (F-ruling) and sub-1% effects.
3. **The coverage-flag trilogy is one mechanism, and the ruling is batch 7's.** `routes_known`
   (batch 5) and `rzsnap_known` (batch 7) share source (`participation`, starts 2016) and
   geometry (source begins inside the training window) — both are time dummies, not coverage
   effects. Batch 3's NGS-separation VOID (control = 92% of treatment; NGS starts 2016) has the
   same geometry. **All VOID/artifact verdicts stand** — a time dummy is just as fatal to a
   treatment's interpretation as a coverage artifact — but the mechanism sentence in batch 5's
   results should be corrected by reference (no document edit by me; routed via PM), and the fix
   for future arms is batch 7's: restrict the *training* window so the flag is constant, rather
   than only gating target-season coverage.

### 2026-08-01 · M2-6 — the suspiciously clean PR-009 result

**Computed from the committed `pr009_consensus_quality.csv` this run (44 covered cells).**

| crowd | cells | gap<0 (crowd behind heuristic) | POOR | STRONG | STRONG inside own noise band | gap>0 outside band | median null half-width |
|---|---|---|---|---|---|---|---|
| expert ECR | 16 | **0** | 0 | 12 | 0 | 12 | 0.097 |
| market ADP | 28 | **13 (46%)** | 0 | 6 | **1** | 5 | **0.262** |

**Ruling: zero-POOR is a real quality statement for expert ECR and a power statement for market
ADP.** Against ECR the heuristic never takes a cell even on point estimate — consensus quality is
genuine there. Against the market, the crowd's point estimate is *behind the three-line
heuristic in nearly half the cells*, and "zero POOR" holds only because the single-season noise
band (median ±0.26) is enormous — nothing clears it in either direction, while the STRONG label
needs only a fixed +0.134, *below* the band, and one STRONG cell sits inside its own band. The
asymmetry is in the registered rule (band-clearance for POOR, fixed constant for STRONG), so the
process was honest and the prediction-contradiction real — but the headline sentence
("consensus... routinely beats the weighted-PPG heuristic and never measurably loses") prices the
two labels as if they cost the same, and they do not. **Symmetric restatement for the record:
ECR 12 up-band / 0 down-band / 4 unresolved; market ADP 5 up-band / 0 down-band / 23
unresolved.** This is F5's power wall measured from the other side, by the same instrument class,
and it is consistent with everything else this run found: single-season, single-position crowd
comparisons at this sample size mostly cannot resolve, and any decision rule that appears to
resolve them routinely should be checked for asymmetric label prices first.
