---
ID: 040
FROM: pm
TO: backend, frontend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: Mock Lab build, Settings build
---

## Ask

Three founder requirements from 2026-07-27. Related but distinct — do not conflate them.

### 1. Multiple real leagues, not one pre-coded one

The founder plays in several leagues. The app currently ships a switcher over **pre-generated
configurations** — the 24-config matrix plus the founder's own league — which is not the same as being
able to define a league.

The missing capability is league *creation*: name it, set team count, roster shape, scoring rules,
draft slot, and have replacement levels and the board recomputed for it. That is the Settings editor
(`docs/design-handoff/settings/`), already specified in six states and entirely unbuilt.

**Consequence worth stating:** replacement levels are measured *per format*. RB30/WR40/TE10/QB10 is
this league's answer, not a universal one. A second league with different scoring needs its own
measurement, not the first league's numbers reused. Confirm the pipeline does this per league rather
than assuming.

### 2. The user does not control their draft slot in a mock

In a public mock lobby the slot is assigned. The 2026 league config hardcodes slot 3 and the pick
sequence 3, 18, 23, 38, 43, 58, 63 that follows from it.

Mock Lab must accept **any slot**, with the pick sequence derived rather than fixed, and must not
assume the logged mock shares the founder's league slot. This also affects availability: "who survives
to *your* next pick" is a different question from slot 8 than from slot 3, and it is the whole point
of the calculation.

### 3. Undo — and the problem it creates

Requirement: select a pick, go back, undo entries. A misclick during a fast mock must be recoverable.
Design already specced Backspace-undo in the Mock Lab TypeAhead; this asks for it as a general
capability, including several picks back.

**The architectural conflict, which needs deciding before either side builds.**

Thread 025 requires predictions to be **written at entry and immutable** — never recomputed on read —
because a calibration curve built from hindsight-recomputed predictions is guaranteed to look good and
mean nothing.

But an undo invalidates *downstream* predictions. If pick 14 is wrong and gets undone, the predictions
generated for picks 15, 16, 17 were computed against a board state containing a player who was never
actually taken. They are not merely stale; they answer a question about a draft that did not happen.

Three options:

- **(a) Recompute downstream predictions on undo.** Breaks immutability. Rejected — this is the exact
  hindsight contamination the immutability rule exists to prevent.
- **(b) Void them.** Predictions stay immutable and on disk, marked `voided_by_undo`, excluded from
  calibration. Preserves the audit trail; costs some data from every undo.
- **(c) Truncate the mock at the undo point.** Simple, and throws away the most work.

**Recommended default: (b).** It is the only option that keeps both immutability and a recoverable
mistake, and it makes the cost of an undo visible rather than hidden.

Two things follow from (b) and should ship with it:
- Record an **undo count per mock**. A mock with fifteen undos is lower-quality data than one with
  none, and calibration should be able to see that. This is the same instrumentation logic as
  `entry_mode` in ADR-D.
- Undo must be **explicit and bounded** — a visible action with a visible consequence ("this voids 3
  predictions"), not a silent rewind. Under Principle #2 the user should see what their correction
  costs.

## Done looks like

Founder confirms or overrides option (b) — logged as a decision. Then: Settings enables real league
creation with per-format replacement levels; Mock Lab accepts any draft slot with a derived pick
sequence; undo voids rather than recomputes, with a per-mock undo count and a visible cost.

---

## AMENDMENT — 2026-07-27. Founder overruled the undo design, correctly.

**Disregard options (a), (b) and (c) above.** The reasoning behind them was wrong and the founder
caught it.

### What I got wrong

I claimed recomputing downstream predictions after an undo constitutes hindsight contamination. It
does not.

An availability prediction is a **pure function of board state at pick N** — the pre-draft marginal
survival curve, share-based roster-need arithmetic, and a trailing 10-pick window for run detection.
None of those inputs reference anything after pick N. So if the draft is genuinely reset to the state
before the erroneous pick and replayed, the recomputed predictions are **identical** to what would
have been produced live. Same inputs, same deterministic function, same output.

I conflated two different things. The real contamination risk is recomputing old predictions with a
**newer model version** — improve the model, re-run last week's mock, and calibration improves for
free without the model getting better at anything. That risk is real and must be guarded. It has
nothing to do with undo.

**Corrected rule: never recompute with a different model version.** Not "never recompute."

### The design: event sourcing

- **The pick sequence is the source of truth.** Predictions are derived state, not stored facts.
- **Undo truncates the log and replays.** No voided records, no lost data, no undo count, no
  user-visible "this costs you 3 predictions" warning. Undo becomes ordinary.
- **Each mock pins `model_version` and the RNG seed** at creation.
- **Replay is permitted only while the current model version matches the pinned one.** If the model
  has changed since the mock was logged, that mock's predictions are frozen — replay is refused and
  the mock is marked, because a replay under a new model would be exactly the contamination the
  immutability rule was protecting against.

That last clause is the entire safeguard, and it is one comparison.

### Consequences

- Simpler than voiding, better to use, and loses nothing.
- ADR-D's `entry_mode` instrumentation is unaffected and still needed — it addresses shortcut bias,
  a separate concern.
- Thread 025's "immutable prediction storage" requirement is **superseded** for the undo case.
  Predictions become reproducible-on-demand rather than write-once. The property being protected was
  never immutability for its own sake; it was *reproducibility under the model that made the claim*.
  Event sourcing plus a version pin delivers that more directly.
- Backend: update thread 025 before implementing. The storage design changes.

### Note for the record

This was a founder correction to a PM design, and the PM's version was more complex, lost data, and
protected against a risk that did not exist in the case it was applied to. Worth logging as evidence
that "the rigorous option" and "the conservative-sounding option" are not always the same thing.
