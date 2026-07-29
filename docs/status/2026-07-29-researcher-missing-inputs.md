# 2026-07-29 · researcher · sourcing the three unbuilt inputs

**Task:** research only — establish what exists and on what terms for the three inputs `CLAUDE.md`
§5 names but that were never built: Vegas odds, coaching staff history, route participation.
Build nothing, ingest nothing, write no scraper.

**Output:** `docs/research/missing-inputs-sourcing-2026-07-29.md`.

---

## What was done

Read first, as instructed: `docs/CURRENT-STATE.md`, `docs/environment.md`, `docs/pm/MEMORY.md` §4,
`docs/research/source-audit-2026-07.md`, `CLAUDE.md` §5/§10. Then read
`docs/test-registry.md` (rows 11, 16/17, 29/29b/30), `docs/data-availability.md` §7.9,
`docs/deferred.md`, `docs/research/tier1-usage-source-inventory-2026-07.md`, and
`docs/handoffs/054-ftn-and-sleeper-harvest.md`.

Roughly 30 external fetches/searches. Every claim in the output document is tagged `[VERIFIED]`,
`[SNIPPET]`, `[SECONDARY]` or `[GAP]`. No `[GAP]` was filled.

## Premise challenges raised, not resolved unilaterally

1. **The dispatch calls Vegas odds "probably the highest-value missing input."
   `docs/test-registry.md` rates it Tier 0, edge "Low", and defines Tier 0 as "having them is not an
   edge" — while rating route participation (#17) and coordinator continuity (#29) "High".** That is
   a contradiction between the task framing and a written project document. I did the research on all
   three as asked, but did not adopt the ordering as fact; the recommendation is decided on the
   evidence gathered. Escalated in the output document §0(b), for PM/founder to settle.
2. Minor citation slip: the dispatch attributes the MFL retrospective-aggregate trap to `CLAUDE.md`
   §6.1; it is actually recorded in `docs/CURRENT-STATE.md` open item 2 and `docs/pm/MEMORY.md` §4.
3. `docs/environment.md` describes a Windows conda box with a `PreToolUse` hook. This session ran in
   a Linux cloud container **with no shell tool of any kind** — read/write/grep/glob/web only. Not a
   conflict to resolve, but it meant **zero `[MODAL-SAMPLED]` evidence was possible**: no `nflreadpy`
   call, no `data/nfl.db` query, no API call needing a key. Several gaps in the report are one
   Python query away for anyone with a shell, and the report says which.

## Headline findings

- **Vegas game lines are not a sourcing problem.** `nflreadpy.load_schedules()` already carries
  `spread_line`, `total_line`, four odds columns and two moneylines, CC-BY-4.0, $0, from 1999. Implied
  team total is arithmetic on two of them. The repo references none of these columns anywhere in
  `src/` (grepped). **The one gap that matters — opening vs closing line — is undocumented**, and the
  report explains precisely where that bites (season-N in-season use) and where it does not
  (season N−1 aggregates, which is what the backtest rule permits anyway).
- **The Odds API is the only odds source whose terms permit display to a third party.** Genuine
  10-minute point-in-time snapshots from 2020-06-06, paid-plans-only, historical requests at 10×
  credits, cheapest usable tier **$30/month**. **It has no NFL season-win-totals market** — verified
  against their sport-key list, so it must not be bought expecting that.
- **Season win totals: covers.com/sportsoddshistory, 1999–2026, $0, fetch permitted, display
  prohibited.** Sample-quality caveat is the decisive finding: the 2020 page is dated "As of
  September 10, 2020"; the **2012 page carries no date at all.** n = 2 of 28 seasons and they
  disagree on the property that determines look-ahead safety.
- **Coaching staff — the real finding of the session.** PFR re-verified as blocked today (both
  `robots.txt` and `sports-reference.com/data_use.html` return HTTP 403; recorded and stopped).
  nflverse confirmed to carry head coaches only. **Wikipedia's `Template:NFL final staff` is
  transcluded on 1,062+ mainspace articles spanning 1946–2024, names offensive and defensive
  coordinators, is reachable through the official MediaWiki API, and is CC BY-SA 4.0 — fetch *and*
  display both permitted.** Two hazards flagged: I verified only two articles, both Atlanta, so
  per-team-season population rate is a `[GAP]`; and the template is *final* staff, an end-of-season
  end-state with no `as_of_date`, which is a genuine look-ahead problem for a preseason input.
- **Route participation: record is still accurate.** No routes-run column in nflverse. The
  participation `route` field describes only the *targeted* receiver's route, not who ran routes.
  The defensible proxy is pass-play presence via `offense_players`, 2016–2024 only, with a
  **systematic position-correlated bias** (overstates blocking-heavy RBs and inline TEs) that must be
  named in the column and not just called "a proxy". Fantasy Points sells real route data and its ToS
  forbids automated collection outright; its price is a `[GAP]` because the page renders client-side.
  Thread 054 (the founder's existing, unaudited FTN subscription) is the cheaper next move and was
  deliberately not duplicated.

**Recommendation: coaching staff first** — it is the only one of the three that ungates a
registry item rated High edge, and the only one whose licence permits display.

## Not done, and why

- **No handoff thread was opened or replied to.** This task named no thread, and the three open
  `researcher` threads (054, 057, 070) are different asks. A new thread would need
  `python tools/handoffs.py new` for its ID, and IDs must never be hand-typed or computed from a
  directory listing (the 043/049/053 and ADR-048 collisions). **No shell tool was available in this
  session**, so the allocator could not be run. Flagged for the coordinator.
- **Nothing was committed** — same reason: no shell. Files written: this log and
  `docs/research/missing-inputs-sourcing-2026-07-29.md`. `python tools/status_log.py sync` has not
  been run, so `docs/status/INDEX.md` is stale by one entry.
- No founder statement occurred in this session, so no `docs/founder-requests/` entry was created.
- `docs/CURRENT-STATE.md` not edited: this session changed no build state, only added a research
  document.
