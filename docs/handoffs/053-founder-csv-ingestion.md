---
ID: 053
FROM: pm
TO: data-ops, strategist
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: FR-001 comparison view
---

## Ask

Ingest three founder-supplied CSVs. They are three different data types, not three copies of one, and
one of them enables something the project does not currently have.

Files land in `data/raw/founder-export/2026-07-27/`.

### 1. Underdog ADP — 407 players, real ADP with decimals

`Rank, Player, Pos, Team, ADP, Pos Rank`. Actual average draft position (`1.1`, `2.0`, `5.4`), which
is a genuine improvement on MFL's n=50 hobbyist sample.

**Carry this caveat in the schema, not just in a comment: it is best-ball ADP.** Underdog runs
best-ball, which has no waivers and no start/sit, so it systematically overvalues volatile
spike-week players and undervalues week-to-week consistency relative to redraft. It is also a
different roster shape from this league. Do not present it as redraft ADP, and do not blend it with
MFL's without recording that they measure different populations.

Store the source name on every row. `adp_source = 'underdog_bestball'`, not `adp = 1.1`.

### 2. FantasyPros ALL Rankings — 578 players, and it contains ADP implicitly

`RK, TIERS, PLAYER NAME, TEAM, POS, BYE WEEK, UPSIDE, BUST, SOS SEASON, ECR VS. ADP`.

`RK` is ECR. **`ECR VS. ADP` is populated for 566 of 579 rows**, so ADP is recoverable as
`ADP = RK − delta` (verify the sign convention against the Underdog file, where several players
overlap — that is a free cross-check).

Also here and not elsewhere: **`TIERS`** (15+ tiers, expert-assigned rather than derived), **bye
weeks**, and **strength of schedule** as a 1–5 star rating.

`UPSIDE` and `BUST` are placeholder strings ("Coach Upside rating") — the export did not include the
actual values. Ignore those two columns; do not parse them into anything.

### 3. Three-analyst rankings — 395 players, and this is the interesting one

`Player, Team, Position, Ratcliffe, Popielarz, Orginski, Consensus`. Three **individually named**
analysts plus a consensus.

**This gives the project something it has never had: a direct, external measure of expert
disagreement per player.** 265 players carry all three ranks. The spread between them is an
uncertainty signal derived from independent human judgement rather than from our own model.

The signal is real and large:

| | Spread | Ranks |
|---|---|---|
| Puka Nacua | **0** | 4, 4, 4 |
| De'Von Achane | **0** | 16, 16, 16 |
| Omarion Hampton | **14** | 12, 15, 26 |
| Saquon Barkley | **13** | 14, 27, 14 |

Three experts placing Nacua identically and disagreeing by 14 slots on Hampton is exactly the
distinction this product exists to surface. Store per-analyst ranks, not just the spread — the raw
values allow anything later; a pre-computed spread does not.

Handle missing ranks honestly: several players are ranked by only one or two analysts. `NULL`, never
zero, never imputed.

## For `strategist`

Two questions, and the first may be more valuable than anything else in these files.

**Is expert disagreement predictive of outcome variance?** If players with wide analyst spread also
show wider realised outcome variance, that is an externally-sourced uncertainty input — and it is
**testable on historical data** if analyst rankings can be obtained for prior seasons. It would let
the product say "the experts genuinely disagree about this player" as a fact rather than an
impression. Pre-register before testing.

**A caution the data already shows.** The widest disagreements are almost entirely **kickers and
defences** — Steelers DST spread 167, Cairo Santos 156, Jason Myers 155. That is not meaningful
uncertainty about football; it is three analysts not really ranking positions nobody drafts on merit.
Any disagreement metric must exclude or separately handle K and DST, or it will be dominated by noise
at positions the project has already declined to model.

## Done looks like

Three sources ingested with source attribution on every row, best-ball caveat in the schema, ADP
cross-check between files 1 and 2 reported, per-analyst ranks stored raw with honest nulls. Then a
`strategist` reply on whether the disagreement signal is worth pursuing and what would test it.
