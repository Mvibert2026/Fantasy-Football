# Briefing for design — what changed on 2026-07-29

**From:** `pm` (now owns `docs/design-protocol.md`, transferred at the founder's instruction)
**For:** `design`, whose last run was 2026-07-27. A great deal has changed since, and some of it
falsifies premises in work already produced.

**You can read this repo. You cannot write to it.** That has not changed and is not a problem to
solve — every output of yours arrives as a file for the PM or `frontend` to commit, and landing them
is now explicitly the PM's job rather than an unowned gap. `docs/handoffs/README.md` said you could
not read at all; that was stale from 2026-07-27 and is corrected.

---

## 1. The app is on the internet

`https://draft.maplerock.net` — a static build of `main`, rebuilding on every push. There is now a
real, always-current URL you can point at when specifying a screen, instead of reasoning from
committed exports.

**This creates a new context you have not designed for: the app served with no dev server behind
it.** One consequence is already visible — the "Refresh data" control calls a dev-server endpoint
that cannot exist on a static deploy, so on the live site it always fails with an explanatory
message. It is honest but wrong: a control that can never work is present-but-inert, which the
project treats as a form of the app lying about itself.

**Open question for you:** what should a control that is meaningful locally and impossible when
hosted actually do? Absent, disabled with a reason, or replaced by a statement of when the data last
rebuilt? This is a design decision, not an engineering one, and it will recur.

## 2. Screenshots work now — your acceptance harness is unblocked

The limitation behind thread 068 is gone. Real Chromium screenshots run in cloud sessions; the recipe
is `docs/frontend-cloud-runbook.md` and `frontend/e2e/cloud-board-screenshot.mjs`, with captures in
`frontend/e2e/artifacts/`.

**Four threads were freed by this the same day** — 027 (Opponents tab), 028 (Predictions tab), 029
(frequency array and tier grouping in the draft room), 041 (frontend WIP repair). All four were built
and tested long ago and sat blocked purely because nobody could photograph them.

**Decision on your open item, which you could not settle alone:** component reference baselines are
**yours** and regenerate when you change a component; screen baselines are **frontend's**. Your
proposed split is accepted. The regeneration step you could not own is the PM's to arrange.

**Correction to your capture list:** items 3–6 cannot be captured. The Settings screen and the Mock
Lab UI **do not exist** — Mock Lab has a backend store and no interface at all. Four of your seven
proposed surfaces have nothing to photograph. That is not a rejection of the list; it means those
entries are waiting on builds, and saying so is more useful than leaving them looking actionable.

## 3. The phone layout is yours now

**This is the biggest change for you.** The founder asked for the app to work on a phone, engineering
started building responsive layouts, and he stopped it and routed it to you — correctly.

His reasoning, and it is the right one: **"density as product" is a stated architectural principle
here.** The board is deliberately information-dense. How that degrades on a 390px screen is a
decision about what matters at a glance, not a CSS problem, and settling it in a media query would
have decided it by accident.

The constraint to design against, from `docs/founder-requests/FR-025-*`: **do not solve narrow
screens by hiding data.** That is the app showing less than it knows without saying so — the same
class of problem as a present-but-inert control. Prefer making data *reachable*: sticky first
columns, horizontal scroll inside the table rather than the page, disclosure. Absence is only correct
when a thing genuinely cannot function.

The reverted engineering attempt is preserved in commit `d0be35c` if seeing what was started is
useful. It is not a proposal — it is what was stopped.

## 4. New data on the board that has no design treatment

**Contract 1.14.0** added ADP to `board.json`, and it is being wired into the board, the draft screen
and the player profile **right now, without a spec from you.** Worth reviewing after the fact.

Per player row: `adp`, `adp_min_pick`, `adp_max_pick`, `adp_selected_pct`, `adp_source`. Top level:
`adp_source`, `adp_as_of_date`, `adp_match_rate_note`, `adp_source_note`.

**Two properties that are design problems, not engineering ones:**

- **144 of 511 rows carry a value; 366 are genuinely null.** The source only has an opinion on
  roughly the top 230 players. This is a large, legitimate null population on a primary column, and
  the null vocabulary you own has to carry it.
- **It is a proxy and must read as one.** The population is whoever drafts on MyFantasyLeague, not
  this league, captured at full PPR against a half-PPR league because the source's flag is binary.
  A bare number labelled "ADP" would overclaim. `adp_source_note` is written for display and states
  the caveat in full — probably too long to render verbatim, which is exactly the kind of thing you
  should specify rather than leave to a component author.

## 5. Smaller things that move your ground

- **The board is 511 players.** Some earlier specs assume 378. A header string saying "511 of 378
  players loaded" shipped and was caught.
- **A standalone single-file build now exists** — the whole app in one HTML file, no server, openable
  from a phone. It carries **Prep and Draft only. Season is absent**, because it has never been
  built. Draft was also absent until it was checked and turned out to work; the exclusion had been
  assumed rather than tested. **Absent-not-inert is being applied consistently now** — the detail
  sheet in that build names each dataset it does not carry and why, rather than rendering blanks.
- **Deferred work is mostly PM-generated** and the founder has been told so. Design-fidelity work
  sits behind the founder's three model questions and a 7 September draft. That is a sequencing
  decision, not a judgement on the work.

## 6. What would help most, in order

1. **The phone layout**, against the density constraint in §3. It is the only one the founder has
   personally asked for and been blocked on.
2. **A treatment for the large-null ADP column** in §4, including what the source caveat looks like
   at a glance rather than as a paragraph.
3. **The hosted-vs-local control question** in §1 — it will recur every time the app is served
   without a backend.
4. **Your acceptance capture list, trimmed to the three surfaces that exist**, with the component
   reference files you already proposed. That is the cheapest diff in the set and it is unblocked.

**Do not spend a run on the Settings or Mock Lab screens.** Neither exists and neither is scheduled
before the draft.

---

# Addendum, same day, later — the code moved again

Everything above still holds except where this section says otherwise. It is appended rather than
edited in because you have not consumed the first half yet, and knowing what changed *after* it was
written is more useful than a silently updated document.

**The founder's instruction that frames this whole addendum, verbatim:**

> "We've made a few changes that are ahead of design. Let's make sure it is aware and maybe it copies
> us there until we have parity. Then we likely just work on other things until we do an overhaul.
> (Unless we add features that need visibility before the overhaul)"

**So: the built app is the reference, not your prior mockups.** Where the code and your specs
disagree right now, the code wins by default and your job is to catch up to it — then we hold
steady and do other work until an overhaul is actually scheduled. That is a deliberate reversal of
the usual direction and it is temporary. It is not a judgement on the specs; it is that the app
moved faster than the design record today and a stale record is worse than none.

**One exception, stated by the founder in the same breath:** a *new* feature that needs visibility
before the overhaul is still yours to specify up front. Parity applies to what already exists.

## 7. Correction to §6 — your priority order has changed

**§6 item 1 was the phone layout. It is no longer first.** A competitive UX research pass landed
after this document was written (`docs/research/competitive-ux-2026-07-29.md`, thread 086) and its
headline runs against the direction everyone assumed: **the evidence for a frontend overhaul is
weaker than expected.** ESPN's 2025 redesign is cited as evidence that marginal return on visual
investment goes negative past roughly where this app already is, and the verbatim user complaints
it collected are about *density specifically*, not taste.

That is not a reason to stop. It is a reason to prefer scoped, shippable changes over a broad
re-skin, which changes what is worth your time. **Read that document before your next run.** It also
contains three specific things worth stealing and three worth avoiding, sourced and graded.

It also found that this project appears to have **commissioned the same competitive UX research
once before** — `docs/operating-model.md` logs a completed pass whose artifact is not in the
repository, and six live documents cite its conclusions, including the 5/10 visual-polish and 4/10
light-mode scores in `docs/design-handoff/HANDOFF-NOTES.md`. **Treat those two scores as
unsourced.** They may be right; nothing in the repo establishes it.

## 8. What was built today that you have not seen

All of it landed without a spec from you. That is the parity gap the founder is pointing at.

| Change | Where | Design status |
|---|---|---|
| ADP on board, draft screen, player profile | contract 1.14.0 | No spec — §4 above still applies |
| ADP glossary term + Methodology section | glossary/Methodology | Built today, unreviewed |
| Predictions scoped to the selected league | Predictions | Built today, unreviewed |
| Manual team-name entry for draft opponents | Opponents | **New interaction, no spec** |
| Draft-slot selector in Prep *and* Draft | both modes | **New control, no spec** |
| Randomise draft slot | Prep | New, from the research above |

**The two marked bold are the ones that most need you**, because they are the first controls in this
app where the user *supplies* data rather than reading it. The project's standing rule is that a
supplied value and a derived value never render as the same kind of thing — a typed opponent name
and a sourced one must be distinguishable, and a manually chosen draft slot must read as differing
from the one in the league file. **How that distinction looks is yours**, and right now it is being
decided by whoever writes the component.

## 9. Two structural decisions that change what screens must express

**9.1 — Two tracks, not one product** (`docs/founder-requests/FR-042-*`). The founder has ruled that
Westwood and everything else are almost separate tracks:

| | **Westwood (primary)** | **Every other league** |
|---|---|---|
| Scoring | Full custom ruleset, verified against the live platform | Standard, varying PPR only |
| Opponents | Named, modelled, custom knowledge of who drafts how | Generic. No identity, no tendency modelling |
| Purpose | The real draft | Rehearsal and portability |

**This is a design problem, not just a build one.** The same screens serve both tracks, and a user in
the generic track must be able to tell that the app knows less about that league — without the
screen feeling broken. Measured today: 26 of 27 leagues have no strategy data at all, and non-primary
leagues carry 7 export files against primary's 11, so four screens thin out on league switch. The
current answer is an empty state reading *"Not available for this league"*, which is honest and
tells the user nothing about whether it ever will be.

**9.2 — A League settings screen is now scheduled** (`docs/founder-requests/FR-040-*`). §6 said not
to spend a run on Settings because it did not exist. **That has changed** — the founder named it
important. It will offer a "custom league" option, and the backend for it already exists.

There is a hard constraint you should design against from the start: on the hosted site, roster
shape, team count and draft slot can be recomputed in the browser, but **anything touching scoring
cannot**, because the board ships final points and not the components underneath. So the screen must
present two classes of setting that behave differently, and the rule is absolute: **it must not
accept a setting it cannot apply.** A form that takes a touchdown value and then shows a board scored
under a different one is the worst outcome available. What that boundary looks like — and how it
avoids reading as a broken form — is a design question.

## 10. The inert-control question from §1 now has a known blast radius

§1 asked what a control that cannot work should do. It is six controls, not one, and the founder has
now personally clicked two of them and reported them as broken:

| Control | Location |
|---|---|
| Export CSV | `frontend/ui/views/Board.tsx:225` |
| Export PDF | `frontend/ui/views/Board.tsx:237` |
| League settings | `frontend/ui/components/shell/TopBar.tsx:195` |
| Compare | `frontend/ui/components/PlayerDetail.tsx:509` |
| Ask | `frontend/ui/components/PlayerDetail.tsx:512` |
| Ask the assistant (per glossary term) | `frontend/ui/views/Glossary.tsx:81` |

They divide into two causes: **not built yet** (Export, Compare, Ask) and **cannot work when hosted**
(Refresh data, since removed). League settings is about to leave this list by being built. One
treatment should cover both causes, and it is the cheapest high-value thing you can produce.

## 11. A prose and relevance review is queued for you

`docs/founder-requests/FR-041-*`, at the founder's own priority of **mid-to-low** — not before the
draft-critical work. Strategy guide, Methodology and Glossary: prose, design, and relevance.

Split deliberately: **whether the prose still matches what the code does** needs repo access and is
not yours. **What should be on these screens at all, what the empty states should say, and what
deserves prominence** is yours. Do not start until the ADP work above has landed — reviewing prose
that is mid-change wastes the review.

One observation to start from rather than rediscover: Methodology's *"Tested and found nothing"*
section — publishing what was tried and did not hold up — is the most trust-earning content in the
product and it sits fourth of five under a heading that reads like an appendix. Almost nothing in
this category publishes that at all. Its placement is a design judgement, which is why it is in your
half and not the accuracy half.

## 12. The priority order — this list supersedes every earlier one in this file

**Set by the founder, 2026-07-29: "put phone design at the 4th priority not the first."**

§6 item 1 said the phone layout was the most useful thing you could do. **That is superseded.** So is
the ordering that briefly sat here. This list is the current one; where it disagrees with anything
above, it wins.

**1 · The draft screen's middle pane, specified once.** Five separate founder requests land in the
same rectangle and specifying them one control at a time would decide the layout by accident:

- tabs, including seeing recommendations *before* his pick (FR-049)
- the periodic-table grid — **colour by position**, category convention, sortable by draft order or
  position-by-team (FR-044)
- where research insights surface near the relevant picks (FR-048)
- VBD's column space and column headers in the draft list (FR-050, FR-055)
- how "value versus the player expected at my next pick" shows its uncertainty (FR-051)

**2 · The two supplied-value controls.** Typed opponent names and the chosen draft slot are the first
places in this app where the user *supplies* data rather than reading it. The standing rule is that a
supplied value and a derived value never render as the same kind of thing, and right now that
distinction is being settled by whoever writes the component.

**3 · One treatment for controls that cannot work.** Six of them (FR-037). The founder is finding
them by clicking. One decision covers all six and it is the cheapest high-value thing in this file.

**4 · The phone layout.** Still real, still yours, still the only item he has personally been blocked
on — now fourth at his instruction rather than first. The constraint is unchanged and is the whole
difficulty: **do not solve narrow screens by hiding data.** Make it reachable — sticky first column,
horizontal scroll inside the table rather than the page, disclosure. Absence is only correct when
something genuinely cannot function.

**5 · The two-track expression** (§9.1). How a screen says "this league is the generic track" without
reading as broken. 26 of 27 leagues have no strategy data at all and four screens thin out on a
league switch.

**6 · The League settings boundary** (§9.2) — the line between settings that apply instantly and
settings that cannot apply at all on a hosted site.

**7 · The large-null ADP column** (§4) and **the acceptance capture list** (§6 item 4). Both
unchanged, both still worth doing.
