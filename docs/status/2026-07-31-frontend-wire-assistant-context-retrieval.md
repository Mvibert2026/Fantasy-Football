# 2026-07-31 · frontend · wire assistant retrieval to docs/assistant-context.md

**Role:** frontend (Sonnet, high effort per this session's explicit instruction — a fidelity/
correctness verification task with a contained fix, not a large spec port, but treated with the
same "follow it section by section, don't skim" discipline).

## What was asked

Verify whether the assistant's context pipeline actually reads `docs/assistant-context.md` — the
file librarian curates with intervals, effective n and scope inline so a paraphrasing model can't
drop the uncertainty invisibly. Trace both paths (local dev via the Vite plugin, hosted via the
Cloudflare Worker), confirm the content survives intact if it's read at all, ask a real question
end to end, and fix it if contained (no contract/export-shape change) — otherwise stop and report.
Do not edit `docs/assistant-context.md` itself (librarian is actively rewriting it). Thread named
in the dispatch, `docs/handoffs/2026-07-30-wire-assistant-retrieval-to-docs-assistant-conte.md`,
did not exist anywhere in this worktree (confirmed by `Glob`/`grep`, and via `tools/handoffs.py
inbox frontend`, which did not list it) — opened a new one via the allocator instead of hand-typing
an ID, `docs/handoffs/121-wire-assistant-retrieval-to-docs-assistant-conte.md`.

## What was found

**It did not read the file at all, on either path.** `grep -rn "assistant-context" frontend/
worker/` returned zero hits before this session. Traced the full chain:
`ui/assistant/reasoning.ts`'s `retrieveContext` → `ui/assistant/retrieval.ts`'s `buildCorpus`,
which assembled its corpus from six functions (`boardDocs`/`glossaryDocs`/`strategyDocs`/
`leagueDocs`/`nullsDocs`/`playerDescriptionDocs`) — none touching the file. Root cause:
`scripts/sync-exports.mjs`, the only thing that copies anything into `public/data/` (all the
browser can ever fetch), copies `data/export/*.json` only, a directory entirely separate from
`docs/`. The file was never even shipped to the frontend, let alone chunked or summarized —
"does it survive intact" was moot because it never arrived. Confirmed both `frontend/server/
proxy.ts` (local) and `worker/index.js` (hosted) are pure passthroughs — byte-identical system
prompt and request/response contract, neither fetches anything itself, both just relay whatever
`context` array the already-built client code sends. So this was a shared failure across both
paths, not the kind of local/hosted divergence the dispatch's example (`/__reasoning` once dead in
production) described.

Verified with a debug harness (`retrieveContext` against the real dataset via
`loadDatasetFromDisk()`) before any fix: `is alpha detection happening for 2026` — a question the
file answers in full (2021-2025 consensus window, one season held back, ~2028 for enough data) and
nothing else in the corpus does — returned `[]`. Genuinely empty, not truncated or wrong.

## What was built (contained fix, no contract/export-shape change)

- `frontend/scripts/sync-exports.mjs`: new `copyAssistantContextDoc()` — copies
  `docs/assistant-context.md` → `public/data/assistant_context.md` verbatim, raw text (no
  `contract_version`, not part of the six-artifact per-league set, not folded into
  `_manifest.json`). Absence logged, not thrown — it's not a required artifact.
- `frontend/ui/data/load.ts`: `Dataset.assistantContextMd: string | null`,
  `fetchAssistantContextOrNull()` (same SPA-fallback content-type guard as `fetchJson`), fetched
  project-wide (the doc has no league concept), wired into `loadDataset`. `leagueIdsOf`/
  `assertLeagueMatches`'s `Omit<Dataset, ...>` type updated to exclude it from the per-league
  `league_id` check.
- `frontend/ui/assistant/retrieval.ts`: new, exported `assistantContextDocs(md)`. Chunks on `##`
  headings (kept in the doc text so a differently-phrased question still connects to its topic); a
  bulleted section ("Registered nulls", "Known data traps") splits one document per bullet — the
  file's own stated "one paragraph per settled decision" unit at that granularity; a prose section
  stays whole so an interval is never severed from the sentence naming what it's an interval on.
  `stripBoldMarkers()` removes markdown `**` so a chunk boundary can never leave a stray, unpaired
  marker in what the model reads as plain prose (found and fixed mid-session via the probe
  transcript, not assumed). Added to `buildCorpus`.
- `frontend/ui/__tests__/helpers.ts`: `loadDatasetFromDisk()` reads the new file as raw text,
  mirroring the existing `rosters`/`playerDescriptions` optional-artifact pattern.
- `frontend/scripts/build-standalone-data.mjs` (phone-friendly single-file build): **not touched**.
  Casts its embedded dataset `as unknown as Dataset`, so the new field is simply `undefined` at
  runtime there, and `assistantContextDocs` treats that the same as `null` — identical to the
  already-documented `playerDescriptions` precedent in that same file.

## Verification

**Unit** (`ui/__tests__/retrieval.test.ts`, +6 tests): null → `[]`; a prose section keeps heading +
full body + interval verbatim in one chunk; a bulleted section splits per-bullet without either
bullet leaking into the other; no stray `**` survives a chunk boundary; end-to-end —
`retrieveContext` against the real dataset now returns an `assistant_context.*` item for the alpha-
detection question containing `2021`, `2025`, and no `**`.

**Real browser, not simulated.** New `frontend/e2e/verify-assistant-context-retrieval.mjs`: drives
Playwright against a live dev server (pre-installed Chromium at
`/opt/pw-browsers/chromium`, per `docs/frontend-cloud-runbook.md` — never ran `playwright
install`), opens the assistant dock, types "is alpha detection happening for 2026", and inspects
the actual `POST /__reasoning` request body the browser sent. Result: **1 context item,
`assistant_context.why-alpha-detection-is-closed-for-2026`, confidence medium, full text including
the exact interval and scope** ("Market-consensus data...only exists for 2021-2025...one of those
five seasons has to be held back...around 2028"). This is the literal payload the model would
receive in production. No live model response was obtainable — no `ANTHROPIC_API_KEY` in this
container (documented, pre-existing gap, same one the FR-048 session
(`docs/status/2026-07-30-frontend-fr048-retrieval.md`) hit and called "the ceiling of what's
verifiable here"); the UI correctly showed the designed "no_key" unavailable state, screenshotted
(`frontend/e2e/artifacts/assistant-context-0{1,2,3}-*.png`).

**Tests / build.** Measured baseline in this container (fresh `npm ci`, before any change, via
`git stash`): **459 passed, 0 failed, 59 files**. After: **465 passed, 0 failed, 59 files** (+6, all
in `retrieval.test.ts`, no new test files). `npx tsc -b --noEmit` clean. `npm run build` clean;
confirmed `dist/data/assistant_context.md` present in the production bundle, so the Worker's static-
asset serving carries it without any Worker-side change (it never builds context itself).

## Not done / explicitly out of scope

The actual LLM prose response to a real question — blocked on the missing API key, an environment
limitation, not a code gap. `docs/assistant-context.md`'s content itself: untouched, per the
constraint. No change to `docs/assistant-persona.md` or the system prompt in either
`server/proxy.ts` or `worker/index.js` — neither needed one; the fix was entirely "does the context
array the client builds include this source," which both already-shared implementations inherit
automatically.

## A note on `docs/CURRENT-STATE.md`'s size during this session

The very first read of `docs/CURRENT-STATE.md` this session returned content describing a 2026-07-31
ranker session ("ranking version v1"), a PR-009 backend session, and several 2026-07-30 ranker
factor-batch sessions, with a system-reminder claiming 1252 total lines. Partway through this
session, the same file (re-read, and via `git show HEAD:docs/CURRENT-STATE.md`) was 724 lines,
ending at the 2026-07-30 FR-114 entry, with `git diff HEAD -- docs/CURRENT-STATE.md` empty (working
tree matches HEAD exactly) and `git log` showing HEAD unchanged at `5e82225` throughout. Per this
project's own guidance on shared-worktree artifacts ("the evidence was manufactured upstream" —
`CLAUDE.md`'s section on work appearing in a commit you didn't make), treated the git-verified,
currently-on-disk 724-line version as ground truth rather than trying to reconcile against the
earlier read, and inserted this session's entry at the top of that file's actual current stack.
Flagged here rather than silently assumed consistent; not investigated further since it did not
block this task and no destructive action (checkout/reset) was taken either way.

## Files touched

- `frontend/scripts/sync-exports.mjs`
- `frontend/ui/data/load.ts`
- `frontend/ui/assistant/retrieval.ts`
- `frontend/ui/__tests__/helpers.ts`
- `frontend/ui/__tests__/retrieval.test.ts` (+6 tests)
- `frontend/e2e/verify-assistant-context-retrieval.mjs` (new)
- `frontend/e2e/artifacts/assistant-context-0{1,2,3}-*.png` (new)
- `docs/handoffs/121-wire-assistant-retrieval-to-docs-assistant-conte.md` (new, opened + resolved
  same session)
- `docs/CURRENT-STATE.md` (new entry, in place)
