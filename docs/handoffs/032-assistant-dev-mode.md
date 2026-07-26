---
ID: 032
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Wire a working LLM assistant now, cheaply. Founder's call: get something usable for diagnosing the
product, defer the proper design (thread 033 holds that and is parked).

**Build:**
- Anthropic API, **Haiku** tier. Key from env, never committed.
- Gated behind a dev flag, default off. Founder tool, not a shipped feature.
- Give it the export artifacts from `data/export/<league_id>/` — `board.json`, `availability.json`,
  `league.json`, `nulls.json`, `glossary.json`, `opponents.json`, `strategies.json`. Whole files if
  they fit the context; a simple lookup tool per artifact if they do not. `board.json` is ~672 KB, so
  it almost certainly does not — start with a lookup-by-player-name tool over it and pass the smaller
  files whole.
- Conversational restrictions off. No canned refusals, no hedging templates, no topic limits. It
  should answer directly about internals, data, and failures.

**Keep one rule, and only one:** *when it states a number, it names the field and file it came from.*

Nothing else. No elaborate tool taxonomy, no evaluation harness, no ADR. Those live in 033 for
whenever the real design happens.

## Why that one rule survives the shortcut

It is close to free — a line in the system prompt — and it is the difference between a diagnostic tool
and a confusing one. The stated purpose is learning what is wrong. *"That's `board.json:vbd_ci_low`"*
sends you to the right file; *"looks like a projection issue"* sends you nowhere and sounds more
confident.

Worth noting the counterintuitive part: **Haiku raises the hallucination risk, not lowers it.** A
smaller model asked to explain will confabulate more readily than a larger one. That is an argument
for keeping the citation rule, not for a bigger model — the citation is what lets the founder catch a
fabrication in one glance, and a fabricated field name is obvious in a way a fabricated explanation
is not.

## Also give it, in the system prompt

The standing data traps, so it does not have to be told each session: no market ADP for this league ·
the board holds no player-level opinion (`evaluative_adjustment` is always null by design, so
"is X undervalued" has no answer) · availability is uncalibrated at 1 of ~30 mocks · 2003–08 target
data is a hole · depth charts end 2024 · seven of nine opponents are known only by draft slot ·
2025 is a sealed holdout.

Point it at `docs/assistant-context.md`, which already exists for exactly this and is written to be
the only project doc an in-app assistant reads.

## Keep the scope small

Do **not** touch `narrate.py` layer 2. Do not replace the existing template renderer. This is an
additional dev-mode surface alongside it, not a migration. If it starts turning into a rebuild, stop
and say so — the rebuild is a separate sprint.

## Done looks like

Founder can open it behind the flag and ask questions about the running product, and answers cite
fields. Key handled via env with a test that fails if a key is committed. One test that a numeric
answer includes a field reference. Commit hash and test count. Note the rough per-question cost.
