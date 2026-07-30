---
ID: FR-120
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
---

## Request

Founder's own words:

> "I'm not sure all those updates made it to the front end by the way (archetype etc, th elast fiew
> you showed me) or they haven't shown up yet"

then, a few minutes later:

> "updates are now showing on front end"

**So the deploy landed.** The immediate worry resolved itself — Cloudflare's build simply lagged the
push. The request stands anyway, because of what the intervening minutes exposed.

## Why it matters

The project already has a rule that UI work is not "done" on an agent's own report — it requires a
screenshot (`CLAUDE.md`, Agent operating rules, Completion reporting). That rule closed one gap and
left a second one open, and this is it: **every screenshot so far was captured against a local dev
server.** A local screenshot proves the code renders. It says nothing about whether the change is on
the site the founder actually opens.

Between "the code is correct" and "the founder can see it" sit four independent failure points:

1. The commit reaches `main` — checkable, and checked.
2. Cloudflare's build runs and succeeds — **not checked by anything**. A failed build leaves the
   previous deployment serving, silently, with no signal in this repo.
3. The new bundle is what the site serves — **not checked by anything**.
4. The founder's browser fetches the new bundle rather than a cached one — not checked.

Every "shipped" claim made to the founder so far has really been a claim about step 1 plus a local
screenshot. That is a materially weaker statement than it sounded like, and the founder is the one
who noticed. This time the answer was a benign build lag; the same symptom is what a failed build
looks like, and nothing in the repo distinguishes the two.

## Initial read

**What was verified this session, in response to the question:**

| Check | Result |
|---|---|
| Archetype code on `main` | Yes — `e668c57`, pushed 2026-07-30 14:35Z |
| Production build succeeds from a clean tree | Yes — `tsc -b && vite build`, no errors, bundle `index-BDGFp0ip.js` 361.77 kB (the pre-archetype bundle was 322.90 kB, so the change is genuinely in it) |
| Archetype data present in the built output | Yes — 213 players in `player_descriptions.json`, eight distinct labels |
| The live site serves that bundle | **Not verifiable by any agent.** `https://fantasy-football.soft-water-e755.workers.dev` returns 401 to the password held by this session. Confirmed live by the founder in his own browser instead |

**The blocker is access.** No agent can reach the deployed site, which means no agent can honestly
say "this is live" — only "this is on `main` and it builds." Confirmation currently depends on the
founder looking, which is exactly the dependency the hosted deploy was meant to remove.

Two ways out, not equivalent:

- **Founder supplies the current site password per dispatch** (the existing pattern — passed in the
  prompt, never written to a file, since the repo is public). Restores full verification, costs
  nothing, but keeps a password moving through prompts. Note the password this session held no
  longer works, so it has changed or a `SITE_USERNAME` was added.
- **A build-status signal that needs no auth.** Cloudflare Workers Builds can report to GitHub; a
  failed or still-running build would then be visible in the repo. Catches failure point 2 only —
  it says nothing about what the site serves — but that is the point most likely to produce this
  exact complaint, and it needs no secret.

Recommend both: the build signal as the standing fix, the password for spot verification.

**Until one exists, the honest phrasing changes.** "Shipped" becomes "on `main`, builds clean,
deploy unverified." Do not report frontend work as live on the strength of a local screenshot.
