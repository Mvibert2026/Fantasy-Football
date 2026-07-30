---
ID: FR-096
STATUS: NEW
PRIORITY: MEDIUM-HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Bust-candidate flag — the mirror of the sleeper screen

Founder's own words:

> "since we are doing sleeper, what about bust candidates, sort of the same thing in reverse with
> same use cases - avoid big risks when given two similar vbd choices"

## Why it matters

The use case is exactly as he describes: a tiebreaker between near-equivalent VBD choices, sitting
beside the ranking rather than inside it. The machinery is the same as FR-094 — frozen pre-season
universe, ADP residuals, base rates, precision and recall against those base rates. Most of the
sleeper screen's code should be reusable.

## Initial read — where the symmetry breaks

Not the founder's own words — PM's read. **Two asymmetries, and the second changes the evidence
bar.**

### 1. Busts bite early; sleepers pay late

A round-12 bust costs nothing — the player is cut. A round-2 bust costs the asset you spent, and
those are the picks that decide a season. So the two flags are mirror images in *purpose* but not in
*where they apply*: the sleeper screen should be trained and evaluated on late-ADP players, the bust
screen on early ones. Running one model across the whole board would blur both.

### 2. The evidence bar is HIGHER for busts, not equal

FR-094's argument for accepting a weak sleeper signal was asymmetric cost: a false positive costs
nothing because a wrong late pick is cut. **That argument does not survive being reversed.**

| | False positive | False negative |
|---|---|---|
| **Sleeper** | Drafted a round-12 player who did nothing — cost ≈ 0 | Missed a breakout — opportunity cost |
| **Bust** | **Faded a genuinely good early player — real, immediate value lost** | Drafted the bust — high cost |

Both bust errors are expensive; only one sleeper error is. A bust flag therefore has to be *right*,
not merely directionally useful, and should carry a visibly higher confidence threshold before it is
allowed to influence a pick. Shipping it at the same bar as the sleeper flag would make the tool
actively worse than no tool.

### 3. Two nulls it must beat, or it is measuring nothing

- **Regression to the mean is the trivial bust predictor.** Players drafted high after a career year
  underperform on average because the career year was a positive outlier. Any bust model must beat
  "his prior season was an outlier" as an explicit baseline, or it has rediscovered mean reversion
  and dressed it as insight.
- **Injury is the other.** A large share of realised busts are injuries, which are substantially
  unpredictable. Without separating injury-driven busts from performance-driven ones, the screen
  will fit noise and report it as signal.

**Point 3's injury half forces a decision the project has been deferring.** `nfl.db.injuries` holds
79,816 rows and is read by no model. `ranker`'s RB/QB/TE pass-1 found the table answers the question
backwards — it captures 26–35% of short absences but only 2.5–4.8% of absences of nine games or
more, because season-ending IR drops a player off the weekly report entirely. **The absences that
actually destroy a season are precisely the ones this data cannot see.** A bust screen built on it
without saying so would be unearned confidence of the worst kind.

### Already partly measured

`docs/analysis/adp-vs-production-2026-07-30.md` found early-round RB underperforming same-round peers
at other positions by roughly 3×, surviving an era split at moderate confidence — though the broader
position-level framing did not clearly survive the 2024 holdout. That is a positional bust signal
already in hand and the obvious starting point.
