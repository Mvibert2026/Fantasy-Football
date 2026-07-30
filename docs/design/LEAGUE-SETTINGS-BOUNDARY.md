---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 5 (briefing §12)
DATE: 2026-07-29
COVERS: FR-040
---

# The League settings boundary

The constraint: the board ships **final points**, not the components underneath, so scoring cannot
be recomputed in the browser. The absolute rule: **the screen must not accept a setting it cannot
apply.**

## The two classes are not two sections of one form

**One is a form. The other is not.** A greyed-out scoring field is still a field — it says "this is
a thing you set here", and the honest answer is that it is not.

### Applies immediately — a form

Roster shape, team count, draft slot. Editable, applies on change, **no save button and no
confirmation**, because nothing is being submitted anywhere. Recomputable in the browser from what
the board already ships. Values the user sets carry the supplied-value treatment from
`SUPPLIED-VALUES.md` (dotted underline + marker).

### Cannot apply when hosted — not a form

Scoring. Rendered as a **read-only statement** of what the board was scored under, plus the one
route to changing it. No inputs at all.

    SCORED UNDER
    Westwood custom ruleset · half PPR
    The board ships final points, not the components underneath, so scoring
    cannot be changed here. It changes when the board is rebuilt.

## Why this does not read as a broken form

**The right-hand side never looks like a form in the first place.** It looks like the provenance
footers already all over this app — a statement of what a number is made of. That idiom exists here
and users already read it fluently. Reusing it costs nothing and carries the constraint honestly.

The worst outcome available, named in FR-040 and worth restating: a form that accepts a touchdown
value and then shows a board scored under a different one. The rule above makes that unreachable
rather than unlikely.
