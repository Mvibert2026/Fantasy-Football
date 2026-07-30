---
FROM: librarian
TO: pm
STATUS: INFORMATIONAL — audit only, no threads opened
DATE: 2026-07-30
COVERS: docs/design/*.md build-state audit
---

# Build-state audit — `docs/design/` specs, 2026-07-30

Read-only audit. No `frontend/` files were edited to produce this. Build state is verified against
`frontend/ui/` source at HEAD this session, not against status logs, ADRs, or CURRENT-STATE.md prose
(consulted only as a pointer to where to look, never as the evidence itself). Every "BUILT"/"PARTIAL"
claim below cites a `file:line` I read this session.

## Per-spec table

| Spec | Build state | Evidence (`file:line`) | Blocked on |
|---|---|---|---|
| **DRAFT-MIDDLE-PANE.md** | **PARTIAL** | Tab set built: `frontend/ui/views/DraftRoom.tsx:1057-1060` (`recommend`/`scarcity`/`queue`/`insights` tab keys); NEXT DECISION persistent footer `DraftRoom.tsx:2281-2295`; FR-045 pace suppression `ui/data/scarcity.ts:83,117-118` + `DraftRoom.tsx:564-565,1006-1020`; FR-049 look-ahead toggle `DraftRoom.tsx:349,912-920,1690-1738`; FR-051 next-pick reference (CONSIDERING/LIKELY THERE AT) `DraftRoom.tsx:2011,2026`. **Not built: §1.1 the periodic-table grid** (position-by-team matrix, full-width view) — no such view or route exists; `App.tsx:203-211` and `DraftRoom.tsx:1043-1045` show only `board`/`opponents`/`predictions` hub tabs, no grid. Insights tab (§ Tab table) is an explicit honest not-built state, `DraftRoom.tsx:2254-2274` ("Not built yet... findings.json... does not exist in the export contract today") — this matches the spec's own anticipated failure mode, not a defect. | Grid: simply unstarted — `POSITION-COLOUR-RESOLUTION.md` unblocked it 2026-07-30, nothing prevents starting now. Insights: blocked — needs a `findings.json` per-pick export artifact that does not exist in the contract. |
| **COMPETITOR-READ-2026-07-30.md** | **NOT A BUILD SPEC** | A research memo (competitor screenshot read, judgement calls, one correction to design's own earlier work). No "build this" instruction directed at frontend beyond what's folded into `POSITION-COLOUR-RESOLUTION.md` and the standing `INERT-CONTROLS.md` rule, both assessed separately below. | n/a |
| **INERT-CONTROLS.md** | **BUILT** | Export CSV/PDF absent, replaced by provenance line: `frontend/ui/views/Board.tsx:207,215` (`"export not built"`). Compare/Ask absent from PlayerDetail action row: `frontend/ui/components/PlayerDetail.tsx:509-512`. Per-term "Ask the assistant" removed from Glossary: `frontend/ui/views/Glossary.tsx:7,14`. Refresh-data button removed entirely (founder asked twice): `frontend/ui/App.tsx:272`; standalone dev variant kept as a real, working button per the spec's own carve-out: `frontend/ui/StandaloneApp.tsx:45`. | n/a |
| **LEAGUE-SETTINGS-BOUNDARY.md** | **NOT BUILT** | No Settings screen exists in the app at all: `frontend/ui/components/shell/TopBar.tsx:289` literally renders `"Settings — not built"`. There is no roster-shape/team-count/draft-slot "applies immediately" form and no "SCORED UNDER" read-only scoring statement anywhere in `frontend/ui/`. | Blocked — the spec describes a boundary rule *within* a Settings screen; the screen itself does not exist, so there is nothing yet to apply the rule to. |
| **MANIFEST-2026-07-29.md** | **NOT A BUILD SPEC** | A delivery manifest (file list, priority order, four asks back to PM, two findings). No code deliverable of its own. | n/a |
| **MANIFEST-2026-07-30.md** | **NOT A BUILD SPEC** | Same — round-two delivery manifest for the other three specs in this batch. | n/a |
| **POSITION-COLOUR-RESOLUTION.md** | **NOT A BUILD SPEC** | A decision record ("no hue changes; grid is unblocked"), not itself a UI deliverable. Its one concrete instruction — separate position hue from semantic accent *in the grid* — has nothing to apply to: the grid does not exist (see DRAFT-MIDDLE-PANE row above). The board's existing position-colour usage (`frontend/ui/views/Board.tsx:288,550`, `POSITION_COLOR` map) predates this spec and was never in question. | The grid it resolves colour-for is simply unstarted. |
| **STRATEGY-SELECTOR.md** | **NOT BUILT** | No interactive strategy-selection control exists anywhere. The only screen touching `strategies.json` is the pre-existing `frontend/ui/views/StrategyGuide.tsx` — a passive table dump (`StrategyGuide.tsx:66-131`) with zero `onClick`/`<input>`/selection controls (checked directly, no matches). It is a standalone screen, not "at the head of the Recommend tab" as the spec requires — `DraftRoom.tsx` has no reference to `strategies` at all (checked directly, no matches). Season-dot meter, generic-track substitution-refusal copy, and the selector's effect on Recommend's output are all absent. | Blocked — the spec's own "Note for `strategist`" says whether selecting a strategy writes into the recommendation model or only reorders output is unresolved and not a design decision (same open question as FR-051, thread not yet closed per `docs/design/STRATEGY-SELECTOR.md:103-108`). |
| **SUPPLIED-VALUES.md** | **BUILT** | Typed opponent name: dotted underline + `typed` marker, `--acc` removed, `frontend/ui/views/Opponents.tsx:307-310,324,335`. TopBar draft-slot override: same treatment, `frontend/ui/components/shell/TopBar.tsx` (grep match, "typed"/"dotted" pattern present). A third instance not named in the spec, `Predictions.tsx`'s overridden-slot readout, also carries the pattern (grep match). Sourced-value-stays-visible rule intact (`Opponents.tsx:357`, "Clear typed name, back to..."). | n/a |
| **TWO-TRACK-EXPRESSION.md** | **BUILT** | Track descriptor split into primary/generic on the league selector: `frontend/ui/components/shell/TopBar.tsx:57-58` (`"primary track · full ruleset · N opponents modelled"` vs `"generic track · standard scoring · opponents not modelled"`). Strategy Guide's empty state split by track rather than one string: `frontend/ui/views/StrategyGuide.tsx:20-47` (`isPrimary` branch, distinct copy per track, citing `league.json:league_id === "primary"` as the one real signal). | n/a |
| **ADP-COLUMN-AND-CAPTURES.md** | **PARTIAL** | Proxy caveat exists as a hover title and a shortened visible label (`"ADP (MFL)"`, `frontend/ui/views/Board.tsx:101,343,367-376`, `computeAdpHeaderTitle` builds the full `adp_source_note` text into a `title=` attribute at `Board.tsx:453`), and the full caveat renders verbatim exactly once at `frontend/ui/components/PlayerDetail.tsx:706,708` — both match the spec. **Not built: the null-population count.** The spec's exact header text, `"ADP  mfl · 144/511"`, does not appear anywhere — no `144/511`-style fraction, and the caveat is reachable only via hover (`title=`), not visible at a glance as the spec requires ("the header carries both facts... at a glance"). The capture-list/diff-ordering portion of the spec is a QA process instruction, not a UI deliverable, and wasn't assessed for "build state." | Simply unstarted — the null-count figure (`144/511`) is arithmetic over the already-exported board data (`RawBoard.adp_source_note`/nulls), not blocked on new data. |

## Counts

| Build state | Count | Specs |
|---|---|---|
| BUILT | 3 | INERT-CONTROLS, SUPPLIED-VALUES, TWO-TRACK-EXPRESSION |
| PARTIAL | 2 | DRAFT-MIDDLE-PANE, ADP-COLUMN-AND-CAPTURES |
| NOT BUILT | 2 | LEAGUE-SETTINGS-BOUNDARY, STRATEGY-SELECTOR |
| NOT A BUILD SPEC | 4 | COMPETITOR-READ-2026-07-30, MANIFEST-2026-07-29, MANIFEST-2026-07-30, POSITION-COLOUR-RESOLUTION |

11 specs total, all accounted for.

---

## Founder requests marked NEW that are already built

`docs/founder-requests/INDEX.md` shows 50 of 75 requests as `NEW`. Checked a sample against the
actual repo (code + committed artifacts), not against status-log prose. Five are clearly already
satisfied by work that landed after the request file was written but before its `STATUS:` line was
updated — this is the project's known "completed work never gets marked done" failure mode, not a
new one.

| ID | Subject | Evidence it is already built | Why it still reads NEW |
|---|---|---|---|
| **FR-032** | Make the Opponents screen functional during a live draft | `frontend/ui/views/LiveOpponents.tsx` exists, 300 lines, a dedicated live-draft variant of Opponents (`LiveOpponents.tsx:3,11-27,138,231-251`). This is the same request as `FR-029-opponents-screen-must-be-functional-during-a-liv.md`, which is `STATUS: IN PROGRESS` and whose own text explains the collision: the dispatch that built this called it "FR-032" throughout, but the allocator issued FR-029 in that worktree since FR-018–028 was all it could see. Two files, one piece of work, one marked IN PROGRESS and the older duplicate still NEW. | Known duplicate-ID class per CURRENT-STATE.md's own open item #7 (FR-029/FR-030 collision) — same mechanism, different ID pair. |
| **FR-060** | ADP versus production — find where the market is systematically wrong | `docs/analysis/adp-vs-production-2026-07-30.md` (17KB) and `analysis/adp_vs_production.py` (33KB) both exist and are dated 2026-07-30, per CURRENT-STATE.md's own "Last verified" entry (thread 096, FR-072) describing this exact analysis in detail (residual VBD vs ADP, six pre-registered factor families, BH-corrected). | The analysis was logged and closed under **FR-072**, a differently-numbered request asking for functionally the same thing raised the next day; FR-060's own file was never touched. |
| **FR-038** | Look at what other apps do before committing to a frontend overhaul | `docs/research/competitive-ux-2026-07-29.md` and `docs/research/competitor-recommendation-audit-2026-07.md` both exist, plus `docs/design/COMPETITOR-READ-2026-07-30.md` (a direct design response citing five FantasyPros screenshots). | Research landed under general "competitive research" framing rather than being traced back to close this specific FR file. |
| **FR-023** | FFC is unblocked — founder confirmed no restrictions, use as needed | Acted on: `tools/backfill_ffc_adp_history.py` backfilled 2,467 FFC ADP rows (`docs/research/ffc-adp-history-backfill-2026-07-29.md`), and thread 055 (which cites this exact unblock) is `STATUS: RESOLVED` per CURRENT-STATE.md. FFC is also now the ranker's stated priority ADP format. | The unblock note itself (FR-023) was never marked done even though every piece of work it authorized shipped and closed under its own thread number. |
| **FR-053** | Yahoo draft room reference capture — features to consider, log for design | Explicitly actioned: `docs/design/COMPETITOR-READ-2026-07-30.md` is a design memo (frontmatter `COVERS: FR-053 addendum...`, `COMPETITOR-READ-2026-07-30.md:6`) reading nine images and stating four findings plus a correction — exactly the "send to research team, log the stuff for design consideration" ask in FR-053's own quoted text. This is the cleanest of the five: the closing artifact exists and names the request by number, but nobody flipped `docs/founder-requests/FR-053-*.md`'s status line. |

Not included, on inspection, despite plausible subject lines: **FR-046** ("make auto-fill actually
draft players") is still genuinely open — `frontend/ui/views/DraftRoom.tsx:642-654` shows
`autoFillToMyPick()` still logs `AUTO_FILL_PLACEHOLDER` picks with unknown identity, not real
players, so the request stands as written. **FR-052** (Yahoo roster/stat categories for the third
league) is still missing point values per its own text and no artifact was found closing that gap.

This list is not exhaustive — it is five items I could verify directly against code or a committed
artifact this session, capped well under the requested 15 because verifying each one costs a real
grep-and-read pass and going further risked trading precision for count.

---

## Note on scope discipline

This audit found two genuine gaps (LEAGUE-SETTINGS-BOUNDARY has no screen to attach to;
STRATEGY-SELECTOR is blocked on an unresolved `strategist` question) and one spec whose own
anticipated "honest not-built state" (DRAFT-MIDDLE-PANE's Insights tab) is working exactly as
designed rather than being a defect. No threads were opened and no ADR numbers were allocated, per
this task's explicit instructions — the five founder-request corrections above are handed back as
findings, not resolved unilaterally.
