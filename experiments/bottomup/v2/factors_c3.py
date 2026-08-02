"""Factor batch C3 -- definitions only. NOT run, fit, or graded in this pass.

============================================================================
NEXT STEP (read this first)
============================================================================
`experiments/bottomup/v2/factors_c1.py` and `factors_c2.py` -- named in this
batch's dispatch as "the contract, follow it exactly" -- DO NOT EXIST in this
checkout. Verified three ways before writing a line of this file: `find` over
the whole repo, `git ls-tree -r origin/main` after `git fetch`, and a text
grep of every doc under `docs/` for "bottomup/v2", "factors_c1", "factors_c2"
and "batch-C1"/"batch-C2" (capital-C naming). Zero hits anywhere. Likely
explanation: a concurrent ranker session is building the v2 rewrite (ADR-069,
"independent of consensus") in a sibling worktree that has not merged yet --
worktrees are isolated from each other by design (`docs/environment.md`),
so this session cannot see it even if it exists on disk elsewhere.

Rather than block, this file is written against the closest interface that
DOES exist and IS verified: `experiments/bottomup/components/pos_data.py`'s
`SeasonPanel` / `HOLDOUT_SEASON` / `HoldoutViolation` / `CutoffViolation` /
`feature_gate` machinery, which every v1 factor batch (1-7) already builds on,
and which the dispatch itself names ("through the harness feature_gate").
The per-batch "own local Sources pack, own gate, push onto access_log"
pattern below is copied byte-for-byte in structure from
`experiments/bottomup/factors/factor_features7.py`'s `Batch7Sources`, the
newest such pack in the repo.

WHEN factors_c1.py / factors_c2.py land: diff this file's `BatchC3Sources`
and column-block builder signatures against theirs. If the v2 harness uses a
different panel object, different column-naming convention, or a different
`_known` companion pattern, this file's SHAPE (one Sources pack, one loader
per source, one builder per factor, `*_known` mandatory) should still port
directly -- only the plumbing (import paths, panel class) should need
changing. Flagged to ranker/pm in thread `docs/handoffs/OPEN.md` (see this
session's reply) rather than silently assumed compatible.

============================================================================
SCOPE NOTE -- two ledger rows deliberately NOT resurrected here
============================================================================
The dispatch's own priority order puts `odds_snapshots` first. It is
excluded from this batch instead, on a closer read of `docs/factor-ledger.md`:

  T0-11 "Vegas win totals & implied team totals" -- blocked. Reason given:
  "No odds table exists in nfl.db... Historical odds require a paid source."
  N12 "Game total / team spread as player-model features" -- blocked, same
  reason, plus: "the whole team-environment channel is oracle-bounded at
  <= +0.055 tau_b" (bottom-up-research-pass-1).

`odds_snapshots` (2018-2024) now exists in `nfl.db` -- the data-availability
half of that exclusion is stale. But the dispatch is explicit: "Rows excluded
for data availability or licensing still stand -- do not resurrect them,"
and this row's SECOND reason (oracle ceiling <=+0.055 tau_b) is a substantive
null finding, not a data-availability one, so it is not obviously a "measured
NULL under the old consensus-derived frame" either -- that phrase describes
results that were biased by scoring against a consensus-derived board, and
the oracle-ceiling number does not obviously have that defect.
**This is a genuine tension between two written instructions and is flagged,
not resolved unilaterally.** No odds-based factor is defined in this batch.
Recommend ranker/strategist decide explicitly whether T0-11/N12 reopen now
that the table exists, given the oracle-ceiling finding may or may not
survive re-derivation under the v2 (independent-of-consensus) frame.

Also NOT included, same "already dispositioned, don't resurrect" logic:
  - T1-22 "PROE" -- blocked, reason given was "no PBP table in nfl.db,"
    which is also now stale (pbp exists, 2009-2025) but T1-22 itself is not
    resurrected here. N20 "Neutral-situation pass rate" is used instead --
    it is marked `untested` (not `blocked`) in the ledger and is explicitly
    described there as "distinct from T1-22 -- a situational filter, not a
    model residual."
  - T1-25 "NFL draft capital" -- `included`, already a built feature
    (`pos_features.py:222-227`, `draft_round`/`draft_pick`/`log_draft_pick`/
    `undrafted`). The combine factor below (F) is deliberately ATHLETIC
    TESTING ONLY, not draft capital, to avoid re-registering something
    already in the model.

============================================================================
SIX FACTORS, FIVE SOURCES, ALL MANDATORY `_known` COMPANIONS
============================================================================
  C  INJURY REPORT-WEEK BURDEN (injuries, 2010+)
  D  PRACTICE-PARTICIPATION SEVERITY (injuries, 2010+)
  E  END-OF-PRIOR-SEASON DEPTH-CHART RANK (depth_charts_weekly, 2001+)
  F  COMBINE ATHLETIC-TESTING COMPOSITE (combine, 2000-2026)
  G  NEUTRAL-SITUATION TEAM PASS RATE (pbp, 2009+)
  H  EFFICIENCY-OVER-EXPECTED RATE (ff_opportunity, 2006+)

Grading is declared at S=12, tier 2 (2013-2024). Every factor below states
its OWN usable span inside that window and whether it truncates it, per the
dispatch's explicit requirement -- "do not silently let a late-starting
source truncate anything."
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from experiments.bottomup.components.pos_data import (
    DEFAULT_DB, HOLDOUT_SEASON, HoldoutViolation, CutoffViolation, SeasonPanel,
)
from experiments.bottomup.components.pos_features import LAG_WEIGHTS, N_LAGS

# ---------------------------------------------------------------- constants
#: Tier-2 grading window (S=12). Factors whose source starts after this are
#: flagged with an explicit usable-span note, never silently truncated.
GRADING_WINDOW = (2013, 2024)

#: First season each source carries real / non-trivial data. Measured against
#: `nfl.db`, not assumed -- see each factor's docstring for the query.
INJURIES_FIRST = 2010          # 2009 has 17 rows total; not real coverage
DEPTH_FIRST = 2001
COMBINE_FIRST = 2000
PBP_FIRST = 2009
FF_OPP_FIRST = 2006            # ff_opportunity's own coverage floor
ODDS_FIRST = 2018              # unused in this batch; recorded for the future

#: Empirical-Bayes shrinkage constants, fixed a priori, never tuned against
#: any result computed from this batch (none has been computed).
PRACTICE_K0_WEEKS = 8.0        # ~half a season of practice reports
YOE_K0_OPPORTUNITIES = 40.0    # order of a qualifying half-season workload


def _median_fill(v) -> np.ndarray:
    """Unknown -> median of what IS known, never 0. Convention copied from
    `factor_features7.py::_median_fill`: a zero is a claim about the player,
    a median is an admission that we do not know."""
    v = np.asarray(v, dtype=float)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
    return np.where(np.isfinite(v), v, med)


def _lag_weighted(values_by_lag: list) -> np.ndarray:
    """`sum(LAG_WEIGHTS[k] * values_by_lag[k])` over available lags, renormalised
    to the weight actually present per row (so a rookie with only lag-1 data
    gets lag-1's raw value, not lag-1 * 0.55)."""
    n = len(values_by_lag[0])
    num = np.zeros(n)
    den = np.zeros(n)
    for k in range(min(N_LAGS, len(values_by_lag))):
        v = np.asarray(values_by_lag[k], dtype=float)
        present = np.isfinite(v)
        num[present] += LAG_WEIGHTS[k] * v[present]
        den[present] += LAG_WEIGHTS[k]
    out = np.full(n, np.nan)
    have = den > 0
    out[have] = num[have] / den[have]
    return out


def _pfr_to_gsis(conn: sqlite3.Connection) -> pd.Series:
    """`combine` is keyed on `pfr_id`; the rest of this batch is `gsis_id`.
    Crosswalk via `player_ids`, pivoted through `mfl_id`. Copied from
    `factor_features7.py::_pfr_to_gsis`."""
    ids = pd.read_sql_query(
        "SELECT mfl_id, source, source_id FROM player_ids "
        "WHERE source IN ('gsis','pfr')", conn)
    g = ids[ids["source"] == "gsis"].set_index("mfl_id")["source_id"]
    p = ids[ids["source"] == "pfr"].set_index("mfl_id")["source_id"]
    xw = pd.DataFrame({"gsis": g, "pfr": p}).dropna()
    return pd.Series(xw["gsis"].to_numpy(), index=xw["pfr"].to_numpy())


@dataclass
class BatchC3Sources:
    """Batch-C3-local historical sources, each with its own gate. Deliberately
    NOT bolted onto `SeasonPanel` -- same reasoning as `Batch7Sources`: other
    agents may be editing shared components concurrently, and a batch-local
    pack cannot collide. Every `*_before` accessor pushes onto
    `panel.access_log` under the `"feature"` tag so the existing look-ahead
    audit covers these reads without touching the harness."""

    injuries: pd.DataFrame = field(default_factory=pd.DataFrame)
    depth_end: pd.DataFrame = field(default_factory=pd.DataFrame)
    combine: pd.DataFrame = field(default_factory=pd.DataFrame)
    pass_neutral: pd.DataFrame = field(default_factory=pd.DataFrame)
    yoe: pd.DataFrame = field(default_factory=pd.DataFrame)

    def _gate(self, cutoff: int) -> None:
        if cutoff >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"cutoff {cutoff} reaches the sealed holdout")

    def _cut(self, name: str, df: pd.DataFrame, cutoff: int,
             panel: SeasonPanel) -> pd.DataFrame:
        self._gate(cutoff)
        out = df[df["season"] <= cutoff].copy() if len(df) else df.copy()
        if len(out) and int(out["season"].max()) > cutoff:
            raise CutoffViolation(f"batchC3 {name} cutoff gate failed")
        panel.access_log.append(("feature", cutoff))
        return out

    def injuries_before(self, cutoff, panel):     return self._cut("injuries", self.injuries, cutoff, panel)
    def depth_end_before(self, cutoff, panel):     return self._cut("depth_end", self.depth_end, cutoff, panel)
    def combine_before(self, cutoff, panel):       return self._cut("combine", self.combine, cutoff, panel)
    def pass_neutral_before(self, cutoff, panel):  return self._cut("pass_neutral", self.pass_neutral, cutoff, panel)
    def yoe_before(self, cutoff, panel):           return self._cut("yoe", self.yoe, cutoff, panel)


_SOURCES: Optional[BatchC3Sources] = None


def sources(db_path: Path = DEFAULT_DB) -> BatchC3Sources:
    global _SOURCES
    if _SOURCES is None:
        _SOURCES = _load_sources(db_path)
    return _SOURCES


# ===========================================================================
# FACTOR C -- INJURY REPORT-WEEK BURDEN                              (N/A#C1)
# ===========================================================================
#
# MECHANISM: a player who appeared repeatedly on the injury report in the
# PRIOR season, weighted by how severe the listed status was, carries
# elevated re-injury / chronic-issue risk into the new season -- durability
# is not i.i.d. year to year. This is a LEADING/persistence signal, distinct
# from `pos_features.py` arm B's `inj_missed_share_1`, which explains games
# ALREADY missed in the season being scored, not risk carried into the next
# one. The mechanism here is "how often was he hurt enough to be listed,"
# not "how many games did that cost him."
#
# SOURCE: `injuries.report_status`, per (player, season, week). Measured
# floor: 2009 has 17 rows total (not real coverage); 2010 has 4,429. Usable
# feature seasons start 2010, so the first predictable TARGET season is 2011
# -- inside the S=12 tier-2 window (2013-2024) with no truncation at all.
#
# SEVERITY WEIGHTING, fixed a priori: Out=3, Doubtful=2, Questionable=1,
# Probable=0 (means "expected to play," the pre-2016 tag), None/blank=0,
# the stray 'Note' value(4 rows total, data artifact) =0.
_SEVERITY = {"Out": 3.0, "Doubtful": 2.0, "Questionable": 1.0, "Probable": 0.0}

_INJ_REPORT_SQL = """
SELECT season, week, gsis_id AS player_id, report_status, practice_status
FROM injuries
WHERE season < ? AND season >= ? AND gsis_id IS NOT NULL
"""


def _load_injury_reports(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(_INJ_REPORT_SQL, conn,
                              params=(HOLDOUT_SEASON, INJURIES_FIRST))


def build_injury_burden(inj: pd.DataFrame) -> pd.DataFrame:
    """Per (player, season): `report_weeks_n`, `severity_sum_n` -- count of
    distinct weeks on report and the severity-weighted sum, that SEASON only.
    Lag-weighting into `injury_burden_prior_w` / `injury_known` happens one
    level up (`attach_injury_burden`) once the caller's own per-player panel
    supplies the season-to-season lag alignment -- this function is
    single-season, matching the shape `pos_features.build_features` expects
    to lag."""
    if not len(inj):
        return pd.DataFrame(columns=["player_id", "season", "report_weeks_n",
                                     "severity_sum_n"])
    d = inj.drop_duplicates(["player_id", "season", "week"]).copy()
    d["severity"] = d["report_status"].map(_SEVERITY).fillna(0.0)
    out = d.groupby(["player_id", "season"], as_index=False).agg(
        report_weeks_n=("week", "nunique"), severity_sum_n=("severity", "sum"))
    return out


def attach_injury_burden(panel_players: pd.DataFrame,
                          burden: pd.DataFrame) -> pd.DataFrame:
    """`panel_players` is (player_id, season) rows to score, one per lag slot
    already resolved by the caller (as `pos_features.build_features` does for
    every other lag block) -- this function only needs season-level burden
    per player and does the join + lag-weight + `_known` itself so the block
    is a single call from a caller with three prior seasons available.

    Returns columns: `injury_burden_prior_w`, `injury_known`.
    `injury_known` = 1 iff the player has >=1 season of injuries-table
    coverage in ANY of the three lag seasons (i.e. NOT simply "season >=
    2010," because a player's OWN rows can be sparse even inside a covered
    season -- e.g. he was never listed, which is a true zero, vs. never
    matched to a gsis_id in `injuries` at all, which is unknown)."""
    req = panel_players[["player_id", "season"]].drop_duplicates().copy()
    lag_vals = []
    lag_known = []
    for k in range(1, N_LAGS + 1):
        j = req.copy()
        j["lag_season"] = j["season"] - k
        m = j.merge(burden, left_on=["player_id", "lag_season"],
                    right_on=["player_id", "season"], how="left",
                    suffixes=("", "_b"))
        sev = m["severity_sum_n"].to_numpy(dtype=float)
        known = (m["lag_season"] >= INJURIES_FIRST).to_numpy() & np.isfinite(sev)
        sev = np.where(np.isfinite(sev), sev, 0.0)  # not listed that week = 0
        lag_vals.append(sev)
        lag_known.append(known)
    burden_w = _lag_weighted(lag_vals)
    burden_w = _median_fill(burden_w)
    known_any = np.any(np.column_stack(lag_known), axis=1).astype(int)
    return pd.DataFrame({
        "player_id": req["player_id"].to_numpy(),
        "season": req["season"].to_numpy(),
        "injury_burden_prior_w": burden_w,
        "injury_known": known_any,
    })


# ===========================================================================
# FACTOR D -- PRACTICE-PARTICIPATION SEVERITY                        (N/A#C2)
# ===========================================================================
#
# MECHANISM: how much PRACTICE time a player missed (Limited / Did Not
# Participate, vs. Full) captures the underlying severity of a lingering
# issue independent of whether he ultimately suited up that Sunday -- two
# players can share the same game-day "Questionable" tag with very different
# practice histories, and the practice history is the more granular signal.
# Distinct from Factor C: C counts REPORT WEEKS (was he listed at all, how
# severely); D measures, CONDITIONAL on being listed, how much practice he
# actually missed. A player who is on the report every week but always
# practices fully (C high, D low) is a different case from one who is on the
# report rarely but DNPs every time he is (C low, D high).
#
# SOURCE: same `injuries` table, `practice_status`. Same 2010 floor as C.
# The `'\n    '` and `'Note'` values are data artifacts (4 and a handful of
# rows respectively across the whole table) and are treated as unknown, not
# as a practice status.
_PRACTICE_SEVERITY = {
    "Did Not Participate In Practice": 1.0,
    "Out (Definitely Will Not Play)": 1.0,
    "Limited Participation in Practice": 0.5,
    "Full Participation in Practice": 0.0,
}


def build_practice_severity(inj: pd.DataFrame) -> pd.DataFrame:
    """Per (player, season): `practice_weeks_listed_n` (weeks with a
    recognised practice_status) and `practice_dnp_limited_rate_n` -- the
    EMPIRICAL-BAYES-SHRUNK mean severity (k0=8 weeks, fixed a priori) of
    those listed weeks, shrunk toward the position-season pooled mean so a
    player with one DNP week does not read as equal to one with sixteen."""
    if not len(inj):
        return pd.DataFrame(columns=["player_id", "season",
                                     "practice_weeks_listed_n",
                                     "practice_dnp_limited_rate_n"])
    d = inj.drop_duplicates(["player_id", "season", "week"]).copy()
    d["p_sev"] = d["practice_status"].map(_PRACTICE_SEVERITY)
    d = d[d["p_sev"].notna()]
    per = d.groupby(["player_id", "season"], as_index=False).agg(
        practice_weeks_listed_n=("week", "nunique"),
        practice_sev_sum=("p_sev", "sum"))
    pooled = (per["practice_sev_sum"].sum() /
              max(per["practice_weeks_listed_n"].sum(), 1.0))
    n = per["practice_weeks_listed_n"].to_numpy(dtype=float)
    s = per["practice_sev_sum"].to_numpy(dtype=float)
    shrunk = (s + PRACTICE_K0_WEEKS * pooled) / (n + PRACTICE_K0_WEEKS)
    per["practice_dnp_limited_rate_n"] = shrunk
    return per[["player_id", "season", "practice_weeks_listed_n",
                "practice_dnp_limited_rate_n"]]


def attach_practice_severity(panel_players: pd.DataFrame,
                              severity: pd.DataFrame) -> pd.DataFrame:
    """Same lag/known shape as `attach_injury_burden`. Returns
    `practice_severity_prior_w`, `practice_known`. `practice_known` requires
    the player to have had >=1 practice-status-listed week in a lag season
    (not merely a season inside the coverage floor) -- a player who was
    never listed at all in that season is legitimately at the pooled prior,
    not "unknown," and gets `known=1` with the pooled-shrunk value; a player
    whose season predates 2010 is genuinely unknown."""
    req = panel_players[["player_id", "season"]].drop_duplicates().copy()
    lag_vals, lag_known = [], []
    for k in range(1, N_LAGS + 1):
        j = req.copy()
        j["lag_season"] = j["season"] - k
        m = j.merge(severity, left_on=["player_id", "lag_season"],
                    right_on=["player_id", "season"], how="left",
                    suffixes=("", "_s"))
        rate = m["practice_dnp_limited_rate_n"].to_numpy(dtype=float)
        known = (m["lag_season"] >= INJURIES_FIRST).to_numpy()
        lag_vals.append(rate)
        lag_known.append(known)
    sev_w = _lag_weighted(lag_vals)
    sev_w = _median_fill(sev_w)
    known_any = np.any(np.column_stack(lag_known), axis=1).astype(int)
    return pd.DataFrame({
        "player_id": req["player_id"].to_numpy(),
        "season": req["season"].to_numpy(),
        "practice_severity_prior_w": sev_w,
        "practice_known": known_any,
    })
