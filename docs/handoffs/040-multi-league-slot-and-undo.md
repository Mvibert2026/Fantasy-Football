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

## Reply — backend, 2026-07-27 (undo/slot portion only)

Built the undo/event-sourcing design exactly as the AMENDMENT specifies, in `src/mock_lab_store.py`
(thread 025, ADR-046 in `docs/decisions.md`): pick log is the sole source of truth, undo truncates
and replays, no voided records, no undo count. The one guard is `mocklab_drafts.model_version`
pinned at creation vs. the module's current `MODEL_VERSION` -- `replay_predictions` refuses the
moment they diverge. Full detail in ADR-046 and the reply on thread 025.

**Item 2 (any slot)**: `create_mock(..., slot, teams)` accepts any slot 1..teams, validated against
the caller-supplied `teams` (from that league's own config) rather than assuming the founder's
slot 3. Deriving a full snake pick sequence from an arbitrary slot and wiring the real hazard model
to it needs a general-purpose prep-mode P0 source that doesn't exist for non-primary configs yet --
flagged as a gap in ADR-046, not solved here. This thread's slot item is otherwise addressed for the
storage layer; a caller (Mock Lab UI / whatever builds the pick-sequence generator) still needs that
P0 source before live availability numbers are meaningful for a non-primary slot.

**Item 1 (real league creation / Settings editor) is NOT this reply's scope** -- untouched, still
open, still blocks Mock Lab UI and Settings build per this thread's own text.

Backend's piece of this thread (undo architecture + slot acceptance in storage) is done. Leaving
STATUS as-is since item 1 remains open and this thread is addressed to both backend and frontend --
not setting RESOLVED unilaterally on a thread with unresolved scope outside my piece.

### backend · 2026-07-27

Item 1 (real league creation) built: `src/league_builder.py` -- `create_league(name, teams,
starters, flex_slots, flex_eligible, bench, ir, user_draft_slot, ...)` builds and saves a
`LeagueConfig` from plain, founder-facing parameters; `export_league(cfg, out_dir, conn)`
recomputes board/league/availability/rosters for it via the existing
`export_contract.write_all`; `create_and_export_league(...)` chains both. `unique_league_id()`
handles name-to-id slugging and collisions, refusing the reserved `primary` id.

Checked the consequence this thread flagged -- per-format replacement levels -- directly rather
than assuming. It was already correct: `scoring.ReplacementLevels.from_league_config()` and
`export_contract.build_board_json(conn, cfg)` (ADR-041/047) already derive replacement levels
from whichever `LeagueConfig` is passed, not from a shared default. `league_builder.py` doesn't
touch that arithmetic -- it only makes a config reachable from plain inputs instead of a
hand-built `LeagueConfig()` call. Confirmed with a DB-backed test: a 14-team, 1.0-PPR,
2RB/2WR/1TE-starter probe league created and exported through this new path gets
`board.json["replacement_levels_used"] == {"QB":14, ...}`, not the founder league's
`{"QB":10,"RB":30,"WR":40,"TE":10}`.

`flex_split` is deliberately never set by `create_league` -- a new league's split is
unmeasured, so `from_league_config` takes its existing flagged-placeholder path
(`measured=False`) rather than this module silently presenting a borrowed number as the new
league's own.

Scope boundary, stated plainly: this is the backend capability only. No API layer, no job
queue/polling, no tier-1/tier-2 distinction, no shadow-recompute-then-apply state machine --
that is `docs/design-handoff/settings/SETTINGS-EDITOR-SPEC.md` SS7's contract for the Settings
editor UI itself, unbuilt, not this round's scope. `export_league()` is synchronous/blocking
(~7-10s per ADR-047's existing timing), the same shape `write_all` already has for the 24
pre-generated configs -- a future API layer wraps this in a job rather than replacing it.

Full detail: ADR-049 in `docs/decisions.md`. Tests: `tests/test_league_builder.py`, 19 passed
(one DB-backed integration test, rest pure). `tests/test_league_config.py` +
`tests/test_multi_league_export.py` re-run targeted, 26 passed, no regression.

Item 1 is now done for backend's scope (the capability behind the Settings editor). Not setting
STATUS: RESOLVED unilaterally -- this thread is `TO: backend, frontend` and item 1 also names
the Settings editor UI itself, which is frontend scope and untouched this round. Frontend or PM
should close it once the UI side is addressed or explicitly deferred.
