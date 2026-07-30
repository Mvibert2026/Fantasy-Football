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
| data-ops | FFC PPR ADP + coordinator table | 171,724 | complete |
| researcher | Archetype taxonomy | 198,034 | complete |
| librarian | Bookkeeping investigation (FR-090) | 96,650 | complete |
| backend | Sleeper screen (FR-094) | 172,751 | complete |
| researcher | Injury-service evaluation (FR-097) | 143,959 | complete |
| frontend | Assistant page context + chat (FR-076/077) | 398,259 | complete |
| frontend | Founder feedback batch (FR-067/79/82/83/87) | 502,570 | complete |
| ranker | Zero RB + volatility (FR-085/086) | 366,670 | complete |
| ranker | Skewness/kurtosis + dead-zone era contrast | 418,450 | complete |
| librarian | Insights-ledger backfill | 151,552 | complete |
| backend | League-scoring export fix | 264,402 | stopped mid-run; work recovered by PM |
| ranker | RB/QB/TE component models | not reported | died on session limit; work recovered |
| frontend | Correctness queue (first attempt) | not reported | stopped by PM |
| backend | Consensus vs ADP (FR-099) | not reported | died on API error; work recovered |

**Reported so far: 3,411,346 tokens across 14 agents.** Three more died or were stopped without reporting; their spend is real and missing here.

At Sonnet rates that is **$10.23 if entirely input, $51.17 if entirely output** — the true figure sits
between, and the split is not reported. A plausible mid-case (80% input / 20% output) is roughly
**$18**. Treat **tens of dollars** as the right order of magnitude for a session of this size, and do
not report a tighter number than that. Three agents died or were stopped without reporting at all, so
even the range is a floor.

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
