# Agent cost log

Founder asked for cost tracking to be resumed and kept up (2026-07-30). This file is the record;
the PM dashboard's Cost tab reads stale within hours and should link here rather than restate it.

## What is actually measurable, and what is not

**Measurable:** every completed agent reports a `subagent_tokens` figure on completion. That number
is recorded below verbatim.

**Not measurable, and not guessed here:**

- **The input/output split.** The reported figure is a single number. Input runs $3/MTok and output
  $15/MTok on Sonnet — a 5× spread — so the dollar cost of the same token count varies by 5×
  depending on a split nobody reports. Dollar figures below are therefore a **bounded range**, not a
  point estimate. Anyone who replaces them with a single confident number has invented it.
- **Agents that die.** An agent killed by a session limit or stopped mid-run reports no usage at
  all. Two did that today. Their spend is real and is missing from every total here.
- **PM's own context.** The main session's tokens are not reported to itself. Only agent spend is
  counted, so **every total below is a floor, not a total.**

## Rates (per million tokens, verified 2026-07-30)

| Model | Input | Output |
|---|---|---|
| Opus 5 | $5.00 | $25.00 |
| Sonnet 5 | $3.00 ($2.00 intro through 2026-08-31) | $15.00 ($10.00 intro) |
| Haiku 4.5 | $1.00 | $5.00 |

Routing per `CLAUDE.md` §9: mechanical work → Haiku, build work → Sonnet, methodology and
red-teaming → Opus. So `librarian`, `backend`, `frontend`, `data-ops` bill at Sonnet; `ranker`,
`strategist` and `fable` at Opus.

## 2026-07-30 (PM session)

| Agent | Work | Tokens | Status |
|---|---|---:|---|
| librarian | Backlog triage, 38 threads | 213,070 | complete |
| backend | ADP vs. production mispricing | 210,285 | complete |
| librarian | Design-spec build-state audit | 102,970 | complete |
| ranker | RB/QB/TE component models | not reported | died on session limit |
| frontend | Correctness queue (first attempt) | not reported | stopped by PM |
| frontend | Player card, Opponents, headers, rounds | pending | running |
| frontend | Chatbot data access + UX | pending | running |
| ranker | Zero RB simulation, volatility | pending | running |
| researcher | Archetype taxonomy | pending | running |
| data-ops | Historical ADP, coordinator table | pending | running |

**Reported so far: 526,325 tokens across three completed agents.**

At Sonnet rates that is **$1.58 if entirely input, $7.89 if entirely output** — the true figure sits
between. A plausible mid-case (80% input) is roughly **$3**. Treat single-digit dollars as the right
order of magnitude for a session of this size, and do not report a tighter number than that.

## Where the effort actually went

Dispatch count is a better effort signal than tokens, because a cheap agent and an expensive one
both consume a PM decision and a slot.

| Track | Dispatches | Share |
|---|---:|---:|
| Rankings / research | 5 | 56% |
| Frontend | 2 (+1 stopped) | 22% |
| Meta / bookkeeping | 2 | 22% |

Two things worth watching:

1. **Bookkeeping took as much as frontend.** Both librarian runs were backlog and audit work — real
   value (24 of 38 threads turned out to need no action; two numbering collisions were caught) but
   it is overhead, not product. If that share does not fall next session, the process is eating the
   work.
2. **The 7 September draft is a hard date and research is not gated by it.** The current 56/22 split
   favours the model over the tool. That matches the founder's stated priority ("when we use our
   Fable tokens, that's what I want to spend them on") and it is the right call *now* — but the
   ratio has to invert before the draft, because an un-usable app with a great model behind it is
   worth nothing on draft day.
