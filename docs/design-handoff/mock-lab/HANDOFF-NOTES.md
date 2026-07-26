# Mock Lab — session handoff
**Date:** 26 July 2026 · **Screen:** Mock Lab · **Status:** specified, referenced, unbuilt

---

## What's in this export

| Path | What it is |
|---|---|
| `MOCK-LAB-SPEC.md` | The spec. 10k, structured, meant to be read end to end. |
| `spec/mocklab-tokens.json` | **Additive** tokens — and deliberately, **no new colour tokens**. Four new *patterns* instead. |
| `spec/mocklab-screen.json` | Machine-readable: entry-mode costs, state list, grid strings, five endpoints with requirements, 14 assertable checks, founder decisions, backend questions. |
| `reference/01-empty.dc.html` … `07-aggregate.dc.html` | **One working reference per state**, each opening directly in that state. `support.js` must stay beside them. |
| `reference/*.png` | 2× render of each state, matching its HTML file. |
| `HANDOFF-NOTES.md` | This file. |

Keyboard entry and the paste parser are **live** in the reference — type in `03-logging`, press
`1`–`5`, watch the tempo readout compute from real timestamps. `04-paste-reconcile` opens with a
sample block already parsed, including one misspelling and one off-board player so the fuzzy and
no-match rows are visible without typing anything.

---

## The framing I designed to

You said this is the mechanism that makes the core claim true, not an analytics screen. Taken
literally, that makes it an arithmetic problem: **30 mocks × 160 picks ≈ 4,800 entries.** Every extra
interaction per pick multiplies by 4,800.

So the design rule is: **the model's own prediction is the fastest input device.** Before each pick the
model already ranks the five players most likely to go next. Those five are a numbered list, so the
common case is **one keystroke** — press `2`, it's logged, the list re-ranks, focus never moves.
Typing is the fallback, not the default.

It also compounds in the right direction: the better calibrated the model gets, the more picks its top
five covers, and the faster logging becomes. The thing being validated makes the validation cheaper.

Three modes, because a realistic user arrives in three situations: keyboard (~2s/pick, ~5 min a mock),
paste (one action, ~1 min), grid (~4s/pick, for working from a screenshot). **Paste is the 100× win
and should be the marketed path** — it's the only mode whose cost doesn't scale with 160.

**On calibration:** I reused the existing 10-dot frequency array rather than inventing a second idiom.
Each bucket is one row — filled dots are what happened, a ▲ beneath sits where we said it would land.
Triangle left of the fill edge means under-confident, right means over-confident, under the edge means
honest. Readable without knowing the word "calibration". Brier score is kept but demoted to a "for the
record" card: it's the measure, the dots are the claim.

**On progress toward 30:** the 30 squares are secondary. The primary signal is the confidence band
narrowing, with bar lengths that are real Wilson half-widths at each sample size. No badges, streaks
or levels — the honest incentive already exists, and the screen says so outright: *"the only thing that
changes when you fill one is that the band above gets narrower."*

## The state I added

`04-paste-reconcile`, which wasn't in your list. Two reasons: paste is the mode most likely to
decide whether 30 mocks ever happen, and it's the only one that needs a reconcile design — a fuzzy
name match that silently resolves to the wrong player would corrupt the calibration data quietly,
which is the worst possible failure on this screen. Exact / fuzzy / no-match are shown per row before
commit, and an unresolvable pick commits as `player_id = unknown` with the raw text kept and is
**excluded from calibration rather than dropped** — dropping would bias the exact thing being measured.

---

## Decisions for the founder — product judgement

**1. Does offering the model's top five bias the logged data?** **No recommendation.** Presenting our
own prediction as the fastest key risks a user hammering `1` and logging what we guessed rather than
what happened. Options run from doing nothing, to hiding probabilities during entry, to a periodic
blind spot-check. This trades the entry speed the entire screen depends on against the integrity of
the only data that validates the product. That's your call, not mine — and it's the most consequential
open question in this handoff.

**2. Is 30 the right target, and is it per league or global?** **No recommendation.** A 10-team
half-PPR mock may not validate a 12-team full-PPR league. If the target is per league, the grind
multiplies by the number of leagues.

**3. Do other users' mocks count?** *Recommendation: keep the personal view primary, treat pooled as a
separate labelled number.* Pooling reaches 30 much faster and is the obvious growth loop, but it
changes the claim from "calibrated for you" to "calibrated on average".

**4. Is a partial mock worth logging?** *Recommendation: accept it, and record `rounds_logged` so
calibration can weight or filter.* Rounds 1–6 carry nearly all the availability decisions at a third
of the cost. Confirm.

## Questions for the backend engineer — facts I had to assume

1. **Can `predicted_top` / `predicted_p` be written at entry and made immutable?** The whole review
   and calibration design rests on this. If predictions can only be recomputed on read, §3 and §4 of
   the spec are both invalid and need redesigning.
2. **Is there a bulk pick endpoint, and does it return per-row resolution?** The reconcile table needs
   per-row exact / fuzzy / none, not an aggregate count.
3. **Does the player matcher exist server-side?** The reference fuzzy-matches client-side against 70
   players. Against 378 with nicknames and suffixes this should be a server endpoint.
4. **Can a pick store `player_id = unknown` plus `raw_text`?** Required for the off-board case.
5. **Is `entered_at` recorded per pick?** Without it the tempo readout and the "logged in 6m 12s"
   figure aren't real numbers and must be removed — they'd violate the traceability constraint.
6. **Are validation buckets available per-mock as well as pooled?** `06-calibration` needs per-mock;
   `07-aggregate` needs pooled.

---

## Prototype data caveat

The candidate pool in the reference is 28 players, the pre-logged mock is 10 sample picks, and the
aggregate view uses illustrative bucket counts for 7 mocks. The keyboard flow, the parser, the tempo
maths and the Wilson intervals are real and computed. Layouts, copy and null states are final; the
wiring is the work.
