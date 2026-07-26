### Budget calibration log — session of 2026-07-26

Readings are 5-hour window percentages, cumulative across the Cowork PM chat and all Claude Code
sessions running concurrently. Weekly (all models) shown where it moved.

| Reading | 5-hour | Weekly | What was running | Verified complete? |
|---|---|---|---|---|
| Baseline | 47% | 38% | Cowork planning only — 4 subagents (~220k tokens): source audit, 3 ADRs, fidelity harness | Yes — all three artifacts committed |
| +2 pts | 49% | 38% | **Full sprint-1 bootstrap in Code**: 6 agents installed, CLAUDE.md, /inbox, permissions merged, 5 threads answered, 1 commit | Partially — closeout skipped, statuses never set |
| +9 pts | 58% | 39% | Design handoffs committed (3 zips), 10 threads written, sprint running | Yes |
| +14 pts | 72% | 41% | Frontend merge into monorepo, environment verification, duplication found | Yes — merge verified building |
| +6 pts | 78% | 41% | **5 concurrent subagents** dispatched: researcher, data-ops, strategist, backend, frontend | In flight |

### What this actually tells us

**Execution is roughly an order of magnitude cheaper than planning.** The entire sprint-1 bootstrap
cost 2 points. Four Cowork planning subagents cost ~220k tokens and were the single largest line item
of the day. Correction adopted mid-session: the PM writes specs and threads; Claude Code produces
artifacts.

**Five concurrent subagents cost ~6 points.** Roughly 1.2 points per agent-task at mixed tiers. That
is cheap enough that parallelism is not the thing to ration.

**Weekly barely moved** — 38% to 41% across an entire day of heavy work. The 5-hour window is the real
constraint; the weekly ceiling is not close.

**`Weekly · Fable` is metered separately and sat at 0% all day.** A Fable session does not compete with
sprint work for budget. Earlier advice to ration Fable questions was wrong and was reversed.

**Unused 5-hour budget does not roll over.** With a reset before the next planned Fable session, running
the window to its cap is free. The per-thread closeout rule is what makes hitting the cap safe — a hard
stop then loses at most one thread rather than a batch.

### Open calibration questions
- Cost of a Fable session at the heaviest tier — the denominator on that meter is unknown.
- Whether `strategist` at Opus/high is justified versus Sonnet/high for the same ADR quality
  (Fable candidate 6).
- Per-question cost of the Haiku assistant once thread 032 lands.
