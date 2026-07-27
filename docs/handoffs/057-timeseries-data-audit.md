---
ID: 057
FROM: pm
TO: data-ops, researcher
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: injury-aware rankings, ADP drift model, suspension correctness guarantee, Fable Addendum 2
---

## Ask

Establish **what time-series and as-of-date data we can actually obtain**, before anyone designs a
model that assumes it exists. Every item below gates a piece of the ranking architecture in
`docs/fable-mandate-2026-07-27.md` Addendum 2.

Answer with evidence — endpoints called, row counts, sample rows, field names. A working request beats
a paragraph about whether one might exist.

### 1. Dated ADP snapshots — MERGED, do not answer separately here

**FFC date-range question → merged into [055](055-ffc-adp-history-harvest.md).** It is a prerequisite
question for that thread's historical harvest, not separate research — 055 already owns building the
FFC ingestion under D-021.

**Sleeper/MFL dated-ADP question → merged into [054](054-ftn-and-sleeper-harvest.md) § 2.** Exact
duplicate of 054's three Sleeper-endpoint tests (draft ID enumerability,
`/v1/user/{user_id}/drafts`, listing surfaces). Struck from here.

~~- Does Fantasy Football Calculator expose ADP filtered by **date range**, or only a single current
  aggregate per format? Their pages appear to support a date window — confirm or refute by fetching.~~
~~- Sleeper, MyFantasyLeague, or any other free source with dated or rolling ADP.~~
- Failing all of that: can we build our own time series **going forward** by snapshotting FFC weekly
  from now until the draft? That is a low-cost fallback and it starts paying immediately, but only if
  it starts now. **If nothing historical exists, say so and start the forward snapshot the same day.**
  (Still open here — not covered by 054 or 055, both of which are historical-harvest scoped.)

Constraints from D-021 apply: HTML endpoints only, ≤1 req/sec, cached, honest User-Agent.

### 2. nflverse injury data — and the question that actually matters

Confirm coverage from 2009: fields available, practice participation (DNP / limited / full), game
status designations, row counts by season.

**Then the critical question, which is not about coverage:** are these tables **point-in-time or
retroactively updated?** If a row for week 3 reflects what was known in week 3, we can backtest
honestly. If it has since been corrected with information that arrived later, then every backtest
using it **leaks the future** and its results are fiction.

This is the single most important finding in this thread. Test it if you can — compare an archived
older copy against the current one for the same season, or check whether the package documents
revision behaviour. **If you cannot determine it, say "unresolved" rather than assuming the
convenient answer.**

### 3. Games played, snap share and return-from-injury history

For the ramp-curve work — estimating how a player's usage recovers over the weeks *after* returning
from injury — we need, by player-week: games active/inactive, snap share, route participation, touch
share. Confirm availability and span. Identify how many historical return-from-injury cases exist
with usable pre- and post-injury usage on both sides; that count determines whether the ramp curve is
estimable at all, and by injury type or only in aggregate.

### 4. Suspensions — structured source, or manual?

Known suspensions are a **correctness guarantee**, not a nicety: an eight-game suspension must be a
deterministic deduction from expected games played, enforced by a blocking test. See Addendum 2 § 2C
correction.

- Is there any free structured source for NFL suspensions — length, effective date, appeal status?
- If not, the table is hand-maintained. **Say so plainly**, and propose the smallest maintainable
  schema plus a `current_as_of` field, because staleness here is worse than absence: a four-week-old
  table makes the board look authoritative while being wrong.
- Note appeal reductions specifically. Suspensions announced in the offseason are frequently reduced,
  and a table that captures only the announcement will overstate the deduction.

### 5. News and transactions

RotoWire RSS is already known. Anything else free and structured — depth charts, transactions,
personnel and coordinator changes. Latency matters more than richness; note the lag on each.

## Done looks like

`docs/research/timeseries-data-audit-2026-07.md`. Per source: what exists, span, fields, licence
status, latency, and **whether it is point-in-time or retroactively revised**. Confidence tagged
throughout. Blocked means recorded with evidence and stopped, never routed around.

Then one recommendation: which of the four modelling directions in Addendum 2 are **actually
supported by obtainable data**, and which should be dropped before anyone specs them.

**File boundary:** `docs/research/`, `data/raw/`, `tools/`. Do not touch `src/`, `frontend/`, or
`docs/CURRENT-STATE.md`.

---
### pm · 2026-07-27

Struck §1's dated-ADP sub-item (→ [055](055-ffc-adp-history-harvest.md), prerequisite question) and
Sleeper sub-item (→ [054](054-ftn-and-sleeper-harvest.md) § 2, exact duplicate) per reconciliation
pass (`docs/handoffs/RECONCILIATION-2026-07.md`). Remainder (forward-snapshot fallback, injury
point-in-time-ness, return-from-injury history, suspensions, news latency) stays open — none of it is
duplicated elsewhere, and the injury retroactive-revision question is the single highest-consequence
item in this backlog. Still `TO: data-ops, researcher`.
