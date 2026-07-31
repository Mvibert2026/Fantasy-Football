# Factor batch 5 — pass-catcher opportunity

**ranker, 2026-07-30.** Autonomous, one of four factor batches dispatched concurrently.

## What ran

17 registered tests, once each, on the `experiments/bottomup/components` walk-forward. Two blocks:
routes from `participation.offense_players` (7 target seasons) and receiving first downs from
`ff_opportunity.rec_first_down` (11). Plus one descriptive family, outside the FDR family, that
settles a contradiction between two published sources.

Pre-commitment `c857c67`, written and committed before any arm was fitted. Results
`docs/ranking/factor-batch-5-results.md` (`0c727a4`).

## Outcome

**0 of 17 survive.** 11 NULL, 5 MARGINAL, 1 MARGINAL-HARMFUL. Nothing is BH-significant at the
campaign denominator (m = 80) and nothing is significant at the batch-local m = 17 either — the
smallest p is 0.0084 against a rank-1 threshold of 0.0059, so the choice of denominator changes no
grade. The too-good trigger did not fire; the largest effect anywhere is 0.90% of the primary's
own error.

**The finding is the control arm.** `routes_known` — a bare 0/1 flag for "we have evidence he ran
routes in the last three seasons" — beats every route feature built on top of it, at every
position, by 1.06× to 19.7×. All eight route treatment cells are graded VOID — COVERAGE ARTIFACT
under the rule batch 3 wrote after batch 2's `move_known` defect. An independent instrument agrees:
E1b, the ADP-board restriction, is *worse* for every route arm at WR and TE (TE routes-per-game
**+1.59** targets MAE) while E1a is neutral — the signature of a feature whose content is "is this
an NFL pass-catcher", which helps sort a 200-player universe and hurts among the ~50 players a
draft chooses between.

## The contested result, settled

The external sweep recorded a direct contradiction: Heath at **0.79** for first-read target share
against Hoopes's measured ceiling of **0.68** for prior FPG. Measured on one population, identical
rows:

- **Hoopes replicates.** Prior FPG = **+0.668** on our data against his published 0.68, and it is
  the ceiling — all ten alternatives sit below it.
- **Heath does not.** Our first-read proxy reaches +0.637 survivor-filtered, +0.607 on the frozen
  universe. His *direction* holds (+0.006 over ordinary target share); his magnitude does not.
- **4for4's rate-stat ordering replicates exactly**, YPRR > 1D/RR > TPRR, twice, on two different
  supports.
- **Fantasy Points' own +0.004 catchable-vs-raw gap reproduces at +0.003** — the best available
  evidence that the pipeline measures what they measured.
- **The literature's survivorship premium is measured at 0.06–0.09 of correlation**, always in the
  direction that flatters the publisher.

## Data findings

- **FTN charting is in no table in `nfl.db`** — two of the four dispatched factors name it as their
  only source. Fetchable, joins to `pbp` at 99.5%, fetched 2022–2024 ad hoc and cached; nothing
  written to the shared database. Thread open to `data-ops`, including that the FTN subset is
  CC-BY-SA rather than CC-BY.
- **`pbp.first_down_pass` does not exist here**, and neither does `ydstogo`, so it cannot be
  derived. `ff_opportunity.rec_first_down` is the working source, coverage 1.0000.
- **Registry #16/#17's corrected tag is confirmed and measured.** `participation` supplies routes
  2016–2025 on every pass play. `CLAUDE.md` §5's "route participation is not in `nfl.db`" and batch
  2 §7's refusal to say anything about routes are both now out of date — with the caveat that what
  exists is a labelled proxy.

## Structural

Opened `docs/ranking/factor-campaign-manifest/`, the shared campaign family manifest, one file per
batch so four concurrent agents cannot clobber each other's registration. Batch 6 independently
built a second manifest, then migrated into this one and retired its own in place. Σ m_b = 40, so
the pre-declared floor of 80 bound for both batches.

**Every batch-5 arm made zero season-N reads**, proven structurally rather than by review:
`allow_preseason_proxy` left False, so `WalkForward.run` raises on any violation.

## Open

`strategist` (campaign denominator, the UNGRADEABLE disposition, the no-control exemption),
`data-ops` (FTN ingest), `researcher` (whether Heath's 0.79 and Hoopes's 0.68 are the same
quantity — the part our data cannot settle), `librarian` (six ledger rows). `fable` review not yet
dispatched.

Nothing ships. No sentence about routes or receiving first downs may render on any surface — the
founder's "new OC, expect routes to increase" remains unlicensed. Routes are now measurable;
measuring them did not produce a factor that earns a place.
