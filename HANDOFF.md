# HANDOFF — ADP vs production analysis, 2026-07-30

Checkpoint write, container may be reclaimed. Commit `e334473` pushed to
`origin/worktree-agent-a3f0bc3cc3efb7185`. This file describes exactly what has and hasn't been
done so a resumed session doesn't redo (or worse, re-spend) anything.

## **THE 2024 HOLDOUT HAS ALREADY BEEN TOUCHED. DO NOT RE-RUN AND TREAT A NEW HOLDOUT NUMBER AS FRESH.**

`analysis/adp_vs_production.py` trains/explores on 2018-2023 and reports 2024 once, per
`docs/statistical-guardrails.md` §3's "touch it once, at the end" rule. That has already happened
— the 2024 numbers are in `data/qa/adp-vs-production-2026-07-30.json` under every family's
`"holdout_2024"` key, and are narrated in `docs/analysis/adp-vs-production-2026-07-30.md` §2. If
you resume this and change the residual design, the factor buckets, or anything upstream of the
holdout split, **that invalidates the existing holdout look — you cannot get a second clean look
at 2024 with the same methodology.** Either (a) don't touch the analysis design and just extend
reporting/formatting, or (b) if a real design change is needed (e.g. per strategist review, thread
096), treat it explicitly as a NEW analysis with its own holdout discipline, not a rerun of this
one — say so in the writeup, don't quietly overwrite `holdout_2024`.

2025 was never in scope at all (the FFC ADP backfill covers 2018-2024 only), so the project's
actual locked holdout season is untouched by construction, separately from the 2024 internal
holdout discussed above.

## What has been measured

All six pre-registered factor families, full pooled/train, per-era (2018-2020 vs 2021-2023), and
holdout (2024) tables — see `data/qa/adp-vs-production-2026-07-30.json` and the writeup:

1. **Position** — done. RB overpriced, WR/TE underpriced (train); did NOT clearly survive the
   2024 holdout at the unconditional level (RB flipped sign).
2. **ADP round bucket** — done. Early rounds negative residual, late rounds positive — flagged as
   partly a regression-to-the-mean artifact (§1.5 of the writeup), not standalone evidence.
3. **Age × position** — done. Young WR/TE (≤23) is the strongest, most stable result in the whole
   analysis (holds both eras).
4. **Prior-season games missed** — done. No reliable pattern found (sign flips between eras).
5. **Team change** — done, but narrower than what was asked. `play_callers` (coach/coordinator
   identity) has ZERO rows in this environment's `nfl.db` — only literal team-roster change was
   testable, not coordinator change, which is what the dispatch actually wanted (`coach_id` is
   first-class in this schema for exactly this reason). No reliable pattern found on the narrower
   proxy either.
6. **Prior volume-vs-efficiency split** — done. No reliable pattern found (small-n buckets, noisy).

**Diagnostic (not one of the six pre-registered families, added after §1.5's caveat forced it):**
position residual conditional on round bucket. This is the strongest, most defensible single
result — early-round RB underperforms same-round peers at every other position by ~3x. Also
computed on train seasons only; not separately re-checked against the 2024 holdout as its own
family (would need a seventh pre-registered test to do that cleanly — noted as follow-on work,
not done).

## What has NOT been done

- No draft-simulation-based evaluation (guardrails §6's stated next step beyond list/rank
  correlation) — this analysis is list/residual-based throughout.
- No real 10-team historical ADP validation — everything runs on FFC's 12-team mock-draft archive
  (see writeup §0). If someone finds or builds a real 10-team source, this whole analysis should
  be re-run against it as a genuinely new pass, not patched.
- No coordinator-identity (`play_callers`) ingestion attempted — logged as follow-on in
  `docs/ideas-inbox.md`, not started.
- No ADR opened, no ranker/model code touched — deliberate, per the dispatch's explicit
  instruction not to duplicate the ranker's concurrent RB/QB/TE component-model work.
- The Opus-tier methodology review this needs before reaching the ranking model has NOT happened
  yet — thread 096 (`docs/handoffs/096-adp-vs-production-methodology-review.md`) is OPEN, addressed
  to `strategist`, unanswered as of this checkpoint.

## Single next step if resuming

Do not re-run the analysis. Check `docs/handoffs/096-...md` for a `strategist` reply. If answered
and it calls for a design change, treat that as a new analysis (new holdout discipline, as above).
If unanswered, either wait or escalate — this thread, not a rerun, is the correct next action.

## Full pytest run status

A full `pytest -q` was started in the background before this checkpoint to confirm nothing broke.
**It timed out after 280s with no output captured (killed, exit 143) — inconclusive, not a
failure signal, and not yet re-attempted with a longer budget.** What IS confirmed:
`tests/test_holdout_audit.py` alone passed 3/4 on its own (fast, ~0.05s) — the one failure,
`test_no_new_direct_sqlite_connections_in_src` on `ingest_sleeper_projections.py`, is pre-existing
(thread 094), not caused by this session's changes, which live entirely under `analysis/` and
`docs/`, outside `src/`. The new `analysis/` script has no tests of its own (not requested; a
one-off measurement script, not shipped infrastructure). **Next session should re-run `pytest -q`
with a longer timeout (or in the background via `run_in_background`) to get a real full-suite
count before reporting one** — do not assume green, and do not assume red; it is simply unmeasured
past the point this checkpoint captured.
