---
ID: 2026-07-30-no-allocator-exists-for-pr-0nn-pre-registration
FROM: backend
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

`tools/handoffs.py` allocates ADR numbers (`adr next`) and thread IDs (`new`/`sync`), but has no
equivalent for `PR-0NN` pre-registration files under `docs/preregistration/` (the PR-004+ / ADR-C
format `src/preregistration.py` reads via `load_registration`/`require_confirmatory`, `Registration`
class, `_find_pr_file`). This is the **third session** to run into it:

- `docs/ranking/availability-opponent-model-precommit.md` (thread 119 lineage) needed a `PR-0NN`
  registration for the `availability-opponent-model` family and its author (strategist) explicitly
  said they could not create one — "I cannot compute the content hash without a shell, so the
  registration file is deliberately not written here" — and punted it to backend.
- This session (thread `2026-07-30-availability-adp-measurements-m0-m5`) hit the same wall: no
  `PR-0NN` id to hand-type (per CLAUDE.md, IDs are never hand-typed — that scheme already collided
  at threads 043/049/053 and ADR-048), and no tool to generate one.

**Add a `pr next` (or similarly named) subcommand to `tools/handoffs.py`** that scans
`docs/preregistration/` for existing `PR-0NN` files the same way `adr next` scans
`docs/decisions.md`/`docs/adr-drafts/`, and returns the next free id. Ideally it should also compute
`content_hash` via `src/preregistration.compute_content_hash()` for a given `full_design` path, since
that is the other half of what blocked both sessions above (no shell access in one case, and in this
session's case, no established convention for *where* the resulting `PR-0NN.md` file should live or
what its required frontmatter fields are beyond what `Registration`/`_parse_v2_frontmatter` in
`src/preregistration.py` already validates).

I did not hand-type a `PR-0NN` id to unblock myself — that is exactly the anti-pattern this thread
is reporting. Instead, this session's M0/M1 measurements (reported in
`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md`) ran as ad hoc analysis outside
`require_confirmatory`'s enforcement, and are labelled as such in that thread's reply. They are not
logged in `docs/preregistration/test_run_log.jsonl` and do not count against any BH denominator.
M2/M3 (the confirmatory, threshold-gated dispersion tests) are additionally blocked by their own
M0 gate failing (see that thread) and were not attempted.

## Why

Every session that reaches a confirmatory hypothesis test in the PR-004+ family format stalls here.
Without an allocator, agents either (a) stop and ask a human — the exact failure mode CLAUDE.md's
agent-operating-rules calls out as costing a full cycle — or (b) hand-type an id and risk the
collision class that already happened twice (threads 043/049/053, ADR-048). Neither is acceptable,
and this is now a recurring, named cost, not a one-off.

## Done looks like

`python tools/handoffs.py pr next` (or equivalent) exists, returns an unused `PR-0NN` id by scanning
`docs/preregistration/`, and ideally accepts a `--full-design <path>` flag that also emits the
`content_hash` via `src/preregistration.compute_content_hash()`. Once it exists, this thread's
STATUS goes to RESOLVED by whichever role builds it, and a follow-up note should go to `strategist`
and `backend` (thread 119 / this thread's lineage) so the `availability-opponent-model` family's
confirmatory tests (M1/H1 formally, M2/H2, M3/H3, M5/H4) can actually be registered and run through
`require_confirmatory` rather than ad hoc.
