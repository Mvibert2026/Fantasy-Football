# Corrections export — 26 July 2026

Previous export shipped only `design_system/`. This one contains all five amended files.

## The three that were missing

| File in this export | Repo path | What changed |
|---|---|---|
| `mock-lab/MOCK-LAB-SPEC.md` | Mock Lab spec | **§5a Configuration and staleness** — the build-fidelity spec: three config states, the grouping-key consequence, per-column staleness split, mixed-aggregate and all-stale treatments, backend additions. Two new reference states in the states table. |
| `mock-lab/spec/mocklab-screen.json` | Mock Lab machine-readable | `screen.configuration` block, `GET /api/validation?config_hash`, **checks ML-17…ML-22**, MFD2 marked resolved (per-configuration), MBQ1/MBQ5 marked answered. 22 checks total. |
| `draft/screens/01-draft-board.md` | Draft board spec | **§Pick entry (RETROFIT-5)** — TypeAhead back-port: key map, autofocus requirement, order randomisation, `entry_mode`. |

## Also included (unchanged since you committed them, for path completeness)
The other Draft screen specs, the Settings spec and both Settings JSON files, so the four folders in
this export mirror the repo layout rather than arriving as loose files.

## Where the staleness spec actually is
`mock-lab/MOCK-LAB-SPEC.md` → **§5a**, between §5 (progress toward 30) and §6 (states). Engineers
building staleness need §5a and checks ML-17…22; nothing in `design_system/` is sufficient on its own —
AUDIT.md states the finding, §5a states the build.

## Where the TypeAhead back-port actually is
`draft/screens/01-draft-board.md` → the amended **Pick entry** section at the top, plus RETROFIT-5 in
`design-system/AUDIT.md` for the done-when condition.

## Nothing here is a summary
Every change is in the spec it belongs to. `design-system/DESIGN-SYSTEM.md` → **Amendments** lists all
five with their paths; it is an index, not a second source of truth.
