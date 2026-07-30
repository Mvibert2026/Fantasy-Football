# Ranker — factor batch 3: the sweep's five, and the one they pointed at by accident

**2026-07-30.** 24 registered tests, campaign BH m = 24 at q = 0.10, sealed 2025 holdout not opened.
Design `1c452a1` committed before any arm was fitted; results `c7161ce`; post-hoc `bda27ea`.

## What was asked and what was run

The researcher's ranked five plus the founder's correction that coordinator continuity be specified
as *tenure*, and that **QB had never been tested at all**. Ran as **two declared families**: 16 model
arms and 8 baseline respecifications, corrected together at the campaign level because the dispatch
specified campaign-level multiplicity and a per-test correction would have been the sin the
pre-commitment exists to prevent.

**Nothing graded SURVIVES.** Three PROJECTION-ONLY, one EARNS-ITS-PLACE (an ablation), three
MARGINAL, one VOID, four BASELINE-WORSE, ten NULL.

## The four things worth remembering

**1. The best result is a missing wire inside our own model, and it is post-hoc.** The registered
explosive-rush arm worked (−0.7508 carries MAE, −1.51%, clean control). Then a post-hoc check found
that **lagged yards per carry does the same job better** — −0.9331 (−1.88%), and **−0.7200 against
−0.0264 on the ADP board**. YPC is not new: `RBComponentModel` already fits it and already uses it,
for the yards channel. `_RB_CARRY_VOLUME` contains no efficiency term at all, and neither does the
WR/TE or QB equivalent. A back's efficiency predicts how much work he gets next year and nothing in
the model connects the two. It costs no new data. **It is not shipped, not merged, not run
confirmatorily** — it went to `strategist` for registration, which is the entire reason that role
exists.

**2. The VOID rule fired, on the arm I most wanted to work.** Three coverage-flag control arms were
registered *in the family* with a numeric threshold fixed in advance (control ≥ 50% of treatment ⇒
the treatment loses its interpretation). NGS separation at WR cleared BH and then died: its control
is **92%** of it. Batch 2 discovered that shape after the fact and had to disown three arms; batch 3
caught it in the same run. **OC tenure at QB survived the rule by 0.04** and should be read as if it
had not.

**3. Registry #29 is closed at seven arms.** The pre-commitment said, before measurement, that a QB
null would close it on both specifications. `new_oc` at QB: −0.0660, p = 0.274. Tenure at four
positions: nothing clears BH. The founder's prior — that OC continuity matters most at QB — is not
supported. The source floor was measured rather than assumed: a backfill to 2004 **failed**, 96 of
192 team-seasons, because the Wikipedia club staff navbox templates did not exist before ~2010; under
a clean 2010 floor censoring is **one club-season a year, 3.1%**, so the nulls are believable as
nulls.

**4. Two defects of mine, both disclosed.** The too-good trigger fired on the QB ablation
(+14.4% of primary error) and is escalated with a decomposition rather than waived. And four of my
own 24 registered tests were algebraically degenerate — `ppg_1 × gshare_1` is `pts_1/season_len`,
rank-identical to the incumbent, residual 1.776e-15. Conservative direction, still a fault, and the
same class as batch 2's `move_known`.

## Batch 4 registered and deliberately not run

The founder's *"running backs coming off of high carry years (350/375/400)"* is registered as its own
family in `docs/ranking/factor-batch-4-precommit.md` and **blocked on `strategist`**. Counting first:
**≥350 carries is 26 player-seasons since 1999 and TWO in the harness's window; ≥400 is two all-time
and zero in window.** Two of his three thresholds are undefined, not underpowered — the workload the
hypothesis is about has been coached out of the league (20 of the 26 are 1999–2007). And season-total
carries *is* per-game carries × games played, both already in the model, so the FR's matched design
cannot identify anything. The reformulation — does a **gate** add anything on top of a **smooth term
in the same quantity** — is better posed and is also a different question from the one the founder
asked, which is why it went to `strategist` instead of being run.

## Threads opened

`strategist` ×2 (register batch 3's family + the post-hoc YPC test; unblock batch 4), `fable`
(attack, with the five weakest points named), `data-ops` (`pbp` and `ngs_receiving` are now model
inputs and may not be in the rebuild path — the defect that lost `play_callers`; plus the 2010 navbox
floor), `librarian` (nine ledger rows).

## Artifacts

`docs/ranking/factor-batch-3-precommit.md` · `factor-batch-3-results.md` ·
`factor-batch-4-precommit.md` · `experiments/bottomup/factors/{factor_features3,run_factors3,diagnostics3}.py` ·
`experiments/bottomup/components/pos_data.py` (two new gated accessors) ·
`experiments/bottomup/results/factor_batch3_{results,diagnostics}.csv` ·
`tests/test_factor_batch3_features.py` (10 tests; batch 2's 10 still green, bit-for-bit).

Commits `1c452a1`, `c7161ce`, `bda27ea`, `20a9c74`, and `87ec2a2` — the last is a concurrent agent's
`git add -A` that swept in `tests/test_factor_batch3_features.py`; the file is mine and the commit
message is not, the same collision batch 2 recorded at `70bc893`.
