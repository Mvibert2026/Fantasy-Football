---
ID: FR-2026-08-19-compute-setup-must-not-require-terminal-access-r
STATUS: NEW
SOURCE: chat 2026-08-19
RAISED: 2026-08-19
---

## Request
Compute setup must not require terminal access (RunPod web UI only)

<Founder's own words where possible -- paraphrase only when necessary, and say so.>

## Why it matters

## Initial read
<Not the founder's own words -- your read on scope, constraints, sequencing.>

## Context

Founder rented a RunPod CPU box (32 vCPU) to accelerate the ADR-070 campaign and could not
reach a shell on it: *"no I don't know how to add any of that, I'm showing you my view, I
can't get to the terminal."* `tools/runpod_setup.sh` assumes a shell and a `GITHUB_TOKEN`
exported into it, so the box sat billing at $0.96/hr with nothing running.

## What this means for future compute plans

Any "rent a box and run the campaign" plan must be startable **entirely from a web console**:
env vars typed into the provider's UI, and the run command baked into the container start
command. A setup path whose first step is "open a terminal" is not a setup path the founder
can execute, and the meter runs while it is not executed.

GitHub Actions remains the only fully hands-off option — it needs no console at all, and on a
public repo it has no minutes cap.
