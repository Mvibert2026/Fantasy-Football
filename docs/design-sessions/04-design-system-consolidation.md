Continuing from the Mock Lab handoff, which has been received and committed in full — seven states,
spec, tokens, PNGs.

═══════════════════════════════════════════════════════════════════════════════
PART 1 — WHAT HAPPENED TO WHAT YOU FLAGGED
═══════════════════════════════════════════════════════════════════════════════

**The shortcut-bias question — routed to the statistician, not the founder.** This is the one call
you made that I'd push back on. You framed it as a taste question with a fixed trade-off: fix the bias
or keep the speed. It's a study-design question, and it has a third answer you didn't consider.

Don't prevent the bias — **measure it.** Log an `entry_mode` per pick (shortcut, typed, pasted), then
test whether shortcut-entered picks show systematically better calibration than typed ones. If they
do, that's measured evidence and it can be corrected for or those picks discarded. If they don't, the
concern is closed with data rather than argument. Costs nothing in speed.

Two implications for your design. There's a nearly-free partial mitigation worth considering:
**randomise the order of the five.** Still one keystroke, but position no longer encodes our
confidence, which breaks the "press 1 for our top pick" reflex — while keeping the tempo the whole
screen depends on. And the instrumentation must be visible in the review state, because a user should
be able to see how a pick was entered when auditing their own logged mock.

The statistician is specifying this now. Assume `entry_mode` exists as a field.

**Your other three, with defaults set (founder can loosen any):**
- *30 per league or global* — per league configuration. Calibration is claimed for one config, not
  the other 23. Harsh but honest.
- *Do others' mocks count* — your recommendation stands. Personal primary, others stored separately,
  never silently merged.
- *Partial mocks* — accepted with `rounds_logged`, as you proposed. One addition: partials are **not
  missing at random** — people abandon when a draft gets lopsided, which may correlate with what's
  being predicted. Design the affordance so an abandoned mock reads as a real, countable artifact
  rather than a failure.

**Your six backend questions — the load-bearing one is already answered yes.** Immutable
`predicted_top` / `predicted_p` written at entry was already specified before your handoff arrived,
for the same reason you raised it: recomputing predictions on read produces a calibration curve
guaranteed to look good and mean nothing. `entered_at` per pick wasn't specified and is being added,
so the tempo readout survives.

**And the thing you got most right:** adding `04-paste-reconcile` unprompted. You were correct that a
fuzzy match resolving silently wrong is the worst failure available on that screen, precisely because
it corrupts the calibration data quietly. Same instinct as `04-ready-to-apply` last time — you're
reasoning about failure modes, not layouts, and it's the most valuable thing you're doing.

═══════════════════════════════════════════════════════════════════════════════
PART 2 — THIS SESSION: CONSOLIDATE BEFORE THE NEXT SCREEN
═══════════════════════════════════════════════════════════════════════════════

No new screen this round. Three handoffs are in — Draft (four screens), Settings (six states), Mock
Lab (seven states) — and the risk now is quiet divergence: two names for the same colour, two
treatments for the same idea, a component reinvented because the first one wasn't findable.

That drift is cheap to fix now and expensive after a fourth screen. It's also the precondition for
automated design-to-code sync, which needs a canonical component set to sync *against*.

**Deliverable 1 — a single canonical token set.** Reconcile `design-tokens.json`,
`settings-tokens.json`, and `mocklab-tokens.json` into one file. Every token defined once. Where the
same value appears under two names, pick one and record the alias. Where the same *name* carries two
values, that's a bug — flag it explicitly rather than silently choosing.

**Deliverable 2 — a component inventory.** Every reusable element across all seventeen states, with
its variants and states, and the screens it appears on. I expect the interesting finds to be near-
duplicates: three pill treatments that should be one, two progress indicators, several disclosure
patterns. Name them.

**Deliverable 3 — a consistency audit.** Where do the three handoffs contradict each other? Be
specific and unkind about it. Particular things to check, because they're where this product's
identity lives:
- **Null rendering.** `0`, `0%`, `—`, and "not computed" are four different claims. Is each rendered
  identically everywhere it appears? Any inconsistency here is a real defect, not a nit.
- **The 10-dot frequency array.** You reused it for calibration rather than inventing a second idiom
   — correct. Is its treatment identical in both places, or has it drifted?
- **Numeric versus label typography.** Mono for measurements, sans for codes like WR1 and LV. Any
  slippage?
- **Stale, loading, and disabled states.** Settings introduced staleness as a concept. Does anything
  in Mock Lab need it and lack it?
- **Colour carrying meaning alone.** Every colour signal needs a redundant non-colour cue. Audit all
  seventeen states, not just the recent ones.

**Deliverable 4 — one reference HTML per component**, each opening in isolation showing all its
variants. This is the format that will eventually sync into code, so structure matters more than
presentation here.

**Format:** `DESIGN-SYSTEM.md` as the index, `tokens.json` canonical, `components/<name>.dc.html` per
component, and `AUDIT.md` listing every inconsistency with a recommended resolution.

If the audit turns up something that changes a shipped screen, say so plainly. A retrofit now is
cheaper than three more screens built on a divergence.

**Next after this:** the Compare tray, then the research/comparison section — the latter is waiting on
a data-source audit, since designing a comparison view before knowing what we may legally display
would produce a mock of data we might have no right to show.
