---
ID: 031
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: 027, 028, Settings build
---

## Ask

A full audit of the shipped frontend against every design artifact now in the repo, followed by
wiring anything that has backend data behind it. Two phases — **do not start phase 2 until phase 1 is
written down**, or the audit becomes a memory of what you fixed rather than a record of what was
wrong.

### Phase 1 — audit, and write it down

Compare what actually runs against:
- `docs/FRONTEND-SPEC.md` (38K, the full implementation spec)
- `docs/design-handoff/screens/01-draft-board.md` through `04-player-detail.md`
- `docs/design-handoff/settings/SETTINGS-EDITOR-SPEC.md`
- `docs/design-handoff/spec/design-tokens.json`, `api-contract.json`, `formulas.json`,
  `acceptance-checks.json`
- The reference PNGs in `docs/design-reference/`

Produce `docs/frontend-audit-2026-07.md` with one row per spec element and a verdict of
**built / partial / absent / drifted**. Be exhaustive and be blunt. "Absent" is a fine answer and by
far the most useful one.

Pay particular attention to `acceptance-checks.json` — Design shipped a machine-readable checklist,
so work through it item by item rather than eyeballing screens.

### Phase 2 — wire what has data

For every element marked partial or absent, check whether the backend artifact exists in
`data/export/<league_id>/`. Where it does, wire it. Where it does not, render the **explicit null**
and open a handoff thread to `backend` naming the field you need.

**Do not invent a placeholder to fill a gap.** A fabricated value is worse than an empty cell,
because nothing downstream catches it. This is Principle #2 and it is the whole product.

Confirm while you are in there: are you reading from `data/export/<league_id>/` or the old flat
`data/export/`? The path convention changed and the notification was never sent. A stale path does
not error — it silently serves old data.

## Why

Design has now shipped four Draft screens plus a six-state Settings editor, and nobody knows how much
of it exists in the running app. The one time this was checked, two screens reported complete were
absent entirely while the whole suite passed. The audit is how that stops being a surprise.

## Done looks like

`docs/frontend-audit-2026-07.md` committed with a verdict per element. Everything wirable, wired.
Everything else rendering an honest null with a thread open to `backend`. A **screenshot** of each
materially changed screen. Report as "built, pending screenshot verification." Commit hash and test
count — and please record the frontend test count, which still exists nowhere in this repo.

---

## Addendum — 2026-07-26, requested by Design

*(Folded in from the standalone `031-ADDENDUM-audit-additions.md`, which had no `TO:` field and was
failing `tools/handoffs.py check` as an orphaned, unaddressable thread — see the frontend reply below.
Content preserved verbatim; only the location moved.)*

Two additions to the audit, both cheap if done during the pass and expensive to reconstruct later.

### 1. Retrofit status — picked up or deferred?

`docs/design-system/AUDIT.md` specifies five retrofits, RETROFIT-1 through RETROFIT-5. For each,
record whether the shipped app already reflects it, partially reflects it, or does not. RETROFIT-5
(the TypeAhead back-port to the Draft board — key map, autofocus, order randomisation, `entry_mode`)
is the one most likely to be partially present, since a type-ahead already exists there in a worse
form.

The point is to know which retrofits can be closed for free versus which are real work.

### 2. Null vocabulary — did it survive contact?

This is the higher-value of the two and the reason Design asked for it.

The product distinguishes five null-ish renderings, and they are **different claims**:

| Rendering | Means |
|---|---|
| `—` | no value exists for this field |
| `<1%` | a real, computed, very small probability |
| `0%` | a real, computed zero |
| `not yet` | will exist, has not been computed |
| `·` | structurally not applicable here |

Audit whether all five remain distinct in the running app, or whether any have collapsed into one
another.

**Why this specifically.** Design's framing is exact and worth preserving: *drift here is silent and
compounds, because each individual substitution looks reasonable in isolation.* Nobody ever decides to
degrade the null vocabulary. Someone renders `—` where `not yet` belonged because it looked tidier,
and six months later the distinction no longer exists anywhere and no commit is responsible for
removing it.

This is also the single place where drift attacks the product's actual thesis rather than its polish.
Principle #2 exists because `0%` and "not computed" are different claims; a build where they render
identically has quietly abandoned the differentiator while every test still passes.

Report per screen: which of the five appear, and any place two are rendered the same way.
