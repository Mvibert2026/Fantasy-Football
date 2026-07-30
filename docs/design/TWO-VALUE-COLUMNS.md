---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 8 of 8
DATE: 2026-07-31
COVERS: founder ask "VBD probably should show me both numbers value of that position, and based on flex and other options"
---

# Two numbers where there is one

Two questions, two denominators, so **two names** — and the naming is most of the design work,
because `VBD` and `VBD (flex)` would read as one number and its footnote.

| | |
|---|---|
| **vs replacement** | Against a replacement-level player at his position. Answers *is he good at his position*. Unchanged from today's VBD. |
| **vs your options** | Against the best other use of this roster spot, flex included. Answers *is he the right pick for me*. |

## How they coexist

**Equal type size, equal weight, equal colour. Neither is styled as the real one. No third blended
figure** — the smaller number is not a correction to the larger, it answers a different question.

    #  PLAYER            POS   VS REPLACEMENT   VS YOUR OPTIONS
    1  Bijan Robinson    RB1            172.2              41.8
    2  Ja'Marr Chase     WR1            152.0              48.3
    3  Jahmyr Gibbs      RB2            137.1               9.4
    4  Puka Nacua        WR2            123.5              37.0

**Row 3 is why this is worth two columns:** strong at his position, poor use of the spot, because the
roster already has two starters there. One number cannot say that.

**Where they disagree, that disagreement is the most useful thing on the card** — the layout should
let it show rather than resolving it. This is the project's standing position that value definitions
stay separate rather than converging.

## Two constraints

- Per the drop order in `RANKINGS-PANE.md`, `vs your options` is roster-dependent and **drops before
  the name and after the dots.**
- `vs your options` has no value before a roster exists. On the Prep board with an empty roster it
  renders `—`, not a duplicate of `vs replacement`. Two identical columns would be the app implying a
  computation it has not done.

## Open question, and it is a contract question not a design one

**Is `vs your options` an export field or a client computation?** If it derives in the browser from
roster state plus the board, it can ship with what exists. If it needs a new export field it is a
contract change and belongs in a backend thread before any of this is built.
