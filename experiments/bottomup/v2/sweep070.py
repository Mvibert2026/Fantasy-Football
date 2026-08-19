#!/usr/bin/env python
"""ADR-070 sweep driver — detached, resumable, phase-gated.

    nohup .venv/bin/python -m experiments.bottomup.v2.sweep070 &

TESTS ARE COMPUTE, NOT TOKENS (founder, 2026-08-03). This process is designed
to keep fitting factors long after the session that launched it is gone. All
state lives on disk under `experiments/bottomup/results/sweep070/`:

    cells.csv          observed runs (k=0), arms + controls, §4.8-keyed
    draws/<cell>.csv   permutation-null draws, per-season metrics per draw
    graded_<batch>.csv ADR-070 §4.6 cell reports (grade070.py, idempotent)
    VERIFY_STATUS      PASS/FAIL + measured rates — the gate
    state.json         phase progress + wall-clock timings
    sweep.log          the log (this process's stdout is appended there)

PHASES, IN ORDER — THE GATE IS STRUCTURAL:

  1  VERIFY   VD1 (1-column seeded-noise arm) x 4 positions, K = 200 fixed
              draws -> §6.2(a) leave-one-out calibration + the 4 placebo cells
              graded end-to-end through the full rule. FAIL -> the process
              EXITS. Nothing real is graded on an unverified instrument.
  2  D1A1     Q0 first (the founder-priority population-refit arm), then
              Q0w (co-report), Q1, Q2, PG0. Endpoint: games MAE, M-panel.
  3  C1       full re-run at tier 2 + sequential ensembles + lazy k-arm
              ensembles for WIN candidates (p_two <= 0.10).
  4  C2       same.
  5  C3       if `c3_ready.flag` exists (the reconciled adapter registers its
              arms); otherwise skipped with a note and re-checked at the end.
  6  VD23     dimension-matched diagnostics (d = 2, 3; §6.2(b) / M-2 curve).

Resumability: every draw is appended to disk the moment it returns; on
restart the driver re-reads what exists and continues from the next k. The
Besag-Clifford scan is deterministic in the registered draw order, so a
restart cannot change any p.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.v2 import ensemble070 as ens              # noqa: E402
from experiments.bottomup.v2 import grade070 as gr                  # noqa: E402
from experiments.bottomup.v2.adr070 import H_EXCEED, bc_sequential_p  # noqa: E402

OUT = gr.OUT
DRAWS = gr.DRAWS
CELLS_CSV = gr.CELLS_CSV
STATE = OUT / "state.json"
VERIFY_STATUS = OUT / "VERIFY_STATUS"
#: flag-driven batch queue: each file under batches/ is one line,
#: "<batch_name> <importable.module.path>". The driver processes new flags as
#: they appear and keeps polling until queue_closed.flag exists — room for
#: late-arrival batches (the blocked-ledger re-audit) at zero token cost.
BATCH_FLAGS = OUT / "batches"
QUEUE_CLOSED = OUT / "queue_closed.flag"
POLL_SECONDS = 600

#: Workers. Measured 2026-08-04 on the 4-core container: 3 workers held the box
#: at 271% of 400% with 21.7% idle, so a fourth is free headroom rather than
#: oversubscription. The parent is idle while `imap` is in flight.
N_WORKERS = 4

#: Draws per `imap` batch. Between batches the parent re-reads the whole draws
#: CSV and re-derives every delta_bar to run the sequential test, so a FIXED
#: chunk makes that serial step O(n) work every CHUNK draws — quadratic in the
#: draw count, and the workers idle through all of it. At the L=8,999 tail that
#: was the single largest source of lost throughput.
#:
#: It cannot simply be raised: Besag-Clifford stops at h=20 exceedances, and a
#: dead factor stops within tens of draws. A large fixed chunk would compute
#: hundreds of draws past the stop on every null cell — and most cells are null.
#: So grow it with progress: small while an early stop is still plausible, large
#: once the cell is clearly running to L.
CHUNK_MIN = 12
CHUNK_DIVISOR = 8


def chunk_for(n_done: int) -> int:
    """Draws to request next. Overshoot past a sequential stop is bounded by
    n_done/CHUNK_DIVISOR, so the wasted fraction is constant, not growing."""
    return max(CHUNK_MIN, n_done // CHUNK_DIVISOR)


CHUNK = CHUNK_MIN          # retained: VERIFY's fixed-k path reads it
K_VERIFY = 200
L_DRAWS = gr.L_DRAWS


def log(msg: str) -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def _load_state() -> Dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"phases_done": [], "timings": {}}


def _save_state(st: Dict) -> None:
    STATE.write_text(json.dumps(st, indent=1))


# ------------------------------------------------------------------ workers
_worker_cache: Dict = {}
_worker_cell: List = [None]


def _init_worker() -> None:
    # under the fork context the parent's panel is inherited copy-on-write;
    # this is a no-op then, and a lazy build under spawn
    ens.shared_panel()


def _batch_module(batch: str) -> Optional[str]:
    for p in sorted(BATCH_FLAGS.glob("*.flag")) if BATCH_FLAGS.exists() else []:
        parts = p.read_text().split()
        if len(parts) == 2 and parts[0] == batch:
            return parts[1]
    return None


def _ensure_batch(batch: str) -> None:
    """Idempotent import of an adapter batch's registry — works in workers
    forked before the flag appeared."""
    if any(b == batch for (b, _) in ens.ARMS070):
        return
    mod = _batch_module(batch)
    if mod:
        import importlib
        importlib.import_module(mod)


def _task(args: Tuple) -> List[Dict]:
    kind = args[0]
    if kind in ("obs", "draw"):
        _ensure_batch(args[1])
    panel = ens.shared_panel()
    if kind == "ctrl":
        _, family, pos = args
        players = ens.run_control(panel, family, pos)
        cells = ens.season_cells(players, f"CTRL-{family}", "CTRL", pos,
                                 family, None, 0)
        return cells.to_dict("records")
    if kind == "obs":
        _, batch, arm, pos = args
        a = ens.ARMS070[(batch, arm)]
        players = ens.run_players(panel, batch, arm, pos, k=0)
        cells = ens.season_cells(players, arm, batch, pos, a.family,
                                 a.known_col, 0)
        return cells.to_dict("records")
    if kind == "draw":
        _, batch, arm, pos, k = args
        cell = (batch, arm, pos)
        if _worker_cell[0] != cell:
            _worker_cache.clear()
            _worker_cell[0] = cell
        a = ens.ARMS070[(batch, arm)]
        players = ens.run_players(panel, batch, arm, pos, k=k,
                                  frame_cache=_worker_cache)
        cells = ens.season_cells(players, arm, batch, pos, a.family, None, k)
        keep = ["season", "rho_points", "mae_games", "n_board_vet"]
        rows = cells[[c for c in keep if c in cells.columns]].copy()
        rows["k"] = k
        rows["batch"] = batch
        rows["arm"] = arm
        rows["position"] = pos
        return rows.to_dict("records")
    raise KeyError(kind)


def _task_safe(args: Tuple) -> List[Dict]:
    """`_task`, but a failure returns a marker row instead of raising.

    One bad arm used to kill the whole batch: `pool.imap` re-raises in the
    parent, so C4's 36 observed runs all died because a single arm tripped the
    look-ahead guard. Isolating the failure lets the other arms grade.

    This is deliberately NOT error-swallowing. Every failure is logged, written
    to errors_<batch>.csv, and the arm simply produces no observed cells -- so
    it is reported as NOT TESTED rather than quietly counted as a null. A factor
    that errored and a factor that was measured and found dead must never look
    the same in the four-number report.
    """
    try:
        return _task(args)
    except Exception as exc:                                # noqa: BLE001
        return [{"__error__": f"{type(exc).__name__}: {exc}",
                 "__task__": " ".join(str(x) for x in args)}]


# ------------------------------------------------------------ disk plumbing
def _append_cells(rows: List[Dict]) -> None:
    """Write observed rows to a PER-BATCH shard, never to a shared file.

    `cells.csv` used to be one file every batch appended to. That single fact
    made batch-level parallelism impossible: two runners each rewrite the whole
    CSV and collide on push. Sharding by batch makes batches independent on
    disk, which is what lets the workflow matrix run them at the same time.
    `grade070.load_cells()` unions the shards (and the legacy flat file, so
    nothing already computed is lost).
    """
    if not rows:
        return
    new = pd.DataFrame(rows)
    gr.CELLS_DIR.mkdir(parents=True, exist_ok=True)
    key = ["batch", "run", "position", "season", "k"]
    # Control rows all carry batch="CTRL", so batching alone would funnel every
    # family into one shared CTRL.csv -- reintroducing exactly the collision
    # this sharding exists to remove. Shard those by family instead (the `run`
    # column is "CTRL-<family>"). Two jobs may still both compute a shared
    # family; the rows are identical and load_cells() dedupes, so that costs a
    # little compute and corrupts nothing.
    new["_shard"] = new.apply(
        lambda r: str(r["run"]) if r["batch"] == "CTRL" else str(r["batch"]),
        axis=1)
    for shard, grp in new.groupby("_shard", sort=False):
        grp = grp.drop(columns=["_shard"])
        p = gr.CELLS_DIR / f"{shard}.csv"
        prev = pd.read_csv(p) if p.exists() else pd.DataFrame()
        merged = pd.concat([prev, grp], ignore_index=True) if len(prev) else grp
        merged = merged.drop_duplicates(subset=key, keep="last")
        merged.to_csv(p, index=False)


def _append_draws(batch: str, arm: str, pos: str, rows: List[Dict]) -> None:
    """Append one draw's rows. TRUE append — O(1) in the draws already banked.

    This used to read the whole CSV, concat, drop_duplicates and rewrite it,
    once per completed draw. That is O(n) per draw and therefore O(n^2) per
    cell: measured 2026-08-04 at 20% of a core at n=2,800, and it grows, so at
    the L=8,999 tail the parent would have been spending most of its time
    rewriting a 90,000-row file while the workers waited.

    Safe to append blind because `imap` yields in submission order and the
    driver resumes at `_draws_done() + 1`, so a k is never issued twice — and
    the reader pivots with aggfunc="last" regardless, so a duplicate from a
    torn resume would still resolve rather than corrupt.

    Written as one buffered `write` of the whole block so a container kill
    lands between rows rather than inside one. The old full rewrite could
    truncate the entire file at exactly that moment; this cannot.
    """
    if not rows:
        return
    p = DRAWS / f"{gr.cell_id(batch, arm, pos)}.csv"
    new = pd.DataFrame(rows)
    header = not p.exists() or p.stat().st_size == 0
    if not header:
        # match the existing header exactly: appending columns in a different
        # order than the file was created with would silently shift values
        with p.open("r") as fh:
            cols = fh.readline().strip().split(",")
        if set(cols) != set(new.columns):
            raise ValueError(f"{p.name}: draw columns {list(new.columns)} do "
                             f"not match the file's header {cols}")
        new = new[cols]
    with p.open("a", newline="") as fh:
        fh.write(new.to_csv(index=False, header=header))


def _have_cells(cells: pd.DataFrame, run: str, pos: str) -> bool:
    if not len(cells):
        return False
    return bool(((cells["run"] == run) & (cells["position"] == pos)
                 & (cells["k"] == 0)).any())


def _draws_done(batch: str, arm: str, pos: str) -> int:
    p = DRAWS / f"{gr.cell_id(batch, arm, pos)}.csv"
    if not p.exists():
        return 0
    d = pd.read_csv(p)
    return int(d["k"].max()) if len(d) else 0


# ------------------------------------------------------------- observed runs
def ensure_observed(pool, arms: List[ens.Arm070], st: Dict) -> None:
    cells = gr.load_cells()
    tasks = []
    fams = sorted({(a.family, p) for a in arms for p in a.positions})
    for family, pos in fams:
        if not _have_cells(cells, f"CTRL-{family}", pos):
            tasks.append(("ctrl", family, pos))
    for a in arms:
        for pos in a.positions:
            if not _have_cells(cells, a.arm, pos):
                tasks.append(("obs", a.batch, a.arm, pos))
    if not tasks:
        return
    log(f"observed runs needed: {len(tasks)}")
    t0 = time.time()
    errors: List[Dict] = []
    for rows in pool.imap(_task_safe, tasks):
        if rows and "__error__" in rows[0]:
            errors.append(rows[0])
            log(f"  ARM FAILED — {rows[0]['__task__']}: {rows[0]['__error__']}")
            continue
        _append_cells(rows)
    if errors:
        ep = OUT / f"errors_{arms[0].batch}.csv"
        pd.DataFrame(errors).to_csv(ep, index=False)
        log(f"*** {len(errors)} of {len(tasks)} observed runs FAILED and are "
            f"recorded in {ep.name}. Those arms produce no cells and must be "
            f"reported as NOT TESTED, never as null. ***")
    st["timings"][f"observed_{arms[0].batch}"] = round(time.time() - t0, 1)
    _save_state(st)
    log(f"observed runs done in {time.time()-t0:.0f}s")


# ---------------------------------------------------------------- ensembles
def obs_delta_bar(a: ens.Arm070, pos: str) -> Tuple[float, pd.DataFrame]:
    cells = gr.load_cells()
    deltas, seasons, n_g, _, _ = gr.obs_deltas(a, pos, cells)
    _, ctl_c = gr.obs_frames(cells, a, pos)
    if not len(deltas) or not np.isfinite(deltas).any():
        return np.nan, ctl_c
    return float(np.nanmean(deltas)), ctl_c


def run_ensemble(pool, a: ens.Arm070, pos: str, fixed_k: Optional[int] = None,
                 st: Optional[Dict] = None) -> None:
    """Draw until Besag-Clifford stops (or fixed_k draws exist). Resumable —
    reads what is on disk, appends in chunks."""
    if a.null_kind == "none":
        return
    db, ctl_c = obs_delta_bar(a, pos)
    cid = gr.cell_id(a.batch, a.arm, pos)
    if ctl_c is None:
        log(f"{cid}: no control cells — skipping ensemble")
        return
    if fixed_k is None and (not np.isfinite(db) or db == 0.0):
        log(f"{cid}: obs delta_bar={db} — no ensemble needed")
        return
    t0 = time.time()
    n_done = _draws_done(a.batch, a.arm, pos)
    while True:
        if fixed_k is not None:
            if n_done >= fixed_k:
                break
            nxt = list(range(n_done + 1, min(n_done + CHUNK, fixed_k) + 1))
        else:
            bars, _, _ = gr.draw_delta_bars(a, pos, ctl_c)
            seq = bc_sequential_p(db, bars, h=H_EXCEED, L=L_DRAWS)
            if seq.stop_reason in ("h_reached", "L_exhausted"):
                log(f"{cid}: stopped ({seq.stop_reason}) at n={seq.n_draws_used} "
                    f"p_two={seq.p_two:.4g} after {time.time()-t0:.0f}s")
                break
            # never request past L: draws beyond it can change no verdict
            hi = min(n_done + chunk_for(n_done), L_DRAWS)
            nxt = list(range(n_done + 1, hi + 1))
            if not nxt:            # L reached but the test did not stop: bail
                log(f"{cid}: at L={L_DRAWS} without a stop — leaving UNRESOLVED")
                break
        tasks = [("draw", a.batch, a.arm, pos, k) for k in nxt]
        # imap appends each draw as it lands, so a container kill mid-chunk
        # banks every completed draw — chunk size costs nothing on restart
        for rows in pool.imap(_task, tasks):
            _append_draws(a.batch, a.arm, pos, rows)
        n_done = nxt[-1]
        log(f"{cid}: {n_done} draws")
    if st is not None:
        st["timings"][cid] = round(time.time() - t0, 1)
        _save_state(st)


# ----------------------------------------------------------------- VERIFY
def loo_calibration(a: ens.Arm070, pos: str) -> Dict:
    cells = gr.load_cells()
    _, ctl_c = gr.obs_frames(cells, a, pos)
    bars, _, _ = gr.draw_delta_bars(a, pos, ctl_c)
    bars = bars[np.isfinite(bars)]
    K = len(bars)
    n_sig = 0
    for i in range(K):
        others = np.delete(bars, i)
        if bars[i] == 0.0:
            continue
        if bars[i] > 0:
            p1 = (1 + int(np.sum(others >= bars[i]))) / (len(others) + 1)
        else:
            p1 = (1 + int(np.sum(others <= bars[i]))) / (len(others) + 1)
        if min(1.0, 2 * p1) <= 0.05:
            n_sig += 1
    return {"position": pos, "K": K, "n_p_le_05": n_sig,
            "rate": n_sig / K if K else np.nan}


def verify_phase(pool, st: Dict) -> bool:
    arms = [ens.VERIFY_ARMS["VD1"]]
    ensure_observed(pool, arms, st)
    a = arms[0]
    for pos in a.positions:
        run_ensemble(pool, a, pos, fixed_k=K_VERIFY, st=st)

    # §6.2(a) leave-one-out — implementation must be exact before anything real
    rows = [loo_calibration(a, pos) for pos in a.positions]
    per_pos_ok = all(r["n_p_le_05"] <= 19 for r in rows)
    pooled = sum(r["n_p_le_05"] for r in rows)
    pooled_n = sum(r["K"] for r in rows)
    pooled_ok = pooled <= 53

    # §6.2(c) end-to-end: the 4 placebo cells through the FULL rule
    graded = gr.grade_batch("VERIFY")
    bad = graded[graded["verdict"].isin(["INCLUDE", "EXCLUDE (variance)",
                                         "RE-SPECIFY"])] if len(graded) else \
        pd.DataFrame()
    hyp = int((graded["verdict"] == "HYPOTHESIS").sum()) if len(graded) else 0
    e2e_ok = len(bad) == 0 and hyp <= 1

    status = "PASS" if (per_pos_ok and pooled_ok and e2e_ok) else "FAIL"
    lines = [f"{status}  ({time.strftime('%Y-%m-%d %H:%M:%S')})",
             f"LOO p<=0.05: pooled {pooled}/{pooled_n} (pass <= 53)"]
    for r in rows:
        lines.append(f"  {r['position']}: {r['n_p_le_05']}/{r['K']} "
                     f"(pass <= 19)")
    lines.append(f"end-to-end placebo: {len(bad)} INCLUDE/EXCLUDE/RE-SPECIFY "
                 f"(pass = 0), {hyp} HYPOTHESIS (pass <= 1)")
    VERIFY_STATUS.write_text("\n".join(lines) + "\n")
    log("VERIFY: " + " | ".join(lines))
    return status == "PASS"


# ------------------------------------------------------------- batch phases
def batch_phase(pool, batch: str, st: Dict) -> None:
    arms = [a for (b, _), a in ens.ARMS070.items() if b == batch]
    # graded order: Q0 first for D1A1 (founder priority), placebos with the rest
    order = {"Q0": 0, "Q0w": 1}
    arms.sort(key=lambda a: (order.get(a.arm, 5), a.arm))
    ensure_observed(pool, arms, st)
    karm_names = {a.arm for a in arms if a.arm.endswith("k")}
    for a in arms:
        if a.arm in karm_names or (a.batch, a.arm) in gr.CO_REPORT_ONLY:
            continue
        for pos in a.positions:
            run_ensemble(pool, a, pos, st=st)
    # lazy k-arm ensembles: only where the treatment is a WIN candidate
    cells = gr.load_cells()
    for a in arms:
        if a.arm in karm_names or a.null_kind == "none":
            continue
        kname = f"{a.arm}k"
        if (batch, kname) not in ens.ARMS070:
            continue
        ka = ens.ARMS070[(batch, kname)]
        for pos in a.positions:
            db, ctl_c = obs_delta_bar(a, pos)
            if not np.isfinite(db) or db <= 0 or ctl_c is None:
                continue
            bars, _, _ = gr.draw_delta_bars(a, pos, ctl_c)
            seq = bc_sequential_p(db, bars, h=H_EXCEED, L=L_DRAWS)
            if np.isfinite(seq.p_two) and seq.p_two <= 0.10 \
                    and seq.direction == "WIN":
                log(f"{batch}:{a.arm}:{pos} WIN candidate "
                    f"(p={seq.p_two:.3g}) — running paired {kname} ensemble")
                run_ensemble(pool, ka, pos, st=st)
    graded = gr.grade_batch(batch)
    try:                                # the deliverable stays current with
        from . import report070         # the compute; a report bug must never
        report070.generate()            # kill the sweep
    except Exception as e:              # pragma: no cover
        log(f"report070 regeneration failed (non-fatal): {e}")
    if len(graded):
        log(f"graded {batch}: " + ", ".join(
            f"{r.arm}/{r.position}={r.verdict}"
            for r in graded.itertuples() if r.verdict not in
            ("NULL (calibrated)",)) or "all NULL (calibrated)")
        incl = graded[graded["verdict"] == "INCLUDE"]
        if len(incl):
            log(f"*** {batch}: {len(incl)} INCLUDE verdict(s) — per M-6 this "
                f"is a stop-and-report trigger; verdicts recorded, adoption "
                f"requires strategist review ***")


def _pending_flag_batches(done) -> List[Tuple[str, str]]:
    out = []
    if not BATCH_FLAGS.exists():
        return out
    for p in sorted(BATCH_FLAGS.glob("*.flag")):
        parts = p.read_text().split()
        if len(parts) == 2 and parts[0] not in done:
            out.append((parts[0], parts[1]))
    return out


# ----------------------------------------------------------------------- main
def run_single_batch(batch: str) -> None:
    """Run exactly one batch, then grade it and stop.

    This is what makes batch-level parallelism possible. The default main()
    walks every phase in order on one machine, which is correct but strictly
    serial -- and with ~300 cells left and most of the cost in a handful of
    real effects, serial was the difference between finishing in a day and
    finishing in a week.

    Isolation is the whole point, so nothing here touches shared state:
    observed rows go to a per-batch shard (`_append_cells`), draws are already
    per-cell, grading writes `graded_<batch>.csv`, and progress is recorded in
    `state_<batch>.json` rather than the shared `state.json`. Two of these can
    run on two machines and collide on nothing.
    """
    import importlib
    OUT.mkdir(parents=True, exist_ok=True)
    DRAWS.mkdir(parents=True, exist_ok=True)
    # Import EVERY registered batch module, not just this one, then run only
    # the requested batch. Control families are shared across batches and are
    # registered as an import side effect -- `T2P` is defined in
    # factors_c3_adapter.py but used by C4 -- so importing one batch in
    # isolation left TIER2 incomplete and every matrix job died with
    # KeyError: 'T2P'. Serial mode never hit this because it imported the
    # batches cumulatively as it walked the queue. Imports are cheap and
    # idempotent; only the run below is scoped to one batch.
    for _, _mod in _pending_flag_batches([]):
        try:
            importlib.import_module(_mod)
        except Exception as exc:                            # noqa: BLE001
            log(f"could not import {_mod}: {type(exc).__name__}: {exc}")
    mod = _batch_module(batch)
    if mod:
        importlib.import_module(mod)
    if not any(b == batch for (b, _) in ens.ARMS070):
        log(f"batch {batch} has no registered arms — nothing to do")
        return
    st_path = OUT / f"state_{batch}.json"
    st = json.loads(st_path.read_text()) if st_path.exists() else \
        {"phases_done": [], "timings": {}}
    log(f"single-batch mode: {batch}")
    log(f"L={L_DRAWS}, h={H_EXCEED}, M={gr.M_CAMPAIGN}, workers={N_WORKERS}")
    ens.shared_panel()
    with mp.get_context("fork").Pool(N_WORKERS, initializer=_init_worker) \
            as pool:
        batch_phase(pool, batch, st)
    st["phases_done"] = sorted(set(st["phases_done"]) | {batch})
    st_path.write_text(json.dumps(st, indent=1))
    log(f"batch {batch} complete")


def main() -> None:
    import argparse
    import importlib
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", help="run only this batch, then grade and exit "
                                    "(enables running batches in parallel)")
    args = ap.parse_args()
    if args.batch:
        run_single_batch(args.batch)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    DRAWS.mkdir(parents=True, exist_ok=True)
    BATCH_FLAGS.mkdir(parents=True, exist_ok=True)
    st = _load_state()
    log(f"sweep070 starting; phases done: {st['phases_done']}")
    log(f"L={L_DRAWS}, h={H_EXCEED}, M={gr.M_CAMPAIGN}, workers={N_WORKERS}")

    # build the panel BEFORE forking: all workers share it copy-on-write,
    # one 8-second build and one copy in RAM instead of three
    ens.shared_panel()
    with mp.get_context("fork").Pool(N_WORKERS, initializer=_init_worker) \
            as pool:
        if "VERIFY" not in st["phases_done"]:
            ok = verify_phase(pool, st)
            if not ok:
                log("VERIFY FAILED — stopping before grading anything real. "
                    "Report to strategist; do NOT weaken the check.")
                sys.exit(2)
            st["phases_done"].append("VERIFY")
            _save_state(st)

        for batch in ("D1A1", "C1", "C2"):
            if batch not in st["phases_done"]:
                batch_phase(pool, batch, st)
                st["phases_done"].append(batch)
                _save_state(st)

        # flag-driven batches (C3, C4, AB1, and any late arrival), then the
        # dimension diagnostics, then keep polling until the queue is closed
        while True:
            todo = _pending_flag_batches(st["phases_done"])
            for name, mod in todo:
                importlib.import_module(mod)
                log(f"flag batch {name} ({mod})")
                batch_phase(pool, name, st)
                st["phases_done"].append(name)
                _save_state(st)

            for vd in ("VD2", "VD3"):
                if vd not in st["phases_done"]:
                    a = ens.VERIFY_ARMS[vd]
                    ensure_observed(pool, [a], st)
                    for pos in a.positions:
                        run_ensemble(pool, a, pos, fixed_k=K_VERIFY, st=st)
                    st["phases_done"].append(vd)
                    _save_state(st)

            if _pending_flag_batches(st["phases_done"]):
                continue
            if QUEUE_CLOSED.exists():
                break
            log(f"queue open, no new batch flags — polling again in "
                f"{POLL_SECONDS//60} min (touch queue_closed.flag to finish)")
            time.sleep(POLL_SECONDS)

    log("sweep070 complete. Graded CSVs + VERIFY_STATUS under "
        f"{OUT.relative_to(_REPO)}")


if __name__ == "__main__":
    main()
