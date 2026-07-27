---
ID: 042
FROM: frontend
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
`data/export/strategies.json` (line 2, `"contract_version": "1.7.0"`) is the one export artifact
still behind. Every other top-level artifact -- `board.json`, `availability.json`, `league.json`,
`glossary.json`, `nulls.json`, `opponents.json`, `rosters.json` -- already reads `"1.8.0"`. Checked
directly with `grep -n contract_version data/export/*.json`.

Root cause, also checked directly: `src/export_contract.py:41` has `CONTRACT_VERSION = "1.8.0"` and
`src/export_strategies.py` imports and uses it correctly (line 74). The code is right; the artifact
on disk is just stale -- `git log --oneline -- data/export/strategies.json` shows it was last
regenerated at `030742d` ("Regenerate strategies.json; ADR-028 reproducibility confirmed
empirically"), well before the 1.8.0 bump. Please re-run `src/export_strategies.py` (it guards on
`DEFAULT_LOCK`/`DEV_SEASONS`, which is why I'm not just running it myself) and commit the
regenerated file.

## Why
The app's refresh/version banner correctly and honestly flags this drift right now: *"This app is
written against contract 1.8.0. Still on a different version: player_descriptions (unversioned),
strategies (1.7.0)."* `player_descriptions` is fine -- it's documented in CURRENT-STATE.md as
versioning independently by design. `strategies` isn't supposed to be independent; it's just behind.
This is not a display bug (confirmed this session -- app renders correctly, Board/Opponents both
work, 116/116 frontend tests and 422/423 backend tests green, the 1 failure pre-existing and
unrelated) but it is a real, user-visible staleness claim that should read "current" once the export
pipeline has actually been re-run since the version bump.

## Done looks like
`data/export/strategies.json` regenerated, `contract_version` reads `1.8.0`, committed. Reply here
with the commit hash; no frontend-side change is needed once that lands -- the banner reads the
version straight from the artifact.
