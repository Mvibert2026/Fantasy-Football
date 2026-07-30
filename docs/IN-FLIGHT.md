# In flight as of 2026-07-30, PM session

Written because this session was near a token limit with agents still running. **Delete this file
once both branches below are merged or explicitly abandoned.** If it is still here and the dates
look old, treat it as stale and verify against `git branch -a` before trusting it.

## Two agents were mid-run

Both were told to WIP-commit and push before stopping, and to leave a `HANDOFF.md` at the root of
their worktree. Check for those first — they are more current than this file.

| Strand | Branch to look for | What it was doing |
|---|---|---|
| Bottom-up component model | `worktree-agent-ab3387738c3dfd2a8` | Extending the component projection model from WR to **RB, QB and TE**. Also instructed to fix the injury-data defect: `nfl.db.injuries` holds 79,816 rows and is read by no model. |
| ADP vs. production | `worktree-agent-a3f0bc3cc3efb7185` | Measuring where consensus ADP is *structurally* wrong across seasons. Deliverable: `docs/analysis/adp-vs-production-2026-07-30.md`. |

### The one thing that must not be got wrong on resumption

The ADP strand has a **holdout season that may be spent or unspent**. Its `HANDOFF.md` was asked to
state this in bold. A resumed agent that assumes the holdout is fresh, when it is not, will look at
it twice — and that silently invalidates the entire analysis (`CLAUDE.md` §6.3). **Read the handoff
before running anything against holdout data.** If the handoff is missing or ambiguous, treat the
holdout as SPENT and restart the analysis on the training seasons rather than gambling.

## Founder's standing instruction at the time

Frontend work is **paused** at his explicit request until his token budget resets — "wait on front
end till we get a token reset in an hour unless i tell you otherwise". Bottom-up model work only.

A frontend agent was dispatched and then stopped for this reason; nothing was committed from it.
The queue it was given, still unstarted, in his agreed order:

1. **FR-067** — column headers don't align with rows in Draft view. Fix is one shared column
   definition consumed by both header and rows, not a pixel nudge.
2. **FR-066 / FR-057 part 2** — availability model doesn't update when the draft slot changes; it is
   pinned to the exported slot's pick numbers. Agreed fix is browser-side recomputation through the
   existing `applyUserSlotOverride` seam in `frontend/ui/data/league.ts`, with the derived value
   visibly marked as client-derived rather than sourced.

## Also open, not started

- **FR-072** — thread hygiene. The mailbox guard `tools/handoffs.py check` is **red right now** (7
  findings: duplicate threads 093/094, conflicting ADR-054/055 headers). `tests/test_handoffs.py::
  test_mailbox_health` asserts it passes, so the suite is red on that test. Diagnosis and proposed
  fixes are in the FR; the free one is that **PM allocates thread/ADR numbers before dispatch**
  instead of letting parallel worktree agents race for them.
