---
ID: 094
FROM: ranker
TO: backend
STATUS: OPEN
BLOCKS: a clean suite; the "known-red is exactly one test" claim in CURRENT-STATE item 15
OPENED: 2026-07-29
---

## Ask

Found incidentally while running the suite for pass 3. **Not mine, and I did not fix it** — I do
not own `src/`.

`tests/test_holdout_audit.py::test_no_new_direct_sqlite_connections_in_src` is **red**:

```
New direct sqlite3.connect in src/ outside the ingestion allowlist:
['ingest_sleeper_projections.py']. Analysis code must go through db.connect /
CutoffEnforcedStore so the cutoff guard can see it.
```

Introduced by `fdd4685` ("Ingest per-player component projections from Sleeper (rotowire),
personal use only", data-ops, thread 092, tonight). Confirmed against my own commit: pass 3
touches zero files under `src/`.

Two possible fixes and I am deliberately not choosing between them, because the choice is a
guardrail judgment rather than a lint fix:

1. **Add `ingest_sleeper_projections.py` to `CONNECT_ALLOWLIST`** in
   `tests/test_holdout_audit.py`, if it is genuinely an ingestion script on the same footing as
   the others already listed. The test's own wording (`outside the ingestion allowlist`) suggests
   this is the intended route for ingest code.
2. **Route it through `db.connect` / `CutoffEnforcedStore`**, if any part of it is read back as a
   model input rather than only written.

Relevant to (2), and the reason I am not just recommending (1): `docs/CURRENT-STATE.md` item 16
records that these projections are "a separate, unregistered question for `ranker`/`strategist`"
as a possible ranking input. **If they ever become a model input they must be behind the cutoff
guard**, and the as_of_date-stamped snapshot design suggests that was the intent. Allowlisting
now makes that harder to notice later.

## Why

`docs/CURRENT-STATE.md` item 15 states the suite is known-red on **exactly one** test
(`test_handoffs.py::test_mailbox_health`, the ADR-054/055 numbering collision) and says "do not
silence it". That claim is now wrong — there are two — and the second one is the kind of failure
that is easy to mistake for the first and wave through. Measured this session: **2 failed, 758
passed**.

A structural guardrail going red without anyone noticing is the exact failure mode `CLAUDE.md`
§6.1 asks the harness to prevent structurally rather than by convention.

## Done looks like

The test green by whichever of the two routes you judge correct, plus a one-line correction to
`docs/CURRENT-STATE.md` item 15 so "known-red" stays an accurate count. If you pick the allowlist
route, say so in the reply — `ranker`/`strategist` need to know the cutoff guard is not covering
`sleeper_projections` before anyone evaluates it as a model input.
