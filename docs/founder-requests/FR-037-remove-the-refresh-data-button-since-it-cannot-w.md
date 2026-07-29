---
ID: FR-037
STATUS: SHIPPED
SOURCE: pm relay, 2026-07-29 (second ask, first was missed)
RAISED: 2026-07-29
---

## Request
Remove the Refresh data button since it cannot work on the hosted static site

Relayed via PM/coordinator dispatch mid-session, not captured as the founder's own transcript
text in this repo. As relayed: he asked for this once already today and it was never actioned; he
raised it a second time after seeing the button still live on the deployed site
(`draft.maplerock.net`). The button calls `/__refresh`, a dev-server-only endpoint
(`server/refresh.ts`) that a production `vite build` never ships, so on the hosted static site
every click can only fail.

## Why it matters

Present-but-inert is the exact failure mode this project's own standing rule (docs/CURRENT-STATE.md,
"Not built / null-stated" and the Season/Draft-mode-on-frozen-file precedent in the standalone
build) says not to ship. A control the founder can see and click, that can only ever fail, is worse
than no control — it reads as broken rather than absent.

## Initial read

**IMPORTANT — a real cross-branch collision was found while doing this, and is being logged here
rather than resolved unilaterally (per the project's own escalation rule for genuine collisions).**

This exact request was **already built once**, independently, on branch
`claude/pm-agent-setup-gobxa0` (and its own worktree branch `worktree-agent-a575f78efa5c23088`),
commit `59b58cf` ("...drop the dev-only Refresh data button on production builds (FR-030)"), merged
into that branch's own history at `2a1a735` — **but that branch was never merged into `main`**
(`origin/main` is still at `4980b29`, confirmed via `git merge-base --is-ancestor`), so this
worktree (built from `main@4980b29`) never saw it. Two things follow from that:

1. **A real FR-030 already exists in this repo, and it is a different subject** (`FR-030-run-the-
   rankings-validation-at-maximum-effort-ac.md`). The sibling branch's `59b58cf` created its *own*
   `FR-030-remove-the-refresh-data-button-since-it-cannot-w.md` — the same number, a different
   subject, on a different unmerged branch. This is a genuine ID collision, not a numbering
   mistake on either side individually; each branch's allocator ran against a working tree that
   didn't have the other's file yet. Filed fresh here as FR-037 rather than overwriting the real
   FR-030 in this tree or guessing which FR-030 file "wins."
2. **The two implementations differ architecturally, not just cosmetically.** The sibling branch
   kept `RefreshData.tsx` and gated the button behind `import.meta.env.DEV` (visible in `npm run
   dev`, absent from any `vite build`). This worktree, per the coordinator's explicit instruction
   this session, **deleted `RefreshData.tsx` and its test entirely** and replaced the mount with an
   inline `FreshnessNote` in `App.tsx` (keeping only the generation-timestamp line, following
   `StandaloneApp.tsx`'s existing `StandaloneFreshnessNote` pattern). Both remove the button from
   the hosted site; they are not the same code, and naively merging both branches into `main` would
   conflict on `App.tsx` and `RefreshData.tsx`.
3. Separately, and larger: the same sibling-branch commit also introduces `LiveOpponents.tsx`, a
   Draft-mode-only reimplementation of the Opponents tab (reading live `DraftState.picks` instead
   of `rosters.json`) that does not exist in this worktree at all — this worktree's Draft-mode
   Opponents tab still wraps the same `Opponents.tsx` used in Prep mode (`AdaptedOpponentsPane`),
   which this session extended for FR-036 (typed names). **Whoever merges these branches needs to
   decide which Opponents-in-Draft-mode implementation is kept** — that is a design decision, not
   a merge-conflict resolution, and is well outside this session's authority to make unilaterally.

Built this session (this worktree only): `App.tsx` no longer imports or mounts `RefreshData`;
`components/RefreshData.tsx` and `__tests__/refresh.test.tsx` deleted;
`ui/__tests__/refresh-button-removed.test.tsx` added (asserts no "Refresh data" button renders
anywhere, and the freshness note still does). 231/231 frontend tests pass, `tsc -b --noEmit` clean.
Screenshot: `frontend/e2e/artifacts/topbar-no-refresh-button.png`.
