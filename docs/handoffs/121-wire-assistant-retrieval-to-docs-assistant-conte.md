---
ID: 121
FROM: pm
TO: frontend
STATUS: RESOLVED
BLOCKS: none
OPENED: 2026-07-31
---

## Ask

Verify the assistant actually retrieves `docs/assistant-context.md`. Librarian has been curating
factor-test results into it with intervals, effective n and scope inline, specifically so a
paraphrasing model cannot drop the uncertainty without visibly dropping a field.

1. Does the assistant's context pipeline read `docs/assistant-context.md` at all? Trace it --
   `frontend/ui/assistant/`, `pageContext.ts`, `frontend/server/proxy.ts`, and `worker/index.js`
   for the hosted path. Report with `file:line`.
2. Does it survive intact -- not chunked, truncated, or summarised in a way that severs an
   interval/scope from its headline number?
3. Both paths: local dev (Vite plugin) and production (Worker) are separate implementations of
   the same contract and have diverged before (`/__reasoning` was once dead in production while
   working locally).
4. Ask it a real question end to end -- something the file answers and nothing else does --
   and verify the answer carries the interval and scope, not just the verdict word.

Fix it if the fix is contained (no contract/export-shape change). If it needs one, stop and
report instead -- the contract moved twice on 2026-07-30 alone.

## Why

A curated context file the assistant cannot read is worth nothing. If retrieval silently never
reached the file, every hour librarian spends refining intervals/scope onto it is invisible to
the one consumer it exists for.

## Done looks like

A definitive yes/no on whether either path reads the file, evidence (not just an assertion) that
a real question gets a real, intact answer, and a reply on this thread with commit hash + test
count.

---
### frontend · 2026-07-31

**Finding: it did not read the file at all, on either path. Fixed, contained, no contract change.**

**1. Traced -- confirmed zero references, both paths.**
`grep -rn "assistant-context" frontend/ worker/` returned nothing before this session's fix. The
full chain: `ui/assistant/reasoning.ts:82-85`'s `retrieveContext` calls `buildCorpus` +
`retrieve`, both from `ui/assistant/retrieval.ts:577-586` (pre-fix). `buildCorpus` assembled its
corpus from `boardDocs`/`glossaryDocs`/`strategyDocs`/`leagueDocs`/`nullsDocs`/
`playerDescriptionDocs` -- six functions, none of which touched `docs/assistant-context.md`.
`frontend/scripts/sync-exports.mjs` (the only thing that copies files into `public/data/`, which
is all the browser can ever fetch) copies `data/export/*.json` only -- a different directory
entirely from `docs/`. So the file was not merely mis-parsed; it never reached `public/data/` at
all, on either path, because both `frontend/server/proxy.ts` (local) and `worker/index.js`
(hosted) are pure passthroughs -- they receive whatever `context` array the client already built
and never fetch anything themselves (`worker/index.js:177-267`, `server/proxy.ts:150-258`, byte-
identical system prompt and request/response contract, confirmed by direct read of both files).
Both paths were equally broken with respect to this file specifically -- not a local/hosted
divergence this time, a shared one.

**2. "Does it survive intact" was moot -- it never arrived.** Confirmed via a debug harness
(`retrieveContext(data, rows, 'is alpha detection happening for 2026')` against the real dataset,
`loadDatasetFromDisk()`) run before any fix: **`[]` -- empty.** That question is answered in full,
with its own stated interval and scope, by assistant-context.md's "Why alpha detection is closed
for 2026" section (2021-2025 consensus data, one season held back, ~2028 for enough seasons to
accumulate) and by nothing else in the corpus. The reasoning lane's `no_context` branch
(`reasoning.ts:116-129`) would have told the user "nothing matched," which is an honest non-answer
rather than a wrong one, but the curated content was structurally unreachable regardless.

**3. Fix (contained -- frontend-only, no `data/export/`, no `export_contract.py`, no contract
version bump):**
- `frontend/scripts/sync-exports.mjs`: new `copyAssistantContextDoc()`, copies
  `docs/assistant-context.md` -> `public/data/assistant_context.md` verbatim (raw text, not
  JSON -- it has no `contract_version`, is not part of the six-artifact per-league set, and is not
  folded into `_manifest.json`). Absence is non-fatal (logged, not thrown) since it's not a
  required artifact.
- `frontend/ui/data/load.ts`: new `Dataset.assistantContextMd: string | null`,
  `fetchAssistantContextOrNull()` (same SPA-fallback-content-type guard as `fetchJson`, resolves
  to `null` on any failure rather than throwing), fetched project-wide (not per-league -- the
  source doc has no league concept), wired into `loadDataset`.
- `frontend/ui/assistant/retrieval.ts`: new `assistantContextDocs(md)`, exported. Chunks on `##`
  headings (kept as part of the doc, so a differently-worded question can still connect a
  paragraph to its topic); a section that is itself a bulleted list of independent findings
  ("Registered nulls", "Known data traps") splits one document per bullet, since that's the file's
  own stated "one paragraph per settled decision" unit at that granularity; a prose section is kept
  whole so an interval is never severed from the sentence stating what it applies to. Strips
  markdown `**` bold markers so a chunk boundary can never leave a stray, unpaired marker in what
  the model reads as plain prose. Added to `buildCorpus`.
- `frontend/ui/__tests__/helpers.ts`: `loadDatasetFromDisk()` now reads
  `public/data/assistant_context.md` as raw text (mirrors the existing `rosters`/
  `playerDescriptions` optional-artifact pattern).
- `frontend/scripts/build-standalone-data.mjs` (the phone-friendly single-file build): **not
  touched**. It casts its embedded dataset `as unknown as Dataset`, so the new field is simply
  absent there at runtime (`undefined`), and `assistantContextDocs` treats that the same as `null`
  -- identical to the existing, already-documented `playerDescriptions` precedent in that same
  file's own doc comment.

**4. End-to-end verification, both a unit level and a real browser:**
- Unit (`ui/__tests__/retrieval.test.ts`, 6 new tests + `assistantContextDocs` exported for direct
  testing): null input -> `[]`; a prose section keeps heading + full body + the interval verbatim
  in one chunk; a bulleted section splits one doc per bullet without leaking either bullet's
  content into the other; no stray `**` survives a chunk boundary; and the real end-to-end case --
  `retrieveContext(data, rows, 'is alpha detection happening for 2026')` against the real dataset
  now returns an `assistant_context.*` item whose text contains `2021`, `2025`, and no `**`.
- **Real browser, not simulated**: `frontend/e2e/verify-assistant-context-retrieval.mjs` (new,
  committed) drives Playwright against a live dev server, opens the assistant dock, types "is
  alpha detection happening for 2026", and inspects the actual `POST /__reasoning` request body
  Chromium sent -- not a mock. Captured: **1 context item,
  `[assistant_context.why-alpha-detection-is-closed-for-2026]`, confidence medium, source
  `docs/assistant-context.md#why-alpha-detection-is-closed-for-2026`**, full text verbatim
  including "Market-consensus data...only exists for 2021-2025...one of those five seasons has to
  be held back...around 2028," no stray markdown. This is the literal request the model would
  receive in production -- the interval and scope ride along with the verdict, not just the word
  "closed." No live model response was obtainable (no `ANTHROPIC_API_KEY` in this container --
  documented, pre-existing gap, `docs/frontend-cloud-runbook.md`; UI correctly shows the designed
  "no_key" unavailable state, screenshotted). The request payload is the load-bearing evidence,
  same ceiling the FR-048 session (`docs/status/2026-07-30-frontend-fr048-retrieval.md`) hit and
  documented for the same reason.
- `data/export/*.json` and `export_contract.py`: **untouched**. `docs/assistant-context.md`
  itself: **untouched**, per the constraint (librarian is actively rewriting it) -- this session
  only reads it.

**5. Screenshots** (looked at directly, `frontend/e2e/artifacts/`):
`assistant-context-01-board-loaded.png` (board renders normally, nothing regressed),
`assistant-context-02-dock-open.png` (dock open, "Nothing asked yet"),
`assistant-context-03-after-question.png` (question asked, honest "no_key" unavailable message --
the UI-visible half of what the network capture above proves is happening underneath).

**Tests / build:** baseline (this container, fresh `npm ci`, before any change) **459 passed, 0
failed, 59 files**. After: **465 passed, 0 failed, 59 files** (+6, all in
`ui/__tests__/retrieval.test.ts`). `npx tsc -b --noEmit` clean. `npm run build` clean (`dist/`
built successfully; confirmed `dist/data/assistant_context.md` is present in the production
bundle, so the Worker's static-asset serving path carries it too -- no separate Worker change was
needed, since `worker/index.js` never builds context itself, only relays whatever the bundled
client code sends).

**Not done / out of scope:** the actual LLM prose response to a real question -- blocked on no API
key in this container, same gap every prior cloud session hit. `docs/assistant-context.md`'s
content itself was not touched. No change to `docs/assistant-persona.md` or the system prompt in
either `server/proxy.ts` or `worker/index.js`.
