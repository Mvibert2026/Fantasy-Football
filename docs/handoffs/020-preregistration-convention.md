---
ID: 020
FROM: pm
TO: backend
STATUS: OPEN
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
