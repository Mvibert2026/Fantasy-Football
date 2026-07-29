"""
Mock draft logging (ADR-042) -- the validation instrument for the availability
model, per the Strategist's mock_validation_protocol.md.

WHY THIS EXISTS. Every availability figure in this project (ADR-034's ranking
mixture, mechanical need, sigma schedule) is currently UNVALIDATED against any
real draft behaviour -- there is no historical board to check "did tier-1 RBs
actually survive to pick 18 ~46% of the time" against. Logged mock drafts are
the first real check. mock_validation_report.py is the comparison; this module
is only ingestion.

FILE-BASED, NOT AN API ENDPOINT. Matches the project's static/offline
architecture (CLAUDE.md SS4): the front end produces one JSON file per
completed mock draft; this module reads, validates, and inserts it. No server,
no live endpoint.

SCHEMA IS FIXED TO WHAT THE FRONT END EXPORTS -- do not add required fields
without checking with that session first; the whole point of matching it
exactly is that ingestion needs no translation. `drafter_type` is the one
OPTIONAL exception (ADR-043): 'human' | 'bot' | 'unknown', per pick, added
specifically so the bot-seat discard gate can be checked instead of being
permanently unenforceable.

    mock_drafts(mock_id, league_config_id, platform, drafted_at, source, is_mock)
    mock_picks(mock_id, overall_pick, round, team_slot, mfl_id, player_name_raw,
               predicted_top, predicted_p, timestamp, drafter_type=optional)

NAME RESOLUTION. `mfl_id` is trusted directly if the source file supplies it
(validated against players_canonical, not blindly accepted). If null,
`player_name_raw` is resolved via identity.resolve_name() -- the same
suffix/punctuation-normalized exact match used by coverage_report_for_board()
(measured 98.5% on the live board). Zero or ambiguous (>1) matches go to
mock_pick_quarantine, NEVER a best-effort guess -- the whole point of a
quarantine table is that "probably this player" is not the same as "this
player", and calibration numbers computed from guessed identities would be
silently wrong in a way nothing downstream could detect.

DISCARD GATES (protocol SS4), BOTH NOW CHECKABLE:
  - Format-mismatch (10-team/3WR-2FLEX/no-kicker/half-PPR): via
    league_config_id -> LeagueConfig lookup. `format_conforms()`.
  - Bot-seat (>3 bot seats discarded): ADR-043. If NO pick in a mock supplies
    `drafter_type`, the whole mock is `bot_seat_status='unknown'` -- flagged,
    never silently included as passing or excluded as failing. If at least
    one pick supplies it, the number of DISTINCT team_slots with
    drafter_type='bot' is counted; >3 -> `bot_seat_status='excluded_too_many_bots'`
    (a hard discard, same as format-mismatch), else `'conforms'`.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import identity as idn
import league_config as lc
import mock_prediction as mpred

_CREATE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS mock_drafts (
        mock_id TEXT PRIMARY KEY,
        league_config_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        drafted_at TEXT NOT NULL,
        source TEXT,
        is_mock INTEGER NOT NULL DEFAULT 1,
        format_conforms INTEGER,
        format_conforms_note TEXT,
        bot_seat_status TEXT NOT NULL DEFAULT 'unknown',
        bot_seat_count INTEGER,
        ingested_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mock_picks (
        mock_id TEXT NOT NULL REFERENCES mock_drafts(mock_id),
        overall_pick INTEGER NOT NULL,
        round INTEGER,
        team_slot INTEGER,
        mfl_id TEXT,
        player_name_raw TEXT,
        predicted_top TEXT,
        predicted_p REAL,
        timestamp TEXT,
        drafter_type TEXT,
        resolution_method TEXT NOT NULL,
        PRIMARY KEY (mock_id, overall_pick)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mock_pick_quarantine (
        mock_id TEXT NOT NULL,
        overall_pick INTEGER NOT NULL,
        player_name_raw TEXT,
        mfl_id_supplied TEXT,
        reason TEXT NOT NULL,
        quarantined_at TEXT NOT NULL,
        PRIMARY KEY (mock_id, overall_pick)
    )
    """,
]

REQUIRED_DRAFT_FIELDS = ("mock_id", "league_config_id", "platform", "drafted_at", "picks")
REQUIRED_PICK_FIELDS = ("overall_pick",)


@dataclass
class IngestReport:
    mock_id: str
    picks_total: int
    picks_resolved: int
    picks_quarantined: int
    format_conforms: Optional[bool]
    format_conforms_note: str


class MockDraftValidationError(ValueError):
    pass


def ensure_tables(conn: sqlite3.Connection) -> None:
    for stmt in _CREATE_SQL:
        conn.execute(stmt)
    _migrate_add_column(conn, "mock_drafts", "bot_seat_count", "INTEGER")
    _migrate_add_column(conn, "mock_picks", "drafter_type", "TEXT")

    # ADR-054: frozen per-draft league-shape snapshot (never a live re-lookup
    # -- see module docstring update below). ALTER TABLE, same non-destructive
    # pattern as bot_seat_count/drafter_type above -- these tables accumulate
    # real logged mock drafts and must not be rebuilt.
    _migrate_add_column(conn, "mock_drafts", "teams", "INTEGER")
    _migrate_add_column(conn, "mock_drafts", "draft_type", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "user_draft_slot", "INTEGER")
    _migrate_add_column(conn, "mock_drafts", "starters_json", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "flex_slots", "INTEGER")
    _migrate_add_column(conn, "mock_drafts", "flex_eligible_json", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "bench", "INTEGER")
    _migrate_add_column(conn, "mock_drafts", "ir", "INTEGER")
    _migrate_add_column(conn, "mock_drafts", "scoring_json", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "league_config_hash", "TEXT")

    # ADR-054: prediction-snapshot completeness, the structural gate.
    _migrate_add_column(conn, "mock_drafts", "predictions_model_version", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "predictions_board_source", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "predictions_board_as_of_date", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "predictions_complete", "INTEGER")
    _migrate_add_column(conn, "mock_drafts", "predictions_note", "TEXT")
    _migrate_add_column(conn, "mock_drafts", "calibration_usable", "INTEGER")
    _migrate_add_column(conn, "mock_drafts", "calibration_usable_note", "TEXT")

    _migrate_add_column(conn, "mock_picks", "predicted_top5_json", "TEXT")
    _migrate_add_column(conn, "mock_picks", "prediction_source", "TEXT")
    _migrate_add_column(conn, "mock_picks", "board_as_of_date", "TEXT")


def _migrate_add_column(conn: sqlite3.Connection, table: str, column: str, sql_type: str) -> None:
    """ADR-043 added drafter_type/bot_seat_count after mock_drafts/mock_picks
    already existed for some earlier sessions. ALTER TABLE ADD COLUMN rather
    than drop-and-rebuild (the pattern ingest_reference.py/identity.py use
    elsewhere) -- those tables are rebuilt from an external source on every
    run; these are an accumulating log, and dropping them would destroy
    already-logged real mock drafts."""
    existing = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()}
    if column not in existing:
        conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {sql_type}')


def format_conforms(cfg: lc.LeagueConfig) -> tuple[bool, str]:
    """Hard gate, protocol SS4: 10-team, 3WR/2FLEX, no kicker, half-PPR. A
    conforming mock's league_config_id must point at a LeagueConfig matching
    this shape -- NOT adjusted or reweighted if it doesn't, discarded."""
    reasons = []
    if cfg.teams != 10:
        reasons.append(f"teams={cfg.teams}, need 10")
    if cfg.starters.get("WR") != 3:
        reasons.append(f"WR starters={cfg.starters.get('WR')}, need 3")
    if cfg.flex_slots != 2:
        reasons.append(f"flex_slots={cfg.flex_slots}, need 2")
    if "K" in cfg.starters and cfg.starters["K"] > 0:
        reasons.append("rosters a kicker, need none")
    ppr = cfg.scoring.get("offense", {}).get("receptions")
    if ppr != 0.5:
        reasons.append(f"receptions={ppr}, need 0.5 (half-PPR)")
    if reasons:
        return False, "; ".join(reasons)
    return True, "conforms to the 10-team/3WR-2FLEX/no-kicker/half-PPR gate"


def _league_config_hash(cfg: lc.LeagueConfig) -> str:
    """SHA-256 of the full frozen config, so two mocks whose
    `league_config_id` string collides (or whose referenced file is later
    edited) can still be told apart -- CURRENT-STATE flagged this as a real
    gap: `mock_drafts` previously stored only the FK-style
    `league_config_id`, so a later edit to that saved file would silently
    reinterpret every historical mock under the new shape."""
    return hashlib.sha256(
        json.dumps(cfg.to_dict(), sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def calibration_usable(
    format_ok: bool, bot_seat_status: str, predictions_complete: bool
) -> Tuple[bool, str]:
    """ADR-054's structural gate: 'conforming' is necessary but not
    sufficient for calibration use. A mock is usable toward the ~30-mock
    pre-registered decision rule (CLAUDE.md SS6.3, ADR-045's D-004) only if
    it ALSO carries a complete per-pick prediction snapshot -- otherwise
    there is nothing to score a Brier/calibration comparison against, and a
    mock silently missing that must never be counted toward the target
    (founder's framing: "visibly worse than not-yet-logged", not quietly
    included). This is additive to, not a replacement for,
    `format_conforms`/`_bot_seat_status` -- see
    `mock_validation_report.conforming_mock_ids` for the pre-existing gate
    those two alone drive (depletion-only reports that need no per-pick
    prediction at all)."""
    reasons = []
    if not format_ok:
        reasons.append("format does not conform to the protocol gate")
    if bot_seat_status == "excluded_too_many_bots":
        reasons.append("too many bot seats (>3)")
    if not predictions_complete:
        reasons.append(
            "prediction snapshot incomplete -- this mock cannot validate the "
            "availability model and must not count toward the ~30-mock target"
        )
    if reasons:
        return False, "; ".join(reasons)
    return True, (
        "usable for calibration: format conforms, bot-seat gate passes, "
        "prediction snapshot complete for every pick"
    )


def _bot_seat_status(picks: List[dict]) -> Tuple[str, Optional[int]]:
    """ADR-043. Bot-seat gate, protocol SS4: 'Mocks with >3 bot seats are
    discarded.' Computed from ALL picks (resolved or not -- drafter_type is a
    property of the SEAT, independent of whether the picked player's name
    resolved) that carry a team_slot.

    'unknown' if NO pick anywhere in the mock supplies drafter_type -- the
    front end simply doesn't have this data for that mock, which is expected
    to be common until whatever mock platform is used exposes it. Distinct
    from 'conforms'/'excluded_too_many_bots', which both mean the data WAS
    supplied and the count WAS checked.
    """
    any_supplied = any(p.get("drafter_type") is not None for p in picks)
    if not any_supplied:
        return "unknown", None
    bot_seats = {
        p.get("team_slot") for p in picks
        if p.get("drafter_type") == "bot" and p.get("team_slot") is not None
    }
    n = len(bot_seats)
    return ("excluded_too_many_bots" if n > 3 else "conforms"), n


def _load_league_config(league_config_id: str) -> lc.LeagueConfig:
    if league_config_id == lc.PRIMARY_LEAGUE_ID:
        return lc.CURRENT_LEAGUE
    return lc.LeagueConfig.load(league_config_id)


def ingest_mock_draft_file(conn: sqlite3.Connection, path: Path) -> IngestReport:
    """Validate and insert one mock-draft JSON file. Idempotent per mock_id
    (INSERT OR REPLACE) so re-ingesting the same file is safe."""
    ensure_tables(conn)
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    missing = [f for f in REQUIRED_DRAFT_FIELDS if f not in raw]
    if missing:
        raise MockDraftValidationError(f"{path}: missing required field(s) {missing}")

    mock_id = str(raw["mock_id"])
    league_config_id = str(raw["league_config_id"])
    try:
        cfg = _load_league_config(league_config_id)
    except FileNotFoundError:
        raise MockDraftValidationError(
            f"{path}: league_config_id={league_config_id!r} has no saved LeagueConfig"
        )
    conforms, conforms_note = format_conforms(cfg)
    picks = raw.get("picks", [])
    bot_seat_status, bot_seat_count = _bot_seat_status(picks)
    drafted_at = str(raw["drafted_at"])

    # ADR-054: frozen league-shape snapshot, taken from the LeagueConfig
    # resolved above -- never re-read live later, so a subsequent edit to the
    # saved config file cannot silently reinterpret an already-logged mock.
    starters_json = json.dumps(cfg.starters, sort_keys=True)
    flex_eligible_json = json.dumps(list(cfg.flex_eligible))
    scoring_json = json.dumps(cfg.scoring, sort_keys=True, default=str)
    cfg_hash = _league_config_hash(cfg)

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO mock_drafts "
        "(mock_id, league_config_id, platform, drafted_at, source, is_mock, "
        " format_conforms, format_conforms_note, bot_seat_status, bot_seat_count, ingested_at, "
        " teams, draft_type, user_draft_slot, starters_json, flex_slots, flex_eligible_json, "
        " bench, ir, scoring_json, league_config_hash) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (mock_id, league_config_id, str(raw["platform"]), drafted_at,
         raw.get("source"), int(bool(raw.get("is_mock", True))),
         int(conforms), conforms_note, bot_seat_status, bot_seat_count, now,
         cfg.teams, cfg.draft_type, cfg.user_draft_slot, starters_json, cfg.flex_slots,
         flex_eligible_json, cfg.bench, cfg.ir, scoring_json, cfg_hash),
    )
    conn.execute("DELETE FROM mock_picks WHERE mock_id=?", (mock_id,))
    conn.execute("DELETE FROM mock_pick_quarantine WHERE mock_id=?", (mock_id,))

    # Batch-build the normalized-name index once per file rather than
    # re-querying players_canonical per pick (a mock draft is ~150+ picks).
    name_index: Dict[str, List[str]] = {}
    for mfl_id, display_name in conn.execute(
        "SELECT mfl_id, display_name FROM players_canonical"
    ).fetchall():
        if display_name:
            name_index.setdefault(idn.normalize_name(display_name), []).append(mfl_id)
    known_mfl_ids = {r[0] for r in conn.execute("SELECT mfl_id FROM players_canonical")}

    resolved = 0
    quarantined = 0
    resolved_entries: List[dict] = []  # buffered; inserted after prediction replay below
    for p in picks:
        pick_missing = [f for f in REQUIRED_PICK_FIELDS if f not in p]
        if pick_missing:
            raise MockDraftValidationError(
                f"{path}: pick missing required field(s) {pick_missing}: {p}"
            )
        overall_pick = int(p["overall_pick"])
        mfl_id_supplied = p.get("mfl_id")
        name_raw = p.get("player_name_raw")

        mfl_id: Optional[str] = None
        method = "none"
        reason = None

        if mfl_id_supplied is not None:
            if str(mfl_id_supplied) in known_mfl_ids:
                mfl_id = str(mfl_id_supplied)
                method = "supplied_mfl_id"
            else:
                reason = f"supplied mfl_id {mfl_id_supplied!r} not found in players_canonical"
        if mfl_id is None and reason is None and name_raw:
            key = idn.normalize_name(name_raw)
            candidates = name_index.get(key, [])
            if len(candidates) == 1:
                mfl_id = candidates[0]
                method = "resolved_name"
            elif len(candidates) == 0:
                reason = f"no players_canonical match for {name_raw!r}"
            else:
                reason = f"ambiguous: {len(candidates)} players_canonical matches for {name_raw!r}"
        elif mfl_id is None and reason is None:
            reason = "neither mfl_id nor player_name_raw supplied"

        if mfl_id is None:
            quarantined += 1
            conn.execute(
                "INSERT OR REPLACE INTO mock_pick_quarantine "
                "(mock_id, overall_pick, player_name_raw, mfl_id_supplied, reason, quarantined_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (mock_id, overall_pick, name_raw,
                 str(mfl_id_supplied) if mfl_id_supplied is not None else None, reason, now),
            )
            resolved_entries.append({"overall_pick": overall_pick, "mfl_id": None})
            continue

        resolved += 1
        resolved_entries.append({
            "overall_pick": overall_pick, "mfl_id": mfl_id, "round": p.get("round"),
            "team_slot": p.get("team_slot"), "name_raw": name_raw,
            "source_predicted_top": p.get("predicted_top"),
            "source_predicted_p": p.get("predicted_p"),
            "timestamp": p.get("timestamp"), "drafter_type": p.get("drafter_type"),
            "method": method,
        })

    # ADR-054: replay every pick (in overall_pick order) through the D-3
    # baseline, board state built from the snapshot valid as of `drafted_at`
    # -- never the current/live board (CLAUDE.md SS6.1). A mock with ANY
    # quarantined pick, or with no valid as-of snapshot on file at all,
    # comes back with an all-None prediction list -- see
    # mock_prediction.compute_pick_predictions for why (the undrafted pool
    # cannot be trusted past an unresolved pick).
    resolved_entries.sort(key=lambda e: e["overall_pick"])
    season = int(drafted_at[:4])
    board_source, board_as_of_date, predictions = mpred.compute_pick_predictions(
        conn, [e["mfl_id"] for e in resolved_entries], season, drafted_at,
    )

    predictions_complete = (
        quarantined == 0
        and len(predictions) > 0
        and all(pred is not None for pred in predictions)
    )
    if quarantined > 0:
        predictions_note = (
            f"{quarantined} pick(s) quarantined (unresolved identity) -- the undrafted "
            "pool cannot be trusted past an unresolved pick, so no prediction snapshot "
            "was computed for this mock at all."
        )
    elif board_as_of_date is None:
        predictions_note = (
            f"no rankings snapshot on file at or before drafted_at={drafted_at!r} for "
            f"season {season} -- an honest gap (CLAUDE.md SS6.1: never fall back to the "
            "live/current board for a historical record), not computed."
        )
    else:
        predictions_note = (
            f"computed at ingest time from {board_source!r} as of {board_as_of_date} "
            f"(model_version={mpred.PREDICTION_MODEL_VERSION!r}), replayed pick-by-pick "
            "per mock_lab_store.predict_next_pick, reused rather than re-derived."
        )

    for entry, pred in zip(resolved_entries, predictions):
        if entry["mfl_id"] is None:
            continue  # quarantined; no mock_picks row
        if pred is not None:
            predicted_top = pred["predicted_top"]
            predicted_p = pred["predicted_p"]
            top5_json = json.dumps(pred["predicted_top5"])
            pick_board_as_of = pred["board_as_of_date"]
            prediction_source = "computed_at_ingest"
        else:
            # Fall back to whatever the source JSON supplied, if anything --
            # never fabricated, and predictions_complete is already False.
            predicted_top = entry["source_predicted_top"]
            predicted_p = entry["source_predicted_p"]
            top5_json = None
            pick_board_as_of = None
            prediction_source = (
                "source_supplied" if predicted_top is not None or predicted_p is not None
                else "missing"
            )
        conn.execute(
            "INSERT OR REPLACE INTO mock_picks "
            "(mock_id, overall_pick, round, team_slot, mfl_id, player_name_raw, "
            " predicted_top, predicted_p, timestamp, drafter_type, resolution_method, "
            " predicted_top5_json, prediction_source, board_as_of_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mock_id, entry["overall_pick"], entry.get("round"), entry.get("team_slot"),
             entry["mfl_id"], entry.get("name_raw"), predicted_top, predicted_p,
             entry.get("timestamp"), entry.get("drafter_type"), entry["method"],
             top5_json, prediction_source, pick_board_as_of),
        )

    usable, usable_note = calibration_usable(conforms, bot_seat_status, predictions_complete)
    conn.execute(
        "UPDATE mock_drafts SET predictions_model_version=?, predictions_board_source=?, "
        "predictions_board_as_of_date=?, predictions_complete=?, predictions_note=?, "
        "calibration_usable=?, calibration_usable_note=? WHERE mock_id=?",
        (mpred.PREDICTION_MODEL_VERSION, board_source, board_as_of_date,
         int(predictions_complete), predictions_note, int(usable), usable_note, mock_id),
    )

    conn.commit()
    return IngestReport(
        mock_id=mock_id, picks_total=len(picks), picks_resolved=resolved,
        picks_quarantined=quarantined, format_conforms=conforms,
        format_conforms_note=conforms_note,
    )


def main() -> None:
    import argparse

    import db as dbmod

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="JSON file for one completed mock draft")
    ap.add_argument("--db", type=Path, default=dbmod.DB_PATH)
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        report = ingest_mock_draft_file(conn, args.path)
    finally:
        conn.close()
    print(f"mock_id={report.mock_id}  "
          f"resolved={report.picks_resolved}/{report.picks_total}  "
          f"quarantined={report.picks_quarantined}  "
          f"format_conforms={report.format_conforms} ({report.format_conforms_note})")


if __name__ == "__main__":
    main()
