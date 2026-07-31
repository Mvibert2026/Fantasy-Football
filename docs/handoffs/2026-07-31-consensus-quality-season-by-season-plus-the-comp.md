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
