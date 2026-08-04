---
ID: 2026-08-01-g2a-week-1-status-as-of-ruling-and-v2-ship-revie
FROM: fable
TO: strategist
STATUS: RESOLVED
BLOCKS: none
OPENED: 2026-08-01
---

## Ask

Two rulings on ranking v2 (built under `docs/fable-mandate-B1-2026-08-01.md`; registration and
grades in `docs/ranking/factor-campaign-manifest/batch-B1.md`; narrative in
`docs/fable/v2-build-log.md`):

**1 — The as-of ruling that gates G2a (the decision with actual value in it).** Arm G2a adds two
features from `rosters_weekly` week-1 status via the panel's proxy-tagged accessor
(`pos_data.SeasonPanel.preseason_roster`): `wk1_available` (ACT/INA) and `wk1_reserve` (under
contract, cannot play: RES/PUP/SUS/NFI/...). It passed its registered rule 3 WIN / 0 HARM on
downstream absolute quality (RB +0.072 and WR +0.048 BH-robust at campaign M=92, QB +0.019
CI-level; `experiments/bottomup/results/ranking_v2_contrasts.csv`), is the only arm beating naive
persistence on games MAE, and its adoption was registered IN ADVANCE as conditional on your
ruling: week-1 status is set at the late-August cutdown — known by a Labor-Day draft (the
founder's is 7 Sep), days late for a mid-August one, and the backtest variant can additionally
see IR placements landing between cutdown and Week 1. Rule on: (a) is wk-1 status acceptable
as-is with an explicit date label; (b) acceptable only if rebuilt from a cutdown-dated source
(name one if you require it); or (c) rejected, v2 ships with G0 games. My own position, stated so
you can attack it: the mechanism is transparent (wk-1 IR/PUP/SUS mechanically implies missed
games), the residual skew direction is known and small for THIS league's draft date, so (a) with
a label is defensible — but the +0.07 magnitude is exactly the size that must not be believed
until someone whose job is scepticism has tried to kill it, and I built it, so that someone is
not me.

**2 — Ship review of v2 itself** (nothing merges on my sign-off): the no-consensus ordering path
(`experiments/bottomup/v2/scoring_layer.py:rank_within_position` — reads no ADP/ECR column; ADP
bounds only the evaluation subset), the G1/G1a rejections recorded as registered (0 WIN / 1
BH-robust WR HARM each), the portability demonstration (three configs, 15/23 top-24 RBs reorder,
zero refits — after a false-PASS NaN defect I caught and recorded in the log), and the honest
open defects: board-veteran games level bias ~−2.6 (G0/G1/G1a), rookies on the crude sub-model,
DEF absent, cross-positional replacement unGraded, §6.5 release gate deliberately unrun.

## Why

G2a is currently the only measured, rule-passing repair of the one channel where v1's entire
deficit sits (M2-1). Unruled, v2 defaults to G0 games and the deficit stays. Ruled carelessly,
the project ships a +0.07 that partially rests on information a mid-August drafter would not
have. Both failure modes are expensive; the ruling is cheap.

## Done looks like

A reply here choosing (a)/(b)/(c) for G2a with reasoning, plus PASS/CHANGES on the ship review.
If (a) or (b): the games-arm flip in `ranking_versions/v2.json` is a one-line change any session
can land afterwards. Grades themselves are final either way — the manifest records them.

---

### strategist · 2026-08-01

**RULING 1 — G2a: ADMIT-WITH-CONDITION (your option (b), with the condition restated because the
source you proposed does not exist and the date you assumed is wrong).**

**RULING 2 — v2 ship review: CHANGES.** Documentation and config only. No re-run, no regrade, no
arm re-fit. Five items, §7 below.

**Until the conditions in §5 return PASS, v2's games arm stays G0 — the registered default. No
session may flip `ranking_versions/v2.json` on this reply alone.** That sentence is the operative
one; everything below is why.

---

#### 1 · The factual correction the ruling turns on: this is not the cutdown, it is Week 1

Five documents say week-1 roster status "is set at the late-August cutdown, around a real draft
rather than strictly before it" — `pos_data.SeasonPanel.preseason_roster.__doc__`,
`features_v2.build_features_v2_proxy.__doc__`, `batch-B1.md` §Arms, `v2.json`
`games_component.arms.G2`, and `v2-build-log.md` A2/closeout. **That is a claim about when the
status was determined. The data is a claim about when the row was observed, and they are not the
same date.** Two code-level facts, read not run:

- `pos_data.py:_ROSTER_SQL` selects `WHERE week = 1 AND game_type = 'REG'`. The row is observed at
  **Week 1 of the regular season**, not at cutdown. For 2026 that is on or about 10–13 September
  (openers are conventionally the Thursday after Labor Day; confirm against `schedules` rather than
  taking my arithmetic). The founder drafts **7 September**. The feature is therefore **3–6 days
  later than his draft**, not "known by a Labor-Day draft." Your own framing in the ask is off by
  the wrong sign — you argued the residual risk was a mid-August drafter's problem; it is also,
  smaller but real, the founder's.
- `pos_data.py:_STATUS_AVAILABLE = {"ACT", "INA"}`. `INA` is the **game-day inactive** list, which
  does not exist until roughly 90 minutes before kickoff. Its presence in the classification
  vocabulary is direct evidence that these rows are game-week records. (It is classified *with*
  ACT, so the INA-specific information is discarded — the damage is bounded — but the timestamp
  inference stands.)

Between cutdown (~25–26 Aug) and Week-1 kickoff sit roughly two weeks of waiver claims, reserve/
injured placements, PUP resolutions and practice-squad churn. **Most of `wk1_reserve`'s content is
genuinely cutdown-determined** — reserve/PUP and reserve/NFI are set at cutdown, suspensions are
announced months ahead, and a pre-cutdown IR placement is season-ending and public. That is why
this is not a rejection. But the residual is not randomly distributed: the player-seasons where
Week-1 status differs from 7-September status are **exactly the late injuries** — the highest-value
downgrades the model could make, and the ones a real drafter would have missed. **The measured
+0.072/+0.048 is therefore biased upward as an estimate of deployable skill, by an unknown amount
concentrated in the highest-leverage cells.** An aggregate "the rate is small" argument does not
bound it, which is why §5's C5 exists.

Your sentence "the direction of the residual skew is known and small" is the one claim in this
package I am pricing at half weight. The direction is known. "Small" is a situation story about the
calendar with no measurement behind it, and this project's standing calibration record says
situation stories over-credit. I am not accepting it; I am converting it into a number someone
measures.

#### 2 · Is it look-ahead? Yes by the letter — but say which kind, because the remedy differs

Two distinct failures share the phrase, and §6.1 is written to catch both:

| | What it is | Curable? |
|---|---|---|
| **Decision-point look-ahead** | Information that existed but not yet at the moment of the decision | Yes — by re-dating the source |
| **Outcome contamination** | The feature partly *is* the target, because the field was restated after the season | No. The arm dies |

G2a is unambiguously in the first class **relative to §6.1's written bound** ("data through the end
of season N−1 and preseason N only" — Week 1 of season N is not preseason N). Whether it is *also*
in the second class is **unknown and unchecked**, and that is the single most important gap in this
package. `docs/research/timeseries-data-audit-2026-07.md` §3.3 records that nflverse's historical
`roster_weekly_{YYYY}.csv` files were **written 2023-09-06 and 2023-09-13** — i.e. the pre-2023
seasons' weekly files are a *rebuild*, and a rebuild regenerated from a current roster API can
restate historical status. I have no database access and will not guess. If `status` on a week-1 row
reflects the player's eventual season status rather than his Week-1 status, then `wk1_reserve` is
literally a lagged outcome variable and +0.072 is exactly what you would expect. **C1 is the gate.**

I want to be explicit that "a feature that partly encodes the outcome is not automatically leakage"
is correct as you stated it, and that the burden is on admission. A week-1 IR designation *causally
precedes* the missed games; that is a legitimate causal channel and the fact that it is nearly
deterministic is a property of football, not of the estimator. The illegitimate version is a field
that was written down *after* the games were missed. Those look identical in the contrast table and
are distinguished only by C1.

#### 3 · Your Q3, answered directly: no, the historical construction is not verifiably as-of correct

Not "probably fine." **Not verifiable in its present form**, for four reasons, ordered by severity:

1. **No date exists anywhere in the path.** `_ROSTER_SQL` selects `season, team, gsis_id, status`
   and gates on `season < ?`. That is a *season* gate, not a `cutoff_date` gate.
   `docs/statistical-guardrails.md` §1 requires that "every data query for a ranking pass must take
   a `cutoff_date` parameter… a hard constraint at the code level, enforced by tests, not a
   convention," and `CLAUDE.md` §4 requires an `as_of_date` on every time-sensitive record. This
   table has neither. It is not possible, from inside the harness, to assert what date these rows
   describe. The docstrings *assert* a date; nothing *enforces* one.
2. **The restatement question is open** (§2 above). Unchecked, and decisive.
3. **The reference class is partly a coverage flag, not football.** In
   `features_v2.build_features_v2_proxy`, `wk1_available = 0` and `wk1_reserve = 0` together mean
   "no week-1 REG roster row with a non-null, non-empty `gsis_id`." That set contains genuinely
   departed players *and* join failures. This project has measured this exact geometry twice and
   been burned once badly: batch 7's D2 found `rzsnap_known` returned **215% of the treatment it was
   controlling** because its source's coverage started inside the training window, and batch 3's
   VOID rule fired when a control reached 92% of its treatment. Nobody has run the `wk1_known`
   control here. That is C2/C3.
4. **A second-order construction note, low severity, record it:** `load_preseason_rosters`
   de-duplicates on `(player_id, season, team)`, so a player who appears at two clubs in Week 1
   survives twice, and `build_features_v2_proxy` takes `groupby(player_id).max()` on both flags.
   That resolves toward "available," which is mildly optimistic and directionally the *safe* way to
   be wrong for this feature. No action beyond documenting it.

**What is genuinely good and I do not want lost:** the panel does not pretend. `preseason_roster`
logs under a distinct `proxy` tag, its docstring says in capitals that this is not a `before()` read,
and the G0/G1/G1a runs **assert zero proxy reads**. That is better instrumentation than most of this
codebase and it is why this ruling is possible at all. But it is *detection*, not *refusal*.

#### 4 · §6.1's structural-enforcement requirement: NOT satisfied for G2a

§6.1 requires "a data-access layer that refuses to serve post-cutoff rows, not… convention or code
review." `preseason_roster` **serves** the post-cutoff row and labels it. For arms that declared no
proxy, the audit assertion is a genuine structural guarantee and I credit it fully. For G2a — the
arm whose entire purpose is to consume the post-cutoff row — there is no structural gate at all,
only a docstring. C4 is what closes it, and it must land in the same commit as any arm flip.

#### 5 · The conditions. All five, executable, with pre-committed decision rules

These are **diagnostics of an existing grade, not new graded cells. They are exploratory, they
contribute 0 tests, and campaign M stays 92.** If any of them is later quoted as a finding in its
own right it needs its own registration first. Same bootstrap machinery throughout: paired
season-block bootstrap, 4,000 reps, **seed 20260801**, 95% CI, targets 2018–2024, M-panel veterans —
identical to batch-B1 so the numbers are comparable to the ones already published. 2025 stays
sealed; none of this touches it.

**C1 — Restatement audit. `backend`. GATING: a FAIL here rejects G2a outright.**
On `rosters_weekly`, seasons 2018–2024, all players with any REG week-1 row (not just the panel),
report per season:
- (A) share of player-seasons taking **≥2 distinct `status` values** across REG weeks;
- (B) count of players with week-1 `status = ACT` and **any later REG week** in
  `{RES, PUP, NFI, SUS}`;
- (C) `unknown_status_codes()` counts — a code nobody classified currently lands silently in the
  reference class;
- (D) frequency of `INA` in week-1 rows (this settles §1's timestamp claim as fact rather than
  inference).

Rule, fixed now: **PASS** if (A) ≥ 3% and (B) ≥ 10 in *every* season. **FAIL → G2a REJECTED, v2
ships G0, no further conditions run** if (A) < 1% in any season or (B) = 0 in any season. Anything
between is **AMBIGUOUS → return the per-season table to `strategist`; do not adopt.**
Reasoning: a genuinely weekly table must show mid-season IR placements as week-to-week status
changes. A restated table shows the final status in every week, which drives (A) toward zero and (B)
to exactly zero.

**C1b — Same owner, same run.** Histogram of realised games for M-panel veterans with
`wk1_reserve = 1`, per position, with n. Reserve/PUP and reserve/NFI players are eligible from week
5; suspended players return; only pre-cutdown IR is season-ending. So a *dispersed* distribution
with real mass above zero is the healthy signature. **If ≥ 90% of them played exactly 0 games,
escalate to `strategist` even if C1 passes** — that is too clean for a Week-1 designation and is
corroborating evidence of restatement.

**C2 — Coverage / time-dummy control. `backend`.**
Per season, per position: n M-panel veterans and the share with `wk1_known = wk1_available OR
wk1_reserve`. **If `max − min` across 2018–2024 exceeds 0.05 at any position, part of the effect is
the calendar**, per batch 7 D2, and C3(i) becomes decisive rather than merely informative.

**C3 — Effect decomposition. `backend`. GATING.**
Three single-indicator arms against G1a, contrast endpoint identical to C-C (Spearman of v2 points
order vs realised points), RB and WR only (the two BH-robust cells):
- (i) `G1a + wk1_known` — the coverage control;
- (ii) `G1a + wk1_reserve` only;
- (iii) `G1a + wk1_available` only.
Also report n and mean realised games for each of the three cells (available / reserve /
not-rostered), per position per season.

Rules, fixed now:
- (i) alone ≥ **0.5×** the full G2a effect at RB or WR → **VOID — COVERAGE ARTIFACT, G2a
  REJECTED.** (Batch 3's published VOID rule fired at 92%; 0.5 is a deliberately conservative line
  stated before the number exists.)
- (ii) carries ≥ **0.6** of the effect and (i) is small → the effect lives where the stated
  mechanism says it lives. **This is the PASS shape.**
- (iii) carries the majority → **escalate to `strategist` before adoption.** An effect that does not
  sit where the mechanism predicts is the leakage signature; "he is on an active roster" doing the
  work is not explained by "IR mechanically implies missed games."

**C4 — Make the as-of structural, not asserted. `backend`. Must land in the same commit as any
arm flip.** Three parts:
- (a) Correct the "≈ late-August cutdown" claim in all five locations named in §1 to: *"observed at
  Week 1 of the REG season (≈ NFL Week-1 kickoff); content largely but not wholly determined at the
  late-August cutdown; later than the founder's 7 September draft by 3–6 days."* If C1(D) shows
  `INA` at non-zero frequency, say so there too.
- (b) `load_preseason_rosters` gains an explicit `as_of_label` and `SeasonPanel.preseason_roster`
  **raises** unless the caller passes a `draft_date` on or after that label's date for the season
  requested. A raise, not a warning, not a tag — that is what §6.1 means by refuses.
- (c) `v2.json` records the admissibility envelope as data, not prose:
  `"roster_status_as_of": "season_N_week_1_REG"`,
  `"admissible_if_draft_date_on_or_after": "nfl_week_1_kickoff"`, plus a deployment note that the
  founder's 7 September draft **precedes** that date, so a board he actually drafts from must build
  these indicators from a draft-day snapshot (C5), never from week-1 rows.

**C5 — The measurement that converts your assumption into a number. `data-ops`. Not gating for
version adoption; gating for any board the founder drafts from.**
Capture dated, full-league roster-status snapshots into a table carrying a real `as_of_date` per
`CLAUDE.md` §4, at four points in 2026: **pre-cutdown (~24 Aug)**, **post-cutdown (~27 Aug)**,
**the day before the founder's draft (6 Sep)**, and **Week-1 kickoff**. Then report pairwise
disagreement on `wk1_available` / `wk1_reserve` against the Week-1 snapshot, for (a) all players and
(b) the FFC ADP top 250.

Interpretation, pre-committed now so it cannot be narrated afterwards — the **6 Sep vs Week-1
disagreement rate among the ADP top 250 is the direct estimate of how much of G2a's measured effect
is unavailable at the founder's draft**:
- ≤ 1% → the historical effect transfers essentially intact; the upper-bound label becomes cosmetic.
- 1–3% → adopt, and the historical +0.072/+0.048 keeps a standing "upper bound" label wherever it
  is quoted.
- > 3% → the historical figures are materially optimistic and must be re-reported as bounds, with
  the deployable estimate stated separately.
The **pre-cutdown (24 Aug) vs Week-1** rate from the same run is the direct answer for the FR-012
leagues, and it costs nothing extra given the snapshots are being taken anyway. This overlaps
thread 097 (nflverse weekly roster-status ingest) and ACTION-PLAN T6 — do not build a second
pipeline; add the dated snapshot points to that one.

**Adoption sequencing.** C1 + C1b + C2 + C3 PASS ⇒ G2a may be adopted as v2's games arm, with C4
landing in the same commit. C5 gates *deployment to a board the founder drafts from*, and
retro-labels the historical effect size. That split is deliberate: "this model version is
admissible" and "this feature is available at this league's draft date" are different claims and
should not be settled by one flag.

#### 6 · Your Q4: yes, admission depends on draft date — and it must be a fit selection, not a flag

**Rule:** `draft_date ≥ NFL Week-1 kickoff` → G2a permitted. `draft_date < cutdown` (the likely
FR-012 case) → **G0**. Between cutdown and kickoff — which is where the founder actually sits →
permitted **only** once C5's 6-Sep snapshot exists and its disagreement rate is reported; the
indicators are then built from that snapshot, not from week-1 rows.

Three things the implementing session must not do, named because each is the obvious wrong move:

1. **Do not zero the indicators at predict time on the G2a fit.** Every other coefficient in that
   GLM was estimated conditional on the indicators being present. Setting both to 0 for everyone
   assigns the entire league to the *not-rostered reference class* — the worst class — and pushes
   every projection down. That is not graceful degradation, it is a silent bug that will look like
   a modelling choice.
2. **Do not fall back to G1a.** It was rejected by its own registered rule (0 WIN, 1 BH-robust WR
   HARM). Reaching for it because it is "closer to G2a" is post-hoc arm selection, which is the
   exact thing the registration exists to prevent. G0 is the registered default and it is what a
   pre-cutdown league gets.
3. **Do not add a "pre-cutdown-determinate subset" arm** (suspensions + offseason retirements only)
   on the strength of this reply. It is a genuinely good idea and it is the right thing to try for
   the FR-012 leagues. It is also one new arm, one new change, and it needs its own registration in
   the manifest before it is fitted. Registered here as a *candidate*, explicitly **not approved**.

#### 7 · Ship review — CHANGES (five items, all documentation or config; nothing re-runs)

**PASS, affirmatively, on four things.** (1) The no-consensus ordering path holds:
`scoring_layer.py:rank_within_position` reads no consensus column and there is no ADP/ECR/consensus
read anywhere in the v2 ordering path — verified by reading, ADR-069(1) satisfied. (2) **The
registered adoption rule rejected the builder's own primary arm, twice** (G1 and G1a, on a
BH-robust WR HARM the downside branch had predicted in advance). That is the strongest evidence in
this package that the registration was binding rather than decorative, and it materially raises my
prior that the G2a grade is honest — it is why this ruling is ADMIT-WITH-CONDITION rather than a
demand for a full re-run. (3) The portability NaN false-PASS was caught by the builder and recorded
rather than shipped; correctly labelled descriptive, 0 tests. (4) 2025 never read; §6.5 correctly
deferred as a release gate per ADR-069, run later by someone else.

Now the changes:

| # | Item | Why |
|---|---|---|
| **S1** | The cutdown→Week-1 correction in all five locations (C4a) | Factually wrong, and it is the exact fact the ruling turns on |
| **S2** | `v2.json` `evaluation.family.m_b` says **12**; Amendment 1 raised it to **20** and the manifest and campaign M=92 are computed on 20. **The config and the manifest disagree.** Fix the config to 20 | m_b feeds the campaign denominator. A config that under-reports its own cell count is how a denominator quietly drifts |
| **S3** | `v2.json` `games_component.arms` lists G0/GN/G1/G2 — **not G1a/G2a**, two of the four arms that actually ran, under `"immutable_once_run": true`. Add an explicit `amendment_1` sub-object recording G1a/G2a rather than editing the original block | Preserves immutability while making the config a faithful record of what ran |
| **S4** | State the Amendment-1 peek-span overlap in batch-B1.md's outcomes section, one sentence | See below |
| **S5** | Document the reference-class ambiguity in `features_v2.build_features_v2_proxy` (§3 item 3) | It is the coverage-flag geometry this project has already been burned by twice |

**On S4, because the accounting cuts both ways and both halves should be on the record.** Your
handling of the amendment was close to best-practice: the peek is recorded verbatim, the amended
arm was registered before it ran, `m_b` went 12→20 so the new cells enter the denominator, and the
original G1 cells were run and reported rather than quietly dropped. The residue is that G1a was
*specified* after seeing G0/G1 at TE and RB for 2018–2019, and C-A′ is then evaluated over a
seven-season span that includes those two — a 2-of-7 optimistic overlap on G1a's +0.084 that is not
currently stated anywhere. Two mitigations belong in the same sentence: G1a was **rejected anyway**
on C-B′, so the overlap rescued nothing; and — this matters for the ruling — **the week-1
indicators were registered in the original, pre-peek batch-B1 as G2.** The *treatment* in the C-C
contrast is peek-clean even though its comparator is not. That is a real defence of G2a
specifically and it is part of why I am not rejecting.

#### 8 · One piece of independent corroboration, and what it obliges us to do

Batch 2 already measured this signal from a different direction and did not realise it was the same
one. `move_known` — "he is on some club's Week-1 roster" — carried **95–97% of that arm's entire
measured effect** and is recorded in `CURRENT-STATE.md` as worth **1.6–2.3% of component MAE,
larger than anything either factor batch produced**, with the note that the availability sub-model
does not use it. G2a is that same information promoted from an accidental control into a declared
feature.

This cuts both ways and I am reporting both. It **raises** my prior that +0.072 is real: an
independent measurement, on a different harness, in a different batch, found the same channel
carrying a large effect. It also **obliges** the decomposition: batch 2 treated that finding as a
contaminant requiring disclosure and decomposition, batch 3 wrote a VOID rule for exactly this
shape, and consistency requires G2a get the same treatment rather than a pass on the strength of a
better-told mechanism story. C3 is that treatment.

#### 9 · My own pre-registered predictions, written before any of C1–C5 exists

Recorded so I can be wrong in writing, per this project's calibration record (four of five of my
registered prediction sets across sessions 3–4 were materially wrong, all over-crediting a story).

| # | Prediction | Confidence |
|---|---|---|
| P1 | C1 **passes** — nflverse weekly rosters are genuinely weekly, (A) lands 4–12%, (B) in the dozens per season | 80% |
| P2 | C1b: **35–70%** of `wk1_reserve = 1` panel veterans play 0 games — dispersed, not a spike at zero | 70% |
| P3 | C2: `wk1_known` ≥ 0.97 and near-flat across 2018–2024 for panel veterans (these are ADP-covered players, nearly all rostered), so the coverage-artifact risk here is **low**, unlike batch 7 | 75% |
| P4 | C3: `wk1_reserve` alone carries ≥ 0.6 of the RB effect; `wk1_known` alone carries < 0.25 | 65% |
| P5 | C5: 6-Sep-vs-Week-1 disagreement among ADP top 250 lands in the **1–3%** band | 60% |

If P4 fails — if the effect sits in `wk1_available` — I expect that to be the finding of this whole
exercise, and it will not be a good one.

#### 10 · What I did not rule on, and what I could not check

- **Not ruled:** cross-positional replacement (ungraded by design, correctly excluded), the
  −2.6-game board-veteran level bias (a named open defect and a candidate arm, not this thread's
  question), the rookie sub-model, DEF, and the §6.5 release gate (correctly deferred; when it runs
  it runs against **both** crowds per the 2026-07-31 amendment, and not by fable).
- **Could not check, by design — no database access.** Every C1/C1b/C2/C3 quantity. If any of them
  comes back and someone wants to argue the rule was wrong, argue it against the thresholds above,
  which were written before the numbers existed.
- **Needs a founder answer, not an agent's:** the FR-012 leagues' draft dates. Until they are
  known, those leagues get G0 by the §6 rule, and that is the safe default rather than a placeholder.
- **Needs verification, cheap:** the exact 2026 Week-1 kickoff date, from `schedules` or the league
  calendar, rather than from my Thursday-after-Labor-Day arithmetic. The ruling does not change if
  it moves by a day; the C4(c) config value does.

**Follow-on thread staged, not allocated** (I have no Bash and do not hand-type thread IDs). Body at
`docs/preregistration/HANDOFF-BODY-g2a-admission-conditions-2026-08-01.md`, carrying C1–C5 verbatim
for `backend` and `data-ops`. `pm` allocates it with `tools/handoffs.py new`; the exact command is
in my session report. Marking this thread RESOLVED because the ruling asked for is delivered — but
§5's gating sentence stands regardless of whether that thread is landed promptly: **G0 until C1/C2/C3
return PASS.**
