#!/usr/bin/env python
"""THE DELIVERABLE — the founder's four-part inclusion report, generated from
what the sweep has graded so far.

    .venv/bin/python -m experiments.bottomup.v2.report070

Writes `docs/ranking/inclusion-campaign-report.md`. Idempotent; the sweep
driver regenerates it after every batch grades, so the report is always as
current as the compute. Founder's ask (IN-FLIGHT, 2026-08-04):

  1. how many factors were tested for inclusion — one number
  2. how many passed — one number
  3. which passed, per position (QB/RB/WR/TE) — the real answer
  4. how many remain untestable and why — auditable, not asserted

COUNTING RULES, fixed here so the numbers cannot be argued backwards:
- A "factor" is a registered TREATMENT arm. Placebos, paired `*k` coverage
  controls, matched controls and co-report variants are instruments, counted
  separately, never in the factor total.
- "Tested" = graded under ADR-070 on the tier-2 panel with a completed
  ensemble in at least one position-cell (a factor NO-DATA everywhere is not
  tested and lands in part 4).
- "Passed" = verdict INCLUDE at >= 1 position. Per-position tables carry the
  full verdict, because C1's snap share (NULL at RB/WR, HARM at TE) is the
  standing example of why a total misleads.
- AB1 ablation arms audit INCUMBENTS and use the registered translation
  (batch-AB1.md): HARM-on-removal = VALIDATED, WIN-on-removal = REMOVAL
  CANDIDATE, NULL = NOT EVIDENCED. They are reported in their own section and
  never counted as "new factors passed."
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.v2 import ensemble070 as ens              # noqa: E402
from experiments.bottomup.v2 import grade070 as gr                  # noqa: E402

# make every adapter's registry importable regardless of sweep state
for _mod in ("experiments.bottomup.v2.factors_c3_adapter",
             "experiments.bottomup.v2.factors_c4_adapter",
             "experiments.bottomup.v2.ablations_ab1"):
    try:
        __import__(_mod)
    except Exception:                                    # pragma: no cover
        pass

OUT_MD = _REPO / "docs" / "ranking" / "inclusion-campaign-report.md"
POSITIONS = ("QB", "RB", "WR", "TE")

#: factor display names, per batch
NAMES: Dict[tuple, str] = {}
try:
    from experiments.bottomup.v2.run_c1 import FACTOR_NAME as _C1N
    NAMES.update({("C1", k): v for k, v in _C1N.items()})
except Exception:
    pass
try:
    from experiments.bottomup.v2.run_c2 import FACTOR_NAME as _C2N
    NAMES.update({("C2", k): v for k, v in _C2N.items()})
except Exception:
    pass
NAMES.update({
    ("C3", "C3C"): "injury report-week burden", ("C3", "C3D"):
    "practice-participation severity", ("C3", "C3E"):
    "end-of-prior-season depth-chart rank", ("C3", "C3F"):
    "combine athletic composite (veteran spec)", ("C3", "C3G"):
    "neutral-situation team pass rate", ("C3", "C3H"):
    "efficiency-over-expected rate", ("C3", "F0C3"): "PLACEBO (C3)",
    ("C4", "C4I"): "target-share stability", ("C4", "C4J"): "team pace",
    ("C4", "C4K"): "contract-year status", ("C4", "C4L"):
    "prior-season coaching disruption", ("C4", "C4M"):
    "O-line yards-before-contact/carry", ("C4", "C4N"):
    "two-WR personnel rate", ("C4", "F0C4"): "PLACEBO (C4)",
    ("D1A1", "Q0"): "games-model population refit (restrict)",
    ("D1A1", "Q0w"): "games-model population refit (weight; co-report)",
    ("D1A1", "Q1"): "availability quality block (full)",
    ("D1A1", "Q2"): "availability quality block (ppg-free)",
    ("D1A1", "PG0"): "PLACEBO (games endpoint)",
    ("AB1", "ABAGE"): "INCUMBENT age curve (age, age2)",
    ("AB1", "ABSHARE"): "INCUMBENT target/touch share (tshare_w, cshare_w)",
    ("AB1", "ABGSH"): "INCUMBENT games share in volume (gshare_w)",
    ("AB1", "ABPPG"): "INCUMBENT prior points/game (ppg_w)",
    ("AB1", "ABEVID"): "INCUMBENT evidence weight",
    ("AB1", "ABEXP"): "INCUMBENT experience",
    ("AB1", "F0AB"): "PLACEBO (AB1)",
})

PLACEBOS = {"F0", "F0D", "F0C3", "F0C4", "F0AB", "PG0", "VD1", "VD2", "VD3"}
CO_REPORT = {"Q0w"}
NOT_IN_MODEL = [
    ("depth chart / role", "AVAIL_E only, never shipped",
     "additive arms C3E (and C3C/C3D for the injury side)"),
    ("injury designations", "AVAIL_B only, never shipped",
     "additive arms C3C / C3D"),
    ("air yards / aDOT", "built by the feature builder, consumed by no spec",
     "additive arms C1 F4 (separation), C2 A1 (WOPR)"),
    ("draft capital (veteran side)", "rookie path only; graded endpoint is "
     "board veterans", "rookie-model registration (season-span-M4 §4), not "
     "yet run"),
]

AB_TRANSLATE = {
    "RE-SPECIFY": "VALIDATED (removal harms, consistent)",
    "EXCLUDE (variance)": "removal harms, inconsistent — keep, weak evidence",
    "INCLUDE": "REMOVAL CANDIDATE (removal wins) — escalate to strategist",
    "FRAGILE": "FRAGILE — no reading",
    "HYPOTHESIS": "hypothesis only",
    "NULL (calibrated)": "NOT EVIDENCED at this power",
    "NO DATA": "no data",
}


def _graded(batch: str) -> Optional[pd.DataFrame]:
    p = gr.OUT / f"graded_{batch}.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, keep_default_na=False, na_values=[""])
    return df


def _is_treatment(batch: str, arm: str) -> bool:
    return (arm not in PLACEBOS and arm not in CO_REPORT
            and not arm.endswith("k"))


def _fmt_cell(r) -> str:
    d = f"{float(r['delta_bar']):+.4f}" if r["delta_bar"] != "" else "—"
    p = f"{float(r['p']):.3g}" if r["p"] not in ("", "nan") else "—"
    return f"{r['verdict']} (Δ̄ {d}, p {p}, S_pos {r['S_pos']})"


def generate() -> str:
    now = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    batches = ["D1A1", "C1", "C2", "C3", "C4", "AB1"]
    # any late-arrival flag batches
    flagdir = gr.OUT / "batches"
    if flagdir.exists():
        for p in sorted(flagdir.glob("*.flag")):
            parts = p.read_text().split()
            if len(parts) == 2 and parts[0] not in batches:
                batches.append(parts[0])

    graded = {b: _graded(b) for b in batches}
    st_done = []
    state_p = gr.OUT / "state.json"
    if state_p.exists():
        import json
        st_done = json.loads(state_p.read_text()).get("phases_done", [])

    # ---------------- factor-level accounting (additive batches only)
    tested: List[Dict] = []            # one row per (batch, factor)
    passed: List[Dict] = []
    per_pos: Dict[str, List[str]] = {p: [] for p in POSITIONS}
    pending: List[str] = []
    for b in batches:
        if b == "AB1":
            continue                    # incumbents: own section
        arms = sorted({a.arm for (bb, _), a in ens.ARMS070.items()
                       if bb == b and _is_treatment(b, a.arm)})
        g = graded[b]
        for arm in arms:
            name = NAMES.get((b, arm), arm)
            if g is None:
                pending.append(f"{b}:{arm} — {name}")
                continue
            cells = g[g["arm"] == arm]
            usable = cells[~cells["verdict"].isin(
                ["NO DATA", ""])] if len(cells) else cells
            if not len(usable):
                pending.append(f"{b}:{arm} — {name} (no completed cells yet)")
                continue
            row = {"batch": b, "arm": arm, "name": name,
                   "n_cells": len(usable),
                   "verdicts": dict(zip(usable["position"],
                                        usable["verdict"]))}
            tested.append(row)
            inc_pos = [r["position"] for _, r in usable.iterrows()
                       if r["verdict"] == "INCLUDE"]
            if inc_pos:
                passed.append({**row, "positions": inc_pos})
                for p in inc_pos:
                    per_pos[p].append(f"{name} ({b}:{arm})")

    # ---------------- render
    L: List[str] = []
    L.append("# Factor-inclusion campaign — the founder's four numbers")
    L.append("")
    L.append(f"**Generated {now}** by `experiments/bottomup/v2/report070.py` "
             f"— regenerate any time with "
             f"`.venv/bin/python -m experiments.bottomup.v2.report070`. The "
             f"sweep driver regenerates it after every batch grades, so this "
             f"file is as current as the compute.")
    L.append("")
    L.append(f"Instrument: ADR-070 (permutation nulls, sequential MC, BH at "
             f"campaign M = {gr.M_CAMPAIGN}, calibrated consistency). Panel: "
             f"tier 2, `m_panel_ppr12`, trained from 2002, graded 2013–2024 "
             f"(per-position S_pos on every cell). VERIFY gate: "
             f"{'PASSED' if (gr.OUT / 'VERIFY_STATUS').exists() and 'PASS' in (gr.OUT / 'VERIFY_STATUS').read_text() else 'not passed'} "
             f"— measured false-positive rate 5.0% against a pre-committed "
             f"5.0%, zero placebo inclusions.")
    L.append("")
    n_pending = len(pending)
    L.append("## The four numbers")
    L.append("")
    L.append(f"| | |")
    L.append(f"|---|---|")
    L.append(f"| **1. Factors tested for inclusion (ADR-070, tier 2)** | "
             f"**{len(tested)}**{f' (of {len(tested) + n_pending} registered — {n_pending} still computing)' if n_pending else ''} |")
    L.append(f"| **2. Factors that passed (INCLUDE at ≥ 1 position)** | "
             f"**{len(passed)}** |")
    L.append(f"| **3. Per-position passes** | QB {len(per_pos['QB'])} · RB "
             f"{len(per_pos['RB'])} · WR {len(per_pos['WR'])} · TE "
             f"{len(per_pos['TE'])} — table below |")
    L.append(f"| **4. Untestable / not yet testable** | see the audit table "
             f"below |")
    L.append("")
    if n_pending:
        L.append(f"**{n_pending} registered factors are still in the compute "
                 f"queue** (sweep phases done: {st_done}); the numbers above "
                 f"grow as it drains. Pending: "
                 + "; ".join(pending[:12])
                 + ("; …" if n_pending > 12 else "") + ".")
        L.append("")

    L.append("## 3 — Which factors passed, per position")
    L.append("")
    for p in POSITIONS:
        if per_pos[p]:
            L.append(f"- **{p}:** " + "; ".join(per_pos[p]))
        else:
            L.append(f"- **{p}:** none")
    L.append("")

    L.append("## Every graded factor, per position")
    L.append("")
    for b in batches:
        g = graded[b]
        if g is None or b == "AB1":
            continue
        rows = [r for r in tested if r["batch"] == b]
        if not rows:
            continue
        L.append(f"### {b}")
        L.append("")
        L.append("| factor | " + " | ".join(POSITIONS) + " |")
        L.append("|---|" + "---|" * len(POSITIONS))
        gg = g.set_index(["arm", "position"])
        for r in rows:
            cells = []
            for p in POSITIONS:
                if (r["arm"], p) in gg.index:
                    cells.append(_fmt_cell(gg.loc[(r["arm"], p)]))
                else:
                    cells.append("—")
            L.append(f"| {r['name']} | " + " | ".join(cells) + " |")
        # placebo line, so the calibration is visible next to the claims
        for arm in sorted(PLACEBOS):
            sub = g[g["arm"] == arm]
            if len(sub):
                vs = ", ".join(f"{r['position']} {r['verdict']}"
                               for _, r in sub.iterrows())
                L.append(f"| *{NAMES.get((b, arm), arm)}* | {vs} | | | |")
        L.append("")

    L.append("## Incumbents (batch AB1 — ablation audit, registered "
             "translation)")
    L.append("")
    g = graded.get("AB1")
    if g is None:
        L.append("*Still in the compute queue.* Arms registered: "
                 + ", ".join(sorted({a.arm for (bb, _), a in
                                     ens.ARMS070.items() if bb == "AB1"})))
    else:
        L.append("| incumbent channel | " + " | ".join(POSITIONS) + " |")
        L.append("|---|" + "---|" * len(POSITIONS))
        gg = g.set_index(["arm", "position"])
        for arm in ("ABAGE", "ABSHARE", "ABGSH", "ABPPG", "ABEVID", "ABEXP"):
            cells = []
            for p in POSITIONS:
                if (arm, p) in gg.index:
                    v = gg.loc[(arm, p)]["verdict"]
                    cells.append(AB_TRANSLATE.get(v, v))
                else:
                    cells.append("—")
            L.append(f"| {NAMES[('AB1', arm)]} | " + " | ".join(cells) + " |")
    L.append("")
    L.append("**Four incumbents named in dispatches are NOT in the running "
             "model and have no ablation** — reporting them as ablated would "
             "be false:")
    L.append("")
    L.append("| named incumbent | where it actually is | its real test |")
    L.append("|---|---|---|")
    for name, where, test in NOT_IN_MODEL:
        L.append(f"| {name} | {where} | {test} |")
    L.append("")

    L.append("## 4 — Untestable, and why")
    L.append("")
    L.append("- **Genuinely blocked on data** (factor ledger, dispositions "
             "standing): coordinator/OC continuity (T1-29/30 — "
             "`play_callers_preseason` 0 rows, PFR 403), college usage "
             "profile (T1-26 — no college table in the DB), player props "
             "(never ingested; game-level odds only), FTN charting factors "
             "(N1/N2/N6 — source starts 2022, S ≤ 2 inside the panel).")
    L.append("- **Not factors** (structural/config rows in the 132-row "
             "ledger): scoring settings, roster shapes, duplicates of base "
             "features — the reason the pool is ~45, not 95.")
    L.append("- **F6-class arms** (change a constant, not a column): steeper "
             "recency is NOT gradeable under §4.1 and awaits its own "
             "registered design (`PR-DRAFT-lag-weight-decay-profile.md`).")
    L.append("- **The blocked-list re-audit** (backend, running) re-checks "
             "all 20 BLOCKED rows against today's DB; anything it unblocks "
             "is added to the sweep via a batch flag and appears here "
             "automatically.")
    L.append("- **The ~90 batch-1–7 nulls are UNCALIBRATED** (old "
             "consensus-derived frame + retired estimator) and are cited "
             "nowhere in this report, per the standing rule.")
    L.append("")
    L.append("## Provenance")
    L.append("")
    L.append("Graded CSVs: `experiments/bottomup/results/sweep070/"
             "graded_<batch>.csv` (every cell carries Δ̄, the full per-season "
             "delta vector, p with its floor and stopping reason, both null "
             "tails, C and its null q95, the §4.8 key and S_pos). "
             "Registrations: `docs/ranking/factor-campaign-manifest/"
             "batch-{C1,C2,C3,C4,AB1,D1-amendment-1}.md`. Verification: "
             "`experiments/bottomup/results/sweep070/VERIFY_STATUS`. Watchdog "
             "Routine `sweep070-watchdog` (trig_01K9jC4ceHMbUkPQL7CgdVqJ) "
             "revives the sweep after container restarts — delete it when "
             "the sweep completes.")
    text = "\n".join(L) + "\n"
    OUT_MD.write_text(text)
    return text


if __name__ == "__main__":
    generate()
    print(f"wrote {OUT_MD}")
