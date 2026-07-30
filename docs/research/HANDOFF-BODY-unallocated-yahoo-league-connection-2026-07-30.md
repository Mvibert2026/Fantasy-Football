# UNALLOCATED handoff body — Yahoo/ESPN league connection, FR-062 (researcher → pm, founder)

**This is not a thread. It has no ID and must not be given one by hand.**

The researcher session that produced `docs/research/yahoo-espn-league-connection-2026-07-30.md` ran
in a cloud container with **no shell tool**, so `python tools/handoffs.py new` could not be run.
Thread IDs come only from the allocator — hand-typing or computing max+1 is what collided at ADR-048
and threads 043 / 049 / 053. The body is staged here so the next session with a shell can allocate it
in one command and paste this in.

**Allocator command:**

```
python tools/handoffs.py new --from researcher --to pm,founder \
  --subject "FR-062: the Yahoo API path is probably open; the blocking questions are a 5-minute test and a retention clause" \
  --blocks "FR-062, FR-012 (unconfirmed league settings), any league-connection feature"
```

---

## Ask

`docs/research/yahoo-espn-league-connection-2026-07-30.md` is the full audit, tagged claim by claim.
Four things need a decision or an action that a researcher may not take alone.

### 1. The founder's premise did not survive, and the good news is the useful part

He asked what happens *if* he cannot get a Yahoo API. **Nobody had established that it was closed.**
The evidence says it is not: five independent third-party SDKs, one maintained as recently as
2025-09-14, all document the same self-serve registration at `developer.yahoo.com/apps/create/` —
Installed Application, `https://localhost:<port>` redirect, Fantasy Sports → Read, Client ID and
Secret shown immediately. Concrete steps are in §2.2 of the research doc, written so he can follow
them without an agent.

**What actually needs doing is not more research. It is one attempt.** §2.4 gives the sequence, and
step 4 is the part worth insisting on: call `league/{key}/draftresults` for the **2025** season and
diff it against the project's existing hand-transcribed 2025 Westwood draft (n=160, the sole basis
for `DEFAULT_LAMBDA`). That single call exercises auth, league-key discovery and the exact endpoint a
live-draft feature would use — **and independently audits a transcription the availability model
currently depends on.** It pays for itself even if the API answer comes back no.

### 2. One genuine ambiguity, stated as a gap rather than guessed

There are two Yahoo surfaces. `[SECONDARY]` The self-serve app creator hands over credentials with no
review. `[SNIPPET]` The Yahoo Sports Developer Portal — which is where the old fantasy guide now
308-redirects — describes a gated flow requiring "information about your organization, your product,
and your use case(s)" and says Yahoo "will review your application."

`[GAP]` **Whether a brand-new self-serve app still gets Fantasy Sports scope in 2026.** I could not
close it: Yahoo hosts were not fetched per the dispatch, and Reddit and Stack Overflow — the two
places a dated first-hand report would live — were refused by the search tool. My prior is that the
portal is a commercial/partner tier and self-serve is unchanged, **but that is a prior and it is not
in the document as a finding.** The five-minute test settles it.

### 3. The clause that should shape the build is about retention, not passwords

`[VERIFIED — prior audit]` Yahoo's developer terms require deletion of Yahoo user data "not
explicitly identified as being storable indefinitely" within **24 hours**. `[SNIPPET]` the
storable-indefinitely set is reported as **GUID and authenticated token value only**.

If that reading holds, **"sync my league into `nfl.db`" is the one design the terms forbid**, and the
compliant shape is fetch-at-session-start / hold in memory / discard. That is fine for a draft-day
assistant and fatal for "the app remembers my league." **Nobody should build the first believing it
is the second.** Closing this gap means reading one document nobody on this project has ever read:
`legal.yahoo.com/us/en/yahoo/terms/product-atos/fantasysportsapi/index.html`, the fantasy-*specific*
API terms, distinct from the general developer terms the prior audit read.

### 4. Escalation, not a decision I will make: the public-hosting exposure now has a third source

`[VERIFIED — prior audit]` Yahoo's developer terms forbid using the APIs "in a product or service
that competes with products or services offered by Yahoo." Yahoo ships Draft Scout, a draft
assistant. This is a draft assistant, and `CURRENT-STATE.md` records it as **live on the open
internet by explicit founder choice**.

This is the same fault line `docs/ideas-inbox.md` already records for FFC and FantasyPros — every one
of those authorisations is scoped "private use by one person, void if the product reaches a second
human," against an app that is now publicly reachable. **Yahoo would be the third source on that
list. One ruling should cover all three**; answering it three times separately will produce three
different answers. Founder decision, arguably a lawyer's. Not an agent call and I have not made it.

---

## Two things for the founder specifically, both cheap

1. **Which platform is the third league on?** FR-062 says "all three are on Yahoo or ESPN"; FR-052
   records his own same-day correction that "**Not all three leagues are Yahoo**" and that the third
   league remains uncaptured. The answer changes everything: `[VERIFIED — prior audit]` if it is
   **Sleeper**, the API is public, documented and needs no auth at all — a strictly easier problem
   than either platform in this report. One question, and it is a prerequisite to scoping any of
   this.
2. **Twenty minutes in a free Yahoo mock draft closes the highest-value unknown in the document.**
   Join a mock, poll `league/{key}/draftresults` every ~5 seconds, log timestamps against picks. That
   converts "live draft state is probably readable, on one source" into a `[VERIFIED]` with a real
   latency number. **The live-draft claim currently rests on a single undated docstring in a single
   library, and it happens to point the direction that makes this product most interesting — which
   is exactly when to test rather than plan.**

## Answered directly, so it is not left hanging

**"Can I connect through my username and password?"** On Yahoo, technically probably — and it would
buy **nothing** OAuth does not already give, while costing a stored password, a login flow that
breaks silently on draft night, and a ToS clause that on its face covers it (`[SNIPPET]`, §5.1). On
ESPN it reportedly does not work at all: recaptcha is documented by the community as having ended
password-based access, and the working method there is copying two cookies by hand — a method
Disney's ToU §2.B.x names directly.

**The finding is not that the fallback is bad. It is that the thing he was worried about losing does
not appear to be lost.**
