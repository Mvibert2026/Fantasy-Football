# ADR-070 instrument + tier-2 panel — execution log

**ranker, 2026-08-03.** Live document for the six-step dispatch: implement ADR-070, rebuild the
panel at tier 2, verify the instrument, run D1-A1 Q0, re-run C1/C2, reconcile and launch C3.

---

## NEXT STEP

*Rewritten on every update. Being cut off is the expected case.*

**THE SWEEP IS RUNNING, DETACHED, WITH THE FULL 75-FACTOR POOL QUEUED** (restarted 2026-08-04
01:25 UTC under the crash-restart supervisor; relaunch line:
`nohup bash experiments/bottomup/v2/run_sweep070.sh >/dev/null 2>&1 &`). Batches: VERIFY (PASSED,
5.0% vs pre-committed 5.0%, zero placebo inclusions) → D1A1 → C1 → C2 → C3 → C4 → AB1 → C5 → CT1
(+ VD2/VD3), then it polls `batches/*.flag` for late arrivals until `queue_closed.flag` exists.
M = 442, L = 8,999. **Container reboots kill detached processes** (measured: the 00:04 reboot
killed the first run); the hourly Routine `sweep070-watchdog` (trig_01K9jC4ceHMbUkPQL7CgdVqJ)
revives it, regenerates the founder report, and commits snapshots — **delete the Routine when the
sweep completes.** THE DELIVERABLE is `docs/ranking/inclusion-campaign-report.md`, regenerated
after every batch grades. **Wall-clock estimate, measured not guessed: ~238 ensembles ≈ 14–18 h
from restart** (D1A1+C1+C2 within ~3–4 h, C3+C4 by ~8 h, AB1/C5/CT1 the tail).

**For any successor session:**

1. `tail experiments/bottomup/results/sweep070/sweep.log` and `cat .../state.json` — phase progress.
   If the process died (`ps aux | grep sweep070` empty), relaunch the same nohup line; it resumes
   from disk exactly (deterministic draw order, incremental CSVs).
2. When `VERIFY_STATUS` appears: **read it before trusting anything graded.** FAIL → the driver has
   already exited; report to strategist, do not weaken the check, do not grade.
3. **Commit accumulated sweep results periodically** (`cells.csv`, `draws/`, `graded_*.csv`,
   `VERIFY_STATUS`) — the container is disposable and an unmerged container is how results die.
4. When `graded_D1A1.csv` exists: report Q0 against the amendment's §5 decision rules (games-MAE
   recovery share). When `graded_C1.csv`/`graded_C2.csv` exist: report which dispositions moved vs
   the UNCALIBRATED S=7 grades. Any INCLUDE anywhere → stop-and-report to strategist (M-6 rule).
5. Outstanding non-compute items: reply lands on thread
   `2026-08-01-m-1-m-6-...` (done this session — check it stayed current), C1's M-6 re-grade **at
   S=7 on CTRL-A/B/C** (strategist ruled the old-panel re-grade stays separate from the tier-2
   re-run; the tier-2 re-run here does NOT discharge M-6), and the F6/Q0-class "no-column arm"
   ruling strategist still owes.

## Where to read sweep state

- `experiments/bottomup/results/sweep070/cells.csv` — observed runs (k=0), §4.8-keyed.
- `.../draws/<batch>__<arm>__<pos>.csv` — one row per (draw k, season): per-season metrics per draw
  (M-1(B): stored, never summarised). Deltas derive against the control cells exactly.
- `.../sweep.log`, `.../state.json` — progress + wall-clock timings.
- `.../VERIFY_STATUS` — PASS/FAIL + measured LOO rates + end-to-end placebo verdicts.
- `.../graded_<batch>.csv` — §4.6 cell reports; regenerate any time with
  `.venv/bin/python -m experiments.bottomup.v2.grade070 --batch <B>`.
- Phase order (structural gate): VERIFY → D1A1 (Q0 first) → C1 → C2 → C3 (flag set, registered) →
  VD2/VD3 dimension diagnostics.

---

## Decisions taken this session (decide-and-log; escalations flagged)

### D1 — Tier-2 window is per-position, and WR/TE cannot reach S = 12 cleanly

The dispatch says "grading at S = 12, tier 2 (2013–2024) — clear of the targets hole at all four
positions." **The S = 12 claim is true of target seasons but not reachable at WR/TE with the
adopted training windows, and I am not hand-rolling a way around it:**

- QB/RB: `first_feature_season = 2002` (adopted deep window), targets **2013–2024, S_pos = 12**.
- WR/TE: the targets hole (2003–2008) forces `first_feature_season = 2012` (feature season s needs
  lag seasons s−1..s−3 clear of the hole ⇒ s ≥ 2012). With `min_train_seasons = 2`, the first
  target is 2014 ⇒ targets **2014–2024, S_pos = 11**.

Reaching 2013 at WR/TE would require either `min_train_seasons = 1` (a methodology change nobody
registered) or training across the hole (the measured −0.0338 WR defect). Per §4.8, S is a
per-position property; the keys carry `S_pos` and the bare claim "S = 12" is not made for WR/TE.
**This is a deviation from the dispatch's letter, logged here rather than silently absorbed.**

### D2 — Arms with late-starting sources keep matched sub-windows inside tier 2

Same discipline as C1's CTRL-A/B/C, re-based on the ppr12 universe: an arm whose source starts
late gets its own control at its own window and reports its own `S_pos`; the §4.8 raise makes it
impossible to difference against anything else. Window map (targets clipped to ≤ 2024, first
target = max(2013 (QB/RB) / 2014 (WR/TE), ff + min_train)):

| control | ff | targets | used by |
|---|---|---|---|
| T2-A | 2002 (QB/RB), 2012 (WR/TE) | 2013/2014–2024 | base, F0, F2, F3, F6, C2 A1–A4/B1, most C3 |
| T2-B | 2015 | 2017–2024 | F1 (snap) |
| T2-C | 2017 | 2019–2024 | F4 (sep), F5 (routes) |
| T2-D | 2018 | 2021–2024 | C2 A5 (implied team total) |

### D3 — Q0's null ensemble (an arm that adds no column)

Q0 changes the fit population, not the design matrix, so §4.1's block permutation does not apply
(the F6 precedent). Matched null: **within-season permutation of the board-membership indicator
over the training population** — same restriction size, same estimator, provably no player-level
information. Documented as a construction decision, escalatable if strategist disagrees; graded
nothing until VERIFY passes anyway.

### D4 — Placebo in every batch

C1/C2 re-runs keep F0 (and F0D). Q0's registered m_b = 12 has no placebo; rather than silently
amending strategist's registration, the sweep carries a **calibration placebo arm** on the games
endpoint (seeded noise column appended to the availability spec) graded through the full rule,
contributing 0 tests per M-1..M-6 registry accounting, with the §6.2(c) registered prediction
(0 INCLUDE / 0 EXCLUDE, ≤ 1 HYPOTHESIS). C3's registration includes its own in-family placebo.

### D5 — §4.8 backfill keys for published batches

Backfilled per-control, from the registered CONTROLS maps (labelling, not re-derivation):
C1/B1 CTRL-A → `m_panel_halfppr12 / 2018-2024 / S=7 / ff=2012`; CTRL-B ff=2015; CTRL-C
`2019-2024 / S=6 / ff=2017`; C2 CTRL-A2 as CTRL-A; CTRL-D `2021-2024 / S=4 / ff=2018`.

### D6 — C3 odds tension: not resolved here

backend flagged the T0-11/N12 (odds) tension. C3 launches without an odds factor, exactly as
backend wrote it; reopening a dispositioned ledger row is strategist's call, not mine, and not
this session's bottleneck.

### D7 — Q0 gets its own family (T2Q: targets 2015–2024, S = 10)

Board-membership history (the ppr12 archive) starts 2013 and Q0-restrict needs ≥ 2 board training
seasons, so its first target is 2015 — the CTRL-A/B/C late-source discipline applied to the board
archive itself, with a matched control at the identical key. The amendment's blanket
"targets 2013–2024" is not reachable for this arm; deviation logged, not absorbed. The Q0 fit
asserts board coverage where it should exist, so a broken archive fails loudly instead of silently
reproducing the control. Inner bonus-calibration refits on pre-board sub-windows keep the incumbent
availability (they cannot be restricted to a population that has no board).

### D8 — Measured: the ppr12 archive is shallow before ~2017, and TE gains nothing from tier 2

Matched board veterans per season (ppr12, ≥10 = gradeable cell):
QB 8,9,11,13,13,18,20,20,24,19,24,26 · RB 3,3,8,11,23,34,… · WR 8,11,23,30,36,… ·
TE 2,5,7,5,8,11,13,16,19,14,19,19 (2013→2024). Non_ppr is no deeper; the raw archives are simply
shallow (26 total rows in 2013, zero crosswalk misses). **Realised S_pos at the 10-player floor:
QB 10 / RB 9 / WR 11 / TE 7.** The tier ruling's "S = 12 at all four positions" holds for target
seasons, not graded cells, and **TE remains the S = 7 position**. Reported to strategist in the
M-1..M-6 thread reply; early-season cells also grade rho on boards of 10–23 players, where the
§4.7 quantum is large — the machinery handles it, but power at QB/TE early seasons is thin.

### D9 — Campaign M corrected to 259 (+ 25 at C3)

`adr070.M_CAMPAIGN_BASE = 230` omitted batch C2's registered m_b = 29 (`batch-C2.md`, ee87b53).
Shrinking the denominator after the fact is the textbook error, so grading uses
M = 130 + 29 + 88 + 12 = **259**, and 284 once C3 grades. L = 5,999 (p-floor 3.33e-4) covers
M ≤ 300. Flagged to strategist rather than silently chosen either way.

### D10 — Timings, measured

Observed T2A control + VD1 runs, all four positions: 20.8 s wall on 3 workers. One permutation
draw: ~2.6 s wall (deep window ~4–9 s single-core; short families ~1.5 s). VERIFY (800 fixed
draws) ≈ 45 min; a typical null cell (~120 draws to h = 20) ≈ 5–10 min wall; the full sweep
(VERIFY + D1A1 + C1 + C2 + C3 + VD2/3, ~90 ensembles) is an estimated **1–3 days** — acceptable
under "tests are compute, not tokens," and resumable at any point.

---

## Status vs the six steps (final, 2026-08-03)

| step | state |
|---|---|
| 1 ADR-070 instrument | **DONE**: `adr070.py` + 27 tests (`a9f0d0e`), draw engine `ensemble070.py` (`071eb93`) |
| 2 tier-2 panel + keys | **DONE**: `adp_fmt` on WalkForward, T2 window map, keys raised on every join; backfill of 865 published rows (`a702bf8`) |
| 3 verification | **RUNNING**: VERIFY phase is the sweep's structural gate; FAIL exits before anything real grades |
| 4 Q0 (D1-A1) | **CODED + QUEUED first after the gate** (`d1a1_models.py`); smoke at TE: board bias −2.29 → +0.60, MAE 3.63 → 2.46 vs naive 3.12 — direction matches the registered finding |
| 5 C1/C2 re-run | queued behind D1A1; arms re-run (not re-grade-only), lazy k-arm VOID ensembles |
| 6 C3 reconcile + launch | **DONE**: adapter + registration (m_b = 25) + flag (`fee403a`); sweep picks it up in order |

**Sweep detached at 23:22 UTC, PID 10688.** No blocker.
