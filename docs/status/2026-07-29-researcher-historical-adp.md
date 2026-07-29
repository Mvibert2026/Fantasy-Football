# 2026-07-29 · researcher · historical preseason ADP availability

**Mandate:** research only. Establish what historical, point-in-time, preseason draft-market data is
legitimately obtainable, how far back, and in what formats — because the confirmatory market-baseline
comparison `CLAUDE.md` §6.5 demands is currently limited to n=4 expert-consensus seasons.

**Nothing was built, ingested, scraped in bulk, or committed to code.** Output is
`docs/research/historical-adp-availability-2026-07-29.md` plus a reply on thread 055.

## What was done

~35 individual page reads of Fantasy Football Calculator's HTML ADP pages (one per season-format,
no concurrency, no bulk harvest), plus its `robots.txt`, its ToS/terms paths, and its ADP index.
Cross-checked against `data/adp-snapshots-ffc/2026-07-29_half_ppr.csv` (the repo's own same-day
capture) and `src/ingest_ffc_adp.py`.

## Headline

**The n=4 wall lifts, to 13 (non-PPR 12-team, 2010 + 2013–2024) or 7 (half-PPR 12-team,
2018–2024).** FFC states an explicit bounded draft-date window on every archived season that carries
data, so a per-season look-ahead gate is computable rather than assumed. It is genuinely unlike MFL,
which stamps today's date on an accumulated aggregate.

But: **"back to 2007/2009" is not achievable.** 2007–2009 windows all run to June 20 2010, 2011
straddles kickoff, 2012 ends on kickoff day. And the archive is **12-team only** — 10-team and
14-team requests silently return the 12-team page with HTTP 200. Westwood is half-PPR *10*-team, so
no archived season matches the primary league's format exactly.

## Premise challenges raised

1. **This does not rescue PR-004.** It is registered and frozen; §4 exit 3 and ADR-C both say a new
   baseline is a new test with a new id, not an amendment. The honest path is a fresh confirmatory
   registration. PR-004 should still run as-is.
2. **PR-004's primary arm was never n=4** — only the market-comparison headline was.
3. **n=7 half-PPR does not survive BH at m=4.** Sign-test floor 0.0156 > α/m = 0.0125. A perfect
   7-of-7 sweep would still fail. The format arm and `m` must be chosen before the run.
4. **n=13 is n=1 by market** — thirteen draws from one site's *mock*-draft pool, sample sizes varying
   9x across seasons.

## Escalated, not resolved

- **The app is public; every source authorisation is scoped "private, one person, void if a second
  human."** FR-023, D-020 and D-021 all carry that condition, and `CURRENT-STATE.md` records the app
  as live on the open internet by founder choice. Founder decision with a licensing consequence.
- **`docs/ideas-inbox.md` contains unresolved merge-conflict markers** (`<<<<<<< HEAD` /
  `=======` / `>>>>>>> c191f45...`) around the strategist's PR-004 entry and backend's ADR-057
  entries. **Not touched.** Both sides look like real work; this is a genuine conflict for the
  coordinator.
- **`CURRENT-STATE.md` still says FFC is blocked** ("FFC is blocked by robots.txt regardless",
  "FFC remains blocked") while `docs/pm/MEMORY.md` §4 and FR-023 record it as unblocked. MEMORY
  states it supersedes; the supersession was never propagated. Stale-line fix, not mine to make.

## Blocked, recorded, not routed around

`web.archive.org` — "Claude Code is unable to fetch from web.archive.org". Wayback captures would
have been a strong independent source of true point-in-time ADP boards. Stopped there.

## Gaps left open deliberately

- Exact row count per archived season. WebFetch's markdown conversion drops rows demonstrably.
  Closes by running `src/ingest_ffc_adp.py::parse_adp_table()` over saved HTML.
- FFC Terms of Service, in any retrievable form. Third independent attempt, third failure.
- Whether the displayed window is exactly the sample bound. Closes for free from two weeks of the
  existing daily capture.
- FFC PPR archive depth (2010 verified present, 2009 absent, 2011–2024 not probed).

## Tooling note

This session had **no Bash tool**. Consequences: no `tools/handoffs.py new` (so no thread was
allocated for this work — the reply went on the existing thread 055, which is exactly on-topic), no
`tools/status_log.py sync`, and **no commit**. Files written this session:
`docs/research/historical-adp-availability-2026-07-29.md`, this log, the thread 055 reply, and one
`docs/ideas-inbox.md` append.
</content>
</invoke>
