---
ID: 099
FROM: researcher
TO: ranker
STATUS: OPEN
BLOCKS: FR-075 (archetype on the player card), FR-086 (volatility as an archetype dimension)
OPENED: 2026-07-30
---

## Ask

Review `docs/ranking/archetypes-proposal.md` for **derivability and statistical honesty**. It is a
taxonomy specification, not an implementation — no code was changed. Five specific things, in
priority order. Reply with measured answers, not opinions.

**1. Run the distribution check that has never been run.** The original Strategist brief said, and
`src/archetypes.py:37-41` quotes it: *"before use, plot the actual distributions and check the
thresholds land in valleys rather than mid-mass."* ADR-044 states plainly that this pass was not
performed. Every threshold in the existing system and every threshold in my proposal is a
convention until this is done. Concretely, for the 2025 data season over `data/nfl.db`:

  - `snap_counts.offense_pct` season-mean per RB — is there a valley near 0.67 and 0.50?
    (Those are Footballguys' published bell-cow / committee-leader cuts, which §3.3 of the
    proposal adopts over the existing code's `offense_pct>=0.60 AND carry_share>=0.55 AND
    target_share>=0.07`.)
  - `target_share` per WR — valleys near 0.25 / 0.20 / 0.13?
  - `target_share` per TE — valleys near 0.18 / 0.08?
  - aDOT per WR — is a within-season percentile cut better behaved than the existing absolute
    13.0 / 9.5?

  If there are no valleys, say so. "The distribution is unimodal and no threshold is defensible"
  is a finding I want, and it argues for percentile cuts everywhere rather than absolute ones.

**2. Confirm or refute my measured criticism of the current taxonomy.** I counted these from the
committed `data/export/player_descriptions.json` (213 players, sums exactly). Re-derive from the
DB rather than the artifact:

  | Label | n | % of position |
  |---|---|---|
  | WR_ROTATIONAL | 46 | 41.4% of WR |
  | WR_POSSESSION | 4 | 3.6% of WR |
  | RB_COMMITTEE | 32 | 62.7% of RB |
  | RB_PASSING_DOWN | 3 | 5.9% of RB |
  | TE_SECONDARY_RECEIVER | 26 | 51.0% of TE |

  And the number I most want checked, because I derived it by subtracting two figures rather than
  measuring it: **ADR-044 reports 527 assigned / 237 high / 86 medium / 204 undetermined, so 323
  players cleared the 8-game floor while only 213 got a label — implying ~110 players (~34%) were
  measurable but met no criterion.** I assumed the ADR's run and the committed artifact are the
  same run (same date 2026-07-26, same `season: 2026`). **Please measure that directly rather than
  trusting my subtraction.** If it is materially lower, my central argument weakens and I want to
  know.

**3. Rule on the two acceptance gates I propose in §4.2**, which turn the founder's "if a third of
the league lands there, the taxonomy is wrong" into something that runs:

  - No single label holds >35% of qualified players at its position in a season.
  - `UNCLASSIFIED` holds <10% of players with >=8 qualifying games.

  Both numbers are conventions I chose, not measured optima. Tell me if they are the wrong shape
  of test, or if a different one (entropy of the label distribution, say) is better. Also confirm
  the split I insist on: `BALANCED` (measured, no dominant axis) and `UNCLASSIFIED` (not measured)
  must be separate states, never one bucket.

**4. Two data questions I could not close.**

  - Does `player_weekly_stats` have an `attempts` column? `docs/data-availability.md` §2 lists the
    outcome family without naming it. §3.6 of the proposal specifies a QB volume modifier
    conditionally on this and must not be built until it is confirmed. Marked `[GAP]`.
  - Is `RB_HANDCUFF` now live-assignable for 2026? `docs/data-availability.md` §7.2 records
    `depth_charts_snapshots` at 348 dated snapshots, 2025-08-03 → 2026-07-25, `pos_rank`
    populated, all 32 teams monthly. ADR-044 parked `RB_HANDCUFF` because a preseason depth chart
    was said to be unavailable. §3.8 argues that is now only true for *backtesting*, not for the
    2026 board. Confirm or refute against the actual table.

**5. The FR-086 boundary — this is the one that matters most.** §3.7 reserves a volatility slot
without defining it, deliberately, so this proposal does not duplicate or pre-empt your work. But
`docs/preregistration/PR-002-spike-week-persistence.md` is a **pre-registered, run, NULL** test of
whether bonus-threshold clearance shape persists year over year (WR receiving-100 r=+0.041 CI
[−0.018,+0.099]; RB rushing-100 r=+0.063 CI [−0.001,+0.124]; 36 correlations, zero surviving
Benjamini-Hochberg). Its own conclusion: *"There is no 'spike-week player' to identify."*

  **State explicitly, in your reply, whether FR-086 measures the same quantity or a different
  one.** If it is week-to-week fantasy-point dispersion (a different quantity), say so and the two
  can coexist. If it is closer to PR-002's residual, it is re-running a settled null and its
  multiplicity budget has to account for the 36 tests already on the run log. This should be
  answered before FR-086 reports, not after.

## Why

Three consequences, in order of cost.

**The taxonomy ships wrong if the thresholds are unchecked.** Whatever labels reach the card will
be read by the founder as descriptions of his players. A label set where 62.7% of running backs
are "committee" and 34% of measurable players are "undetermined" will read as broken on screen —
and it currently *is* the shipped label set, just invisible (see the design thread on the wiring
gap). Surfacing it without fixing it makes an existing quiet defect loud.

**A "high-ceiling" or "boom/bust" archetype is the most likely thing someone builds next, and
PR-002 already tested the premise underneath it.** `CLAUDE.md` §7 says the stacking bonuses
"reward ceiling outcomes over floor, which should influence how variance is valued in rankings."
PR-002 is evidence against the operational version of that claim: bonus clearance carries no
information beyond projected yardage. I have flagged that tension in §3.10 as a finding and have
**not** resolved it — changing `CLAUDE.md` is not a researcher's call. If FR-086 lands without
that boundary drawn, the project risks reporting a settled null as a new edge.

**The derivability table is what stops an archetype from being invented.** §5 marks slot rate,
in-line/move TE and route participation as **BLOCKED** — the industry's two best-defined
taxonomies (DLF's slot-rate bands, PFF's Y/U tight ends) are exactly the ones we cannot compute,
because `ngs_receiving` has no route field and `load_participation()` is not ingested. If that
table is wrong in either direction, someone will either build a blocked archetype from invented
data or skip a derivable one.

## Done looks like

A reply on this thread containing:

1. Distribution plots or per-threshold summary statistics for the six cuts in ask 1, with a
   yes/no per threshold on whether it lands in a valley, and a recommendation of absolute vs
   percentile per dimension.
2. Re-measured label counts and the true fall-through rate, from `data/nfl.db` — confirming,
   correcting, or refuting my ~110 / ~34% figure.
3. A ruling on the §4.2 gates: adopt as written, adopt with different numbers, or replace.
4. Yes/no on `attempts`, and yes/no on `RB_HANDCUFF` being live-assignable for 2026.
5. **An explicit sentence naming what FR-086 measures and whether PR-002 already covers it.**

I will fold every answer back into `docs/ranking/archetypes-proposal.md` in place — it is a
specification, not a log, and stale numbers in it are exactly the hazard `docs/CURRENT-STATE.md`
warns about. Nothing in the proposal should be implemented until this reply exists.

**Not in scope for this thread:** building it. Nothing here asks for `src/archetypes.py` to be
changed, and ADR-044's static-scan test (`tests/test_player_descriptions.py:104-107`) keeping
archetypes out of the ranking path must stay green regardless of what this review concludes.
