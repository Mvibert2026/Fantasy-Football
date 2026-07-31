---
id: PR-DRAFT-consensus-quality-by-season
title: How good is consensus ADP, season by season, and is its bad years identifiable in advance
hypothesis: >
  Consensus market ADP's rank-correlation to realised outcomes varies materially across seasons
  beyond sampling noise (the founder's "certainly not every year"), AND no pre-season signal
  available before Week 1 predicts which seasons will be poor.
metric: >
  Per (season, position) Spearman rho between pre-season FFC half-PPR 12-team ADP and realised
  season fantasy points under this league's scoring engine, on the frozen pre-season universe with
  busts retained at 0; scored against two in-season-computable comparators (B3 weighted prior PPG x
  games share; B2 prior-season points) and against a within-season sampling-only null band.
confirmation_threshold: >
  See section 5. A season is POOR at position p iff rho_ADP < rho_B3 AND the gap falls outside the
  season-constant sampling null band. Outcome (ii) -- the only outcome that changes the product goal
  -- additionally requires a walk-forward predictive signal with AUC interval excluding 0.50 AND a
  predicted-POOR vs predicted-not-POOR gap of at least 0.134 in rho_ADP - rho_B3.
status: REGISTERED
number: NOT YET ALLOCATED -- assign the next free PR-<nnn> at registration time; do not reuse this
  filename's DRAFT slug in the run log.
registered_by: strategist
registered: 2026-07-31
answers: docs/founder-requests/FR-2026-07-31-separate-edge-over-consensus-from-absolute-ranki.md
companion_ruling: docs/adr-drafts/ADR-DRAFT-edge-vs-absolute-quality.md
holdout: 2025 stays sealed. Not opened, not read, not needed -- the FFC backfill does not contain it.
---

# Consensus quality, season by season

**Written before any value is seen.** I have deliberately **not** opened
`experiments/bottomup/results/*_components_metrics.csv`, which already contains the per-season
`adpsub_rho_b1_adp` values this test measures. Reading them before fixing the decision rule would
convert a pre-registration into a post-hoc rationalisation, which is the single thing my role exists
to prevent. The strategist has no database access by design and cannot run this; it is specified for
`backend` to execute.

---

## 1. Why this test exists

Every result in the factor campaign treats consensus as a **fixed bar**. The founder says it is not:

> *"These analysts all aren't better than consensus. Certainly not every year."*

If consensus quality is stable, the bar is a bar and nothing changes. If it varies **and the poor
years are identifiable in advance**, the product goal changes from "beat consensus on average" to
"be right in the years consensus is wrong" — a different, smaller, more achievable objective. If it
varies and the poor years are identifiable **only afterwards**, that kills the idea, and §5 says so
now so it cannot be softened when the number arrives.

---

## 2. What is measured

For each season `S` in **2013–2024** and each position `p` in {QB, RB, WR, TE}:

```
rho_ADP(p, S) = Spearman( -average_pick , realised_season_points )
```

- **Universe:** that season's frozen pre-season universe, ADP-covered subset (`adpsub_*`), **busts
  retained at realised 0 points, no games-played filter of any kind.**
- **Outcome:** realised season total under this league's scoring engine
  (`scoring.score_offensive_game`, summed per game so the stacking yardage bonuses are computed at
  the game level, per `CLAUDE.md` §7).
- **Predictor source:** `data/adp-snapshots-ffc/*_half_ppr_12team_period{S}.csv`, loaded through
  `experiments/bottomup/components/adp_baseline.py::load_adp`, which **already** re-asserts the
  strictly-pre-kickoff gate and raises rather than trusting the file (`:88-92`). Do not bypass it.

**This quantity already exists.** `pos_eval._season_metrics` computes `adpsub_rho_b1_adp` per season,
and `run_position.py:82-85` already prints it. It has never been reported **as a level** — only as
the subtrahend inside a delta. This test is extraction plus three additions (§3, §4, §6).

---

## 3. Three comparators — a bare rho is forbidden

A per-season rho on its own is a raw accuracy number in isolation, which `CLAUDE.md` §6.5 forbids.
Each season's consensus is scored against something computable **in that same season**:

| id | comparator | already exists as | what a gap means |
|---|---|---|---|
| **B3** | weighted prior PPG × games share | `b3_wavg_ppg` in `_baseline_columns` | consensus's margin over a three-line heuristic — the existing power check, now **per season** |
| **B2** | prior-season points | `b2_prior_points` | consensus's margin over the founder's own intuitive baseline (§6.5 baseline #2) |
| **B4** | within-season predictability context: `n_adp`, and realised points of ADP-top-12 vs ADP 13–24 | new, trivial | how much of that year's variation was **available** to be predicted at all — guards against calling a season "poor" when it was merely flat |

---

## 4. The null model — mandatory, and it is what stops this being a fishing expedition

**Season-to-season variation in rho is guaranteed by sampling noise** at n ≈ 50–100 players. Finding
some is evidence of nothing. Before any season may be called POOR:

> For each `(p, S)`, bootstrap `rho_ADP` **within season** by resampling players with replacement,
> **4,000 reps, integer seed recorded** (guardrails §11 — never builtin `hash()`). This gives the
> width `rho` would have **if consensus quality were constant across seasons**. Report the band.

**A finding of "consensus quality varies" that does not exceed this band is a NULL and must be
reported as one.** Without this, twelve seasons of a noisy statistic will always produce a spread, and
presenting that spread as a finding would be confident, false — and *convenient*, because it re-opens
a line that a day of nulls closed.

---

## 5. The decision rule, pre-committed

**"Consensus was poor in season N at position p"** iff **both**:

1. `rho_ADP(p,S) < rho_B3(p,S)` — market ADP was beaten, that season, by weighted prior PPG; **and**
2. the gap falls **outside** §4's season-constant sampling null band.

Rejected alternatives, stated so they cannot be substituted later:
- *A percentile of consensus's own distribution* — guarantees ~⅓ of seasons are "poor" by
  construction. Unfalsifiable.
- *A fixed threshold on rho itself* — uncalibrated across positions (QB rho and TE rho are not
  comparable levels).

**"Consensus was strong"** iff `rho_ADP − rho_B3 ≥ +0.134` — the RB point estimate already on file,
chosen because it is the one margin this project has measured as resolvable at n = 7, not because it
looked right. Everything between POOR and STRONG is **UNRESOLVED** and is reported as such, never
sorted into one bucket to make the table tidy.

### The three outcomes and what each one does to the product

| | finding | verdict | product consequence |
|---|---|---|---|
| **(i)** | POOR seasons rare (≤ 2 of 12 at ≥ 3 of 4 positions) **and** the season-level spread of `rho_ADP − rho_B3` has a 95% bootstrap CI narrower than 0.10 | consensus quality is **stable**; the founder's "certainly not every year" is not supported at position level | The bar is a bar. Continue as now. Report the campaign's nulls as **expected**, per Ruling 3 |
| **(ii)** | POOR seasons occur **and are predictable in advance** (§6 clears **both** its gates) | **the product goal changes** | "Be right in the years consensus is wrong" becomes the objective. Different, smaller, more achievable model than "beat consensus on average" |
| **(iii)** | POOR seasons occur **and are identifiable only afterwards** | **this kills the idea** | A consensus-quality signal knowable only in December is worth **exactly zero** at an August draft. Correct action: record the variance as a **widening of every CI in the campaign** — consensus is a noisy bar, so a single-season comparison against it is weaker evidence than it has been treated as — and close the "target the bad years" line permanently |

---

## 6. The prediction test — separates (ii) from (iii), and must run in the same pass

**Outcome (ii) may not be claimed unless this runs.** Leave-one-season-out walk-forward: fit on
seasons `< S`, predict whether `S` will be POOR at position `p`, score by whether predicted-POOR
seasons actually had lower `rho_ADP − rho_B3`.

Candidate signals, restricted to what exists **strictly pre-Week-1** and is already in `nfl.db`:

| id | signal | source | mechanism |
|---|---|---|---|
| **S1** | rookie share of the position's ADP top-36 | `draft_picks` — draft classes are known pre-season | the market has least information about players with no NFL sample |
| **S2** | dispersion of `average_pick` within the position's top 36 | `average_pick`; **FFC also publishes a std-dev column that `adp_baseline.py:98` currently drops — retain it** | how much the crowd itself disagreed |
| **S3** | previous season's own `rho_ADP − rho_B3` at that position | this test's own output | does consensus quality autocorrelate at all |

**Two gates, both required, both pre-committed:**

- **(a) Statistical:** walk-forward AUC interval **excludes 0.50**, season-level bootstrap.
- **(b) Magnitude:** predicted-POOR seasons' mean `rho_ADP − rho_B3` is **at least 0.134 below**
  predicted-not-POOR. A real but smaller signal is **usable-in-principle and unusable-in-practice**,
  and is reported as outcome (iii), not (ii). Naming this now stops a statistically-real,
  operationally-worthless result from being reported as a product pivot.

---

## 7. Registered prediction, discounted per the standing calibration prior

The situation story here — *"some years the market is just wrong, and you can tell which"* — is
exactly the kind of narrative that has cost this project four of five registered prediction sets
(`docs/reviews/FABLE-EXT3-2026-07-27.md`). Priced at half its intuitive weight:

> **I predict outcome (iii).**
> `rho_ADP − rho_B3` will vary materially across seasons — the founder is right that consensus is not
> equally good every year — **and none of S1–S3 will predict it**: all three walk-forward AUC
> intervals inside [0.40, 0.60] and covering 0.50.
> I further predict **at least one POOR season at every position, including RB**, purely because a
> 12-season sample of a noisy statistic produces one by chance whether or not underlying quality
> moved. **That is precisely why §4's null band is mandatory** — without it this prediction would
> "confirm" itself.

Written now so it can embarrass me later.

---

## 8. Scope limits, binding

- **2013–2024 only. 2025 stays sealed** — not opened, not read. The FFC backfill does not contain
  2025 at all, so this holds by construction as well as by rule. **State that in the report** rather
  than relying on it silently.
- **Multiplicity, split explicitly.** The 12 seasons × 4 positions = **48 descriptive cells are
  EXPLORATORY** per `ADR-C-preregistration`'s registry categories — a characterisation of a baseline,
  not a factor test — and **do not enter the factor campaign's FDR denominator** (`M_campaign = 80`).
  Say so in the report. §6's prediction test is 3 signals × 4 positions = **12 CONFIRMATORY tests**
  and carries its own BH correction at **m = 12**, reported separately.
- **Half-PPR 12-team is not this league** (10-team). Consensus quality measured in a 12-team format
  is a **proxy** for consensus quality in ours. Label every figure as such. FFC archives no other team
  count for past seasons (`adp_baseline.py:5`).
- **This measures the MARKET; the founder's sentence is about ANALYSTS.** Run the same design against
  `fantasypros_ecr` **if and only if** a historical, dated, strictly-pre-Week-1 archive exists beyond
  the current season. **If it does not, say so plainly in the report** — it means the founder's literal
  question about analysts cannot be answered with the data we hold, and only the market proxy can.
  Do not substitute one for the other silently. See the escalation in
  `ADR-DRAFT-edge-vs-absolute-quality.md` §2.4.
- **Every interval is a season-level bootstrap**, never player-level, except §4's within-season null
  band which is player-level **by design and labelled as such**. Integer seed recorded for both.

---

## 9. What would falsify the design itself

- A season's `rho_ADP` turns out to be driven by ADP **coverage** rather than ADP **quality** —
  `n_adp` moving with `rho`. B4 exists to catch this; if it fires, the comparison is between
  different universes and the whole table is uninterpretable as stated.
- The pre-kickoff gate rejects seasons unevenly across positions, leaving an unbalanced panel. Report
  `n_adp` and the retained season list **per position**, before any rho is read.
