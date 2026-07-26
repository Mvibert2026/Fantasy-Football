---
ID: 034
FROM: pm
TO: strategist
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: Mock Lab build (025, and the UI)
---

## Ask

Design has raised a measurement-validity problem and explicitly declined to recommend on it. Rule on
it, and specify the instrumentation. This is a study-design question, which is why it is yours and
not the founder's.

**The problem.** The Mock Lab's central design rule is that *the model's own prediction is the fastest
input device*: its top five candidates render as a numbered list, so logging a pick is usually one
keystroke. That is what makes 4,800 entries (30 mocks × 160 picks) tractable at all.

But it means **we are presenting our own guess as the cheapest thing to record.** A user who is tired,
fast, or half-attending may press a number that is close rather than correct — and the resulting bias
is self-serving, since it inflates apparent calibration. We would be validating the model against data
the model helped produce.

Design's counter-observation, which is also true: the effect compounds favourably. Better calibration
means the top five covers more picks, so the thing being validated makes validation cheaper. The
mechanism is genuinely good; the question is whether it is contaminating.

## What I want you to specify, not just judge

Every naive fix trades away the speed the screen depends on, so the interesting answers are the ones
that keep it. Three candidates — assess each, add any I have missed, and pick:

**(a) Randomise the order of the five.** The keystroke stays a single key, but position no longer
encodes our confidence, which breaks the "press 1 for our top pick" reflex. Nearly free. Does it
address the bias or only its most obvious form?

**(b) Instrument rather than prevent.** Log an `entry_mode` per pick — shortcut, typed, or pasted.
Then test directly whether shortcut-entered picks show systematically better calibration than typed
ones. If they do, that is measured evidence of the bias and it can be corrected for or those picks
discarded. If they do not, the concern is answered with data rather than argument.

**(c) A blind control arm.** Log some fraction of mocks with predictions hidden entirely. Slower, and
the founder is the only logger, so specify how many are needed to detect a difference worth caring
about — and say plainly if that number exceeds what is realistically collectable.

## Why this needs deciding before the build, not after

`entry_mode` and any randomisation have to exist from the first logged pick. Retrofitting them means
the early mocks are uninstrumented and cannot be compared with later ones — and given the target is
~30, discarding the first several is expensive.

There is also a pre-registration angle: if (b) is adopted, the shortcut-versus-typed comparison is a
test with a decision rule, and under the convention in ADR-C it should be registered before the data
exists. Which is now.

## Constraint on your answer

You have no database access and should not try to measure anything. Specify the design, the
instrumentation, and the pre-committed decision rule. Backend implements; the founder decides only if
you conclude it is genuinely a taste question rather than a methods one.

## Done looks like

An ADR draft covering: which option, why, the exact fields to log, the pre-registered comparison with
its decision rule, and an honest statement of what remains uncontrolled. Reply here and set RESOLVED.
