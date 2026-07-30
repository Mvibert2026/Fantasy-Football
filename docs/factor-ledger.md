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

| Disposition | Count |
|---|---|
| included | 21 |
| excluded | 9 |
| untested | 46 |
| blocked | 13 |
| rejected-with-evidence | 12 |
| **Total** | **101** |

(Counts finalized after all sections are written; see bottom of document for the as-built total,
which should match this table — if it does not, the table below is stale and the bottom count
governs.)

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
