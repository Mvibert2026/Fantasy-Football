---
ID: STAGED-strategist-fr136-q1-measurements
FROM: strategist
TO: backend
STATUS: OPEN
BLOCKS: FR-136 Q1 metric promotion (items 1-2); the FFC refit decision (item 3)
OPENED: 2026-07-30
---

**STAGED BODY — not yet allocated a thread id.** The strategist has no shell and must not hand-type a
thread number. PM/backend: run `python tools/handoffs.py new --from strategist --to backend --subject
"FR-136 Q1 measurements the strategist rulings depend on"`, then move this body into the allocated
file and `python tools/handoffs.py sync`. Do not compute an id by reading the directory.

## Ask

Five measurements. Every ruling in the FR-136 Q1 thread
(`docs/handoffs/2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar.md`, strategist reply
2026-07-30) that needs a number needs one of these. **I cannot run any of them — no database access,
deliberately, because an independent check that can run the analysis itself stops being independent.**

Rulings: `docs/adr-drafts/ADR-DRAFT-primary-evaluation-metric.md`,
`ADR-DRAFT-market-rank-curve-source.md`, `ADR-DRAFT-component-projection-display.md`,
`ADR-DRAFT-oracle-ladder-disposition.md`, `ADR-DRAFT-table-stakes-multiplicity.md`.

**Standing requirements on all five:** season-level bootstrap for any interval (never player-level),
integer seed recorded (guardrails §11 — never builtin `hash()`), `n` printed beside every figure,
busts retained at realised 0 points, **no games-played filter anywhere except item 5's explicitly
scoped diagnostic**, and **2025 stays sealed** except where item 1 says otherwise.

---

### 1 — BLOCKING. Confirm or refute the `top_k_starter_vbd` never-played-bust defect

Found by reading the code; not confirmed against data. **Refuting it is as valuable as confirming
it** — say so plainly if I have misread.

**The claim.** `src/backtest.py:487` (`top_k_starter_vbd`) and `:443` (`_vbd_sum_for_ranking`) both do
`total += vbd.get(pid, 0.0)`. `_vbd_lookup` (`:403`) builds `vbd` only over players present in
`_season_actuals` — i.e. players with ≥1 weekly stat row in season S. A ranked player with **no weekly
row at all** still resolves a position via `build_position_lookup`'s second query (`:234-239`,
"rankings win"), therefore **consumes a starting slot** and contributes **0.0** — exactly replacement
level on the VBD scale — when the correct contribution is `0 − replacement_points[pos]`.

**Report:**

1. Per arm (`rescored_consensus_board`, `fantasypros_ecr_raw`, `bpa_prior_season_points`), per season
   2022–2024: **the count of players in that arm's top-15 with no row in `_season_actuals`**, and
   their names. If the count is 0 everywhere, the defect is inert in practice — say so and stop at
   step 3.
2. The same count over each arm's **full ranked universe** (bears on `_vbd_sum_for_ranking`).
3. `replacement_points[pos]` for each position, each season — the actual points total at the
   replacement rank (QB10 / RB30 / WR40 / TE10). This is the magnitude a single such player is
   mis-scored by.

**Then fix it** — such a player contributes `0 − replacement_points[pos]`, in both functions —
with a regression test **written before the fix**, per the project's standing rule.

**Then re-report ADR-025** (+176.0 / −34.7 / +113.4 / **+83.8 holdout**) under the corrected metric,
with the per-season deltas.

> **Holdout note, and please follow it exactly.** Re-computing an already-spent number under a
> corrected metric is **not** a second holdout access. 2025 was unsealed for this decomposition
> already (three entries in `holdout_access_log.jsonl`, ADR-025) and no new decision is made from it.
> Append a `holdout_access_log.jsonl` entry with `reason: "recomputation of ADR-025 under corrected
> top_k_starter_vbd; no new decision"`. Do **not** treat it as a fresh spend and do **not** let the
> corrected number become a new claim.

### 2 — BLOCKING. The projection skill score, incumbent arm

Implements `ADR-DRAFT-primary-evaluation-metric.md` §3. Per position `p`, per season `S ∈ {2022, 2023,
2024}`:

- `MAE_model(p,S)` — the shipped `projected_points` vs realised season points, **walk-forward** (curve
  for S fitted only on `fantasypros_ecr` seasons < S), universe = that season's consensus board,
  busts retained at 0. **This is the number the ranker already produced** (74.0 / 62.0 / 48.0 / 35.8
  means); reuse it rather than re-deriving, and confirm the universe matches.
- `MAE_floor(p,S)` — **new.** Predict, for every player at position `p`, the **mean realised season
  points of that position's same-universe players over seasons < S**. Walk-forward, no target-season
  information.
- `SS(p,S) = 1 − MAE_model / MAE_floor`. Report `SS` per season, the mean, and a season-level
  bootstrap 95% CI (n=3 — `degenerate=True` will fire; surface it, do not suppress it).
- Report raw `MAE_floor` alongside. It is independently interesting: it is how well you do knowing
  nothing about any player.

**Pre-committed audit trigger:** any `SS > 0.35` at any position **halts reporting and escalates as
suspected leakage** (guardrails §8.7). Do not report it as a good result.

**Registered prediction, on file before the run:** SS lands +0.05 to +0.20 everywhere, possibly
negative at QB.

### 3 — The FFC exchangeability check. Decides ruling 2.

Implements `ADR-DRAFT-market-rank-curve-source.md` §4.1. **Not a football hypothesis — a calibration
check. It enters no FDR denominator** (PR-004 §3's precedent for a pre-freeze coverage census).

Overlap seasons only, **2021–2024**:

1. For each source `s ∈ {fantasypros_ecr, ffc_half_ppr_12team}` and each `p ∈ {QB,RB,WR,TE}`, fit
   `points = a + b·ln(positional rank)` on that source's own board universe, outcomes scored with
   `scoring.score_offensive_game` under this league's rules (summed after per-game scoring, so the
   stacking yardage bonuses are computed at game level), busts retained at 0.
2. Report `b_ECR(p)`, `b_FFC(p)`, `Δb(p)`, each with a **season-level** bootstrap 95% CI (n=4,
   10,000 draws, seed recorded).
3. **The governing readout:** rebuild the 2026 board twice — once with `b_ECR`, once with `b_FFC`,
   everything else identical, **both served on the same `fantasypros_csv_2026draft` consensus ranks**
   — and report the **top-100 mean signed Δ-vs-consensus per position** for each. That is the two
   versions of the ranker's `QB +5.3 / RB −1.2 / WR −1.8 / TE +10.6` row.

**Pre-committed rule — apply it, do not re-open it.** APPROVE the refit iff the induced tilt moves
**≤ 2.0 rank places at every one of the four positions** AND all four `Δb` CIs contain zero. Otherwise
**REJECT PERMANENTLY** — no re-run at a different window, universe or fit form.

**Registered prediction:** `Δb(QB)` is the **largest** of the four. If it is the smallest, the ADR's
central mechanism is wrong and it should be re-examined rather than patched — reply saying so.

### 4 — Component models vs the incumbent, on season points. The cheapest real answer available.

The ranker's §6.2 step. **No new model — arithmetic on two committed objects.** Blocked on item 2's
`MAE_floor` (it needs the same floor to form a skill score).

- Score the existing component projections through `pos_model.score_components()` under **this
  league's rules**, on **season points**, not per-component MAE.
- Same universe and same seasons as the incumbent arm, or the comparison is not a comparison. State
  which universe you used and why.
- Report `SS_component(p)` beside `SS_incumbent(p)`, per position, with season-level CIs.
- 2018–2024. **2025 sealed** — this does not authorise `release_for_final_fit()`.

This decides ruling 3's condition (a). Per position: a model that wins at WR and loses at QB displays
at WR and not at QB.

### 5 — The durability-oracle decomposition. Small, and it deflates a startling claim.

Implements `ADR-DRAFT-oracle-ladder-disposition.md` §2.1. Same universe as the ranker's §4 (FFC
half-PPR 12-team boards 2018–2024, busts retained, **2025 not touched**).

1. Per season, per position: **the fraction of the board universe that recorded zero games played.**
2. Re-run the games-played oracle **restricted to players with ≥1 game**, and report ρ beside the
   unrestricted ρ.

> **This is not an ADR-B:54 violation and the distinction must be stated wherever the number appears.**
> ADR-B:54 forbids a minimum-games filter in **model evaluation**, because it deletes the outcomes a
> model failed to anticipate. Here it decomposes an **oracle's** own upper bound into an identity
> component and an information component. Permitted only on oracle arms, reported alongside the
> unrestricted number, never as a performance figure, never applied to any model-evaluation arm.

**Point estimates only — no CIs.** §4 is an exploratory artifact and
`validate_exploratory_artifact` forbids an exploratory result carrying an interval.

**Expected:** ρ falls materially on the ≥1-game subset, and claim (b) — *"perfect availability
foresight alone beats consensus at all four positions"* — is substantially the identity
`games = 0 ⟹ points = 0`. If ρ holds up, the durability channel has real content and the drafted
`F-DURABILITY` registration is worth allocating an id for.

---

## Not asked for, deliberately

- **No new model.** Items 1–5 are measurements and one bug fix. Nothing here builds a ranking.
- **No holdout spend.** Item 1's recomputation is explicitly not a spend; items 2–5 are 2018–2024.
- **No re-run of anything that already has a number**, except item 1's ADR-025 recomputation, which
  is required because the metric underneath it changed.

## Done looks like

Item 1 answered (confirm/refute + counts + fix + regression test + ADR-025 restated) and item 2
answered. Those two unblock the metric promotion and therefore all bottom-up build work. Items 3–5
can follow; item 3 decides whether the FFC refit happens at all and should not be skipped, because
leaving it open leaves the three-season limitation looking like an oversight rather than a ruling.
