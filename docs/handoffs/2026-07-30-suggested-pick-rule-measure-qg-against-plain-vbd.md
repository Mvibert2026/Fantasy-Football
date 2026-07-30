---
ID: 2026-07-30-suggested-pick-rule-measure-qg-against-plain-vbd
FROM: strategist
TO: backend
STATUS: OPEN
BLOCKS: FR-2026-07-30-recommendation-logic-is-inverted (question 3 of the founder's bar), FR-051, FR-115
OPENED: 2026-07-30
---

## Ask

Run the four-arm draft simulation registered in
**`docs/ranking/suggested-pick-rule-precommit.md`** (family `F-OPPORTUNITY-COST-RULE`, m = 3
confirmatory). The rule being tested and its derivation are in
`docs/adr-drafts/ADR-DRAFT-suggested-pick-opportunity-cost-rule.md` — **read §3 before writing any
code**, because the object is not what its name suggests and the most likely implementation error
is silently reproducing thread 111's arm.

**Do not re-derive any of it.** The precommit file governs; this thread is the runnable spec.

### The rule in one line

$$\arg\max_X \; q_X\,g_X, \qquad q_X = 1 - \Pr(X\text{ survives to } t'), \qquad g_X = u_X - u_{f_X}$$

$u_{f_X}$ = expected best marginal value obtainable at the user's *next* pick $t'$ in the branch
where $X$ was **not** taken. Survival enters as a multiplier on an opportunity cost — never as an
additive term in a points score.

### Arms (all share one underlying VBD value array)

| Arm | Definition |
|---|---|
| `vbd_plain` | $u_X - \text{repl}(pos_X)$. Comparator. |
| `vbd_all4` | `vbd_plain` + the three shipped constants (+8 unfilled need / +18 tier-1 TE / −25 QB before round 6), ported per PR-007 §1's table. What ships today. |
| `vona_q1` | $u_X - u_{f_X}$, i.e. $q \equiv 1$. **Part A alone.** |
| `qg_rule` | $q_X (u_X - u_{f_X})$. **Parts A + B.** |

`vona_q1` is deliberately *not* thread 111's arm re-run — it uses **this** design's fallback
estimator, so H2 isolates the $q$ factor and nothing else.

### The three confirmatory comparisons

| id | Comparison | Question |
|---|---|---|
| H1 | `qg_rule − vbd_plain` | Beats the researched quantity? |
| H2 | `qg_rule − vona_q1` | **Does the survival factor earn its place?** The founder's actual claim. |
| H3 | `qg_rule − vbd_all4` | Beats what ships today? Founder-facing headline. |

**ADOPT** iff (a) mean margin at σ=10 ≥ **+20 roster points** (M inherited verbatim from
PR-003/PR-007, do not re-derive) **and** (b) positive in **every** season×σ cell **and** (c)
season-level bootstrap 95% CI at σ=10 excludes 0 **and** the conjunctions (d) ΔP(top-4) sign
agreement, (e) the regime gate, (f) determinism + CRN identity. **REJECT** otherwise, including
every null. Full text: precommit §3.

### The fallback estimator — where this will go wrong if it goes wrong

$u_f$ is $\mathbb{E}[\max_Y u(Y)]$ over a **joint** survival distribution.

- **Use (iii) simulator-exact for every arm**: condition `simulate_availability` on live draft
  state, take the empirical mean of $\max_Y u(Y)$ over simulated continuations.
- **Do NOT use the deterministic top-$k$-are-gone form** — that is thread 111's `gap_length ×
  share(pos)`, it hardcodes $q = 1$ for the candidate, and it is the thing this test exists to
  correct.
- **Do NOT compute "the value of the player most likely to be there."** $\mathbb{E}[\max] \neq
  \max\mathbb{E}$. `findLikelyThereCandidate` (`DraftRoom.tsx:134-153`) is exactly that wrong form;
  it is display-only today and must not become the estimator. Precommit §5's Jensen guard.

### Blocking assertions (any failure voids the run — reply, do not caveat)

1. **CRN identity.** `zlib.crc32` of the first draft's `effective_rank` bytes, per (arm, season, σ),
   asserted equal across all arms in the cell. **Do not copy `run_draft_sim.py:68`'s
   `stable_offset(name)`** — it gives each arm a different room and destroys the pairing.
2. **Look-ahead, and this design creates a new one.** $u_f$ is an expectation over *who will still
   be available*. An implementation that computes it from the historical season's realised draft
   order leaks the answer into the decision. **Assert, executed and printed: the fallback
   estimator's inputs are the board and the opponent model only — never `data.pts`, never the
   realised pick sequence.** Plus the standing `max(training_seasons) < N` print per fitted curve.
3. Cross-process determinism: run twice in **separate** processes, compare byte-for-byte.

### STOP conditions (precommit §7 — reply, do not run through them)

Fold set < 3 seasons · CRN assertion fails · look-ahead assertion fails · `qg_rule` flip rate vs
`vbd_plain` < 1% of user picks at σ=0 (report **UNEXERCISED**) · `qg_rule` and `vona_q1` pick an
identical roster in ≥ 99% of paired drafts (H2 has no signal to measure — say so, do not report a
margin).

### Also required, both exploratory and outside every denominator

**D1 — the pick-18 decomposition.** Reproduce the founder's observed state (pick 18, his live
`USER_SLOT`, his rostered players). For Allen, McBride and the next four candidates report
$u$, $p$ at $t'=23$ (σ 5/10/20), $q$, $u_f$, $g$, $qg$ — and three orderings: shipped `vbd_all4`;
Part A only (dynamic $u_f$, $q$ forced to 1); Part A+B.
**My registered prediction, made before the run:** the Part-A-only ordering already reverses
Allen/McBride and a $q$-only variant (static replacement, real $q$) does not — i.e. the dominant
error at pick 18 is the static replacement level, not the missing survival term. I want that on the
record either way. This is one board state; it can never be reported as an edge.

**D2 — does `qg_rule` make the `−25` QB constant redundant?** (precommit §4b). Report QB selection
rate in rounds 1–3 for `qg_rule` / `vbd_plain` / `vbd_all4`; the paired margin `qg_rule` vs
`qg_rule + (−25 QB, round<6)`; and mean $g_{\text{QB1}}$ against mean $g$ for the best RB/WR
available, per user pick in rounds 1–3. **Registered prediction:** `qg_rule` under-selects early QBs
relative to `vbd_plain` with no QB term at all, and adding −25 on top moves the margin by less than
+20. If the −25 still helps materially on top of `qg_rule`, the ADR-draft §3.4b argument is wrong
and I want that said. Descriptive; does not adjudicate the −25 (**PR-007 does that**).

**A1 — fallback estimator acceptance check.** Mean and max $|u_f^{(ii)} - u_f^{(iii)}|$ in VBD
points, by position and by intervening-pick gap (this league alternates 14 and 4; `USER_SLOT=3`,
`N_TEAMS=10`), where (ii) is the independent-marginal closed form
$\sum_j u_{(j)} p_{(j)} \prod_{i<j}(1-p_{(i)})$ from `availability.json:by_player[·][t']`.
**Pass iff mean ≤ 5 and max ≤ 20.** Report the **sign** of the bias, not just the size — I am
explicitly declining to predict it. This decides whether the browser can compute $u_f$ client-side
or must read exported values.

### One sequencing constraint, and it is not a nicety

**PR-007 has never run** (`docs/strategic-insights.md:171-172`; thread 093 still OPEN). Its
registered prediction is that all three constants in `recommendationScore` get deleted. Running a
new rule on top of three unvalidated constants confounds them.

**Resolution: `qg_rule` is defined against `vbd_plain`, and H1–H3 run in the same batch and on the
same CRN seeds as PR-007's arms** so the two sets are directly comparable. **Do not amend PR-007** —
an amendment after seeing data irreversibly demotes it to exploratory. Two registrations, one run.

## Why

This is **question 3 of the founder's three model questions** — the suggested-pick model — observed
failing on 2026-07-30 in the surface he intends to use on 7 September. His bar is his own: *"If I
don't have those three things in place, I don't want to use the tool for my real draft."*

The ordering defect is structural, not a sign flip: `recommendation.ts:64-72` and `:82-97` take
`(row, round, unfilledPositions)` and cannot reach `availability.json` at all. There is no
coefficient to invert. **A "sign fix" would ship a differently wrong model with a more convincing
explanation attached — strictly worse than today**, which is why this is a measurement thread and
not a patch.

The three non-statistical defects from the same screenshot (a false causal sentence, an
unconditional "only", and the board's `AVAIL` column reading the wrong pick) are split into a
separate `frontend` thread and need no measurement — they are fixed now.

## Done looks like

1. Results appended to `docs/ranking/suggested-pick-rule-precommit.md` and the `PR-0NN`
   registration, `status: RUN`, with per-comparison verdicts against **each** of (a)–(f)
   individually — never a summary judgement.
2. For each of H1–H3: margin at each σ, per-season margins, season-level bootstrap 95% CI at σ=10,
   the simulation SE **reported separately and never combined with it**, the full sign table,
   ΔP(top-4), and the pick-flip rate + mean VBD surrendered per arm per cell.
3. D1's table and its three orderings, marked exploratory, no CI, no p-value.
4. A1's pass/fail and the bias sign.
5. All three comparisons appended to `docs/preregistration/test_run_log.jsonl`, **including
   failures**.
6. An explicit statement of which `docs/statistical-guardrails.md` checks were applied and how.
7. **One plain sentence answering the founder**, stated whichever way it lands — e.g. *"Taking
   scarcity into account this way does not build better rosters than plain best-available; the
   recommendation now sorts by VBD and says so."*

**If everything is null:** the recommender falls back to plain VBD and the card says so. A null here
does **not** license keeping the three constants — that is PR-007's question, not this one.
