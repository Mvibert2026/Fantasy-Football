---
ID: FR-103
STATUS: DECIDED — DO NOT BUILD
PRIORITY: N/A
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Do not store assistant chat logs — standing constraint

Founder's own words, declining a PM proposal:

> "don't store the chat logs"

## Context

PM observed that the assistant currently persists nothing — the Worker does not log, and the
front end does not write conversations to `localStorage`. Questions the founder asks the live site
are discarded when the tab closes. PM offered three options: browser-local storage with an export
control, Worker-side storage in Cloudflare KV, or nothing.

**The founder chose nothing.** This is a decision, not a deferral.

## What this forecloses

- No `localStorage` conversation log.
- No Cloudflare KV or any other server-side transcript store.
- No analytics or telemetry capturing question text.
- No committed transcripts, which was never on the table — the repo is public.

**Do not re-propose this.** The cost is understood and accepted: the founder's real questions are the
best available signal for what the assistant must handle, and we are choosing not to collect them.
When assistant behaviour needs fixing, the input is the founder quoting a question in chat — which is
how today's intent-classification bug was found (the `"trade"` inside `"trade offs"` regex, FR-076).

Note that the 6-turn in-memory conversation history added for FR-077 is **not** affected — it lives
in the page's memory for continuity within a session and is never persisted. Keeping that is
consistent with this decision; persisting it would not be.
