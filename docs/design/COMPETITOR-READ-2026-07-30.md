---
FROM: design
TO: pm
STATUS: OPEN
DATE: 2026-07-30
COVERS: FR-053 addendum, competitor-screenshots/README.md
---

# What the FantasyPros captures changed

Nine images, read directly. Four findings that the written record did not carry, and one correction
to my own round-one work.

## 1. Tabs or jump-to-section — the judgement asked for

**It does not generalise to the middle pane. It does answer the top-level problem.**

The distinction is not card-versus-pane, it is what the content *is*:

- **Tabs are right for mutually exclusive answers to one question.** Recommend / Scarcity / Queue /
  Insights are four ways of answering *what do I do with this pick*. You want one at a time and
  hiding the other three is correct — they would compete. A 452px pane cannot scroll usefully under a
  clock anyway; scroll position becomes state the user manages at the worst moment.
- **Jump-nav is right for one long thing with sections.** A player card is all the facts about one
  player. Nothing competes; it is simply tall. That is the right pattern for **our player detail
  sheet**, which is the same content shape.

**Where it bites is the top-level tabs, and the project has already decided this.** FR-025's phone
constraint says do not solve narrow screens by hiding data — prefer making data reachable.
Predictions replacing the board during a live draft is the same defect on a wide screen. The
principle is on the books; it was not applied here. Not respecifying the top level this round —
bigger than the pane, and engineering is mid-flight — but the direction is settled rather than open.

## 2. Their jump-nav is dressed as tabs, and that is the part not to copy

In the capture, `Latest News` is a filled white pill against five plain labels — visually identical to
an active tab. The founder's correction says it scrolls rather than filters. **The affordance is
lying about the behaviour:** it promises the other five are hidden, and they are not.

If we adopt jump-to-section, it renders as **links, not a selected control** — no pill, no active
fill, nothing implying the rest is hidden. The bar is a shortcut and should look like one.

## 3. A fourth cause for the inert-control rule — gated

Their Draft Configuration is full of controls that do not work: Custom scoring, Salary Cap, Advanced
opponent logic, all seven Position Values, Keepers. **Every one is present, greyed, carrying a
padlock.** That is the present-but-inert pattern my round-one rule bans — and here it is correct.

- **Their case: the action exists and is purchasable.** The padlock is not an apology, it is a price
  tag. Hiding it would hide a real capability and a real offer.
- **Our six: nothing is purchasable.** Export, Compare and Ask are not built; no action is being
  withheld. Refresh cannot work when hosted. No offer behind either.

**Refined rule: a control may render inert only when the action exists and the reader can obtain
it.** Then the disabled state is information about a route. Absent that, the fact goes where the
control was. **None of our six qualifies, so round one's list is unchanged** — but the rule now says
why rather than asserting it, and it holds if this ever ships a paid tier.

## 4. Positional ranks, and it is cheap

Their player-card strip is four equal-weight cells, every one a positional rank:

    ADP    ECR    Last Season    SOS
    WR3    WR3    WR1            21st

Their suggestion cards go further and show **both**: *"Overall 5 (WR 3), ADP 8"*. That is the pattern
worth taking — the rank reads fast, the raw value keeps it traceable. **Never the rank alone.**

We already have the machinery: `positionalLabel` exists and Chip's `code` variant renders it. Our
board shows raw ADP where a positional ADP rank would read faster.

## 5. One more observation, recorded not actioned

**Their "Draft Strategy" button is paywalled and opaque** — a locked yellow button in the simulator
header, no indication of what any strategy costs or whether it was ever tested. Our strategy
selector publishes measured margins including two strategies that lost badly. That contrast is the
product argument, and it is the same one as the Coach panel: **theirs is confident and unsourced,
ours is hedged and traceable.** Worth keeping deliberately.

## Correction to my own round-one work

I asserted our position palette was already the category convention, reasoning from a written record
that described Yahoo only. **The two leaders disagree** — see `POSITION-COLOUR-RESOLUTION.md`. The
decision is unchanged; the justification was wrong and is now repaired.
