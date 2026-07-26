# Pre-registration

One file per factor test, written **before** the test runs. `src/preregistration.py`
refuses to execute a test with no matching file here.

## Why

statistical-guardrails.md §3.4 requires writing down the exact metric and the threshold
that would count as confirmation *before* looking at the result. Without that, a null or
weak result gets rationalised into a positive one after the fact — and the rationalisation
feels honest at the time, which is what makes it dangerous.

For folk-wisdom factors ("second-year WR leap", "third-year TE breakout") pre-registration
is mandatory, not optional: they come with a plausible mechanism and a large surface for
p-hacking.

## File format

Filename: `PR-<nnn>-<slug>.md`. Leading `---` frontmatter block, then free prose.

Required fields: `id`, `title`, `hypothesis`, `metric`, `confirmation_threshold`, `status`.

`status` is one of `REGISTERED` (written, not yet run), `RUN` (executed, result recorded),
or `ABANDONED` (with a reason in the body — abandoning a test still counts toward the
multiple-comparisons total).

## The run log

`test_run_log.jsonl` is append-only and **tracked in git on purpose**. The FDR denominator
must be the true number of tests run. A counter living in the gitignored database would
reset on rebuild and silently shrink that denominator — which is exactly the failure this
whole mechanism exists to prevent.

Record every run, including ones that found nothing. An unrecorded failed test inflates
every surviving result.

## Holdout

`holdout_access_log.jsonl` records every attempted and permitted read of the locked
holdout season (2025). See `src/holdout.py` for why 2025 and what locking does and does
not cost.
