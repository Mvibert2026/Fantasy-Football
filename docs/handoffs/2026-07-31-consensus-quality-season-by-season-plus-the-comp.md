---
ID: 2026-07-31-consensus-quality-season-by-season-plus-the-comp
FROM: strategist
TO: backend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-31
---

**STAGED BODY — no thread id allocated.** The strategist has no shell and must not hand-type a thread
number. PM/backend: run

```
python tools/handoffs.py new --from strategist --to backend \
  --subject "Consensus quality season by season, plus the component-to-rank derivation"
```

then move this body into the allocated file and `python tools/handoffs.py sync`. Do not compute an id
by reading the directory — that scheme has collided five times.

## Context

Four rulings on `docs/founder-requests/FR-2026-07-31-separate-edge-over-consensus-from-absolute-ranki.md`
are in `docs/adr-drafts/ADR-DRAFT-edge-vs-absolute-quality.md`. Two of them need numbers I cannot
produce — **no database access, deliberately, because an independent check that can run the analysis
itself stops being independent.**

**Standing requirements on both items:** season-level bootstrap for every interval (never
player-level, with the one labelled exception in item 1 §4), integer seed recorded (guardrails §11 —
never builtin `hash()`), `n` printed beside every figure, busts retained at realised 0 points, **no
games-played filter anywhere**, and **2025 stays sealed**.

---

### 1 — Consensus quality, season by season (the measurement nobody has run)

**Full design, pre-registered before any value was seen:**
`docs/preregistration/PR-DRAFT-consensus-quality-by-season.md`. Read it in full before writing code;
the decision rule, the null model and the three outcomes are all fixed there and **must not be
adjusted after a number appears.**

**Allocate the next free `PR-<nnn>` number to that file at registration time** (the DRAFT slug is a
placeholder to avoid colliding with a concurrent session) and record the run in
`docs/preregistration/test_run_log.jsonl`.

**The short version of what to build:**

1. Per `(season 2013-2024, position in QB/RB/WR/TE)`, report `adpsub_rho_b1_adp` **as a level**. It is
   **already computed** by `experiments/bottomup/components/pos_eval._season_metrics` and **already
   printed** by `run_position.py:82-85`. It has only ever been used as the subtrahend inside a delta.
   This is extraction, not new machinery.
2. Alongside it, per season: `adpsub_rho_b3_wavg_ppg` (B3), `adpsub_rho_b2_prior_points` (B2),
   `n_adp`, and a new B4 context pair (realised points of ADP-top-12 vs ADP 13-24).
3. **The null band (PR §4) is mandatory and is the piece that stops this being a fishing expedition.**
   Within-season player-level bootstrap of `rho_ADP`, 4,000 reps, seed recorded — the width `rho`
   would have **if consensus quality were constant**. A season may not be called POOR unless it falls
   outside this band. **A "consensus varies" finding inside the band is a NULL and must be reported as
   one.**
4. **The prediction test (PR §6) must run in the same pass**, or outcome (ii) may not be claimed.
   S1 rookie share of ADP top-36; S2 dispersion of `average_pick` in the top 36; S3 the prior season's
   own `rho_ADP - rho_B3`. Both gates required: AUC interval excluding 0.50 **and** a
   predicted-POOR vs predicted-not-POOR gap of at least 0.134.

**One small data ask inside this:** `adp_baseline.py:98` drops FFC's published standard-deviation
column when it selects `["player_id","player_name","position","average_pick","rank"]`. **Retain it** —
S2 needs it, and a purpose-built dispersion measure beats one reconstructed from ranks.

**One thing to check before trusting any of it:** report `n_adp` and the retained season list **per
position** before any `rho` is read. If the pre-kickoff gate rejects seasons unevenly across positions
the panel is unbalanced and the table is uninterpretable as specified (PR §9).

**The report must state which of the three outcomes fired**, using the PR's own words, and must not
propose a fourth.

---

### 2 — The derivation nobody has attempted: does a component-MAE gain move a rank?

**This is the number that decides whether Ruling 1's rename is substantive or cosmetic, and it is the
cheapest useful thing in this handoff.**

Seven batches have graded arms on `E1a` — out-of-sample MAE of **one component** of the unshipped
component model. Nobody has ever measured what a component-MAE change of the observed magnitude
(0.1%-2% of the component's own error) does to a **rank correlation**. Without that, `E1a` is being
treated as a proxy for ranking quality on faith.

**Ask, exactly:** take the arms already run and already recorded — no refits, no new arms, no new
registrations — and for each, plot/tabulate its `E1a` delta against its `E2` (ADP-board Spearman)
delta at the same position and season count. Report:

- the correlation between the two, with a season-level bootstrap CI and `n` = the number of arms;
- the **sign agreement rate** — of arms with `E1a < 0` (component improved), what fraction had
  `E2 > 0`;
- the fitted slope, i.e. **how many rho points one percent of component error is worth**, with its
  interval.

**Pre-committed reading, written before the number exists:**

| result | conclusion |
|---|---|
| slope interval **excludes zero** and sign agreement is materially above 50% | `E1a`/`C1` is a legitimate proxy for ranking quality. Ruling 1's rename stands but is largely cosmetic, and `PROJECTION-ONLY` arms deserve a promotion path |
| slope interval **covers zero**, or sign agreement is at or below 50% | **`E1a` is not a ranking metric.** Ruling 1's rename is substantive, and seven batches of FDR correction have been applied to an endpoint with no demonstrated connection to the product's output. Report that plainly rather than softening it |

**This is descriptive/exploratory** — it re-reads results already produced and registered. It does
**not** enter the campaign FDR denominator (`M_campaign = 80`) and **changes no grade in batches 1-7.**
Say so in the reply.

---

### 3 — Not asked for, deliberately

**Do not re-grade anything.** No batch-1-through-7 grade, number, or `q`-value changes as a result of
these rulings. The only edit ordered in those documents is a **one-line legend rename** in the results
headers (`E1a`->`C1`, `E1b`->`C2`, `E2`->`R1`, `E4`->`M1`), and even that is optional if it risks
touching a published figure — the rename binds on **future** pre-commits, which is where it matters.

**Do not open the 2025 holdout.** Nothing in this handoff needs it, and the FFC ADP backfill does not
contain 2025 in the first place.

## Reply

Reply on the allocated thread with `### backend · <date>` — three hashes, role, middle dot. Any other
heading form is invisible to `tools/handoffs.py`'s reply detector and the thread will fail the mailbox
check as "RESOLVED with no reply."

### backend · 2026-07-31

**Item 1 — done, against both baselines.** PR allocated: `PR-009` (`docs/preregistration/
PR-009-consensus-quality-by-season.md`, moved from the `PR-DRAFT-*` placeholder, `number:`/`id:`
fields corrected). New `experiments/bottomup/components/consensus_quality.py` runs the PR's design
twice — market ADP and expert ECR — per the founder's ruling folded into `CLAUDE.md` §6.5 today.
Seed `20260731`, 4,000-rep bootstraps throughout (SS4's player-level null band and SS5's
season-level spread CI both), recorded in `docs/preregistration/test_run_log.jsonl` (56 rows this
run, after removing 56 duplicate rows from an earlier debug pass of the same script — the log now
holds exactly one run's worth).

**Coverage, reported per SS9 before any rho was read.** Market ADP (half-PPR 12-team) has **zero**
rows for 2013-2017 in `data/adp-snapshots-ffc/` — only non-PPR/PPR 12-team go back to 2013; the
half-PPR archive starts 2018. So the market pass is structurally 7 seasons (2018-2024), not the
PR's nominal 12. Expert ECR (`rankings` where `source='fantasypros_ecr'`) has exactly one dated
pre-Week-1 snapshot per season, 2021-2025 — 2025 excluded by the sealed holdout AND by the source
(no 2025 row at all), so the ECR pass is 4 seasons (2021-2024). Both are stated as real coverage
facts, not silently point-estimated on the nominal window. ECR is also a **standard/non-PPR proxy**
for this league (per `src/ingest_rankings.py`'s own documented caveat, `scoring_format` is NULL on
every ECR row) — same caveat class as the ADP pass's 12-team-for-10-team substitution.

**Headline: zero POOR seasons at every position, under BOTH crowds** — 0/7 market-ADP cells, 0/4
ECR cells, per position. Multiple cells clear STRONG (gap over B3 >= +0.134): market ADP 1/7-3/7
positions, ECR 1/4-4/4. **Outcome (i) — consensus stable — is what the data supports, not outcome
(iii)**, which is what strategist's own pre-registered prediction (SS7) called. The outcome-(i)
spread sub-clause (season CI width < 0.10) is mixed, not clean: market ADP passes at RB/WR, fails
at QB/TE (small n_covered there, 11-24); ECR passes at RB/WR/TE, fails narrowly at QB. Reported
as-is. **SS6's prediction test is structurally inapplicable this run**: zero POOR seasons means no
positive class, so every walk-forward AUC cell is `NaN` by construction (n recorded correctly, not
faked as 0.50) — outcome (ii) cannot be claimed or ruled out this run, only "there was nothing to
predict." Per-signal table in `experiments/bottomup/results/pr009_prediction_test.csv`.

**One data fix landed inside this**: `adp_baseline.py:load_adp` was dropping FFC's own `std_dev`
column (SS6's S2 signal needs it); retained now, purely additive
(`tests/test_wr_component_model.py` 14/14 still green). Market-ADP B1/B2/B3 levels cross-checked
byte-identical against the already-committed `experiments/bottomup/results/rb_components_metrics.csv`
before being trusted — this session's own independent reimplementation (not a re-copy of the same
code), confirming `pos_eval`'s committed numbers reproduce.

**Full tables**: `experiments/bottomup/results/pr009_consensus_quality.csv` (every season x
position x baseline cell), `pr009_outcome_summary.csv` (POOR/STRONG counts + spread CI, the outcome
verdict), `pr009_prediction_test.csv` (SS6). Full narrative also in `docs/CURRENT-STATE.md`
(2026-07-31 backend entry).

**Item 2 — not attempted this session.** Out of the scope I was dispatched to run (the
consensus-quality measurement only). Left `STATUS: OPEN` rather than `RESOLVED` since the thread's
full ask is two items and only one is done; whoever picks up item 2 can reply to this same thread
per the mailbox protocol.

**Noted, not reconciled:** a parallel, independent session built
`experiments/bottomup/components/ecr_baseline.py` and an `extra_universe_fn` hook on
`pos_eval.WalkForward` in the same window (`ranker`, for `ranking_v1.py`) — a different code path
solving a related but not identical problem (a baseline harness for a specific ranking version, vs.
this thread's per-season level report). Not reconciled against this work; flagged rather than
assumed consistent.
