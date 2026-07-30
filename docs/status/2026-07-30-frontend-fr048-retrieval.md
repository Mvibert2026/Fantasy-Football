# 2026-07-30 · frontend · FR-048 retrieval rebuild

**Role:** frontend (Sonnet, effort 4-5 per operating-model.md's "full spec port" exception —
treated this as fidelity-critical since it's the founder's own live complaint). **Cloud session**,
no worktree DB dependency; frontend-cloud-runbook.md's recipe used throughout.

## What was asked

`docs/founder-requests/FR-048-...md`'s "real bottleneck" section: the assistant's seven
regex-matched templates (`ui/assistant/templates.ts`) retrieve nothing for any question that
doesn't match one of them, so most questions reach the LLM with an empty context array and it
correctly refuses. Build real retrieval over the shipped artifacts (board rows, glossary,
strategies, league.json, nulls.json, player_descriptions.json), keeping the seven templates, and
keeping rule 3 (refuse when nothing genuinely matches — wider retrieval must not become licence to
guess). `findings.json` (the research corpus) is explicitly out of scope, dependent on this work.

## What was actually there already (read before building)

`ui/assistant/reasoning.ts` already had a two-tier matcher: exact substring matching on player
names/glossary terms/nulls keywords, and — when that found nothing — an **unconditional dump** of
every `strategies.json` comparison and every `nulls.json` finding, regardless of relevance. That
second tier was itself the rule-3 violation the ticket describes, arrived at from the opposite
direction: retrieval that always returns *something* is indistinguishable from no retrieval at
all. `ui/__tests__/reasoning-fallback.test.ts` asserted this dump behavior directly (e.g. "a truly
unrelated question still gets something rather than silently nothing" — asserting `zzz qqq xyzzy`
returns non-empty). That test's premise is exactly what this ticket asks to fix; it's deleted and
replaced by `ui/__tests__/retrieval.test.ts`.

## What was built

**`ui/assistant/retrieval.ts`** (new, ~530 lines). A BM25-style lexical scorer:
- Tokenize (lowercase, alnum runs, length >= 2), no stopword list — IDF handles common-word
  suppression on its own.
- Standard BM25 (k1=1.4, b=0.75, BM25+ idf variant, never negative).
- A non-exact match needs >= 2 independently-distinctive shared tokens (idf >= 2.0, i.e. token in
  under roughly 13% of the corpus) AND a minimum score — found empirically necessary: a single
  rare shared word (e.g. "wide" in the glossary's *confidence interval* entry, "wide means we are
  guessing," lexically matching a "wide receivers" question) is a real false-positive risk with
  plain single-token BM25.
- Confidence: `high` for an exact player-name/glossary-term substring match, or for a
  deterministically-**attached** companion doc (see below); `medium`/`low` graded by match
  strength for everything else. Never `high` on lexical accident.
- Per-artifact diversity cap (`MAX_PER_KIND = 3`, non-exact matches only): `player_descriptions.json`
  templates its prose per archetype, so ~40 tight ends share the near-identical sentence "...a
  secondary receiving option at tight end..." — without a cap, a positional question returns eight
  near-duplicate blurbs and crowds out the one `nulls.json` finding that actually answers it.
  Found empirically (debug harness against the real dataset), not assumed.
- `attachWhenKindPresent`: a small number of caveat docs (`strategies.json`'s power-floor and
  not-compositional notes) share too little vocabulary with most strategy questions to clear the
  relevance floor on their own, but are dishonest to omit whenever a strategy comparison is shown
  at all (CLAUDE.md 6.3 — a 4-season backtest cannot support significance claims). Attached
  conditionally, only when something of that artifact already cleared retrieval on lexical merit —
  never on a bare, unrelated query. This is the one place the design deliberately departs from
  "pure relevance," and it's narrow and documented.

**Corpus**: one function per artifact (`boardDocs`, `glossaryDocs`, `strategyDocs`, `leagueDocs`,
`nullsDocs`, `playerDescriptionDocs`), assembled by `buildCorpus(data, rows)`. `league.json` split
into ~6 topic docs (scoring, roster shape, replacement levels, flex split, playoff/trade/FAAB)
rather than one blob, so unrelated league questions don't always retrieve everything together.

**`player_descriptions.json` was not loaded into `Dataset` at all before this session** —
`ui/data/types.ts` (new `RawPlayerDescription`/`RawPlayerDescriptions` types),
`ui/data/load.ts` (`fetchPlayerDescriptionsOrNull`, mirrors the existing `rosters.json` optional-
artifact pattern — primary league only, absence is a real state not a load error). Test fixture
loader `ui/__tests__/helpers.ts` updated to match.

**`ui/assistant/reasoning.ts`**: the old ~170-line narrow/fallback matcher deleted outright (not
kept as commented-out dead code — a clean diff against the new file is a better audit trail than
half-dead code). `retrieveContext` is now `buildCorpus` + `retrieve`, three lines.

**A real formatting bug caught and fixed in the process**: my first draft used
`lib/format.ts#percent()` (expects a 0-1 fraction) on `adp_selected_pct`, which is already a 0-100
value (`PlayerDetail.tsx` and `Board.tsx` both handle this correctly with a local `adpPctText`
helper and say so in a comment). Would have rendered "16%" as "1600%" — caught by cross-checking
against the existing view components before shipping, not by a test. Fixed with a duplicated local
formatter (kept this module's only dependency on `ui/data/`+`ui/lib/`, not a view component).

## Verified — real questions against the real dataset

Ran via a temporary vitest harness against `loadDatasetFromDisk()` (real exports, not fixtures),
transcripts below are the actual output of `retrieveContext(data, rows, question)`. Full detail
also lives in `docs/founder-requests/FR-048-...md`'s 2026-07-30 update section.

- **"why is Josh Allen ranked 6th"** → `board.6.identity` (high) + `board.6.attribution` (high),
  both exact name matches: "Josh Allen is a QB1, tier T1, on this board at overall rank 6.
  Consensus has Josh Allen at 26, a difference of +20... Josh Allen's difference against consensus
  is entirely structural, reflecting this league's format, not an opinion about the player."
- **"what's my gap versus consensus for Bijan Robinson"** → identity + attribution (high, exact),
  his `player_descriptions.json` archetype (high, exact), plus two related `nulls.json` findings
  (medium) — QB-early and hero-RB, both lexically related through shared "consensus"/positional
  vocabulary.
- **"when should I take a tight end"** → **does not come back empty**, contrary to the ticket's own
  prediction. Real matches: `nulls.PR-003-elite-te` ("Reaching for a top tight end in the first
  three rounds cost roughly 3-5% of total roster points...") and a few TE `player_descriptions.json`
  archetype blurbs. This is honest, sourced, already-shipped content genuinely responsive to the
  question — I judged that suppressing it to match the ticket's guess would itself be the
  "confidence must be honest" failure the ticket warns against, and decided to report the real
  result rather than force emptiness. Logged in `docs/ideas-inbox.md` (decide-and-log, not asked).
  The founder's *new* finding (picks 75-113, `findings.json`) is correctly still absent — that
  corpus is explicitly out of scope for this ticket and does not exist yet.
- **"which draft strategy is best"** → 3 strategy summaries + the power-floor and
  not-compositional caveats attached, + a glossary hit. **"is our board better than consensus"** →
  the ADR-025 nulls finding, correctly, plus supporting glossary/strategy context.
- **"zzz qqq xyzzy"** → `[]`. Rule 3 holds — verified as a test assertion, not just eyeballed.

## Screenshot verification

Dev server (`npm run dev -- --port 5199 --strictPort`), Playwright against the pre-installed
Chromium (`frontend/e2e/shot-assistant-fr048.mjs`, follows the cloud-runbook's `executablePath`
pattern):

- `frontend/e2e/artifacts/fr048-00-loaded.png` — Board loads with real 510-player data; confirms
  the `Dataset`/`types.ts`/`load.ts` changes didn't break the base app.
- `frontend/e2e/artifacts/fr048-02-template-answer.png` — "what is VBD" through the assistant dock:
  export-lane template answer renders correctly with MODEL tags, confidence, provenance.
- `frontend/e2e/artifacts/fr048-03-reasoning-lane-offline.png` — "when should I take a tight end"
  correctly routes to the reasoning lane ("Matched no export template..."), retrieval runs, the
  `/__reasoning` fetch fails (no `ANTHROPIC_API_KEY` in this container — documented, pre-existing
  gap, `frontend-cloud-runbook.md` "Known gaps" #4), and the UI shows the designed "offline" notice
  rather than crashing. **This is the ceiling of what's verifiable here**: the actual LLM call
  (retrieved context -> model prose, tagged INFERENCE) cannot be exercised end-to-end in this
  container. The retrieval layer itself — the part this ticket is about — is verified at the unit
  level against the real dataset (11 tests, `ui/__tests__/retrieval.test.ts`) and via the debug
  transcripts above, which is the load-bearing evidence, not the screenshot.

## Tests / typecheck

`npx tsc -b --noEmit`: clean. `npm test`: **240 passed, 0 failed, 27 files** (baseline 236; net
+4 from replacing `reasoning-fallback.test.ts` (7 tests, deleted) with `retrieval.test.ts` (11
tests, new)). Two `board-filters.test.tsx` timeouts seen in one run were confirmed to be
concurrency flakes (two `vitest run` processes fighting for CPU in this container) — that file
passes 14/14 cleanly in isolation and was reconfirmed in the final clean run.

## Decided without asking (logged in `docs/ideas-inbox.md`)

1. "When should I take a tight end" does not come back empty (see above) — reported honestly
   rather than tuned to match the ticket's guess.
2. `player_descriptions.json` added to `Dataset`; `frontend/scripts/build-standalone-data.mjs`'s
   comment ("nothing in `ui/` reads it yet") is now stale, not fixed this pass (out of
   `ui/assistant/` scope; the standalone build already degrades gracefully since
   `data.playerDescriptions` is `undefined` there, handled the same as `null`).
3. Added the `MAX_PER_KIND` diversity cap after finding it empirically necessary against real data,
   not speculatively.

## Out of scope, confirmed still open

`findings.json` (the research corpus) does not exist. Surfacing insights at the point of decision
(the original FR-048 ask, "near relevant picks... on the draft page") is untouched — that's a
`views/DraftRoom.tsx` change and explicitly not this ticket's scope (another frontend agent is
working there this session). The system prompt in `docs/assistant-persona.md` /
`server/proxy.ts` / `worker/index.js` was not touched.

## Files touched

- `frontend/ui/assistant/retrieval.ts` (new)
- `frontend/ui/assistant/reasoning.ts` (rewritten, narrower)
- `frontend/ui/data/types.ts`, `frontend/ui/data/load.ts` (player_descriptions.json support)
- `frontend/ui/__tests__/helpers.ts` (test fixture loader, same support)
- `frontend/ui/__tests__/retrieval.test.ts` (new, 11 tests)
- `frontend/ui/__tests__/reasoning-fallback.test.ts` (deleted, superseded)
- `frontend/e2e/shot-assistant-fr048.mjs` + 4 screenshots in `frontend/e2e/artifacts/`
- `docs/founder-requests/FR-048-...md` (STATUS -> IN PROGRESS, update section)
- `docs/ideas-inbox.md` (decide-and-log entries)
