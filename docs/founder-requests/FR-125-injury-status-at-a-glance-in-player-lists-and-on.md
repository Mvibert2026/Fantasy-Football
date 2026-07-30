---
ID: FR-125
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
NEEDS: data-ops (ingestion) before any UI
---

## Request

Founder's own words:

> "injury status should show in lists of players and in player card, if no injury, it should show
> healthy - needs to be easy to see at a glance - this includes suspension or IR, or PUP etc  but
> all the regular status as well"

## Why it matters

He described it as a display item. **It is not — the data does not exist.** That is the finding, and
it is the whole reason this needs an FR rather than a one-line dispatch.

Measured against the shipping export, `data/export/board.json`, all 510 players:

| `roster_status` value | Count |
|---|---|
| `active` | 402 |
| `unknown_no_contract_data` | 72 |
| `no_active_contract_on_file` | 36 |

| `suspension_flag` | Count |
|---|---|
| `False` | 510 |

**There is no injury status in the export at any granularity.** No IR, no PUP, no NFI, no
questionable / doubtful / out. `roster_status` is a *contract* field — whether the player is under
contract — which is a different question wearing a similar name, and would be actively misleading if
rendered as health. `suspension_flag` is uniformly false, which is a plausible reading for the
current date but is not evidence that suspensions are tracked.

So the honest state today is: the app cannot say a player is healthy, because it does not know.

## Initial read

**Building the UI first would produce exactly the defect this project refuses.** His "if no injury,
it should show healthy" is the dangerous half of the request — rendering `HEALTHY` from the absence
of an injury field is fabricating a value from missing data, which `CLAUDE.md` §1 and the never-
fabricate rule prohibit outright. **Absence of an injury record is not evidence of health.** Until
ingestion exists, the correct render is that status is not tracked, stated in place with the reason.
That distinction must be built in from the start.

**Two threads already cover the ingestion half and both are open and unworked:**

- **070** — recurring injury / suspension feed. `TO: pm`, OPEN 3 days. Blocks *"T4 suspensions and
  roster-status table stakes"* and `E[games_played]`.
- **097** — ingest nflverse weekly roster status. `TO: ranker`, OPEN. Named as *"the only source"*
  for the season-ending-IR and suspension error classes in the bottom-up component model.

Thread 097 is the concrete one: nflverse's weekly roster data carries status codes, it is already a
dependency this project uses, it is free and its licensing is settled. **That is the cheapest path
to a real answer and it is already written up.** This FR should not spawn a third parallel effort —
it should raise the priority of 097 and give it a consumer, which is what it has lacked.

**Once the data exists, the display half is genuinely small and folds into work already specified:**

- **In lists** — `RANKINGS-PANE.md` defines a strict column drop order for width. A status indicator
  has to enter that order explicitly, and it must drop *before* the player's name, which never drops.
- **On the card** — `PLAYER-PROFILE.md` §1 puts identity first. Status belongs in the identity strip,
  which is the same contested line the archetype chip wanted and could not have. Design should rule
  on whether both fit, given that the archetype chip is absent on 57.8% of players and status would
  be present on all of them — arguably the stronger claim on that space.

**Sequencing:** ingestion (097) → export field + contract bump → design ruling on the strip →
frontend. Not a fold-in to current work. Do not build the UI against `roster_status`.

---

## Founder direction on sources, 2026-07-30

His own words, after being told the data does not exist:

> "Find sources for injury. It's gotta be nfl available. Lots of other fantasy sites track it. We
> probably also should be scraping twitter of reporters etc. Research should figure it out (but
> let's get all front end and app work to main first)"

**Explicitly sequenced behind the frontend queue.** Do not dispatch `researcher` until the
2026-07-31 design items are merged to `main`.

### What to hand `researcher` when it is time

The mandate is a **sourcing and licensing audit, not a build**. Four candidate tiers, in the order
they should be evaluated — cheapest and most defensible first:

| Tier | Candidate | What to establish |
|---|---|---|
| 1 | **nflverse weekly roster status** (thread 097) | Already a dependency, free, CC-BY, licensing settled. Which status codes it carries, at what latency, and whether it distinguishes IR / PUP / NFI / suspension from game-day designations. **If this covers the ask, the other three tiers are unnecessary** — say so and stop. |
| 2 | **The NFL's own injury report** | Clubs are required to publish participation and game status. Establish whether it is retrievable without a commercial licence, and at what cadence. |
| 3 | **Aggregators** ("lots of other fantasy sites track it") | Establish terms before anything else. Most restate wire copy under terms that forbid redistribution. A source we cannot use is the likeliest outcome and is cheap to rule out. **Do not fetch Yahoo, ESPN or CBS — they block research agents by name.** |
| 4 | **Reporter feeds on X/Twitter** | See the constraint below. Evaluate last. |

### The X/Twitter constraint, stated plainly

The founder suggested scraping reporters' feeds. Three things make that the weakest option, and he
should have them before anyone spends time on it:

1. **Scraping X is against its terms**, and the documented API path is a paid subscription. `CLAUDE.md`
   §5 requires terms be checked before a scraper is built, not after; §10 rules out approaches that
   create a credential or compliance liability. This is not a "we'll see" — it is the same class of
   decision as the Yahoo password question, which was already resolved against browser automation.
2. **Free-text posts have no join key.** A headline resolves to a player only by name matching — the
   problem that quarantined eight players out of 330 in this session's mock ingestion, on far cleaner
   input than a reporter's phrasing.
3. **Reporter feeds carry rumour at the same confidence as fact.** A designation on the official
   report is a claim the club made. A post saying a player "looked limited" is not, and the app has
   no way to grade the difference. Under the never-fabricate rule the second cannot render as status.

**Recommend: rule out tier 4 unless tiers 1–3 all fail**, and say so to the founder rather than
quietly not doing it. If tiers 1–3 do fail, the honest answer may be that this feature does not ship,
which is a legitimate outcome.

### What "healthy" can honestly mean

Whatever source lands, the render for an uninjured player must be traceable to a source that
*affirmatively* lists him as available — not inferred from his absence from an injury list. If the
chosen source only publishes injured players, then "healthy" is not a fact we hold, and the correct
render is the status's own vocabulary (e.g. "not on this week's report"), not a health claim.

---

## Founder correction, 2026-07-30 — personal use, and what survives it

His words:

> "rememer, I'm not redistributing these, it's personal use as if I went to the sites themselves -
> I'm just making my digestion more efficient"

**He is right, and the tier table above overstated the licensing objection.** Most of what was
written as a blocker was a *redistribution* restriction, and nothing here is redistributed. The
posture is one person reading sources he could open in a browser, assembled for his own use.

**The password gate is what makes that claim true, and it already exists.** `worker/index.js`'s own
comment states the reasoning: every data source this project uses — FantasyPros, FFC, Sleeper —
permits personal use only, and *"a public URL with no auth is the one fact that turns 'personal use'
into 'distribution', for all three at once."* The gate was built for exactly this. So the constraint
that actually binds is **keep the gate on**, not "do not use these sources."

### Revised tier table

| Tier | Candidate | Status after the correction |
|---|---|---|
| 1 | **nflverse weekly roster status** (thread 097) | Unchanged. Still first — free, CC-BY, already a dependency, no terms question at all. If it covers the ask, stop here. |
| 2 | **NFL's own injury report** | Unchanged. Clubs publish participation and game status. |
| 3 | **Aggregators / other fantasy sites** | **Substantially opened up.** The redistribution objection does not apply. Evaluate on retrievability and reliability. Still do not fetch Yahoo, ESPN or CBS — they block research agents by name, which is a practical wall, not a legal one. |
| 4 | **Reporter feeds on X** | Weakened but not cleared — see below. |

### What still stands, narrowed

Three objections survive the correction, and only one of them is about terms:

1. **X's terms prohibit automated scraping as a contract term, independent of what is done with the
   data.** Personal use does not dissolve that particular clause the way it dissolves a
   redistribution clause. This is worth one sentence and no more: it is the founder's call on his own
   tool, the stakes are low, and he has been told. **It is not a reason to refuse the work** — and if
   he wants it evaluated anyway, evaluate it.
2. **No join key.** Free-text posts resolve to a player only by name matching — the problem that
   quarantined eight of 330 picks in this session's mock ingestion, on cleaner input than a
   reporter's phrasing. This is a data-quality objection and it is unaffected by licensing.
3. **Rumour and designation arrive at the same confidence.** "Looked limited in practice" is not a
   claim a club made; an official designation is. The app has no way to grade the difference, and
   under the never-fabricate rule the first cannot render as status. Also unaffected by licensing.

**Objections 2 and 3 were always the stronger reasons to prefer tier 1**, and they do not depend on
the legal argument at all. That was under-weighted in the original writeup and is the correction that
matters.

### What this changes for the researcher mandate

Lead with retrievability and reliability, not licensing. The question is *"which source publishes an
affirmative status for every player, at what latency, in a form that joins to `player_id_gsis`"* —
not *"which source are we allowed to read."* Report terms only where a hard technical or contractual
wall exists (X's scraping clause, the Yahoo/ESPN/CBS agent block), and do not spend a paragraph on
redistribution for a tool that redistributes nothing.
