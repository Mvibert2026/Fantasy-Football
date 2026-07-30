# Founder browser exports

Files the founder downloads by hand from a provider's site, because no API path exists. One directory
per pull, named `YYYY-MM-DD` — **ISO dates only**, because the ingest sorts these lexically to find
the newest and silently ignores anything else.

## FantasyPros "ALL Rankings" — the board's ranking source

`src/ingest_fantasypros_csv.py` defaults to the **newest dated directory containing the file**, so a
re-export is a drop-in with no flags.

    1. On FantasyPros, confirm the scoring format is Half PPR before exporting.
       The format is not recorded in the file — if it is wrong, the ingest cannot tell,
       and the board silently ranks on the wrong scoring.
    2. Save as:  data/raw/founder-export/<today, YYYY-MM-DD>/FantasyPros_2026_Draft_ALL_Rankings.csv
    3. Run:      python src/ingest_fantasypros_csv.py
    4. Verify:   python tools/data_freshness_check.py     # rankings:fantasypros_csv_2026draft -> OK
    5. Re-export the board afterwards, or the fresh rankings sit in the DB unused.

Why the filename matters: the resolver looks for that exact name. A directory dated today holding a
differently-named file is skipped, and the ingest quietly uses the older export instead — a stale
read that looks like a successful run.

`2026-07-30/` is present and empty, waiting for the next pull.

## What is already here

| Directory | Contents |
|---|---|
| `2026-07-27/` | FantasyPros ALL Rankings (575 players, Half PPR), Underdog ADP, three-analyst rankings |
