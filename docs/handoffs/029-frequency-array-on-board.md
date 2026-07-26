---
ID: 029
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
Add the 10-dot frequency array to the Board's inline availability badges. It is already implemented
on the player detail sheet and the Availability Explorer — this is applying an existing component in
one more place, not building something new.

## Why
The frequency array is how this product expresses probability honestly: ten dots, three filled, for a
33% chance. It is the single clearest expression of the product's whole thesis.

It is currently missing from the Board — the screen users spend nearly all their time on. So the
signature feature is inconsistently applied, and it is absent from precisely the surface where it
would do the most work. A bare "33%" on the board is the same point-estimate presentation every
competitor ships.

## Constraint
Density is the product. Ten dots inline must not push the row taller or reduce rows per screen. If it
cannot be done inside the existing row height, say so and propose an alternative rather than trading
away density — that trade is the ESPN 2025 mistake this product is explicitly organised against.

## Done looks like
Frequency arrays on Board availability badges, row height unchanged, screenshot attached showing
before and after at the same viewport. Commit hash and test count.
