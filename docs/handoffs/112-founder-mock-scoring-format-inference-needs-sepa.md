---
ID: 112
FROM: data-ops
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Two new founder mocks were ingested this session (`data-ops`, 2026-07-30):
`data/mock-drafts/yahoo-10team-slot4-2026-07-30.json` (150 picks, 131 resolved) and
`data/mock-drafts/yahoo-12team-slot2-2026-07-30.json` (180 picks, 160 resolved). The founder
could not confirm their scoring format ("I think they are for half PPR, but not sure"). Full
writeup: `docs/analysis/founder-mocks-2026-07-30.md`.

I computed Spearman rank correlation of each mock's realized pick order against FFC ADP
(`ffc_adp_snapshots`, joined on `mfl_id`) at the matching team count, all available formats:

- 10-team (current 2026-07-29 snapshots): standard ρ=0.9333 (n=126), half-PPR ρ=0.9485 (n=130),
  PPR ρ=0.9541 (n=130).
- 12-team (**stale**, no snapshot newer than 2024-09-01 for either 12-team format, and no
  `ffc_ppr_12team` source exists at all): standard ρ=0.5590 (n=104), half-PPR ρ=0.5707 (n=101).

Need three things, all past what data-ops's remit covers:

1. **A formal test for whether the 10-team ρ's are actually separable** (e.g. Steiger/Hittner
   test for the difference between two correlations computed on overlapping/dependent samples,
   since standard vs. half vs. PPR ADP values are correlated with each other by construction).
   Right now I can only say "PPR fits best, standard fits worst, direction matches the founder's
   guess" — I cannot say whether 0.9541 vs. 0.9333 is a real signal or noise at n≈130.
2. **Whether the missing current 12-team/PPR ADP snapshots are worth back-filling** before
   trusting the 12-team comparison at all — right now that comparison runs against a ~2-year-old
   market, not the current one, and I don't have a call on whether that's acceptable evidence or
   needs a fresh scrape first.
3. **Any read on the TE-early anomaly**: Bowers went pick 23/150 (10-team) and 15/180 (12-team);
   McBride went 28/150 and 20/180. Both are earlier than even the most reception-friendly current
   FFC format predicts (Bowers ranks 37th-50th, McBride 32nd-48th, depending on format). Is this
   evidence the room drafted more PPR-aggressively than any FFC format captures, or noise from a
   small, possibly bot-heavy mock pool that a scoring-format read shouldn't try to explain?

## Why

The founder is about to log ~30 mock drafts total (currently at 3). If scoring format is treated
as settled at LOW-to-MODERATE data-ops confidence when it should be either higher (worth stating
plainly) or genuinely inconclusive (worth telling the founder to stop guessing and just confirm
the platform setting), that confidence level propagates into every downstream use of these mocks
without anyone re-checking it.

## Done looks like

A reply here stating: (a) whether the 10-team half-PPR-vs-PPR gap is statistically separable at
this n, with the test used; (b) a yes/no on back-filling current 12-team ADP (and if yes, whether
that's a `data-ops` re-scrape ask back to me); (c) a one-line read on the TE-early anomaly. No
new ingestion or scoring code expected — this is a methodology judgment call on data already
ingested.
