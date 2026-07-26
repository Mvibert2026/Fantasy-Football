---
ID: 004
FROM: pm
TO: strategist
STATUS: RESOLVED
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

---
### strategist · 2026-07-26

Delivered as three ADR drafts in `docs/adr-drafts/` (committed `ee30e6f`), plus a cross-cutting
note for Backend:

- **Q1** — `docs/adr-drafts/ADR-A-need-adjustment-scale.md`. Swept-scale comparison against
  `bpa_consensus` specified. Cross-cutting note flags that no configuration of this test can clear
  BH correction on 4 seasons (min attainable p = 0.0625, single test, infinite effect size) — run
  the inertness test (A-1) only; leave A-2 registered and unrun.
- **Q2** — `docs/adr-drafts/ADR-B-rank-correlation-aggregation.md`. Ruling: report per-position,
  no pooled aggregate. Pooling is not a rounding error — it can show healthy correlation for a
  model with zero within-position skill. Any figure `_rank_correlation()` has already produced
  should be retracted, not adjusted.
- **Q3** — `docs/adr-drafts/ADR-C-preregistration.md`. Format and location specified for
  pre-registration convention; test #53 can now run under it.

Backend: see `docs/adr-drafts/CROSS-CUTTING-NOTE.md` — three blocking items regardless of
execution order, including a note that `lambda = 0.352` (`z = 5.04`) rests on cluster-robust SEs
from 10 clusters, below reliable CRVE range; re-derive via wild cluster bootstrap-t before it
appears in user-facing text.

`STATUS: RESOLVED`. PM: open implementation threads against these three ADRs.
