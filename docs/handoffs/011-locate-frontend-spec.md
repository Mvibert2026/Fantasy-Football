---
ID: 011
FROM: pm
TO: founder, frontend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: 007
---

## Ask

Find and commit two artifacts that the project treats as authoritative but that do not exist in this
repository:

1. **`FRONTEND-SPEC.md`** — the ~38,000-character implementation spec. Commit to `docs/FRONTEND-SPEC.md`.
2. **`Draft_Assistant_reference.dc.html`** — the reference prototype from Claude Design. Commit to
   `docs/design-reference/`, split per screen if it is a single file containing several.

Likely locations, in order: the frontend working copy (uncommitted or on a branch), a Claude Design
project export, or a chat attachment in a prior session. If it exists only in a chat, download it now
— chat attachments are not durable storage.

## Why

This was raised by `librarian` reading the repo, and it is a real hole rather than a bookkeeping one.

The project's own operating model names `FRONTEND-SPEC.md` as the source of truth for the port, and
`docs/design-fidelity.md` specifies that the fidelity harness diffs the running app against a
**pinned** reference committed to the repo. Neither is possible right now: thread 007 cannot be built
without the prototype, and Frontend has been porting against a document that no session other than
its own can read.

This is also the concrete form of the design gap. Design produces the spec, it lands somewhere
outside version control, and every other agent is blind to it. Committing it does not fix the
handoff, but it does mean the spec stops being a single point of failure living in one session's
context.

One thing to check while retrieving it: whether the spec still matches what Design currently shows.
If the spec predates recent design changes, commit it anyway with a dated note — a pinned stale
reference is still far better than no reference, because at least drift becomes measurable.

## Done looks like

Both files committed. Reply with paths and the spec's character count so we can confirm it is the
full document and not a truncated copy. Then 007 unblocks.

---
### frontend · 2026-07-28

Confirming founder's half of this ask (locating and committing the files) with a direct fact-check,
independent of any prior session's claim that this was already done. This reply resolves only the
"are these files present, committed, and full-length" question; it is not a design-fidelity review.

**Verified directly this session:**

- `docs/FRONTEND-SPEC.md` — `wc -c` reports **38,222 characters**, matching this thread's own
  "~38,000-character" description. Not truncated: the file's own table of contents runs sections 1
  through 11 (`# 1. Non-negotiable principles` through `# 11. Prototype data caveat`), and section 11
  ("Prototype data caveat") reads as a genuine closing section, not a mid-thought cutoff.
- `docs/design-reference/prototype.dc.html` (361,376 bytes) plus the four reference screenshots
  named in this thread's "done looks like":
  `docs/design-reference/reference/01-draft-board.png`,
  `docs/design-reference/reference/02-draft-opponents.png`,
  `docs/design-reference/reference/03-draft-predictions.png`,
  `docs/design-reference/reference/04-player-detail.png`.
- Both are git-tracked, not just present on disk: `git ls-files docs/FRONTEND-SPEC.md
  docs/design-reference/` lists them (along with additional design-reference material beyond what
  this thread asked for — see below). `git log --oneline -- docs/FRONTEND-SPEC.md
  docs/design-reference/` shows a single commit, `ee30e6f20b42f1ee73dbb5cb302def5b9978d495`
  ("Checkpoint: accumulated design/handoff/doc work before frontend session", 2026-07-26 16:58:49
  -0600), already on `main`.
- Bonus, not asked for in this thread but relevant to 007: the same commit also carries
  `docs/design-reference/mock-lab/` (7 `.dc.html` files + 7 reference PNGs) and
  `docs/design-reference/settings/` (6 `.dc.html` files + 6 reference PNGs), plus
  `docs/design-reference/fidelity.py` and `docs/design-handoff/` (screen-by-screen handoff notes,
  JSON specs for tokens/formulas/API contract/acceptance checks). None of this was reported missing
  by this thread, but it means 007's fidelity harness has more pinned reference material available
  than the original ask described.

**Staleness gut-check (shallow, as the ask allowed — not a full audit):**

One concrete drift found, worth flagging plainly rather than burying: `FRONTEND-SPEC.md` §6.2 and
§7.3 describe `global_tier` and `sim_generated_at`/`sim_settings_hash` as fields the board API
contract returns (line 447: `"position_tier": 1, "global_tier": 1`; lines 291/412/430/484 for the
sim fields). `docs/CURRENT-STATE.md` (thread 058 audit, thread 071/072) confirms none of these three
fields exist in the real `board.json` export today — threads 071 and 072 are still `OPEN`, not
filled with a client-side substitute. So the spec is describing an API shape that was never built on
the backend side, not a shape that changed out from under the frontend. Separately, the spec has
zero mentions of `suspension_flag`/`suspension_games`/`scoring_format`/`roster_status`/
`snapshot_stale` (ADR-050/051/052/053, thread 074) — all landed on the backend after this spec was
written (spec committed 2026-07-26; those contract fields landed 2026-07-27) and are additive, not
contradictory, since the spec never claimed those fields didn't exist. Neither gap is a truncation
or corruption concern; both are "spec is a point-in-time UI/behavior document, not synced to the
live data contract" — expected drift, not a defect in this thread's deliverable. I did not do a
deeper pass (e.g. comparing every screen section against current `frontend/ui/` build state) —
`docs/CURRENT-STATE.md`'s "Not built / null-stated" section already tracks the build-completeness
gap (Predictions tab, Season mode, Settings editor, Mock Lab UI, Compare tray) separately from this
thread's narrower "does the file exist and is it full" question.

**Resolution:** both artifacts exist, are committed, and are full-length. Founder's half of this ask
(locate + commit) is confirmed done — no further action needed from founder on this thread. 007
(design fidelity harness) can now unblock on artifact availability; the `global_tier` /
`sim_generated_at` gap above is a pre-existing backend-contract gap for 007 to account for, not a
blocker on the harness itself having a pinned reference to diff against.

Setting `STATUS: RESOLVED` as the `TO: frontend` addressee, per this thread's own protocol that only
the `TO:` role may resolve.
