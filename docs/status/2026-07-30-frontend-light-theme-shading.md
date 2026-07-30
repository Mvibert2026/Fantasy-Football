# 2026-07-30 — frontend — light theme shading (design handoff item 5/8)

**Task:** implement `docs/design/LIGHT-THEME-SHADING.md` (design, 2026-07-31 handoff, item 5 of
8 — the only item with no dependency on the other seven, dispatched alone for that reason). The
spec answers the founder's only unprompted visual-comfort complaint: *"light view maybe needs a
touch up, it's very bright, it could use some shading."*

**Verdict: built, pending screenshot verification.** Commit `3d20984`. 356 tests passed, 42 files;
`npx tsc -b --noEmit` clean; `npm run build` clean.

## What changed

`frontend/ui/styles/tokens.css`, `:root[data-theme='light']` block only — dark's whole block is
untouched:

| Token | Before | After | Role |
|---|---|---|---|
| `--bg` | `#f4f6f8` | `#eef0f3` | page — grey, recedes |
| `--panel` | `#ffffff` | `#fbfcfd` | sits on the page |
| `--panel2` / `--s3` | `#eaeef3` / `#ffffff` | `#ffffff` (both) | raised — the row/tab you are on, and only that |
| `--line` | `#e1e6ec` | `#dde1e6` | border — same-level joins only |

`--line2`, and every semantic/position colour (`--acc`, `--down`, `--up`, `--live`, `--qb`, `--rb`,
`--wr`, `--te`, `--def`, `--soon`) are unchanged — the spec scopes this to surfaces only, and
"identical hues in both themes" in the spec reads as "this task doesn't touch hue mapping," not
"light's hex must equal dark's hex" (their lightness/chroma already differ per theme, correctly,
for contrast reasons).

Two new light-only helper vars, added inside the same light block:

```css
--row-alt: var(--panel);
--row-line: transparent;
```

`frontend/ui/views/Board.tsx` (`BoardRowLine`) now references these via `var(--row-alt,
transparent)` / `var(--row-line, var(--line))` — undefined in dark, so dark falls back to its
exact prior behaviour (transparent unselected rows, hairline `var(--line)` border) with **no
theme branch in component code**. Unselected rows alternate `transparent` / `var(--row-alt)`
(panel tint); the selected/expanded row keeps `var(--panel2)` (now raised, `#ffffff`) as the sole
"row you are on" — this operationalizes the spec's two named consequences ("alternating row tint
replaces row borders," "borders survive only at same-level joins") on the flagship table rather
than leaving them as token-level theory.

## What did not get the row-level treatment, and why

`DraftRoom.tsx`, `Availability.tsx`, `Opponents.tsx`, `Predictions.tsx` all have similar per-row
`borderBottom: '1px solid var(--line)'` patterns. They benefit for free from the token-level
border-colour change (`--line` is softer now) but did not get the zebra/border-removal rewrite
Board did. A full app-wide redundant-border audit — which hairlines now duplicate a tone step
that already separates two surfaces, everywhere in the app — was judged out of scope for one
session against real regression risk with no per-screen screenshot check for each one. One
specific redundant border was identified and deliberately left alone: Board's own header-bar
(`--panel`)/control-row (page-toned) divider, which per the spec's letter shouldn't need a
hairline once the tone step exists. Logged to `docs/ideas-inbox.md` rather than silently dropped.

## Verification

- `npx vitest run`: 356 passed, 0 failed, 42 files.
- `npx tsc -b --noEmit`: clean.
- `npm run build`: clean (hit a container-wide disk-full condition mid-session — `df -h /` showed
  2.2M/40M available at points; freed space by deleting an 854MB stale `nfl_test.db` copy inside
  this session's own scratchpad, `/tmp/claude-0/.../scratchpad/`, not by touching any other
  worktree — build succeeded after).
- Screenshots, `frontend/e2e/artifacts/` (new script `e2e/shot-light-theme-shading.mjs`):
  - `light-shading-01-board.png` — Board, light. Visible three-tier shading: grey page behind the
    sidebar/nav, near-white panel on the header bars, alternating panel/white row tint replacing
    the old uniform-white hairlined list.
  - `light-shading-02-player-card.png` — PlayerDetail sheet (Bijan Robinson), light. Board dims
    correctly behind the raised sheet.
  - `light-shading-03-availability.png` — Availability Explorer, light. Confirms the token change
    alone (no component edit) already reshades a second screen.
  - `light-shading-04-board-dark.png` — Board, dark, **taken on a second, fresh Playwright page**
    (not a reload of the light one) to sidestep a real bug found while writing the capture script:
    `page.addInitScript` persists across every navigation on the same page object, so a
    same-page light→dark toggle silently re-applied the light init script and produced a
    dark-labeled screenshot that was still light underneath. Confirmed correct: `data-theme`
    attribute absent, screenshot pixel-identical in layout to the pre-existing dark board.

## Findings for the report

- No hardcoded colours found duplicating the four surface tokens outside `tokens.css` itself
  (`grep` for the old and new hex values across `frontend/ui/**/*.tsx,*.css` came back clean
  except the token file).
- Files explicitly out of scope this session per the dispatch (another frontend agent's
  provenance/trace-mode work in progress): `PlayerDetail.tsx`, `AssistantDock.tsx`,
  `trace-fields.ts` — none needed a token-driven edit; `PlayerDetail.tsx` already only reads
  `var(--panel)` / `var(--panel2)`, which pick up the new shading automatically.
- Environment note for the runbook: `npm run build`'s static-asset copy step can fail with
  `ENOSPC` under concurrent multi-worktree load even when the working repo itself is small — the
  fix that worked was clearing this session's own `/tmp/claude-0/.../scratchpad/` of a stale large
  file, not anything in the repo.
