# Factor batch 2 — results

**Ranker, 2026-07-30.** Runs registry **#28** (vacated targets and carries, on real pre-season
rosters) and **#29** (coordinator continuity, on preseason-dated staff). Both are the factors behind
the founder's own two examples of what a bottom-up ranking should be able to *say*
(`docs/founder-requests/FR-2026-07-30-bottom-up-must-produce-causal-insights-new-oc-de.md`).

Design fixed in `docs/ranking/factor-batch-2-precommit.md`, content committed **`851a6bb`
(2026-07-30 20:00:54) before any arm was fitted**; marker commit `70bc893` records why that commit's
message belongs to another agent's `git add -A`. Two amendments were made **before fitting** and are
dated inside that document: the V4 mover definition, and a correction of the E1b season count from
11 to 7 with the FDR family moved back to E1a.

15 pre-registered tests, BH at q = 0.10 across all 15. Sealed 2025 holdout **not opened**.

Reproduce:

```
.venv/bin/python -m experiments.bottomup.factors.coord_preseason --start-season 2012 --end-season 2024
.venv/bin/python -m experiments.bottomup.factors.run_factors2          # the 15 registered tests
.venv/bin/python -m experiments.bottomup.factors.diagnostics2          # the post-hoc splits
.venv/bin/python -m experiments.bottomup.factors.coord_join_diagnostic # the coach_id join check
```

---

## 1. Conclusion first — three answers, one of them a trap I set for myself and fell into

### (1) Batch 1's #28 harm was a proxy artifact. Measured directly, not argued.

Batch 1 graded #28 **HARMFUL at RB (+0.203 carries MAE)** and reported it as blocked rather than
null, because the vacancy had to be measured off a Week-1 depth chart. Re-run on `rosters_weekly`,
same harness, same seasons, same everything else:

| | V1 depth-chart proxy (batch 1) | **V2 real rosters** | **V2 − V1, paired, 11 seasons** |
|---|---|---|---|
| **RB** `carries` | **+0.2031** HARMFUL | **−0.0123** NULL | **−0.2154 [−0.3003, −0.1384], p = 0.0006** |
| TE `targets` | +0.0448 HARMFUL | +0.0153 NULL | −0.0295 [−0.0552, −0.0043], p = 0.056 |
| WR `targets` | +0.0818 NULL | +0.0284 NULL | −0.0534 [−0.1557, +0.0507], p = 0.362 |

**The V1 column reproduces batch 1's table to four decimal places** (+0.0818 / +0.0448 / +0.2031),
so this is one harness measuring two data sources, not two harnesses measuring one factor.

The mechanism batch 1 hypothesised is confirmed by the split it proposed (`diagnostics2`, post-hoc):

| RB `carries` MAE, by measured-vacancy tercile | n | primary | arm | Δ |
|---|---|---|---|---|
| V1 proxy, **high vacancy** | 475 | 56.57 | 57.34 | **+0.770** |
| **V2 rosters, high vacancy** | 475 | 55.20 | 55.26 | **+0.064** |

**92% of the harm in the contaminated bucket disappears.** TE shows the same shape (+0.145 → +0.040).

The two measures genuinely disagree — this is not a re-run of the same numbers. |V2 − V1| > 0.05 for
**32–35% of player-seasons** at every position, V2 is systematically *lower* (the depth chart
over-states vacancy, as predicted), and the two sources disagree about whether a player even changed
club for 85 / 1,441 RB, 140 / 2,271 WR and 66 / 1,041 TE player-seasons.

**But V2 is NULL at all three positions.** So the honest headline is both halves at once: *the harm
was an artifact of the data source, and the factor still earns nothing.* Registry #28 moves from
**BLOCKED** to **measured and NULL** — which is a real result, and a different one from "harmful."

### (2) Registry #29 is no longer gated, the `coach_id` join works, and "new OC" is NULL.

`play_callers_preseason`, built this session, covers **2012–2024, 416 team-seasons, 803 OC+DC rows**, all 32 clubs.
`oc_known` is **0.995 / 0.992 / 0.997** on the ADP board at WR / TE / RB — far above the 0.80
coverage gate committed in advance, so C1 is a genuine test and not a data failure.

| | E1a full universe | 95% CI | p | E1b ADP board | grade |
|---|---|---|---|---|---|
| WR `targets` | −0.0055 (−0.02%) | [−0.0324, +0.0220] | 0.713 | **+0.1274** | **NULL** |
| TE `targets` | −0.0031 (−0.02%) | [−0.0346, +0.0315] | 0.868 | **+0.1513** | **NULL** |
| RB `carries` | +0.0932 (+0.19%) | [−0.0637, +0.2406] | 0.288 | **+0.1470** | **NULL** |

Not underpowered-null: the OC changes in **46–48% of board player-seasons**, so there is no shortage
of contrast. Whatever a new coordinator does to a player's opportunity, this model cannot see it in
targets or carries.

**Consequence, under the rule committed in advance: the "new OC" sentence may not render.** See §5.

### (3) My own registered M1 arm was mis-specified, the escape hatch caught it, and the two SURVIVES are not what they look like.

M1 ("this player moved clubs") is the only thing in the batch that clears BH — at **all three**
positions, with the largest effects in either factor batch:

| | E1a | % of primary error | p | E1b | registered grade |
|---|---|---|---|---|---|
| WR `targets` | **−0.5783** | **−2.40%** | 0.0001 | −0.1584 | PROJECTION-ONLY |
| TE `targets` | **−0.3395** | −1.73% | 0.0006 | −0.1261 | **SURVIVES** |
| RB `carries` | **−0.9477** | −1.91% | 0.0001 | −0.3547 | **SURVIVES** |

**WR's −2.40% exceeds the 2%-of-primary-error trigger I committed in advance to treat as suspected
leakage rather than as a win.** It fired. The decomposition it forced:

| | **M1 registered** (`moved_club` + `move_known`) | **M1a `move_known` only** | **M1b `moved_club` only** |
|---|---|---|---|
| WR | −0.5783 (−2.40%) | **−0.5510 (−2.29%)** | −0.0104, p = 0.28 |
| TE | −0.3395 (−1.73%) | **−0.3174 (−1.62%)** | +0.0137, p = 0.62 |
| RB | −0.9477 (−1.91%) | **−0.9036 (−1.82%)** | +0.0991, p = 0.12 |

**95–97% of the effect is `move_known`, and `moved_club` — the variable the arm is named after and
the only one the founder's example is about — does nothing at any position.**

`move_known = 0` means the player is on **no** club's Week-1 roster: 34.1% of the WR universe, 28.1%
of TE, 34.2% of RB. The arm's gain is the model learning *"this player is not in the league, project
near zero."* That is true, large, and completely uninformative about vacated opportunity.

**I built this defect.** `move_known` was added as a companion "we know his club" flag by analogy
with batch 1's `vac_team_known`, which was computed but never entered a model. Here it entered the
model and turned out to be the treatment. **The registered grades above stand as recorded** — that
is what pre-registration is for — but **no claim about player movement may be drawn from them**, and
the SURVIVES rows must never be quoted without this paragraph.

**The residue is a real finding for someone else.** "Is this player on an NFL Week-1 roster" is worth
1.6–2.3% of component MAE and the availability sub-model does not use it. That belongs to
availability, not to #28, and it is handed over rather than claimed here.

---

## 2. The registered table — all 15, plus 3 reference rows

E1a = out-of-sample MAE of the one component declared per cell in advance, full universe, arm −
primary, paired by season, 11 seasons, season-block bootstrap 4,000 reps. **Negative = better.**
E1b = the same on the ADP board, 7 seasons — a required direction check, not the significance test.
E2 = ADP-board Spearman, 7 seasons, known underpowered at WR and TE before it was run.

| # | pos | arm | E1a | 95% CI | p | BH q=.10 | E1b | E2 | grade |
|---|---|---|---|---|---|---|---|---|---|
| 1 | WR | **V2** departure share (team, real rosters) | +0.0284 | [−0.0469, +0.1083] | 0.512 | n | +0.0352 | −0.0027 | NULL |
| 2 | TE | **V2** departure share | +0.0153 | [−0.0102, +0.0482] | 0.359 | n | −0.0103 | −0.0007 | NULL |
| 3 | RB | **V2** departure share | −0.0123 | [−0.0415, +0.0151] | 0.447 | n | −0.0427 | −0.0001 | NULL |
| 4 | WR | **V3** absence share (team, real rosters) | +0.0361 | [−0.0406, +0.1312] | 0.460 | n | +0.1262 | +0.0001 | NULL |
| 5 | TE | **V3** absence share | +0.0406 | [+0.0189, +0.0634] | 0.0067 | **Y** | +0.1869 | +0.0036 | **HARMFUL** |
| 6 | RB | **V3** absence share | +0.0327 | [−0.0087, +0.0733] | 0.178 | n | −0.0106 | −0.0029 | NULL |
| 7 | WR | **V4** opportunity ahead of me (player) | +0.0773 | [+0.0090, +0.1591] | 0.086 | n | +0.0735 | −0.0000 | MARGINAL-HARMFUL |
| 8 | TE | **V4** opportunity ahead of me | −0.0065 | [−0.0602, +0.0621] | 0.851 | n | −0.1140 | +0.0000 | NULL |
| 9 | RB | **V4** opportunity ahead of me | −0.0804 | [−0.1976, +0.0045] | 0.174 | n | +0.0164 | −0.0001 | NULL |
| 10 | WR | **M1** moved clubs (player) † | −0.5783 | [−0.7534, −0.4338] | 0.0001 | **Y** | −0.1584 | −0.0004 | PROJECTION-ONLY † |
| 11 | TE | **M1** moved clubs † | −0.3395 | [−0.4813, −0.2249] | 0.0006 | **Y** | −0.1261 | +0.0124 | **SURVIVES** † |
| 12 | RB | **M1** moved clubs † | −0.9477 | [−1.2586, −0.6872] | 0.0001 | **Y** | −0.3547 | +0.0080 | **SURVIVES** † |
| 13 | WR | **C1** new offensive coordinator (player) | −0.0055 | [−0.0324, +0.0220] | 0.713 | n | +0.1274 | −0.0020 | NULL |
| 14 | TE | **C1** new offensive coordinator | −0.0031 | [−0.0346, +0.0315] | 0.868 | n | +0.1513 | −0.0057 | NULL |
| 15 | RB | **C1** new offensive coordinator | +0.0932 | [−0.0637, +0.2406] | 0.288 | n | +0.1470 | +0.0009 | NULL |
| — | WR | *V1 depth-chart proxy (batch 1 reference)* | +0.0818 | [−0.0075, +0.1795] | 0.126 | — | −0.0327 | −0.0007 | *reference* |
| — | TE | *V1 depth-chart proxy* | +0.0448 | [+0.0106, +0.0773] | 0.033 | — | +0.0652 | +0.0057 | *reference* |
| — | RB | *V1 depth-chart proxy* | +0.2031 | [+0.1150, +0.2963] | 0.002 | — | −0.1264 | −0.0010 | *reference* |

**† Read every † row with §1(3).** All three are `move_known`, not `moved_club`. Quoting a SURVIVES
without that paragraph would be a misuse of this document.

**Grade counts (family of 15):** NULL 10 · SURVIVES 2 † · PROJECTION-ONLY 1 † · HARMFUL 1 ·
MARGINAL-HARMFUL 1. **Excluding the mis-specified arm, the batch is 12 NULL-or-worse out of 12.**

The three reference rows are batch 1's V1 arm re-run unchanged. They are not in the family, carry
their batch-1 grades, and exist only for the §1(1) head-to-head.

---

## 3. What the coordinator data turned out to be

**`play_callers` was empty.** The 607 rows data-ops ingested on 2026-07-30 (`6ba3887`) are not in
`data/nfl.db` — the table is not in `scripts/rebuild_database.py`, so a rebuild dropped it silently,
along with the `data/raw/wikipedia/` cache. Reported to data-ops (thread
`2026-07-30-play-callers-is-not-in-nfl-db-and-end-of-season`). **This is a rebuild-path defect, not a
one-off.**

**End-of-season staff cannot answer #29, and the reason matters.** `play_callers` stores
`{{NFL final staff}}` — whoever held the role at the *end* of a season. For a club that fired its OC
in November, that names the replacement. A "did the OC change?" feature built from it reads *changed*
for a club that entered the season with continuity — and the firing is *caused by* the season going
badly. **The contamination points the same way as the hypothesis**, which manufactures signal rather
than blurring it.

**The obvious fix does not work, and that is worth recording.** Fetching each season article's
pre-Week-1 revision and re-running the same parser returns **0 of 32** team-seasons: "final staff" is
a static block editors substitute in *after* the season. What the in-season article carries is a
`==Staff==` section transcluding the club's **live** navbox, whose content is today's.

So `coord_preseason.py` makes **two revision-dated reads** per club-season — the article before
kickoff (to learn which navbox it pointed at) and that navbox page's own revision before the same
kickoff. `redirects=1` is required: four franchises renamed inside the window and their old navbox
titles are now redirects, which left **28 team-seasons empty for exactly four clubs** until it was
added — a non-random hole, not noise.

### Does `coach_id` actually follow a coordinator across a team move?

`CLAUDE.md` §4 reserves `coach_id` as a first-class dimension for precisely this. It has never been
checked against data. It checks out:

| | |
|---|---|
| coverage | **414 OC rows, 2012–2024, all 32 clubs**; 32/32 clubs in 11 of 13 seasons |
| distinct named OCs | 126 |
| **OCs appearing for 2 or more clubs** | **53 (42.1%)** |
| club-seasons whose OC is one of those movers | **243 of 400** |
| same name as OC of 2+ clubs in the **same** season (collision risk) | **0** |
| OC change rate, consecutive seasons | **46.9%** (179 of 382 comparable club-seasons) |
| new OC who was an OC *elsewhere* the prior season | 32 of 179 (**17.9%**) |

**The join works.** Greg Roman spans SF→BUF→BAL→LAC; Nathaniel Hackett BUF→JAX→GB→NYJ. Name-as-id is
safe here in the sense that matters — zero same-season collisions — though it remains an unverified
assumption for any future name clash.

**The limit worth knowing:** only **17.9%** of OC changes bring in someone who was an OC somewhere
else last year. The rest are promotions from position coach or returns from outside the OC pool, and carry
**no prior OC-level history in this table at all.** Any future tendency-following signal (#30, or a
"this coordinator's offences historically run X% more") can reach at most **one change in six**.

**Three of 170 detected changes were the same person rendered differently** ("Pete Carmichael, Jr." →
"Pete Carmichael"; two cases of a navbox dropping a head coach from the OC line while he kept calling
plays). Normalised before fitting; each would otherwise have fabricated a new-OC event.

**Honest `as_of`:** the navbox revision is dated a median 45 days before kickoff, but **76 of 414
rows are inside 14 days** — i.e. around or after a real late-August draft. Coordinator hires are
January–March events so the practical exposure is small, and `as_of_date` states the truth on every
row. Nothing is backdated.

---

## 4. Guardrails applied (`docs/statistical-guardrails.md` requires this section)

| check | how |
|---|---|
| **Look-ahead** (§6.1) | `SeasonPanel.before()` gate; separate `outcomes()` accessor; per-target-season audit asserting max feature cutoff and max outcome season strictly < target and zero outcome reads at target. All 18 arms × 11 seasons passed |
| **The season-N reads, isolated** | `preseason_roster()` and `preseason_coordinators()` log under the **same `proxy` tag** as batch 1's `week1_roster()`. **Every primary asserts `n_preseason_proxy_reads == 0` as a live `RuntimeError`.** Measured: 0 for all three primaries, 88 per V1 arm (batch 1's value, unchanged), 134 per batch-2 arm |
| **Survivorship** (§6.2) | universe frozen pre-season; busts retained at 0. 2,271 WR / 1,441 RB / 1,041 TE player-seasons |
| **Multiple comparisons** (§6.3) | BH across all m = 15, q = 0.10 and 0.05, denominator fixed at 15 regardless of outcome |
| **Holdout** (§6.3) | 2025 sealed at the SQL gate. **Not opened.** No holdout spend requested |
| **Effect size** | every E1a as a % of the primary's own error; every candidate re-checked on the ADP board |
| **Autocorrelation** | seasons are the bootstrap unit and the t-test's n, never player-seasons |
| **Pre-registration** (§6.3) | `factor-batch-2-precommit.md`, content committed `851a6bb` before the first fit; both amendments dated inside it and both made before fitting |
| **Reproduction** | batch 1's feature frame reproduces **bit-for-bit** under the extended builder (`tests/test_factor_batch2_features.py`), and V1's E1a reproduces batch 1's published numbers to four decimals |
| **Roster status taxonomy** | every status code present in the data is classified; `unknown_status_codes()` returns empty and a test asserts it |
| **"Too good" trigger** | committed in advance at 2% of primary error. **It fired on WR M1 and the decomposition it forced overturned the interpretation of three arms.** See §1(3) |

---

## 5. The insight sentence — what may render, and what may not

The rule was fixed in §7 of the pre-commitment, before any result existed: a sentence renders only
if the factor **graded** (SURVIVES or PROJECTION-ONLY) **and** the feature is non-null for that
specific player.

| the founder's example | the factor | result | **may it render?** |
|---|---|---|---|
| *"So and so has a new OC"* | #29 C1 | **NULL at all three positions** | **No.** |
| *"The starter from last year left"* | #28 V2 / V3 / V4 | **NULL at 7 of 9 cells, harmful at 1** | **No.** |
| *"…and we expect routes run to increase"* | — | route participation is **not in `nfl.db` at all** | **No, and it was never testable here.** |
| *"this player changed clubs"* | M1 | graded, but §1(3) shows the grade is `move_known` | **No.** |

**Nothing in batch 2 earns the right to render an insight sentence.** That is the answer, and
delivering it is the deliverable.

The counting makes the cost of getting this wrong concrete. `new_oc` is true for **187 of 391 WR**,
**167 of 357 RB** and **49 of 106 TE** ADP-board player-seasons — **46–48% of the board.** A "new OC,
expect more" line would therefore have been attached to roughly half of every draft board, asserting
a mechanism that measures **NULL** in this model. That is the same failure the recommendation card
was caught committing, at ten times the surface area.

**Separately: directional wording was never licensed by this campaign and would not have been even
if C1 had graded.** "Expect routes to increase" asserts a sign. Nothing here estimates a signed
per-player effect and nothing here measures routes.

---

## 6. What I am not claiming

- **Not claiming #28 is dead as a concept.** It is dead *as measured here*: three constructions,
  three positions, one model. `docs/ideas-inbox.md` records the untested variant that most plausibly
  explains every null — **this project counts who LEFT a club and has never once counted who
  ARRIVED.** A club that loses 200 carries and signs a 250-carry back has vacated nothing.
- **Not claiming #29 is dead.** It is NULL *for this question*: does a coordinator change move a
  player's targets or carries. It says nothing about tendency-following (which the join now supports
  for 16% of changes), about coordinator *tenure* rather than change, or about #30.
- **Not claiming the M1 SURVIVES rows are edges.** They are `move_known`. See §1(3).
- **Not claiming "is he on a Week-1 roster" should be added to the model.** It is worth 1.6–2.3% of
  component MAE, it belongs to the availability sub-model, and it is a `proxy`-tagged season-N read
  whose draft-time availability needs its own assessment. Handed to `strategist` and `backend`, not
  adopted here.
- **Not claiming the V2 − V1 comparison licenses V2.** It licenses only the statement that the
  earlier harm was a data artifact. V2 itself is NULL.
- **Not treating any of this as final.** `strategist` has the design on an open thread and has not
  yet ruled; `fable` has not attacked it.

---

## 7. Independent checks, because I do not grade my own work

| claim | who checks it | status |
|---|---|---|
| the design, endpoints, family size and the endpoint correction | `strategist` | thread `2026-07-30-register-factor-batch-2-28-vacated-opportunity-o`, **OPEN** |
| the result once it exists, at maximum effort | `fable` | not yet opened — weekly budget |
| the coordinator source and whether it should be productionised | `data-ops` | thread `2026-07-30-play-callers-is-not-in-nfl-db-and-end-of-season`, **OPEN** |
| whether `move_known` belongs in the availability sub-model | `strategist` → `backend` | raised on the strategist thread |
| shipping anything | `backend` | nothing is proposed for shipping |
