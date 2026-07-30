---
FROM: design
TO: pm, frontend
STATUS: OPEN
DATE: 2026-08-01
AMENDS: STRATEGY-SELECTOR.md — placement only. The table, margins, season dots and both caveats are unchanged.
---

# The strategy selector collapses

## Why, and it is not space

**The argument is proportion.** Zero RB tested `NULL`. The selector reorders recommendations because he
may want that, not because it wins games — and it says so every time it fires. A control with no
measured edge should not hold permanent space on the screen he stares at for an entire draft.

My spec put it at the head of the Recommend pane. **That overstated it — my error, not a changed
requirement.**

## Collapsed is the default

    Strategy  Best player available  · the default, no reordering            change ⌄

    Strategy  Zero RB  · reordering active · tested, no measured edge        change ⌄
              ^^^^^^^ dotted underline — a chosen strategy is a supplied value

Both constraints are met **without a gesture**:

- **The collapsed row names the active strategy.** Never an anonymous icon, so a reordering he has
  forgotten about cannot hide.
- **The `NULL` disclosure does not move behind the expand gesture.** It collapses to four words that
  stay on screen permanently. Four words is a price worth paying to keep the honest claim at zero
  gestures.
- **The default strategy carries no marker**, because when nothing is being reordered there is nothing
  to disclose. The marker appears exactly when a claim is being made, which is also what makes it
  readable rather than ambient.

The dotted underline is the established *you put this here* marker from `SUPPLIED-VALUES.md` — a chosen
strategy is a supplied value and already has a vocabulary.

## The mechanism — borrowed, but not the one suggested

Neither `Expand` nor the layout modes fit. Expand is a full-bleed sheet for a view you study; the modes
are whole-screen geometry. **This is a disclosure inside one pane**, and the app already has that
pattern — Disclosure's `provenance-line` sibling, the same one *Why that matters* uses.

| | |
|---|---|
| **Collapsed** | One row, always present. Default on every load. |
| **Expand** | Click the row. **Pushes the recommendation down; does not cover it.** |
| **Collapse** | Click again, or `Esc`. |
| **Persistence** | Stays collapsed across picks and reloads. The choice persists; the panel does not reopen. |

Borrowing an in-pane disclosure over a sheet means the recommendation stays visible while he picks a
strategy — which is the thing he is choosing *about*.

## On change — the one moment the full disclosure is not optional

**Selecting a non-default strategy does not collapse the panel on click.** It stays open with the
choice confirmed, so both caveats are still on screen at the instant the choice takes effect. He
collapses it himself — the gesture he asked for — and by then he has read the thing he needed to read.
