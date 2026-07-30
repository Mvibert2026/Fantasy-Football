---
ID: FR-123
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
NEEDS: ranker, then design
---

## Request

Founder's own words:

> "the archetpes need work, we probably need more categories - the 35% rule can't be global -
> Ratcliffe does a decent job of that - maybe we need one in football terms and one in fantasy
> context/terms"

## Why it matters

Measured against the current export, the taxonomy is worse than the standing figures suggest:

| Covered-position board rows (RB/WR/TE) | 460 |
|---|---|
| Carry a real archetype label | 194 (42.2%) |
| Render `UNCLASSIFIED` | 266 (57.8%) |

**The label is absent on the majority of players it is meant to describe.** The previously quoted
figure — roughly a third unclassified — came from a researcher's snapshot; measured live against
what the browser actually loads, it is 57.8%. And among the players who *do* get a label, the
concentration problem stands: `RB_COMMITTEE` covers 62.7% of running backs, `TE_SECONDARY_RECEIVER`
51.0% of tight ends.

So the chip is uninformative when present and absent when not. `docs/design/PLAYER-PROFILE.md` §4
has already had to design around that.

## Initial read

**Three separable claims in the founder's message. They should not be answered as one.**

**1 · "More categories."** Straightforwardly right, and the measurement supports it — a bucket
holding 62.7% of a position is not a description, it is a default.

**2 · "The 35% rule can't be global."** He is correcting this project's own proposal.
`docs/ranking/archetypes-proposal.md` set a hard rule that no label may exceed 35% of its position
and unclassified may not exceed 10%. His objection is that positions are not equally
differentiated — tight end usage genuinely does concentrate in a way wide receiver usage does not,
so forcing every position to the same maximum share invents distinctions at some positions to
satisfy a constant. **That is a real methodological point and it should be tested, not conceded.**
The testable version: does a per-position cap produce labels that predict anything the global cap's
labels do not? If neither predicts, the cap is cosmetics either way and the honest answer is that
the taxonomy is descriptive, not predictive.

**3 · "One in football terms and one in fantasy context/terms."** The most interesting of the three
and the one most likely to be right. *Bell-cow back* and *high-volume receiver* describe how a team
uses a player; *safe floor*, *touchdown-dependent*, *volatile ceiling* describe what owning him does
to a fantasy roster. These are different axes and a single label cannot carry both. Two chips or one
chip plus one modifier is a design question — **but only after the second axis is shown to be
computable from data this project has.** Note the standing hazard: `CLAUDE.md` §7 records that four
independent measurements found no persistent per-player variance signal, and τ̂² was driven to
exactly zero. A "volatile ceiling" label would be re-deriving exactly that. **Do not build a
fantasy-context axis on a volatility claim without re-reading `docs/strategic-insights.md` §5b
first.**

**On the named reference.** "Ratcliffe" is presumed to be Matt Ratcliffe / the archetype work he is
known for; the founder cited it as doing a decent job of per-position categorisation. That is a
lead, not a source — `researcher` should establish what the actual scheme is and what it is based
on before anyone models against a half-remembered name.

**Sequencing:** ranker owns the taxonomy, researcher owns the competitive read, design owns the chip
only after both. Behind the eight items in flight. Related: threads 100 (archetype volatility
dimension) and 107 (how the label surfaces on the card).
