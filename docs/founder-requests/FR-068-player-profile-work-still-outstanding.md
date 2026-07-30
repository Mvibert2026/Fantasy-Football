---
ID: FR-068
STATUS: NEW
PRIORITY: MEDIUM
ROUTED-TO: design
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Player profile work still outstanding

Founder's own words:

> "The player profile work still needs to occur"

## What is outstanding

ADP was wired into the player profile alongside the board and draft screen (contract 1.14.0), but
**no design spec was ever written for the profile itself** — it was one of the surfaces design's
round-one capture list could not review, and it has not been specified since.

**FantasyPros' player card is the reference the founder has already reacted well to**, recorded in
detail at `docs/design-handoff/competitor-screenshots/README.md`. What it does that ours does not:

- **Four header stats as one strip, each expressed as a positional rank** — `ADP WR3 · ECR WR3 ·
  Last Season WR1 · SOS 21st`. Not raw numbers. That is the readable form under a clock, and our
  board shows overall rank and raw ADP instead.
- **A scoring-format selector on the card itself**, re-pricing in place.
- **A jump-to-section bar over one continuous page** — the founder corrected an earlier reading of
  this: it is not tabs, nothing is ever hidden.
- **A "Draft Now" primary action** on the card.

**And one thing to study rather than copy:** its AI sentiment meters (OVERALL / UPSIDE / BUST) are a
good idiom — five segments plus a word, no false precision, survives greyscale — but they are backed
by prose sourced to nothing. If we ship meters they must be computed from something and say what.

## Two things ours has that theirs does not, and they should lead

Our profile can show **VBD** and **the delta against consensus** — a stated, defensible disagreement
about a player. That is the thing no competitor card carries, and it is the reason to have our own
profile rather than a copy of theirs.

Queued for design's next round.
