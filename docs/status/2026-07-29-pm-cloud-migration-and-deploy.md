# 2026-07-29 — PM: zero approvals, the move off the founder's machine, and the app online

**Role:** pm (in-repo, taking over from the outside-the-repo PM)
**Branch:** `claude/pm-agent-setup-gobxa0` → merged to `main` @ `a3dab01`

## What the founder asked for, in order

Get to zero approvals · finish the move off his machine · challenge every premise in the handover ·
then, mid-session: see the app on a website.

## What landed

**Zero approvals.** Deleted the `PreToolUse` hook, all 25 `permissions.ask` rules, 86 of 94
`permissions.allow` entries, and the seven Windows scripts that installed them. **The hook had been
inert here all along** — registered with a Windows conda path that does not exist in Linux — so zero
approvals was true by accident, which is worse than either extreme. Replaced with the measured bigger
lever: FR-018 counted agents *choosing* to stop and ask at 42% of interruptions across 57 sessions
against 24% for hook and permission stops combined. Decide-and-log is now a hard rule in all seven
agent definitions.

**The move off his machine, finished.** One-command rebuild (`scripts/rebuild_database.py`, 64s),
the ADP snapshot CSV→DB loader that had never existed, `pandas`/`numpy` added to `requirements.txt`
(15 `src/` modules imported pandas; without it pytest collection aborted and *zero* tests ran),
`.python-version`, and `tools/state.py` unhardcoded from the founder's conda path.

**The app is online.** `https://fantasy-football.soft-water-e755.workers.dev` — Cloudflare Worker,
static Vite build from `main`, rebuilds on every push. Founder confirmed it in his own browser.
Independently verified `/data/board.json` serves `contract_version 1.14.0`.

**A single HTML file that runs a full draft** — no server, no network, no install. Originally
excluded Draft mode on the assumption it needed a backend; challenged that, and it was wrong.

**ADP, captured daily and never once displayed, now on the board** at contract 1.14.0 — 144 of 510
rows, 366 honest nulls, labelled a proxy.

**The format was wrong, and the founder caught it.** MFL's `IS_PPR` flag is binary, so four days
were captured at full PPR for a half-PPR league. FFC publishes half-PPR at 10 teams — exact match,
27× the sample — and he had already lifted the block on it. All three formats now capture daily.

## Corrections to things the repo asserted

- **The daily capture had never run on schedule.** One run existed, `event: workflow_dispatch`,
  triggered by hand. `CURRENT-STATE` said the Windows task was redundant. It was not.
- **The 2021–2025 rankings history is not permanently lost** — it re-pulls, verified row-by-row by
  another session.
- **`docs/pm/HANDOFF.md` was not in the repo.** Now committed.

## What the PM got wrong, recorded because it is the point of this file

- **Manufactured a phantom collision twice** by committing running agents' in-flight files to satisfy
  a clean-tree hook. The second cost a chain a full decision cycle. Ruleset now in `PLAYBOOK.md` and
  all seven agent definitions.
- **Over-read "optimize all for phone viewing right now"** as build responsive layouts. ~a third of
  the largest agent run on record (374k tokens) went on work the founder then cancelled. *"Right
  now" is urgency, not scope.*
- **Dispatched three Fable mandates mid-week.** Fable runs on a separate weekly budget spent at the
  end of the week. All three killed. Now recorded in `ROLE.md`.
- **Declared worktrees obsolete in the cloud.** Half right — the concurrency reason moved from
  session level to agent level rather than vanishing, and removing it caused the collision above
  within hours.

## Cost

~1.09M tokens across reporting agent chains. Logged per-dispatch in `docs/operating-model.md`.

## What a next session should pick up first

1. **Verify tomorrow's 09:15 UTC run fires on schedule.** Check `event: schedule`, not the commit
   author — that is how this was got wrong once. Until then the Windows task stays.
2. **The hardcoded league config** — correctness-floor item 1, now also the enabler for FR-027's
   generic tier. Must land before any mock is recorded.
3. **The Fable queue, at the end of the week** — and write `.claude/agents/fable.md` first; it is the
   one role with no definition.
4. **ID allocation is broken structurally**, not by indiscipline — three collisions today, all from
   tool-allocated IDs on parallel branches. See thread 081.
