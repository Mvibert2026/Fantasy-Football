---
ID: 091
FROM: researcher
TO: pm,design
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

# UNALLOCATED handoff body — component projections + FR-053 features (researcher → pm, design)

**This is not a thread. It has no ID and must not be given one by hand.**

This researcher session ran in a cloud container with **no shell tool** (tools available: Read, Write,
Edit, Glob, Grep, WebSearch, WebFetch — no Bash), so `python tools/handoffs.py new` could not be run
and **nothing could be committed**. Thread IDs come only from the allocator; hand-typing or computing
max+1 is what collided at ADR-048 and threads 043 / 049 / 053. The body is staged here so the next
session with a shell can allocate it in one command and paste this in. Same pattern thread 086 used
on 2026-07-29.

**Allocator command:**

```
python tools/handoffs.py new --from researcher --to pm,design \
  --subject "Component projections exist and are cheap for personal use, illegal to redistribute; kill the source switcher" \
  --blocks "FR-040 (custom scoring in the browser), FR-053 feature decisions, FR-044/FR-049 design work"
```

---

## Ask

`docs/research/component-projections-and-fr-053-features-2026-07-29.md` is the full artifact. Five
things need a decision or an owner; **two of them are escalations, not researcher calls.**

### 1. FR-040's blocker was misdiagnosed — `pm`, then the founder

FR-040 concluded that full custom scoring "cannot be computed in the browser" because `board.json`
carries no component stats, and treated that as definitive. **The absence is real; the diagnosis was
one step short.**

Component projections are obtainable **today**, per player, per component:

- **Free**: Sleeper's public endpoint `api.sleeper.com/projections/nfl/2026?season_type=regular&position[]=QB`
  returns 151 QB rows for 2026, updated late July 2026, with `pass_att/cmp/yd/td/int`, `rec/rec_yd/
  rec_td`, `rush_att/rush_yd`, `fum_lost` and `gp` (projected games played). Provider is Rotowire.
  robots.txt permits it. `[VERIFIED — fetched]`
- **$8.99/mo**: FantasyPros API Premium — *"Rankings, projections … full stat lines"*, *"Production
  keys for personal apps"*. `[VERIFIED]`

**But neither may be served from the public site.** Sleeper ToS §9.2 grants a *"personal and
non-commercial"* licence and expressly forbids redistribution `[VERIFIED, quoted verbatim in the
artifact]`. FantasyPros Premium is *"Personal & non-commercial apps"* only; redistribution rights live
in the Commercial tier at custom, sales-call pricing `[VERIFIED]`.

**So the real constraint is not the data — it is that we host this publicly.** Three routes, costed in
artifact §2.6: personal-use ingestion (free–$8.99/mo, requires the site stop serving derived component
values), a commercial licence (unknown price, `[GAP]` — founder's spend decision, not mine), or
building our own from nflverse CC-BY-4.0 (legal for the public site, but it is a projection system,
i.e. `CLAUDE.md` build-order steps 4–5 done properly).

**Note for whoever costs route 3:** nflverse core data is CC-BY-4.0, attribution only — but
`ffopportunity`'s **data and models are CC-BY-SA 4.0**, and ShareAlike is viral. Building on raw
nflverse play-by-play carries attribution only; building on ffopportunity's pre-fitted model may
oblige us to release derivatives under CC-BY-SA. Same ecosystem, two licences, easy to miss.

Also worth recording: `ffopportunity` is **retrospective, not predictive** — an
opportunity→expected-components model over past plays, trained 2006–2020. It is not a 2026 forecast
and never was. It *is* an excellent component-level **backtest substrate** for re-scoring history
under any scoring format, which serves Phase 1 directly even if no forward projection is ever built.

### 2. ESCALATION — two live licensing conditions the public deploy may have crossed

**I am flagging these and stopping. Neither is a researcher's call, and one is probably the
founder's.**

- **`board.json` is served publicly and carries FantasyPros-derived values.** Every row exports
  `consensus_rank` (`src/export_contract.py:347`); the header names `board_source`/`consensus_source`
  as `fantasypros_csv_2026draft` (`src/export_contract.py:435-441`), from a founder-downloaded
  FantasyPros CSV (`src/ingest_fantasypros_csv.py:1-15`). FantasyPros' Terms of Use: *"Except for a
  single copy made for personal use only, you may not copy, reproduce, modify, republish, upload,
  post, transmit, or distribute any documents or information from this site in any form or by any
  means without prior written permission."* `[VERIFIED]`
- **FR-023's FFC permission is conditional and the condition names this exact situation.** Its own
  text: *"Scoped to **private use by one person**. Void if the product ever reaches a second human,
  alongside D-020 and D-021."* `docs/CURRENT-STATE.md` records the app as live on the internet,
  public by explicit founder choice.

These are contradictions between a documented condition and a documented state, which the operating
rules say to escalate rather than resolve. They also change the shape of item 1: **if the site is
going to stay public, the licensing question is not new — it is already open.**

### 3. Kill the projection-source switcher — `design`, and the evidence is unusually strong

FR-053 lists "selectable projection source" as a feature Yahoo has and we do not. **Do not build it.**

- `[VERIFIED]` Fantasy Football Analytics, **2014–2025, 11 sources, MAE**: *"The average of sources is
  more accurate than individual sources. This remains true and is perhaps the most robust finding in
  our analysis."* · *"FFA Average outperformed individual sources in 69% of head-to-head comparisons
  across all positions and seasons."* Individual sources are volatile year to year (CBS: 1st for QB
  in 2019, 6th in 2021, 2nd in 2022, 7th in 2023).
- `[SNIPPET]` **Yahoo's own free default is a consensus** of multiple licensed providers, marketed by
  Yahoo as more accurate; the switcher is a **Fantasy Plus paid** upsell. (Yahoo hosts are a standing
  block and were not fetched.)
- `[VERIFIED]`, thread 086: Draft Sharks shows **three numbers simultaneously** (own, 38-site
  consensus, ceiling/floor) rather than a switcher.

**The productive version is the one thread 086 already ranked #1:** if we ever hold more than one
component set, average them and render the **spread** — which is the same object as *"not
distinguishable from ranks X–Y."* One display, two findings, no new control. A switcher asks the user
for a choice they have no basis to make and discards the variance reduction. It also multiplies the
licensing surface by the number of options.

### 4. The "your turn — Nth pick" divider: build it, but not as a line — `design`

`[GAP]` **No user-demand evidence exists in either direction.** I looked and found nothing; the one
third-party draft-software feature comparison I could fetch does not mention the feature at all. I am
reporting the absence rather than reasoning from plausibility, per the standing instruction.

What is established: two vendors (FantasyPros' Pick Predictor, Draft Sharks) monetise the underlying
question, and **this project already computes survival probability to the next pick**. So the divider
is not a new capability — it is a cheaper rendering of one we have.

**The constraint that must not be lost:** a hard line asserts *"everything above is gone"* about a
quantity that is a smoothly decaying probability. That converts a calibrated distribution into a
binary claim — the unearned confidence `CLAUDE.md` §11 forbids, and the same failure mode thread 086
flagged for composite scores. Ship it as a **band** (*"picks 12–19 are the uncertain zone"*) or a
labelled line (*"~50% of these are gone by your pick"*). Not a rule across the list.

### 5. ADP trend: build it, scoped to availability — needs **no new source and no new licence**

`[IN-REPO]` The daily capture is already running off-machine; `data/adp-snapshots/` holds 2026-07-26,
07-28 and 07-29 today. A rolling 7-day window becomes computable within days, and the draft is
7 September — so by draft day we would hold roughly six weeks of our own daily history. Yahoo charges
for "Last 7 Days ADP"; we would compute it from data we already own.

**Frame it as a market-behaviour signal, not a value signal.** RotoWire — which sells the data —
states verbatim: *"Fantasy football ADP is solely a measure of how a player's perceived value is
trending. These changes will oftentimes not match up with a player's updated RotoWire fantasy football
projections."* `[VERIFIED]` `[GAP]`: no empirical study of short-window ADP movement's predictive
value was found; the category publishes the feature weekly and the evidence never. Used for *"will he
still be there at my pick"* (thread 078's framing) it measures the right thing. Used for *"is he
good"* it measures hype.

## Why

FR-053 asked whether components can be sourced and on what licence, and stated that licensing is the
deliverable rather than a footnote. The answer is that the sourcing question is easy and the licensing
question is the whole problem — and it turns out to be the same question already sitting unanswered
under the public deploy. Returning a list of vendors without that would have been the wrong artifact.

## Constraints honoured

Every recorded block was honoured and none routed around. **Yahoo, ESPN and CBS hosts were not
attempted**; all Yahoo claims are `[SNIPPET]` from search-result synthesis and are labelled as such.
**NFL.com publishes the single best-matching component column set found** (it includes return TDs and
2-point conversions, which even the Sleeper feed lacks) — and its Terms of Service prohibit
*"systematic retrieval of data or other content … to create or compile … a collection, compilation,
database"* `[VERIFIED]`. **Recorded as blocked and stopped.** One assessment fetch of the projections
page was made *before* reading the terms; no further access and no ingestion is proposed.
`www.fantasylife.com` left unfetched for consistency with thread 009. `www.reddit.com` remains refused
by the tool.

**Fetching vs. redistributing, answered separately for every candidate** — artifact §2.3 has two
distinct columns for exactly that, because for this project the answer *differs by column for every
single source*. No competitor's data is proposed for storage or display anywhere in the artifact.

## Sample quality, stated plainly

Twelve candidate sources collapse into **three licence regimes** — open-but-no-projections (n=1),
published-but-personal-use-only (3 vendors, one answer), and commercial-by-sales-call (4 vendors, one
answer, **all four prices `[GAP]`**). The count that matters is **zero**: no source found publishes
component projections under a licence permitting redistribution, and that is structural rather than a
coverage failure.

Section B has **no voice-of-customer evidence at all** — Reddit is still refused. And the strongest
study in it (FFA's accuracy work) **is run by the maintainers of the aggregate it benchmarks**, who
found their own aggregate wins. It agrees with what I expected before looking, which is when it
deserves the most scrutiny; it is partly rescued by an unsurprising mechanism and by Yahoo
independently behaving as if it is true. Quote it accordingly.

One structural observation worth PM's attention: **five founder screenshots produced more competitive
fact than two full agent research passes.** Yahoo blocks agents by name; the founder is not blocked.

## Done looks like

PM dispositions the two escalations in §2 (they may need the founder) and records a decision on §1's
three routes. Design takes or declines §3 (decline recommended), §4 and §5 with a thread each. Then
reply here and set `STATUS:` appropriately — only the `TO:` role may resolve.
