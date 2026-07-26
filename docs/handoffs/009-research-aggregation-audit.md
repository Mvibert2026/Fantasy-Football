---
ID: 009
FROM: pm
TO: researcher
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: FR-001 spec
---

## Ask

Source-availability audit for the research/aggregation section (FR-001). **Audit only — do not
design the feature and do not propose a UI.** The output is a table of what can actually be
obtained, so a spec can be written against reality.

For each candidate source, establish and tag with the standard confidence markers
(`[VERIFIED]` / `[SNIPPET]` / `[SECONDARY]` / `[GAP]`):

1. Does a public, documented API or feed exist? Exact endpoint if so.
2. Auth required? Rate limits? Cost?
3. What does `robots.txt` and the ToS actually permit — separately for *fetching* and for
   *displaying to a user*. These differ and the difference is the whole legal question.
4. Push (webhook/RSS) or pull-only? Push is materially cheaper to run.
5. What granularity — overall ranks, positional, tiers, projections, prose takes?
6. Update cadence, and whether historical snapshots are retrievable.

**Candidates:** FantasyPros (ECR + ADP, free vs paid), Sleeper, ESPN, Yahoo, CBS, NFL.com (being
retired into ESPN — legacy value only), Underdog, FFC, MFL, PFF, 4for4, FootballGuys, Establish
The Run, RotoWire, Fantasy Life, plus beat-reporter and injury feeds for the "takes" half.

Several of these are already established as blocked — FFC's `robots.txt`, ESPN/Yahoo OAuth,
Sleeper's absent aggregate endpoint. Re-confirm rather than assume; some may have changed, and one
that has changed is worth the whole audit.

## Why

FR-001 as stated ("see other public rankings or takes, anything we can aggregate") is the
user-facing surface of two things already in Fable scope — the multi-consensus benchmark layer
(item 5) and newsfeed aggregation (item 6), both currently specced as backend capability with no UI.

The project's standing sequencing is data-source audit first. Designing a comparison screen before
knowing what may be legally displayed produces a mock of data we might have no right to show — and
this becomes load-bearing the moment the product stops being private-use.

## Constraints

- **Never fill a `[GAP]` with a plausible-sounding number.** This rule has held throughout and it
  holds here.
- Distinguish *fetching* from *redistributing*. A source that permits personal fetching may forbid
  display to third parties. That single distinction decides whether a source is viable for a
  product versus only for backtesting.
- Flag anything where the answer changed since the last audit — that is the highest-value finding
  in the whole exercise.

## Done looks like

A markdown table committed to `docs/research/source-audit-2026-07.md`, one row per source, every
cell confidence-tagged. Plus a short closing section naming the two or three sources that are
genuinely viable today, and what a minimum viable comparison view could honestly show using only
those. Then reply here and set `STATUS: RESOLVED`.
