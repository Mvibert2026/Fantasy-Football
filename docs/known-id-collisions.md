# Known ID collisions — frozen legacy debt, 2026-07-30

**Do not use this file to decide anything about the threads/decisions listed below.** It exists
so `tools/handoffs.py check` and `tools/founder_requests.py check` can tell "already-known,
pre-existing ambiguity" apart from "a brand-new collision that must still be prevented." It is not
a resolution of the ambiguity — nobody has picked a canonical thread/decision for any number below,
and this file does not do that either.

**Why these are not renamed.** `CLAUDE.md`/`docs/handoffs/README.md` policy: existing thread and
FR files keep their existing filenames and numbers, because they are referenced by number in prose,
commit messages, ADRs, and other threads across the repo. Renaming any of them to "fix" a collision
would silently invalidate every one of those references — worse than leaving the ambiguity visible.
Recorded here instead (ADR-064).

**Root cause.** All of this predates ADR-064's date+slug scheme (`docs/decisions.md`). The old
counter-based allocator (`next_id = max(existing) + 1`, widened later to scan git refs but never
closing the race — see thread 076) let two worktrees each compute a locally-valid "next free"
number and then reconcile at merge in whatever way a human or agent happened to resolve the merge
conflict — sometimes by renaming one file's filename to the next free slot *without* re-stamping
its own `ID:` frontmatter field to match, which is why several of the entries below have a
`filename number ≠ frontmatter ID:` mismatch on top of the plain "two files, one number" collision.
Nobody hand-fixed any of this; it is exactly what the old scheme produced under real concurrent use.

---

## `docs/handoffs/` — thread ID collisions

| Number | Files sharing it | Note |
|---|---|---|
| 093 | `093-contract-1-15-0-scoring-ruleset-note-on-league-j.md`, `093-fr-057-part-1-availability-json-now-covers-every.md`, `093-pass-3-the-qb-slope-collapse-is-not-established.md`, `093-run-pr-007-recommendation-constants-vs-plain-vbd.md` | Four unrelated threads, all `ID: 093`, all `OPENED: 2026-07-29`. |
| 094 | `094-register-the-wr-availability-fix-as-the-confirma.md`, `094-sleeper-projection-ingest-landed-red-against-the.md` | Two unrelated threads, both `ID: 094`. |
| 109 / 110 | `109-opponents-and-liveopponents-have-diverged.md` and `110-opponents-and-liveopponents-have-diverged.md` | **Same slug, different filenames** — looks like the identical thread ingested twice under two numbers. `110-...md`'s own frontmatter still says `ID: 109` (never re-stamped after the rename that gave it its `110-` filename). |
| 109 | also `109-league-settings-custom-pane.md` — unrelated to the pair above but shares the plain number 109. |
| 110 / 111 | `110-sleeper-screen-use-recent-usage-not-career-mean.md` and `111-sleeper-screen-use-recent-usage-not-career-mean.md` | Same pattern: identical slug, two filenames, and `111-...md`'s frontmatter still says `ID: 110`. |
| 111 | also `111-valuation-tests-35-36-results.md` — unrelated subject, correctly stamped `ID: 111`, but the number is already doubly claimed by the pair above. |
| 112 | `112-preregistration-gates-need-a-decision-subset.md` (correctly stamped `ID: 112`) and `114-founder-mock-scoring-format-inference-needs-sepa.md` (**filename says 114, frontmatter still says `ID: 112`** — same rename-without-restamp pattern). |

`tools/handoffs.py`'s `check` treats the id set `{093, 094, 109, 110, 111, 112}` as frozen, known
debt (`KNOWN_LEGACY_ID_COLLISIONS`) — flagged every run, non-fatal, printed separately from any
new collision. Any collision on a number outside that set, or any collision involving a
`YYYY-MM-DD-slug.md` filename, still fails `check` hard.

## `docs/decisions.md` — ADR header conflicts

| ADR | Two conflicting headers recorded under the same number |
|---|---|
| ADR-054 | "Batch mock-draft ingestion gains a frozen league-config snapshot and a computed..." **vs.** "FFC half-PPR/non-PPR/PPR 10-team ADP ingester, daily capture wired into CI (2026-07-29, data-ops, FR-023/FR-026)" |
| ADR-055 | "Kickers get a consensus-only export artifact, never blended into the combined board" **vs.** "`live_availability.py`'s structural assumptions are now LeagueConfig-derived, not frozen module constants" |

This is worse than a filename collision: two *different, real decisions* are both cited in the
repo as "ADR-054" / "ADR-055", and nothing in this file or the tooling can tell a reader which one
a given citation meant. `find_adr_collisions()` still detects and prints this every run —
`KNOWN_LEGACY_ADR_COLLISIONS` only stops it from failing `check`, it does not resolve which
decision is canonical. **Whoever next needs to cite ADR-054 or ADR-055 should quote the header text
inline, not just the number**, until this gets a real disambiguation (out of this session's scope —
requires an editorial call about which decision is actually the one referenced elsewhere, which
this tool has no authority to make unilaterally).

## `docs/founder-requests/` — FR ID collisions

| Number | Files sharing it |
|---|---|
| FR-029 | `FR-029-be-less-verbose-and-technical-enough-to-prioriti.md`, `FR-029-opponents-screen-must-be-functional-during-a-liv.md` |
| FR-030 | `FR-030-remove-the-refresh-data-button-since-it-cannot-w.md`, `FR-030-run-the-rankings-validation-at-maximum-effort-ac.md` |

`tools/founder_requests.py`'s `check` treats `{FR-029, FR-030}` the same way
(`KNOWN_LEGACY_FR_COLLISIONS`).

---

## What would actually resolve this

Not attempted here — it is a content decision (which thread/FR/ADR is the "real" one under a
contested number, and what the other one should be called going forward), not a mechanical fix,
and this session's scope was preventing new collisions, not adjudicating old ones. If someone wants
to resolve a specific entry above: the safest shape is *not* renaming the existing file, but adding
a short editorial note at the top of the file(s) that lost the adjudication, pointing at whichever
one is treated as canonical, and leaving the number's ambiguity on the record rather than erasing
it.
