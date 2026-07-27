# Overfitting exposure and whether pre-registration binds — 2026-07-27 (Priority 2D)

**Verdict in two sentences: accumulated forking-paths exposure against the 26 seasons is real but
modest and concentrated in a short list of fitted constants — the shipped artifacts are mostly
consensus-derived plumbing with nothing to overfit, and the one pre-registered test that returned
null (PR-002) was reported as null, which is the strongest available evidence the discipline is
genuine. The pre-registration machinery, however, binds against *accident* only: the ADR-C
season-gate has zero production callsites, the holdout unlock is self-service, no test audits the
access logs, and a name collision makes ungated season loads look gated.**

---

## 1 · Forking-paths exposure, estimated

### What is mechanically countable

- **49 ADRs** (ADR-001–ADR-049 in `docs/decisions.md`) accumulated over roughly three project-days,
  the majority predating ADR-C (thread 020, implemented `be3deb3`).
- **51 entries** in `docs/preregistration/test_run_log.jsonl` — the logged-run discipline is in
  actual use, which makes the *post*-ADR-C exposure boundable, exactly as designed.
- **3 pre-registrations** (PR-001 carry-concentration, PR-002 spike-week persistence, PR-003
  hero-RB simulation) — and PR-002's null was accepted and then *built upon* (ADR-E's S2 rules
  derive from it). A registry that only ever confirms is theatre; this one has a recorded null
  with consequences, which is the single best fact in this section.

### The named output-contingent choices against history (the exposure that matters)

Pre-ADR-C decisions that fitted, tuned, or selected against the 26-season history without
multiplicity accounting, as recorded in the repo itself:

1. **Estimator swap after inspecting output** — the isotonic rank-curve was "discarded after
   inspection" when it put a QB at overall #1 (`make_board.py:40-48`). Documented, diagnostically
   reasoned, and still a post-hoc selection against the same data.
2. **Replacement levels** — RB/WR split "moves ±1 rank by year selection" (CURRENT-STATE
   constants table): year-window sensitivity was examined, and the shipped values sit inside an
   acknowledged instability band.
3. **`NEED_ADJUSTMENT_SCALE`** — explored, argued unidentifiable, deleted (D-001). The
   exploration itself consumed looks at the data.
4. **`delta = 0.10`** — an admitted unvalidated prior (D-004), pre-registered kill rule attached.
5. **Archetype thresholds** — ADR-034's "TE T1@23" numeric move, bounds-checked but
   output-adjacent (`availability.py:106-109`).
6. **`DEFAULT_LAMBDA` functional form** — whether the form was fixed before or after seeing the
   2025 draft data is **unresolved from the repo** (the B1 question in the withdrawn brief; the
   ADR records n, SE, z but not form-selection order). Stated as unresolved, not assumed either way.
7. **`RELEVANT_DEPTH` / depth cutoffs** — roster arithmetic, low risk, listed for completeness.

Roughly **6–8 fitted or selected quantities** against the shared history, informally. Two honest
qualifiers in opposite directions: (i) the *unrecorded* looks (every "let me check whether that
helped" that never reached an ADR) are uncountable by construction — that is the ADR-C rationale,
not a gap this review can fill; (ii) the *consequences* are capped by what ships — the current
board is consensus re-scored (2B), so pre-ADR-C overfitting could contaminate secondary constants
(replacement levels, curves, availability parameters) but there is no shipped proprietary model
for it to have contaminated. The serious exposure window opens with ADR-E's first confirmatory
run, which is why the bindingness question below matters more than the retrospective count.

## 2 · Does the machinery actually bind?

The mandate's test: "a holdout requiring a signed unseal is a guardrail only if the seal cannot
be worked around. Check whether it can." **It can, at three escalating levels — and one of them
requires no working-around at all.**

### Level 0 — you can simply not use it (the real gap)

Enforcement is **opt-in per entrypoint**. `DEFAULT_LOCK.guard()` is called at four live
entrypoints (`backtest.py:702`, `export_strategies.py:53`, `run_draft_sim.py:42`,
`spike_persistence.py:322`) — good coverage of the analyses that exist. But seven modules connect
to the database directly (`sqlite3.connect`, legitimately for ingestion), and nothing intercepts
a *new* analysis module that reads season-2025 rows without volunteering for the guard.
`statistical-guardrails` / CLAUDE.md §6.1 requires the access layer to refuse post-cutoff rows
**structurally**; the current guarantee is procedural at the module boundary — precisely the
distinction ADR-E §3.2(3) itself insists on for folds.

Compounding it, a **name collision manufactures false confidence**: the ADR-C prereg-tied gate is
`holdout.load_season(year, prereg_id)` — which has **zero production callsites** (only
`tests/test_holdout.py` calls it) — while production code calls `ds.load_season(conn, season)`
(`run_availability.py:51`, `run_draft_sim.py:46`, `export_strategies.py:56`,
`mock_validation_report.py:211`), a *different, ungated* dataset loader. A reader greps
"load_season", sees it everywhere, and concludes season reads are prereg-gated. They are not.
CURRENT-STATE admits the gate is "**not yet enforced at any entrypoint**" (Built section, ADR-C
paragraph) — the admission is honest; the risk is that the admission lives in one paragraph while
the code's surface suggests otherwise.

### Level 1 — walk through the gate (logged)

`final_evaluation(reason=…)` and `release_for_final_fit(reason=…)` are **self-service context
managers**: any code that types a reason string unlocks the holdout (`holdout.py:127-165`). Every
entry is logged to `holdout_access_log.jsonl` — the design is "auditable, not preventable," which
is a legitimate design for a single-operator project. But **nobody audits the audit trail**: no
test or `check` inspects the access log (it currently holds 3 entries; nothing would fail if it
held 300), and no check asserts that `UNSEAL_LOG.md` does not exist (it currently does not —
verified — meaning **the holdout has never been formally unsealed**, which is worth stating
plainly as a clean bill). A guardrail whose evidence trail nobody reads binds only until the
first agent under deadline pressure discovers that it doesn't.

### Level 2 — forge the signature

`prereg.append_unseal_log()` writes the "signed" entry — a markdown line with an approver name
supplied by the caller (`holdout.py:243-249` checks only that a matching entry exists). There is
no cryptography and no human-in-the-loop step; "signed" means "a string was appended." Against a
malicious agent this is nothing; against an honest-but-drifty one it is a speed bump plus a git
trace. Consistent with the project's threat model (accident, not adversary), but the word
"signed" overstates it and should not be relied on in any claim about the 2025 read's integrity —
the *reviewable git history* of `UNSEAL_LOG.md` and the access log is the actual control.

### Assessment

For the project's real threat — an honest agent, twenty iterations of "just check whether that
helped" (`holdout.py:4-6`) — the machinery as built is **adequate at the four wired entrypoints
and absent everywhere else**, and its evidence trail is write-only. The seal can be worked
around; more importantly, for any new code path it does not need to be. The fixes are cheap and
listed below. One genuinely positive finding to keep: the **lock-governs-selection-not-fitting**
design (`holdout.py:16-20`, `release_for_final_fit`) is conceptually right and prevents the
classic overcorrection of shipping a 2026 board that ignores 2025.

## 3 · Work orders

**H1 — Audit the audit trail in CI** [backend, small]
A test (suite-embedded, like `test_handoffs.py`) that: (a) parses `holdout_access_log.jsonl` and
fails on any `FINAL_EVALUATION_OPENED` or `FINAL_FIT_OPENED` event whose reason does not
reference a registration id present in `docs/preregistration/`; (b) fails if `UNSEAL_LOG.md`
exists at all until the first sanctioned unseal (then pins its expected entry count); (c) fails
on any `DENIED` event newer than the last reviewed marker — a DENIED means someone *tried*, and
that is worth a human glance. Converts write-only logs into tripwires.

**H2 — Kill the load_season name collision** [backend, trivial]
Rename `holdout.load_season` → `holdout.load_season_registered` (or rename the `ds` loader).
Zero production callers means zero breakage — the rename is free today and not free after ADR-E
wires it.

**H3 — Wire the prereg gate before ADR-E's first confirmatory run** [backend, ~1 session —
already specified in thread 020's deferred items]
The `prereg` CLI / entrypoint enforcement deferred in the thread 020 reply stops being deferrable
when F-BOTTOMUP-CORE registers: ADR-E's §3.2(4) per-fold assertion and §10 budget only bind if
season reads route through the registration. Sequence it as a *prerequisite* of the first
confirmatory run, not a parallel chore.

**H4 — Structural read guard, cheap version** [backend, small]
Short of a real DB proxy: a test that greps `src/` for `sqlite3.connect` outside an allowlist
(the seven ingest/db modules) and fails on new direct connections, forcing new analysis code
through `db.CutoffEnforcedStore` / the guard. Crude, boundary-enforcing, and in the spirit of
"structural, not procedural" at a few lines' cost.

**Accepted risks, stated:** no defence against deliberate log deletion or forged approvals beyond
git history (threat model is accident); the retrospective exposure of §1 cannot be reduced, only
carried honestly — its practical mitigation is that ADR-E's baselines are refit under the same
protocol (§7.1), so a contaminated constant would have to beat an identically-treated baseline to
mislead anyone.
