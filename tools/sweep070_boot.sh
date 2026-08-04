#!/bin/bash
# SessionStart hook: revive the ADR-070 inclusion sweep after a container restart.
#
# WHY. The container is torn down on token exhaustion and on periodic reclaim,
# which kills the detached sweep with it. Three deaths in five hours on
# 2026-08-04 gave roughly a 20% duty cycle. The hourly watchdog Routine cannot
# cover this: firing it also needs tokens, and the container dies more often
# than hourly. A SessionStart hook fires the moment a session exists again,
# which is the earliest possible moment anything can run.
#
# SAFE TO RUN ALWAYS. run_sweep070.sh exits immediately if the sweep is already
# running, and sweep070.py skips phases already in state.json, so a spurious
# launch after completion costs seconds and changes nothing. Nothing is ever
# lost: draws are checkpointed every chunk and resume from the last one.
cd /home/user/Fantasy-Football 2>/dev/null || exit 0
LOG=experiments/bottomup/results/sweep070/sweep.log
[ -f "$LOG" ] || exit 0
# Do not resurrect a finished or deliberately-halted sweep.
if tail -5 "$LOG" 2>/dev/null | grep -q "completed cleanly\|VERIFY FAILED"; then exit 0; fi
# Clear zero-byte draw files before launching. A container kill mid-write leaves
# a truncated/empty CSV, and the resume then dies on
# "pandas.errors.EmptyDataError: No columns to parse from file" — the supervisor
# retries forever against the same bad file. Found 2026-08-04 by deliberately
# killing the sweep to test this hook. Deleting is safe: that cell simply
# restarts from zero draws, which is what an unreadable file means anyway.
find experiments/bottomup/results/sweep070/draws -name "*.csv" -size -2c -delete 2>/dev/null

if pgrep -f "experiments.bottomup.v2.sweep070" >/dev/null 2>&1; then exit 0; fi
echo "[boot-hook] $(date -u +%FT%TZ) reviving sweep after container restart" >> "$LOG"
nohup bash experiments/bottomup/v2/run_sweep070.sh >/dev/null 2>&1 &
exit 0
