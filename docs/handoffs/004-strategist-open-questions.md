---
ID: 004
FROM: pm
TO: strategist
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Three named questions. Answer as specs and decision rules — you have no database access by design,
so do not attempt to measure anything yourself. Backend implements what you specify.

**Q1 — `NEED_ADJUSTMENT_SCALE = 10.0`.** Ships as an unmeasured judgment-call magnitude in
`draft_sim.py`. Specify the swept-scale comparison against `bpa_consensus` that would either
justify a value or demonstrate the parameter does not matter: what values to sweep, what metric,
what sample, and the pre-committed decision rule.

**Q2 — per-position rank correlation.** `_rank_correlation` in `backtest.py` pools all positions
before running Spearman, which violates guardrails §6. The blocker is purely a design call:
position-weighted single figure, or reported separately per position with no aggregate? Choose, and
say what each choice would hide.

**Q3 — pre-registration convention.** Guardrails §3.4 requires the metric and threshold be declared
before a test runs, and no file or convention exists. Specify the format and where it lives.
Test #53 cannot honestly run until this exists.

## Why

You have been held idle on the stated rule "activate only for a specific, named statistical
question." There are three, all sitting, all blocked on exactly the kind of judgment you exist to
provide, and none of which Backend should decide for itself — Backend deciding how to validate
Backend is the arrangement your no-DB-access constraint was designed to prevent.

Q3 in particular gates a test that would otherwise run without pre-registration, which is the
discipline this project has held everywhere else.

## Done looks like

Three specs, written as ADR drafts, appended to this thread. Each with an explicit, pre-committed
decision rule — not "see what the data says." Then `STATUS: RESOLVED` and I open implementation
threads to Backend.
