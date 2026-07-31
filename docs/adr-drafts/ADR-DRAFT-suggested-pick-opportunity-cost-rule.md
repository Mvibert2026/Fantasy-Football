# ADR-DRAFT — The suggested-pick decision rule: opportunity cost, not a survival score

**Status:** DRAFT. Allocate a number with `python tools/handoffs.py adr next` before landing.
**Author:** `strategist`, 2026-07-30. **No database access, by design** — every number below is
read from a committed artifact (`data/export/availability.json`) or from source, and each is cited
to `file:line` so it can be checked without trusting me.
**Answers:** `docs/founder-requests/FR-2026-07-30-recommendation-logic-is-inverted-it-prefers-the.md`
**Also answers the referral design parked here:** `docs/design/DRAFT-MIDDLE-PANE.md:119-120` —
*"FR-051 also floats feeding this into the recommendation. That is a model change to register with
`strategist`, not a display decision."*

---

## 1. What the founder saw, and what he is right about

On the clock at pick 18 the tool recommended Josh Allen (QB1) over Trey McBride (TE2) and explained
the choice by Allen being **71% likely to still be available at pick 23** against McBride's **25%**.
His objection: *"you'd take the player with less chance of being there if you wait, not more."*

He is right that the stated rule is inverted, and he found it from the product's own words, which is
the strongest possible form of the complaint. **He is not right about the rule that replaces it**,
and the difference matters — §3.4.

He is also right about something he did not say: the sentence he read is not a description of what
the software did. It is a fabricated explanation. That is worse than a wrong ordering, and §2 is
about that.

---

## 2. Sign error or structural error? **Structural, and then some.**

### 2.1 There is no survival term to flip

`frontend/ui/data/recommendation.ts:64-72`:

```ts
export function recommendationScore(
  row: BoardRow,
  round: number,
  unfilledPositions: ReadonlySet<string>,
): number | null {
  if (row.vbd.kind !== 'present') return null;
  const terms = recommendationTerms(row, round, unfilledPositions);
  return row.vbd.value + terms.reduce((sum, t) => sum + t.points, 0);
}
```

`recommendationTerms` (`recommendation.ts:32-49`) returns at most three things: `unfilled_need +8`,
`tier1_te +18`, `early_qb_penalty −25`. **No availability term of any sign exists.**

The decisive evidence is the **signature**, not the body: `recommendationScore` and
`rankByRecommendation` (`recommendation.ts:82-97`) take `(row, round, unfilledPositions)`. They
receive no `Dataset`, no `LeagueConfig`, no pick log. `availability.json` is not reachable from
inside the ordering function. The call site confirms it — `DraftRoom.tsx:912-920` calls
`rankByRecommendation(available, currentRound, unfilledPositions)` and passes none of the three
arguments a survival read needs.

**A sign error is a coefficient with the wrong polarity. There is no coefficient.** Anyone who
"fixes the sign" will add availability as an additive term in VBD points, and that is the wrong
object — §3 shows survival enters as a *multiplier on an opportunity cost*, not as an addend on a
value. The sign/structure distinction is not pedantry here; it determines whether the fix is
correct or merely differently wrong.

### 2.2 The card states a causal claim about code that did not run

`DraftRoom.tsx:945-1023` (`recommendationDetail`) computes availability **after** the ordering is
already fixed — it reads `recommended[0]` and `recommended[1]`, which were produced at
`DraftRoom.tsx:912-920` before any availability call happened. Then:

`DraftRoom.tsx:1005`:

```ts
survivalClause = ` ${topName} is ${percent(topPct)} to still be there at ${followingUserPick} and ${altName} is ${percent(altPct)}. That difference, not the point gap, is the reason for the order.`;
```

**That sentence is false, unconditionally, on every render.** The order is `vbd + 8 + 18 − 25`
sorted descending. The two percentages in the same sentence were computed twenty lines later and
have never influenced an ordering in this codebase. This is the single most serious defect in the
report, because it is a claim about the product's own reasoning that the product cannot support,
and it is stated to the founder under a draft clock.

### 2.3 The word "only" is hardcoded

`DraftRoom.tsx:960-961`:

```ts
const survivalFragment = (pct: number | null) =>
  pct !== null && followingUserPick !== null ? `, and only ${percent(pct)} likely to survive to your pick at ${followingUserPick}.` : '.';
```

`only` is unconditional. **71% renders as "only 71%".** A number meaning *he will probably still be
there* is delivered in the rhetoric of scarcity. This is the proximate cause of the founder reading
an inverted rule off the screen — and the rhetoric was, in that instant, more informative than the
code, because it at least implied a rule.

### 2.4 The assistant is not at fault, and that is worth recording

`frontend/ui/assistant/pageContext.ts:164` ships the card's own text to the model as
`Stated reason: ${rec.reason}`, and `:174` ships the give-up text. The assistant's verbatim
"he's just 71% likely..." is a faithful paraphrase of `DraftRoom.tsx:974` + `:961`. **The assistant
inherited the inversion; it did not invent it.** It then independently contradicted the
recommendation with the simulation finding (FR defect 1), which is the reasoning lane working
correctly against a broken recommender.

### 2.5 The missing term is already on screen, and is explicitly forbidden from being used

`DraftRoom.tsx:134-153`, `findLikelyThereCandidate` — *"the single highest-VBD available player
(excluding the one already being considered) with at least even odds of surviving to `pick`."*
Rendered at `DraftRoom.tsx:2517` as **"LIKELY BEST AVAILABLE AT YOUR PICK 23"**. That is a crude
estimate of exactly the quantity §3 calls the continuation value $u_f$ — the term whose absence
causes the whole defect. Its own docstring (`DraftRoom.tsx:132`) says *"Display only, per the
design doc's explicit instruction not to feed this into the recommendation."*

The instruction was correct at the time: design routed the model change to `strategist` rather than
making it as a display decision (`DRAFT-MIDDLE-PANE.md:119-120`). **This ADR is the answer to that
referral.**

### 2.6 Classification, for the record

| # | Defect | Class | Location | Needs a measurement? |
|---|---|---|---|---|
| 1 | Ordering ignores availability entirely | **Structural — term absent from the model** | `recommendation.ts:64-72`, `:82-97` | **Yes** — §5 |
| 2 | Card asserts survival caused the order | **False claim about own behaviour** | `DraftRoom.tsx:1005` | No. Fix now. |
| 3 | "only X%" for every X | **Unconditional intensifier** | `DraftRoom.tsx:960-961` | No. Fix now. |
| 4 | Board `AVAIL` is the probability of an event you can see already happened | **Wrong target pick** | `DraftRoom.tsx:1915` vs `:634` | No. Fix now. §6 |

---

## 3. The correct rule, stated formally

### 3.1 Setup and objective

On the clock at overall pick $t$; the user's own next pick is $t'$ (from
`availability.json:metadata.picks_by_slot`). $\mathcal{A}_t$ is the undrafted pool, $R_t$ the
user's roster so far. The objective is the one `draft_sim.weekly_optimal_points` already
implements: expected season points of the final roster under a weekly-optimal legal lineup, with
$P(\text{top-4})$ as the league's real secondary objective (`CLAUDE.md` §7).

### 3.2 The two-branch value — the general form

For a candidate $X \in \mathcal{A}_t$:

$$
V_t(X)\;=\;u\!\left(X \mid R_t\right)\;+\;\mathbb{E}\!\left[\;\max_{Y \in \mathcal{A}_{t'}(X)} u\!\left(Y \mid R_t \cup \{X\}\right)\right]
$$

**Take $\arg\max_X V_t(X)$.** Every term named:

| Term | Name | What it is | Data it needs |
|---|---|---|---|
| $u(\cdot \mid R)$ | **marginal value** | Season points this player adds to *this* roster under a weekly-optimal legal lineup. Zero-ish for a second QB in a 1-QB league. | Today approximated by `board.json:players[].vbd`, which is roster-*un*conditioned. The gap is FR-115 / test #35. |
| $\mathcal{A}_{t'}(X)$ | **survivor set** | The random set still undrafted at $t'$ given $X$ was taken at $t$. | The opponent model: `availability.json:client_simulation_parameters`, post-thread-119. |
| $\mathbb{E}[\max \ldots]$ | **continuation value** | What you actually expect to get at your next turn. | A **joint** distribution over survivors, not per-player marginals — see §4. |

**Survival probability does not appear in this expression.** It appears only when the expression is
reduced, and it appears attached to the branch you *did not* take. That is the whole content of the
founder's complaint, stated precisely.

### 3.3 The two-candidate reduction — the interpretable form

Let $S_X$ = "$X$ survives to $t'$", $p_X = \Pr(S_X)$, and define

$$
q_X \;=\; 1 - p_X \quad\text{(the probability he is \textbf{gone})}, \qquad
u_{f_X} \;=\; \mathbb{E}\!\left[\max_{Y \in \mathcal{A}_{t'},\, Y \neq X} u(Y \mid \cdot)\right]
$$

$u_{f_X}$ is the **fallback**: the best you expect to get at $t'$ in the branch where you did *not*
take $X$. Write $g_X = u_X - u_{f_X}$, the **gap over your realistic fallback** (not over a static
replacement level). Then, for two candidates $A$ and $B$:

$$
\boxed{\;V_t(A) - V_t(B)\;=\;q_A\,g_A\;-\;q_B\,g_B\;}
$$

**Take $A$ over $B$ iff $q_A g_A > q_B g_B$.**

$q_X g_X$ is the **expected value lost by waiting** — literally, (chance he's gone) × (how much
better he is than what you would take instead). It is a loss, so you take the player whose loss is
largest.

<details>
<summary>Derivation, so nobody has to trust the algebra</summary>

With a fallback $f$ common to both branches,
$C(A) = p_B u_B + (1-p_B) u_f$ and $C(B) = p_A u_A + (1-p_A) u_f$. Then

$V(A)-V(B) = (u_A - u_B) + p_B u_B - p_B u_f - p_A u_A + p_A u_f
= u_A(1-p_A) - u_B(1-p_B) - u_f\big[(1-p_A)-(1-p_B)\big]
= (1-p_A)(u_A-u_f) - (1-p_B)(u_B-u_f) = q_A g_A - q_B g_B.$

Position-specific fallbacks ($u_{f_A} \neq u_{f_B}$, the QB-vs-TE case) give the same form with
$g_X = u_X - u_{f_X}$; the two-position version drops straight out of §3.2 as
$V(A)-V(B) = \big(u_A - \mathbb{E}[\max_{QB,S}]\big) - \big(u_B - \mathbb{E}[\max_{TE,S}]\big)$,
and $\mathbb{E}[\max_{QB,S}] = p_A u_A + q_A u_{f_A}$ recovers $q_A g_A$ exactly.
</details>

### 3.4 Four rules, three of them wrong, and each wrong in a nameable way

| Rule | What it assumes | Consequence |
|---|---|---|
| **Shipped today** (`recommendation.ts:64-72`) | $q \equiv 1$ **and** $u_f \equiv$ a static per-position replacement level | Collapses to plain VBD + three constants. Scarcity structurally cannot enter. |
| **Test #36's VONA arm** (thread 111) | $q \equiv 1$, $u_f$ position-specific from a deterministic gap-count | Over-reaches — credits scarcity in full whether or not it materialises. **Measured at −106 [−182,−54] / −126 [−215,−69] points vs plain BPA.** |
| **The founder's shorthand** ("take the one less likely to be there") | rank by $q$ alone; $g$ ignored | Drafts a 1%-survival replacement-level player ahead of a 60%-survival star. $q=0.99$, $g \approx 0$, $qg \approx 0$ — the correct rule already refuses this; his does not. |
| **Correct** | both factors | $q_X g_X$ |

**The finding worth carrying out of this ADR:** the shipped recommender and the tested-and-rejected
VONA arm make the *same* error — hardcoding $q = 1$ — in opposite directions. VBD's $q\equiv1$ is
benign because its $u_f$ is a constant per position, so it cancels within a position and is a fixed
offset across positions. VONA's $q\equiv1$ is harmful because its $u_f$ moves with the candidate,
so the un-discounted gap gets credited in full. **Nobody has yet run the version with both terms.**
Thread 111's −110-to-−126 caution therefore does *not* license "opportunity-cost drafting loses";
it licenses "opportunity-cost drafting with the survival term hardcoded to 1 loses," which is a
narrower claim and is very close to the thing the founder is complaining about.

### 3.4b The early-QB simulation finding: does the recommender ignore it?

The assistant told the founder that *"reaching for a quarterback in the first three rounds was the
single most costly strategy tested in simulation, negative in all 12 scenarios run, with the worst
case losing 115.4 points."* Read at source (`PR-003:114-121`, `:147-153`; arm definition
`draft_sim.py:311`, `strategy_qb_early = _positional_bias({"QB": −45.0}, early_rounds=3)`; ranker's
independent read, thread `2026-07-30-pick-18-recommendation-defect-traced-reproduced` finding 4):

**The finding is narrower than the summary in five ways, one of which the assistant got backwards.**

1. **It is a blanket policy, not a pick.** The arm applies −45 **rank points** to *every* QB in
   *every* one of rounds 1–3, against a **consensus-rank** board. That is "reach for a QB
   repeatedly, early," not "take the QB1 who happens to be the highest-VBD player left at pick 18."
2. **Effective n is 4, not 12.** "12 scenarios" is 4 seasons × 3 σ settings; the σ sweep is three
   settings of one guessed parameter over the *same* seasons, not independent evidence.
3. **It is not significant and cannot be.** 0 of 4 seasons positive, sign p = 0.125 (the floor at
   n=4), 0 of 15 comparisons survived BH in PR-003. `strategic-insights.md:181` grades it
   **MARGINAL**; `PR-003:196` licenses only *"strongly suggests."*
4. **The assistant inverted the uncertainty.** −115.4 is the **point estimate at σ=10**, not the
   worst case; the season 95% CI is **[−176.3, −54.4]**. Calling a point estimate a worst case
   understates uncertainty in the direction that flatters the claim.
5. **The units do not map.** −115.4 is season roster points from a full-draft policy simulation.
   −25 is a VBD addend inside a per-pick score. There is no conversion between them, so *"encode
   the finding"* is not a well-formed instruction.

**But the recommender is not ignoring it.** It encodes a hand-picked proxy — `−25 if QB && round <
6` — the proxy **fires** at pick 18 (round 2), and it loses. Reproduced by ranker against the real
`board.json`: Allen VBD **113.71**, McBride **49.01**, raw gap **64.70**; final scores 96.71 vs
75.01, gap **21.70**. So the constants move the differential by **43.00 points** and fall 21.70
short. (Their absolute magnitudes sum to 51, which is a different quantity — the +8 applies to both
candidates and cancels.)

**The honest resolution of the contradiction:** the recommender neither ignores the finding nor
encodes it. It carries an **unfitted constant standing in for a finding measured in incompatible
units, whose magnitude has never been checked** — because PR-007, the instrument that checks it,
has never run.

**And the deeper point, which is the argument for §3.3.** A correct rule should not need this
finding encoded as a constant at all. If reaching for an early QB is costly, $q\,g$ discovers it
endogenously: $g_{\text{QB}} = u_{\text{Allen}} - \mathbb{E}[\text{best QB at } 23]$ is small
whenever QB is deep, with no hand-picked penalty anywhere. **A constant is a patch for a missing
term.** That claim is checkable and is registered as diagnostic **D2** in
`docs/ranking/suggested-pick-rule-precommit.md` §4b.

### 3.5 Where I think the pick-18 error actually comes from — and it is not the survival term

Set $q_{\text{Allen}} = q_{\text{McBride}} = 1$ and the rule still moves, because $u_f$ moves.
VBD prices Allen against **QB10** (ADR-029 replacement levels; ADR-016 QB1 slot value 114.1) — but
QB10 is not the QB you would get at pick 23. The relevant fallback is QB2–QB5, which in a 1-QB
10-team league sit far closer to QB1 than QB10 does. **Substituting a static replacement level for
a dynamic fallback inflates $g$ most for exactly the position whose elite-to-replacement gap is
widest relative to its elite-to-next-best gap, and in a 1-QB league that position is QB.**

That is arithmetic, not a situation story, and I am flagging the distinction deliberately per my
standing calibration prior. But whether $g_{\text{Allen}}$ is in fact small at pick 18 depends on
QB2–QB5's projections and survival odds, which I cannot query. It is therefore registered as a
**measurable prediction with a threshold** (§5, D1), not asserted.

Consequence if D1 confirms: **"flip the sign on the survival number" is the wrong fix, and would
have left most of the error in place.** The first-order fix is replacing the static replacement
level with the dynamic fallback. Survival is the second-order correction — real, and in this case
pushing the same direction ($q_{\text{McBride}} = 0.75$ vs $q_{\text{Allen}} = 0.29$), but second.

### 3.6 Approximations this rule carries, named rather than discovered later

1. **Two-pick truncation.** $V_t$ looks ahead exactly one turn. The exact object is a full dynamic
   program to the end of the draft. Truncation error grows when the deferred position is deep
   (you could have waited *two* turns). Required: the shipped copy says *"compared against your
   next pick only."*
2. **$u$ is not roster-conditioned today.** `board.json:players[].vbd` is a global quantity. The
   `+8 unfilled_need` constant is the crude stand-in. In the correct rule, roster conditioning is
   *automatic* — a second QB has $u \approx 0$ — which is what PR-007 §13.1 meant by "the
   replacement is a model, not a constant."
3. **$\mathbb{E}[\max]$ is not $\max \mathbb{E}$.** Jensen bites here: computing the fallback from
   point projections of "the guy who'll probably be there" underestimates the continuation value.
   §4 is about doing this correctly.

---

## 4. Computing the continuation value — three options, with a required cross-check

$u_{f_X}$ is an expectation of a maximum over a **joint** survival distribution. `availability.json`
ships `by_player` (per-player marginals) and `by_tier` (P(≥1 of a tier survives) —
`docs/data-contract.md:153`). Neither is the required statistic; `by_tier` is the right *shape*.

| Option | Method | Cost | Correctness |
|---|---|---|---|
| **(i) Deterministic** | assume the top-$k$ at the position are gone, $k = \text{gap} \times \text{share}$ | free | **What #36 did. Measured to lose. Do not ship.** |
| **(ii) Independent marginals** | over the position's board order, $\mathbb{E}[\max] = \sum_j u_{(j)}\, p_{(j)} \prod_{i<j} (1 - p_{(i)})$ using `by_player[·][t']` | closed form, browser-side, uses only shipped fields | Biased by an **unknown-sign** amount: survivals are positively correlated through a positional run and negatively correlated through fixed pick supply. The sign is not knowable a priori and must be measured, not argued. |
| **(iii) Simulator-exact** | condition `simulate_availability` on live draft state, take the empirical mean of $\max_Y u(Y)$ over simulated continuations | expensive | Correct. Exactly the job thread 119 §5 says the simulator should keep — conditioned on live state, where the closed form cannot go. |

**Pre-committed:** the offline test in §5 runs **(iii)**. The shipped client may use **(ii)** only
if the acceptance check below passes; otherwise the client reads (iii)'s numbers from an export.

**Acceptance check A1 (blocking, not optional).** Report mean and max $|u_f^{(ii)} - u_f^{(iii)}|$
in VBD points, broken out by position and by intervening-pick gap (this league alternates 14 and 4).
**Pass iff mean ≤ 5 points and max ≤ 20 points** — 20 being the materiality floor M inherited from
PR-003/PR-007 unchanged. Fail ⇒ (ii) does not ship and the reason is stated on screen.

---

## 5. Pre-registered measurements

Full registration, written before any run: **`docs/ranking/suggested-pick-rule-precommit.md`**.
Family `F-OPPORTUNITY-COST-RULE`, **m = 3 confirmatory**, declared before any arm executes.
Summarised here so the ADR is readable alone; the precommit file governs.

| id | Comparison | Question |
|---|---|---|
| **H1** | `qg_rule − vbd_plain` | Does the rule build better rosters than plain VBD? |
| **H2** | `qg_rule − vona_q1` | Does the survival factor $q$ earn its place? (**the founder's actual claim**) |
| **H3** | `qg_rule − vbd_all4` | Does the rule beat what ships today? (the founder-facing headline) |
| D1 | pick-18 decomposition | Diagnostic, **exploratory, not in the denominator** — see below |
| A1 | (ii) vs (iii) fallback error | Acceptance check, not a hypothesis |

**Decision rule for each of H1–H3, pre-committed, unchanged from PR-007's structure:** ADOPT iff
mean paired margin at σ=10 **≥ +20 roster points** (M inherited verbatim from PR-003, not re-derived
for this test) **and** positive in **all** season×σ cells **and** the season-level bootstrap 95% CI
at σ=10 excludes 0. **REJECT in every other case, including every null.** Resampling unit: the
**season**. Common random numbers across arms within a cell, with a `zlib.crc32` identity assertion
on the shared `effective_rank` draw; a mismatch voids the run.

**Benjamini–Hochberg is not applied, and the reason is not convenience.** At n = 3–4 seasons the
exact sign test floors at p = 0.125–0.0625 and `paired_season_bootstrap` deliberately returns no
p-value; there is no admissible p at the registered resampling unit, so there is nothing for BH to
correct. Same ruling and the same replacement machinery as PR-007 §5, cited rather than re-derived:
fixed denominator declared in advance, all three reported including failures, unanimity across every
cell, and an explicit false-ADOPT bound (≤ 0.375 expected false ADOPTs across m = 3 at n = 3;
≤ 0.19 at n = 4). Moving the resampling unit to the simulated draft to manufacture power is refused
— the season is the argument.

**D1, the pick-18 decomposition (exploratory, never in any denominator).** Reproduce the founder's
board state, then report $u$, $p$, $q$, $u_f$, $g$ and $qg$ for Allen, McBride and the next four
candidates, plus a two-row counterfactual: the ordering with $q$ forced to 1 (dynamic $u_f$ only),
and the ordering with $u_f$ forced to the static replacement level ($q$ only). **My registered
directional prediction:** the *dynamic-$u_f$-only* arm already reverses Allen/McBride, and the
*$q$-only* arm does not. If that is wrong I want it on the record that it was predicted before it
was run. This is a single-state audit of one board, so it is a diagnostic and can never be reported
as an edge.

**Prerequisite, stated as a dependency and not a nicety.** PR-007 is registered and **has never
run** (`strategic-insights.md:171-172`; thread 093 still OPEN). Its registered prediction is that
all three constants in `recommendationScore` are deleted. Testing a new rule on top of three
unvalidated constants confounds the two. **Resolution: `qg_rule` is defined against `vbd_plain`,
never against `vbd_all4`'s constants, and H1–H3 run in the same batch and on the same CRN seeds as
PR-007's arms** so the two are directly comparable. PR-007 is not amended — amending a frozen
registration after seeing data demotes it to exploratory.

---

## 6. The two availability numbers: both correct, three different quantities, none labelled

Settled from a committed artifact, `data/export/availability.json` — **not** by inference:

| Player | pick 18, σ=10 | pick 23, σ=10 | file line |
|---|---|---|---|
| Josh Allen | **0.7875** | **0.6312** | `availability.json:1977-1986` |
| Trey McBride | **0.4042** | **0.2250** | `availability.json:1157-1166` |

So the on-screen numbers reconcile exactly:

| On screen | Value | What it actually is | Code |
|---|---|---|---|
| Board `AVAIL` | Allen 79% / McBride 40% | **Unconditional marginal at pick 18** — the pick the user is making right now | `DraftRoom.tsx:1915` uses `targetPick: nextUserPick`; `nextUserPick` **equals `currentPick` while on the clock** (`DraftRoom.tsx:634`, and the codebase's own comment at `:1093-1095`) |
| Card / assistant | Allen 71% / McBride 25% | **Live-adjusted value at pick 23** (baselines 63% / 22.5%, nudged by the need/run terms) | `DraftRoom.tsx:902-905` defines `followingUserPick`; `:952` passes it |

**Answer to the FR's question: they are different picks and both are internally correct.** The
card's own Allen-vs-McBride comparison is apples-to-apples (both at 23, both live-adjusted), so the
founder's objection to the *rule* stands entirely on its own and is not an artefact of the number
confusion.

**But nothing on screen distinguishes them, and one of them should not exist.** The `AVAIL` header
tooltip (`DraftRoom.tsx:1870`) says *"availability at your next pick"* with no pick number, and the
card says *"at your pick at 23"*. Two labels, one of which is silently a different pick.

**Worse — the board number is a probability of an event the user can see has already resolved.**
While on the clock at pick 18, every player on the board *has* survived to pick 18; the honest
figure is 100%. `computeLiveAvailability` cannot even adjust it: with `targetPick == currentPick`,
`teamSlotsBetween` returns empty and the function short-circuits to `live: null` at
`liveAvailability.ts:141-151`, so the cell renders the raw unconditional marginal. The consequence
is that **while on the clock — the only moment that matters — the `AVAIL` column never shows the
decision-relevant quantity.**

**Pre-committed disposition, needs no measurement:** while `userOnClock`, the draft board's `AVAIL`
column retargets to `followingUserPick` and the header states the pick number explicitly
(`AVAIL @ 23`). Off the clock, `nextUserPick` is already correct and unchanged.

---

## 7. Decisions, pre-committed

| # | Decision | Gate |
|---|---|---|
| **D-1** | The suggested-pick model's decision rule is $\arg\max_X q_X g_X$ (§3.3), the two-candidate reduction of the two-branch value in §3.2. Survival probability enters as $q = 1 - p$ multiplying an opportunity cost, never as an additive score term. | Methodology, settled here |
| **D-2** | `DraftRoom.tsx:1005`'s *"That difference, not the point gap, is the reason for the order"* is **deleted immediately**. Nothing may claim survival drove an ordering until §5 lands and the ordering actually reads it. | None — it is false today |
| **D-3** | `DraftRoom.tsx:961`'s unconditional `only` is replaced by wording keyed to the value. | None |
| **D-4** | On the clock, board `AVAIL` retargets to `followingUserPick` and the header carries the pick number (§6). | None |
| **D-5** | `qg_rule` does **not** ship to the recommender before H1–H3 report. Thread 111 measured the nearest relative losing ~110–126 points; the rule is better-argued, not yet better-measured. | §5 |
| **D-6** | If H1–H3 are all null, the shipped recommender falls back to **plain VBD**, and the card says so plainly. A null here does not license keeping the three constants — that is PR-007's question, not this one. | §5 |
| **D-7** | The founder's shorthand rule ("always take the one less likely to last") is **refused in writing** as a shipping rule, with §3.4's reason. His diagnosis of the sign is adopted; his replacement is not. | Methodology |
| **D-8** | Client-side fallback via the independent-marginal closed form ships only if acceptance check A1 passes; otherwise (iii)'s values are exported. | §4 |

---

## 8. What I am refusing, in writing

1. **Shipping the $qg$ rule on the strength of the derivation.** It is correct as a decision-theory
   object and that is not evidence about rosters. Thread 111 is a live, measured caution against its
   nearest relative and it is not dismissible by pointing at the $q$ term I say they were missing.
   My own calibration prior — situation narratives at half weight — applies to *me* here: "opportunity
   cost is obviously right" is a story, and it goes into a pre-registration at half weight, not into
   a shipped model.
2. **Adding an availability term to `recommendationScore` as a quick fix.** It is not additive and
   not in points units. A "sign fix" would produce a differently wrong model with a more
   convincing explanation attached, which is strictly worse than today.
3. **Fitting the rule's shape (a $q$ exponent, a blend weight against VBD) on these seasons.** With
   n = 3–4 seasons a search returns a fitted object with no out-of-sample support that then carries
   false authority. Same refusal as PR-007 §13.1, for the same reason.
4. **Reading thread 111's −110-to-−126 secondary as "opportunity-cost drafting loses."** It is
   uncorrected, its sign test floors at p = 0.125, and it tested the $q \equiv 1$ variant. It is a
   caution about a specific formulation, cited as such.
5. **Claiming the pick-18 diagnostic (D1) as evidence about the rule.** One board state, no
   resampling unit, exploratory forever.
6. **Inferring what the 2026 room will do to Allen from a market ADP proxy without the thread-119
   labelling constraint.** ADR-035's rule extends here unchanged: an FFC-derived $p$ may never be
   presented as this league's own draft room.
