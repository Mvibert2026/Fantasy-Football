---
ID: FR-026
STATUS: IN PROGRESS
SOURCE: chat session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
Capture non-PPR ADP as well, alongside half-PPR

> "we should also download and store no ppr"

Founder's own words, 2026-07-29, immediately after the first half-PPR capture landed.

## Why it matters

Two reasons, and the second is worth more than the first.

**Non-PPR is the market he will actually meet in mock drafts.** He joins public Yahoo rooms and
autodrafts. Those rooms are standard scoring and standard roster shape; Westwood is neither. Mock
drafts are the only calibration path this project has for its availability model, so capturing the
format the mocks actually run in is capturing the population whose behaviour those mocks will teach
us about.

**Three formats from one source, one day, one league size isolates the format effect.** Same site,
same drafters, same rolling window, one variable moving. The difference between a player's non-PPR
and half-PPR ADP *is* the format correction — measured rather than assumed.

That bears directly on the hardest open problem in the availability model: separating what a mock
teaches about **drafter behaviour** (which transfers across formats) from what it teaches about
**positional demand** (which does not, and must come from league config). There is currently no
empirical handle on that split at all — the mandate for the availability review asks whether the
model even distinguishes the two, and suspects hardcoded constants mean it does not. This gives a
direct measurement of one half of it, for the cost of two extra HTTP requests per day.

**Timing matters and cannot be recovered.** ADP is not an archive — MyFantasyLeague serves a rolling
aggregate whose sample was observed *falling* (50 drafts on 2026-07-26, 43 on 2026-07-29), and FFC
publishes a five-day rolling window. A day not captured is gone. Every day the format ladder is
incomplete is a day the format effect cannot be measured for.

## Initial read

Scope taken as **all three formats at 10 teams — non-PPR, half-PPR, full PPR** — rather than only
the one named. Half-PPR already captures; the other two go through the same path. Dispatched to the
running data-ops chain 2026-07-29.

Full PPR earns its place independently: it gives a same-day, same-team-count check against the
existing MyFantasyLeague full-PPR proxy — two independent measurements of one quantity, on a source
the project has been relying on unverified.

**Constraints, all pre-existing rather than invented here:**

- **Each format is its own `adp_source` value** (`ffc_half_ppr_10team` and siblings), precise enough
  that format and team count are unambiguous from the value alone. Formats must never be blended or
  averaged into a "consensus ADP" — `CLAUDE.md` §4, enforced by an existing test.
- At most one fetch per format per calendar day, descriptive User-Agent, backoff on 429. Three
  requests a day to a small site is courteous; a retry storm is not.

**Deliberately not done: other team sizes.** FFC offers 8/10/12/14 and taking all of them is
tempting, but the room sizes his mocks will actually use are not yet known, and over-collecting from
a small site with no consumer for the data is not a courtesy worth spending. Ten-team matches
Westwood and is the one that can be reasoned about. **This is a decision waiting on a fact, not an
oversight** — once the mock rooms are known, adding a team-size variant is cheap.

Historical backfill remains in scope for these formats if FFC serves genuine point-in-time data, and
must carry `is_retrospective_aggregate` if it does not — treating a retrospective aggregate as a
preseason board is look-ahead bias (`CLAUDE.md` §6.1).
