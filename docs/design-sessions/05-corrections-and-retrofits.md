The consolidation is received and committed — `DESIGN-SYSTEM.md`, `tokens.json`,
`components.json`, `AUDIT.md`, and eight component files now live at `docs/design-system/`.

═══════════════════════════════════════════════════════════════════════════════
PART 1 — RESPONSE
═══════════════════════════════════════════════════════════════════════════════

**The staleness finding is being treated as a defect, not a note.** It is now a build-blocking thread
against both engineers, and the reasoning you gave carried it: calibration buckets are derived, so a
mock logged under 0.5 PPR describes a league that stops existing after a scoring change, while its
dots keep rendering at full contrast. That is the failure Settings exists to prevent, on the screen
whose whole purpose is honesty about what we know.

One thing you could not have known, which makes it more urgent than your "before the fourth screen"
framing: **retrofitting it later is not merely expensive, it is impossible.** Every mock logged before
the field exists is unstampable, and a mock whose configuration is unknown can be neither honestly
included nor honestly excluded. At one logged mock the fix costs nothing. At fifteen the data is
permanently ambiguous.

It also turns out to be load-bearing beyond staleness. There is an open question about whether the
30-mock target is per league configuration or global. If per configuration — which is the current
default — then your stamp is not a staleness flag at all, it is the **grouping key for the entire
calibration analysis**.

**Your dot-array reasoning is accepted, and I want to be explicit about why**, because it is the kind
of call that usually gets overruled by a consistency audit. An availability figure is actionable, so
colour carries urgency; a calibration figure is the number under inspection, so colouring it would
tell the reader what to think about the thing they are checking. That is a real distinction and
holding it as two variants rather than collapsing them is correct. Five sizes down to three is the
right call in the same breath — one was drift, the other was not.

**The TypeAhead finding is the best cheap win in the audit.** Built twice, with the worse
implementation on the screen that actually runs under a clock. Back-porting the digit shortcuts to
Draft costs almost nothing and improves the highest-traffic surface in the product.

**On the stale palette in the standing-context block — that is my defect and you are right.** Every
brief I have sent restates the hex list inline, which is exactly the duplication your audit exists to
eliminate. Future briefs will point at `tokens.json` rather than restate it.

═══════════════════════════════════════════════════════════════════════════════
PART 2 — THIS SESSION: FINISH THE CORRECTIONS, NO NEW SCREENS
═══════════════════════════════════════════════════════════════════════════════

**Context you should have, plainly: you are far ahead of the build.** Seventeen specified states have
shipped and zero have been built. Frontend has not run a session yet. So further screens would deepen
a backlog that is already the project's largest liability, and unbuilt design drifts from reality the
longer it sits.

That is a queue problem, not a quality problem — your output has been the strongest work here. But
the right move now is to reduce the defect count in what already exists rather than add to it.

**Deliverable 1 — spec the Mock Lab staleness treatment properly.** You described the fix as one
field, one comparison, two existing components. Specify it at build fidelity: what a stale mock looks
like in the review state, in the aggregate view, and in the calibration dots specifically. What
happens to an aggregate that mixes stale and current mocks — excluded by default, with what
affordance to include? And what a user sees when *every* logged mock is stale, which is the realistic
case immediately after a scoring change.

**Deliverable 2 — the four smaller retrofits, specified.** `AUDIT.md` lists them with costs. Turn
each into something buildable rather than a description of a problem, so they can be picked up
opportunistically at each screen's next touch without re-deriving what to do.

**Deliverable 3 — the TypeAhead back-port.** Update the Draft board spec to use the Mock Lab
implementation. One component, one spec amendment.

**Deliverable 4 — a build-order recommendation.** You now have the fullest view of the design surface
of anyone on this project. Given that Frontend is starting from behind and will build incrementally,
what order minimises rework? Specifically: which screens share the most components, so building them
adjacently means the component work is done once? That ordering is genuinely yours to advise on and
nobody else can see it as clearly.

**Format:** amendments to existing files where possible rather than new documents. If a spec changes,
change the spec — do not write a companion note describing the change, which is how a second source
of truth gets created.

**After this, expect a pause** while Frontend catches up. When you return, the first work will be
whatever the frontend audit reveals as drifted — which is design work informed by reality rather than
by anticipation, and probably more useful than another screen would have been.
