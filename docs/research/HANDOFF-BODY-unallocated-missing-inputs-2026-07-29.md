# UNALLOCATED handoff body — missing inputs sourcing (researcher → pm, data-ops)

**This is not a thread. It has no ID and must not be given one by hand.**

The researcher session that produced `docs/research/missing-inputs-sourcing-2026-07-29.md` ran in a
cloud container with **no shell tool**, so `python tools/handoffs.py new` could not be run. Thread IDs
come only from the allocator — hand-typing or computing max+1 is what collided at ADR-048 and threads
043 / 049 / 053. The body is staged here so the next session with a shell can allocate it in one
command and paste this in.

**Allocator command:**

```
python tools/handoffs.py new --from researcher --to pm,data-ops \
  --subject "Sourcing decision: Vegas odds, coordinator history, route participation" \
  --blocks "test-registry #11, #17, #29, #30; the coach_id dimension"
```

---

## Ask

`docs/research/missing-inputs-sourcing-2026-07-29.md` is the full audit. Three things need a decision
that a researcher may not take alone.

### 1. A premise contradiction that needs settling, not averaging

The dispatch that commissioned the audit called Vegas odds "probably the highest-value missing input
in the project." `docs/test-registry.md` places it at **#11, Tier 0, expected edge "Low"**, and
defines Tier 0 as *"Everyone has these. Not having them is a loss; having them is not an edge."* The
same registry rates **#17 route participation "High"** and **#29 coordinator continuity "High"**.

The audit did not resolve this. Both statements can be true — odds are almost certainly the
*cheapest* input and may still be the *lowest-edge* one — but the roadmap needs one of them to be the
ordering principle. **PM or founder call.**

### 2. Coaching staff: the block is real and there is now a legitimate way past it

- Pro Football Reference re-verified blocked today: `robots.txt` **HTTP 403**,
  `sports-reference.com/data_use.html` **HTTP 403**. Conservative default applies, no scraper
  considered.
- **Wikipedia's `Template:NFL final staff` carries offensive and defensive coordinators per
  team-season**, is transcluded on **1,062+ mainspace articles** (that is a floor — the API paginator
  had not exhausted), spans **1946 → 2024**, is reachable through the official MediaWiki API, and is
  **CC BY-SA 4.0 — fetch and display both permitted** with attribution and share-alike. It is the
  best licensing position of any source this project holds.

Two things a build must handle, and both are cheap to get wrong:

- **Sample quality:** only two articles were verified, both Atlanta (2019 and 2024). That is an n of
  one franchise. Per-team-per-season population rate is a `[GAP]`. Measure it and quarantine misses
  before trusting coverage.
- **Look-ahead:** the template is *final* staff — the end-of-season end-state, with no `as_of_date`.
  For a preseason input that is post-cutoff information in any season with a mid-year firing. Either
  restrict to seasons with no in-season change, or reconstruct start-of-season names from article
  revision history (possible via the API, cost unmeasured).

**Ask:** is this worth an ingestion task, and if so does it go to data-ops now or after the bottom-up
work lands?

### 3. Two numbers the founder has to decide on, not an agent

| Want | Cost | Display to a second person |
|---|---|---|
| Point-in-time game-line snapshots back to 2020-06-06 | **$30 / month** (The Odds API, 20K plan; historical requests cost 10× credits) | **permitted in-app**; raw redistribution prohibited |
| Season win totals 1999–2026 | **$0** (covers.com/sportsoddshistory) | **prohibited** — reproduction clause, fetch-only |
| Routes run, direct per-player | **`[GAP]`** — Fantasy Points renders prices client-side; not retrievable by fetch. Their ToS forbids automated collection but permits manual browser reading, so this is a one-minute look for a human | not established |

Note that the free game-line path (nflverse `load_schedules`, 1999→present, CC-BY-4.0, display
permitted) covers most of what `CLAUDE.md` §5 asks for at zero cost, and implied team total is
arithmetic on two columns already in it. The $30/month buys **intraday point-in-time snapshots**, not
coverage — and it does **not** carry season win totals at all (verified against their sport-key list).

## Also flagged, no action taken

- `docs/ideas-inbox.md` still carries **unresolved merge-conflict markers** around the strategist
  PR-004 and backend ADR-057/ADR-059 entries. Second session to report it; both sides look like real
  work; not resolved unilaterally.
- Thread 054's FTN audit is the cheapest next move on route participation — the founder already holds
  an FTN subscription and FTN is the upstream supplier of nflverse participation data 2023+.
  Deliberately not duplicated.

## Done looks like

A decision on (1), a routing decision on (2), and the founder reading the Fantasy Points price off
the page so the third row of the table above stops being a `[GAP]`.
