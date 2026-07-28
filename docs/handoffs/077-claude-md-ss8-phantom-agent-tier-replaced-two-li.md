---
ID: 077
FROM: librarian
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-27
---

## Ask
Per `docs/RUN-2026-07-27-overnight.md` PHASE 3 Chain 2, I rewrote `CLAUDE.md` §8 ("Agents and
gates" → "Agents and review") on branch `docs/phase3-chain2-claude-md-agents`
(commit `8011925`), pushed, not merged. It described a "Builder / Verifier / Statistician /
Red-team" tier with standing per-task/per-milestone gates and Red-team block authority — none of
this was ever built. §8 now lists the actual roster (backend, data-ops, frontend, librarian,
strategist, researcher, pm, design, fable, founder), sourced from `.claude/agents/*.md`
frontmatter and `docs/operating-model.md`, and states plainly that there is no standing automatic
per-task gate — review in practice is: self-check against `docs/operating-model.md`'s evidence
table, PM verification gatekeeping via handoff threads, Strategist review by named request only
(no DB access, no formal block authority), Fable's weekly framework-level pass. §3's cross-ref
to §8 was reworded to match ("reviewed per the roster and process in §8" instead of "gated").
§2 had no phantom-tier references, left unchanged.

**Two live (non-historical) docs still assert the old model exists and were left untouched —
out of scope for this thread's chain, flagging for you to route:**
1. `docs/statistical-guardrails.md` §10 "Who enforces this" (lines 226-233): states "Per
   `CLAUDE.md` §8: the **Red-team** agent's mandate explicitly includes checking every backtest
   against this document before it is accepted. Red-team has standing authority to block... The
   **Statistician** agent designs the methodology up front..." This is read "before running any
   backtest" per CLAUDE.md §12 — it's an active instruction, not a log entry, and now
   contradicts the corrected §8.
2. `docs/test-registry.md` line 19: "Nothing is DONE here until it is in the repo, covered by
   tests, and past Verifier." — the DONE-status legend, still live, still references the
   nonexistent Verifier agent as a status criterion.
Also noted but explicitly historical-log and left alone per librarian's own reading discipline:
`docs/status.md` lines 680 and 2397 (2397 is itself a prior session already flagging this same
gap).

## Why
Without a real enforcement mechanism named in `statistical-guardrails.md` and `test-registry.md`,
anyone reading those two docs on their own (which CLAUDE.md §12 tells them to do) will believe a
blocking Red-team/Verifier gate exists and defer to it — a gate that will never actually run. That
is a worse failure mode than no gate: false confidence that a check happened. This needs an actual
decision (assign real enforcement to an existing role, e.g. Strategist for guardrails-compliance
review and PM/self-check for DONE status, or state there is no automated enforcement) — a decision
that changes process, which is PM/founder's call, not mine to make unilaterally per librarian's
"escalate, don't resolve" rule.

## Done looks like
Either: (a) PM or backend edits `docs/statistical-guardrails.md` §10 and
`docs/test-registry.md`'s status legend to name the real enforcing role(s) consistent with the
corrected `CLAUDE.md` §8, or (b) PM explicitly defers this with a reason recorded here. Either way,
reply in this thread and set STATUS.
