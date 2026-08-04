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
| C1 · C2 | 12 | Tested under the broken rule — **re-running** |
| C3 · C4 | 12 | Registered, queued |
| Incumbents (AB1 + additive) | 6 | **Four of the six were never in the running model** — they run as *additive* arms, not ablations. Only the six channels genuinely in the specs are ablated |
| C5 — newly unblocked | ~7 | PROE was **never blocked**; coordinator continuity via a Wikipedia-derived table, not the PFR source the ledger blamed |
| CT1 — within-cluster contrasts | 40 | The founder's collinearity insight. TE depth-rank-vs-usage was the strongest single result found (ρ ≈ −0.5 to −0.6) |
| **Pool total** | **75 base + contrasts, 5 untestable** | **All queued.** Authoritative list: `docs/ranking/standalone-screen-2.md` |

**Runtime estimate below is SUPERSEDED — see "Throughput" section. Original: 14–18 hours from 01:25 UTC 2026-08-04**, measured — ~238 ensembles, 0.6–4.1 s per draw on
3 workers, L = 8,999 at M = 442. Founder ruled **no trimming**: *"The 2 hours saved are not worth the
trimming, run it all."* The report fills progressively — D1A1+C1+C2 by ~3–4 h, C3+C4 by ~8 h, the
contrasts are the tail.

**Report regenerates automatically** after every batch and hourly:
`docs/ranking/inclusion-campaign-report.md`. Counting rules fixed in `report070.py`.

### Throughput: what was actually wrong, measured 2026-08-04

**Two independent problems, and the earlier diagnosis named neither.** "The sweep dies when tokens
run out" was wrong — the founder confirmed tokens did not run out overnight. Both causes below were
found by measuring the live run, not by reading the code.

**Problem 1 — the parent process was the bottleneck, not the model.** With a fixed `CHUNK = 12`, the
parent re-read the entire draws CSV and re-derived every `delta_bar` between every twelve draws to
run the sequential test: O(n) serial work every 12 draws, **quadratic in draw count**, with all
workers idle through it. Measured at the L-tail: parent burning a full core on re-parsing, box at
271% of 400% with 21.7% idle.

Fixed by `chunk_for(n) = max(12, n//8)` plus a fourth worker (commit `ae40f6a`). The chunk could not
simply be raised — Besag–Clifford stops at h=20 and a dead factor stops within tens of draws, so a
large *fixed* chunk overshoots the stop on every null cell, and most cells are null. Growing it keeps
overshoot a constant fraction of progress. **47 chunks reach L instead of 749.**

**Measured, sustained over 5–6 minutes: 42 → 89.3 draws/min, 2.1×.** An earlier claim of 5.1× in
this file and in chat came from a 90-second sample that landed inside a compute burst — **quote
sustained rates only, measured over minutes, and read them off the chunk-boundary timestamps in
`sweep.log` rather than from a short `wc -l` window.**

**Problem 1b — the actual quadratic, which two earlier diagnoses both missed.** `_append_draws` read
the entire draws CSV, concatenated, de-duplicated and rewrote the whole file **after every completed
draw**. O(n) per draw, O(n²) per cell; 20% of a core at n=2,800 and growing, so at the L=8,999 tail
the parent would have been rewriting a 90,000-row file per draw while four workers waited. Now a
true append (commit `4333ec9`), with the header read back and column order enforced on each write —
appending in a different key order would silently shift values across columns, the one failure here
that could corrupt a verdict without failing loudly.

It also removed a live data-loss window: the old rewrite truncated before writing, so a kill
mid-write rolled the file back to a partial state. That happened during this session's restart and
cost ~960 banked QB draws. An append cannot do it.

**The box is now saturated — 4 workers at ~98% each, parent at 3.5%, 398% of 400%. No further
parallelism exists on this machine.** Any additional compute gain must come from making a draw
cheaper or from more cores.

**Problem 2 — the container exists only while a session turn is in flight, and this is the bigger
factor.** Disk persists across container death (draws resumed 480 → 985 → 1,267 correctly); compute
does not. Observed duty cycle before the fix: **~11%** — roughly 7 minutes of compute per hour.

**The old watchdog Routine was the reason overnight was a total loss.** It fired correctly at 13:49
— and left no entry in the sweep log, because it was configured to spawn a **fresh session**, which
gets a **fresh container** with no `data/nfl.db` (gitignored) and no banked draws. It revived a
throwaway box hourly while the real one stayed dead. Deleted.

Replaced by `sweep070-keepalive` (`trig_014aiAwEr2nPX8Lvz5gYf6fv`), **bound to this session** so it
wakes *this* container, and holding it open with five foreground `timeout 570 tail -f` blocks per
firing — ~50 of every 60 minutes rather than ~7. **Delete it when the sweep completes**; it stops
itself on "sweep completed cleanly" but cannot delete its own Routine.

**Combined effect: ~16× effective throughput** (2.1× compute × ~7.5× duty cycle).

**Remaining unknown, and it is the one that sets the finish date:** Besag–Clifford stops a
cell as soon as 20 null draws beat it, so a dead factor costs seconds and only a genuinely
strong one pays the full L=8,999. Total runtime is therefore set by **how many cells run to
L**, which is not knowable in advance. Full-L cost per cell at the current rate: QB ~1.7 h,
TE ~2.7 h, WR ~3.9 h, RB ~11 h (per-draw costs scale as the VERIFY timings: QB 123s · TE 193s
· WR 286s · RB 822s for identical work).

**Cron's floor is hourly**, so ~10 min/hour of container downtime remains. Closing that needs either
GitHub Actions (free, 6-hour jobs, no tokens) or the founder's own machine — his desktop is Windows
and the sweep uses `fork`, so it would need WSL2, not native Python.

**Realised per-position span differs and TE is thinnest:** QB 10 · RB 9 · WR 11 · **TE 7**.

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
