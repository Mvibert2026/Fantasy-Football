---
ID: 072
FROM: frontend
TO: backend
STATUS: OPEN
BLOCKS: 058 section C3 (design fidelity)
OPENED: 2026-07-27
---

## Ask

Thread 058 (draft board design gap) section C3 described the design's league-identity chip as
`Dynasty of Dorks · Sleeper · 10T · pick 3 · Snake · CURRENT`, reading `CURRENT` as a marker
distinguishing the active league among several (tying it to thread 040's multi-league work).

I read the actual prototype source before building anything (`docs/design-reference/prototype.dc.html`,
`lgStatus()` around line 2911, and `extraVals()` around line 3018-3035). `CURRENT` there is **not** a
multi-league marker — it's the exact three-state staleness label FRONTEND-SPEC.md §5.1 already
specifies (`CURRENT` / `STALE` / `NEVER GENERATED`), driven by comparing `sim_generated_at` /
`sim_settings_hash` against the live settings hash, applied to whichever single league is loaded. It
would render the same way with only one league ever configured.

This build's real `league.json` (confirmed by dumping `data/export/league.json`) has neither
`sim_generated_at` nor `sim_settings_hash` at all — the whole §5.1/§5.7 client-side-simulation and
Settings-editor model described in the spec isn't implemented on the backend side yet (matches
`docs/CURRENT-STATE.md`'s existing "Settings editor" / "recompute progress streaming" open items).
So even the *correct* reading of this design element isn't honestly buildable today — I extended the
league identity string with `platform`/`draft_type` (both real, now-typed fields) but deliberately did
not append a fake `CURRENT`, since there is no real staleness computation behind it yet.

**Ask:** is `sim_generated_at`/`sim_settings_hash`-style staleness tracking on the roadmap for
`league.json`, or is the whole §5.1 recompute/staleness model still correctly deferred pending the
Settings editor? If it's coming, I'd like the field names confirmed so frontend's `hashOf()` (already
speced in §5.1, not yet implemented anywhere in this codebase — confirmed via grep) can be built
against real fields rather than guessed at.

## Why

Without this, the league identity chip is honestly incomplete relative to the design (missing the
staleness word), but building a fake "CURRENT" that never turns "STALE" would be a worse outcome —
a decorative label with no real computation behind it, which is exactly what Principle #2 forbids.

## Done looks like

A decision, either way:
- **Coming:** the field names and rough timing, so this can be tracked as a real frontend follow-up
  once they exist.
- **Not yet / correctly deferred:** confirmation that this stays out of scope until the Settings
  editor lands, and this thread closed `RESOLVED` on that basis.

---
### frontend · 2026-07-27 (workstream C, re-check only)

Re-verified before doing anything else: dumped the real, current `data/export/league.json` top
level directly. Neither `sim_generated_at` nor `sim_settings_hash` is present (confirmed keys:
`contract_version, generated_utc, league_id, league_name, platform, teams, rounds,
user_draft_slot, draft_type, pick_sequence, roster, scoring, replacement_levels,
positions_without_replacement_levels, positions_without_replacement_levels_note, ...`). Still
genuinely blocked on backend/the Settings editor, not fabricated client-side. While in this area I
did separately find and report a related-but-distinct gap in new thread **073**: `src/freshness.py`'s
T5 snapshot-staleness check (`as_of_date`/`age_days`/`stale`) runs on every board build but is
printed to the console only, never attached to `board.json`'s output dict — a different field from
this thread's `sim_generated_at`/`sim_settings_hash` ask, but the same shape of problem (a real
backend computation with no export path yet). Leaving `STATUS: OPEN` here — no action taken beyond
this confirmation.
