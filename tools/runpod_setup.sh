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
set -euo pipefail

REPO_URL="https://github.com/Mvibert2026/Fantasy-Football.git"
BRANCH="claude/pm-agent-setup-gobxa0"
WORKDIR="${WORKDIR:-$HOME/ff}"
BATCHES="${BATCHES:-C1 C2 C3 C4 AB1 C5 CT1}"
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

# --- run --------------------------------------------------------------------
# Batches are independent (per-batch cells shards, state and logs), so they run
# sequentially here while each one internally uses every core. That is the right
# split: within-cell parallelism is what the expensive cells need.
for b in $BATCHES; do
  echo "=== batch $b ==="
  ./.venv/bin/python -W ignore -u -m experiments.bottomup.v2.sweep070 --batch "$b" \
    2>&1 | tee -a "experiments/bottomup/results/sweep070/sweep_${b}.log" || \
    echo "!!! batch $b exited non-zero; continuing with the rest"

  ./.venv/bin/python tools/sweep070_archive.py archive
  ./.venv/bin/python -m experiments.bottomup.v2.report070 || true

  if [ -n "${GITHUB_TOKEN:-}" ]; then
    git add -A experiments/bottomup/results/sweep070/ docs/ranking/inclusion-campaign-report.md
    if ! git diff --cached --quiet; then
      git commit -q -m "sweep070: $b from runpod ($(nproc) cores)"
      for i in 1 2 3 4 5; do
        git pull --rebase origin "$BRANCH" && git push origin "HEAD:$BRANCH" && break
        echo "push attempt $i failed; retrying"; sleep $((i * 5))
      done
    fi
  fi
done

echo "=== all batches attempted ==="
grep -c 'stopped (' experiments/bottomup/results/sweep070/sweep_*.log 2>/dev/null || true
