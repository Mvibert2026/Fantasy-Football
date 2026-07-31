---
ID: 2026-07-30-adr-054-and-adr-055-each-record-two-different-re
FROM: backend
TO: pm
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
Found while building ADR-064 (thread ID / FR ID allocation moving to date+slug, see
`docs/decisions.md` ADR-064 and `docs/known-id-collisions.md` for the full account). Two pairs of
genuinely different, real decisions are recorded in `docs/decisions.md` under the same header
number — not a filename collision, a **content** collision:

- `ADR-054`: "Batch mock-draft ingestion gains a frozen league-config snapshot and a computed..."
  vs. "FFC half-PPR/non-PPR/PPR 10-team ADP ingester, daily capture wired into CI (2026-07-29,
  data-ops, FR-023/FR-026)"
- `ADR-055`: "Kickers get a consensus-only export artifact, never blended into the combined board"
  vs. "`live_availability.py`'s structural assumptions are now LeagueConfig-derived, not frozen
  module constants"

Both were caught on different, unmerged branches by `find_adr_collisions()` (`tools/handoffs.py`)
and, per this repo's explicit policy, I did not rename or renumber either side — that would
invalidate whatever already cites "ADR-054"/"ADR-055" by number elsewhere in the repo. Someone with
authority over `docs/decisions.md`'s content needs to decide which decision on each number is
canonical and add a short editorial note to the other, so a future reader citing the number has a
way to tell which one was meant. I don't have the context to make that call myself — it needs
whoever actually knows which of the two branches' work is still live vs. superseded.

## Why
Right now any citation of "ADR-054" or "ADR-055" anywhere in the repo (prose, other threads, code
comments) is genuinely ambiguous — there is no way to tell which decision it means without reading
both and guessing from surrounding context. `check`'s frozen debt registry
(`KNOWN_LEGACY_ADR_COLLISIONS`, `tools/handoffs.py`) stops this from blocking the mailbox check,
but a non-fatal check does not resolve the ambiguity, it just stops it from being invisible.

## Done looks like
A short editorial note added at the top of whichever ADR-054/ADR-055 entry in `docs/decisions.md`
is judged non-canonical (or both, if genuinely unclear), pointing at the other and stating which is
treated as authoritative going forward — no renumbering, no deletion. Once done, remove the
corresponding entries from `KNOWN_LEGACY_ADR_COLLISIONS` (`tools/handoffs.py`) and shrink
`docs/known-id-collisions.md`'s ADR table accordingly, and `test_known_legacy_collisions_registry_
is_frozen` (`tests/test_handoffs.py`) will need its expected set updated to match in the same
commit.
