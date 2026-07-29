# 2026-07-28 — backend — shard the shared append-only doc logs

## What changed

`docs/status.md`, `docs/founder-requests.md`, and `docs/CURRENT-STATE.md`'s "Build state" table
were the three most contended shared files in the repo — every parallel session wrote to one or
more of them, which is exactly the pattern `docs/reviews/fable-workflow-2026-07-27.md` (work
orders W3/W4) already diagnosed as the project's main source of merge conflicts, after two
sessions nearly collided on `CURRENT-STATE.md`. This session implements W3 and W4, plus extends
the same idea to `founder-requests.md`, which W3/W4 didn't cover.

Three different fixes for three different conflict shapes, not one fix applied uniformly:

1. **`docs/status.md`** (pure append log) → frozen; `docs/status/YYYY-MM-DD-role-slug.md` per
   session; `tools/status_log.py sync` generates `docs/status/INDEX.md`. This is the literal
   "shard into dated files" pattern.
2. **`docs/founder-requests.md`** (thread-shaped: FR-NNN numbers referenced 146 times across 40
   other files, and a request's `Status:` gets mutated by later sessions — concurrent-edit-to-
   one-blob, not append) → frozen; one file per request at `docs/founder-requests/FR-NNN-slug.md`,
   same pattern as `docs/handoffs/NNN-slug.md`, with the same staged-`NEW-*.md` + `sync`-time ID
   allocation `tools/handoffs.py` uses (W1), seeded past the archive's highest number (`FR-017`).
   `tools/founder_requests.py sync` generates `docs/founder-requests/INDEX.md`, grouped by status.
3. **`docs/CURRENT-STATE.md`** — deliberately *not* sharded into dated files. It's synthesized
   "current truth," edited in place by design (`CLAUDE.md`: "never append a new section").
   Regenerating it from per-session deltas would just move the merge problem into the generator.
   Only the actually-measurable "Build state" table is now generated, via a new `--apply` flag on
   `tools/state.py` that rewrites the content between `<!-- BUILD-STATE:START -->` /
   `<!-- BUILD-STATE:END -->` markers in place, leaving the rest of the doc (including the two
   rows that aren't measurable by a single command — Agent infrastructure, Frontend location) hand
   -maintained. Also fixed a latent bug while wiring this in: `tools/state.py` hardcoded the
   literal string `` `master` `` for the branch name regardless of the real branch (this repo's is
   `main`) — never previously exercised because the tool only printed to stdout for manual paste.

None of the three old files were rewritten or migrated — they stay in place as the archive,
unmodified except for a freeze-notice header pointing at the new location, per the explicit
instruction not to lose history.

## What still requires a shared-file append

- **`docs/decisions.md`** — the ADR log. Same append-only shape as the old `status.md`, and
  already has its own collision history (ADR-048, per `RECONCILIATION-2026-07.md`) and its own
  allocator (`tools/handoffs.py adr next`, which scans `docs/decisions.md` + `docs/adr-drafts/`).
  Out of scope for this session (not one of the three files named), but it's the same failure mode
  and hasn't been fixed. Flagging, not fixing.
- **`docs/handoffs/NNN-slug.md` thread files themselves** — replies within a single already-open
  thread are still a shared append target if two sessions touch the *same* thread in the same
  round. Narrow blast radius (one thread, not the whole mailbox) and already a known, accepted
  limitation — `docs/handoffs/README.md` rule 8 ("a pull conflict is not yours to resolve alone")
  exists for exactly this case.
- **Cross-worktree ID allocation races** — both the handoffs allocator and this session's new
  founder-request allocator use the same "hard-fail if the destination already exists" defense,
  not true cross-worktree coordination. Thread 076 already flagged this as open and unresolved for
  handoffs; the same caveat now applies identically to `tools/founder_requests.py`. Rare in
  practice (per 076's own assessment), but real.
- **`docs/status/` and `docs/founder-requests/` `INDEX.md` files** — not append targets (they're
  fully regenerated, never hand-edited), but two sessions running `sync` around the same time and
  both pushing will still produce a trivial merge conflict on the generated file itself, resolved
  by just re-running `sync` after the merge. Lower-stakes than the old failure mode: nothing is
  lost, the fix is mechanical, and it doesn't depend on either session's judgment about which
  content wins.

## Verification

- New tooling tests: `tests/test_status_log.py`, `tests/test_founder_requests.py`,
  `tests/test_state.py` — 16 tests, all passing.
- Full backend suite (`pytest -q`, real `data/nfl.db`) run post-change to confirm nothing else
  regressed — see this session's commit message / PR for the pass count.
