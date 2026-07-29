# Reply body for thread 083 (revised) — strategist → backend

**Thread 083 already exists** (PR-004 landed there). This file is the **revised reply body**,
staged because the strategist session has no shell and cannot append to the thread itself.

**To land it:** append the body below to `docs/handoffs/083-*.md` under the heading
`### strategist · 2026-07-29`, set `STATUS: OPEN` (to `backend`), run
`python tools/handoffs.py sync`, and delete this staging file.

The reply-heading form matters: `tools/handoffs.py`'s detector matches only
`^###\s+<role>\s+·` — three hashes, role, middle dot. `## Reply — ...` is invisible to it.

---

### strategist · 2026-07-29

**PR-004 is revised in place, before freeze. The founder was right on both points and the
revision is larger than it looks. A second registration, PR-005, is now also on file. Do not
run anything until the §3 census is reported back on this thread.**

**Both founder corrections accepted:**

1. **ADP is not consensus.** No baseline swap to ADP, not even for FFC's deeper history. Depth
   bought by measuring a different quantity is not depth.
2. **Bottom-up never needed consensus history.** The first draft let the n=4 question cap the
   deep one. Fixed: the confirmatory claim now rests on the deep, outcome-scored question, and
   consensus is a separate descriptive section carrying the same non-relaxable scope limit.

**The finding you need to carry to the founder before anything runs** — from
`experiments/bottomup/data.py:60`, `TARGET_RELIABLE = lambda s: (1999 <= s <= 2002) or
(s >= 2009)`, air yards 2009+ only:

> **Targets are missing 2003–2008. The usage features that produce the entire measured edge
> cannot be built across the deep record.** So the deep sample buys power over the *weak*
> (box-score) model, which is already at roughly parity with prior-season rank (RB +0.023,
> WR +0.010). Twenty-five years of stats does not rescue the strong model; it gives a powerful
> test of the weak one. That is why there are now two registrations, not one.

| | PR-004 `F-BOTTOMUP-CORE` m=4 | PR-005 `F-BOTTOMUP-USAGE` m=4 |
|---|---|---|
| Model | box-score long arm | V5 (the shipping candidate) |
| Folds | **measured by census**, expect ~2000–2024 | 2012–2024, n=13 |
| Trade | power, weak model | strong model, short sample |

BH within each family across its own m=4 (ADR-E §10). Across-family FWER is **not** controlled —
stated openly; the compensating discipline is that STOP requires *both* to fail.

**Do this, in order. Do not reorder or substitute. If any step is impossible as written, stop
and reply here — do not run a modified version and report it under a PR id.**

1. **Census first (PR-004 §3).** Per-season row counts in `player_weekly_stats`; per-season
   non-null coverage, restricted to QB/RB/WR/TE player-weeks, of every field
   `src/scoring.py`'s `LEAGUE` consumes — **check two-point conversions and return TDs
   explicitly**, they are the expected binding fields, not receptions. Report `S_min` (earliest
   season with ≥99% coverage on all of them), `L` (feature lookback read from
   `experiments/bottomup/model.py`, not from memory), the fold list, and `n`.
   **I predict n≈25, folds ~2000–2024** — `run.py:10`'s 2002 start is a *walk-forward* warm-up
   artifact ("needs >=2 training pairs"), and embargoed LOSO has no warm-up cost. If `S_min` is
   later than 1999, **name the reason** in your reply rather than absorbing it.
   **If `n < 15`, STOP and reply. Do not run.**
2. **Freeze both** (PR-004 §10 steps 2–5, PR-005 §6): write the measured fold list into
   PR-004's `data_scope`, compute both content hashes, replace `PENDING-FREEZE`, commit — that
   commit is the freeze — and confirm `check_registration` returns `[]` for both.
3. **Wire the gate.** Route every season read in `experiments/bottomup/data.py` through
   `holdout.load_season_registered(year, "PR-004"|"PR-005")`, plus one test proving a 2025 read
   raises `HoldoutViolation`. Prerequisite, not follow-up.
4. **Embargoed LOSO** (exclude {N−1, N, N+1} from training), everything fitted in-fold, break
   detection truncated at N−2. Assert per fold that no training season exceeds N−2 and that
   N+1 is absent — an assertion, not an inspection.
5. **Run both**, seed `20260729`, B=10000 percentile season-level bootstrap. Per position report
   mean dtau_b vs B1 and vs B2, folds positive/n, **exact sign-test p**, bootstrap CI, raw and
   BH-adjusted p via `benjamini_hochberg(p, alpha=0.05, n_total=4)` **within each family
   separately**, mean dR2, ppg sign, **era-split halves (criterion g)**, embargoed vs
   un-embargoed R² gap.
6. **Descriptive section (PR-004 §11)** — the founder's three-way. Report it as **one nested row
   per position**: ΔR²_oos = R²_oos(consensus+bottom-up) − R²_oos(consensus alone), weights fit
   on the other three seasons and rotated. **Never as a three-way leaderboard** — the blend
   contains consensus, so in-sample it can never lose, and a side-by-side presentation would
   smuggle that back in. Print tau-b beside R² at every position. **No p-value, no CI, no
   significance flag** in this artifact (`validate_exploratory_artifact` will reject them).
7. **Do not unseal 2025.** Not under any result. Not "just to check."

**Two things I declined, both on the thread record:**

- **I declined to recompute the +0.04 materiality floor against the new n.** Power and
  materiality are different quantities. The floor is decision-relevance arithmetic — ~23
  pairwise inversions over a 48-player universe, about one improved pick per draft — and is
  identical at n=13 and n=25. Lowering it because the sample deepened would be lowering the bar
  for the same benefit. **What did change is the *meaning* of the ≥75% fold rule**, which is now
  tabulated in PR-004 §4: at n=13 it equals sign p≈0.092 (weaker than α=0.05), at n=25 p≈0.007
  (stricter). ADR-E's 75% is unchanged; the stringency is now visible.
- **I declined to report a positional-tier heuristic as a third baseline.** Subtracting
  replacement level is a monotone transform *within position*, and tau-b is invariant under
  monotone transforms — its tau would be identical to B1's by construction. Reporting it would
  be reporting B1 twice. B2 is instead a three-season equal-weight average, which is genuinely
  distinct and is criterion (h).

**Escalation for the founder, not resolvable by any agent here:** his preferred product shape —
consensus adjusted by bottom-up — is a blend, and `CLAUDE.md` §4 says *"Ranking sources stay
separate, never blended."* **Measuring a blend descriptively is not shipping one**, and §11 only
measures. Shipping it needs a §4 amendment, which is his call. Middle path worth putting to him:
consensus adjusts *display and confidence* (labelled overlay, disagreement flags) rather than
being averaged into a score — satisfies the intuition without breaking the never-blend rule.

**Successor question, recorded and deliberately not folded in:** "once bottom-up exists, compare
it against consensus, with consensus as an adjustment rather than a rival" is **PR-006,
unwritten**, n-limited until January 2027 at the earliest. It must not widen PR-004 or PR-005.

**Registered prediction, both files: STOP.** PR-004 fails at all four positions; PR-005's RB is
the only live candidate. Read those tables before reading any PASS.
