#!/usr/bin/env python
"""Does the coordinator table actually support a `coach_id` join across team moves?

`CLAUDE.md` §4 makes `coach_id` a first-class dimension *specifically* so tendency
signals follow the person rather than the team. That is a claim about the data,
not about the schema, and it has never been checked. This script checks it and
reports what it finds, including if the answer is no.

    .venv/bin/python -m experiments.bottomup.factors.coord_join_diagnostic

Descriptive only. Nothing here is a factor test and nothing here may be quoted as
evidence that a factor works.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.bottomup.factors.factor_features2 import (  # noqa: E402
    _normalise_coach,
)

DB = REPO / "data" / "nfl.db"


def load(title: str = "OC") -> pd.DataFrame:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(
            "SELECT team, season, coach_id, head_coach, as_of_date, "
            "days_before_kickoff FROM play_callers_preseason WHERE title = ?",
            conn, params=(title,))
    finally:
        conn.close()
    df["key"] = df["coach_id"].where(df["coach_id"].notna(),
                                     "HC:" + df["head_coach"].astype(str))
    # the key the FEATURE actually compares on -- see
    # factor_features2._normalise_coach for why the HC:/OC distinction is
    # deliberately dropped from the continuity key
    df["nkey"] = df["key"].map(lambda k: _normalise_coach(str(k)[3:]
                                                          if str(k).startswith("HC:")
                                                          else k))
    return df


def main() -> None:
    oc = load("OC")
    seasons = sorted(oc["season"].unique())
    print(f"play_callers_preseason OC: {len(oc)} rows, "
          f"{seasons[0]}-{seasons[-1]}, {oc['team'].nunique()} clubs")

    print("\n--- coverage per season (32 clubs is full) ---")
    cov = oc.groupby("season").agg(
        clubs=("team", "nunique"),
        oc_named=("coach_id", lambda s: int(s.notna().sum())),
        hc_called=("coach_id", lambda s: int(s.isna().sum())),
        median_days_before_kickoff=("days_before_kickoff", "median"))
    print(cov.round(1).to_string())

    print("\n--- 1. can a coordinator be followed ACROSS a team move? ---")
    named = oc[oc["coach_id"].notna()]
    per = named.groupby("coach_id")["team"].nunique()
    movers = per[per >= 2]
    print(f"distinct named OCs: {len(per)}")
    print(f"OCs appearing for 2+ clubs: {len(movers)} "
          f"({100*len(movers)/len(per):.1f}%)")
    print(f"club-seasons whose OC is one of those movers: "
          f"{int(named['coach_id'].isin(movers.index).sum())} of {len(named)}")
    print("\ntop 10 by number of clubs:")
    ex = movers.sort_values(ascending=False).head(10)
    for name, n in ex.items():
        rows = named[named["coach_id"] == name].sort_values("season")
        spans = ", ".join(f"{t}{s}" for t, s in zip(rows["team"], rows["season"]))
        print(f"  {name:26s} {n} clubs   {spans}")

    print("\n--- 2. name-collision risk (the known weakness of a name-as-id) ---")
    dup = named.groupby(["season", "coach_id"])["team"].nunique()
    dup = dup[dup > 1]
    print(f"same name as OC of 2+ clubs in the SAME season: {len(dup)}"
          + ("" if len(dup) == 0 else f"\n{dup.to_string()}"))
    print("  (a nonzero count is either a genuine name collision or a parse "
          "error; either way the name is not a safe key)")

    print("\n--- 3. how many OC changes are there to detect, and are they traceable? ---")
    rows = []
    for s in seasons[1:]:
        cur = oc[oc["season"] == s].set_index("team")["nkey"]
        prev = oc[oc["season"] == s - 1].set_index("team")["nkey"]
        both = cur.index.intersection(prev.index)
        changed = [t for t in both if cur[t] != prev[t]]
        # of the new OCs, how many were an OC somewhere else the previous season?
        prev_all = set(oc.loc[oc["season"] == s - 1, "nkey"])
        from_elsewhere = [t for t in changed if cur[t] in prev_all]
        rows.append(dict(season=s, clubs_comparable=len(both),
                         oc_changed=len(changed),
                         change_rate=len(changed) / len(both) if len(both) else float("nan"),
                         new_oc_was_an_oc_elsewhere=len(from_elsewhere)))
    ch = pd.DataFrame(rows)
    print(ch.round(3).to_string(index=False))
    print(f"\nmean OC change rate: {ch['change_rate'].mean():.3f} "
          f"({ch['oc_changed'].sum()} changes over {int(ch['clubs_comparable'].sum())} "
          f"comparable club-seasons)")
    traceable = ch["new_oc_was_an_oc_elsewhere"].sum()
    print(f"of {ch['oc_changed'].sum()} changes, {traceable} brought in someone who was "
          f"an OC elsewhere the prior season ({100*traceable/max(1,ch['oc_changed'].sum()):.1f}%) "
          "-- the rest are promotions, position coaches, or returns from outside the OC pool, "
          "and carry NO prior OC-level history in this table")

    print("\n--- 4. the honest as_of ---")
    d = oc["days_before_kickoff"].dropna()
    print(f"days before Week 1: median {d.median():.0f}, "
          f"10th pct {d.quantile(0.10):.0f}, min {d.min():.0f}, max {d.max():.0f}")
    print(f"rows dated fewer than 14 days before kickoff: "
          f"{int((d < 14).sum())} of {len(d)} "
          "-- these are the ones closest to being post-draft information")


if __name__ == "__main__":
    main()
