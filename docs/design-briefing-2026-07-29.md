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
