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

**The truncated remainder, supplied 2026-07-30:**

> "each strategy tested across all league types and basic presets - then they can be loaded and no
> math needs to happen, also you'll need to define the rules to each strategy tested somewhere (like
> how long till you take your first RB in zero RB, do you take a TE or no judgment?) within it is it
> BPA? VBD? etc. what is balanced?"

### Two requirements, and the second is the more important

**1 · Pre-compute across every league type and preset; the app loads, it does not calculate.**

Right now `strategies.json` exists for **primary only** — one league, one roster shape. The founder
wants the full matrix so a selector works in any league he opens, with no runtime cost.

Scope it honestly before building: 27 league configs × 6+ strategies × the sigma sweep {5,10,20} ×
simulated seasons. That is a large grid and the availability sweep already showed this class of
simulation is expensive — a single 10-slot availability run took hours. **Measure one cell first and
report the total**, rather than starting a job nobody has costed. If the full matrix is impractical,
the honest fallback is the presets the founder actually uses, named as such.

**2 · Write down what each strategy actually is. This is the real gap and he is right that it is
missing.**

His questions are exactly the ambiguities: *how long until the first RB in zero-RB? Is a TE allowed,
or is that unconstrained? Within the constraint, is the pick BPA or VBD? What does "balanced" even
mean?*

**The rules do exist — in code, in `src/draft_sim.py` (`strategy_bpa`, `strategy_hero_rb`,
`strategy_zero_rb`, `_positional_bias`) — and nowhere a human can read, check or disagree with
them.** That is the defect. A strategy whose definition lives only in a function body cannot be
audited, cannot be shown on screen beside its measured cost, and cannot be compared to what the
category means by the same word.

**Every tested strategy needs a written definition covering, at minimum:**

| | |
|---|---|
| **The constraint** | What it forbids or forces, and until when — "no RB before round N" |
| **The within-constraint rule** | Once the constraint is satisfied or inactive, is it BPA, VBD, or something else? |
| **Unconstrained positions** | Explicitly stated. Is TE free, or does the strategy have a view? |
| **Termination** | When does the constraint stop applying? |
| **Source** | Is this the category's conventional meaning, or this project's own? Say which. |

**`balanced` is the one to define first**, because it is the least standard word in the set and the
most likely to be doing something arbitrary that nobody has looked at.

Owner: `strategist` writes the definitions, since it also owns the pre-registration that tests them;
`ranker` or `backend` runs the matrix. **Definitions committed before the runs**, or the results
describe rules nobody agreed to.

---

## Scope narrowed by the founder, 2026-07-30

> "at the beginning I likely just need westwood, ethans league and a to be named espn league, so we
> can wait on others, but having the math done on those would be good for me to be able to choose."

**Three leagues, not 27.** That turns an uncosted matrix into a tractable job: Westwood (primary),
Ethan's Expert League, and the ESPN league whose settings are still uncaptured (FR-052 — its point
values were never supplied, so it cannot be simulated until they are).

So realistically **two now, one when its settings land**. Run those; leave the preset matrix until
someone asks for it. The purpose is stated plainly in his words — *"good for me to be able to
choose"* — which is a selector with real numbers beside each option, not a research programme.

