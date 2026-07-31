# 2026-07-30 — backend — thread/FR ID allocation moves to date+slug (ADR-064)

**Task:** founder-approved directive, relayed via dispatch — replace counter-based ID allocation
in `tools/handoffs.py` / `tools/founder_requests.py` with a scheme that structurally cannot
collide across git worktrees, without renaming or renumbering any of the ~135 existing threads or
~120 existing FRs.

## What shipped

New threads/FRs are named `docs/handoffs/YYYY-MM-DD-slug.md` and
`docs/founder-requests/FR-YYYY-MM-DD-slug.md`. Allocation (`new_thread_filename()` /
`new_request_filename()`) is a pure function of (today's date, this thread's own slugified
subject) claimed atomically via `os.O_CREAT | os.O_EXCL` — no shared counter, no git ref scan.
Same-day-same-slug within one working tree deterministically gets a `-2`/`-3`/... suffix instead
of failing. The one case a single tree can't disambiguate — two separate worktrees choosing the
identical subject on the identical day — is no longer a silent collision either: the filename is
now the identifier, so it becomes an ordinary git same-path merge conflict instead of two
different filenames quietly carrying the same `ID:`.

Existing `NNN-slug.md` / `FR-NNN-slug.md` files: untouched, never renamed. `load()` in both tools
now matches either filename shape so old numeric threads keep resolving exactly as before
(verified: `docs/handoffs/119-*.md` still loads/sorts/appears in `inbox`/`sync`/`check`).
`next_free_id()` in both tools is kept (still tested, still answers "highest legacy number
claimed" honestly) but is no longer wired into `cmd_new`/`ingest_pending` — dead as an allocator,
alive as a query. `adr_next()` is explicitly out of scope, unchanged.

## The mid-task addition (coordinator-directed)

Running `check` against the real repo surfaced pre-existing collisions from before this fix —
threads 093/094/109/110/111/112 (some with a filename/frontmatter-ID mismatch on top, from a
rename-without-restamp pattern — see `docs/known-id-collisions.md`), ADR-054/ADR-055 (two
different real decisions recorded under one number — a content problem, not a naming one), and
FR-029/FR-030. Verified pre-existing via `git stash` before touching anything. Per coordinator
direction: recorded as a frozen, dated exception registry
(`KNOWN_LEGACY_ID_COLLISIONS`/`KNOWN_LEGACY_ADR_COLLISIONS` in `tools/handoffs.py`,
`KNOWN_LEGACY_FR_COLLISIONS` in `tools/founder_requests.py`) so `check` goes green on today's debt
and stays red on anything new — pinned by test so growing the registry to hide a future collision
is a visible diff, not silent. Did not attempt to reconcile ADR-054/ADR-055's actual content
ambiguity myself — no authority to pick a winner unilaterally — opened
`docs/handoffs/2026-07-30-adr-054-and-adr-055-each-record-two-different-re.md` to PM instead.

## Evidence

- `python3 -m pytest tests/test_handoffs.py tests/test_founder_requests.py -q` — **36 passed**
  (was 27 handoffs + a subset — old counter-allocation tests rewritten for the new scheme; no
  legacy-resolution or cross-branch-backstop test changed).
- `python3 tools/handoffs.py check` — exit 0 (was exit 1, confirmed pre-existing failure via
  `git stash`).
- `python3 tools/founder_requests.py check` — exit 0 (was exit 1, same pattern, not previously
  wired into the test suite at all — still isn't; flagged as a gap, not fixed here, see
  `docs/ideas-inbox.md`).
- Full suite: see this session's commit for the final count (kicked off before session close;
  the handoffs/founder_requests subset above is the code this session actually touched).
- ADR-064 in `docs/decisions.md`, allocated via `tools/handoffs.py adr next` (returned 64,
  independently re-verified after the coordinator reported the same number).

## Docs touched

`docs/decisions.md` (ADR-064), `docs/known-id-collisions.md` (new), `docs/handoffs/README.md`,
`CLAUDE.md` (tight edit, one paragraph), `docs/CURRENT-STATE.md` (Agent infrastructure row +
"Top open items" #15, in place — the old #15 said "do not silence" the ADR-054/055 check failure;
updated to say what actually changed and why, with the still-open content question now tracked
separately).

## Not done / left open

- ADR-054/ADR-055's actual disambiguation (whose content is canonical) — PM's call, threaded.
- `tools/founder_requests.py check` still isn't wired into the automated test suite the way
  `tools/handoffs.py check` is (`test_mailbox_health`) — noted, not fixed, logged to
  `docs/ideas-inbox.md`.
