# In flight — read this first on Monday

**Last written 2026-08-01 (Saturday) by pm, with the weekly token pool nearly spent.** The founder's
words: *"Likely we hit weekly usage soon… If we hit it, next time we will talk is Monday morning."*

Two audiences. **§A is for the founder** — what happened, what it cost, what to decide. **§B onward is
the agent resume detail.** `CURRENT-STATE.md` is settled state; `docs/status/` is history; **this file
is the volatile one** and should be emptied when nothing is in flight.

---

# §A · For the founder, Monday morning

## The one-paragraph version

Ranking **v2** is built and independent — no consensus anywhere in its ordering path, with a swappable
scoring layer proven to re-rank under half-PPR / full-PPR / standard with zero refits. It is **not yet
as good as consensus**: on the three seasons where both exist, v2 averages ρ 0.583 against consensus
0.725. **But the instrument we were grading factors with turned out to be broken**, which is the real
news of the day, and it has been replaced (**ADR-070**).

## What happened today, in order of importance

1. **A placebo — pure seeded noise — passed our factor inclusion test.** Graded `INCLUDE` at
   p = 0.0002. Replicated across 34 noise draws: the rule awarded wins to noise on **9.6% of cells
   against a nominal 2.5%**. Every "significant" factor result this project ever produced sat on that
   rule. It was caught only because `ranker` registered the placebo as a deliberate calibration check.
2. **The rule has been replaced — ADR-070.** Permutation-based nulls matched to each arm, sequential
   Monte Carlo p-values with no parametric tail fit, BH retained at campaign M = 130. **Two of the
   founder's own inputs were adopted into it:** calibrated sign-consistency as a required condition,
   and the HARM split into **RE-SPECIFY** vs **EXCLUDE (variance)** — "a consistent signal pointing
   the wrong way is usable."
3. **The most valuable item on the whole list — and PM had it wrong until the founder challenged it.**
   PM reported "we only have 7 seasons" as a structural finding. **It is a choice, not a limit.**
   Measured 2026-08-01: `player_weekly_stats` covers **1999–2025** (475,626 rows);
   `depth_charts_weekly` 2001–2024; `rosters_weekly` 2002–2025. **v2's evaluation panel is 2018–2024
   only because it was built on the intersection with the latest-starting sources** (`odds_snapshots`
   and `pfr_advstats_*` begin 2018, `ngs_*`/`participation` 2016, `snap_counts` 2013). We let the
   newest feature set the window for the entire model.

   This matters because it is exactly the constraint strategist named as binding: at S = 7 **no exact
   season-level randomisation test can reach a BH threshold by any method**; at 12 it can. **We have
   up to 26.** Staggered feature availability is normal and is handled per-feature (matched windows,
   indicator-and-interaction, or per-era fits) — never by truncating the panel.

   The one genuine caveat is `CLAUDE.md` §6.4 non-stationarity, and it is **an empirical question, not
   a reason to stop**: measure where the span stops helping, per position, and report the curve.
   **Report what the span *can* be (a data fact) and what it *should* be (a measured result)
   separately — do not let the second silently become an argument for the status quo.**

   Dispatched to `ranker` as measurement **M-4**, thread
   `docs/handoffs/2026-08-01-m-1-m-6-the-measurements-the-replacement-inclusi.md`. **First call on
   Monday's budget.**
4. **Factor inclusion: 6 of ~95 tested against v2, none included.** Snap share, red-zone usage, xFP,
   NGS separation, route participation, steeper recency. The four sources this repo has long called
   "in the database and untouched" do not improve v2's ordering. C1 now **re-grades** under ADR-070 —
   the arms do not re-run, only the null baselines get built.
5. **Data landed:** Vegas odds 2018–2024 (3,884 rows — spreads, totals, implied team totals), never
   before ingested and not yet used by any model. Per-analyst boards: 66 experts, **2026 only and
   structurally unbackfillable**, so the "on par with any single analyst" bar cannot be measured on a
   completed season.
6. **A correction to something PM told the founder.** Week-1 roster status was described as
   cutdown-dated and therefore safe for a 7 September draft. `strategist` read the code: it is
   **Week-1-kickoff-dated**, 3–6 days *after* the draft. G2a is conditionally admitted with unmet
   conditions; **v2 stays on the old (G0) games model.**

## Decisions waiting on the founder

- **The definition of "exhausted"** before news work begins — proposed in
  `docs/founder-requests/FR-2026-08-01-ingest-and-use-camp-reports-beat-reporters-depth.md`. Five
  criteria; correct it if the bar is wrong.
- **Draft dates for the two secondary leagues** (FR-012). Until known they get the safe default.
- **Confirmation of the 2026 Week-1 kickoff date** — needed for one config value, not for the ruling.

## Standing rulings made today (all recorded, none need re-deciding)

| Ruling | Where |
|---|---|
| Bar is absolute quality, not edge over consensus; projections are stat lines, scoring portable | ADR-069, `CLAUDE.md` §2a |
| Deviation from consensus is a **diagnostic to explain**, never a penalty to minimise | `CLAUDE.md` §2a |
| Terms of service are the founder's concern, not an agent gate | `CLAUDE.md` §5 |
| Exhaust measurable modelling before news; capture deferred too | FR, `…camp-reports-beat-reporters-depth.md` |
| A consistent signal pointing the wrong way is usable — re-specify, don't exclude | ADR-070 §4.4b |
| The sealed 2025 holdout does not open | `CLAUDE.md` §6.3, restated by founder |

---

# §B · Agent resume detail

## Running when this was written — check their output files before assuming nothing landed

| Agent | Task | Output |
|---|---|---|
| `ranker` | **Player-availability model** from `injuries` (2009+, incl. practice participation), `depth_charts_weekly` (2001+), `rosters_weekly` | results doc + manifest |
| `backend` *(worktree)* | **Batch C2** — more ledger factors **+ threshold/breakpoint tests as a class** | `docs/ranking/batch-C2-results.md` |
| `backend` *(worktree)* | **Discovery pass** — hypothesis *generation* from residuals | `docs/ranking/discovery-pass-1.md` |
| *(bg process)* | **PR-007** recommendation-constants ablation, `src/run_pr007.py` | results doc → thread to `frontend` |

All were told to commit incrementally and keep a `NEXT STEP` block at the top of their output.
**Two worktrees under `.claude/worktrees/` belong to running agents — do not sweep them until their
branches are merged.** Procedure in `docs/environment.md` §4b; each costs ~0.9–1.0 GB.

## Monday's order of work

1. **M-4 — how far back can the target span go.** Thread
   `docs/handoffs/2026-08-01-m-1-m-6-the-measurements-the-replacement-inclusi.md` (`TO: ranker`).
   Everything else is rate-limited by S = 7. Do this first.
2. **Merge and read whatever the four agents landed.** Their files, not their absence, are the record.
3. **Re-grade batch C1 under ADR-070** — build null ensembles only; do not re-run arms.
4. **Resume factor inclusion**, now on a rule whose error rates are pre-committed (HYPOTHESIS ≤ 5.0%,
   any INCLUDE/EXCLUDE across an all-null 20-cell batch ≤ 1.3%) — and **verify them empirically the
   way C1 verified its predecessor.**
5. Carry a **placebo arm in every batch, permanently.** It is the only reason today's failure was
   visible.

## Live constraints that survive any reset

- **Seasons through 2024. The sealed 2025 holdout does not open** — no agent on its own authority,
  including on a result it considers decisive. Log: `docs/preregistration/holdout_access_log.jsonl`.
- **v2's games arm stays G0.** No session may flip `v2.json` on the G2a ruling reply alone; conditions
  C1–C5 in `docs/handoffs/2026-08-01-g2a-admission-conditions-c1-c5-run-these-before.md` are unmet.
  **C1 of those conditions is the dangerous one** — if nflverse's rebuilt historical roster files
  restated status, week-1 status is a lagged *outcome* variable and the +0.072 was never real.
- **Do not cite the old ~90 factor nulls as evidence about inclusion.** They measured a
  consensus-derived model, not v2. Founder's ruling.
- **Register thresholds before measuring; correct at the campaign level** (Σm_b = 130). With consensus
  out of the development loop, this plus the sealed holdout is the *only* overfitting protection.
- **`v2.json` has two known config defects** flagged by strategist and not yet fixed: `m_b` = 12 where
  the manifest computes on 20, and the arms list omits G1a/G2a — inside a block marked
  `immutable_once_run`.
- Branch **`claude/pm-agent-setup-gobxa0`**; merge to `main` is founder-authorised.

## Known-open, nobody working

`PR-` ids still have no allocator. The metric rename (`E1a→C1`) was never applied. Threads 109–111
carry literal merge-conflict markers. Three corrections owed from Fable's M2 review. `docs/status/`
narrative for the strategist session was not written (no shell access in that role).
