---
ID: 111
FROM: backend
TO: strategist
STATUS: OPEN
OPENED: 2026-07-30
---

## Ask

Sign-off request, no urgent blocker: both results are NULL and nothing was wired into the live
board or the availability/recommendation code. Please confirm the design was sound and the NULL
verdicts are safe to close the registry entries on, or flag anything that should reopen them.

Reports: `docs/ranking/valuation-tests-35-36-precommit.md` (design, committed before either test
ran), `docs/preregistration/PR-006-global-flex-baseline.md`, `docs/preregistration/PR-008-vona-
pick-gap-awareness.md` (both `status: RUN`, results in the frontmatter). Code:
`experiments/valuation/replacement_and_vona.py`, `run.py`. Sanity checks (written before the
implementation, per the project's non-negotiable):
`tests/test_valuation_experiments_sanity.py`. Raw output:
`data/qa/valuation-tests-35-36-run-2026-07-30.log`. Both driven through `src/draft_sim.py`
**unmodified** — new board arrays / `Strategy` callables only.

12 comparisons, joint Benjamini-Hochberg (n_total=63, persistent run log). Zero survived — expected
at n=4 development seasons (2021-2024; 2025 sealed holdout untouched), where the exact sign test
floors at p=0.125 regardless of effect size.

---

### Test 1 — #35, global flex baseline: NULL

Replaced the current per-position replacement scheme (RB30/WR40/TE10/QB10, `scoring.
ReplacementLevels`, ADR-029) with ONE global replacement points figure — the 80th-ranked
flex-eligible (RB/WR/TE) player, derived not assumed (RB20+WR30+TE10 mandated + 20 flex slots =
80, the same total the current scheme already sums to) — applied identically to RB/WR/TE. Both
boards built from season S-1's real points (no player-level projection exists yet, ADR-017;
guardrails baseline #2), read through `db.CutoffEnforcedStore` so the look-ahead guard is
structurally exercised. Compared **only** on `strategy_bpa`-driven decisions/realised roster
points, never on VBD magnitude — a shifted replacement moves every player's VBD by construction.

| comparison | σ=10 | σ=20 |
|---|---|---|
| global − current | +1.7 [−67.6,+74.8] | −6.7 [−51.2,+37.8] |
| global − market (bpa_consensus) | −268.4 [−377.6,−155.1] | −271.1 [−324.1,−207.9] |
| current − market | −270.0 [−321.3,−215.6] | −264.4 [−288.6,−239.9] |

Global vs current: sign flips between σ, both CIs wide around zero, and the margin is well under
the measured simulation noise floor (sim SE ≈ 8.5 pts at 300 sims/cell, measured directly — more
simulated drafts would not narrow this; the n=4-season bootstrap is what's binding, per
`run_draft_sim.py`'s own established separation of the two noise sources). **No change made to
`scoring.ReplacementLevels`.**

Both VBD arms lose to market by ≈−270 pts at both σ — expected and not new: season S-1 persistence
is a known-weak stand-in for a real projection, and this reconfirms `strategic-insights.md` §1's
existing headline rather than adding to it.

### Test 2 — #36, VONA pick-gap awareness: NULL on outcome, decision-divergence CONFIRMED

`USER_SLOT=3`/`N_TEAMS=10` gives real intervening-pick gaps 14, 4, 14, 4, ... (3.5×, matching the
registry's "~3×" framing and the founder's actual live setup) vs. a gap-blind constant
(`N_TEAMS−1=9`, the textbook "assume one round"). VONA(player) = VBD(player) − E[VBD of best
still-available same-position player at the user's next turn], where the expected number taken
during the gap = `gap_length × share(pos)` (`live_availability.TARGET`, renormalised over
QB/RB/WR/TE — sums to exactly `N_ROUNDS−1=15`, the rounds `simulate_one` actually drafts, no
smuggled rescaling). Both arms use the SAME underlying VBD (Test 1's "current" arm) — this isolates
gap-awareness alone.

| comparison | σ=10 | σ=20 |
|---|---|---|
| aware − blind | −37.2 [−118.8,+36.0] | −2.8 [−48.0,+37.1] |
| aware − market | −376.4 [−403.9,−345.2] | −390.4 [−450.9,−352.7] |
| aware − plain BPA (vbd_current, no VONA) | −106.4 [−182.4,−54.3] | −126.0 [−214.5,−69.2] |

**Decision divergence, measured directly** (same opponent-noise seed feeds both arms' single
`effective_rank` draw, so any difference traces to the user's own pick): the two arms choose a
**different full roster in 100% of paired simulated drafts, all 8 season×σ cells** (n=299-300 per
cell). Per-season points margins bounce both directions (−154.0 to +86.7) with no consistent sign
— gap-awareness changes **which player** almost every time, without reliably changing whether the
final roster is better, at this sample size.

**A third, secondary finding not in the win condition but consistent both σ:** this VONA
formulation — either gap variant — underperforms plain best-available-by-VBD by ≈−110 to −126 pts.
CIs exclude zero at both σ, but the n=4 sign test floors at p=0.125 and neither survives BH. Read
as a caution against shipping VONA reaching under this share-based scarcity estimate, not a
confirmed loss — the per-phase-of-draft position demand this uses (a flat, round-averaged share)
is a coarser assumption than the round-varying reality (early rounds are RB/WR-heavy, late rounds
QB/DEF-heavy), and a phase-aware share estimate is the most likely next refinement if this gets
revisited. **Not wired into any live strategy or export.**

---

## What I want confirmed or overruled

1. **Is the NULL on #35 and #36's outcome question safe to close the registry on**, or does the
   design have a flaw that should reopen it (e.g., the S-1-persistence board as the valuation
   stand-in, rather than something closer to the live board's actual inputs)?
2. **Does the decision-divergence-without-outcome-improvement shape of #36's result belong in
   `strategic-insights.md` as its own line**, separate from a plain NULL — it did, and I'd like a
   second opinion on whether that framing is right or overstates what "100% divergence" means when
   the underlying VONA formula may itself be suboptimal (finding 3 above).
3. Whether the VONA-underperforms-plain-BPA caution (uncorrected, but consistent both σ) is worth
   a dedicated registry item of its own (a refined, phase-aware version) or should be left as a
   footnote here.

No response needed before either registry entry closes as measured — this thread is for review,
not a blocker.
