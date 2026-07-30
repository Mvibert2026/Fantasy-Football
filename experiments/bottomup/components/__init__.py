"""Component-level bottom-up projection (FR-054).

Projects the raw quantities scoring consumes -- receptions, receiving yards,
receiving touchdowns, games -- per player, plus a per-game distribution for the
stacking yardage bonuses. A rank falls out of the projection under any ruleset;
the rank is the by-product, not the object.

Scope of the first pass: wide receivers only. See
`docs/ranking/component-model-wr-pass-1.md` for why WR and not another position.
"""
