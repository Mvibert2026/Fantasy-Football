# 2026-07-30 — frontend: assistant page-context (FR-076) and chat surface (FR-077)

Worktree `agent-af87493d6c285e241`. Dispatched as "FR-080" (chat surface) and "FR-081" (page
context) — neither number existed. The real, already-open requests for these two problems were
`FR-076` (assistant must see what the front end already displays) and `FR-077` (standing chat box /
answer area / 3 suggested questions), both `STATUS: NEW` on branch `claude/pm-agent-setup-gobxa0`,
not yet merged into the branch this worktree cloned from. Logged in `docs/ideas-inbox.md`; used the
real numbers throughout rather than re-allocating.

## Problem 1 (FR-076)

**Root-cause check, done before building, per the dispatch's own instruction.** Confirmed the
retrieval lane really did have no page-state input — `ui/assistant/retrieval.ts`'s corpus is board
rows, glossary, strategies, league.json, nulls.json, player_descriptions.json only, nothing about
the live draft. That's real.

**A second root cause was found by writing a test before assuming the fix would work.** The
founder's own literal question, run through `classify()`, came back `news` lane, not `reasoning`.
`ui/assistant/intent.ts`'s `NEWS_PATTERN` matched the bare word "trade" inside "trade offs" — a
regex meant to catch "player X was traded" swallowing an unrelated compound word. The news lane
then correctly says "no player named in that question," which is very plausibly what the founder
paraphrased as "the backend doesn't have that information." A third: even with the news-pattern
fixed, `defineTerm`'s `^what (?:is|are|does)...` regex had no length cap on the captured "term," so
the same sentence would have been swallowed by the glossary template's "not in the glossary"
fallback instead. Fixed both; `ui/__tests__/assistant-intent-classification.test.ts` asserts the
exact sentence classifies as `reasoning`.

**The actual fix.** `frontend/ui/assistant/pageContext.ts` (new): `buildDraftPageContextItems()`
turns values `DraftRoom.tsx` has already computed for its own render — current pick, roster needs,
whichever recommendation is on screen right now (on-clock or look-ahead, matching `lookAheadActive`
exactly), the give-up trade-off, the WHY NOT HIGHEST VBD explanation, the next-pick reference point,
position scarcity — into a bounded `ContextItem[]`, plus a `page.scope_note` item stating what was
deliberately excluded. `DraftRoom.tsx` reports this via a new `onAssistantContext` prop (additive:
one prop, one `useMemo`/`useEffect` placed after everything it depends on, no JSX touched — chosen
specifically to stay out of the column-header/rounds-display work the concurrent frontend agent
owns in the same file). `App.tsx` holds it in state, resets it on mode change and league switch,
passes it to `<Assistant>`. `ui/assistant/reasoning.ts`'s `runReasoningLane` merges it with lexical
retrieval before deciding whether there's anything to reason over.

## Problem 2 (FR-077)

The standing input was already persistent — never literally one-shot. The real gap: `ask()` took no
conversation history, so a follow-up had no memory of the turn before it. Added `ConversationTurn`
threading through `ui/assistant/index.ts` → `reasoning.ts` → `/__reasoning`, bounded (6 turns, 600
chars/answer). `frontend/server/proxy.ts` and `worker/index.js` both build alternating
user/assistant messages from history and gained a 9th binding rule (history is continuity only,
never a fact source) — added to both files and to `docs/assistant-persona.md`, the source of truth,
per its own standing instruction to keep all three in sync. Suggested questions capped 6 → 3
(`SUGGESTED_TEMPLATES`, curated for capability coverage not declaration order). Answers render
oldest-first with auto-scroll, reading as one conversation instead of a newest-first stack.

## Verification

`ANTHROPIC_API_KEY` absent in this container (re-confirmed, matches
`docs/frontend-cloud-runbook.md`), so a real hosted model call could not be exercised. Built
`frontend/e2e/verify-fr076-fr077.mjs`: seeds a real draft via localStorage (2 filler picks, user on
the clock at pick 3, this league's real `pick_sequence[0]`), intercepts `/__reasoning` at the
network layer, and echoes back exactly which context ids the real client sent — proving the request
built from a real, live `DraftRoom` render carried real page-state content. The founder's exact
question retrieved 7 page-context items; a follow-up carried 1 prior turn. Screenshots looked at
directly: `frontend/e2e/artifacts/fr076-founder-question-answered.png`,
`fr077-dock-open-3-suggestions.png`, `fr077-followup-conversation.png` — the answer text matches the
real Recommend-tab numbers rendered behind it.

## Tests

26 new: `page-context.test.ts` (10), `reasoning-page-context-and-history.test.ts` (6),
`assistant-conversation.test.tsx` (5), `assistant-intent-classification.test.ts` (3),
`draft-room-assistant-context.test.tsx` (2). `npx tsc -b --noEmit` clean. Full suite: 301 tests, 300
passed + 1 flaky timeout (`draft-room-typeahead.test.tsx`) under full-suite CPU contention,
reproduced as 25/25 passing in isolation — the same class of finding a prior session already
recorded for this exact file (`docs/status/2026-07-30-frontend-draft-middle-pane-supplied-values.md`),
not a regression from this session.

## Not done / explicitly out of scope

- `AssistantDock.tsx`'s chrome (fixed 430px width, 72vh max-height) was not touched — the founder's
  ask was about the conversation inside it, not the panel's own sizing, and touching it risked
  drifting into the concurrent frontend agent's surface. The screenshots show real text overflow at
  that fixed size with a long INFERENCE claim; worth a follow-up if the founder flags it, not
  assumed here.
- No ADR opened — this is frontend implementation, not a new architectural or statistical decision.
- Did not attempt to reconcile `docs/CURRENT-STATE.md`'s pre-existing, already-tangled
  "Last verified"/"Prior verification" label structure further down the file (several orphaned
  labels from earlier sessions) — followed the established convention at the top of the stack only,
  which is what this session's own entry needed.

Commit and test count: see final session report.
