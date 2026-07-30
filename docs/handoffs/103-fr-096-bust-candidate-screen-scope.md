---
ID: 103
FROM: backend
TO: backend
STATUS: OPEN
BLOCKS:
OPENED: 2026-07-30
---

## Ask
Build the bust-candidate screen (FR-096, mirror of FR-094's sleeper screen), read
`docs/founder-requests/FR-096-bust-candidate-flag-the-mirror-of-the-sleeper-sc.md` and the
coordinator's sequencing message first — not attempted this session per explicit instruction to
finish the sleeper screen first and hand off rather than half-do both.

Founder's words: "since we are doing sleeper, what about bust candidates, sort of the same thing
in reverse with same use cases - avoid big risks when given two similar vbd choices."

The symmetry with FR-094 breaks in three places the coordinator's message spelled out — do not
just mirror the sleeper script:

1. **Train/evaluate on EARLY-ADP players, not the round-10+ cohort `analysis/sleeper_screen.py`
   uses.** A round-2 bust costs the pick that decides a season; a round-12 miss costs nothing.
   Pick and justify an early-ADP cutoff the same way `sleeper_screen.py` §1.2 justified round-10+
   (state the reasoning, don't just reuse a round number from the sleeper pass).
2. **Set a visibly higher confidence bar for a bust flag than a sleeper flag, and state the
   number.** Both bust-flag error types are costly (false-negative: drafted the bust;
   false-positive: faded a genuinely good player), unlike a sleeper miss which costs nothing. A
   bust flag shipped at the sleeper flag's bar would make the tool worse than none.
3. **Beat two explicit baselines or the screen has measured nothing:**
   - **Regression to the mean** — "prior season was a positive outlier" as its own baseline
     feature; a bust model that's just rediscovering mean reversion isn't a finding.
   - **Injury** — `nfl.db.injuries` (79,816 rows) is known (ranker's RB/QB/TE pass-1) to capture
     26–35% of short absences but only 2.5–4.8% of absences ≥9 games — the exact absences that
     wreck a season are invisible to this table. State that limitation prominently if used; if
     injury-driven and performance-driven busts can't be separated with data on hand, scope the
     screen to performance busts only and say so plainly rather than blending them.

**Starting point already in hand, don't re-derive it:** `docs/analysis/adp-vs-production-2026-07-30.md`
already found early-round RB underperforms same-round peers at every other position by ~3×
(−54.1 VBD pts vs. −15.9 to −18.9, rounds 1–3, train seasons, era-stable, though the
unconditional position-level framing didn't clearly survive the 2024 holdout). That's a
positional bust signal already measured. **Be explicit about whether a player-level screen adds
anything over just knowing "early RB is risky"** — if the honest answer is "position is all the
signal there is," that is the reportable finding; don't manufacture a player-level result to
avoid a null.

Same guardrails as the sleeper screen: survivorship (freeze the early-ADP universe pre-season,
include every early pick who busted, not just the famous ones), look-ahead (season N−1 features
only), one holdout look (2024), BH correction across whatever feature family gets pre-registered,
Wilson intervals, output is a flag beside the ranking, never inside it.

## Why
Founder is actively engaged with this idea family (draft-day tiebreaking between similar-VBD
players) and asked for the mirror case in the same session that raised FR-094. Leaving it
unscoped risks a future session either skipping the asymmetry entirely (mirroring the sleeper
script's low evidence bar onto a high-stakes decision) or re-deriving context already gathered
here.

## Done looks like
`docs/analysis/bust-screen-<date>.md` plus reproducible script in `analysis/`, following the same
report shape as `docs/analysis/sleeper-screen-2026-07-30.md`: step 1 (base rate/severity of early
busts, already partially answered — cite it), step 2 (does any player-level feature beat the
position-only and mean-reversion baselines), explicit injury-data caveat, holdout result reported
even if it kills the finding, methodology handoff to `strategist` opened at the end.
