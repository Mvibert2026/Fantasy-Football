# Draft Assistant — design system
**Version:** 2.0.0 · **Consolidated:** 26 July 2026 · **Covers:** 17 states across three handoffs

This is the index. It supersedes the token and component sections of all three prior handoffs; those
files stay in place as history, but nothing should be read from them.

## Files

| File | What it is | Machine-readable |
|---|---|---|
| `tokens.json` | **Canonical token set.** Every token defined once, both themes, with aliases and naming fixes recorded. | yes — diff against this |
| `components.json` | **Component inventory.** Twelve components, their variants, states, and the screens they appear on. | yes |
| `AUDIT.md` | **Consistency audit.** Every inconsistency across the three handoffs with a recommended resolution and a cost. | no — read it |
| `components/*.dc.html` | **Eight reference files** covering all twelve components, each opening in isolation with every variant visible. | structure is the point |

## What changed in consolidation

**Tokens.** No name collisions between the three source files. Two aliases recorded (dark
`--line`/`--s3`, light `--panel`/`--s3` — same value, both names kept because they will diverge).
Two naming mismatches fixed where a JSON key did not match the CSS property it defined. One
**external** collision flagged: the palette in the standing-context block of every design brief is the
pre-26-July set and is stale — this file wins, and the brief should point here rather than restating hex.

**Components.** Twelve named. The finds that mattered:

- **ValuePair was built twice** — `baseline → live` and `in force → edited` are one component with one
  rule. Highest-value merge in the audit.
- **TypeAhead was built twice**, and Draft has the worse one. Mock Lab's digit shortcuts and
  Backspace-undo should be back-ported to the screen that runs under a pick clock.
- **Five chip treatments where three were intended.** Radius now encodes behaviour: rounded =
  interactive filter, pill = display-only and non-sortable, square = structural label or verdict.
- **Five progress treatments.** Four are genuinely different claims and stay; two were the same claim
  at two heights.
- **Six disclosure patterns**, all legitimate, none previously named. Naming them was the deliverable.
- **The 10-dot array has two fill rules and they should both survive** — I checked. An availability
  figure is actionable so colour carries urgency; a calibration figure is the number under inspection,
  so colouring it would tell the reader what to think about the thing they are checking. Recorded as
  variants, not flattened. Its five *sizes* were drift and are now three.

## The audit finding that changes a shipped screen

**`STALE-01` — Mock Lab needs staleness and does not have it.** Calibration buckets are derived
numbers. A mock logged under 0.5 PPR was scored against availability computed for 0.5 PPR; change the
league and those buckets describe a league that no longer exists. Today Mock Lab has no stale treatment
at all, so after a scoring change the calibration dots keep rendering at full contrast — exactly the
failure Settings was built to prevent, on the screen whose entire purpose is honesty about what we know.

Fix is small: store `league_settings_hash` per mock, compare it, reuse the existing stale treatment
and the `StatusBanner` stale variant. **Do this before the fourth screen.** Everything else in the
audit can wait for its screen's next natural touch; this one is a claim the build cannot currently
support.

Four smaller retrofits are listed at the end of `AUDIT.md` with costs — all one-expression or
one-style-string changes except the partial-mock affordance, which needs a small design pass.

## Amendments — 26 Jul 2026

All changes were made in place. There is no companion note; if a spec changed, the spec changed.

- `handoff_mock_lab/MOCK-LAB-SPEC.md` §5a — configuration and staleness at build fidelity, plus two new
  reference states in the states table (`08-stale-config`, `09-all-stale`).
- `handoff_mock_lab/spec/mocklab-screen.json` — configuration block, one new endpoint, checks ML-17…22,
  and MFD2 marked resolved (per-configuration).
- `design_system/AUDIT.md` — retrofit specifications section: RETROFIT-1…5 turned into buildable specs.
- `design_handoff_draft_assistant/screens/01-draft-board.md` — pick entry amended to the Mock Lab
  TypeAhead, with the key map, autofocus requirement, order randomisation and `entry_mode`.
- `design_system/components.json` — TypeAhead find marked resolved.

## Reading order for an implementer

1. `tokens.json` — the vocabulary.
2. `components/value-state.dc.html` — the null vocabulary. If this drifts, nothing else matters.
3. `components/value-pair.dc.html` — the two-number rule.
4. The remaining six reference files, in any order.
5. `AUDIT.md` only if you are touching a screen it names.

## Not yet components

Nav rail item, mode switch, sticky action bar, assistant dock, mini board grid, CI whisker. Each
appears on exactly one surface with no variants. **Promote the second a second screen needs one** —
that is the drift this inventory exists to catch, and it is how ValuePair got built twice.

---

## Build order — recommendation (26 Jul 2026)

Frontend starts from behind: seventeen specified states, zero built. This ordering minimises rework by
building **component-dense screens first**, so the shared parts are written once and every later screen
is assembly rather than invention.

### The dependency that decides the order
Eight components carry the whole surface. Their coverage is lopsided:

| Component | States that need it |
|---|---|
| `ValueCell` (fresh/stale/null) | 17 of 17 |
| `DataRow` | 15 |
| `Disclosure` | 15 |
| `Chip` | 14 |
| `ValuePair` | 8 |
| `FrequencyDots` | 7 |
| `Progress` | 6 |
| `StatusBanner` | 6 |

### Recommended order

**0 · The primitives, alone (no screen).** `ValueCell`, `DataRow`, `Chip`, `Disclosure`. Build against
the four component reference files, not against a screen. Every one of the seventeen states needs the
first of these, and it encodes the null vocabulary — the one thing that cannot be retrofitted cheaply,
because it is a claim about meaning rather than a style.

**1 · Prep board.** The densest table in the product and the least stateful. It exercises `DataRow` at
full complexity (tier grouping, sticky header, CI whiskers, the inline expander) with no live state, no
job, no staleness. If the primitives are wrong, this is where it shows up cheaply.

**2 · Settings editor.** Six states, and it introduces `StatusBanner`, `Progress`, `ValuePair` and `Stepper`
— four components that nothing else can be honest without. It also forces the recompute state machine,
which is the hardest logic in the product and the thing every other screen inherits assumptions from.
Building it second means every later screen already knows what pending, stale and failed look like.

**3 · Mock Lab.** Seven states, reuses everything from steps 0–2, and adds only `FrequencyDots` and
`TypeAhead`. **It must ship with the configuration stamp in the first commit** — see AUDIT STALE-01;
every mock logged before the field exists is permanently unstampable, so this cannot be a follow-up.

**4 · Draft room.** Last, deliberately, and this is the counter-intuitive part of the recommendation.
It is the highest-traffic surface and the most tempting to build first, but it is also the only one with
a real-time clock, three panes, a side sheet and a live-adjusting model — and it reuses `ValuePair`,
positional dots, `TypeAhead` and the whole null vocabulary from the three screens before it. Built
first it would invent all of them under time pressure; built last it is mostly composition.

**5 · Player side sheet.** Naturally after the Draft room, since it opens from it — but specify it as a
separate build step because its generated verdict line depends on availability, VBD and tier data all
being correct, which is only true once steps 1–4 are done.

### Why not build the Draft room first
The instinct is to build the flagship, and it is wrong here for a measurable reason: the Draft room
needs six of the eight shared components, and five of those six are *simpler* elsewhere. Building it
first means writing `ValuePair` against a live band-coloured probability instead of against a static
old-to-new diff, and writing `TypeAhead` under a pick clock instead of in a logging flow. Same
components, harder first drafts, and the harder draft is what everything else inherits.

### What can be parallelised
After step 0, the Prep board and the Settings editor share almost nothing beyond the primitives, so two
people can take one each. Mock Lab and the Draft room cannot start until Settings lands, because both
depend on its staleness semantics.

### One sequencing constraint that is not negotiable
The Mock Lab configuration stamp ships with the first Mock Lab commit, not a later one. It is the only
item in this plan where deferring changes the outcome rather than the schedule.
