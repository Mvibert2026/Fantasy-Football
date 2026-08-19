# Running the ADR-070 campaign on a rented box

Written 2026-08-19 after a RunPod attempt stalled because the founder could not reach a shell
on the pod (FR-2026-08-19). Everything here is doable from a web console. If a step needs a
terminal, it is marked, and there is a no-terminal alternative next to it.

## First: do you actually need a box?

Probably not. GitHub Actions runs this campaign for free — the repo is public, so there is no
minutes cap — and it needs no console at all. A rented box only wins when a *single* batch is
the bottleneck, because within-cell permutation draws are what scale with cores; batch-level
parallelism is already what Actions provides.

Rent a box when: one batch has been the long pole for more than a day of Actions runs.
Do not rent a box when: runs are failing. A faster machine fails faster.

## Billing, which is the part that is easy to get wrong

**Stopping a pod does not stop the bill.** RunPod keeps charging for the disk of a stopped pod.
Nothing on this box is worth keeping — the setup script clones the repo fresh and rebuilds the
database from public sources in about three minutes — so the correct action when you are done
is **Terminate**, not **Stop**. Terminate ends all charges.

Sizing that was chosen and why: `cpu3c-32-64` (32 vCPU, 64 GB), $0.96/hr, 50 GB container disk.
50 GB is not arbitrary — the database is ~3.3 GB, the nflverse download cache is another
~430 MB, and the default 20 GB left no headroom.

## Starting it without a terminal

Set both of these on the **deploy** form (or Edit Pod → Save, which restarts):

1. **Environment variable** — name `GITHUB_TOKEN`, value a fine-grained PAT with
   `Contents: Read and write`, scoped to this repository only. Paste it into the provider's
   UI. Never into a file in the repo, never into chat (CLAUDE.md §10).

2. **Container start command**:

   ```
   bash -c "curl -fsSL https://raw.githubusercontent.com/Mvibert2026/Fantasy-Football/main/tools/runpod_setup.sh | bash"
   ```

That is the whole setup. `tools/runpod_setup.sh` installs Python, clones the branch, rebuilds
the database, restores every draw already computed, runs the batches in value order, and
pushes results back every 20 minutes.

If the pod template offers **Connect → Start Web Terminal**, that works too and is easier to
watch. Not every template exposes it — the one tried on 2026-08-19 did not.

## What it does with the money

`MAX_HOURS` (default 13.5) is a wall-clock budget, and batches run in descending value order so
a budget that runs out cuts the least important work:

| Order | Batch | Cells | Why here |
|---|---|---|---|
| 1 | AB1 | 27 | Ablates factors **already in the shipped model** — "is what we are about to draft with justified" is the most decision-relevant question before a real draft, and it is small enough to finish |
| 2–3 | C1, C2 | 38, 29 | The twelve re-run under the new decision rule |
| 4–6 | C4, C3, C5 | 40, 46, 46 | C4K is excluded by the look-ahead guard |
| 7 | CT1 | 82 | Biggest by far, so it is the one that should be interrupted rather than anything else |

**Nothing is ever recomputed.** Every completed permutation draw is committed to the repo as a
gzipped archive and restored on startup, so an interrupted batch resumes from the next draw.
Killing the box at any moment costs at most 20 minutes.

## Checking on it without a terminal

Watch the branch `claude/pm-agent-setup-gobxa0` on GitHub. Commits titled
`sweep070: <batch> complete from runpod` mean it is working. If nothing lands within ~15
minutes of boot, the database build failed and the pod is burning money — terminate it.
