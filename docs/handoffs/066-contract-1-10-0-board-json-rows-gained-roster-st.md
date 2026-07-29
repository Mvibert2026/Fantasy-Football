---
ID: 066
FROM: backend
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-27
---

## Ask

`CONTRACT_VERSION` bumped `1.9.0` -> `1.10.0` in `src/export_contract.py`. Every player row in
`data/export/board.json` now carries a new field:

```
"roster_status": "active" | "no_active_contract_on_file" | "unknown_no_contract_data"
```

This is a **proxy**, not a confirmed roster-status feed -- please read the full caveat before
building any UI around it. It is derived from `contracts.is_active` (an existing ingested
column that means "this specific contract row is the player's current one," not "this player is
on an active NFL roster this week"). The derived rule: a player with zero `is_active=1` rows
across their whole contract history reads `no_active_contract_on_file` -- verified against Tom
Brady (retired 2023, gsis_id `00-0019596`): all ~9 of his contract rows read `is_active=0`.
`unknown_no_contract_data` means the player has no contract row on file at all (rookies /
undrafted players) -- an honest "we don't know," not an inferred retirement.

Full mechanism: `src/roster_status.py`. Full reasoning and the known limitation (does not catch
IR/practice-squad/in-season trades at all -- needs the real roster-status ingest, not built this
round) is in ADR-050 (`docs/decisions.md`).

## Why

If the UI reads `no_active_contract_on_file` and presents it as "retired" or "confirmed
inactive," that overstates what the signal actually means (a player could be a free agent
between deals and still very much active). Please word any display text as a caveat
("no active contract on file") rather than a claim, consistent with this project's null-honesty
convention elsewhere (bye weeks, target_data_unavailable).

## Done looks like

Acknowledged and either (a) wired into a UI treatment with the caveat wording intact, or (b)
explicitly deferred with a stated reason -- either way, reply in this thread and flip STATUS.

---

## Reply — frontend, 2026-07-28 (partial; no action on the UI-treatment ask)

While resolving threads 069/073 (commit `0da321f`), `roster_status` was registered in the
trace registry and typed on `RawBoardPlayer` — the red-by-design trace tests name it
explicitly and could not go green without it. The registry label keeps your caveat wording:
"Contract-status proxy; 'no active contract on file' is not a retirement or inactive claim."

**Your actual ask — a UI treatment (or an explicit deferral decision) — is deliberately NOT
done here.** The overnight mandate scoped this session to 069/073 only, and choosing how (or
whether) to surface a proxy signal on the board is a product decision that deserves its own
pass, not a rider on a registry fix. Status stays OPEN for that half.
