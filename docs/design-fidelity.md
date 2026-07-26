# Design fidelity — how we keep the shipped app matching the design

Design (Claude Design) cannot read this repo and has no filesystem access. That is a property of
the tool, not a process failure, and no amount of workflow design removes it. So fidelity is
maintained by three mechanisms with different coverage, and it is worth being precise about which
one catches what — because the assumption that one of them covers everything is how the last gap
went unnoticed.

## The three mechanisms

| Mechanism | Covers | Does not cover | Who runs it |
|---|---|---|---|
| **`/design-sync`** | Design system — tokens, colours, type scale, individual components | Screens, layout, client state, data wiring | Frontend, from Claude Code (needs `/design-login`, interactive terminal) |
| **Fidelity harness** (`tools/fidelity.py`) | Screen layout, and critically **whether a screen exists at all** | Semantic correctness, interaction behaviour, whether a number is right | Frontend, every session; gates on failure |
| **Founder screenshot review** | Judgment — "does this feel like the product" | Nothing systematically; it is a sampling method | Founder, decreasing over time as the harness matures |

The intended trajectory is that the harness absorbs most of the third row. It will not absorb all of
it, and it should not: taste is not automatable. But "does the Opponents tab exist" is, and that is
what actually went wrong.

## Why pixel diffing, given the numbers change

The instinct is that a data-dense app is a bad candidate for pixel comparison, and for *subtle*
drift that is true. But the failure this project actually suffered was not subtle — an entire screen
was missing. A missing screen produces the maximum possible diff. Pixel comparison is unusually well
suited to catching absence, and absence is the failure mode with the track record here.

Mask the numeric cells and compare layout. Numeric correctness is the test suite's job and it does
that job well. Let each tool do the thing it is good at.

## Threshold discipline

A harness that shows red every run gets ignored within a week, and an ignored harness is worse than
no harness because it creates false assurance. Two rules:

- Per-screen thresholds, tuned once against a known-good run.
- A `MISSING` verdict (route 404s, renders empty, or diff exceeds a gross ceiling) is **not**
  subject to threshold tuning. It always fails. That is the one signal that must never be tunable
  into silence.

## Pin the reference

Reference HTML lives in `docs/design-reference/`, committed. Do not fetch it live from Claude Design
at check time. The check must work offline, and — more importantly — it must diff against a *pinned*
design. Diffing against a moving reference tells you nothing, because you can never distinguish
"the app drifted" from "the design changed."

When Design ships an update, the reference files are replaced in a deliberate commit, and that commit
is the record of the design changing. Drift then means exactly one thing.

## What Design still has to be told manually

Design has no read access here, so these do not propagate on their own:

- Backend field renames. Under Principle #1 a rename is a product change, not a refactor.
- Which values are honestly null in `nulls.json`. Design will keep drawing populated states
  otherwise, and null-state design is a real part of this product's identity.
- Which screens are currently unbuilt, so specs get written against reality rather than against the
  full imagined app.

This carrying is a PM job, done from `docs/handoffs/` threads marked `TO: design VIA: pm`.
