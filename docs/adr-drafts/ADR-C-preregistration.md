# ADR-C — Pre-registration convention

**Path:** `docs/adr/ADR-C-preregistration.md`
**Status:** Proposed
**Date:** 2026-07-26
**Owner:** Strategist (spec) / Backend (execution)

## Context

The guardrails require declaring metric and threshold before a test runs, BH across the **true** total test count, and a locked 2025 holdout. A partial convention already exists: `docs/preregistration/` holds three registrations (`PR-001-...md`, `PR-002-...md`, `PR-003-...md`) plus `holdout_access_log.jsonl` and `test_run_log.jsonl`. What is missing is a *specified* format, required fields, an amendment mechanism, an FDR-denominator convention, and any enforcement. Every guardrail is currently a habit resting on three ad-hoc files.

The dominant failure mode for a one-person research project is not fraud, it is **drift**: three exploratory looks, a fourth that comes out well, and a memory that reconstructs it as the plan all along. The second failure mode is **abandonment**: a convention with a 40-field template gets bypassed the first time it is inconvenient, and then permanently. The design constraint is therefore that a registration must be writable in under two minutes, and that skipping it must be *harder* than doing it.

This ADR **extends the existing `docs/preregistration/` tree**. It does not introduce a parallel one. The three existing registrations keep their filenames and their numbering; the next registration is `PR-004-...md`.

## Decision

### File format and location

Extend the existing directory. Registrations keep the established `PR-NNN-<slug>.md` naming and remain Markdown files; the machine-readable contract is a **YAML front-matter block** at the top of each, so the existing files stay human-readable and the numbering sequence is unbroken.

```
docs/preregistration/PR-001-....md            # existing, retrofitted with front matter
docs/preregistration/PR-002-....md            # existing
docs/preregistration/PR-003-....md            # existing
docs/preregistration/PR-004-need-scale-inertness.md   # next, this convention
docs/preregistration/families/F-NEEDSCALE.yaml        # family manifest, fixes m for BH
docs/preregistration/holdout_access_log.jsonl         # existing, now written by the loader
docs/preregistration/test_run_log.jsonl               # existing, now written by the runner
docs/preregistration/UNSEAL_LOG.md                    # new, append-only, human-readable
```

Front matter rather than a separate YAML file because a single file per registration means git shows an amendment as a diff, and because the prose body (rationale, power notes) belongs next to the fields, not in a second artifact that drifts from it. `families/` is new and is the only structural addition.

The two existing `.jsonl` logs are retained as-is and become **machine-written** rather than hand-maintained: `holdout_access_log.jsonl` gets one line per holdout access attempt (allowed or refused), `test_run_log.jsonl` one line per analysis run with its prereg id and content hash. Their existing schemas should be extended, not replaced; if a required field is absent, add it and backfill `null` rather than rewriting history.

### Required fields — nine, and no more

```yaml
---
id: PR-004-need-scale-inertness
test_registry_id: T-014          # links to the test registry; unique, never reused
family: F-NEEDSCALE              # FDR family; must exist in families/ and be open
mode: confirmatory               # confirmatory | exploratory
question: >
  Does NEED_ADJUSTMENT_SCALE change the top-1 recommendation at s=10 vs s=0?
metric: flip_rate_top1           # exactly one primary; secondaries in `secondary:`
threshold: "adopt R1 (delete parameter) iff flip_rate(10) < 0.02 and flip_rate(50) < 0.05"
data_scope: {seasons: [2021, 2022, 2023, 2024], holdout_unsealed: false}
frozen:
  at: 2026-07-26T14:02:00Z
  code_sha: 3f9a1c2
  seed: 20260726
  content_hash: sha256:ab12...   # hash of this file excluding `frozen.content_hash`
---
```

Optional: `secondary`, `resampling_unit`, `power_note`, `amendments`.

`resampling_unit` is optional only because `confirmatory` mode **defaults it to `season`** and CI rejects any other value unless `power_note` is present and non-empty. The default should be the guardrail, so that the lazy path is the correct path.

**Retrofit of PR-001 through PR-003:** add front matter with whatever is genuinely known, and set `mode: exploratory` for any of them whose metric and threshold were not demonstrably fixed before the run. Do not reconstruct a threshold from memory. A registration retrofitted with a remembered threshold is worse than one honestly marked exploratory, because it launders drift into the record.

### Tooling — the part that determines whether this is used

```
$ prereg new --family F-NEEDSCALE --mode confirmatory
```
Scaffolds `docs/preregistration/PR-NNN-<slug>.md` with front matter, auto-fills `id` (next number in the existing sequence), `frozen.at`, `frozen.code_sha`, `seed`, `content_hash`, allocates the next `test_registry_id`, opens `$EDITOR`. The human types `question`, `metric`, `threshold`, `data_scope`. Four fields. Under two minutes.

```
$ prereg check           # CI + pre-commit hook
```

And the enforcement that makes it stick: **analysis entrypoints refuse to run without `--prereg PR-...`**. Every result artifact embeds the prereg `id` and `content_hash` in its header, and the run appends a line to the existing `test_run_log.jsonl`. A result file whose embedded hash does not match the current registration is quarantined by CI.

### Amendments — visible, never silent

Git history alone is insufficient: a silent edit is a valid commit and nobody re-reads history. Mechanism:

- `frozen.content_hash` pins the file at registration.
- `prereg check` recomputes the hash. **Mismatch without a new `amendments:` entry is a CI failure.**
- Every amendment appends, in the front matter:
```yaml
amendments:
  - at: 2026-08-02T09:00:00Z
    fields_changed: [threshold]
    from: "flip_rate(10) < 0.05"
    to:   "flip_rate(10) < 0.02"
    reason: "Grid step made 0.05 non-discriminating; changed BEFORE any run."
    data_seen: false          # REQUIRED. true ⇒ mode auto-demoted to exploratory.
    new_content_hash: sha256:cd34...
```
- **`data_seen: true` irreversibly demotes the registration to `mode: exploratory`.** No override flag, no exception path. This is the one rule with teeth: it makes amending after a peek costly in exactly the way that keeps it honest, and it makes the cost automatic rather than a judgment call made by the person with the incentive.
- Any report generated from a registration with amendments must print the amendment count and each `data_seen` value adjacent to the headline result. Not a footnote.

### Exploratory vs confirmatory, and the FDR denominator

- **Exploratory registrations are mandatory but nearly free** — `id`, `mode`, `question`, `date`. No metric, no threshold. Purpose is solely to make the number of prior looks countable.
- **Exploratory results may never be reported with a p-value, a CI, or a comparison to a threshold.** CI enforces this by rejecting artifacts from `mode: exploratory` runs that contain `p_value`, `ci_lower`, `ci_upper`, or `significant` keys. Point estimates and plots only.
- **Exploratory tests do not enter the FDR denominator** — because they never produce a p-value to correct. The corresponding discipline: any hypothesis generated from exploration must be confirmed on data **not used in that exploration**. That is what the holdout is for, and it is a one-shot resource.
- **The denominator is fixed at the family manifest, not at analysis time.** `docs/preregistration/families/F-NEEDSCALE.yaml` declares `m:` — the count of confirmatory tests planned in the family — and `status: open | closed`. BH is applied within family over the declared `m`. Adding a confirmatory test to a `closed` family **reopens it**, increments `m`, and requires recomputing and re-publishing every prior BH adjustment in that family. Not optional, not a judgment call. This is the mechanism that makes "BH across the TRUE total test count" enforceable rather than aspirational: the count is written down before the tests run, and growing it retroactively is expensive and visible.

### HoldoutViolation

Defence in depth, cheapest layer first:

1. **Data-access guard (primary).** All season data loads through one function: `load_season(year, prereg_id)`. It reads the registration's `data_scope.seasons` and raises `HoldoutViolation` if `year` is outside it, or if `year == 2025` and `holdout_unsealed` is not `true`. Every call — allowed or refused — appends a line to the existing `docs/preregistration/holdout_access_log.jsonl`. No other load path exists; a direct filesystem read of the holdout is a lint failure.
2. **Unseal is a signed, one-shot, family-closing event.** `holdout_unsealed: true` requires a corresponding entry in `docs/preregistration/UNSEAL_LOG.md` (date, prereg id, family, reason, approver). Once a family unseals 2025, that family is **closed permanently** — no further confirmatory tests, no amendments, no re-runs. One look is one look.
3. **Test-suite guard.** A `pytest` autouse fixture raises `HoldoutViolation` on any holdout access from a test. Mock draft data gets the same guard with `MockDataViolation` — mocks are judge-only, never training, and that is enforceable at the loader.
4. **Pre-commit grep.** Literal `2025` in `analysis/` or `models/` outside a registration file or the loader itself fails the hook. Crude, catches the hardcode.
5. **Ordering check.** CI verifies the prereg file's commit timestamp precedes the result artifact's. **Honest limitation, stated in the ADR rather than hidden:** local timestamps are forgeable, so this is a discipline device, not an adversarial audit trail. Strengthening it costs one habit — push the registration to the remote before running, so the forge-side commit time is authoritative. Recommended, not enforced, because enforcing it would break offline work and that is how conventions die.

## Pre-committed decision rule

Not a statistical rule — an operational one, pre-committed so it is not renegotiated in the moment:

- A result without a matching `PR-` id and hash is **not a finding**. It does not go in `docs/decisions.md`, a commit message, the UI, or a conversation with a conclusion attached.
- A result from a registration with any `data_seen: true` amendment is **exploratory forever**, regardless of how the analysis is subsequently rerun.
- If the convention is bypassed more than **twice in any 30-day window** (measurable directly from `test_run_log.jsonl`: runs lacking a prereg id), the convention is too heavy and this ADR is revised — the failure is the process's, not the user's. Track it; do not moralize about it.
- If a family's declared `m` is exceeded more than once, the family was scoped wrong; require a written scoping note before the next family is opened.

## Consequences

- ~2 minutes of overhead per confirmatory test, ~20 seconds per exploratory one.
- The BH denominator becomes a real, auditable number rather than a recollection.
- The 2025 holdout gains a mechanical lock; a violation becomes an exception, not an oversight discovered later. The existing `holdout_access_log.jsonl` becomes trustworthy because it is written by the loader rather than by hand.
- `PR-001`–`PR-003` are retrofitted, and any of them without a demonstrably pre-fixed threshold is reclassified **exploratory**. Other past results with no registration at all are likewise grandfathered as exploratory — including the `lambda = 0.352` fit and the existing −1,070 / −226.4 point estimates. This is uncomfortable and correct: `lambda` was fit on the one draft that exists, with a cluster-robust SE on 10 clusters, and its `z = 5.04` should not be quoted as confirmatory until it is re-derived under a registration with a wild cluster bootstrap-t.
- This ADR itself is appended to `docs/decisions.md`, per the existing single-file append-only ADR log convention.
- One-person projects rarely sustain heavy process. Nine fields, four typed by hand, and a `--prereg` flag that blocks the run is roughly the maximum that survives contact with a Sunday afternoon.

## What would falsify this

- **Falsifies the format:** bypass rate exceeds the 2-per-30-days threshold. Cut fields — `question` and `threshold` are the irreducible pair; everything else is negotiable.
- **Falsifies the family-manifest denominator:** families in practice cannot be scoped in advance (m routinely wrong by >2×). Then BH-within-family is fiction and the alternative is a single project-wide denominator that grows monotonically — much more punishing, and the right answer if pre-scoping genuinely fails.
- **Falsifies the `data_seen ⇒ exploratory` rule:** a case arises where a genuinely blind amendment (a bug fix in the harness, discovered by running on synthetic data) is wrongly demoted. Handle by adding a `synthetic_only: true` qualifier — **not** by adding a human-judgment override, which would restore the exact discretion the rule exists to remove.
- **Falsifies the holdout mechanism:** a violation occurs despite all five layers. Then the loader is not the only data path, and finding the second path is the fix.
