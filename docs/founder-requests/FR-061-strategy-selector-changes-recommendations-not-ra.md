---
ID: FR-061
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Strategy selector changes recommendations, not rankings — and bottom-up should be the default board

Founder's own words:

> "those should be our default that show - we also need to allow user to choose a specific strategy
> if not VBD (Default) that would change recommendations (if you are doing zero RB, can leave the
> rankings but need to change recommendations and explain)"

## The separation he drew, and it is the right one

**Rankings are a claim about players. Recommendations are a claim about *this pick, in this draft,
given what you are trying to do.*** Zero-RB does not make Bijan Robinson worse; it makes taking him
wrong *for you*. Conflating the two is how a strategy tool ends up lying about players.

So: **the board does not move when the strategy changes. The recommendation does, and it says why.**
That drops cleanly into FR-058's explanation panel, which already shows what displaced what and by
how much — the strategy simply becomes another named term that can fire.

## Two things that make this harder than it looks, both measured

**1 · We have already tested these strategies, and some of them lost badly.** `strategies.json`
carries simulated strategies from PR-003 — `elite_te_early` came in at **−96.1 roster points, 12 of
12 cells negative.** Offering that in a dropdown as a neutral choice, alongside VBD, would be the app
withholding what it knows at the moment the founder acts on it.

**The selector must carry each strategy's measured cost.** Not a warning box — the number, beside the
option. "Zero RB: −N points against best-available across 12 simulated cells" is honest and lets him
choose it anyway, which is his right. A bare list is not.

**2 · 26 of 27 leagues have no strategy data at all.** Only the primary export carries
`strategies.json`. So in every other league the selector has nothing to offer and nothing to price.
That is the two-track problem (design has just specified its expression) and it bounds this feature
to Westwood until the simulations are run per league.

## On "bottom-up should be the default that shows"

**Agreed as the destination. Not yet as the state.** Stating this plainly because the founder should
not discover it later:

- The bottom-up component model exists for **wide receivers only**, one pass, and it **does not beat
  consensus** — +0.048 Spearman, CI [−0.013, +0.124]. It beats the naive baselines clearly; against
  the market it is indistinguishable.
- Nothing has been run for RB, QB or TE at all.
- The board today is consensus-derived and holds no player-level opinion. Replacing it with a model
  that covers one position and has not beaten the market would be trading a known limitation for an
  unmeasured one.

**The honest sequence:** extend the component model to the remaining positions, get a holdout result
per position, then switch the default — and when it switches, the board should say which source it is
showing. `CLAUDE.md` §4's `ranking_source` enum exists for exactly this and no screen uses it yet.

**A middle step worth considering rather than waiting:** show the bottom-up projection *beside*
consensus for the positions where it exists, as a second opinion, not the default. That surfaces the
independent view — which is the point of building it — without claiming primacy it has not earned.

## Sequencing

Behind design's current specs, which are in build. Depends on FR-058's explanation object already
being built (it is), and on the strategies being available per league, which they are not.

---

## Addition, 2026-07-30: robust RB

> "we should test robust rb strategy too"

**Add robust-RB to the tested set**, alongside the strategies already simulated in PR-003
(`bpa_consensus`, `balanced`, `hero_rb`, `zero_rb`, `elite_te_early`). It is a named, conventional
strategy and it is not currently among them — so the selector would either omit it or offer it
unpriced, and unpriced is the failure mode this ticket exists to prevent.

**Define it before simulating it.** "Robust RB" is used loosely in the category — commonly, taking
running backs with the first two or three picks rather than one (hero) or none (zero). The exact
definition changes the result, so it must be committed in writing before the arm runs, not chosen
afterwards to suit the outcome. `strategist` owns that wording.

**It also fills a real gap in the existing set.** `hero_rb` and `zero_rb` sit at the extremes with
`balanced` in the middle; robust-RB is the heavy end and nothing currently occupies it. A selector
offering only the extremes would misrepresent the space of choices.

**The founder's message was truncated mid-sentence** — *"and those tests need t..."* — by what appears
to be an input glitch. **The remainder is unknown and has not been guessed at.** Whatever condition he
was about to place on these tests is not recorded here and should be asked for rather than inferred.

