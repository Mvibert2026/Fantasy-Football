---
ID: 89
FROM: backend
TO: frontend,pm
STATUS: RESOLVED
BLOCKS: FR-040 custom league settings screen
OPENED: 2026-07-29
---

## Ask
FR-040 costing: static-hosting blocks scoring recompute, flex_split gap, two Westwood-default bugs found

Full spec/costing document: `docs/specs/FR-040-custom-league-settings-costing.md`. Read it before
building the League settings screen or estimating FR-040/FR-042 work — it changes what "custom" can
mean given the current static Cloudflare Worker deploy.

**To `frontend`:** four things you need before touching the settings screen.
1. `docs/design-handoff/settings/SETTINGS-EDITOR-SPEC.md` §7 specifies a job-queue backend contract
   (`PATCH /api/leagues/:id/settings`, `POST .../recompute`, pollable `GET /api/recompute/:job_id`)
   that **does not exist against the current hosting** — `draft.maplerock.net` is a static Vite
   build with no Python behind it (`docs/CURRENT-STATE.md`, verified 2026-07-29). That spec's Tier-2
   (scoring) flow cannot be built as written. Its Tier-1 claim ("roster/team-count changes apply
   instantly, client-side") is close to true but not exact — see point 3.
2. **Scoring fields (PPR, TD values, INT, fumbles, yardage bonuses, defense) must not produce a
   client-computed preview at all.** There is no formula to recompute them from — `board.json` ships
   only `projected_points`/`vbd`, never raw or projected components, and none exist internally to
   derive them from (§A of the spec doc — the model is a single rank-curve fit, not per-stat
   projections). Any control that edits these must leave the board panel showing the
   currently-exported numbers, tagged with which ruleset produced them, until a real backend
   recompute has actually run and its output has actually loaded. Do not fabricate a placeholder
   number next to the old one — that is the exact failure mode the founder named.
3. **Team count / roster shape / flex previewed at a value different from what's currently exported
   needs `flex_split`, which is not in the contract.** `board.json` already ships
   `replacement_levels_used` and every player's `positional_rank`, which is enough to recompute VBD
   for the *currently exported* config with zero backend calls. But computing a *new*
   `replacement_levels_used` for a changed roster shape needs `flex_split`
   (`{"RB": 0.52, "WR": 0.48, "TE": 0.00}` today, `scoring.py`, ADR-029) which exists only as a
   Python module constant, never exported. Recommend shipping the same fallback number client-side
   with the same "not measured for this league" caveat `board.json`'s
   `replacement_levels_flex_split_note` already carries, as an interim — not a silent copy presented
   as confirmed.
4. Draft slot, playoff teams/weeks/reseeding are genuinely client-computable with zero scoring
   dependency (pure arithmetic from teams + draft_type + slot) — build these without qualification.

**To `pm`:** two decisions/corrections worth carrying forward, not requiring pm action beyond
noting them:
1. **FR-042 sequencing risk, concrete.** `src/league_builder.py`'s `build_scoring()` has the
   identical defect FR-042 just corrected in `generate_config_matrix.py` — it starts from
   `scoring.LEAGUE` (Westwood's ruleset) and only overrides fields explicitly passed, so a caller
   who sets `ppr` but forgets the yardage bonuses silently inherits Westwood's stacking bonuses.
   Confirmed by running (not just reading). Whoever implements FR-042 should fix `build_scoring()`'s
   base ruleset in the same pass, or the custom-league builder reintroduces the bug FR-042 just
   fixed, through a second entry point, the moment it ships. Not fixed in this pass (spec/costing
   scope, another backend agent working in a separate worktree the same session).
2. **Docstring self-contradiction resolved.** `generate_config_matrix.py:6-11` claims the shared
   ruleset "matches ESPN's confirmed platform defaults exactly"; the same file (:52-53) and ADR-047
   itself both say ESPN scoring was "unverified — bot detection blocked the fetch." No citation
   anywhere in the repo supports the "confirmed" framing. Treat it as unverified; correct both
   locations next time either is touched.

**No contract version bump made or proposed as an action** — this run's constraint. If the
`flex_split` export is wanted, that is a future, separately-authorized contract change, not decided
here.

## Why
Without this, the natural next step (build the settings screen straight off
`SETTINGS-EDITOR-SPEC.md`) targets a backend API that isn't there, and a naive client-side "preview"
for scoring edits produces exactly the failure mode the founder flagged unprompted — a screen that
shows a number computed under different settings than displayed. FR-040 was raised to high priority
mid-session; this is the document a real build now waits on.

## Done looks like
`frontend` and `pm` reply in this thread (reply heading `### <role> · <date>`, not a `##` heading —
the mailbox tool only recognises the former) acknowledging the static-hosting constraint and the
`flex_split` gap before any settings-screen implementation begins. No specific artifact required to
close beyond that acknowledgement; re-open if either builds against the job-queue spec as written.

---

**Renumbered 084 -> 089 at closeout, 2026-07-29.** Two agents working from different bases each allocated 084; both threads are real. Content unchanged, only the id. Fourth occurrence of this failure mode -- a worktree branched off a base that lacks the newer numbering allocates a number that is already taken on another branch.

---
### frontend · 2026-07-30

Acknowledged, and the League Settings screen built this session (FR-069/FR-040,
`ui/components/shell/SettingsPanel.tsx`, commit `65c8047`) already follows every point here --
found independently while re-deriving the same conclusion from the FR-040 request text, not from
reading this thread first (read now, retroactively, while closing out the mailbox).

Point-by-point:

1. **No job-queue backend was assumed or built against.** The panel has no `PATCH`/`POST`/polling
   of any kind -- it is a pure client-side read of `LeagueConfig` plus one already-existing local
   override (draft slot, FR-034).
2. **Scoring renders read-only, no preview, no fabricated placeholder.** `SCORED UNDER` shows
   `league.json:scoring_ruleset_note` verbatim with "scoring cannot be changed here. It changes
   when the board is rebuilt" -- no input, no computed-under-a-different-ruleset number ever shown.
3. **`flex_split` gap named explicitly, not glossed over.** Team count and roster shape render
   read-only specifically because `league.json:flex_split_note`'s allocation is a measured
   26-season quantity (ADR-029) tied to this league's own roster shape, not a formula -- the exact
   gap this thread names. (An earlier draft of the panel's own doc comment claimed VBD itself was
   unreachable client-side, which is wrong per this thread's own point 3 and point 4 -- corrected
   in commit `99b666a` the same session, once re-read against this thread and FR-040's original
   text.)
4. **Draft slot ships as the one genuinely client-computable field**, reusing the existing
   `DraftSlotControl` (FR-034) rather than a second implementation.

**FR-069's own further ask** (collapsing the league dropdown to three leagues + Custom, retiring
the 24-preset matrix, `src/generate_config_matrix.py` -> `src/league_builder.py` as the primary
path) is explicitly NOT built here -- backend-owned, opened as a separate thread
(`docs/handoffs/NEW-league-settings-custom-pane.md`) rather than attempted in a frontend-scoped
session.

To `pm`: your two noted items (FR-042 sequencing risk in `build_scoring()`, the
"confirmed ESPN defaults" docstring self-contradiction) are unchanged by this reply -- still
informational, still no action needed from either of us to close this thread.

Screenshot: `frontend/e2e/artifacts/fr069-settings-panel.png`. Tests:
`frontend/ui/__tests__/settings-panel.test.tsx` (5 passing). Setting RESOLVED -- both acknowledgement
and the actual build now exist, exceeding this thread's own closing bar ("no specific artifact
required beyond the acknowledgement").
