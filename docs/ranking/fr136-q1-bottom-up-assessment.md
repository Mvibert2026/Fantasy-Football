# FR-136 Q1 — bottom-up rankings: where it actually stands

**Ranker, 2026-07-30.** Assessment only. **No model was built in this pass and nothing here is a
new result about football** — every number is either a re-measurement of an existing artifact or a
structural property of code already shipped. Prior passes are cited, not re-derived.

Reproduce: `.venv/bin/python`, `data/nfl.db`, main checkout, branch `claude/pm-agent-setup-gobxa0`.

---

## 0. Data preconditions — checked first, as instructed

| Precondition | Verified | Evidence |
|---|---|---|
| **Half-PPR only for the board source** | **PASS** | `board.json:scoring_format = "half_ppr"`, read from `rankings.scoring_format`, not hardcoded (`src/export_contract.py:341-355`). Both 2026 snapshots of `fantasypros_csv_2026draft` carry `half_ppr` on every row. |
| **One snapshot, not two** | **PASS** | `board.json:snapshot_as_of_date = "2026-07-30"`, `consensus_source_count = 1`. Both `make_board._consensus_board` and `export_contract` filter on `as_of_date = (SELECT MAX(as_of_date) ...)`. The 07-27 snapshot is retained in the table for as-of-date-correct backtesting and is not read by the live board. |
| **Nothing derived from FFC `times_drafted`** | **PASS** | `board.json:adp_source = "mfl_proxy"`. FFC's `times_drafted` is carried into the export payload but the sigma it would feed is explicitly **withheld**, gated on M0 (`src/export_contract.py:686-693, 761, 915`). No board field derives from it. |

**One precondition finding that was not on the list, and it matters.**

The board's *display* source is confirmed half-PPR. The **curve is trained on a different source
whose scoring format is unknown.** `make_board.TRAINING_SOURCE = "fantasypros_ecr"` (2021–2025) has
`scoring_format = NULL` on all 2,540 rows — the DynastyProcess mirror never carried the column. So
`projected_points` is `E[our half-PPR points | rank on a consensus board of unrecorded format]`.
The *outcome* side is scored correctly under this league's rules; the *rank* side is a consensus
ordering that may have been PPR or standard. This is not fatal — expert overall ranks are broadly
format-insensitive at the top — but it is an unlabelled assumption sitting under every projection on
the screen, and it should be labelled.

**A second one:** historical FFC ADP in `nfl.db` covers 2013–2024 and is **12-team** at every
format; the primary league is **10-team**. 2025 is absent from FFC entirely. Any "beats market ADP"
claim on history is a claim against a 12-team market, not this league's.

---

## 1. Q1 — what is built, measured against §6.5's baseline rule

### 1.1 The shipped board holds no player-level opinion. Verified, not asserted.

`data/board_2026.csv`, 378 rows, all four positions:

| position | n | is the board's within-position order identical to consensus order? |
|---|---|---|
| RB | 116 | **yes** |
| WR | 148 | **yes** |
| QB | 45 | **yes** |
| TE | 69 | **yes** |

`projected_points` is a deterministic log curve of consensus positional rank. Refitting
`a + b·ln(positional rank)` to the shipped column returns **max |residual| = 0.005 points** at every
position — the 2-dp rounding in the CSV, nothing else:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| intercept | 359.01 | 303.16 | 276.48 | 180.31 |
| slope | −49.38 | −50.62 | −41.21 | −30.45 |

Independently reproduced by pass 3 §0 from a different direction (the intercept cancels in VBD, so
all 510 board rows reconstruct from four slopes and four replacement ranks with zero mismatches).

**The board's entire deviation from consensus is cross-positional.** `delta_vs_consensus`: mean
|Δ| = 35.1 places over the full board, but **mean |Δ| = 5.9 places, max 20, across the top 100** —
which is every pick in a 10-team draft. In the draft-relevant region the board is consensus moved by
about six places.

### 1.2 The primary harness metric cannot see the board's only edge channel. Measured.

`src/backtest.py:_rank_correlation_by_position` computes Kendall's τ_b **within** each position
(ADR-B forbids any cross-position aggregate — not computed, not stored, not on request). Because
within-position order is identical to consensus, the two arms are the same object under that metric.
Measured, `rescored_consensus_board` vs `fantasypros_ecr_raw`:

| season | QB | RB | WR | TE |
|---|---|---|---|---|
| 2022 | Δτ_b = 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2023 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2024 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

Exactly zero, twelve of twelve. This is not a null result about football. **It is a structural
property**: the project's primary evaluation metric is mathematically incapable of distinguishing
the shipped board from raw consensus, and always was. `top_k_starter_vbd` exists precisely to fix
this and says so in its own docstring — it is the *secondary* metric.

### 1.3 The comparison that has been run, and the two that have not

| §6.5 required baseline | run against the shipped board? | result |
|---|---|---|
| **1. Consensus market ADP** | **NEVER MEASURED** | The `consensus_adp` arm is `available=False` in `standard_arms()`, with ADR-018's reason ("no market ADP source obtainable"). **That reason is stale** — FFC ADP is now ingested (2018–2024 half-PPR, 12-team) and FR-023 records the founder confirming it unblocked. The arm was never re-enabled. |
| 2. Prior-season points, ranked | yes | `bpa_prior_season_points` is a live arm |
| 3. Positional-tier heuristic | **NEVER MEASURED** for the shipped board | No tier-heuristic arm exists in `standard_arms()`. Test-registry #3 is still `SPEC`. |

**The one real comparison on record** is the board against *raw expert consensus* (not market ADP),
on `starter_vbd`, ADR-025:

| Season | Board | Raw consensus | Δ |
|---|---|---|---|
| 2022 | 1001.8 | 825.8 | **+176.0** |
| 2023 | 626.1 | 660.8 | **−34.7** |
| 2024 | 673.9 | 560.5 | **+113.4** |
| 2025 (**holdout**) | 693.1 | 609.3 | **+83.8** |

Development-only: **+84.9, 2/3 positive, sign-test p = 1.000, power floor 0.250.** With the holdout:
+84.6, 3/4 positive, p = 0.625, power floor 0.125. **The correct reading is ADR-025's own: the
board's advantage is not statistically established on development data alone.** Four seasons cannot
establish it, and the sign test's floor (0.125) is above 0.05 — *this design cannot produce a
significant result at any effect size*.

### 1.4 The component models — measured, and they do not clear the market

Already reported in `component-model-wr-pass-1.md` §5 and `component-model-rb-qb-te-pass-1.md` §3.
Restated, not re-derived:

| position | model − consensus ADP (Spearman) | 95% CI | does the design have power? |
|---|---|---|---|
| WR | +0.051 | [−0.011, +0.129] | **no** — ADP − heuristic +0.043 [−0.032, +0.126] |
| **RB** | **−0.052** | [−0.126, +0.038] | **yes** — ADP − heuristic +0.134 [+0.043, +0.223] |
| QB | −0.069 | [−0.255, +0.104] | no |
| TE | −0.024 | [−0.182, +0.123] | no |

Against B2 (prior points) and B3 (weighted prior PPG) they win clearly at all four positions on the
full universe. **Against baseline #1 they do not, and at RB — the one position where the experiment
demonstrably has power — the point estimate is negative.**

Decision-relevant (§6.6), top-k capture and mean actual points of the drafted top-k: **every interval
is open at every position.** Nothing translates into better rosters.

### 1.5 The sealed holdout has never been spent on a ranking model

`HOLDOUT_SEASON = 2025`. `docs/preregistration/holdout_access_log.jsonl` has **three entries**, all
one 2026-07-25 backtest decomposition (ADR-025). No component-model result has ever touched it.
Thread 094 (ranker → strategist) asked for the one registration worth making; the ranker's own §9
then withdrew the factor it proposed, because it measured null. **There is currently no registered
confirmatory test of any bottom-up ranking, and nothing is queued to spend the holdout on.**

---

## 2. Status of this document

**Settled by this pass:** §0 preconditions; §1.1 (board holds no player-level opinion — verified
numerically); §1.2 (primary metric is structurally blind — measured, twelve of twelve exact zeros);
§1.3 (baseline #1 and #3 never measured against the shipped board, and the reason baseline #1 is
disabled is stale).

**Still open at the time of this commit:** Q2 (how much of the output is our own view, quantified),
Q3 (what a real bottom-up projection needs vs. what the DB holds), Q4 (the ordered gap list and what
can be validated before 7 September).

**Not judged here, by design:** whether any of the above is *good enough*. That is not the ranker's
call. See §5 when written.
