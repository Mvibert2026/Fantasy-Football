---
FROM: design
TO: pm, frontend, whoever specifies the injury source
STATUS: OPEN — spec ahead of data, as instructed
DATE: 2026-08-01
COVERS: founder ask "injury status should show in lists and in player card… if no injury, show healthy"
---

# Availability status — four states, and healthy is the hard one

## The rule that encodes the dangerous half of the ask

> **Healthy is a positive claim and requires positive evidence. It renders only from a source that
> affirmatively lists the player as available — never from the absence of an injury record.**

Today **every one of the 510 players is in the fourth state, not the first.** `board.json` carries no
injury status, `roster_status` is a contract field only, and `suspension_flag` is `False` for all of
them — **a uniform `False` across every row is the signature of a field nobody has populated, not a
league with no suspensions.** Reading it as evidence of health is exactly the failure this rule makes
unreachable.

## The four states

| State | Renders as | Type | The claim, and what it requires |
|---|---|---|---|
| **available** | hollow dot + `healthy`, no colour, no box | 11px / 400 | A source affirmatively lists him as available. **No added weight** — the common state must cost almost nothing. |
| **a named status** | filled dot + boxed `OUT` / `IR` / `PUP` / `SUS` / `Q` / `D` | **10px / 600** | The source names a specific state. Q and D take `--down`; OUT, IR, PUP, suspension take `--live`. **The only semibold state.** |
| **not tracked** | dashed box + `not tracked` | 11px / 400 | No source is wired. True of all 510 today, so it is a **column-header fact stated once** — not 510 identical row markers. Deliberately quiet: a fact about the app, not about him. |
| **no record** | `—` | 11px / 400 | Source is live and covers this league but says nothing about him. Genuine per-row information, **and still not health.** |

**Weight is per state, not per column.** Only the named status is semibold — that is what makes it the
loudest thing in the strip. Applying the floor to all four would flatten the whole point of the
treatment, which is that visual weight tracks how much the state should change the pick.

### Why four and not three

**`not tracked` and `no record` look identical on screen and are completely different claims.**

*Not tracked* is a fact about the app — true of every player at once, so it belongs in the header.
*No record* is a fact about the player — the source is live and covers this league but has nothing for
him.

Collapsing them is how "show healthy" ships as a lie: **the app would report 510 healthy players on a
day it knows nothing about any of them.**

## In lists — not a column, so not in the drop order

You asked where status enters `RANKINGS-PANE.md`'s drop order. **It does not, because making it a
column is the wrong shape.** A column would compete with the name for width at exactly the widths
where width is scarce, and a fact that can invalidate a pick must not be droppable.

**It rides the name cell as a marker**: zero column width, undroppable, physically attached to the
identity it qualifies.

    PLAYER                          POS   VBD
    status not tracked   ← header carries the tracking state

    1  Bijan Robinson               RB1   172.2
    3  Jahmyr Gibbs  Q              RB2   137.1
    5  Christian McCaffrey  IR      RB3   116.6

**Only exceptions render a marker. Healthy renders nothing in a list.** 460 green dots is noise, and
it would make the one player who is actually `OUT` harder to see rather than easier — the opposite of
"easy to see at a glance."

Silence is only safe because **the header states the tracking state** — the same rule as ADP's
`mfl · 144/511`: one fact about a whole column belongs once in the header, not 511 times. Today it
reads `status not tracked` and no row implies anything. When a source lands it reads
`status live · 3 flagged`, and an unmarked row means checked-and-clear.

## On the card — always, in the identity strip, weight by consequence

**Healthy is a word and a hollow dot: no box, no colour, no added weight.** The box and the hue arrive
with the consequence, so the loudest thing in the strip is always the state that most changes the
pick. He gets the affirmative "healthy" he asked for without it shouting on the majority of cards.

Status takes the identity strip; **archetype moves to the disclosed section** — see
`PLAYER-PROFILE-AMENDMENT-ARCHETYPE.md`.

## A carve-out stated explicitly rather than quietly

`POSITION-COLOUR-RESOLUTION.md` restricts the semantic accents to signed deltas. **Status hue is a
third family and needs its own permission:** it appears *only* on a status glyph, always adjacent to
the word naming it, and **never on a number.** It cannot be mistaken for a delta because it never sits
where one goes.

**The named status** takes the same 10px semibold `--f-ui` floor as a position code, for the same
reason — the word is the non-hue channel and it is the state that carries consequence. The other three
states stay 11px regular, deliberately.

**Healthy takes no colour at all**, which keeps `--acc` meaning exactly one thing.

## The question that decides whether this is buildable as asked

**Will the source affirmatively list available players, or only exceptions?**

If it publishes exceptions only, **the healthy state is unrenderable** and the founder's "show healthy"
cannot be honoured as worded. The honest substitute is *"checked, nothing flagged"* — a weaker claim,
and he should be told that before the source is picked rather than after.
