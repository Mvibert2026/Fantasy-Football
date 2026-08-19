#!/usr/bin/env bash
# One-shot setup + run for the ADR-070 factor campaign on a rented CPU box.
#
# WHY A BIG BOX HELPS, and why a GPU would not. The campaign's runtime is
# dominated by single cells grinding through all 8,999 permutation draws -- a
# genuinely predictive factor pays full price, a dead one stops in ~75s. Batch
# parallelism (the GitHub Actions matrix) does nothing for that; only more cores
# do, because the draws within a cell are embarrassingly parallel. Measured on
# the 4-core container: 4 workers held it at 398% of 400% with the parent at
# 3.5%, a serial fraction near 1%, so this scales close to linearly well past
# 32 cores. The per-draw work is small-matrix pandas/sklearn fitting, which is
# exactly the shape a GPU is bad at.
#
# NOTHING IS RECOMPUTED. Every completed draw is committed to the repo as a
# gzipped archive, so this restores them and continues from the next k. Killing
# and restarting this script is safe at any moment.
#
#   curl -fsSL https://raw.githubusercontent.com/Mvibert2026/Fantasy-Football/main/tools/runpod_setup.sh | bash
#
# Optional environment:
#   SWEEP_WORKERS   worker processes (default: all cores minus two)
#   GITHUB_TOKEN    fine-grained PAT, contents:write, THIS REPO ONLY. Without
#                   it the box still computes and archives locally, it just
#                   cannot push results back. Never write it into a file in the
#                   repo -- export it in the shell only (CLAUDE.md 10).
#   BATCHES         space-separated batches (default: the remaining seven)
#   MAX_HOURS       wall-clock budget (default 13.5). $14 at $0.96/hr is ~14.5
#                   hours, so this stops with margin and, crucially, with a
#                   final push completed rather than mid-write.
set -euo pipefail

REPO_URL="https://github.com/Mvibert2026/Fantasy-Football.git"
BRANCH="claude/pm-agent-setup-gobxa0"
WORKDIR="${WORKDIR:-$HOME/ff}"
# Order matters on a metered box: the budget may not cover everything, so run
# the batches whose answers are worth most first, and the biggest last.
#
#   AB1 (27 cells) first -- it ablates the factors ALREADY IN the shipped
#       model. "Is what we are about to draft with actually justified" is the
#       most decision-relevant question before a real draft, and it is also
#       one of the smallest batches, so it completes.
#   C1  (38, part-done) then C2 (29) -- the twelve re-run under the new rule.
#   C4 (40), C3 (46), C5 (46) -- C4K is excluded by the look-ahead guard.
#   CT1 (82) last -- the biggest by far and the most likely to be cut off, so
#       it is the one that should be interrupted rather than anything else.
BATCHES="${BATCHES:-AB1 C1 C2 C4 C3 C5 CT1}"
MAX_HOURS="${MAX_HOURS:-13.5}"
START_TS=$(date +%s)
DEADLINE=$(python3 -c "print(int($START_TS + $MAX_HOURS*3600))")
remaining() { echo $(( DEADLINE - $(date +%s) )); }
: "${SWEEP_WORKERS:=$(( $(nproc) > 2 ? $(nproc) - 2 : 1 ))}"
export SWEEP_WORKERS

echo "=== ADR-070 campaign runner ==="
echo "cores=$(nproc)  workers=${SWEEP_WORKERS}  batches=${BATCHES}"

# --- deps -------------------------------------------------------------------
if ! command -v python3.12 >/dev/null 2>&1 && ! python3 -c 'import sys;exit(0 if sys.version_info[:2]>=(3,12) else 1)' 2>/dev/null; then
  echo "--- installing python 3.12"
  apt-get update -qq && apt-get install -y -qq software-properties-common
  add-apt-repository -y ppa:deadsnakes/ppa >/dev/null 2>&1 || true
  apt-get update -qq && apt-get install -y -qq python3.12 python3.12-venv
fi
command -v git >/dev/null 2>&1 || { apt-get update -qq && apt-get install -y -qq git; }
PY=$(command -v python3.12 || command -v python3)

# --- repo -------------------------------------------------------------------
if [ -d "$WORKDIR/.git" ]; then
  git -C "$WORKDIR" fetch origin "$BRANCH" && git -C "$WORKDIR" checkout -B "$BRANCH" "origin/$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO_URL" "$WORKDIR"
fi
cd "$WORKDIR"

# Push auth, if supplied. Kept in the remote URL for this clone only, never
# written to a tracked file.
if [ -n "${GITHUB_TOKEN:-}" ]; then
  git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/Mvibert2026/Fantasy-Football.git"
  git config user.name  "runpod-sweep"
  git config user.email "runpod-sweep@users.noreply.github.com"
  echo "--- push enabled"
else
  echo "--- WARNING: no GITHUB_TOKEN; results will be archived locally but NOT pushed"
fi

[ -d .venv ] || "$PY" -m venv .venv
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -r requirements.txt

# --- database ---------------------------------------------------------------
# ~3.3 GB, gitignored, so it is never in the clone. Built from public sources,
# no credentials. Takes about three minutes.
if [ ! -s data/nfl.db ]; then
  echo "--- building the database from public sources (~3 min)"
  ./.venv/bin/python scripts/rebuild_database.py --db data/nfl.db
else
  echo "--- database already present ($(du -h data/nfl.db | cut -f1))"
fi

# --- restore everything already computed ------------------------------------
echo "--- restoring banked draws"
./.venv/bin/python tools/sweep070_archive.py restore

# --- periodic save ----------------------------------------------------------
# A rented box can be stopped at any moment -- deliberately, when the budget
# runs out, or by the provider. Archiving only between batches would throw away
# hours of a long batch. This snapshots every 20 minutes so the most that can
# ever be lost is 20 minutes of compute.
#
# flock because the end-of-batch save below runs the same commands; two git
# processes in one repo at once corrupts the index.
LOCK="$WORKDIR/.sweep-git.lock"
save_now() {
  flock -w 600 9 || return 0
  ./.venv/bin/python tools/sweep070_archive.py archive >/dev/null 2>&1 || true
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    git add -A experiments/bottomup/results/sweep070/ >/dev/null 2>&1
    if ! git diff --cached --quiet; then
      git commit -q -m "sweep070: periodic snapshot from runpod" || true
      for i in 1 2 3; do
        git pull --rebase -q origin "$BRANCH" && git push -q origin "HEAD:$BRANCH" && break
        sleep $((i * 5))
      done
    fi
  fi
} 9>"$LOCK"

( while true; do sleep 1200; save_now; done ) &
SAVER_PID=$!
trap 'kill $SAVER_PID 2>/dev/null || true' EXIT
echo "--- periodic save every 20 min (pid $SAVER_PID)"

# --- run --------------------------------------------------------------------
# Batches are independent (per-batch cells shards, state and logs), so they run
# sequentially here while each one internally uses every core. That is the right
# split: within-cell parallelism is what the expensive cells need.
for b in $BATCHES; do
  LEFT=$(remaining)
  # Below a quarter hour there is not enough time for a cell to finish AND be
  # pushed, and an unpushed draw on a box about to be destroyed is worth
  # nothing. Stop while the result still gets home.
  if [ "$LEFT" -lt 900 ]; then
    echo "=== budget spent ($(( LEFT ))s left); stopping before $b ==="
    break
  fi
  echo "=== batch $b — $(( LEFT / 60 )) min of budget left ==="
  # Cap the batch at the remaining budget. A cut-off batch is not lost work:
  # every completed draw is banked and the next machine resumes from the next
  # k. This just stops one huge batch (CT1 is 82 cells) from eating the whole
  # clock and leaving the smaller ones unrun.
  timeout "${LEFT}s" ./.venv/bin/python -W ignore -u -m experiments.bottomup.v2.sweep070 --batch "$b" \
    2>&1 | tee -a "experiments/bottomup/results/sweep070/sweep_${b}.log" || \
    echo "!!! batch $b stopped early (budget or error); continuing"

  save_now
  ./.venv/bin/python -m experiments.bottomup.v2.report070 || true
  {
    flock -w 600 9 || true
    if [ -n "${GITHUB_TOKEN:-}" ]; then
      git add -A experiments/bottomup/results/sweep070/ docs/ranking/inclusion-campaign-report.md
      if ! git diff --cached --quiet; then
        git commit -q -m "sweep070: $b complete from runpod ($(nproc) cores)"
        for i in 1 2 3 4 5; do
          git pull --rebase origin "$BRANCH" && git push origin "HEAD:$BRANCH" && break
          echo "push attempt $i failed; retrying"; sleep $((i * 5))
        done
      fi
    fi
  } 9>"$LOCK"
  echo "--- $b done; graded batches so far: $(ls experiments/bottomup/results/sweep070/graded_*.csv 2>/dev/null | wc -l)"
done

echo "=== finished after $(( ( $(date +%s) - START_TS ) / 60 )) minutes ==="
echo "graded batches: $(ls experiments/bottomup/results/sweep070/graded_*.csv 2>/dev/null | wc -l)"
echo "archived cells: $(ls experiments/bottomup/results/sweep070/draws_archive/*.gz 2>/dev/null | wc -l)"
grep -c 'stopped (' experiments/bottomup/results/sweep070/sweep_*.log 2>/dev/null || true
echo
echo "############################################################"
echo "#  CAMPAIGN RUN FINISHED — STOP THE POD to stop the meter.  #"
echo "############################################################"
