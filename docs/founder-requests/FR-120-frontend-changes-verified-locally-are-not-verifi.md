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
| The live site serves that bundle | **Yes — verified.** The founder supplied the current password (it had been rotated, which is why the session's held value 401'd). `GET /` returns 200 and its `<script src>` is `assets/index-BDGFp0ip.js`, the identical hash to the local build of `main` |

**Access was the blocker, and it is now unblocked — but the rotation is the point.** No agent could
reach the deployed site for an unknown period, and nothing surfaced that fact until the founder was
asked. Every "shipped" claim made in that window rested on a local screenshot. A rotated password
is normal and correct; an agent silently losing the ability to verify, and not noticing, is not.

**The verification method, now established and cheap.** Vite writes a content-hashed bundle name
into `index.html`. Comparing the deployed `index.html`'s script hash against a local build of the
same commit answers "is the site current" in one request, with no browser, no Playwright, and no
screenshot:

```
curl -sS -u ":$PASSWORD" https://fantasy-football.soft-water-e755.workers.dev/ \
  | grep -o -E 'assets/index-[A-Za-z0-9_-]+\.js'
# compare against: grep -o -E 'assets/index-[A-Za-z0-9_-]+\.js' frontend/dist/index.html
```

Identical hash → the site is serving this commit. Different hash → the build is lagging or failed,
and the two are distinguishable by whether the local build succeeds. **The password goes in the
shell invocation, never into a file** — the repo is public.

**Still worth building, because the above needs a secret:**

- **A build-status signal that needs no auth.** Cloudflare Workers Builds can report to GitHub; a
  failed or still-running build would then be visible in the repo to any agent, with no credential
  in the loop. It catches only the "build failed" case — it says nothing about what the site
  serves — but that is the case most likely to produce this exact complaint, and it degrades
  gracefully when the password next rotates.

**Reporting standard from here.** A frontend change is "on `main`, builds clean" until the bundle
hash matches, and "live" only after. Do not report frontend work as live on the strength of a local
screenshot.

**Until one exists, the honest phrasing changes.** "Shipped" becomes "on `main`, builds clean,
deploy unverified." Do not report frontend work as live on the strength of a local screenshot.
