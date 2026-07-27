---
ID: 056
FROM: pm
TO: strategist
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: any change to the need term or the run term
---

## Ask

Pre-register two founder hypotheses about the hazard model **before** we have data to test them
against. Do not fit anything. Do not estimate anything. Register the predictions, the functional
forms, the decision rules, and the multiplicity denominator — then stop.

You have no `Bash`. That is the point. This registration is credible precisely because you cannot
look first.

## The two hypotheses, in the founder's words

> "I think positional need gets stronger in the middle rounds, 4–7, where they need to close out
> their starters."

> "It should take runs into account, to a point — after 5–7 in a row, at some point usually value and
> sobriety come into play."

## H1 · The need effect is not constant across the draft

**Current model:** `N_t(p) = (share_t(p)/share_bar(p))^lambda` with a single `lambda = 0.352`
(n=160, 10 clusters, SE 0.070).

**Predicted shape:** inverted U. Weak early, strongest in the middle, weakening late.

**The mechanism, which is why this is a hypothesis and not a curve-fit.** In the first few rounds
every slot is empty, so nearly every good player fills a need — need cannot discriminate between
candidates and should barely move the hazard. In the late rounds picks are bench and upside, where
"need" is diffuse and lottery tickets dominate. In between there is a window where a manager has
three or four starters filled and a specific hole, and that hole is binding. The inverted U falls out
of roster construction; we are not fitting a bump because one appeared.

**Register a competing parameterisation, and I want your view on which is primary.** The founder
framed it as rounds 4–7. I think **round number is a proxy for the real variable, which is
starter-slot completion**, and that the proxy will not transfer:

- `H1a` — **round-bucketed.** `lambda_r` varying over buckets {1–3, 4–7, 8+}. Two extra parameters.
  Bucket boundaries are registered now and may not be moved afterwards.
- `H1b` — **completion-indexed.** `lambda` a function of unfilled starter slots on the picking team,
  not of round number. Same parameter count or fewer.

`H1b` should dominate if the mechanism is real, and the reason is practical rather than aesthetic:
the founder plays in **multiple leagues**. Round 5 of a 12-team league is a different roster state
from round 5 of a 10-team league, and a round-indexed `lambda` would need refitting per league
format while a completion-indexed one transfers. **Register both. Registering the discriminating
test between them is more valuable than either alone** — if the round version fits better than the
completion version, the roster-construction story is wrong and we have learned something real.

## H2 · The run effect saturates, and may reverse

**Current model:** `delta = 0.10`, an unvalidated prior, currently shipping flagged with an existing
kill rule (see D-004).

**Predicted shape:** concave and saturating in run length `L`, not linear. The founder's stronger
claim is that it **reverses** somewhere around `L = 5–7`, as the depleted position stops being worth
reaching for and value reasserts.

**Mechanism:** a run is driven by perceived scarcity, but each pick in the run depletes the position,
so the marginal value of the next player at that position falls relative to other positions. The
hazard should mean-revert on its own. That predicts saturation without needing anyone to be
"sober" — reversal is the stronger claim and needs the behavioural story to hold as well.

Register a saturating form — `delta * (1 - exp(-k*L))` or `delta * L / (L + L_half)` — and register
reversal as a **separate, weaker-powered hypothesis**, because they are not the same claim and
should not be allowed to pass or fail together.

**State the power problem explicitly in the registration.** Runs of `L >= 5` are uncommon and
`L >= 7` is rare. My expectation, which you should either confirm or correct: we will accumulate
enough observations to test saturation and **not** enough to test reversal, possibly for years. If
that is right, say so now, so that a null result on reversal is correctly read as *no power* rather
than *no effect*. Those are different findings and the five-way null discipline applies to results,
not only to the UI.

## The thing I want you to push back on

We deleted `NEED_ADJUSTMENT_SCALE` today (D-001) for being an unmeasured knob stacked on a measured
effect. **Both hypotheses above add parameters to the same model, on the same reasoning that would
have justified keeping it** — someone's sense that the model should behave differently.

The distinction I am relying on is that these two come with mechanisms that generate falsifiable
predictions *before* the data is seen, and the deleted knob did not. **Tell me if that distinction is
thinner than I think it is.** If registering these is a rationalisation for adding flexibility, that
is a finding, and it is more valuable than the registration.

Also: add both to the family manifest and state the resulting multiplicity denominator. Two new
hypotheses is not free.

## The blocker nobody has connected yet

**Neither hypothesis is testable on current data.** `lambda` came from n=160 across 10 clusters.
Splitting by round bucket slices that into roughly 50 per bucket with the same 10 clusters — the
per-bucket SE would be wide enough to be uninformative. Confirm or correct that arithmetic; if I am
wrong and it is testable now, that changes the priority immediately.

And a correction worth propagating: **the FFC harvest (thread 055) does not solve this.** FFC
publishes *aggregate* ADP — mean, standard deviation, high, low, times drafted. It does not publish
pick sequences. It gives us an ADP baseline and a direct read on pick-position variance, both
valuable, but it cannot tell us who picked what in what order given what they already held. Fitting a
round-varying or completion-indexed need term requires **observed per-pick sequences with roster
state**, which is exactly what **thread 054's Sleeper harvest test** would establish the
feasibility of.

That makes 054 the gating item for both hypotheses, which is a higher priority than it was assigned.

## Done looks like

A registration entry per the ADR-C convention, content-hashed, in the pre-registration store:
predicted direction and shape for each hypothesis, the exact functional forms, the bucket boundaries
for H1a, the discriminating test between H1a and H1b, the decision rule that kills each one, the
updated family manifest and denominator, and a stated power expectation for H2-reversal.

Plus a short written verdict on the pushback question above.

**File boundary:** the pre-registration store, `docs/adr/`, `docs/research/`. Do not touch `src/`,
`frontend/`, or `docs/CURRENT-STATE.md`. Estimate nothing.
