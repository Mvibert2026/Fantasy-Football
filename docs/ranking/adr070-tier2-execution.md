# ADR-070 instrument + tier-2 panel — execution log

**ranker, 2026-08-03.** Live document for the six-step dispatch: implement ADR-070, rebuild the
panel at tier 2, verify the instrument, run D1-A1 Q0, re-run C1/C2, reconcile and launch C3.

---

## NEXT STEP

*Rewritten on every update. Being cut off is the expected case.*

1. **DONE (prev. session, `a9f0d0e`):** `experiments/bottomup/v2/adr070.py` — the §4 decision
   machinery (Besag–Clifford sequential p, calibrated C, verdict taxonomy, BH at campaign M,
   §4.7 snap, §4.8 ProvKey enforced by raise) + `tests/test_adr070_instrument.py` (27 tests).
2. **IN PROGRESS:** `experiments/bottomup/v2/ensemble070.py` — the permutation-draw runner
   (§4.1 joint within-season row permutation of the arm's own column block, seed
   `sha256(f"{arm}|{position}|{season}|{k}")`), plus the tier-2 window map below.
3. **THEN:** `sweep070.py` — phase-gated queue driver, detached, resumable, writes to
   `experiments/bottomup/results/sweep070/`. Phase order hard-coded:
   `VERIFY → (gate: LOO calibration must PASS) → Q0 (D1-A1) → C1 re-run → C2 re-run → C3`.
   The driver **refuses to grade real factors until VERIFY passes** — structurally, not by
   convention. Launch it as soon as it and the VERIFY tasks exist; append later phases to the
   queue file while it runs.
4. Backfill §4.8 keys onto B1/C1/C2 CSVs (script, no numbers re-derived).
5. Q0 mixin (population refit of the availability model, graded on games MAE, M-panel primary).
6. C3 adapter to the real `factors_c1`-style block interface + registration + queue append.

## Where to read sweep state (for any successor)

- Queue: `experiments/bottomup/results/sweep070/queue.jsonl` (one task per line, driver appends
  status to `state.json`).
- Draws: `experiments/bottomup/results/sweep070/draws/<cell_id>.csv` — one row per draw with the
  full per-season delta vector (M-1(B): stored, never summarised).
- Log: `experiments/bottomup/results/sweep070/sweep.log`.
- Verification verdict: `experiments/bottomup/results/sweep070/VERIFY_STATUS` (PASS/FAIL + rates).

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

---

## Status vs the six steps (2026-08-03, coordinator check-in)

| step | state |
|---|---|
| 1 ADR-070 instrument | **half done, committed** (`a9f0d0e`, prev. session). Missing: ensemble runner — in progress |
| 2 tier-2 panel + keys | designed (D1/D2/D5), not coded |
| 3 verification | designed (phase-gated into the sweep driver), not run |
| 4 Q0 | designed (D3/D4), not coded |
| 5 C1/C2 re-run | queued behind VERIFY gate |
| 6 C3 reconcile + launch | adapter design settled; not coded |

No blocker. The four silent hours were spent reading the harness before editing it; the
correction from here is commit-per-artifact.
