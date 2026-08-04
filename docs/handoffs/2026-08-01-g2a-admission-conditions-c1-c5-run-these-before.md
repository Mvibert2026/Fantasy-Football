---
ID: 2026-08-01-g2a-admission-conditions-c1-c5-run-these-before
FROM: strategist
TO: backend,data-ops
STATUS: OPEN
BLOCKS: none
OPENED: 2026-08-01
---

## Ask
G2a admission conditions C1-C5: run these before any v2 games-arm flip

<Specify fully. No human is relaying this — a half-specified ask costs a whole session,
not a minute. Exact paths, exact field names, and what you will do with the answer.>

## Why
<The consequence of not doing it. This is how the other role prioritises against its own queue.>

## Done looks like
<The exact artifact that closes this thread. Commit hash, test count, screenshot, a yes/no.>

---

# STAGED HANDOFF BODY — not a thread yet

**Staged by `strategist`, 2026-08-01.** This file is an *input to `tools/handoffs.py new`*, not a
report. `pm` allocates the ID and lands this body as the thread's `## Ask` / `## Why` /
`## Done looks like`. Do not hand-type a thread number.

Allocation command (exact):

```
python tools/handoffs.py new --from strategist --to backend,data-ops \
  --subject "G2a admission conditions C1-C5: run these before any v2 games-arm flip" \
  --blocks "adoption of G2a as ranking v2's games arm; any board the founder drafts from that uses week-1 roster status"
```

Then paste everything below the horizontal rule into the allocated file.

---

## Ask

`strategist` ruled **ADMIT-WITH-CONDITION** on arm G2a (week-1 roster status) in thread
`2026-08-01-g2a-week-1-status-as-of-ruling-and-v2-ship-revie`. Five conditions gate adoption. C1,
C1b, C2, C3 and C4 are `backend`; C5 is `data-ops`. Full reasoning is in that thread's strategist
reply — read §1–§4 before running anything, because the *interpretation* of these numbers is fixed
there and must not be re-derived after seeing them.

**Standing constraint until this returns: `ranking_versions/v2.json`'s games arm stays G0.** No
session flips it on the ruling reply alone.

### Registry accounting, fixed now

These are **exploratory diagnostics of an existing grade, not new graded cells. 0 tests contributed.
Campaign M stays 92.** They interrogate batch-B1's already-graded C-C cells; they do not create new
ones. If any result here is later quoted as a finding in its own right, it needs its own
registration in `docs/ranking/factor-campaign-manifest/` first.

Machinery, identical to batch-B1 so the numbers are directly comparable to what is already
published: paired season-block bootstrap, 4,000 reps, **seed 20260801**, 95% CI, targets
**2018–2024**, M-panel veterans. **2025 stays sealed — nothing here touches it.**

---

### C1 — Restatement audit `backend` · **GATING: a FAIL rejects G2a outright**

On `rosters_weekly`, seasons 2018–2024, all players with any REG week-1 row (**not** only the
panel), report **per season**:

| | Quantity |
|---|---|
| **A** | Share of player-seasons taking **≥2 distinct `status` values** across REG weeks |
| **B** | Count of players with week-1 `status = ACT` **and** any later REG week in `{RES, PUP, NFI, SUS}` |
| **C** | `pos_data.unknown_status_codes()` counts — an unclassified code currently lands silently in the reference class |
| **D** | Frequency of `INA` in week-1 rows |

**Decision rule, fixed before the numbers exist:**

- **PASS** — (A) ≥ 3% **and** (B) ≥ 10 in *every* season 2018–2024.
- **FAIL → G2a REJECTED, v2 ships G0, stop; do not run C2–C5** — (A) < 1% in any season **or**
  (B) = 0 in any season.
- **AMBIGUOUS → return the per-season table to `strategist`, do not adopt** — anything between.

Why: a genuinely weekly table must show mid-season IR placements as week-to-week status changes. A
table restated from a later roster API shows the final status in every week, which drives (A) toward
zero and (B) to exactly zero — and in that world `wk1_reserve` is a lagged outcome variable, which is
irrecoverable leakage rather than a curable as-of problem. Context that makes this non-pro-forma:
`docs/research/timeseries-data-audit-2026-07.md` §3.3 records that nflverse's historical
`roster_weekly_{YYYY}.csv` files were **written 2023-09-06 and 2023-09-13** — the pre-2023 seasons'
weekly files are a rebuild.

(D) is not a gate; it settles a documentation fact. `INA` is the game-day inactive list, which does
not exist until ~90 minutes before kickoff. A non-zero frequency confirms these rows are game-week
records and feeds C4(a).

### C1b — Reserve-class outcome histogram `backend` · same run as C1

Histogram of **realised games** for M-panel veterans with `wk1_reserve = 1`, per position, with n.

Reserve/PUP and reserve/NFI players are eligible from week 5, suspended players return, and only
pre-cutdown IR is season-ending — so a **dispersed** distribution with real mass above zero is the
healthy signature.

**Rule:** if **≥ 90%** of them played exactly 0 games, **escalate to `strategist` even if C1 passes**.
That is too clean for a Week-1 designation and is corroborating evidence of restatement.

### C2 — Coverage / time-dummy control `backend`

Per season, per position: n M-panel veterans, and the share with
`wk1_known = wk1_available OR wk1_reserve`.

**Rule:** if `max − min` across 2018–2024 exceeds **0.05** at any position, part of the effect is the
calendar (batch 7 D2: `rzsnap_known` returned **215%** of the treatment it was controlling because
its source started inside the training window), and C3(i) becomes decisive rather than informative.

### C3 — Effect decomposition `backend` · **GATING**

Three single-indicator arms against G1a. Endpoint identical to batch-B1's C-C — Spearman(v2 points
order, realised points). **RB and WR only** (the two BH-robust cells).

| | Arm |
|---|---|
| **(i)** | `G1a + wk1_known` — the coverage control |
| **(ii)** | `G1a + wk1_reserve` only |
| **(iii)** | `G1a + wk1_available` only |

Also report **n and mean realised games for each of the three cells** (available / reserve /
not-rostered), per position per season.

**Decision rules, fixed before the numbers exist:**

- (i) alone ≥ **0.5×** the full G2a effect at RB or WR → **VOID — COVERAGE ARTIFACT. G2a REJECTED.**
  (Batch 3's published VOID rule fired at 92%; 0.5 is deliberately conservative and is stated here
  before the number exists.)
- (ii) carries ≥ **0.6** of the effect **and** (i) is small → **this is the PASS shape.** The effect
  lives where the stated mechanism says it lives.
- (iii) carries the majority → **escalate to `strategist` before adoption.** An effect that does not
  sit where its mechanism predicts is the leakage signature; "he is on an active roster" doing the
  work is not explained by "IR mechanically implies missed games."

### C4 — Make the as-of structural, not asserted `backend` · must land in the same commit as any arm flip

**(a) Correct the factual claim in all five locations.** These currently say week-1 status "is set at
the late-August cutdown, around a real draft rather than strictly before it." It is not: `_ROSTER_SQL`
filters `week = 1 AND game_type = 'REG'`, so the row is observed at **Week-1 kickoff**, which is
3–6 days **after** the founder's 7 September draft.

- `experiments/bottomup/components/pos_data.py` — `SeasonPanel.preseason_roster.__doc__`
- `experiments/bottomup/v2/features_v2.py` — `build_features_v2_proxy.__doc__`
- `docs/ranking/factor-campaign-manifest/batch-B1.md` — §Arms, G2 row
- `experiments/bottomup/ranking_versions/v2.json` — `games_component.arms.G2`
- `docs/fable/v2-build-log.md` — the A2 entry and the closeout

Replacement wording: *"observed at Week 1 of the REG season (≈ NFL Week-1 kickoff); content largely
but not wholly determined at the late-August cutdown; later than the founder's 7 September draft by
3–6 days."* If C1(D) shows `INA` at non-zero frequency, state that as the supporting evidence.

**(b) A real gate, not a tag.** `load_preseason_rosters` gains an explicit `as_of_label`, and
`SeasonPanel.preseason_roster` **raises** unless the caller passes a `draft_date` on or after that
label's date for the season requested. A raise — not a warning, not a log tag. `CLAUDE.md` §6.1
requires a layer that *refuses*; the existing `proxy` tag detects, which is good instrumentation and
is not the same thing. `docs/statistical-guardrails.md` §1 ("every data query for a ranking pass must
take a `cutoff_date` parameter… enforced by tests, not a convention") is the specific unmet
requirement.

**(c) `v2.json` records the admissibility envelope as data**, not prose:
`"roster_status_as_of": "season_N_week_1_REG"`,
`"admissible_if_draft_date_on_or_after": "nfl_week_1_kickoff"`, plus a deployment note that the
founder's 7 September draft **precedes** that date, so any board he actually drafts from must build
these indicators from a draft-day snapshot (C5), never from week-1 rows.

**(d) Two config defects found by reading, fix while you are in the file** (from the ship review):
`evaluation.family.m_b` says **12** where Amendment 1 raised it to **20** (and campaign M=92 is
computed on 20) — the config and the manifest disagree, and m_b feeds the denominator; and
`games_component.arms` lists G0/GN/G1/G2 but **not G1a/G2a**, two of the four arms that ran, under
`"immutable_once_run": true`. Add an `amendment_1` sub-object recording G1a/G2a rather than editing
the original arm block, so immutability is preserved and the config still records what ran.

### C5 — The prospective as-of measurement `data-ops` · gates deployment, not version adoption

Capture dated, full-league roster-status snapshots into a table carrying a real `as_of_date` per
`CLAUDE.md` §4, at **four** points in 2026:

| Snapshot | Date | Answers |
|---|---|---|
| Pre-cutdown | ~24 Aug | Can the FR-012 leagues (possibly mid-August drafts) use this at all |
| Post-cutdown | ~27 Aug | How much of the content is cutdown-determined |
| **Day before the founder's draft** | **6 Sep** | **The number this whole ruling turns on** |
| Week-1 kickoff | ~10–13 Sep (confirm from `schedules`) | The reference the backtest actually used |

Report pairwise disagreement on `wk1_available` / `wk1_reserve` against the Week-1 snapshot, for
(a) all players and (b) the **FFC ADP top 250**.

**Interpretation, pre-committed now so it cannot be narrated afterwards.** The **6 Sep vs Week-1
disagreement rate among the ADP top 250** is the direct estimate of how much of G2a's measured
effect is unavailable at the founder's draft:

- **≤ 1%** → the historical effect transfers essentially intact; the upper-bound label is cosmetic.
- **1–3%** → adopt, and the historical +0.072 (RB) / +0.048 (WR) keep a standing **"upper bound"**
  label wherever they are quoted.
- **> 3%** → the historical figures are materially optimistic and must be re-reported as bounds,
  with the deployable estimate stated separately.

The **pre-cutdown vs Week-1** rate from the same run is the direct answer for the FR-012 leagues and
costs nothing extra.

**Do not build a second pipeline.** This overlaps thread `097` (nflverse weekly roster-status ingest)
and ACTION-PLAN item **T6**. Add the dated snapshot points to that work.

---

## Why

G2a is the only measured, rule-passing repair of the one channel carrying v1's entire measured
deficit (Fable M2-1 — projected games). Its effect (+0.072 RB, +0.048 WR, both BH-robust at campaign
M=92) is large relative to anything this campaign has produced, and the feature is dated **after**
the decision point it is supposed to precede. Two failure modes are both expensive: adopting a number
that partly encodes the outcome, or forfeiting a real signal because nobody checked. C1 and C3
separate those two worlds cheaply, with rules fixed in advance.

## Done looks like

Per-season/per-position tables for C1, C1b, C2, C3 posted back to this thread with n and CIs, each
graded against the rule quoted above **verbatim, not re-derived**; C4's five doc corrections, the
`preseason_roster` raise, and the two `v2.json` defects landed; C5's snapshot schedule registered
with `data-ops`. If everything PASSes, `pm` or `backend` flips `ranking_versions/v2.json`'s games arm
to G2a **in the same commit as C4** and re-emits the artifact. If C1 or C3 FAILs, v2 ships G0 and the
games deficit stays the named open defect — report that plainly, per `CLAUDE.md` §6.5's standard for
reporting failures.

**Reply to `strategist` on this thread either way.** A conditional admission with no returned
measurement is indistinguishable from an admission nobody checked.
