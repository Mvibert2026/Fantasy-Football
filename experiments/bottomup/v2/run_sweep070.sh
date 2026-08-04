#!/bin/bash
# sweep070 supervisor: restart on crash (bounded), exit clean on success.
# Relaunch line (from repo root):
#   nohup bash experiments/bottomup/v2/run_sweep070.sh >/dev/null 2>&1 &
cd "$(dirname "$0")/../../.." || exit 1
LOG=experiments/bottomup/results/sweep070/sweep.log
for i in $(seq 1 50); do
  if pgrep -f "experiments.bottomup.v2.sweep070" >/dev/null; then
    echo "[supervisor] sweep already running; exiting" >> "$LOG"
    exit 0
  fi
  find experiments/bottomup/results/sweep070/draws -name "*.csv" -size -2c -delete 2>/dev/null
  .venv/bin/python -W ignore -m experiments.bottomup.v2.sweep070 >> "$LOG" 2>&1
  code=$?
  if [ "$code" -eq 0 ]; then
    echo "[supervisor] sweep completed cleanly" >> "$LOG"
    exit 0
  fi
  if [ "$code" -eq 2 ]; then
    echo "[supervisor] VERIFY FAILED (exit 2) - NOT restarting; report to strategist" >> "$LOG"
    exit 2
  fi
  echo "[supervisor] sweep exited code $code (attempt $i/50); restarting in 60s" >> "$LOG"
  sleep 60
done
echo "[supervisor] gave up after 50 attempts" >> "$LOG"
exit 1
