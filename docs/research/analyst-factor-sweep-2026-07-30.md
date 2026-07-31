# Widening the ranking-input list — external analyst research

Researcher, 2026-07-30, commissioned by FR-2026-07-30-widen-the-ranking-input-list.
Persisted by PM: the researcher agent has no shell and the harness refuses its report writes.

**~25 fetches across 11 named analytics shops.** Blocked hosts (Yahoo, ESPN/Disney, Reddit, PFR)
were not attempted. No fetch was blocked and routed around.

---

## 0. Sample quality — read before the factor list

| Property | Assessment |
|---|---|
| Independent shops reached | 11 |
| Shops publishing an actual **number** | **6** |
| **Effective independence** | **~6, numeric backbone ~4.** SumerSports' WR stability numbers are computed *on Reception Perception data* — Eager and Harmon are one measurement. Fantasy Points' four position articles are one proprietary charting dataset, two authors. 4for4's four are one modeller, one pipeline |
| **Survivorship** | **Every headline correlation is measured on survivors**, filters stated: "≥30 targets in consecutive seasons", "100+ key snaps in consecutive seasons", "min 235 sampled routes each year". None retains busts. Under §6.2 these are **upper bounds, not our expected effect** |
| **The bar nobody clears** | **Not one shop publishes a comparison against market ADP.** Every number is stat→stat or stat→next-season-FPG on a qualified population. §6.5's baseline #1 is unaddressed across the entire public literature reached. A factor with r=0.79 can still be fully priced into ADP |
| Non-representativeness | Literature is overwhelmingly WR-centric. QB has one systematic treatment, TE almost none. **All four 4for4 models rank market ADP as their single most important input** — the shops we would "beat" are themselves consensus-anchored. Convergent with ranker's finding, which is exactly when to distrust it |

---

## 1. Computability corrections — highest-leverage output of this pass

Four places where `docs/test-registry.md` states a cost that is **wrong**.

| Registry item | Registry says | Actually true | Tag |
|---|---|---|---|
| **#18 xFP**, effort **H**, "highest-value unbuilt Tier 1 item" | Must be built | **A free prebuilt xFP model exists**: `nflreadpy.load_ff_opportunity()` — ffverse `ffopportunity`, xgboost over nflverse PBP, **2006–current**, versioned. **Effort H → a download** | [VERIFIED] |
| **#16 YPRR / #17 route participation**, tagged `nflverse:FTN`, "2022+" | FTN supplies them | **FTN charting has no per-player columns at all** — 28 columns, play-level only, no receiver ID, no routes-run. YPRR and route participation are **not obtainable from FTN**. Real source is `load_participation()` (`offense_players` per play), **2016–current**. **Ten seasons, not four** — the wrong tag has been suppressing these tests | [VERIFIED] |
| **#23 O-line**, `external` | External source needed | **Adjusted Line Yards is a published formula over PBP.** Also `load_pfr_advstats()` (2018+) ships yards-before-contact, broken tackles, drops, pressure/hurry/blitz free — no PFR scrape, no 403 | [VERIFIED] |
| **#27 contract year** | `nflverse (contracts)` | Confirmed. Also present and unused project-wide: `load_combine()`, `load_officials()`, `load_trades()` | [VERIFIED] |

---

## 2. New factor rows — registry-ready

### 2a. Pass-catcher opportunity — strongest evidence in the pull

| # | Factor | Who | Claim | Tag | Computable here |
|---|---|---|---|---|---|
| N1 | **First-read target share** | Ryan Heath, Fantasy Points | YoY self-corr **0.78**; to next-season PPR FPG **0.79**. Top-20 by it average **16.2 FPG** vs 15.7 by ordinary target share | [VERIFIED] | **Yes, as a proxy** — FTN `read_thrown` × PBP `receiver_player_id`. **2022–2025 only.** Not identical to Heath's charted definition. **Must be labelled proxied** |
| N2 | **Catchable target share / rate** | Heath / Barfield, Fantasy Points | Catchable targets **0.948** to fantasy points vs **0.944** raw targets — **essentially no gain** at share level. Catchable *rate* 0.364, YoY 0.41 | [VERIFIED] | Yes, FTN `is_catchable_ball`, 2022+. The shop's own number says the share version buys ~nothing |
| N3 | **Targets per route run** | Fantasy Points; 4for4; Fantasy Footballers; Fantasy Life | Heath: YoY **0.65**, R²=0.36 predicting next-season targets. Hoopes: **0.53** to next-season FPG. Borgognoni: **92% of top-24 finishers since 2006 had TPRR ≥20%** | [VERIFIED] ×3 | Partly — needs routes via `load_participation()` proxy, 2016+ |
| N4 | **First downs, and 1D per route run** | Stephen Hoopes, 4for4 | 1D/RR **0.57** to next-season FPG — **above TPRR (0.53)**, below YPRR (0.59) | [VERIFIED] | **Yes for first downs** — PBP `first_down_pass`, 1999+, zero new joins |
| N5 | **NGS average separation** | Heath, Fantasy Points; NGS | Heath's PASS self-corr **0.687**, claimed more predictive than YPRR/1D-RR *without counting stats*. Reference table: target share 0.773, rec yards 0.693, total FP 0.686, YPRR 0.613, PASS 0.612 | [VERIFIED] | **Yes, already in `nfl.db`** — `ngs_receiving` 2016–2025, 26,723 rows, **untouched by any model** |
| N6 | **Designed-target (screen) share** | Heath, Fantasy Points | ~**1.7 fantasy points each** at **91.4%** success; YoY **0.629**. Elsewhere same shop: designed targets have **"basically no relationship to fantasy points"** | [VERIFIED] — **shop contradicts itself** | Yes, FTN `is_screen_pass`, 2022+ |
| N7 | Contested-catch rate, created receptions, drop rate | Fantasy Points | Contested catches **"basically no value"**; MTF and YAC "weak, positive" | [VERIFIED] | Yes — **listed so we can decline with a citation rather than test** |
| N8 | Tight-window target rate | Hoopes, 4for4 (TE model input) | Named input, **no number published** | [VERIFIED] use; [GAP] contribution | **No** — needs paid window charting |

### 2b. Quarterback — the registry contains **zero** QB-specific factors

| # | Factor | Who | Claim | Tag | Computable |
|---|---|---|---|---|---|
| N9 | **QB rushing attempts per game** | Rich Hribar ("Konami Code"); Heath | **0.576** to next-season FPG — **strongest single QB stat**. Each of the top-9 most predictive QB stats measures rushing in whole or part; first pure passing metric (pass TDs) appears **10th** | [VERIFIED] | **Yes today, zero ingest** — carries already in `player_weekly_stats` |
| N10 | **Passing efficiency over volume** | Heath; Bruchhaus, SumerSports | Heath: passer rating beats total pass attempts; completion % near bottom at **0.154**. Bruchhaus: EPA/dropback **stickiest QB stat since 2021, r≈0.60** | [VERIFIED] ×2 | Partly — `passing_cpoe` only **11% populated**; EPA needs the PBP ingest |
| N11 | **Sack-avoidance rate** | SumerSports | r≈**0.50** YoY, second-stickiest | [VERIFIED] | Yes — PBP or `load_pfr_advstats` 2018+ |
| N12 | Game total / team spread as player-model features | Hoopes, 4for4 | Team spread **4th most important** in his RB model, game total **7th** | [VERIFIED] | **No** — same blocker as registry #11; ranker bounded the whole channel at **≤ +0.055 τ_b** |

### 2c. Running back

| # | Factor | Who | Claim | Tag | Computable |
|---|---|---|---|---|---|
| N13 | **Explosive rush rate** (≥10/15 yd share) | Dwain McFarland, Fantasy Life | **Best balance of stickiness and predictive value** among RB efficiency stats. Contrast: YAC-after-contact and MTF are **stickiest but lowest correlation to next-season points** | [VERIFIED] | Yes — PBP, 1999+ |
| N14 | **Red-zone / inside-10 / inside-5 _snap_ rate** | Graham Barfield, Fantasy Points | **"Snap share in the red zone correlates better to raw fantasy points than any receiving usage stat"** | [VERIFIED] | Yes, 2016+ — `load_participation()` × PBP `yardline_100`. **Different object from registry #10**, which is touches |
| N15 | Inside-5 TD conversion vs base rate | Jared Smola, DraftSharks | NFL average **43.0%** inside the five | [VERIFIED] | Yes — overlaps `load_ff_opportunity`; **not** registry #19, which was TD-rate shrinkage and measured HARMFUL |
| N16 | **YAC per reception (RB)** | Barfield, Fantasy Points | **"Clear best efficiency stat for RBs in the pass game"**; separate summary r=**0.421** | [VERIFIED] qual; [SNIPPET] number | Yes — PBP `yards_after_catch` |
| N17 | **Receiving share of an RB's own points** | McFarland, Fantasy Life 2016–2025 | League-winner RB seasons: receiving-heavy ≥50% **32%**, dual-threat 40–49% **38%**, balanced **15%**, pure rushing **15%** — **70% of league-winning RB seasons came from ≥40% receiving share** | [VERIFIED] | Yes — re-scored under our rules. Interacts with archetype work |
| N18 | Snap-share persistence at threshold | McFarland | **72 of 128 (56%)** repeated ≥60% snap share | [VERIFIED] | Yes — `snap_counts` 2013–2025, 324,611 rows, **unused** |
| N19 | **Late-season role trajectory by draft round / career year** | McFarland | Day-2 and rounds 4–5: **+19% PPG, +14% snap share** late. Year 2–3: +1%. Year 8–9: **−5%**; year 10+: **−11%** | [VERIFIED] | Yes — weekly stats + `draft_picks`. **A late-season-weighting factor; the registry has nothing like it** |

### 2d. Structural — where provenance is weakest, stated up front

| # | Factor | Who | Claim | Tag | Computable |
|---|---|---|---|---|---|
| N20 | **Neutral-situation pass rate** | Bodiford, PFF; Hoopes, 4for4 | 2023 **59.01%**, 2024 **57.30%**, 2025 **57.44%**. Exposes schematic identity free of game script | [VERIFIED] | Yes — PBP. **Distinct from #22 PROE**: situational filter, not model residual. Cheaper and more interpretable |
| N21 | Play-caller portability of tendency | Hoopes, 4for4 | Asserted with two examples. **No R², no correlation, no stability number published** | **[SNIPPET]/anecdote** | Blocked — `play_callers` has **zero rows** here |
| N22 | **Coordinator-change effect** | Establish The Run, DraftSharks, RotoWire, PFF, Fantasy Points — everyone | Universally asserted "one of the most underpriced edges" | **[GAP] — not a single public backtest found** | Blocked. **Registry rates #29/#30 High edge; that rating has no external evidential support** |
| N23 | Pre-snap motion, player level | McFarland | **WRs in motion +45%** PPR per route; league avg 52% | [VERIFIED] | **No at player level** — FTN `is_motion` has no player attribution. Registry #32 rates it Low/arbitraged; PFF's team numbers support the registry. **Unresolvable with free data** |
| N24 | **Play-action rate** | McFarland; Bodiford, PFF | McFarland: WRs **+23%** PPR per route. PFF: **+0.054 EPA/play vs −0.031**; YPA 6.72→7.76 | [VERIFIED] ×2 | Yes team-level, 2022+. Player attribution same problem as N23 |
| N25 | **2-WR (heavy personnel) rate** | McFarland | WRs **+29%** vs three-WR plays; league avg 25%, top staffs 43–55% | [VERIFIED] | Yes, 2016+ — `load_participation()` `offense_personnel`. Inverse framing of registry #31, with a number |
| N26 | Run-concept mix (zone vs gap) | McFarland 2016–2025 | Outside zone **0.48 PPR/att**, inside zone **0.47** — gap concepts beat both | [VERIFIED] | **Not from nflverse.** Registry Tier 5 rejected this as "too noisy"; **the 0.48-vs-0.47 gap arguably supports the rejection** |
| N27 | **Adjusted Line Yards / Adjusted Sack Rate** | Edwards, 4for4; Smola, DraftSharks | Edwards team-level 2025: ALY **R²=0.431**, ASR 0.384, YBC 0.324, blown-block 0.245, pressure 0.182, penalties 0.114, **OL continuity 0.04**. Composite 0.462 (0.591 on top/bottom-10). Smola: ALY→RB rushing **0.314**, "strongest between any pair of stats" | [VERIFIED] ×2 | **ALY yes** — public formula over PBP. PFF grades / ESPN win rates no |
| N28 | O-line continuity | 4for4, Fantasy Footballers, DraftSharks | All assert it matters. **4for4's own table: R²=0.04, weakest of seven** | [VERIFIED] — **number contradicts the prose in the same article** | Yes. **Record the prior as ~zero** |
| N29 | **Team passing-volume floor as a _gate_** | McFarland | On teams at 200–224 passing YPG, **3 of 108 WRs (3%)** finished top-12; even at 24%+ target share, **3 of 23 (13%)** reached 16+ PPG | [VERIFIED] | Yes. **A functional form this project has never tested — a gate, not a weight** |
| N30 | Team win quality → elite-RB hit rate | McFarland 2016–2025 | 11+ wins **40%**, 9–10 **32%**, 7–8 **27%**, 5–6 **9%**, **0–4 wins 0%**. No gradient for mid-RB1 | [VERIFIED] | Realized wins yes, **as oracle upper bound only**; implied wins is odds-blocked |

### 2e. Age, availability, risk

| # | Factor | Who | Claim | Tag | Computable |
|---|---|---|---|---|---|
| N31 | **Age as a bust _hazard_, not a decline curve** | Adam Harstad, Footballguys | On 100 retired top-50 RB/WR: **exactly 50%** declined in their final relevant season; only **17%** showed two consecutive declines; **survivor value almost completely flat** across ages. Aging curves are contaminated by survivorship; mortality tables self-cull | [VERIFIED] | Yes. **Registry #7 is "age → decline curves" — precisely the specification Harstad argues is wrong. A functional-form hypothesis, not a new variable** |
| N32 | Multi-year games-missed model | Chris Lee, Sports Info Solutions | RMSE **3.6 games (1yr), 5.9 (2yr), 7.1 (3yr)**. Top features: slot snap %, snaps blocking, age, points/snap, ST snaps, snaps in motion, projected snaps, routes run, games missed past 3 yrs, snaps hit | [VERIFIED] | Partly — age, ST snaps, projected snaps, games missed yes; charting features no. **Researcher's own caution: they publish no naive baseline. "Everyone plays 17" must be beaten before 3.6 means anything** |
| N33 | Team adjusted games lost | Football Outsiders via PFF | YoY correlation **0.33** back to 2010 | **[SECONDARY]** | Partly; exact FO definition not obtained |
| N34 | Combine athleticism (Speed Score, Burst, Agility) | PlayerProfiler; Barnwell | **Formulas only. No predictive evidence published** | [VERIFIED] formulas; [GAP] predictiveness | Yes, free — `load_combine()`. **Enter with no prior** |

### 2f. Definition-only, evidence-absent — listed so they are not mistaken for findings

`Target Premium`, `Weighted Opportunities`, `True Yards Per Carry`, `Production Premium`, `Lifetime Value`, `Value Over Stream`, `Juke Rate`, `Breakout Rating` — all PlayerProfiler, all published definitions, **no published validation whatsoever**. Several cheaply computable. **Do not test before the evidence-bearing rows above.**

---

## 3. Where analysts disagree — the contested set

| Contest | Side A | Side B | Read |
|---|---|---|---|
| **Does anything beat prior FPG?** | Heath: first-read target share **0.79** | Hoopes, 23 rate stats: the **ceiling is prior FPG itself at 0.68**; best rate stat YPRR 0.59 | **Direct numerical contradiction.** 0.79 exceeds Hoopes's entire list. Either samples differ materially (Heath's filters unstated) or first-read share is the best public WR input. **Resolving it is a real test, either answer worth having** |
| **Efficiency: sticky ≠ predictive** | McFarland: YAC-after-contact and MTF are **stickiest** | Same author: they have the **lowest** correlation to next-season points | **A methodology finding that applies directly to us.** `factor-batch-1-results.md` reports YoY *persistence*. Persistence was never the question |
| Pre-snap motion | McFarland **+45%** | Registry #32 Low/arbitraged; PFF EPA −0.042→+0.002 | Both true — a large per-play effect on a near-universal tactic is what "arbitraged" means. **#32's Low rating stands** |
| Designed/screen targets | Heath: ~1.7 pts, floor-raising | Same shop: **"basically no relationship"** | **One shop contradicts itself.** Floor-vs-total is the likely reconciliation and is testable |
| **Vacated targets** | Everyone's offseason content; registry #28 rates **High** | Multiple skeptics: "not in the least bit predictive", "the snake oil of fantasy football" | **Our own #28 came back harmful on a proxy.** Skeptics agree directionally. **Registry's High rating is not externally supported** |
| O-line continuity | Every article's prose | 4for4's own table: **R²=0.04** | Prose and table disagree inside one article. **Prior ~zero** |
| Second-year WR leap | p = 0.0175 / 0.0258 claimed | Registry #53 flags it a multiple-comparisons trap | [SNIPPET] only; p-values are exactly the shape §6.3 warns about. **No change to #53** |

---

## 4. Explicit gaps

| Question | Status |
|---|---|
| A public backtest quantifying the coordinator-change effect | **[GAP]** — universally asserted, never measured publicly in anything reached |
| Establish The Run's projection methodology | [GAP] |
| Preseason Vegas implied total → next-season fantasy, backtested | [GAP] |
| **Whether any shop beats market ADP, measured** | **[GAP], and the most important one. Zero of eleven publishes it** |
| Football Outsiders' AGL primary source | [GAP] — reached only via PFF citation |
| PlayerProfiler validation for ~8 proprietary metrics | [GAP] |

**Fetching vs redistributing.** Article pages rendered, which permits reading a *methodology*. It does
not give us their per-player *values* — Fantasy Points Data, PFF, SIS and Reception Perception are paid
products and the values are the product. Everything marked computable is computable because **we would
recompute an approximation from nflverse**, never because we can take theirs. Any factor shipped that is
proxied off a paid definition (N1, N2, N3, N6) **must be labelled a proxy on screen**, not as the named
metric.

---

## 5. If only five could be tested — the researcher's call

Chosen against four constraints at once: attacks the *diagnosed* gap (within-position ordering);
buildable from `nfl.db` or a sub-minute fetch; external evidence stronger than assertion; not already
measured NULL here.

| Rank | Factor | Why |
|---|---|---|
| **1** | **QB rushing attempts per game** (N9) | Cheapest real test in the list — **data already in `nfl.db`, zero ingest**. Strongest single-stat claim at any position. And it lands where the board is most exposed: **all twelve of the board's largest top-100 disagreements with consensus are QBs or TEs**, produced by a positional tilt with **no QB-specific input behind it. The board is already making its biggest bets at QB blind** |
| **2** | **NGS average separation** (N5) | Already in `nfl.db`, **untouched**, **10 seasons** — best sample-length-to-cost ratio available. The only in-database signal **not derived from box-score volume**, so least likely to be collinear with what consensus already prices |
| **3** | **First-read target share** (N1, proxied) | Strongest published claim in the pull, **and** a live contradiction against 4for4's measured 0.68 ceiling. Earliest point in the causal chain — play-caller intent before execution — exactly what consensus rank cannot contain. **Two honest costs must travel with any result: 4 seasons, and ours is a proxy** |
| **4** | **Explosive rush rate** (N13) | RB is the **one position where our experiment has demonstrated power** (+0.134 [+0.043,+0.223]) and where the component model is **negative vs ADP (−0.052)**. Power plus a deficit = most measurable and most needed |
| **5** | **Prior points _per game played_, not season total** | Least glamorous, highest EV. Hoopes measures prior FPG at **0.68 — above all 23 of his rate stats**. Our §6.5 baseline #2 is a season *total*, silently blending rate and availability. Splitting them is nearly free and is the same decomposition ranker's oracle ladder found. **Changes what every future factor must beat, so testing it late would waste the other four** |

**Deliberately not first:** anything coaching/coordinator (no public backtest exists anywhere reached —
the registry's High rating is unsupported prior); motion/play-action/personnel at player level (free data
cannot attribute them); the PlayerProfiler set (cheap to compute is not a reason to test); contested
catches and drop rate (their own advocates say they are worthless — cite and skip).

**The one item outranking all five on expected value, flagged separately as a cost correction rather
than a new factor:** `load_ff_opportunity()` makes registry **#18 (xFP)** a download of a prebuilt,
versioned, 2006–current model rather than an H-effort build. If one action is taken before any test
runs, it is re-costing #18 from H to L and re-tagging **#16/#17 off `nflverse:FTN` — which cannot supply
them — onto `load_participation()`, 2016+, ten seasons instead of four.**
