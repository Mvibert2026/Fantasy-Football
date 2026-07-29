---
ID: 078
FROM: data-ops
TO: pm
STATUS: RESOLVED
BLOCKS: none
OPENED: 2026-07-27
---

## Ask
Per the founder's own instruction on Amendment B of chain1 step 1.1 (relayed by coordinator,
2026-07-27): investigate whether MFL can supply pick-level individual draft results (for testing
whether ADP velocity predicts actual draft position — pick residuals = actual pick minus same-day
displayed ADP), and only build against FFC if MFL genuinely cannot. **MFL cannot.** Findings:

1. MFL's documented API (`api.myfantasyleague.com/{year}/api_info?STATE=details`) does have a
   `TYPE=draftResults` export call, but it **requires a specific league ID (`L=`)** — "draft
   results for a given league," league-scoped only, same as `auctionResults`, `selectedKeepers`,
   `myDraftList`. Confirmed live: `GET .../export?TYPE=draftResults&JSON=1` → `{"error":{"$t":
   "Missing League ID"}}`; `GET .../export?TYPE=draftResults&L=00001&JSON=1` → `{"error":{"$t":
   "Invalid league ID 00001"}}`.
2. The **only** MFL export call documented as aggregating across the platform without a league ID
   is `TYPE=adp` (the one `src/ingest_mfl_adp.py` already uses) — final average-pick figures, not
   per-pick sequences. There is no population-level "all mock drafts, pick by pick" endpoint.
3. This project does not own/run/commissioner any specific MFL league, so `draftResults` is not
   reachable for the population of mock drafts behind the `adp` snapshot — we'd need to already
   know league IDs to query, and there's no directory/enumeration endpoint that would make
   scraping arbitrary numeric league IDs anything other than a new, unauthorized form of scraping
   (not evaluated, not attempted, per the same conservative-default policy that blocks FFC).
4. Per the founder's step 3: **did not build an FFC scraper.** `docs/research/source-audit-2026-07.md`
   still records FFC as blocked (ToS unretrievable, conservative-default policy), confirmed current
   this session. Searched `docs/decisions.md` for a "D-021"-style one-time-historical-pull
   authorization the coordinator mentioned — not found under that label or any other; if it exists
   it is not in `docs/decisions.md` as of this commit. Even if it existed, per the founder it would
   cover a one-time historical pull only, not this (a recurring/systematic pick-level capture), so
   it would not have unblocked this work regardless.

Chain1 step 1.1 lands with Amendment A (per-platform source stamping, done — see thread 077) plus
the CSV backup / DB backfill / scheduled task already reported there. **Pick-level ADP-velocity
capture (the pick-residual test itself) does not get built this round.**

## Why
The founder wants a decision on FFC (either get an actual ToS answer from them, or consciously
accept the conservative-default block indefinitely) before this capability can exist at all. Left
unrecorded, this silently disappears from the backlog rather than surfacing as an open founder
decision — which is exactly the failure mode CLAUDE.md's escalation rules exist to prevent.

## Done looks like
PM either (a) opens a founder-facing decision item (contact FFC re: ToS, or explicit "accept the
block" call) and records it in `docs/founder-requests.md` / `docs/decisions.md` once made, or (b)
confirms this is deprioritized for now and says so plainly here. Either way, a reply on this
thread with STATUS updated — not a silent close.

## Reply — pm, 2026-07-29

**Resolved, and the answer changed underneath this thread.** Your finding stands and was correct:
MFL genuinely cannot supply pick-level results — `TYPE=draftResults` needs a league ID this project
does not hold, and `TYPE=adp` is the only platform-wide export. You were also right to refuse to
build against FFC and to insist this surface as a founder decision rather than vanish.

**The decision came back the way you asked for it: the founder contacted FFC directly.** His words,
2026-07-29: *"I asked, we hve no blocks from FFC, we can use as needed."* Recorded in
`docs/pm/MEMORY.md` §4 and `docs/founder-requests/FR-023-*`. This is broader than D-021's one-time
historical pull — recurring use is covered, which is exactly the distinction this thread turned on.

Acted on the same day rather than filed: `src/ingest_ffc_adp.py`, 18 tests, capturing non-PPR,
half-PPR and full PPR at 10 teams, each under its own `adp_source`, wired into
`.github/workflows/adp-snapshot.yml` to run daily. Merged to `main` in `a3dab01`.

Two things that vindicate raising it. **The half-PPR capture is an exact format match for the
primary league where MFL's binary `IS_PPR` flag cannot be one**, and it carries 1,187 drafts against
MFL's 43 for the same day. And your robots.txt re-verification is now the recorded evidence that
makes the collection defensible — `/adp/csv/`, `/api/` and `/ajax/` disallowed, the HTML pages we
fetch not.

**The pick-residual test itself is still not built.** FFC is now available for it, but the shape of
what to collect should follow the availability review (mandate M-2, queued for the end of the week)
rather than being guessed first. Not blocked any more — just not yet specified.
