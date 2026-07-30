---
ID: FR-076
STATUS: SHIPPED
SOURCE: chat 2026-07-30, PM session (feedback batch)
RAISED: 2026-07-30
---

## Request
Chatbot must have access to the data the front end already displays

Founder's own words:

> "When I ask the chatbot about what my likely choices and trade offs will be at my next pick, it
> says teh back end doesn't have that information based on the pick and situation, but it's all
> being displayed on the front end, the chatbot should have access to that data to synthesize it
> intelligently"

## Why it matters

The Draft Room already computes and renders exactly the information the founder asked about --
current pick, roster needs, the recommendation and its stated reason, the trade-off against the
next-best option, the next-pick reference point, position scarcity -- and the assistant sat next
to all of it with none of it. Answering "I don't have that" while the answer is on screen is the
kind of gap that makes the assistant feel disconnected from the product it's embedded in, at
exactly the moment (mid-draft, under a clock) when that trust matters most.

## Initial read

Two root causes, not one, both confirmed by a failing test before either was fixed rather than
assumed from reading the code:

1. **The reasoning lane genuinely had no page-state input.** `ui/assistant/retrieval.ts`'s corpus
   is built only from static export artifacts (board rows, glossary, strategies, league.json,
   nulls.json, player_descriptions.json) -- never anything about the live draft (current pick,
   roster state, the recommendation, scarcity). This is the root cause named in the dispatch, and
   it was real.
2. **The founder's own literal question never reached that lane at all.** "What are my likely
   choices and trade offs at my next pick" matched two things it shouldn't have, checked in
   `classify()`/`matchTemplate()` order: the news-intent regex's bare `trade` alternative matched
   "trade offs" (meant to catch "player X was traded," not "trade-off"), routing the whole question
   to the news lane, which correctly reports "no ingested feed item mentions a player named in that
   question" -- a message a non-technical reader could easily paraphrase as "the backend doesn't
   have that information." Separately, `defineTerm`'s regex (`^what (?:is|are|does)...`) had no
   length limit on the captured "term," so the same sentence would also have been swallowed by the
   glossary template's "not in the glossary" fallback if the news-pattern fix hadn't already routed
   it away. Both are fixed; a regression test (`ui/__tests__/assistant-intent-classification.test.ts`)
   asserts the founder's exact sentence now classifies as `reasoning`, not `news` or `export`.

## Resolution (2026-07-30, frontend)

**Root cause 1 fix -- the page-context payload.** New `frontend/ui/assistant/pageContext.ts`:
`buildDraftPageContextItems()` turns values `DraftRoom.tsx` has *already computed for its own
render* (never re-derived) into a bounded set of `ContextItem`s -- current pick/round/on-clock
state, roster slot chips and unfilled starting positions, whichever recommendation is actually on
screen right now (on-the-clock or look-ahead, matching `DraftRoom`'s own `lookAheadActive` state
exactly, so the assistant can never describe a recommendation the user isn't currently looking at),
the "WHAT YOU GIVE UP" trade-off text verbatim, the "WHY NOT HIGHEST VBD" override explanation when
one fires, the next-pick CONSIDERING/LIKELY THERE reference point, and a one-line-per-position
scarcity summary. A final `page.scope_note` item always states what was deliberately excluded (the
full board, the queue, every remaining player's own odds) -- the founder's own "keep it bounded,
say what you excluded" instruction. `DraftRoom.tsx` reports this bundle via a new
`onAssistantContext` callback prop (additive: one new prop, one new `useMemo`/`useEffect` placed
after every value it depends on, no JSX touched, so column-header/rounds-display work happening
elsewhere in the same file is untouched); `App.tsx` holds it in state and passes it to
`<Assistant pageContext=.../>`, resetting to `[]` on mode change and league switch so a stale
bundle from a prior pick or a prior screen never lingers.

`ui/assistant/reasoning.ts`'s `runReasoningLane` now merges this bundle with whatever lexical
retrieval finds (page items first, de-duplicated by id) before deciding whether there is anything
to reason over -- so a question that shares no vocabulary with the static exports (the exact shape
of the founder's failing question) still has real context once a draft is active. Outside Draft
mode, or before any picks are logged, the bundle is `[]` and behavior is unchanged from before this
session: "nothing matched" is still the honest, correct answer when it's true. Every page-context
item carries `confidence: 'high'` and a `source_path` naming the real on-screen panel it mirrors
(e.g. `"live draft session (this browser): Draft Room > Recommend tab, WHAT YOU GIVE UP"`) --
Principle #1's "traces to a named field" satisfied for client session state exactly the way it is
for a `board.json:` path, just naming a screen location instead of an export field, since that is
what a client-only value can honestly point to.

**Root cause 2 fix -- classifier repair.** `ui/assistant/intent.ts`'s `NEWS_PATTERN` no longer
matches "trade" when immediately followed by "off(s)" in any spacing/hyphenation
(`trad(?:ed|e(?!\s?-?\s?offs?\b))`) -- "traded," "trade rumor," and "trade deadline" are unaffected;
only the "trade-off" compound is excluded. `ui/assistant/templates.ts`'s `defineTerm` now rejects a
captured "term" longer than 4 words (glossary terms are all short noun phrases; a longer capture is
a real question in "what ... " clothing). Both fixes are covered by
`ui/__tests__/assistant-intent-classification.test.ts`, including the founder's exact sentence.

**The persona's binding rules are unchanged and unrelaxed.** Rules 1-4 (`docs/assistant-persona.md`)
still require every claim to trace to a retrieved-context item and forbid stating a number not
verbatim in that context; page-context items are ordinary context items and are bound by the same
rules as a `board.json` line -- confirmed by the "Page awareness" section already anticipating this
exact landing ("the page narrows what is relevant, it never widens what may be claimed").

**Verified, not just tested.** `ANTHROPIC_API_KEY` is absent in this cloud container (confirmed
again this session, matching `docs/frontend-cloud-runbook.md`'s prior finding), so a real hosted
model call could not be exercised here. `frontend/e2e/verify-fr076-fr077.mjs` seeds a real draft
(2 filler picks so overall pick 3 -- this league's real `pick_sequence[0]`, `user_draft_slot` 3 --
is on the clock for the user), intercepts the `/__reasoning` POST at the network layer, and echoes
back exactly which `page.*` context ids the real client sent -- proving the real request built from
a real, live `DraftRoom` render carried real page-state content, not a mocked assumption about what
it would carry. The founder's exact question retrieved 7 items: `page.draft_state`,
`page.roster_needs`, `page.recommendation`, `page.recommendation_tradeoff`,
`page.next_pick_reference`, `page.scarcity`, `page.scope_note`. Screenshot looked at directly:
`frontend/e2e/artifacts/fr076-founder-question-answered.png` -- the assistant's answer text, laid
over the real Recommend-tab panel showing Bijan Robinson recommended with VBD 172.2, matches the
give-up and next-pick-reference numbers visible on screen behind it, word for word.

**Tests:** 10 new (`ui/__tests__/page-context.test.ts`, pure unit tests against
`buildDraftPageContextItems` using real board rows), 6 new
(`ui/__tests__/reasoning-page-context-and-history.test.ts`, the merge behavior and the `no_context`
floor), 2 new (`ui/__tests__/draft-room-assistant-context.test.tsx`, a real `DraftRoom` render
confirming `onAssistantContext` actually fires with real content), 3 new
(`ui/__tests__/assistant-intent-classification.test.ts`, the two classifier fixes). `npx tsc -b
--noEmit` clean. Full suite: 301 tests, 300 passed + 1 flaky timeout
(`draft-room-typeahead.test.tsx`) reproduced as passing (25/25) when run in isolation --
CPU-contention flakiness under the full-suite parallel run, the same class of finding
`docs/status/2026-07-30-frontend-draft-middle-pane-supplied-values.md` already recorded for this
exact file, not a regression from this session's changes.
