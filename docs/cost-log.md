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

---

## 2026-07-30, later block — the design build-out

Eight further agents after the table above. All eight completed and reported.

| Agent | Work | Tokens | Outcome |
|---|---|---:|---|
| frontend | Trace mode — design item 1 | 513,740 | shipped, live |
| frontend | CI mislabelling + glossary aliases | 367,431 | shipped |
| frontend | Periodic grid + layout modes — items 3, 7 | 336,485 | shipped |
| frontend | Assistant window — item 4 | 263,508 | shipped |
| frontend | Light theme — item 5 | 230,724 | shipped, live |
| data-ops | Data freshness pass | 101,197 | **partial — ingest did not land** |
| backend | `vs your options` contract question | 99,139 | answered, no code needed |
| data-ops | Founder mock-draft ingestion | 82,450 | shipped |

**Later block: 1,994,674. Day total across 22 reporting agents: 5,406,020.**

| Basis | Cost |
|---|---|
| All input, $3/MTok | $16.22 |
| All output, $15/MTok | $81.09 |
| 70/30 in/out (illustrative only — the split is not reported) | ~$35.68 |

Still a **floor**: three agents earlier in the day died and reported nothing, and PM's own context is
not counted by any tool.

### What the split says about where effort went

**Frontend took 86% of the later block** (1,711,888 of 1,994,674). That is the correct shape for a
day whose stated goal was catching the app up to two design rounds — but it is worth stating plainly
that it is the *opposite* of the earlier block, where rankings and research took 56%. Effort followed
the founder's sequencing, which is what should happen.

### The one that cost real money and returned nothing durable

`data-ops · data freshness` spent 101,197 tokens and its ingest **did not land**: it wrote to the
worktree's copy of `data/nfl.db`, which is gitignored and does not survive a reset. The agent said so
rather than reporting success, which is the right behaviour and the reason this is recoverable.

**It is also a preventable class of waste, and the dispatch is what failed.** `docs/environment.md`
§4 tells agents to copy `nfl.db` into the worktree to run tests. Nothing told this agent that writes
to that copy are discarded. The instruction that existed covered reading; the work required writing.
Fixed in `environment.md` §4b going forward.

### Cheapest useful work of the day

`backend · vs-your-options contract` — 99,139 tokens to establish that a queued design item needed
**no backend work at all**, unblocking it immediately. A question answered before it becomes a build
is the highest-leverage thing this structure does.
