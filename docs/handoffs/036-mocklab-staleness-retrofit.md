---
ID: 036
FROM: pm
TO: backend, frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: Mock Lab build
---

## Ask

Mock Lab needs a configuration stamp and a three-state staleness model before it is built. Design's
`STALE-01` finding, expanded after a second pass.

## Three states, not two

The obvious model is current/stale. It is wrong, and the third state only became visible once the
retrofit impossibility was pointed out:

- **current** — the mock's configuration hash matches the league's present configuration.
- **stale** — hashes differ. Excluded from calibration by default, includable by explicit user action.
- **unknown** — hash is null, because the mock predates the field. **Excluded, and *not* includable.**
  There is no basis on which a user could make that call, so offering the toggle would be false
  precision dressed as control.

That third state exists because the data forces it, not because anyone wanted it. It is also why this
must land before collection scales: every mock logged before the field exists is permanently `unknown`.
At one logged mock the cost is zero. At fifteen it is unrecoverable.

## Not everything in a stale mock is stale

Design's distinction, and it must survive implementation. **The picks are facts.** What a manager
actually selected does not change when scoring changes. The *derived* fields go stale — `WE SAID`,
`OUR TOP CALL`, `VERDICT`, `SURPRISE`.

Marking whole rows stale would imply we are no longer sure what the manager picked, which is both
false and corrosive to the one thing this screen exists to establish. Stale treatment applies at field
level, not row level.

## If calibration is per configuration — and it currently is

D-015's default makes the stamp the **grouping key for the whole analysis**, not a flag:

- The aggregate becomes pooled *within* a configuration, with a configuration selector.
- The 30-square progress array and the evidence ladder both count **within the selection**, not
  globally. Thirty mocks across four configurations is not thirty mocks.
- **The Brier score is suppressed entirely when configurations are mixed.** Design's framing is exact:
  a score spanning two scoring systems is not a worse number, it is not a number. Suppress it rather
  than caveat it.
- The realistic post-change state — every mock stale — renders as an **honest empty form** stating that
  calibration starts from zero. Not an error, not a zero. It is a true statement about what we know.

## Backend

Stamp each logged mock with the league configuration in force at logging time — scoring rules and
roster shape, hashed. Not the league id, which survives an edit that invalidates the mock. Export it.
A mock must not be writable without a stamp; enforce at the storage layer so `unknown` can only ever
mean "predates the field" and never "we forgot".

## Frontend

Compare stamped hash against current. Apply the existing Settings stale treatment at field level.
Exclude stale and unknown from aggregate calibration by default; allow including stale only, never
unknown. Suppress Brier on mixed selections.

## Also — the TypeAhead back-port

Design amended `01-draft-board.md` to use Mock Lab's TypeAhead: key map, autofocus, order
randomisation, and `entry_mode`. The Draft board runs under a pick clock and currently has the worse
of the two implementations. **Note:** that amended file has not yet reached this repo — see the
missing-amendments note below.

## Missing amendments — do not build from an incomplete set

Design's index lists five amended files. Three have not arrived:
`handoff_mock_lab/MOCK-LAB-SPEC.md` §5a · `handoff_mock_lab/spec/mocklab-screen.json` (checks ML-17–22,
new endpoint) · `design_handoff_draft_assistant/screens/01-draft-board.md`.

The reasoning above is captured here so the design intent is not lost, but **the build-fidelity spec is
those three files.** Do not implement from this summary alone.

## Done looks like

Configuration hash stamped and exported, unwritable without it. Three states implemented with `unknown`
non-includable. Field-level not row-level staleness. Per-configuration aggregate with Brier suppressed
on mixed selections. Test asserting a mock cannot be written without a stamp. Commit hash and test count.
