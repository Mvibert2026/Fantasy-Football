---
ID: FR-077
STATUS: SHIPPED
SOURCE: chat 2026-07-30, PM session (feedback batch)
RAISED: 2026-07-30
---

## Request
Chatbot needs a standing chat box, an answer area, and at most 3 suggested questions

Founder's own words:

> "Chatbot ony allows for one question input at a time, it needs a clear standing chat box, and
> and answer area, shrink the number of suggested or relevant questions to 3 tops."

## Why it matters

Under a draft clock, re-asking a question you just discussed and getting an answer with no memory
of the last one reads as a broken chat, even where the input field itself never technically
disappeared. Six suggested-question buttons crowded the panel and diluted which three questions are
actually the useful starting points.

## Initial read

The input field (`<form className="ask">` in `ui/views/Assistant.tsx`) was already persistent --
it never disappeared after a question, so it was never literally a "one-shot field." The real gap
was structural: `ask()` took no conversation history, so every question -- including a follow-up
that referred back to what was just discussed -- reached the reasoning lane in total isolation. A
"standing chat box" that forgets everything the instant you press Ask is cosmetic, not functional;
the dispatch's own framing ("Follow-ups must carry conversation history, otherwise 'standing chat
box' is cosmetic") is the correct diagnosis. Separately, `TEMPLATES.map()` rendered all 6 export
templates as suggested-question buttons, both in the empty state and every time a question came back
unmatched -- literally twice the founder's stated ceiling.

## Resolution (2026-07-30, frontend)

**Real conversation history, not just a persistent input.** `ui/assistant/reasoning.ts` gained a
`ConversationTurn` type (`{question, answerText}`) and `runReasoningLane`/`retrieveContext` now
accept `history: ConversationTurn[]`, forwarded to `/__reasoning` as a bounded `history` array (last
6 turns, each prior answer truncated to 600 characters -- the same "keep it bounded" instruction
FR-076 states for page context, applied here to conversation history so a long-running dock session
can never grow the request without limit). `frontend/server/proxy.ts` and `worker/index.js` (which
must stay in sync per `docs/assistant-persona.md`'s own standing rule) both gained a `buildMessages`
helper that turns prior turns into alternating user/assistant messages ahead of the current turn,
so the model can resolve "what about him" -- and a **9th binding rule**, added to both files and to
`docs/assistant-persona.md` (the source of truth for all three), stating plainly that history is for
continuity only: every claim in the current answer must still trace to the current turn's retrieved
context, exactly as rules 1-4 already required, even when a prior turn discussed the same player or
number. This is not a relaxation of the safety floor -- a prior turn's own claims already passed
those rules when first produced; rule 9 just says discussing the same player twice doesn't let the
second answer skip citing its own context.

`ui/views/Assistant.tsx` now holds `history` in state, appends one turn per completed answer
(question + the answer's claims flattened to plain text, or its notice if there were no claims), and
passes it to every `ask()` call. Turns render oldest-first with the newest at the bottom (a chat
reads top-to-bottom; the previous newest-first stack read like a feed of unrelated answers, not a
conversation) and the panel auto-scrolls to the newest turn on every new answer.

**Suggested questions capped to 3.** New `SUGGESTED_TEMPLATES` in `ui/assistant/templates.ts` --
`[bestAvailable, comparePlayers, defineTerm]`, chosen to cover three distinct capabilities (board
arithmetic, a head-to-head comparison, a glossary lookup) rather than the first three declared, so
the three buttons don't all look like the same kind of question. The full `TEMPLATES` set (all 7,
after FR-076's `defineTerm` length guard) still matches a typed question exactly as before -- this
only trims what's offered unprompted, both in the empty state and in the "no template matched"
fallback.

**Screenshot verification** (`frontend/e2e/verify-fr076-fr077.mjs`, real Chromium, real DOM):
`fr077-dock-open-3-suggestions.png` shows exactly 3 buttons (`best available at pick 23`, `compare
Bijan Robinson and Deebo Samuel`, `what is VBD`) and the persistent input labeled "Ask about the
board." `fr077-followup-conversation.png` shows a real second turn whose scripted reply states "This
is turn 2 of the conversation; the prior turn's question was 'what are my likely choices and trade
offs at my next pick'" -- proving history reached the request body from a real browser interaction,
not just a unit-test mock (the unit tests in `ui/__tests__/assistant-conversation.test.tsx` cover the
same property with a mocked fetch and inspect the exact request body: `history: []` on the first
question, one real prior turn on the second).

**Tests:** 5 new (`ui/__tests__/assistant-conversation.test.tsx`) plus the 6 in
`ui/__tests__/reasoning-page-context-and-history.test.ts` that cover history bounding/truncation
(shared with FR-076's test session since both landed together). `npx tsc -b --noEmit` clean. See
FR-076's resolution for the full suite count (301 tests, 300 passed + 1 flaky-under-contention
timeout reproduced as passing in isolation).
