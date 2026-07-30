---
ID: 2026-07-30-operator-standing-check-2026-07-30-handoffs-py-r
FROM: operator
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
`tools/handoffs.py` line 31 `ROLES` list does not include `operator` or `verifier`, even though
both were added to the agent roster in `CLAUDE.md` today (2026-07-30). `handoffs.py new --from
operator ...` is hard-rejected by argparse's `choices=ROLES` (line 761) before any thread is
written. This session worked around it by importing the module and calling `cmd_new()` directly
with a Namespace carrying `frm="operator"`, bypassing the CLI's stale choice list — `cmd_check`
(line 688) only validates `TO`, not `FROM`, so the resulting threads pass the mailbox check. That
workaround will not occur to every future operator/verifier session; most will hit the CLI error
and either give up opening the thread or hand-type a filename, defeating the allocator's collision
guarantee.

## Why
The operator and verifier roles are explicitly "read-only … findings go back to the owning role as
threads" — if the tool that files those threads doesn't recognize the role, the mechanism the
whole gate depends on silently degrades to "operator reports in chat only," which is the exact
failure mode operator exists to prevent (see CLAUDE.md operating-model, "the seam is your job").

## Done looks like
Add `"operator"` and `"verifier"` to `ROLES` in `tools/handoffs.py` (line 31), confirm
`handoffs.py new --from operator --to pm --subject "..."` succeeds from the CLI without a
workaround, and `handoffs.py check` still passes.
