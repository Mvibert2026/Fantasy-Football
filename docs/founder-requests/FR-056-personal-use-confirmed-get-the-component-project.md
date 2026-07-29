---
ID: FR-056
STATUS: NEW
PRIORITY: HIGH
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Personal use confirmed: get the component projections. Assistant LLM path is dev-server only.

Founder's own words, deciding the licensing escalation from thread 091:

> "ok, it's for personal use for me, that's fine. Just get the data."

And, on the assistant architecture:

> "the chatbot has access to an LLM via API, so the LLM should be able to answer questions (maybe
> it's an amalgamation of the research department as an agent?) I think it has API access though so
> should be able to call an LLM"

## Part 1 — Licensing: decided by the founder, with one condition he has already accepted

Thread 091 escalated that every component-projection source is personal-use-only, and that two live
conditions were already running against a public site: the board publishes FantasyPros-derived
consensus ranks under a personal-use permission, and FR-023's FFC permission is void *"if the product
ever reaches a second human."*

**His call: personal use, proceed.** That is the correct reading of what this product is — `CLAUDE.md`
§1 says single user, local only, and D-020 already closed the FantasyPros licence question on exactly
this basis.

**The one thing that makes it true is the password**, which he has said twice he intends to add. A
public URL with no auth is the single fact that turns "personal use" into "distribution", for all
three sources at once. **This is not a new ask and not a blocker — it is the condition his own
decision rests on, recorded so it is not forgotten.** Sources affected: FantasyPros, FFC, and now
Sleeper.

## Part 2 — The assistant cannot call an LLM on the hosted site. Measured, not assumed.

The founder's premise is right *locally* and wrong *in production*:

- `frontend/ui/assistant/reasoning.ts:31` posts to `ENDPOINT = '/__reasoning'`.
- That endpoint is a **dev-server plugin**: `frontend/vite.config.ts:22`, `reasoningProxy(env.ANTHROPIC_API_KEY)`.
- The same file states the design intent at lines 13-14 — Vite exposes only `VITE_`-prefixed
  variables and nothing is written into `define`, so **`ANTHROPIC_API_KEY` cannot reach the browser
  bundle.** That is correct and should not be changed; a key in a public bundle is a giveaway.
- `reasoning.ts:15` already documents the consequence: *"Unavailability is permanent, not a
  placeholder. No key, proxy stopped, and offline."*

**So on `draft.maplerock.net` the reasoning path is dead** — the same class as the Refresh button,
and for the same reason: a control whose backend only exists on a dev server.

**But there is a real path, and it is small.** The site is already a Cloudflare Worker
(`wrangler.jsonc`). A Worker can hold a secret and expose a route. Reimplementing `/__reasoning` as a
Worker function with the key in Cloudflare's secret store gives the assistant genuine API access in
production without ever putting the key in the bundle. That is the design to spec — not "ship more
files to a dumb reader," which was the PM's assumption and the founder corrected it.

## Part 3 — What to spec, in the order it should be built

1. **The Worker reasoning endpoint.** Unblocks everything else. Small.
2. **What the assistant is allowed to read.** The founder's framing — *"an amalgamation of the
   research department as an agent"* — is the right one, and it is different from a chatbot with more
   files. The discipline that must survive: the TE finding is 25% with an interval of [10.2, 49.5]
   from n=16, on an ECR proxy. **An LLM given that prose will happily say "take a tight end late."**
   Uncertainty has to be in what it reads *and* it must be required to carry it through, or the
   assistant becomes the one place in this product that overstates.
3. **`src/narrate.py`** — the deterministic facts layer, zero callers, found in the FR-043 audit — is
   what an LLM layer should sit on rather than replace.
