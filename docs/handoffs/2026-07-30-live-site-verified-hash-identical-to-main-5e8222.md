---
ID: 2026-07-30-live-site-verified-hash-identical-to-main-5e8222
FROM: operator
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
Operator standing check, first run (2026-07-30). **Check 1 (deployed vs. intended code): PASS by
hash, but the intended code has moved on.**

- Built `main` (5e822252ca350c20b7e1983b5171e1a46c04b71d) fresh in a scratch worktree:
  `frontend/dist/assets/index-Dzlm53hF.js`, sha256
  `07b8fac492dcd65ed5b6b47fd0c7fb21d8ac35153368d9d4cb482fd71f519ae1`.
- Fetched the live site (`https://fantasy-football.soft-water-e755.workers.dev/assets/index-Dzlm53hF.js`,
  Basic auth): **identical filename, identical sha256.** The live site genuinely is `main`'s HEAD,
  not just a plausible-looking deploy log.
- Live `/data/board.json`: 510 players, `contract_version: 1.16.0` — matches a fresh build of
  `main` exactly (also 510 / 1.16.0).
- Working branch `claude/pm-agent-setup-gobxa0` (HEAD `cff6354`, 8 commits ahead of `main`,
  containing the four-selectable-ranking-sources work and the contract 1.17.0→1.18.0 bump) is
  **not merged to `main`** — `git merge-base --is-ancestor cff6354 main` fails. Its
  `frontend/public/data/board.json` is 527 players / contract 1.18.0.

So: the deploy pipeline itself is not the problem — it is faithfully building and serving whatever
is on `main`. The gap is that `main` hasn't received this branch's merge yet, so the live site is
17 players and one contract minor behind what a founder session would expect after today's work
(four ranking sources, `pbp`/`rosters_weekly`/`schedules` ingestion, etc.).

## Why
If the founder is told "today's work is live" without `main` being updated first, he will see the
510-player 1.16.0 board and reasonably conclude either the work didn't happen or the site is
broken — neither is true; it's an unmerged-branch problem, PM's to sequence.

## Done looks like
This branch (or its content) merged to `main`, then re-run of the operator's check-1 hash compare
confirms the live site's `index-*.js` hash and `board.json` player count/contract_version match
the merged `main` HEAD.
