# 2026-07-29 — backend — a claim checker for live documents (ADR-059)

**Branch:** `worktree-agent-afa13ac8a8bd0c533` (worktree, not merged).

## The premise, checked first

The dispatch said five false claims were found by accident on 2026-07-29 and asked for a
detector. I checked each against the repo before building anything, because a detector built on
a wrong account of the failures would encode the wrong checks:

| Claim in the dispatch | What the repo says |
|---|---|
| FFC "blocked by robots.txt" in CURRENT-STATE | Confirmed still live, in **two** places (lines 192 and 474), contradicted by `docs/pm/MEMORY.md` §0/§4, `docs/research/source-audit-2026-07.md` (row rewritten to UNBLOCKED) and `FR-023` |
| ADP capture "observed to succeed" / local task "redundant" | Already corrected in place in CURRENT-STATE, with the correction narrated inline |
| Predictions tab "absent from the shipped app" | Confirmed still live. `frontend/ui/views/Predictions.tsx` exists and is routed from `App.tsx:167` and `StandaloneApp.tsx:127` |
| `handoffs/README.md`: "design cannot read this repo" | Confirmed still live at line 99; `docs/design-protocol.md` §1 says the opposite and explicitly calls the README line false |
| rankings history unrecoverable | Confirmed live in CURRENT-STATE item 9 and in `can-we-rebuild-the-database.md`'s revision history; the same document's pass 2 disproves it (2,540 rows, row-for-row) |

Premise held. No contradiction with a written rule, so I proceeded without escalating.

## What I built

A **closed registry plus a closed document scope** — deliberately not prose analysis.

- `docs/state-claims.toml` — the registry. `[[artifact]]` (path on disk), `[[constant]]` (value
  read from the file that defines it), `[[status]]` (a named source or capability with a
  polarity vocabulary), `[[count]]` (measured from a file), `[[ignore]]` and `[[paths.allow]]`
  (suppressions, each with a written reason).
- `tools/state_claims.py` — the checker, also a CLI (`python tools/state_claims.py`).
- `tests/test_state_claims.py` — 21 tests, including the planted-fault proof.
- `tests/fixtures/state_claims/` — six planted faults with corrected counterparts, plus a
  two-document contradiction pair.

Three design choices did the real work, and each is a precision decision rather than a coverage
one:

1. **Only ten "live" documents are scanned.** `docs/status.md`, `docs/status/`,
   `docs/decisions.md`, numbered handoff threads, `docs/founder-requests/`, `SNAPSHOT-*` and
   `RUN-*` are never read. They record what was believed then; flagging them would be flagging a
   document for doing its job, and that is the false-alarm factory that gets a checker switched
   off. `test_append_only_logs_are_out_of_scope` pins this so a later session cannot widen it
   casually.
2. **A live document may narrate a superseded belief if it marks it** — `~~struck through~~`, an
   `<!-- state-claims: ignore-block -->` region, or a named suppression carrying a reason. I used
   the region marker once, on `can-we-rebuild-the-database.md`'s "three revisions in one day"
   list, which is genuinely history sitting inside a live document.
3. **A `[[status]]` claim with no registered `truth` flags disagreement *between* documents.**
   That is the cross-document-contradiction class, and it is the only honest form for a fact
   nobody has settled — it needs no ground truth at all.

Two implementation details were bugs I found by measuring rather than reasoning, and both would
have made the tool quietly useless:

- Phrases must match across a **soft line wrap**. The real CURRENT-STATE fault reads
  `FFC remains\n   blocked`; matching a literal single space missed it. The first draft of the
  checker did exactly that and silently under-reported. Fixed with `[^\S\n]+` joins.
- Matching must **not** cross a paragraph or heading boundary. A `## Not built` heading sits
  inside the proximity window of the first sentence under it and manufactures a false positive
  — it did, on my own corrected fixture, which is how I caught it.

## Planted faults — both directions

Six fixtures, each reproducing a real failure in roughly the words the real document used.
`{{CONTRACT_VERSION}}` and `{{BOARD_PLAYERS}}` are substituted from the live repo at test time,
so a *correct* fixture cannot rot into a false one when the real value moves.

| Fixture | Class | Caught | Corrected version silent |
|---|---|---|---|
| F1 FFC blocked by robots.txt | source status | yes | yes |
| F2 Predictions tab absent | existence | yes | yes |
| F3 design cannot read this repo | capability status | yes | yes |
| F4 `CONTRACT_VERSION` quoted as 1.13.0 | version | yes | yes |
| F5 board stated as 511 players | count | yes | yes |
| F6 rankings history unrecoverable | cross-doc / recoverability | yes | yes |
| F7 two docs disagreeing on the ADP capture | cross-doc, no ground truth | yes | n/a (pair) |

## Eight live false claims, found and corrected

The checker's first run on the real documents:

| Document | Claim | Corrected to |
|---|---|---|
| `CURRENT-STATE.md:419` | Predictions tab absent from the shipped app | removed from "Not built", replaced with a stated correction and the two routing sites |
| `CURRENT-STATE.md:44` | `CONTRACT_VERSION` is 1.13.0 | 1.14.0 — the file's own generated Build-state table had been right all along |
| `CURRENT-STATE.md:192` | FFC blocked by robots.txt | FFC unblocked; it is still the wrong *shape* for consensus, which is the point that paragraph was actually making |
| `CURRENT-STATE.md:474` | FFC remains blocked, founder decision needed | FFC unblocked, decision answered, remaining work is scoping |
| `CURRENT-STATE.md:55` and `:349` | board is 511 players | 510, measured from `data/export/board.json` |
| `handoffs/README.md:99` | design cannot read this repo | design has read access, no write access; `VIA: pm` is the landing hop only |
| `can-we-rebuild-the-database.md:33` | rankings history permanently unrecoverable | wrapped the superseded-conclusions list in an ignore-block, since the document's own pass 2 disproves it two paragraphs later |

After the corrections: `python tools/state_claims.py` → **OK, 10 live documents, no contradicted
claims.** Zero false positives across roughly 4,000 lines of live prose, and exactly one reasoned
path allowance (`src/mock_prediction.py`, which `CODE-MAP.md` correctly cites as living on
`backend/mock-calibration-kickers`, not on main — the allowance itself fails if that branch lands
or if the mention disappears).

## What it does not catch, stated plainly

**Failure #2 — the ADP capture — is the one it cannot verify.** "Has been observed to succeed"
and "the local task is now redundant" were false because no run with `event: schedule` had ever
fired; only a manual `workflow_dispatch` had. That is not readable from a checkout. It is
registered *truth-less*, so the checker flags the two polarities coexisting across documents but
**a single document asserting the false version alone still passes.**
`test_each_document_alone_does_not_fire_on_the_contested_claim` asserts that limitation rather
than describing it, so the gap is a measured property and not a paragraph nobody rereads. Closing
it properly needs a step that queries the Actions API — checking `event`, never the commit
author, since `github-actions[bot]` authors a manual dispatch too, and that is precisely how this
was got wrong. Raised as thread 083 item 3.

Also not covered, and deliberately: inferring a *presence* claim from free prose (imprecise — the
exact form, "a doc names a code path that is gone", is covered instead); and `docs/pm/**`, which
holds the richest live claims in the repo but is outside this role's write boundary, so a
violation there would produce a red suite with no available fix. One-line change, raised as
thread 083 item 1.

## Suite

`pytest -q` on this branch: 674 passed, 26 failed, 9 errors. The failing and erroring set is
**byte-identical to the same run with my changes stashed** — all pre-existing, all DB- or
snapshot-dependent, plus `tests/test_handoffs.py::test_mailbox_health`, which is red by design
over a real ADR numbering collision on an unmerged branch and was left alone.
`tests/test_state_claims.py` alone: 21 passed.

## Documents edited

`docs/CURRENT-STATE.md` (six corrections in place, plus a new Build-state row for the detector),
`docs/handoffs/README.md` (design's access), `docs/can-we-rebuild-the-database.md` (ignore-block
around the superseded-conclusions list), `docs/decisions.md` (ADR-059), `docs/ideas-inbox.md`
(four entries). Thread 083 opened to `pm`.
