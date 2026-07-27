---
ID: 020
FROM: pm
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: test #53
---

## Ask
Implement ADR-C from `docs/adr-drafts/ADR-C-preregistration.md`. Read it in full first — it is
specific about format and enforcement.

Key point: it **extends** the existing `docs/preregistration/` directory, which already holds PR-001
through PR-003 plus `holdout_access_log.jsonl` and `test_run_log.jsonl`. Do not create a parallel
tree.

## Why
Guardrails §3.4 requires declaring metric and threshold before a test runs, and there is currently no
file, format, or enforcement — every guardrail is a habit. Test #53 cannot honestly run until this
exists.

The ADR's central mechanism is worth preserving exactly as written: an amendment made after seeing
data **irreversibly demotes the registration to exploratory**, with no override. That rule is what
gives the convention teeth, and it must be automatic rather than a judgment call made by the person
with the incentive.

Keep it light. The ADR is explicit that an onerous convention gets bypassed and then abandoned —
nine fields, four typed by hand.

## Done looks like
Convention implemented, the `--prereg` guard blocking analysis entrypoints, the holdout data-access
guard raising `HoldoutViolation`, tests covering both. Existing PR-001..003 grandfathered as
exploratory per the ADR. Commit hash and test count.

---

### backend · 2026-07-26

Implemented in `src/preregistration.py` (new `Registration`/`Family` machinery, additive —
the original `PreRegistration` loader, run log, and BH functions are untouched) and
`src/holdout.py` (`load_season`, additive).

**Landed:**
- Nine-field confirmatory / four-field exploratory registration format
  (`load_registration`, `require_confirmatory`) alongside the original loader.
- The rule with teeth: `record_amendment(..., data_seen=True)` irreversibly rewrites
  `mode: exploratory` into the file, no override, and `require_confirmatory` refuses a
  demoted registration.
- Content-hash integrity (`compute_content_hash`/`verify_content_hash`/`check_registration`)
  — a silent edit with no matching `amendments:` entry fails the check.
- Family manifests (`docs/preregistration/families/*.yaml`) fixing the BH denominator
  before tests run; closed families reopen on a new confirmatory test, `closed-unsealed`
  families never do.
- `holdout.load_season(year, prereg_id)` — the primary data-access guard. Raises
  `HoldoutViolation` for a year outside the registration's `data_scope.seasons`, or for the
  2025 holdout unless `data_scope.holdout_unsealed: true` **and** a signed
  `docs/preregistration/UNSEAL_LOG.md` entry exists for that `prereg_id` (defense-in-depth
  beyond the ADR's literal text — the front-matter flag alone is spoofable). A permitted
  holdout read routes through the existing `HoldoutLock.final_evaluation` context, so it
  lands in the same `holdout_access_log.jsonl`, not a second log.
- `validate_exploratory_artifact` rejects `p_value`/`ci_lower`/`ci_upper`/`significant` on
  any exploratory-mode result.

**Deferred, explicitly out of scope for this session** (restricted to
`src/preregistration.py` + the holdout guard per the dispatch instructions, to avoid
colliding with other agents editing other files this round):
1. The `prereg` CLI (`prereg new` scaffolding, `prereg check` as a pre-commit/CI hook).
   Right now nothing stops an analysis script from skipping `require_confirmatory` — the
   guard exists but isn't wired to an enforced entrypoint. This is the next thread if the
   convention is meant to have teeth rather than being available-but-optional.
2. Retrofitting PR-001..003 into the new front-matter format. They keep their original
   flat format and still load and pass their own tests unchanged.
3. No PyYAML in this environment, so nested fields (`data_scope`, `frozen`, each
   `amendments` entry) are restricted to single-line YAML flow style, parsed by a small
   hand-rolled parser — not full multi-line YAML block mappings. Documented as a real
   format constraint in `docs/decisions.md`, not a stylistic choice.

**Full ADR entry:** `docs/decisions.md`, "2026-07-26 — ADR-C: pre-registration convention,
extended (thread 020)".

**Tests:** 65 passed, `tests/test_preregistration.py` + `tests/test_holdout.py` (`-q`,
targeted run per instruction — full suite not run this session to avoid DB contention with
concurrent agents). Commit: see `docs/CURRENT-STATE.md` / git log for the hash of this
session's commit.

STATUS: RESOLVED
