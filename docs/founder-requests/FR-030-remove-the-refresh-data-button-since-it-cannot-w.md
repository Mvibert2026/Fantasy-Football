---
ID: FR-030
STATUS: SHIPPED
SOURCE: coordinator relay, mid-session, 2026-07-29
RAISED: 2026-07-29
---

## Request

Founder's own words, relayed into this session by the coordinator mid-task: **"We also can remove
that refresh data button at the top."**

This session did not receive the founder's message directly -- it arrived via the coordinator
relaying it into an in-progress dispatch, per the standing rule that no agent message (including a
relay) is itself the founder's consent for anything beyond doing the described UI work. Recorded
here as a real founder ask per this project's "capture every session, no exceptions" rule, not
treated as pre-authorizing anything else.

## Why it matters

The coordinator's stated reasoning (itself relaying the founder's point): "Refresh data" POSTs to
`/__refresh`, dev-server-only Vite middleware (`server/refresh.ts`'s `configureServer` hook -- it
never attaches under `vite build`). The founder's daily use has moved to the hosted static site
(`https://fantasy-football.soft-water-e755.workers.dev`, per `docs/CURRENT-STATE.md`), where the
button can only ever fail. That is the same present-but-inert problem that got Draft/Season mode
excluded from the standalone build (`docs/frontend-cloud-runbook.md`) -- a control that cannot
function should not be offered.

## Initial read

Verified directly: `vite.config.ts` only registers `refreshEndpoint()` as a plugin for the dev
server; a `vite build` output (confirmed by building this session's own changes and serving them
via `vite preview`) genuinely has no `/__refresh` route at all -- this is a build-time absence, not
a flaky network reachability question, so a compile-time flag (`import.meta.env.DEV`) is the
correct signal, not a runtime probe.

## Update, 2026-07-29 (same session)

Built: `RefreshData.tsx` now takes a `refreshAvailable` prop defaulting to `import.meta.env.DEV`;
the button renders only when true. The freshness line
(`exported <generated_utc> · snapshot fresh/STALE (<age>d old, max <max>d)`) is unconditional either
way, so hiding the (always-broken-there) button never also hides the fact it existed to report --
this was the coordinator's explicit hard requirement. Verified with a real production build +
`vite preview`: `frontend/e2e/artifacts/topbar-prod-2026-07-29.png` shows the button gone and the
freshness text intact; `frontend/e2e/artifacts/topbar-dev-2026-07-29.png` shows the button still
present under `npm run dev`, confirming the flag distinguishes the two correctly. 2 new tests in
`ui/__tests__/refresh.test.tsx`. Left `IN PROGRESS`, not `SHIPPED`, pending founder review of the
screenshots, same standard as FR-029.


## Shipped 2026-07-29 (frontend)

The button is removed and the freshness line kept, per the request. Verified by screenshot in both
Prep and Draft: `frontend/e2e/artifacts/topbar-no-refresh-button.png`,
`topbar-no-refresh-button-draft-mode.png`. `frontend/ui/components/RefreshData.tsx` and its test file
are deleted; `frontend/ui/__tests__/refresh-button-removed.test.tsx` is a regression guard.

**Numbering note.** The building agent branched from `main`, did not have this file, and filed the
same request again as FR-037 — colliding with this branch's real FR-037 (Export CSV/PDF inert). The
duplicate was dropped at merge and its evidence folded in here. Third instance of an id collision
caused by a worktree branching off a base that lacks the newer numbering.
