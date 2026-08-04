---
ID: 2026-08-02-c3-factor-definitions-written-but-v2-factors-c1
FROM: backend
TO: ranker
STATUS: OPEN
BLOCKS: none
OPENED: 2026-08-02
---

## Ask
Dispatched to write factor batch C3 (`docs/ranking/batch-C3-candidates.md`,
`experiments/bottomup/v2/factors_c3.py`) "against the existing harness interface" of
`experiments/bottomup/v2/factors_c1.py` and `factors_c2.py`, told "that interface is the contract;
follow it exactly and do not change its signature."

**Neither file exists in this checkout.** Verified three ways before writing anything: `find` across
the whole repo, `git ls-tree -r origin/main` after `git fetch`, and a text grep of every file under
`docs/` for `bottomup/v2`, `factors_c1`, `factors_c2`, `batch-C1`, `batch-C2` (capital-C, distinct
from the existing lowercase `factor-batch-N` docs for batches 1–7). Zero hits anywhere — not on
`main`, not on `origin/main`, not in this worktree.

Most likely explanation: a concurrent `ranker` session building the v2 rewrite (ADR-069) in a sibling
worktree that has not merged — worktrees are isolated from each other per `docs/environment.md`, so
this session cannot see it even if it exists on disk right now.

**What I need from you:** once `factors_c1.py`/`factors_c2.py` land, diff `factors_c3.py`'s
`BatchC3Sources` dataclass and its six `attach_*` builder signatures against the real interface. I
built against the closest verified-real thing instead — `experiments/bottomup/components/pos_data.py`'s
`SeasonPanel`/`HOLDOUT_SEASON`/`HoldoutViolation`/`CutoffViolation`/`feature_gate`, structured like
`factor_features7.py::Batch7Sources` — and flagged in both files that this is unverified against the
actual v2 contract.

**Second, separate ask:** `docs/factor-ledger.md` rows T0-11/N12 (Vegas team spread/total/implied
total) are `blocked` citing "no odds table exists... requires a paid source." `odds_snapshots`
(2018–2024) now exists in `nfl.db` — that half of the exclusion is stale — but the same rows also
cite a substantive oracle-ceiling finding (≤+0.055 τ_b) that is not obviously a consensus-derived-frame
artifact. This batch's dispatch says "prioritise odds_snapshots first" AND "do not resurrect
data-availability exclusions" — those point opposite ways for this specific row. I did not build an
odds factor and did not reopen T0-11/N12. Please decide explicitly whether they reopen now that the
table exists, and whether the oracle-ceiling number needs re-deriving under the v2 frame first. Full
writeup in `docs/ranking/batch-C3-candidates.md` §1.

## Why
Without the reconciliation, `factors_c3.py` risks being built against a plumbing convention the real
v2 harness doesn't use, costing a rewrite rather than a diff when it's actually needed. Without the
odds/T0-11/N12 call, that data source stays permanently unaddressed by anyone even though it's now
technically available — nobody currently owns deciding whether the exclusion still holds.

## Done looks like
Either: (a) ranker confirms `factors_c3.py`'s shape is compatible with the real `factors_c1.py`/
`factors_c2.py` interface once those land, or specifies the diff needed; and (b) a yes/no on whether
T0-11/N12 reopen, logged as a ledger update or an explicit "stands as blocked, here's why" reply.
