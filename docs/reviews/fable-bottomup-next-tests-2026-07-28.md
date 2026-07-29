# F-A — The next registered test set for bottom-up rankings

**Date:** 2026-07-28 · **Author:** Fable (short-window mandate, F-A)
**Status:** Design + pre-registration draft. Nothing here is a registration until it goes through
the ADR-C machinery (`src/preregistration.py`, family manifest) — this document is the frozen
*content* for that registration, written before any run, per FR-010.
**Evidence base:** `FABLE-EXT-2026-07-27.md` (session-2 prototype table), `FABLE-EXT2` (V3/V5/V6),
`FABLE-EXT3` (V7 falsified, calibration prior), ADR-E + amendment E-A1, `ACTION-PLAN-2026-08.md`
(H3 gate, ground rule 5). Configuration count entering this document: **8 of the 20-config LOSO
budget spent** (V1, V2, F1, V3, V4, V5, V6, V7).

---

## Conclusion (read this even if you read nothing else)

**1. The falsification condition for bottom-up as a whole:** one confirmatory F-BOTTOMUP-CORE run
on frozen V5, H3-gated and red-teamed. **If neither RB nor WR clears ADR-E §9's four conditions
against the prior-season-points baseline, bottom-up is dead as a 2026 product input** — the board
ships consensus-only at every position, no overlay, and the only bottom-up activity left this year
is the free 2026 prospective registration. Two auxiliary triggers produce the same stop: **calendar**
(the run has not happened, fully gated, by **2026-08-22**) and **budget** (the 20-config LOSO cap is
reached before the freeze). A rushed, ungated, or unregistered run does not substitute for the real
one; if we cannot do it properly by the deadline, the answer is consensus, not a shortcut.

**2. The next registered set is three runs, in this order, costing 3 of the 12 remaining configs:**
N-1 (direct-projection collapse control), N-2 (universe/rookie-inclusion sensitivity, resolving C3),
then A0 (the confirmatory run itself, after H3 lands). Plus P-2026, the prospective registration of
our full 2026 rankings before Week 1 — zero compute, cannot leak, highest information per unit cost
of anything on this list. **No new feature families.** The calibration prior (4 of 5 registered
prediction sets wrong, all over-crediting situation stories) is applied here as a hard rule, not a
mood: every remaining pre-draft test is structural (architecture, universe, gating), none is a new
story about why a player will get more work.

**3. TE gets no dedicated run.** It rides along in A0 at zero marginal compute with a pre-registered
adoption rule; the predicted outcome is that it fails to clear and ships consensus.

**4. Weights are derived where the folds can support it (S1 ridge, S2 shrinkage — already the
design) and defaulted with provenance labels where they cannot** (recency = uniform, leverage =
interim 1:2). We do not have the data to fit structural weights, and this document says so rather
than fitting them anyway.

**5. The smallest honest "beats consensus at anything" claim available before the season is not a
modelling claim at all:** our board prices this league's actual scoring and roster rules exactly
(stacking yardage bonuses, 0.5 PPR, measured replacement levels), and format-generic consensus ADP
does not. That is arithmetic, already verified (ADR-052), and it is the only consensus-relative
claim we can make in 2026. Everything else is either a veteran-ordering accuracy claim vs a naive
baseline (available only if A0 clears) or waits for January 2027.

---

## 1. Falsification condition for bottom-up as a whole

Stated now, before we are invested, per the mandate.

**The event:** the single confirmatory F-BOTTOMUP-CORE run — V5 frozen exactly as carried out of
session 4, universe per the C3 resolution (§3 below), R5 calibration family attached, H3 prereg
gate wired, red-team pass complete, registered before execution.

**The condition:** ADR-E §9's four-part rule, applied per position: (i) embargoed-LOSO paired
improvement over the prior-season-points baseline positive in ≥ 75% of folds with the season-level
bootstrap 95% CI excluding 0 after BH; (ii) same sign on points-per-game-played; (iii) no
outstanding §8 audit trigger; (iv) cross-process determinism.

**The verdict rule:** RB and WR are the only positions with exploratory evidence (Δτ vs B1
+0.041 [+0.001, +0.080] and +0.043 [+0.017, +0.071] at the session-2 prototype; RB +0.057 under
V5). **If neither clears, bottom-up as a whole is falsified for 2026.** Ship the consensus-anchored
board with no bottom-up overlay, write the shelving finding in the form ADR-E §9 already
pre-committed ("not measurably more accurate out-of-sample than the existing rank-derived curve"),
and stop. If exactly one clears, the mixed per-position board (D-023) is the outcome, not a
project-level verdict either way.

**What does NOT count as falsification, stated to prevent goalpost drift in either direction:**
QB failing (closed, six configurations, expected); TE failing (predicted below); the consensus gap
not closing (already accepted — two clean channel eliminations ended that program; the
labelled-overlay posture stands regardless of A0's result).

**Auxiliary stop triggers, same outcome:**

- **Calendar.** Draft is provisionally 2026-08-30. The run requires H3 (~1 backend session, not
  started), N-1/N-2 (~1 session), freeze + red-team (~1 session), then the run. If the gated run has
  not completed by **2026-08-22** (one week of board-integration margin), consensus ships for 2026
  regardless of how promising the exploratory numbers look. Promise is not a result.
- **Budget.** 8 of 20 configs are spent. The plan below spends 3 more. If the count reaches 20
  before the freeze, LOSO is demoted to exploratory by ADR-E's own rule, the sealed read cannot
  carry a confirmatory claim alone at any useful power, and the same stop applies.

**Scope of the death sentence:** "stop" means stop for the 2026 draft product. P-2026 (§2.4) runs
either way, because it is free and is the only instrument that can ever ground a market claim. A
2026 prospective result that beats consensus would reopen the program for 2027 with real evidence;
a result that loses to prior-season-rank would close it with the same.

## 2. The pre-registered next hypothesis set

Ranked by expected information per unit of compute. Predictions are stated with direction,
magnitude, and refutation condition *before* any run, and each run must be registered through
ADR-C before execution. Execution order differs from rank order only in that A0 must come last.

### 2.1 N-1 — Direct-projection collapse control (1 config)

**Question:** does the two-stage S1×S2 architecture earn its complexity over a single direct
point-projection ridge on the same declared features, same folds, same universe? This is ADR-E's
own declared falsification arm, never yet run.

**Prediction:** two-stage ≥ direct at RB and WR; paired Δτ (two-stage − direct) in **[−0.01,
+0.03]** at both.
**Refuted if:** direct beats two-stage by **> 0.02 τ at both RB and WR** (fold-majority). Then the
split is decoration; the *direct* model becomes the frozen A0 candidate and the S1/S2 machinery is
collapsed by ADR-E amendment. Either outcome is decision-grade: one config buys the architecture
decision.
**Why rank 1 (after P-2026):** it can change what gets frozen, so it must precede the freeze, and
it is the cheapest question with a structural consequence.

### 2.2 N-2 — Universe sensitivity: rookie inclusion (1 config, resolves C3)

**The discrepancy this settles:** the prototype universe (registered session 2) requires a
prior-season finish, excluding rookies; ADR-E §2's declared universe *includes* rookies inside
pre-season consensus depth where consensus exists. These cannot both be the confirmatory universe.
C3 exists to resolve it, and it must be resolved before the freeze because it defines the
evaluation set.

**This is not a situation story.** It is a survivorship/universe-definition question — the one
family of remaining question the calibration prior does not indict.

**Prediction (anti-inflation, stated deliberately against our own interest):** including rookies
**inflates** RB Δτ vs B1 by **≥ +0.02**, spuriously — B1 ranks every rookie at zero (no prior
season), which is maximally wrong for hits, while our model at least places them somewhere via
situation features. Simultaneously the descriptive consensus gap **widens** by ≥ 0.02, because ECR
prices rookies well and we do not.
**Refuted if:** veteran-only and rookie-inclusive universes agree within **±0.01 Δτ** at RB and WR
— then the universe choice is evidentially immaterial and C3 collapses to a product-display
question.
**Decision rule, pre-committed:** whatever N-2 shows, **the A0 headline claim is scoped to the
veteran universe.** If the inclusive run inflates our margin, that inflation is reported as an
artifact of B1's rookie blindness, not banked as skill. Rookies appear on the product board priced
by consensus/draft-capital, source-labelled, never by bottom-up — bottom-up has no usage features
for them by construction, and inventing placements would be the exact failure mode PR-002 and the
calibration prior exist to prevent.

### 2.3 A0 — The confirmatory F-BOTTOMUP-CORE run (1 config, last, H3-gated)

**Prerequisites, all hard:** H3 wired (prereg gate routing season reads through the registration —
~1 backend session, currently NOT STARTED — this is the critical-path item); N-1 and N-2 resolved
and folded into the freeze; R5 calibration family attached; red-team pass on the frozen package;
registration committed before the run.

**Predictions:**
- **WR clears** (highest confidence — tightest exploratory CI, +0.043 [+0.017, +0.071], 10/13
  folds). Expected confirmatory Δτ **[+0.02, +0.06]**.
- **RB clears** (moderate confidence). Expected Δτ **[+0.03, +0.07]** (V5 carried +0.057).
- **TE fails** condition (ii) or (i) — see §3. Reported as unproven → consensus ships at TE.
- **QB is not run confirmatorily.** Closed. Descriptive numbers only, no prediction stakes.
**Refuted per §1** — this run *is* the falsification event; its refutation condition is the
project-level one.

**Guard restated:** any season-points R² > 0.40 triggers the ADR-E §8 audit posture before any
number is reported, internally or externally. A result that looks too good escalates to the
founder as suspected leakage, per CLAUDE.md §8.

### 2.4 P-2026 — The prospective registration (0 compute, mandatory, deadline-bound)

Register the full 2026 per-player rankings — bottom-up arm and shipped board both — hashed and
committed **before Week 1** (practically: before the 2026-08-30 draft, final deadline ~2026-09-04).
Scored after the season against consensus ADP, prior-season-rank, and the positional-tier
heuristic. It cannot leak because the outcomes do not exist. It is the only path to any future
market claim, its n will be 1, and it carries falsification power only — all three limitations
stated now so they cannot be discovered later. **This is a calendar dependency, not a backlog
item** (ADR-E consequences already say so; this document re-registers the deadline).

### 2.5 Explicitly deferred — and why

| Item | Why deferred |
|---|---|
| F-BOTTOMUP-RECENCY family (m=36, 9 arms) | 9 LOSO configs against 12 remaining; underpowered at n=13 folds; defaults A0/B0 ship labelled unvalidated. Off-season work. |
| Any new feature family (V8+) | Calibration prior. Two clean eliminations (vacated opportunity, rookie draft capital) closed the gap-hypothesis program. Zero pre-draft spend. |
| TE-specific modelling | §3. |
| QB in any form | Closed, six configurations. The mandate says do not reopen it; this registration honours that. |
| Week-leverage measurement (N2 simulator) | Not a ranking test; interim 1:2 weights ship with provenance labels (E-A1). |

## 3. TE — worth a run?

**No dedicated run. Rides along in A0 at zero marginal compute, with its adoption rule
pre-registered here.**

The evidence is genuinely split, which is why "unproven, not failed" is the right description:
Δτ vs B1 **+0.073 [−0.005, +0.152]** — the largest point estimate of any position, CI includes
zero, 8/13 folds; VBD-capture Δ **+0.076 [+0.032, +0.123]** — CI *excludes* zero; but season-points
R² **−0.85** — the point projections are far worse than the positional mean even where the ordering
improves. That last number is disqualifying for board adoption on its own: a mixed-source board
takes bottom-up's *projected points*, and at TE those are wild.

On "too low-variance to matter": the structural argument mostly holds. 10 teams, 1 TE slot,
TE10 replacement, and flex spots that TEs rarely win — the draft-relevant TE decisions reduce to
roughly two (which elite TE, and when). A τ improvement concentrated below TE8 moves approximately
nothing through the roster; the VBD-capture signal suggests the improvement is top-heavy, which is
the one reading under which TE *could* matter — and that is exactly what A0 will measure for free.

**Pre-registered TE rule for A0:** adopt bottom-up at TE only if it clears all four §9 conditions
*including* points-per-game sign agreement. **Prediction: it fails** — condition (ii) is where the
−0.85 R² bites. If it unexpectedly clears all four, adoption follows the rule, not this prediction;
that is what the rule is for.

## 4. Weighting — derived where possible, defaulted with labels where not

The honest split, per component:

| Weight | How set | Status |
|---|---|---|
| S1 feature weights | Per-position ridge, **fit inside each training fold** | Derived. Already the design; keep. Never hand-set. |
| S2 shrinkage constants `k` | Fit per statistic inside each fold, caps pre-committed (w ≤ 0.60 yards, ≤ 0.20 TD) | Derived with a governor. Keep. |
| Season-level recency (B-arms) | **Cannot be fit** — 13 fold-seasons cannot separate 4 arms per position without eating the config budget | Default **B0 (3 seasons, equal weight)**, labelled unvalidated; F-BOTTOMUP-RECENCY stays registered for the off-season. |
| Within-season recency (A-arms) | Same power problem, plus the contamination confound ADR-E §6 names | Default **A0 (uniform)**, same label. |
| Week-leverage | No simulator yet (N2 unbuilt) | Interim 1:2 regular:playoff, mean-1 normalised, provenance-labelled `interim_hand_set_v1` (E-A1). Never hand-tuned twice. |
| Bottom-up ↔ consensus blend | **Refused entirely.** Ranking sources are never blended (CLAUDE.md §4 schema principle); n=4 consensus seasons could not fit a blend weight anyway | Overlay is displayed beside consensus, source-labelled, never averaged into it. |

The pattern is the project's existing D-004 pattern and it is the defensible default the mandate
asks for: **where the folds can estimate a weight inside the training loop, estimate it there;
where they cannot, ship a flat/uniform default with a provenance label and a pre-registered
adoption rule for replacing it — and never a hand-picked number presented as fitted.** "We do not
have enough data to fit the structural weights" is the true sentence, and this document says it.

## 5. The smallest honest claim

Three nested claims, smallest first. Only the first involves consensus, and it is the only one
available before the season.

1. **Claimable today (arithmetic, not prediction):** *"For this league's actual rules — stacking
   yardage bonuses, 0.5 PPR, verified roster shape and measured replacement levels — our board
   prices the scoring format exactly; format-generic consensus ADP does not."* Grounded in the
   scoring engine's tests and the ADR-052 live-platform verification. This beats consensus at
   **bookkeeping**, not forecasting, and must be stated that way. It is also, honestly, where most
   of a single-league tool's real edge lives.

2. **Claimable iff A0 clears (pre-draft, accuracy, not edge):** *"Out-of-sample (embargoed LOSO,
   13 folds, seasons 2012–2024), the bottom-up projection orders veteran RBs/WRs — players with a
   prior-season positional finish inside draft-relevant depth — better than ranking by prior-season
   fantasy points, Δτ = [value] [CI], under this league's scoring."* ADR-E §7.3's language rules
   apply verbatim: no "beats the market," no "edge over ADP," no implication that list accuracy
   converts to roster outcomes.

3. **Claimable January 2027 at the earliest:** any statement comparing our rankings to consensus
   on performance, via P-2026, n=1, falsification-grade only.

There is no configuration of work between now and 2026-08-30 that produces an honest
"our rankings beat consensus at forecasting" claim. The n=4 consensus window and the −0.110 RB
descriptive gap both forbid it. Claim 1 is what we can say; the discipline is wanting to say it
and nothing more.

---

## Checks applied (statistical-guardrails accounting)

No backtest was run in this session; this is design and pre-registration only. Guardrails applied
at design level: look-ahead (§6.1 — P-2026 chosen precisely because it cannot leak; N-2's universe
frozen pre-season), survivorship (§6.2 — C3 resolution is the survivorship control), multiple
comparisons (§6.3 — 3 registered configs against a visible 20-cap, BH within declared families,
recency family deferred rather than run underpowered), baseline rule (§6.5 — falsification defined
against the prior-season-points baseline; consensus kept descriptive at n=4), and the
too-good-to-be-true escalation (§8 audit posture restated in A0).
