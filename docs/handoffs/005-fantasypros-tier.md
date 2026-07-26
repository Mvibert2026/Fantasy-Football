---
ID: 005
FROM: pm
TO: founder
STATUS: BLOCKED-ON-YOU
OPENED: 2026-07-26
BLOCKS: bootstrap CIs, full-board projections
---

## Ask

Do NOT buy the paid tier. Instead: log into FantasyPros in your browser, use its own **export /
download** control on the rankings and projections pages, and drop the CSVs into
`data/raw/fantasypros/<YYYY-MM-DD>/`. Data Ops ingests from there.

Roughly two minutes, repeatable monthly, zero cost, and it yields the full board rather than 40 rows.

## Why not scraping — and why you don't need it

You said personal use shouldn't violate the ToS. That is a reasonable intuition and it is not how
these agreements are written: FantasyPros' terms restrict *automated access and extraction*
regardless of purpose, and having a login makes it more binding, not less — you accepted the terms
to get the account. Personal use limits your exposure; it does not make the access authorised. I am
not going to write a scraper for it, same as I won't for FFC.

The useful part is that the argument is moot. The export button is a **sanctioned feature they built
for logged-in users**. You clicking download is exactly the use they intend, gets you the complete
dataset the API's free tier withholds, and costs $72 less than the paid tier. Refusing to scrape
isn't costing you anything here — it's routing you to the better option.

**On browser automation:** Claude in Chrome could drive your logged-in session to click that button.
That is a genuine grey area — your browser, your session, your credentials, but still automated
access. Given the manual download takes two minutes and happens roughly monthly, I would not spend
the ambiguity. If the cadence ever becomes weekly, revisit.

## What this unblocks

Full-board projections for the 233 players currently missing them, and the FantasyPros 2021–24
backfill that the bootstrap confidence intervals in `backtest.py` chain off. Both currently blocked.

## Done looks like

One dated folder of CSVs in `data/raw/fantasypros/`. Reply here with the folder name and I'll open a
Data Ops thread to ingest it. If the export control isn't where I expect, say so and I'll have
Researcher find it rather than guessing.
