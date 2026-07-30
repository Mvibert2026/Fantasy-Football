"""
Availability opponent-model pre-registration -- M0 (FFC times_drafted/
total_drafts_in_sample reconciliation gate) and M1 (does market ADP predict
realised mock-draft pick order better than expert consensus ECR?).

Full design, thresholds, and every decision rule this script implements:
`docs/ranking/availability-opponent-model-precommit.md`. Ask and results
thread: `docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md`
(backend reply, 2026-07-30).

STATUS. Ran as ad hoc analysis, not through `src/preregistration.
require_confirmatory` -- no `PR-0NN` allocator exists yet (see
`docs/handoffs/2026-07-30-no-allocator-exists-for-pr-0nn-pre-registration.md`).
Not logged in `docs/preregistration/test_run_log.jsonl`. The pre-registration's
thresholds and rules were still followed to the letter (family
`availability-opponent-model`, declared m=4); only the formal logging step is
missing. Promote this into the confirmatory harness once the allocator exists,
rather than re-deriving the pipeline from scratch.

M2/M3 (dispersion) are NOT implemented here -- M0 fails to reconcile in this
run, which blocks them per the pre-registration's own gate rule. M4/M5 also
not implemented; out of this session's scope.

SCOPE NOTE ON THE DISAMBIGUATION LOGIC. `identity.resolve_name()` correctly
refuses to guess between two same-name players (e.g. two WRs both named
"Michael Pittman"). This script adds exactly two additional, logged tiebreak
rules on top, used only where `resolve_name()` itself reports genuine
ambiguity:
  (a) an exact suffix-preserving name match (Jr./Sr./II/III), since
      `identity.normalize_name()` deliberately strips suffixes for its own
      documented purpose (coverage-report matching) and that strip is what
      collapses e.g. "Marvin Harrison Jr." onto his father's canonical row;
  (b) exactly one ambiguous candidate playing a fantasy-relevant skill
      position (QB/RB/WR/TE) -- used only to exclude a non-skill namesake
      (a linebacker, a cornerback), never to choose between two skill
      players sharing a name.
Every resolution's method is recorded per pick (`resolution_methods` in the
output) so this is auditable, not silent.
"""

from __future__ import annotations

import json
import sqlite3
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import identity  # noqa: E402

DB_PATH = ROOT / "data" / "nfl.db"
MOCK_DIR = ROOT / "data" / "mock-drafts"

MOCKS = [
    ("yahoo-10team-slot4-2026-07-30", MOCK_DIR / "yahoo-10team-slot4-2026-07-30.json"),
    ("yahoo-12team-slot2-2026-07-30", MOCK_DIR / "yahoo-12team-slot2-2026-07-30.json"),
    ("founder-mock-2026-07-29", MOCK_DIR / "founder-mock-2026-07-29.json"),
]

SKILL_POS = {"QB", "RB", "WR", "TE"}

CANDIDATES = [
    "fantasypros_ecr",              # incumbent, expert consensus
    "fantasypros_csv_2026draft",    # the board
    "ffc_half_ppr_10team",          # market ADP, primary league scoring match
    "ffc_ppr_10team",
    "ffc_non_ppr_10team",
]


def run_m0(con: sqlite3.Connection) -> dict:
    """Reconcile FFC's times_drafted / total_drafts_in_sample. Not a
    hypothesis -- a data-semantics gate (pre-registration M0)."""
    out = {}
    for date, table_label in (("2026-07-30", "07-30"), ("2026-07-29", "07-29")):
        rows = con.execute(
            "SELECT times_drafted, total_drafts_in_sample FROM ffc_adp_snapshots "
            "WHERE adp_source='ffc_half_ppr_10team' AND as_of_date=?",
            (date,),
        ).fetchall()
        if not rows:
            continue
        total_drafts = rows[0][1]
        sum_times = sum(r[0] for r in rows)
        out[table_label] = {
            "n_players": len(rows),
            "total_drafts_in_sample": total_drafts,
            "sum_times_drafted": sum_times,
            "ratio_sum_to_total_drafts": round(sum_times / total_drafts, 3),
        }
    # picks-per-draft implied by FFC's own API meta (rounds x teams)
    out["implied_picks_per_draft"] = 150  # meta: rounds=15, teams=10 (verified live API 2026-07-30)
    out["implied_total_player_slots_if_full_participation"] = 150 * 1254
    out["reconciled"] = False  # see thread reply for full citation and reasoning
    return out


def _players_canonical(con: sqlite3.Connection):
    return con.execute("SELECT mfl_id, display_name, position FROM players_canonical").fetchall()


def make_resolver(con: sqlite3.Connection):
    canon = _players_canonical(con)

    def resolve_skill(name_raw: str):
        mfl_id = identity.resolve_name(con, name_raw)
        if mfl_id is not None:
            return mfl_id, "resolve_name"
        key = identity.normalize_name(name_raw)
        matches = [r for r in canon if r[1] and identity.normalize_name(r[1]) == key]

        punct_fold = lambda s: identity._PUNCT_RE.sub("", s.strip().lower())
        exact = [r for r in matches if punct_fold(r[1]) == punct_fold(name_raw)]
        if len(exact) == 1:
            return exact[0][0], "resolve_name+suffix_exact_disambiguation"

        skill_matches = [r for r in matches if r[2] in SKILL_POS]
        if len(skill_matches) == 1:
            return skill_matches[0][0], "resolve_name+skill_pos_disambiguation"
        return None, "unresolved"

    return resolve_skill


def load_source_maps(con: sqlite3.Connection, draft_date: str) -> dict:
    """candidate -> (keytype, {key: predicted_pick_value}, as_of_date_used).
    Each candidate read at its own latest as_of_date <= draft_date."""
    maps = {}

    def latest_ranking(source):
        d = con.execute(
            "SELECT MAX(as_of_date) FROM rankings WHERE source=? AND as_of_date<=?",
            (source, draft_date),
        ).fetchone()[0]
        vals = {}
        if d:
            vals = {pid: rank for pid, rank in con.execute(
                "SELECT player_id, adp_rank FROM rankings WHERE source=? AND as_of_date=?",
                (source, d)).fetchall()}
        return ("gsis", vals, d)

    maps["fantasypros_ecr"] = latest_ranking("fantasypros_ecr")
    maps["fantasypros_csv_2026draft"] = latest_ranking("fantasypros_csv_2026draft")

    for fmt in ["ffc_half_ppr_10team", "ffc_ppr_10team", "ffc_non_ppr_10team"]:
        d = con.execute(
            "SELECT MAX(as_of_date) FROM ffc_adp_snapshots WHERE adp_source=? AND as_of_date<=?",
            (fmt, draft_date),
        ).fetchone()[0]
        vals = {}
        if d:
            vals = {mfl: pick for mfl, pick in con.execute(
                "SELECT mfl_id, average_pick FROM ffc_adp_snapshots WHERE adp_source=? AND as_of_date=?",
                (fmt, d)).fetchall()}
        maps[fmt] = ("mfl", vals, d)
    return maps


def spearman(pairs):
    n = len(pairs)
    if n < 2:
        return None
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0] * len(vals)
        for r, i in enumerate(order):
            ranks[i] = r + 1
        return ranks
    actual = [a for a, b in pairs]
    pred = [b for a, b in pairs]
    ra, rp = rank(actual), rank(pred)
    dsum = sum((ra[i] - rp[i]) ** 2 for i in range(n))
    return 1 - (6 * dsum) / (n * (n ** 2 - 1))


def run_m1(con: sqlite3.Connection) -> dict:
    resolve_skill = make_resolver(con)
    gsis_of = {mfl_id: sid for mfl_id, sid in con.execute(
        "SELECT mfl_id, source_id FROM player_ids WHERE source='gsis'").fetchall()}

    results = {}
    for mock_id, path in MOCKS:
        d = json.load(open(path))
        draft_date = d["drafted_at"]
        picks = d["picks"]

        resolved, unresolved, resolution_methods = [], [], {}
        for p in picks:
            mfl_id, method = resolve_skill(p["player_name_raw"])
            resolution_methods[method] = resolution_methods.get(method, 0) + 1
            if mfl_id is None:
                unresolved.append(p["player_name_raw"])
                continue
            resolved.append((p["overall_pick"], p["round"], mfl_id))

        src_maps = load_source_maps(con, draft_date)

        # Arithmetic check: round-by-round MAE vs ffc_half_ppr_10team ALONE,
        # all resolved picks in that round (no common-support filter) --
        # matches how the pre-registration's target numbers were hand-computed.
        _, ffc_vals, _ = src_maps["ffc_half_ppr_10team"]
        round_mae_ffc_only = {}
        for r in (1, 2, 3):
            errs = [abs(ffc_vals[mfl_id] - overall_pick)
                    for overall_pick, rnd, mfl_id in resolved
                    if rnd == r and mfl_id in ffc_vals]
            round_mae_ffc_only[r] = (statistics.mean(errs) if errs else None, len(errs))

        # Common support: a value present in ALL five candidates simultaneously.
        common = []
        for overall_pick, rnd, mfl_id in resolved:
            gsis = gsis_of.get(mfl_id)
            row_vals, ok = {}, True
            for cand in CANDIDATES:
                keytype, vals, _ = src_maps[cand]
                key = gsis if keytype == "gsis" else mfl_id
                if key is None or key not in vals:
                    ok = False
                    break
                row_vals[cand] = vals[key]
            if ok:
                common.append((overall_pick, rnd, mfl_id, row_vals))

        per_cand_mae, per_cand_rho = {}, {}
        for cand in CANDIDATES:
            errs = [abs(row_vals[cand] - overall_pick) for overall_pick, _, _, row_vals in common]
            per_cand_mae[cand] = statistics.mean(errs) if errs else None
            pairs = [(overall_pick, row_vals[cand]) for overall_pick, _, _, row_vals in common]
            per_cand_rho[cand] = spearman(pairs)

        results[mock_id] = {
            "draft_date": draft_date,
            "n_picks_total": len(picks),
            "n_resolved": len(resolved),
            "n_unresolved": len(unresolved),
            "resolution_methods": resolution_methods,
            "unresolved_sample": unresolved,
            "n_common_support": len(common),
            "mae_common_support": per_cand_mae,
            "rho_common_support": per_cand_rho,
            "round_mae_ffc_half_ppr_arith_check": round_mae_ffc_only,
            "source_dates_used": {c: src_maps[c][2] for c in CANDIDATES},
        }
    return results


def h1_verdict(m1_results: dict) -> dict:
    gaps, all_beat = [], True
    per_mock = {}
    for mock_id, r in m1_results.items():
        ecr = r["mae_common_support"]["fantasypros_ecr"]
        ffc = r["mae_common_support"]["ffc_half_ppr_10team"]
        gap = ecr - ffc  # positive => FFC half-PPR ADP beats ECR
        beat = ffc < ecr
        gaps.append(gap)
        all_beat = all_beat and beat
        per_mock[mock_id] = {"ecr_mae": ecr, "ffc_half_ppr_mae": ffc, "gap": gap, "ffc_beats_ecr": beat}
    mean_gap = statistics.mean(gaps)
    confirmed = all_beat and mean_gap >= 2.0
    return {
        "per_mock": per_mock,
        "mean_gap": mean_gap,
        "all_three_beat": all_beat,
        "threshold_met": confirmed,
        "verdict": "H1 CONFIRMED" if confirmed else "H1 NULL",
    }


def main():
    con = sqlite3.connect(str(DB_PATH))
    m0 = run_m0(con)
    m1 = run_m1(con)
    h1 = h1_verdict(m1)

    import pprint
    print("=== M0 ===")
    pprint.pprint(m0, width=140)
    print("\n=== M1 ===")
    pprint.pprint(m1, width=140)
    print("\n=== H1 ===")
    pprint.pprint(h1, width=140)


if __name__ == "__main__":
    main()
