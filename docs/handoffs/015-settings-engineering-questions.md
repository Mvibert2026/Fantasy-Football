---
ID: 015
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: frontend build of the Settings editor
---

## Ask

Design delivered the Settings editor spec and raised three questions it cannot answer without you.
All three change the design, not just the implementation, so answer before Frontend starts.

**1. Can the backend emit five named recompute stages, or only a percentage?**
The design uses named stages ("recomputing replacement levels", "rescoring 378 players", …) because
a 60-second wait with a bare progress bar reads as a hang. Design's words: without named stages the
whole interaction "degrades to a bare percentage." Tell us which stages the recompute genuinely
passes through and whether they can be streamed. If the real pipeline has three stages or seven, say
so — the design should match the truth rather than the truth being bent to five.

**2. Does a recompute job belong to the league or to the session?**
Design asserts it must be league-scoped. Confirm this holds in the current architecture. It matters
because a session-scoped job disappears when the tab closes, which makes question 2 in the founder
decisions below unanswerable and would silently break multi-device use.

**3. How long does the server hold a computed-but-unapplied result?**
Design added a state — `04-ready-to-apply` — for the window where a recompute has finished but
nothing has been applied yet. That window needs a lifetime. Minutes? Until the session ends? Until
superseded? Whatever you choose becomes a user-visible expiry, so it needs to be a deliberate number
with a reason, not an implementation accident.

**Also confirm:** does the server already support, or can it cheaply support, a `superseded`
response for the case where a user edits again while a job is running? Design recommends
auto-restarting the job in that case and telling the user, which needs that response to exist.

## Why

Design flagged four product decisions for the founder and answered none of them silently — those are
logged as D-010 to D-013. These three are different: they are facts about the backend that Design
guessed at and needs confirmed. Guessing them into a build is how a spec and a system quietly
diverge.

Question 1 is the highest-stakes. If the stages cannot be named, the design's central answer to "what
is the user looking at for 60 seconds" collapses, and Design should be told before Frontend builds
against an assumption.

## Done looks like

Three answers, plus the `superseded` confirmation, replied in this thread. Where the answer is "not
currently, but cheaply" say what the work is. I relay anything that changes the design back to
Design, since it cannot read this repo.

### Backend · 2026-07-26

**Answer 1: Recompute pipeline stages**

Current implementation (src/make_board.py, src/export_contract.py) treats recompute as a single cohesive operation:
- Load consensus board + configuration
- Fit rank→points curves on holdout-excluded historical seasons
- Score all players under new settings
- Export JSON + CSV artifacts

**The current pipeline has NO named stages.** It's monolithic. A 60-second wait would show only a percentage bar with no intermediate labels.

**Cheaply? YES.** Decomposing into 4-5 named checkpoints costs ~2-3 hours. Likely stages:
1. "Loading configuration and board data"
2. "Fitting player valuation curves" (~30s, dominated here)  
3. "Scoring and ranking players" (~20s)
4. "Exporting data files" (~5-10s)

These reflect the actual time distribution. No API changes needed — just print/log statements at boundaries for the frontend to poll.

**Answer 2: Job scope — league or session?**

LEAGUE-SCOPED. Confirmed in export_contract.py:57-61. The `export_dir_for(league_id)` function routes output to league-specific directories, and the architecture carries `league_id` as a first-class parameter throughout. Multi-device use works — a recompute on device A materializes to disk under the league, device B reads it.

**Answer 3: Result lifetime in the "ready-to-apply" state**

Current system has NO state machine for ready-to-apply windows. Results are written directly to disk (data/export/*.json) where they persist until next recompute.

**Recommendation:** Store the result with a 5-minute TTL, auto-expire to force re-approval if user doesn't apply within that window. Rationale:
- Settings recomputes can be expensive (~60s). Leaving stale computed results dangling for hours creates confusion ("which version am I looking at?").
- 5 minutes gives the user time to review/decide while respecting that the computation is non-cheap.
- This avoids a "superseded" case — auto-expiry makes "I edited again while computing" just restart fresh.

**Superseded response:** NOT currently supported, but the comment above eliminates the need. If we add auto-restart-on-edit, just cancel the prior job (if running) and launch a new one. No `superseded` response type needed if the prior result expires anyway.

These answers assume Settings editing changes runtime parameters (scoring formula, weights, etc) but not the permanent data model. If Settings editing mutates the league configuration in data/nfl.db, scope/lifetime decisions change.
