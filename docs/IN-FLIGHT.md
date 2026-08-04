# In flight — the singular short-term goal

**Written 2026-08-04 by pm.** Supersedes the 2026-08-01 contents entirely. **Delete this file when the
goal below is delivered** — a stale IN-FLIGHT is worse than none, because it will be read as current.

---

## THE GOAL — founder, 2026-08-04, and nothing else gets tokens until it lands

> "That is the singular short term goal… All factors against the new standards. With that output."
>
> "I want to land at a point we can say we tested # of factors for inclusion (all we are able to and
> may find out we are able to). Then here's how many that passed inclusion in total. And here's the
> ones for each position."

**Deliver exactly this, as a deliverable and not a by-product:**

1. **How many factors were tested for inclusion.** One number.
2. **How many passed.** One number.
3. **Which passed, per position** — QB, RB, WR, TE separately. **This is the real answer; the totals
   are a headline.** A factor can pass at one position and be actively harmful at another: batch C1's
   snap share was NULL at RB and WR and HARM at TE.
4. **How many remain untestable and why** — so "we tested everything we could" is auditable rather
   than asserted.

**Against the new standards** means ADR-070: matched permutation nulls, sequential Monte Carlo,
BH at campaign M, calibrated sign-consistency, HARM split into RE-SPECIFY vs EXCLUDE. Graded on
tier 2 (2013–2024, S=12), trained from 2002.

**Nothing else gets tokens.** The v3 joint fit is parked (separate track, blocked on a season-budget
ruling). PR-007 keeps running because it is already-spent compute, but **no agent is dispatched to
write it up** until this lands.

---

## Where the count stands

| Group | Factors | State |
|---|---|---|
| C1 | 6 | Tested under the broken rule — **re-running** |
| C2 | 6 | Tested under the broken rule — **re-running** |
| C3 | 6 | Defined, queued |
| C4 | 6 | Defined, **needs adding to the sweep queue** |
| Incumbents | 6 | In the model, never tested — **ablation arms, need adding** |
| Screen contrasts | 13 | Within-cluster gaps; TE depth-rank-vs-usage was the strongest result found |
| Blocked-list re-audit | ~5–8? | **Running** — unknown until it reports |
| **Pool total** | **~43–50** | |

**Do not quote 95, 80, or 37.** 95 was the raw ledger row count including structural config,
duplicates, and things already in the model. 37 and "C3 has 19" were **PM counting errors** — a grep
that counted functions rather than factors. The ledger has 132 rows; most are not testable factors.

---

## Running now

| Agent / process | Task | Notes |
|---|---|---|
| `ranker` (fable) | Extend the sweep to C4 + incumbent ablations + late arrivals, then **produce the report above** | Sweep is detached, survives context loss |
| `backend` (worktree) | Re-audit the 20 BLOCKED ledger rows against the DB as it now stands; extend the standalone screen to the full pool | Delivers `docs/ranking/standalone-screen-2.md` and the untestable count |
| `sweep070` | Detached compute, 4 processes | `experiments/bottomup/results/sweep070/` — `sweep.log`, `state.json` |
| PR-007 | Recommender constants, second pass at higher precision | Free compute; **do not dispatch a write-up yet** |

**Sweep progress:** VERIFY phase **PASSED** — 40/800 false positives = 5.0% against a pre-committed
5.0%, and **zero placebo inclusions** where the old rule gave 9.6%. Grading is unblocked. Now on
`D1A1` (the availability fix), then C1, C2, C3, then the additions.

**Timing:** VERIFY took 24 minutes for 4 cells; one RB cell alone took 14. The remaining ~100+ cells
are **3–20 hours of unattended compute.** It costs no tokens.

---

## If you are a successor session, do these in order

1. **`tail experiments/bottomup/results/sweep070/sweep.log`** and read `state.json`. Read
   `docs/ranking/adr070-tier2-execution.md` — ranker keeps a `NEXT STEP` block at its top.
2. **Check every dispatched agent has committed in the last hour.** On 2026-08-03 one sat idle four
   hours with no completion notification and PM did not notice; the founder did. Ping for a forced
   checkpoint and say explicitly that "blocked" and "looping" are acceptable answers.
3. **Merge and sweep any finished worktrees** before starting anything (`docs/environment.md` §4b;
   ~1 GB each, nothing removes them automatically).
4. **Add C4, the incumbent ablations, and any newly-unblocked factors to the sweep queue** if ranker
   has not.
5. **Assemble the four-part report.** That is the deliverable.

## Constraints that survive any reset

- **The sealed 2025 holdout does not open** — no agent on its own authority, on any result. Log:
  `docs/preregistration/holdout_access_log.jsonl`.
- **Seasons through 2024. Grading at tier 2 (2013–2024).** Every ρ carries its four-part provenance
  key (universe / targets / S / first_feature_season) — **cross-universe and cross-span deltas must
  not be computed**, enforced by a raise (ADR-070 §4.8).
- **Carry a placebo arm in every batch, permanently.** It is the only reason the broken rule was found.
- **Incumbents get no grandfather clause.** Six base-spec factors are in the model untested; C4 skipped
  two of them *because* they were incumbents, which is backwards.
- **Do not cite the old ~90 consensus-frame nulls** as evidence about inclusion. Different model.
- **Do not use week-1 roster status** — Week-1-kickoff-dated, after the founder's 7 September draft.
- Branch **`claude/pm-agent-setup-gobxa0`**; merge to `main` is founder-authorised.

## Parked, not forgotten

v3 joint fit (screen → fit → compare, v2 as checkpoint) with its collinearity, per-position and
incumbent constraints in `docs/founder-requests/FR-2026-08-04-v3-build-strategy-screen-all-factors-for-predict.md`.
**Blocked on a `strategist` ruling:** only 5 seasons (2020–2024) remain unspent for a disjoint fit and
test, against a 15–25 predictor survivor set. That is thin and must be registered before any
coefficient is estimated.

**Approved by the founder, to be done later — not now:** backfill **targets for 2003–2008**.
Measured 2026-08-04: season 2005 has **zero** rows with `targets > 0` in `player_weekly_stats`, and
2008 has 17. Air yards are only 97–98% populated from **2009** onward (12% in 2001). This does not
affect the current campaign, which grades 2013–2024 — it caps how far back **receivers and tight
ends** can ever be measured. TE realises only **7** usable seasons even at tier 2, the thinnest of
the four positions, so this is the constraint that would move it. Data-acquisition work; competes
with nothing.

Also parked: player props were **never ingested** (`odds_snapshots` is game-level only, sourced from
`nflverse_schedules`); news/camp-report capture, deferred by founder ruling until the measurable work
is exhausted; the rookie model, which is currently two inputs with `combine` read by nothing.
