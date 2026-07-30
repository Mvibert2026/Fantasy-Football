---
ID: 2026-07-30-wire-assistant-retrieval-to-docs-assistant-conte
FROM: librarian
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
`docs/assistant-context.md` already carries the content the founder asked for
(`docs/founder-requests/FR-2026-07-30-the-assistant-should-have-access-to-the-factor-t.md`) — a
"Factor test results" section with 11 entries, each carrying a number-with-interval, effective n,
and explicit scope, replacing the old verdict-word-only "Registered nulls" section. That is
librarian's remit (content shape) and it is done. **What is still open is retrieval wiring**: does
the chatbot's context-assembly step actually read this file/section today, and if it reads
`assistant-context.md` as a whole, does the new section survive whatever truncation or summarization
happens before the model sees it? Confirm the retrieval path (file path + how much of it is
included per request) and report back.

## Why
The same-day failure that prompted this FR: the assistant retrieved a statistical result unprompted
and correctly flagged that it contradicted the live recommendation, but in the same message called a
point estimate (−115.4) a "worst case" and treated 12 test cells as 12 independent scenarios (true
effective n = 4). The new section is written so a model summarizing any one entry cannot drop the
uncertainty without visibly dropping a field — but that only holds if the entry actually reaches the
model intact. If the retrieval layer truncates `assistant-context.md` or extracts only the first
sentence of a bullet, the safeguard does nothing.

## Done looks like
A reply on this thread stating: (1) which file(s) the assistant's context assembly reads today, (2)
whether `docs/assistant-context.md` in full (including the new section) is one of them, (3) if not,
what change was made (or is needed) to include it, and (4) confirmation that a multi-sentence bullet
with an inline interval/effective-n/scope is not truncated before reaching the model. No frontend
code changes for this thread if the answer to (2) is already yes — just confirm and close.
