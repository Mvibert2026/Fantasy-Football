# Factor ledger

**Librarian, 2026-07-30.** Every factor this project has considered for the ranking model, with its
disposition and the reason attached — the honest denominator for `CLAUDE.md` §6.3's
multiple-comparisons exposure. Per the founder's own framing (`docs/founder-requests/FR-2026-07-30-deliverable-a-ledger-of-every-factor-considered.md`):

> "What I'll want at the end is a list of every factor we considered. Whether it was included or not
> and why. I hope the considerations are 100 or more but you don't have to anchor to that"

**This ledger is not padded.** Every row below was found stated as a considered factor in a repo
document this session. The count is what the repo actually contains, not a target.

## How to read a row

- **Factor** — defined precisely enough to compute, not a vague label.
- **Disposition** — `included` (in a model that exists, shipped or experimental — the Reason column
  says which), `excluded` (a reasoned decision made without a number), `untested` (identified, never
  run), `blocked` (a data or access gap prevents running it), `rejected-with-evidence` (run, and the
  number says no).
- **Reason** — for anything measured, the number and its interval, never a verdict word alone.
- **Provenance** — internal hypothesis / registry row / external source, tagged `[VERIFIED]` /
  `[SNIPPET]` / `[SECONDARY]` / `[GAP]` for external claims per
  `docs/research/analyst-factor-sweep-2026-07-30.md`.
- **Ever run?** — distinct from disposition. A row can be `excluded` and never run (a priori
  judgment call) or `included` and never run (a structural input nobody has ablated).

**Two scope traps, stated once here and repeated at the row:** registry **#13**'s NULL is about
target-share *stability*, not target share itself (which is #8, unimplemented in the shipped
product). Registry **#28**'s harm at RB was measured on a **Week-1 depth-chart proxy** standing in
for a pre-season roster table that does not exist — it is a finding about the proxy, not about
vacated opportunity.

**Shipped vs. experimental, stated once.** Per `docs/ranking/fr136-q1-bottom-up-assessment.md` §1.1,
the live `board.json` has exactly **one** player-level input — consensus positional rank — and
zero of the factors below. Where a row says `included`, the Reason column states whether that means
*shipped* or *present in the unshipped `experiments/bottomup/components/` model only*. Conflating
the two overstates what is live.

---

## Summary

**92 rows.** Not padded to reach the founder's suggested 100 — see the note at the top of this
document. Counted mechanically from the tables below (excludes the two navigation tables in this
Summary section itself).

| Disposition | Count |
|---|---|
| included | 9 |
| excluded | 9 |
| untested | 49 |
| blocked | 17 |
| rejected-with-evidence | 8 |
| **Total** | **92** |

By section: Tier 0 table stakes 12 · Tier 1 standard analytics 21 (incl. #29b) · Tier 2
league-specific 10 · Tier 5 rejected-without-measurement 6 · external analyst sweep N1–N34 34 ·
sweep definition-only 8 · yardage-bonus variance hypothesis 1 = **92**.

---

## Section 0 — Batch C1: the first dispositions measured against **v2** (2026-08-01)

**Read this before treating any row below as settled.** Every disposition in Sections 1–6 was
assigned under the **old frame**: measured, if at all, against the **consensus-derived** board,
which already contained consensus's embedded knowledge. Per the founder's ruling of 2026-08-01
(`FR-2026-08-01-need-an-inclusion-test-run-candidate-factors-as`), those results **carry almost no
information about whether a factor belongs in v2**, and a `rejected-with-evidence` or measured-NULL
row below should be read as **untested for v2**. Rows excluded for **data availability or
licensing** still stand — those reasons have not changed.

Batch C1 (`docs/ranking/factor-campaign-manifest/batch-C1.md`, results
`docs/ranking/batch-C1-results.md`) is the first set of dispositions measured **against v2**, which
contains no consensus. Six factors, 38 registered cells, control = v2 games arm G0, seasons
2018–2024, 2025 holdout never opened.

| Factor | Ledger row | v2 disposition | Result — absolute rank correlation vs realised finish, Δ against v2 |
|---|---|---|---|
| Offensive snap share, recency-weighted | T0-9, N18 | **rejected-with-evidence (v2)** | RB +0.0027 NULL, WR −0.0025 NULL, **TE −0.0285 HARM** (CI, not BH). Coverage 99.8–100% — a measurement, not a gap |
| Red-zone (inside-20) usage share of team | T0/T1 red-zone usage | **rejected-with-evidence (v2)** | RB −0.0001, WR −0.0010, TE +0.0020, all NULL. Full 2009+ PBP window, coverage 98.5–100% |
| Expected fantasy points (xFP) + luck residual | T1-18 | **NULL (v2) — hypothesis retained at RB** | QB +0.0034, RB **+0.0186 (p = 0.059)**, WR −0.0008, TE +0.0263, all NULL. RB clears the placebo null; not demonstrated |
| NGS average separation | N5 | **rejected-with-evidence (v2)** | WR −0.0000, TE −0.0220, both NULL. Coverage 92% |
| Route participation / targets per route run | T1-16, T1-17, N3 | **rejected-with-evidence (v2)** | RB +0.0019, WR +0.0018, TE +0.0004, all NULL. **Labelled proxy** (routes from `participation.offense_players`) |
| Steeper recency weighting (0.70/0.22/0.08) | `CLAUDE.md` §6.4 | **NULL (v2) — hypothesis retained at QB** | QB **+0.0266**, RB −0.0091, WR −0.0107, TE −0.0115, all NULL. Sign pattern exactly as registered |
| **Coverage-indicator controls** (`snap_known`, `rz_use_known`, `xfp_known`, `sep_known_1`, `routes_known`) | Amendment 1 | **rejected-with-evidence (v2)** | All 15 cells NULL, most exactly no-change. No factor's effect is attributable to its presence flag |

**A harness disposition, not a factor one.** A registered **placebo** — seeded noise that provably
carries no signal — returned a BH-robust WIN at TE and the registered inclusion rule graded it
`INCLUDE`. Replication puts the harness's false-positive rate at **~11–15% of cells against a
nominal 2.5%**. It inflates false *positives* only, so it cannot have produced any of the NULLs
above; it does bind the next batch, and `strategist` owns the replacement rule.

**Two factors from the earlier campaign are NOT resurrected by this correction and remain closed:**
vacated opportunity and rookie draft capital were eliminated cleanly, and QB modelling was closed
after six failed configurations.

### Batch C2 (2026-08-01) — more factors, plus the RB high-carry breakpoint

`docs/ranking/factor-campaign-manifest/batch-C2.md`, results
`docs/ranking/batch-C2-results.md`. **Grading suspended, same reason as above** — every row below
is `PENDING-RULE`, not a disposition change, until `strategist`'s replacement WIN rule lands. CI
verdicts (estimator-independent) are reported for the record.

| Factor | Ledger row | v2 CI result — Δ against v2, PENDING-RULE | Notes |
|---|---|---|---|
| WOPR, recency-weighted | T1-15 | WR −0.0021 NULL, TE −0.0005 NULL | both below this batch's own placebo |
| YAC per reception (RB) | N16 | +0.0004 NULL | reused batch-7 block verbatim; coverage-flag control also NULL |
| Receiving share of an RB's own points | N17 | +0.0101 NULL (p=0.345) | reused batch-7 block; largest RB delta in the batch, CI wide, flagged as the one near-miss |
| Late-season role trajectory | N19 | RB −0.0044 **HARM (CI)**, WR +0.0001 NULL, TE +0.0086 NULL | reused batch-7 block; TE's treatment and coverage-flag control produced bit-identical deltas — investigated, confirmed not a code bug (point-level predictions differ), left as an open oddity |
| Implied team total, lagged | T0-11 / N12 | QB +0.0140 CI-WIN (p=0.0002), RB −0.0000 NULL, WR +0.0040 NULL, TE +0.0035 NULL | first read of `odds_snapshots` by any model here; QB's CI-WIN is smaller than its own matched-control placebo delta (+0.0216) — flagged, not claimed |
| RB high-carry-season breakpoint (350/375/400, single hinge-spline test) | founder, 2026-07-31 | RB −0.0002 NULL | confirmed severely underpowered as registered: 1 board-veteran RB-season crossed 350 carries across the entire graded population |
| **Coverage-indicator controls** (`yac_known`, `recpts_known`, `late_known`, `itt_known`) | Amendment-1-style, C2 | All NULL except `itt_known` at RB, +0.0015 CI-WIN (p=0.0002), while the paired treatment (`itt_w`) itself is NULL at RB | not the batch-7/C1 artifact pattern (treatment doesn't win), but adjacent and flagged |

**A second, independent measurement of C1's own finding**: this batch's placebo at a 4-season
control (`F0D`, CTRL-D) won CI-level at 2 of 4 cells (RB, TE) against 0 of 4 at the matched
7-season control (`F0`, CTRL-A2) — the shorter the window, the more miscalibrated the estimator,
confirming C1's mechanism on a control C1 never tested.

---

## Section 1 — Tier 0, table stakes (`docs/test-registry.md` #1–#12)

Everyone has these; not having one is a loss, having it is not an edge (`CLAUDE.md` §12 framing via
`test-registry.md`).

| # | Factor | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|---|
| T0-1 | Multi-source ADP | blocked | `backtest.py`'s `consensus_adp` arm exists but is `available=False`; the ADR-018 reasoning behind that ("no market ADP source obtainable") is stale — FFC ADP is now ingested (FR-023) — but the arm was never re-enabled. Never measured against the shipped board. | internal — `test-registry.md` #1; `fr136-q1-bottom-up-assessment.md` §1.3 | No |
| T0-2 | Consensus projections (component-level: pass/rush/rec yards, TDs, separately, not fantasy points) | blocked | Every public source publishes fantasy points already scored under someone else's rules; FantasyPros ECR verified rank-only. Blocks rankings, tiers, and league-ADP simultaneously. | internal — `test-registry.md` #2 | No |
| T0-3 | Positional tiers | untested | No tier-heuristic arm exists in `backtest.py:standard_arms()`. `CLAUDE.md` §6.5 requires this as baseline #3; it has never been built. | internal — `test-registry.md` #3; `fr136-q1-bottom-up-assessment.md` §1.3 | No |
| T0-4 | Bye weeks | included | Not a ranking factor — a roster-legality input. `rankings.bye_week` populated 515/554; drives the recommender, not the projection. | internal — `test-registry.md` #4; `fr136-q1-bottom-up-assessment.md` §6a.3 | N/A — structural data, not tested as a ranking input |
| T0-5 | Depth chart / role | included | Present in the **unshipped** `experiments/bottomup/components/` model as arms D/E (`rostered_absent_share_1`, `offroster_share_1`, `depth_first_share_1`) — **not** in the shipped board. Measured **NULL on final ranking at all four positions**. Retained by construction (table-stakes; not selected on results, so it does not add to the FDR denominator per `CLAUDE.md` §6.3) rather than dropped for underperforming. | internal — `pos_features.py:42-43`; `fr136-q1-bottom-up-assessment.md` §6a.1, §6a.2 | Yes |
| T0-6 | Injury designations & status | included | Present in the **unshipped** component model, arm B (`inj_missed_share_1`, `unexp_missed_share_1`). Measured **NULL on final ranking at all four positions**. Retained by construction, same rationale as T0-5. | internal — `pos_features.py:34, 181-197`; `fr136-q1-bottom-up-assessment.md` §6a.1 | Yes |
| T0-7 | Age (as a decline curve) | included | In the base feature set of the **unshipped** component model at all positions (`age`, `age2`). No isolated ablation number exists for age alone in this repo. **The functional form itself — "age → decline curve" — is separately challenged**: see N31 below (Harstad, external), which argues age is better modeled as a bust hazard, not a smooth curve, and that aging-curve studies are contaminated by survivorship. That is an untested hypothesis about *form*, not a result against age as an input. | internal — `pos_features.py:33`, `test-registry.md` #7; external — N31 below | Partially — feature is in the model; the decline-curve functional-form question is untested |
| T0-8 | Prior-year target / touch share | included | In the base feature set of the **unshipped** component model (`tshare_w`, `cshare_w`). Its measured effect is reported under #20 below (team-relative share ablation): **NULL at RB** (−0.017 carries MAE [−0.050,+0.003]), **earns its place at WR** (removing it costs +0.196 targets MAE on the ADP board, +0.6%). Do not read #13's stability-arm NULL (below) as a verdict on this row — different question. | internal — `pos_features.py:132-133,159-160`; `factor-batch-1-results.md` §2 rows 9–14 | Yes |
| T0-9 | Snap share | untested | `snap_counts`, 2013–2025, 324,611 rows, `offense_pct` column — **in `nfl.db`, untouched by any model in this project.** | internal — `test-registry.md` #9; `fr136-q1-bottom-up-assessment.md` §3.3, §6a.3, §6a.5 | No |
| T0-10 | Red-zone / goal-line usage | blocked | Needs play-by-play; **there is no PBP table in `nfl.db`.** `load_pbp(2009…2025)` measured at 816,856 rows / 20.4s to acquire, not yet ingested. | internal — `test-registry.md` #10; `fr136-q1-bottom-up-assessment.md` §3.3, §5.0 | No |
| T0-11 | Vegas win totals & implied team totals | blocked | No odds table exists in `nfl.db`. Separately, the entire team-environment channel is oracle-bounded at **≤ +0.055 τ_b** (`bottom-up-research-pass-1`, cited in `fr136-q1-bottom-up-assessment.md` §6.6) — even if sourced, the measured ceiling is small. Historical odds require a paid source. | internal — `test-registry.md` #11; `fr136-q1-bottom-up-assessment.md` §6.6; §5.1 item 8 | No |
| T0-12 | Season-long strength of schedule | excluded | "Weight near zero" — an a priori judgment (defenses shift year over year; worst units get the most offseason investment), not a number-with-interval. `rankings.sos_season` is populated (515/554) but no ablation or correlation number is on record in this repo. | internal — `test-registry.md` #12; `fr136-q1-bottom-up-assessment.md` §6a.3 | No — populated as data, never measured against outcomes |

---

## Section 2 — Tier 1, standard analytics (`docs/test-registry.md` #13–#32, incl. #29b)

What a serious, well-read opponent already has.

| # | Factor | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|---|
| T1-13 | Target share **stability** YoY (not target share itself — see T0-8) | rejected-with-evidence | **Scope: this tests whether a *stability-weighted* share feature beats the plain share already in the model — it is not a test of target share as an input.** S1 arm: −0.035 targets MAE full universe (BH-significant at WR only, q=0.10), but **0.02% of the model's own error on the ADP board (7 seasons)** and no ranking effect at any position. Separately (descriptive, not a factor result): YoY persistence of target share itself is +0.652 [+0.624,+0.680] WR, +0.632 TE, +0.548 [+0.496,+0.597] RB — role-tier, just below snap share's +0.707. | internal — `factor-batch-1-results.md` §1(4), §2 rows 21–23, §3 | Yes |
| T1-14 | Air yards, aDOT | included | Present as a rate pair (`adot_num`/`adot_den`) in the **unshipped** component model. Model-level effect vs. ADP is position-dependent (WR +0.051 [−0.011,+0.129] Spearman, RB −0.052 [−0.126,+0.038]) but feature-level attribution for aDOT alone was never isolated. | internal — `pos_features.py:73`; `fr136-q1-bottom-up-assessment.md` §1.4 | Partially — in the model, never ablated alone |
| T1-15 | WOPR | untested | Inputs (`target_share`, `air_yards_share`) are 100% populated 2009+ in `nfl.db`; WOPR itself is not computed anywhere in this project. | internal — `test-registry.md` #15; `fr136-q1-bottom-up-assessment.md` §3.3 | No |
| T1-16 | Yards per route run | untested | **Registry correction applied 2026-07-30** (see Corrections section) — was tagged `nflverse:FTN` "2022+"; FTN has no per-player, no receiver ID, no routes-run columns and cannot supply this. Correct source is `load_participation()`, **2016+, ten seasons, not four.** The wrong tag suppressed testing. Not yet run under the corrected source. | internal — `test-registry.md` #16; external correction — `analyst-factor-sweep-2026-07-30.md` §1 | No |
| T1-17 | Route participation rate | untested | Same correction as T1-16 — `load_participation()`, 2016+, ten seasons. Not yet run. | internal — `test-registry.md` #17; external — `analyst-factor-sweep-2026-07-30.md` §1 | No |
| T1-18 | Expected fantasy points (xFP) vs. actual | untested | **Registry correction applied 2026-07-30** (see Corrections section) — re-costed H → L. `nflreadpy.load_ff_opportunity()` is a free, prebuilt, versioned xgboost xFP model over nflverse PBP, 2006–current — a download, not a build. Not yet run. Note per `test-registry.md` #19's result: any xFP test should be specified as an increment over the current shrinkage-based model, since #19 shows the existing empirical-Bayes shrinkage already extracts much of what xFP is meant to capture. | internal — `test-registry.md` #18; external correction — `analyst-factor-sweep-2026-07-30.md` §1 [VERIFIED] | No |
| T1-19 | TD-rate regression (discard own TD rate, use pooled positional mean) | rejected-with-evidence | Arm T2 (discard own TD rate entirely): **worse at all four positions** — WR `rec_tds` +0.0251 MAE [+0.0133,+0.0377], TE +0.0180 [+0.0061,+0.0315], RB `rush_tds` +0.0182 [+0.0052,+0.0307], QB `pass_tds` +0.2295 [+0.1256,+0.3253] (+4.0% of the position's own error). All four BH-significant at q=0.10; three of four at q=0.05. **A player's own TD rate carries real out-of-sample signal; the model's existing shrinkage already extracts it.** The registry's "HIGH edge, unbuilt" framing is wrong — this is a solved problem, not an opportunity. | internal — `factor-batch-1-results.md` §1(1), §2 rows 1–8 | Yes |
| T1-20 | Opportunity share (carries+targets / team total) — "single best RB metric" | rejected-with-evidence | **Scope: RB claim only.** Ablating carry share costs −0.0168 carries MAE [−0.0498,+0.0029] (NULL); share×pace reparameterisation −0.0863 [−0.2724,+0.0683] (NULL). **Neither instrument finds this doing anything at RB** — the registry's "single best RB metric" framing is not supported. **At WR the same construct does earn its place**: removing team-relative share costs +0.0796 targets MAE [+0.0132,+0.1547] full-universe, **+0.196 of 31.4 (+0.6%) on the ADP board.** At TE, NULL (−0.0092 to +0.0360, no CI excludes zero consistently). | internal — `factor-batch-1-results.md` §1(4), §2 rows 9–14 | Yes |
| T1-21 | Team pace / plays per game | blocked | Needs play-by-play; no PBP table in `nfl.db`. | internal — `test-registry.md` #21; `fr136-q1-bottom-up-assessment.md` §3.3 | No |
| T1-22 | Pass rate over expectation (PROE) | blocked | Needs play-by-play; no PBP table in `nfl.db`. See T1-N20 below for a related, cheaper, PBP-dependent alternative (neutral-situation pass rate). | internal — `test-registry.md` #22; `fr136-q1-bottom-up-assessment.md` §3.3 | No |
| T1-23 | O-line run-block & pass-block rankings | untested | **Registry correction applied 2026-07-30** (see Corrections section) — re-tagged `external` → public formula + `nflverse`. Adjusted Line Yards is a published formula over PBP (once ingested); `load_pfr_advstats()` (2018+) ships yards-before-contact, broken tackles, drops, pressure/hurry/blitz free — no PFR scrape, no 403 risk. Not yet run. | internal — `test-registry.md` #23; external correction — `analyst-factor-sweep-2026-07-30.md` §1 [VERIFIED] | No |
| T1-24 | QB quality for pass catchers | untested | Not run. | internal — `test-registry.md` #24 | No |
| T1-25 | NFL draft capital (rookies) | included | `draft_round`, `draft_pick`, `log_draft_pick`, `undrafted` are all built features in the **unshipped** component model. `fr136-q1-bottom-up-assessment.md` §3.3 characterizes this as "mandate: eliminated as an edge channel" — **that underlying quantified elimination evidence was not located in any file read this session; flagged as a gap, not asserted as verified.** The feature exists and is used for rookie handling regardless. | internal — `pos_features.py:222-227`; `test-registry.md` #25; `fr136-q1-bottom-up-assessment.md` §3.3, §5.1 item 10 — **[GAP]: source of the "eliminated" ruling unverified this session** | Feature: yes, exists. The specific "eliminated as edge channel" claim: unknown whether or where it was measured |
| T1-26 | Breakout age / college dominator | untested | Not run. | internal — `test-registry.md` #26 | No |
| T1-27 | Contract year / free-agency status | untested | Tag confirmed correct (`nflverse` contracts) by the external sweep; not yet run. Also unused and present: `load_combine()`, `load_officials()`, `load_trades()`. | internal — `test-registry.md` #27; external — `analyst-factor-sweep-2026-07-30.md` §1 [VERIFIED] | No |
| T1-28 | Vacated targets & carries (where opportunity actually opened) | blocked | **Not a verdict on vacated opportunity — a proxy-contamination finding.** `nfl.db` has no pre-season roster table, so the test ran on a Week-1 depth-chart proxy, declared as a proxy before running. Vacancy arm: **harmful at RB** (+0.2031 carries MAE [+0.1150,+0.2963], BH-sig) and **harmful at TE** (+0.0448 [+0.0106,+0.0773], BH-sig); **NULL at WR** (+0.0818 [−0.0075,+0.1795]). The harm concentrates in the high-measured-vacancy bucket the proxy is known to contaminate (a Week-1-inactive player is miscounted as departed, inflating teammates' projected opportunity that never opened): +0.77 MAE in the high-vacancy split vs. −0.03 low, +0.29 for "club unchanged" vs. −0.46 for "club changed." **This experiment cannot separate "vacated opportunity is uninformative" from "the proxy is bad."** Needs `nflreadpy.load_rosters_weekly()`. Externally, skeptics agree directionally ("not in the least bit predictive"), but that does not resolve this project's own confound. | internal — `factor-batch-1-results.md` §1(2), §2 rows 15–20, §4; external — `analyst-factor-sweep-2026-07-30.md` §3 (Contested set: Vacated targets) | Yes — but the result cannot be attributed to the hypothesis (proxy artifact) |
| T1-29 | Coordinator continuity | blocked | Gated on coordinator-level (`coach_id`) data. Pro Football Reference returns HTTP 403 on `robots.txt` and terms page; no scraper built (`CLAUDE.md` §10). `src/ingest_coordinators_wikipedia.py` and `ingest_play_callers.py` exist and have landed no table in `nfl.db`. Head coach is confirmed **not** a substitute — misses every OC/DC change under a retained head coach. Externally: not a single public backtest of the coordinator-change effect was found across 11 analytics shops reached — the registry's "High edge" rating "has no external evidential support." | internal — `test-registry.md` #29; `fr136-q1-bottom-up-assessment.md` §6.6; external — `analyst-factor-sweep-2026-07-30.md` N22 [GAP] | No |
| T1-30 | First-time play-callers | blocked | Same gate as T1-29 — coordinator-level data unobtainable (PFR 403). | internal — `test-registry.md` #30 | No |
| T1-29b | Head-coach continuity (weaker, buildable proxy — a genuinely different hypothesis from #29/#30, not a substitute for them) | untested | `load_schedules` carries `home_coach`/`away_coach`, 1999–2026, 100% populated, 177 coaches. Cheap, buildable today, not built. Must not be reported as evidence for or against #29/#30. | internal — `test-registry.md` #29b | No |
| T1-31 | Personnel package trends (structural WR3 headwind) | untested | Not run in this codebase. Related external evidence exists for a specific slice — see N25 below (2-WR heavy personnel rate, computable via `load_participation()`) — but that is a different framing (inverse) and not run here either. | internal — `test-registry.md` #31 | No |
| T1-32 | Pre-snap motion rates | blocked (at player level) | Registry rates it Low edge / "largely arbitraged." External evidence agrees on both counts: McFarland reports a large per-play effect (WRs +45% PPR per route in motion) but **FTN's `is_motion` has no player attribution**, so it is unresolvable with free data at the player level the registry needs. Team-level motion rate is computable but a different, coarser object. | internal — `test-registry.md` #31/#32 note; external — `analyst-factor-sweep-2026-07-30.md` N23 [VERIFIED] | No |

---

## Section 3 — Tier 2, league-specific (our structural edge) (`docs/test-registry.md` #33–#42)

Nobody else does these, because they only matter in *our* league.

| # | Factor | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|---|
| T2-33 | Re-score all projections under this league's exact rules (yardage bonuses, −2 INT) | included | Positional value structure re-scored (`src/make_board.py` → `data/board_{season}.csv`). Player-level re-scoring still blocked by T0-2 (needs component-level projections). Directionally positive: mean +84.6 VBD, positive 3 of 4 seasons (dev+holdout), but **not statistically established at n=4** — sign-test floor p=0.125 (ADR-025, correcting an earlier reversed-sign claim). | internal — `test-registry.md` #33/§Tier2 note; `decisions.md` ADR-016/ADR-017/ADR-025 | Yes, partial (positional level only) |
| T2-34 | Replacement levels RB30 / WR40 / TE10 / QB10 | included | Shipped — `scoring.ReplacementLevels()` derived from measurement, used unmodified by board and backtest. Revised from RB28/WR41/TE11 by measurement (ADR-029); the change is inside measurement noise except at TE. | internal — `test-registry.md` #34; `decisions.md` ADR-029 | Yes |
| T2-35 | Global flex baseline (~80th flex-eligible replacement, one figure vs. per-position RB30/WR40/TE10) | rejected-with-evidence | **NULL** (PR-006). Season-paired realised-points margin +1.7 [−67.6,+74.8] at σ=10, −6.7 [−51.2,+37.8] at σ=20 — sign flips between noise settings, both CIs wide around zero, well under the ~8.5-pt simulation noise floor at 300 sims/cell. n=4 seasons is the binding constraint, not simulation count. No change to production `ReplacementLevels` (ADR-029 stays). | internal — `test-registry.md` #35; `docs/ranking/valuation-tests-35-36-precommit.md`; `docs/preregistration/PR-006-global-flex-baseline.md` | Yes |
| T2-36 | VONA with pick-gap awareness (3.5x alternation for `USER_SLOT=3`, vs. a gap-blind one-round constant) | rejected-with-evidence | **NULL on realised-points outcome** (PR-008): margin −37.2 [−118.8,+36.0] at σ=10, −2.8 [−48.0,+37.1] at σ=20, CIs include zero. **But decision-divergence CONFIRMED**: the two arms pick a different full roster in 100% of paired simulated drafts, every one of 8 season×σ cells — gap-awareness changes *which* player almost every time without reliably changing whether the resulting roster is better at this sample size. Secondary, uncorrected finding: this VONA formulation underperforms plain BPA-by-VBD by ~110–125 pts both σs (CIs exclude zero, but sign test floors at p=0.125 and doesn't survive BH) — a caution, not a confirmed loss. Not wired into any live strategy. | internal — `test-registry.md` #36; `docs/ranking/valuation-tests-35-36-precommit.md`; `docs/preregistration/PR-008-vona-pick-gap-awareness.md` | Yes |
| T2-37 | League-biased ADP (this league's format + manager priors vs. a generic 2WR/1FLEX/K Yahoo board) | untested | Not run. High edge rating is a prior, not a measurement. | internal — `test-registry.md` #37 | No |
| T2-38 | Bonus-threshold hit rates (does a player "clear" 100/150/200 more often than volume alone implies — a persistent "spike-week" trait) | rejected-with-evidence | **FALSIFIED** (PR-002). Receiving-100 WR YoY residual r = +0.041 [−0.018,+0.099], BH-adj p = 0.668. Rushing-100 RB r = +0.063 [−0.001,+0.124], BH-adj p = 0.336. 36 correlations run, 24 testable, **zero survived Benjamini-Hochberg**. n = 26 seasons, 1,541 WR pairs / 404 players — largest sample in the project. CI upper bounds cap the effect at ~1% of explained variance even optimistically — this rules a large effect out, not merely fails to find one. A regime-dependent near-miss (QB passing-300, 2012–2019: r=+0.265, raw p=0.002) reverses sign in 2020–2024 (r=−0.234) and was pre-committed to be disqualified by regime reversal. | internal — `test-registry.md` #38; `docs/preregistration/` PR-002 | Yes |
| T2-39 | No-kicker effect on pool depth (one extra skill player per team drafted) | untested | Not run. | internal — `test-registry.md` #39 | No |
| T2-40 | Post-draft players follow waiver rules (undrafted pool not instantly free — changes Wk 1 FAAB) | untested | Not run; manual/structural. | internal — `test-registry.md` #40 | No |
| T2-41 | IR restriction (no direct waiver → IR; stashing costs a bench spot, not an IR spot) | untested | Not run; manual/structural. | internal — `test-registry.md` #41 | No |
| T2-42 | Trade deadline Nov 28 (~Wk 12, caps the trade-to-improve path) | untested | Not run; manual/structural, Low edge rating (prior, not measured). | internal — `test-registry.md` #42 | No |

---

## Section 4 — Tier 5, considered and rejected without measurement (`docs/test-registry.md`)

Listed by the registry so the rejection is explicit and revisitable. None of these carry a
measured number — they are a priori scope judgments, which is why disposition is `excluded` rather
than `rejected-with-evidence`.

| Factor | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|
| Weather | excluded | Matters for in-season lineup decisions, not pre-draft ranking. Judgment call, no number. | internal — `test-registry.md` Tier 5 | No |
| QB–WR stacking correlation | excluded | A DFS concept; in redraft H2H it mainly adds variance rather than expected value. Judgment call, no number. | internal — `test-registry.md` Tier 5 | No |
| DFS ownership as a sentiment proxy | excluded | Different game, different incentives — ownership pressure doesn't exist in a redraft league. Judgment call, no number. | internal — `test-registry.md` Tier 5 | No |
| Beat-writer sentiment scoring | excluded | High effort, low signal, hard to validate. Judgment call, no number. | internal — `test-registry.md` Tier 5 | No |
| Nash-equilibrium drafting | excluded | Elegant, but opponents in this league aren't optimizing, so equilibrium is the wrong model for them. Judgment call, no number. | internal — `test-registry.md` Tier 5 | No |
| Coaching scheme fit (zone vs. gap) | excluded | Real effect in principle, judged too noisy to act on at draft time. Cross-check: external N26 (run-concept mix, McFarland 2016–2025) measured outside zone at 0.48 PPR/att, inside zone 0.47 — a near-tie that arguably supports this rejection, though it measures a narrower slice (run-concept mix, not zone-vs-gap scheme fit generally). | internal — `test-registry.md` Tier 5; external — `analyst-factor-sweep-2026-07-30.md` N26 [VERIFIED] (partial cross-check only) | No (as originally framed) |

---

## Section 5 — External analyst sweep, new rows (`docs/research/analyst-factor-sweep-2026-07-30.md`, N1–N34)

Commissioned by `FR-2026-07-30-widen-the-ranking-input-list`. ~25 fetches across 11 named analytics
shops. **Sample-quality caution that applies to every row in this section**: effective independence
across the 11 shops is ~6 (some share underlying datasets); every headline correlation in the source
material is measured on **survivors** (stated filters like "≥30 targets in consecutive seasons"),
which are upper bounds under `CLAUDE.md` §6.2, not our expected effect; and **not one of the 11 shops
publishes a comparison against market ADP** — a claim of r=0.79 can still be fully priced into ADP
already. None of these have been run in this project; "Computable here" in the source doc is not the
same as "run," and disposition is `untested` throughout this section unless noted otherwise.

| # | Factor | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|---|
| N1 | First-read target share (proxy: FTN `read_thrown` × PBP `receiver_player_id`) | untested | External: YoY self-corr 0.78, to next-season PPR FPG 0.79 (Heath, Fantasy Points). Contested by Hoopes (4for4): 23 rate stats topped out at YPRR 0.59, with prior-FPG itself the ceiling at 0.68 — a direct numerical contradiction with N1's 0.79. Computable as a proxy only, 2022–2025 (4 seasons), must be labelled proxied, not identical to Heath's charted definition. | external — `analyst-factor-sweep-2026-07-30.md` N1 [VERIFIED]; contest in §3 | No |
| N2 | Catchable target share / rate | untested | External: catchable-target share → fantasy points 0.948 vs. raw target share 0.944 — "essentially no gain" at share level, per the same shop's own number. Catchable *rate* YoY 0.41. FTN `is_catchable_ball`, 2022+. | external — N2 [VERIFIED] | No |
| N3 | Targets per route run (TPRR) | untested | External ×3 independent framings: Heath YoY 0.65 (R²=0.36 to next-season targets); Hoopes 0.53 to next-season FPG; Borgognoni — 92% of top-24 WR finishers since 2006 had TPRR ≥20%. Needs routes via `load_participation()` proxy, 2016+. | external — N3 [VERIFIED]×3 | No |
| N4 | First downs / route, and 1D-per-route-run | untested | External: 1D/RR 0.57 to next-season FPG — above TPRR (0.53), below YPRR (0.59), per Hoopes. First-downs component is directly computable now: PBP `first_down_pass`, 1999+, zero new joins (once PBP is ingested — see T0-10). | external — N4 [VERIFIED] | No |
| N5 | NGS average separation | untested | External: Heath's PASS self-corr 0.687, claimed more predictive than YPRR/1D-RR without counting stats. Reference table: target share 0.773, rec yards 0.693, total FP 0.686, YPRR 0.613, PASS 0.612. **Already in `nfl.db`**, `ngs_receiving` 2016–2025, 26,723 rows, **untouched by any model in this project.** | external — N5 [VERIFIED]; internal confirmation — `fr136-q1-bottom-up-assessment.md` §3.3 | No |
| N6 | Designed-target (screen) share | untested | External, and **the shop contradicts itself**: ~1.7 fantasy points each at 91.4% success, YoY 0.629 — but elsewhere the same shop calls designed targets "basically no relationship to fantasy points." FTN `is_screen_pass`, 2022+. | external — N6 [VERIFIED, self-contradictory] | No |
| N7 | Contested-catch rate, created receptions, drop rate | excluded | External, listed so we can decline with a citation rather than test: contested catches have "basically no value" per the shop's own finding; MTF/YAC "weak, positive." A reasoned decline backed by a cited (not our own) measurement — not run here. | external — N7 [VERIFIED] | No |
| N8 | Tight-window target rate | blocked | Named as a QB-model input by Hoopes (4for4) but no number was published for its contribution. Needs paid window-charting data. | external — N8 [VERIFIED use]/[GAP contribution] | No |
| N9 | QB rushing attempts per game | untested | External: 0.576 to next-season FPG — strongest single QB stat found; each of the top-9 most predictive QB stats measures rushing in whole or part, first pure passing metric (pass TDs) ranks 10th. **Computable today, zero new ingest** — carries already in `player_weekly_stats`. Researcher's #1-ranked recommendation: the board's 12 largest top-100 disagreements with consensus are all QB/TE, with no QB-specific input behind that tilt. | external — N9 [VERIFIED]; internal — `analyst-factor-sweep-2026-07-30.md` §5 rank 1 | No |
| N10 | Passing efficiency over volume (passer rating / EPA-per-dropback vs. attempts) | untested | External ×2: Heath — passer rating beats total attempts, completion% near bottom at 0.154; Bruchhaus (SumerSports) — EPA/dropback "stickiest QB stat since 2021," r≈0.60. Partly computable: `passing_cpoe` only 11% populated in `nfl.db`; EPA needs PBP ingest. | external — N10 [VERIFIED]×2 | No |
| N11 | Sack-avoidance rate | untested | External: r≈0.50 YoY, second-stickiest QB stat (SumerSports). Computable via PBP or `load_pfr_advstats` (2018+). | external — N11 [VERIFIED] | No |
| N12 | Game total / team spread as player-model features | blocked | External: team spread ranked 4th most important, game total 7th, in Hoopes's RB model. Same blocker as T0-11 — no odds table — and the whole team-environment channel is oracle-bounded at ≤ +0.055 τ_b. | external — N12 [VERIFIED]; internal ceiling — `fr136-q1-bottom-up-assessment.md` §6.6 | No |
| N13 | Explosive rush rate (≥10/15-yd share) | untested | External: "best balance of stickiness and predictive value" among RB efficiency stats (McFarland) — contrast, YAC-after-contact and MTF are stickiest but *lowest* correlation to next-season points. Computable, PBP, 1999+ (once ingested). Researcher's #4-ranked recommendation: RB is the one position where the internal component-model experiment has demonstrated statistical power (+0.134 [+0.043,+0.223] vs. ADP heuristic) and where the model itself is currently negative vs. ADP (−0.052) — power plus a deficit. | external — N13 [VERIFIED]; internal — `fr136-q1-bottom-up-assessment.md` §1.4, `analyst-factor-sweep-2026-07-30.md` §5 rank 4 | No |
| N14 | Red-zone / inside-10 / inside-5 **snap** rate (distinct from T0-10, which is red-zone *touches*) | blocked | External: "snap share in the red zone correlates better to raw fantasy points than any receiving usage stat" (Barfield). Needs `load_participation()` × PBP `yardline_100`, 2016+ — PBP not yet ingested. | external — N14 [VERIFIED] | No |
| N15 | Inside-5 TD conversion vs. base rate | untested | External: NFL average 43.0% inside the five (Smola, DraftSharks). Overlaps `load_ff_opportunity` (see T1-18). **Not** the same as T1-19 (TD-rate shrinkage), which was measured HARMFUL when discarded — this is base-rate context, a different question. | external — N15 [VERIFIED] | No |
| N16 | YAC per reception (RB) | untested | External: "clear best efficiency stat for RBs in the pass game" (Barfield); separate summary r=0.421. Computable, PBP `yards_after_catch`. | external — N16 [VERIFIED qual]/[SNIPPET number] | No |
| N17 | Receiving share of an RB's own points | untested | External: league-winner RB seasons 2016–2025, McFarland — receiving-heavy (≥50%) 32%, dual-threat (40–49%) 38%, balanced 15%, pure-rushing 15%; 70% of league-winning RB seasons came from ≥40% receiving share. Computable, re-scored under this league's rules. Interacts with archetype work outside this ledger's scope. | external — N17 [VERIFIED] | No |
| N18 | Snap-share persistence at threshold | untested | External: 72 of 128 (56%) RBs repeated ≥60% snap share YoY (McFarland). `snap_counts` 2013–2025, 324,611 rows, **unused** — same underlying data as T0-9. | external — N18 [VERIFIED]; internal — same gap as T0-9 | No |
| N19 | Late-season role trajectory by draft round / career year | untested | External: Day-2/rounds 4–5 rookies, +19% PPG and +14% snap share late-season; year 2–3, +1%; year 8–9, −5%; year 10+, −11% (McFarland). Computable from weekly stats + `draft_picks`. A late-season-weighting factor with no registry analogue. | external — N19 [VERIFIED] | No |
| N20 | Neutral-situation pass rate | untested | External: 2023 59.01%, 2024 57.30%, 2025 57.44% (Bodiford/PFF, Hoopes/4for4). **Distinct from T1-22 (PROE)** — a situational filter, not a model residual; cheaper and more interpretable. Computable via PBP once ingested. | external — N20 [VERIFIED] | No |
| N21 | Play-caller portability of tendency | blocked | External evidence is anecdote-only — "no R², no correlation, no stability number published" (Hoopes, asserted with two examples). `play_callers` table has zero rows in `nfl.db`. | external — N21 [SNIPPET]/anecdote | No |
| N22 | Coordinator-change effect | blocked | External: universally asserted "one of the most underpriced edges" by 5+ shops, but "not a single public backtest found" — a [GAP], not a finding. Same internal gate as T1-29/T1-30 (coordinator data unobtainable, PFR 403). Directly undermines registry's "High edge" rating for T1-29/T1-30, which is prior, not evidence. | external — N22 [GAP] | No |
| N23 | Pre-snap motion, player level | blocked | See T1-32 — this is the same finding, sourced. WRs in motion +45% PPR/route (McFarland); league-average motion rate 52%. Unresolvable at player level with free data (FTN `is_motion` has no player attribution). | external — N23 [VERIFIED] | No |
| N24 | Play-action rate | blocked (player level) | External ×2: McFarland — WRs +23% PPR/route on play-action; PFF — +0.054 EPA/play vs. −0.031, YPA 6.72→7.76. Computable team-level, 2022+; same player-attribution problem as N23 blocks a player-level version. | external — N24 [VERIFIED]×2 | No |
| N25 | 2-WR (heavy) personnel rate | untested | External: WRs +29% PPR vs. 3-WR personnel plays; league average 25%, top staffs 43–55% (McFarland). Inverse framing of T1-31 (personnel package trends), with a number attached that T1-31 lacks. Computable via `load_participation()` `offense_personnel`, 2016+. | external — N25 [VERIFIED] | No |
| N26 | Run-concept mix (zone vs. gap) | excluded | External: outside zone 0.48 PPR/att, inside zone 0.47 — gap concepts beat both (McFarland, 2016–2025). Registry Tier 5 already rejected the broader "coaching scheme fit" as too noisy; this specific 0.48-vs-0.47 near-tie arguably supports that rejection. Not from nflverse as a ready-made column. | external — N26 [VERIFIED]; cross-ref — Tier 5 "Coaching scheme fit" row above | No |
| N27 | Adjusted Line Yards / Adjusted Sack Rate | untested | External ×2: Edwards (4for4), team-level 2025 — ALY R²=0.431, ASR 0.384, YBC 0.324, blown-block 0.245, pressure 0.182, penalties 0.114, **OL continuity only 0.04** (see N28). Composite 0.462 (0.591 top/bottom-10 only). Smola (DraftSharks): ALY → RB rushing 0.314, "strongest between any pair of stats" in his pull. ALY is a public formula over PBP (once ingested) — same correction as T1-23. | external — N27 [VERIFIED]×2 | No |
| N28 | O-line continuity | rejected-with-evidence | External, and the evidence contradicts the shops' own prose: all assert it matters, but 4for4's own published table gives it **R²=0.04, the weakest of seven** O-line-adjacent stats tested. "Record the prior as ~zero." | external — N28 [VERIFIED — number contradicts prose in the same article] | No (this is a citation of an external measurement, not a run in this project) |
| N29 | Team passing-volume floor as a gate (not a weight) | untested | External: on teams at 200–224 passing YPG, only 3 of 108 WRs (3%) finished top-12; even at 24%+ target share, only 3 of 23 (13%) reached 16+ PPG (McFarland). A functional-form hypothesis (threshold gate) this project has never tested in any form. | external — N29 [VERIFIED] | No |
| N30 | Team win quality → elite-RB hit rate | untested | External: 11+ wins 40%, 9–10 32%, 7–8 27%, 5–6 9%, 0–4 wins 0% (McFarland, 2016–2025); no gradient found for mid-RB1. Realised wins are computable now as an **oracle upper bound only** (not a forecast); implied wins is odds-blocked, same as T0-11/N12. | external — N30 [VERIFIED] | No |
| N31 | Age as a bust hazard, not a decline curve | untested | External: on 100 retired top-50 RB/WR, exactly 50% declined in their final relevant season; only 17% showed two consecutive declines; survivor value almost completely flat across ages (Harstad, Footballguys). Argues aging curves are contaminated by survivorship. **This challenges T0-7's functional form directly** — registry frames age as "decline curves," which is precisely the specification this evidence argues against. A functional-form hypothesis, not a new variable. | external — N31 [VERIFIED]; cross-ref — T0-7 above | No |
| N32 | Multi-year games-missed model | untested | External: RMSE 3.6 games (1yr), 5.9 (2yr), 7.1 (3yr); top features slot snap%, snaps blocking, age, points/snap, ST snaps, snaps in motion, projected snaps, routes run, games missed past 3yrs, snaps hit (Chris Lee, Sports Info Solutions). Partly computable: age, ST snaps, projected snaps, games-missed history — yes; charting features — no. **The researcher's own caution travels with this row**: no naive baseline was published by the source; "everyone plays 17" must be beaten before 3.6 games RMSE means anything. | external — N32 [VERIFIED] | No |
| N33 | Team adjusted games lost | untested | External: YoY correlation 0.33 back to 2010 (Football Outsiders via PFF). Exact FO definition not obtained — secondary source only. | external — N33 [SECONDARY] | No |
| N34 | Combine athleticism (Speed Score, Burst, Agility) | untested | External: formulas published (PlayerProfiler, Barnwell); **no predictive evidence published for any of them.** Computable free via `load_combine()`. "Enter with no prior" — cheap to compute is not evidence it works. | external — N34 [VERIFIED formulas]/[GAP predictiveness] | No |

### Section 5b — Definition-only, evidence-absent (analyst sweep §2f)

Listed individually so none is mistaken for a tested factor. All eight are PlayerProfiler
proprietary metrics with published formulas and **no published validation of any kind**. Several
are cheaply computable; the source document is explicit that none should be tested before the
evidence-bearing N-rows above.

| Factor | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|
| Target Premium | untested | Definition published, no predictive evidence published anywhere reached. | external — `analyst-factor-sweep-2026-07-30.md` §2f [GAP] | No |
| Weighted Opportunities | untested | Same. | external — §2f [GAP] | No |
| True Yards Per Carry | untested | Same. | external — §2f [GAP] | No |
| Production Premium | untested | Same. | external — §2f [GAP] | No |
| Lifetime Value | untested | Same. | external — §2f [GAP] | No |
| Value Over Stream | untested | Same. | external — §2f [GAP] | No |
| Juke Rate | untested | Same. | external — §2f [GAP] | No |
| Breakout Rating | untested | Same. | external — §2f [GAP] | No |

---

## Section 6 — Yardage-bonus ceiling/variance preference (`CLAUDE.md` §7)

A single hypothesis tested four independent ways, kept as one row rather than four to avoid
inflating the multiplicity denominator with restatements of the same claim.

| Factor | Disposition | Reason | Provenance | Ever run? |
|---|---|---|---|---|
| Do the stacking yardage bonuses imply a variance/ceiling preference that should influence how rankings value volatility? | rejected-with-evidence | **Four independent instruments, all NULL, at the bonus structure's most favourable measurement setting.** (1) WR ceiling ablation: perfect foresight of every WR's bonus points would improve rank correlation by only +0.026 — the hard ceiling on the whole idea; the model actually built to capture it achieved +0.0002. (2) RB stacking-bonus transfer: worth 0.57%–2.39% of realised points, moves only 3 players by ≥3 rank positions across 4,792 player-seasons. (3) Per-player dispersion in the exceedance curve: NULL at every threshold, family, and shrinkage setting tested — with both arms given the *realised* mean, the most favourable setting available. (4) Skewness and kurtosis (the founder's own proposed mechanism): fails upstream — shape does not persist year to year, six of six NULL; empirical-Bayes τ̂² driven to exactly zero (no between-player variance in true shape beyond sampling noise); an oracle arm using the target season's own shape makes bonus error *worse*. Per `CLAUDE.md` §7: "Do not re-derive a variance preference from the bonus structure. It has been tested four ways, including at its most favourable setting, and there is nothing there." | internal — `CLAUDE.md` §7; `docs/ranking/component-model-wr-pass-1.md` §6.2; `docs/ranking/component-model-rb-qb-te-pass-1.md` §6; `docs/ranking/fr086-volatility.md` §3.4; `docs/strategic-insights.md` §5b | Yes, four times |

---
