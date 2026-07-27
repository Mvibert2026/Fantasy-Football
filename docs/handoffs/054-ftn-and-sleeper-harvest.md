---
ID: 054
FROM: pm
TO: researcher, data-ops
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: any subscription decision
---

## Ask

Two data questions the founder raised that never became threads — my error, they were left in chat.

### 1. FTN — audit the subscription the founder already holds

**Nobody has checked what it provides.** Before any new purchase, establish what the existing one covers.

- Does the subscription grant **API or bulk export**, or site viewing only?
- Documented endpoints, auth method, rate limits?
- Do they aggregate **ADP across multiple sites**? Which, at what depth, how far back?
- What **in-season** data — weekly projections, snap counts, usage, news — and **at what latency**?
  Latency is the point. nflverse already provides usage and injuries for free; what free sources do
  not provide is Tuesday-morning freshness.
- Note: nflverse already carries an **FTN charting subset under CC-BY-SA**. Establish whether that
  overlaps what the subscription offers — we may already have some of it, licensed, for nothing.

Display and redistribution are **not** a concern — private personal use. Audit access and latency only.

### 2. Sleeper draft harvesting — is it viable at volume?

The audit established: per-draft picks are available **if you already hold a `draft_id`**, and there is
**no discovery endpoint**. That is the whole blocker. Test three routes empirically:

- Are draft IDs **enumerable or sequential**? Try adjacent values around a known ID.
- `/v1/user/{user_id}/drafts/nfl/{season}` — does it work, and can user IDs be discovered at all?
- Any listing surface for public mock lobbies, documented or otherwise.

**Call the endpoints. Report status codes, row counts and a sample row.** A working request beats a
paragraph about whether one might exist. Respect the stated limit — stay under 1000 calls/minute.

If all three fail, record Sleeper harvesting as **closed** with the evidence, so it is not
rediscovered in a month.

### Why this matters more than it looks

Every completed draft is a test of the availability model — real or mock, ours or a stranger's. And a
completed pick sequence **is** per-pick state; you replay it to reconstruct the board at every pick.
If drafts can be harvested, the requirement to personally run ~30 mocks largely disappears, and with
it the founder-time cost that has been the binding constraint on validating the product's core claim.

## Done looks like

`docs/research/ftn-audit-2026-07.md` and `docs/research/endpoint-test-2026-07.md`. Confidence tagging
throughout. Blocked means recorded and stopped, never routed around. Then a one-line recommendation:
is there a named gap a subscription would close that free sources do not?

---
### pm · 2026-07-27

Note for whoever picks this up: 057 §1 asked the same Sleeper dated/rolling-ADP question and has been
struck there as a duplicate of § 2 above (reconciliation pass). Nothing changes here — just avoiding
it getting answered twice.
