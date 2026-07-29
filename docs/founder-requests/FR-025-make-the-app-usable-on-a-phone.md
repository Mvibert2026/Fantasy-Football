---
ID: FR-025
STATUS: IN PROGRESS
SOURCE: chat session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
Make the app usable on a phone

> "I'm on my phone. Optimize all for phone viewing right now."

Founder's own words, 2026-07-29, immediately after being sent the standalone single-file board.

## Why it matters

He opened his own board on his phone and could not use it. The app was built at desktop widths — a
fixed left sidebar, a dense multi-column table, and controls sized for a mouse. On a 390px screen
the sidebar alone takes half the viewport.

This is not a polish item. **He is the only user, and a phone is where he actually is** — the
request arrived while he was away from his desk. An app that only works at his desk has the same
problem as one that only runs on his laptop, which is the dependency this whole week was spent
removing.

It also matters for **7 September**. A draft is not a desk activity for everyone, and a tool that
cannot be glanced at on a phone under a clock is a tool that will not be used under a clock.

## Initial read

Dispatched to frontend 2026-07-29 with portrait targets 390×844, 430×932 and 375×667, applied to the
**real app** rather than only the standalone file — the same components feed both, and the hosted
version at his domain is coming, so a standalone-only fix would be thrown away.

**The constraint that makes this a judgment call rather than a media query: "density as product" is a
stated architectural principle here.** The board is deliberately information-dense and the founder
values that. The failure mode to reject is a phone view that quietly drops columns so the layout
looks tidy — that is the app showing him less than it knows without saying so, the same class of
problem as a present-but-inert control. Narrow screens should be solved by making data *reachable*
(sticky first columns, horizontal scroll inside the table, disclosure) rather than absent.

Absence is only correct when a thing genuinely cannot function, which was the case for Draft and
Season in the static build and is not the case here.

**Evidence required before this closes:** real Playwright screenshots at each phone viewport, looked
at by the agent, with two specific questions answered — is a whole player row readable without
pinch-zooming, and does the page body ever scroll sideways. A passing test suite does not close this;
this project has shipped a green suite alongside a missing screen before.
