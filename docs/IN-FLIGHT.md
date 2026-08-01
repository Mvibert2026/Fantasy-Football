# In flight — resume here after a token limit or session death

**Written 2026-08-01 by pm, mid-session, at the founder's instruction:** *"Make sure it's all
recorded as you go. Good chance we hit token limits in the middle of this."*

**Read this file first if a session died with work running.** It is deliberately not
`CURRENT-STATE.md` (canonical, settled state) and not `docs/status/` (historical narrative). This is
the volatile one: what was running, what it was going to produce, and what to do if it never arrived.

**Delete or empty this file when nothing is in flight.** A stale IN-FLIGHT is worse than none — it
will be read as current. *(The previous contents, dated 2026-07-30, were exactly that: every item in
them had been resolved or superseded and the worktrees named no longer existed.)*

---

## Where the project is, in one paragraph

Ranking **v2** exists: built from player-level projections, **no consensus anywhere in its ordering
path**, with a swappable scoring layer (same stat lines re-rank under half-PPR / full-PPR / standard
with zero refits). The bar changed on 2026-08-01 (**ADR-069**, `CLAUDE.md` §2a): absolute quality
against realised outcomes steers development; the four-baseline consensus comparison is a **release
gate run once at the end**, not a steering metric. On 2024, v2 scores ρ 0.607 overall against
consensus 0.743 and the shipped adjusted board 0.649 — v2 loses to both, and the **adjusted board
loses to the raw consensus it is derived from**. v2's entire measured deficit is one channel:
**projected games**. The founder's bar is **parity with any single analyst**, not with the aggregate.

---

## Running when this was written

| # | Agent | Task | Where its output goes |
|---|---|---|---|
| 1 | `strategist` | **G2a as-of ruling** — blocking everything below | `docs/handoffs/2026-08-01-g2a-week-1-status-as-of-ruling-and-v2-ship-revie.md` |
| 2 | `data-ops` | Ingest **Vegas odds** + **per-analyst rankings** | `data/nfl.db`, `src/ingest_*`, ingest notes |
| 3 | `ranker` | **Factor inclusion campaign against v2** | `docs/ranking/factor-campaign-manifest/`, batch results doc |
| 4 | *(background process)* | **PR-007** recommendation-constants ablation | `src/run_pr007.py` → results doc, handoff to `frontend` |

All three agents were told to commit incrementally and keep a `NEXT STEP` block at the top of their
output file. **Check those files before assuming an agent produced nothing.**

---

## 1 · strategist — the G2a ruling (do this first if it did not land)

**The question.** v2's games component was tested as four arms. **G2a** — adding **week-1 roster
status (IR/PUP/SUS)** — passed its pre-registered rule at **3 WIN / 0 HARM** (RB +0.072, WR +0.048,
BH-robust) and is the only arm beating naive persistence on games MAE. Adoption was gated, *before
the arm ran*, on an as-of question: week-1 status ≈ the **late-August cutdown**, which a Labor Day
drafter knows and a mid-August drafter does not.

**Why it blocks.** Until it is ruled, **v2 defaults to the G0 games arm** (v1's, the weak one) per
the registered fallback. Every factor graded against v2 is graded against whichever arm is live, so
a late ruling means a re-grade.

**What is needed back:** ADMIT / ADMIT-WITH-CONDITION / REJECT in one line; the exact condition if
conditional; whether the **2018–2024 historical construction** of week-1 status is genuinely as-of
correct or reconstructed post-hoc (**the part most likely to be quietly wrong**, and a different
question from whether a real drafter would know it); and whether admission should depend on draft
date.

**Relevant facts:** primary league drafts **7 September 2026** (Labor Day, after cutdowns). Two other
leagues unconfirmed (FR-012). Fable flagged the effect as "exactly too-good-check-it size" — the
mechanism is transparent (week-1 IR/PUP/SUS mechanically implies missed games), which makes it both
plausible and suspicious. `CLAUDE.md` §6.1 wants the cutoff enforced **structurally**, not assumed.

**If it did not land:** re-dispatch `strategist` with the thread. Do not rule it yourself — it is a
methodology call and PM ruling on it defeats the gate.

---

## 2 · data-ops — the two missing sources

**Vegas odds — confirmed absent.** Zero odds tables in `data/nfl.db` as of 2026-08-01, despite being
listed in `CLAUDE.md` §5 since the project began. Priority: **implied team totals and spreads**, then
props, **win totals last** (weakest for our purpose). **Historical 2018–2024 is what makes them
testable**; a 2026-only pull is much less useful.

**Per-analyst rankings.** Only the *aggregate* (`fantasypros_ecr`, 6 seasons) is stored. The
individual expert boards behind it are needed to make the founder's bar — *"on par with any single
analyst"* — a measurable claim rather than an aspiration. **v2 is −0.031 vs consensus at WR and
−0.022 at TE; the analyst spread is plausibly wider than that**, so v2 may already meet the bar at
those positions and we cannot currently tell.

**Founder's ruling, 2026-08-01, now in `CLAUDE.md` §5:** *"Stop worrying about terms. I will worry
about them. It's all personal use. Just get the data."* **Do not stall an ingest on a terms review.**
Still binding and unrelated: `as_of_date` on every time-sensitive row, no credentials in code, no
paid/trial tiers.

**If it did not land:** check the DB for partial tables before re-dispatching — commit-as-you-go was
instructed, so some may exist.

---

## 3 · ranker — factor inclusion against v2

**Why this is not a repeat.** The previous ~90 factor arms were tested on top of the
**consensus-derived board**, which already contained consensus's embedded knowledge — so an
informative factor could return NULL because consensus had already priced it. **v2 contains no
consensus.** Founder's ruling: those results carry almost no information about inclusion in v2, and
**the inclusion test has never actually been run.** Do not cite the old nulls as evidence about any
factor.

**The test:** add the factor to v2 → measure **absolute rank correlation against realised finish**
(not delta vs consensus) → grade **WIN / HARM / NULL** against a threshold registered **before**
measurement → correct at **campaign** level. Harness already exists — it is what B1 used on the games
arms.

**Standing hazard, and it is the thing most likely to go wrong:** expect a **higher hit rate** than
the old campaign and treat that as a warning, not a breakthrough. A model with less knowledge baked
in has more room for anything correlated with outcomes to look useful.

**Ledger discipline:** `docs/factor-ledger.md` rows that measured NULL under the old frame are
**untested for v2**. Rows excluded for **data availability or licensing** still stand.

**One arm, one change. No stacking.** Weighting is the phase *after* inclusion — founder's explicit
sequencing. He expects the finished model to carry **many** factors.

---

## 4 · PR-007 — recommendation constants

Background process (`src/run_pr007.py`), restarted after a container restart killed the first run at
cell 6 of 9 with nothing written. Grid is 3 seasons × 3 sigmas.

Tests whether the recommender's three hand-set constants — `+8` unfilled need, `+18` tier-1 TE, `−25`
early QB — earn their place, measured in **roster points against actual outcomes**, leave-one-out,
seven criteria per constant. **Powered to delete.** Registered 2026-07-29 and unrun for three days.

**It answers the founder's question** of whether the `−25` should be larger. Note the framing already
given him: the quantity it approximates is **opportunity cost**, which is contextual (slot, board
state, who survives to the next pick) — so the likely correct answer is that it should not be a
constant at all, and PR-007 tests whether it earns its place rather than searching for a better value.

**If the results exist but nobody wrote them up:** dispatch `backend` with the spec at
`docs/preregistration/PR-007-recommendation-constants-ablation.md`. **The registration is frozen** —
do not amend thresholds to make a result come out. Any KEEP is PROVISIONAL at n=3 seasons. A DELETE
means removing the term from `frontend/ui/data/recommendation.ts` via a thread to `frontend`, not a
self-merge.

---

## Standing constraints that survive any reset

- **The sealed 2025 holdout does not open.** `CLAUDE.md` §6.3. No agent on its own authority,
  including on a result it considers decisive. Founder restated it unprompted on 2026-08-01. Every
  access logged in `docs/preregistration/holdout_access_log.jsonl`.
- **Seasons through 2024 only** for all current work.
- **Register thresholds before measuring; correct at campaign level.** With consensus removed from
  the development loop, this plus the sealed holdout is the *only* overfitting protection left.
- **Fable is builder and gate simultaneously**, which the project's own §8 rule exists to prevent.
  `strategist` is its adversary; nothing merges to the board on Fable's own sign-off.
- **Branch `claude/pm-agent-setup-gobxa0`.** Merge to `main` is founder-authorised.

## Known-open, not being worked

`PR-` ids still have no allocator. The metric rename (`E1a→C1`) was never applied. Threads 109–111
carry literal merge-conflict markers. Three corrections owed from Fable's M2 review (batch 7's
"every arm that improved the full universe degraded the board" is measured 10-of-17; batch 5's
coverage-artifact mechanism sentence; PR-009's headline prices its two labels asymmetrically).
