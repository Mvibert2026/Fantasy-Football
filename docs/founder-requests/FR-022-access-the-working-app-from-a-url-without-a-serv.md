---
ID: FR-022
STATUS: NEW
SOURCE: claude code session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
Access the working app from a URL without a server running on the founder machine

> "I want to make sure I can still access the working app"
>
> "what's the URL I need to use"
>
> "local host is saying it can't be reached, let's fix that problem"

Founder's own words, 2026-07-29, during the session that finished moving development off his
machine.

## Why it matters

**This is the gap that makes "moved off his machine" untrue.** Every other dependency on his laptop
was closed on 2026-07-29 — the database rebuilds from a clean clone in a cold container with no
credentials, both suites pass there, the daily capture runs on GitHub Actions, and the three
irreplaceable artifacts are committed. But the one thing the founder personally *does* with this
product — look at his draft board — still requires him to start a dev server on his own computer.

He hit this immediately: opened `localhost`, got "can't be reached," because nothing was serving it.
That is not a defect, it is the architecture. The app is a Vite dev server reading JSON from disk,
and it exists only while a terminal is running.

It gets sharper on **7 September**. If the tool is to be used in a live draft, "is a dev server
running" is a single point of failure under a clock, on the one day it cannot be debugged.

## Initial read

Three routes, in the order I would take them:

1. **A single self-contained HTML file with the data baked in.** No server, no network, no build at
   the far end — openable from a laptop or a phone, and mailable. Dispatched to frontend on
   2026-07-29. Honest limitation: it is a **snapshot**, so anything that writes or recomputes cannot
   work, and those surfaces must be absent or visibly inert rather than buttons that silently do
   nothing (the app-must-not-lie-about-itself rule applies directly).
2. **A hosted static build.** Gives a bookmarkable URL that is always current. The repo is private,
   which constrains the options — GitHub Pages on a private repo needs a paid plan, and the
   third-party static hosts would put his league data on the public internet unless access-controlled.
   **This spends money or publishes data, so it is a founder decision, not a PM one.**
3. **Keep running it locally**, and accept the laptop dependency for viewing while development stays
   in the cloud. Cheapest, and the honest fallback if 1 and 2 both disappoint.

Route 1 does not preclude route 2 — the same build feeds both.

**The draft-day question is separate and harder**, and should not be answered by whichever of the
above lands first: a live draft needs current data and working interaction, which a static snapshot
by definition does not provide. Worth deciding explicitly well before 7 September rather than
discovering it that morning. Related: `docs/reviews/fable-draft-day-premortem-2026-07-27.md`.
