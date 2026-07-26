---
ID: 024
FROM: pm
TO: data-ops
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: P3-2 (date-parametrised board refresh)
---

## Ask
Ingest injury status via nflverse `load_injuries`, which covers 2009–2025, and capture it **with an
`as_of_date` on every row**.

## Why
This is logged as `deferred.md` item P3-2 and the reason it matters is subtle: without `as_of_date`,
any historical rebuild of the board uses final-season injury knowledge, which is look-ahead
contamination and violates the project's own §6.1. The ranking side of P3-2 already works today; this
is the missing half.

**This is not the same as building the injury pipeline.** The real-time injury/news feature is
deliberately deferred over hallucination risk, with that reasoning stated in the code. Do not build
prose generation, do not build alerting. Ingest historical injury facts with dates. Nothing more.

## Constraints
Dates are the entire point. A row without an `as_of_date` is worse than no row, because it looks
usable. Reject rather than default them.

## Done looks like
Injury data ingested 2009–2025 with `as_of_date` on every row, row counts per season reported, a test
asserting no row can be inserted without a date. Commit hash and test count.
