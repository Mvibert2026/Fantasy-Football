---
ID: 2026-07-30-register-factor-batch-7-campaign-m-80-and-rule-o
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: batch 7's grades standing at m=80; whether batch 3's S1 VOID ruling was reached for the right reason; how every concurrent batch should build a coverage control
OPENED: 2026-07-30
---

## Ask

Three rulings, in priority order. I will not act on any of them until you answer, and I have
changed nothing on my own authority.

---

### 1. THE ONE THAT MATTERS. A registered "coverage control" is a TIME DUMMY whenever its source starts inside the training window — and one such control is already published as a VOID ruling in batch 3.

Batch 2 lost three arms to `move_known`. Batch 3's fix was to register every coverage flag as its
own control arm with a 50%-of-treatment VOID rule
(`docs/ranking/factor-batch-3-precommit.md` §5). Batch 7 inherited that rule. **It fired, and the
mechanism is not the one the rule assumes.**

`rzsnap_known` (a binary "is this player in `participation` at all") came in at **−0.1239 carries
MAE, p = 0.038 — more than DOUBLE either red-zone treatment** (−0.0576, −0.0533). Post-hoc D2
(`experiments/bottomup/results/factor_batch7_diagnostics.csv`, run `f8d7757`):

| measurement | value |
|---|---|
| `rzsnap_known` agrees with "is **not** a rookie", RB universe 2018–2024, n = 919 | **99.89%** |
| P(unknown \| rookie) | **1.000** |
| mean `games_1`, known vs unknown | 10.37 vs **0.06** |

And the part that is not about rookies — the flag **among veterans only**, by target season:

| 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | … | 2024 |
|---|---|---|---|---|---|---|---|---|
| 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.869 | **1.000** | | **1.000** |

`participation` starts in 2016; `first_feature_season` is 2012. **Inside the veteran design matrix
the flag is a pre-2017/post-2017 indicator.** What it fits is an era shift in carries per game, not
a coverage confound.

**This is already in a published batch-3 result.** The pattern across every control either batch has
run is exact:

| batch | control | source starts | covers the 2012+ training window? | result |
|---|---|---|---|---|
| 3 | `sep_known_1` NGS | 2016 | **no** | **+0.0584, p = 0.056, MARGINAL-HARMFUL — and it VOIDed S1 at WR** |
| 3 | `expl_known` pbp | 2009 | yes | −0.0058, p = 0.44, **NULL** |
| 7 | `rzsnap_known` participation | 2016 | **no** | **−0.1239, p = 0.038**, largest effect in its family |
| 7 | `snap_known` snap_counts | 2013 | nearly | −0.0478, p = 0.12, voids P1 |
| 7 | `i5_known` pbp / `yac_known` weekly | 2009 / 2006 | yes | +0.0005, −0.0029, both **NULL** |

**Every flag whose source covers the training window is null. Every flag whose source starts inside
it is not.** That is the calendar, not the football.

**What I need ruled:**

- **(1a)** Is batch 3's **S1 (NGS separation, WR) VOID — COVERAGE ARTIFACT** ruling still correct?
  My reading: the ruling's *conclusion* may survive but its *stated reason* does not, because
  `sep_known_1` was not measuring "we have a separation row for him", it was measuring "this is a
  2018-or-later season". `docs/ranking/factor-batch-3-results.md` should say which. **I am not
  editing batch 3's results document; that is your call, not mine.**
- **(1b)** Should the batch-3 rule "first target season = source first season + 2" be amended to
  **also restrict the arm's TRAINING window to seasons with coverage**? That is the fix — the rule as
  written guarantees the arm differs from the primary in at least one training season, but it leaves
  four or five *uncovered* training seasons inside the fit, which is what manufactures the dummy.
  It costs training seasons, so it is a real trade and not a free correction.
- **(1c)** Batches 4, 5 and 6 are running concurrently and any of them using a source with a start
  year after 2012 has the same exposure. **This needs to reach them before they write up, not
  after.** If you agree, I would like you to state the rule once, centrally, rather than each batch
  rediscovering it.

---

### 2. Register batch 7 into the campaign family, and confirm or replace m = 80.

`docs/ranking/factor-batch-7-precommit.md` §4 registers **16 tests at RB**, all graded under
**campaign BH at m = 80**, recorded in the new shared
`docs/ranking/factor-campaign-manifest.md`. The dispatch required registration into a shared campaign
family rather than a batch-local one; no such file existed, so I created it and registered batch 7's
block in it. Batches 4, 5 and 6 have placeholder sections to append to.

**m = 80 = four concurrent batches × 20 registered tests**, declared before fitting as a planning
figure, with this one-directional rule committed in advance:

> If the realised campaign total exceeds 80, every batch-7 grade is recomputed at the realised
> total. If it comes in under 80, nothing is relaxed.

**What I need:** confirm 80, or replace it with a number you compute from the four batches' actual
registrations. **Nothing in batch 7 turns on the answer** — the smallest p-value in the batch is
0.021 and nothing passes at m = 80, at m = 16, or at any denominator down to m = 1 under BH with
q = 0.10 except a bare rank-1 test. I am asking so that the manifest is authoritative for batches
4–6, whose results I have not seen.

---

### 3. A second defect in the endpoint set, and it is not about coverage.

Every arm that improved the full-universe component MAE **degraded the ADP-board MAE**, same sign,
across three unrelated sources — post-hoc D1:

| arm | source | ADP board (51 players/season) | off-board (80/season) |
|---|---|---|---|
| Z1 RZ-20 snap rate | participation | **+0.877 (+1.35%)** worse | −0.659 (−1.73%) better |
| Z2 inside-5 snap rate | participation | **+0.716 (+1.10%)** worse | −0.537 (−1.41%) better |
| P1 prior snap share | snap_counts | **+0.425 (+0.65%)** worse | −0.329 (−0.86%) better |
| L2 group late lift | weekly + draft, **full window coverage** | **+0.299 (+0.46%)** worse | −0.154 (−0.40%) better |

L2's source covers the whole training window, so this is **separate from finding 1**. Batch 1 §1(3)
found this shape once and batch 2 named it BOARD-NEUTRAL. Batch 7 suggests it is not an occasional
trap but **what a usage feature does at RB by default**: it sharpens the model where role is
uncertain — the population a ten-team draft never reaches — and adds noise where role is already
known.

**What I need ruled:** should **E1a (full-universe component MAE) remain the FDR endpoint** for
subsequent batches, given that its sign is systematically opposite to the decision-relevant subset's?
The alternative is to make **E1b the FDR endpoint** and accept 7 seasons and the power loss that
comes with it. Batch 2 §3 explicitly rejected that on power grounds and I think that reasoning was
right at the time — but it was made before anyone had measured that the two endpoints
*systematically disagree in sign* rather than merely differing in precision. **This changes what the
whole campaign is measuring, so it is not mine to decide.**

## Why

Without (1) the campaign keeps shipping a control that cannot do the job it was registered to do, and
one already-published VOID ruling rests on a reason that does not hold. Without (3) every batch in
this campaign is optimising a metric whose sign is opposite to the one that decides a draft — which
is the single most consequential methodological question open in the bottom-up work, and it is
squarely yours rather than mine.

Batch 7 itself is not blocked: 16 of 16 arms are null-or-worse and nothing is being proposed for
promotion, so no ruling here can turn a batch-7 negative into a positive.

## Done looks like

1. A yes/no on (1a), a yes/no with a stated cost on (1b), and — if you agree with (1c) — one
   sentence I can point batches 4–6 at.
2. `m` confirmed at 80 or replaced, written into
   `docs/ranking/factor-campaign-manifest.md`'s "registered denominator" table.
3. A ruling on (3): E1a stays the FDR endpoint, or E1b replaces it, or a third construction you
   specify.

## Reading list, shortest path

- `docs/ranking/factor-batch-7-results.md` §1(2) and §1(3) — the two findings, with the tables above
- `docs/ranking/factor-batch-7-precommit.md` §4–§5 — what was registered, before fitting, at `fb7627a`
- `docs/ranking/factor-campaign-manifest.md` — the shared denominator
- `experiments/bottomup/results/factor_batch7_results.csv` (16 rows),
  `factor_batch7_diagnostics.csv` (D1, D2)
