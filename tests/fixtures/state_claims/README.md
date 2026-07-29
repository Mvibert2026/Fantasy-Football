# Planted-fault fixtures for `tools/state_claims.py`

`docs/pm/CHARTER.md` sets the bar for trusting a detector: *"zero interruptions **plus a
detector that has caught planted faults**."* These are the planted faults.

Each pair reproduces one of the false claims found in this project's own documents on
2026-07-29 — `.bad.md` states the false thing in roughly the words the real document used,
`.good.md` states the corrected version. `tests/test_state_claims.py` asserts the checker
fires on every `.bad.md` and stays silent on every `.good.md`. Both directions are asserted:
a detector that only ever fires is not a detector.

`f7-crossdoc-*.md` is the pair form — neither document is checkable on its own, and the
violation is that the two disagree.

`{{CONTRACT_VERSION}}` and `{{BOARD_PLAYERS}}` are substituted from the live repository at
test time, so a correct fixture cannot rot into a false one when the real value moves.
