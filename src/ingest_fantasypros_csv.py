"""Ingest the founder-supplied FantasyPros "ALL Rankings" CSV export into `rankings`.

WHAT THIS IS. A one-off, founder-downloaded, browser-side FantasyPros export
(not the live API, which caps at 10 players/response -- see docs/deferred.md
"FantasyPros API -- probed 2026-07-25" and src/ingest_rankings.py's header).
This file has no row cap (575 players) and is confirmed **Half PPR** (the
founder had that scoring format selected on FantasyPros' site at export time,
per handoff 053's PM reply, 2026-07-27). That fixes the two defects of the
existing `fantasypros_ecr` mirror: the 10-row cap does not apply here (moot,
this isn't the live API) and the scoring format is finally known rather than
unscored/DynastyProcess-mirror-ambiguous.

This is a DIFFERENT, BETTER source than `fantasypros_ecr` and is stored under
a different `source` value (`fantasypros_csv_2026draft`) so both can coexist
during the transition; nothing here overwrites or deletes the existing rows.

ADP RECOVERY. The CSV does not carry raw ADP, only `RK` (ECR) and
`ECR VS. ADP` (a signed integer delta, or "-" when absent -- 566/575 populated
in this pull). Sign convention was NOT documented by FantasyPros in the
export; it was inferred here by cross-checking overlapping players against
`data/raw/founder-export/2026-07-27/underdog-adp.csv` (Underdog best-ball
ADP, a same-day founder pull, file 1 of handoff 053):

    Player                RK   delta   ADP=RK+delta   Underdog rank (actual)
    Amon-Ra St. Brown      6    +2      8              7   (later than RK -- direction matches)
    CeeDee Lamb            8    +2     10              9   (later than RK -- direction matches)
    Jonathan Taylor        9    -2      7              8   (earlier than RK -- direction matches)
    Jaxon Smith-Njigba     5    +1      6              5   (~flat -- small delta, noise)

Underdog is a different platform/pool so exact numbers never match, but the
*direction* is consistent in 3/4 non-trivial cases: positive delta means the
player is being drafted LATER than their ECR (ADP number bigger/worse than
RK), negative means EARLIER (being drafted ahead of consensus rank). That
fixes the sign as `ADP = RK + delta`. This is inference from a same-day
external file, not a documented FantasyPros convention -- flag accordingly
if it ever needs re-verification against a cleaner source.

QUARANTINE. Player-name resolution to gsis_id goes through nflreadpy's
ff_playerids crosswalk (name/position match, same crosswalk src/ingest_rankings.py
uses for the DynastyProcess mirror). Two failure modes both quarantine to
`rankings_quarantine`, never silently drop and never fuzzy-guess:
  - DST rows: no individual gsis_id exists by construction (team defenses
    aren't players in the crosswalk). Same permanent, by-design gap
    src/ingest_rankings.py documents for the DynastyProcess mirror.
  - Name/position combinations not found in the crosswalk at all (retired
    players, practice-squad names the crosswalk hasn't picked up, etc).

IGNORED COLUMNS. `UPSIDE`/`BUST` are placeholder strings ("Coach Upside
rating", "Coach Bust rating") in every row of this export -- no real values
were included. Not parsed, not stored (handoff 053 explicit instruction).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sqlite3
from pathlib import Path

import nflreadpy as nfl
import pandas as pd
from nflreadpy.config import update_config

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

EXPORT_ROOT = Path(__file__).resolve().parent.parent / "data" / "raw" / "founder-export"
_FALLBACK_EXPORT_DATE = "2026-07-27"

# This league is half-PPR (CLAUDE.md §7), so the half-PPR export is the one that
# may be ingested. Tried in order: the explicit half-PPR name first, then the
# legacy unsuffixed name the 2026-07-27 export used.
#
# The suffix is not cosmetic. FantasyPros does NOT record the scoring format
# inside the file -- the header row is identical across all three -- so before
# 2026-07-30 nothing could detect a wrong selection on their site, and the board
# would have ranked on the wrong scoring with no symptom. Encoding the format in
# the filename is what makes it checkable at all. See `assert_half_ppr_ordering`.
EXPORT_FILENAMES = (
    "FantasyPros_2026_Draft_ALL_Rankings_half_ppr.csv",
    "FantasyPros_2026_Draft_ALL_Rankings.csv",
)
EXPORT_FILENAME = EXPORT_FILENAMES[-1]  # legacy name, kept for callers that import it


CROSSWALK_CACHE = (
    Path(__file__).resolve().parent.parent / "data" / "raw" / "crosswalk" / "db_playerids.csv"
)


_NULL_GSIS_SENTINELS = {"", "NA", "N/A", "NULL", "NONE", "NAN"}


def _real_gsis_id(value: object) -> bool:
    """True only for a genuine gsis_id, not the crosswalk's missing-value sentinel.

    **This exists because of a bug that produced silent, wrong data.** The
    DynastyProcess CSV writes the R idiom `NA` for a missing `gsis_id`. Polars
    parses that to null, so the original `nflreadpy` path dropped those rows.
    `csv.DictReader` returns the literal string `"NA"`, which is truthy — so a
    plain `if r["gsis_id"]` kept every id-less player and mapped them all to one
    shared fake id of `"NA"`.

    The `rankings` primary key is `(source, season, player_id, as_of_date)` and
    the insert is `INSERT OR REPLACE`, so **62 rookies collapsed onto a single
    row, each silently overwriting the last.** Nothing failed: the ingest
    reported 555 rows and the table held 493. The survivor carried another
    player's rank.

    These players have no gsis_id and belong in `rankings_quarantine`, which is
    exactly where the crosswalk miss now sends them — visible, counted, and never
    guessed at.
    """
    return str(value).strip().upper() not in _NULL_GSIS_SENTINELS


def _load_ff_playerids() -> list[tuple[str, str, str]]:
    """(name, position, gsis_id) triples from the DynastyProcess player-id crosswalk.

    Prefers a committed local copy over the network.

    **Why.** `nflreadpy.load_ff_playerids()` fetches
    `github.com/dynastyprocess/data/raw/master/files/db_playerids.csv`, and that
    URL returns **HTTP 403 from this environment** -- the same block that has kept
    `fantasypros_ecr` stale since 2026-07-24. The redirect target,
    `raw.githubusercontent.com/...`, returns 200, so the data is reachable; only
    the `github.com/.../raw/` path is refused.

    Rather than depend on which of two hostnames is unblocked on a given day, the
    file is cached under `data/raw/crosswalk/`. Refresh it with:

        curl -L -o data/raw/crosswalk/db_playerids.csv \\
          https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv

    Falls back to the network path when no cache exists, so nothing that worked
    before stops working.
    """
    if CROSSWALK_CACHE.is_file():
        import csv as _csv

        with CROSSWALK_CACHE.open(newline="", encoding="utf-8-sig") as fh:
            return [
                (r["name"], r["position"], r["gsis_id"])
                for r in _csv.DictReader(fh)
                if _real_gsis_id(r.get("gsis_id"))
            ]

    ids = nfl.load_ff_playerids().select(["name", "position", "gsis_id"])
    ids = ids.filter(ids["gsis_id"].is_not_null())
    return list(ids.iter_rows())


SIBLING_FILENAMES = {
    "ppr": "FantasyPros_2026_Draft_ALL_Rankings_ppr.csv",
    "standard": "FantasyPros_2026_Draft_ALL_Rankings_standard.csv",
}


def _mean_wr_rank_gap(csv_path: Path) -> float:
    """Mean rank of WRs minus mean rank of RBs, over the top 50 of a FantasyPros export.

    Lower (more negative) means receivers are ranked ahead of backs. This is the
    quantity scoring format moves: a reception is worth 1 point in PPR, 0.5 in
    half, 0 in standard, and receivers catch far more passes than backs do.
    """
    import csv as _csv

    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(_csv.DictReader(fh))[:50]
    ranks = {"WR": [], "RB": []}
    for row in rows:
        pos = (row.get("POS") or "")[:2].upper()
        if pos in ranks:
            try:
                ranks[pos].append(int(str(row["RK"]).strip().strip('"')))
            except (ValueError, KeyError):
                continue
    if not ranks["WR"] or not ranks["RB"]:
        raise ValueError(f"{csv_path.name}: no WR or no RB in the top 50")
    return sum(ranks["WR"]) / len(ranks["WR"]) - sum(ranks["RB"]) / len(ranks["RB"])


def assert_half_ppr_ordering(csv_path: Path) -> str:
    """Verify the file named half-PPR actually behaves like half-PPR.

    **The gap this closes.** FantasyPros does not record the scoring format inside
    the export -- all three formats produce a byte-identical header row. Until
    2026-07-30 only one format was ever supplied, so a wrong selection on their
    site was undetectable and would have ranked the whole board on the wrong
    scoring with no symptom at all. This module's header flagged that as the one
    thing no code could check.

    With all three formats present it becomes checkable, because scoring format
    has a *direction*: receptions are worth 1 / 0.5 / 0 point in PPR / half /
    standard, and receivers catch far more passes than backs. So the WR-minus-RB
    mean-rank gap must be most negative in PPR and least negative in standard,
    with half-PPR strictly between.

    Returns a human-readable summary. Raises ValueError if the ordering is wrong,
    which means the founder selected the wrong format for at least one export.

    Skips silently (returning a note) when the sibling formats are absent -- the
    2026-07-27 export predates this and has only one file. An unverifiable claim
    is reported as unverifiable, never as verified.
    """
    siblings = {k: csv_path.parent / v for k, v in SIBLING_FILENAMES.items()}
    missing = [k for k, p in siblings.items() if not p.is_file()]
    if missing:
        return f"scoring-format check SKIPPED -- no {', '.join(missing)} sibling to compare against"

    half = _mean_wr_rank_gap(csv_path)
    ppr = _mean_wr_rank_gap(siblings["ppr"])
    std = _mean_wr_rank_gap(siblings["standard"])

    if not (ppr < half < std):
        raise ValueError(
            "FantasyPros scoring-format check FAILED -- the file named half-PPR does not "
            "sit between the PPR and standard exports.\n"
            f"  WR-minus-RB mean rank gap (top 50):  ppr={ppr:+.2f}  half={half:+.2f}  std={std:+.2f}\n"
            "  Expected ppr < half < standard. At least one export was taken with the "
            "wrong scoring selected on FantasyPros' site. Re-export before ingesting; "
            "ingesting this would rank the board on the wrong scoring with no other symptom."
        )
    return f"scoring-format check PASSED -- ppr={ppr:+.2f} < half={half:+.2f} < standard={std:+.2f}"


def latest_export_csv(root: Path = EXPORT_ROOT) -> Path:
    """Newest dated founder export containing the FantasyPros rankings CSV.

    The founder re-exports this by hand from FantasyPros' site (there is no API
    path -- see this module's header). Each export lands in its own
    `data/raw/founder-export/YYYY-MM-DD/` directory, so a hardcoded default goes
    stale the moment he supplies a fresher one, silently ingesting the old file.
    Resolving to the newest directory makes a re-export a drop-in: put the file
    in a new dated folder, run the script, no flag.

    Directory names must be ISO dates so lexical sort is chronological; anything
    else is ignored rather than guessed at. Falls back to the 2026-07-27 export
    when nothing matches, which keeps the historical default reproducible.
    """
    dated = sorted(
        d for d in root.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]")
        if d.is_dir() and any((d / name).is_file() for name in EXPORT_FILENAMES)
    )
    if dated:
        newest = dated[-1]
        return next(newest / n for n in EXPORT_FILENAMES if (newest / n).is_file())
    return root / _FALLBACK_EXPORT_DATE / EXPORT_FILENAME


DEFAULT_CSV_PATH = latest_export_csv()

SOURCE = "fantasypros_csv_2026draft"
RANKING_SOURCE = "expert"
SCORING_FORMAT = "half_ppr"
SEASON = 2026
AS_OF_DATE = "2026-07-27"  # legacy default; real value comes from as_of_date_for()
IS_PRESEASON_FINAL = 0  # current board is preseason but not final; late-Aug re-pull pending

_EXPORT_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def as_of_date_for(csv_path: Path) -> str:
    """The export's own date, taken from its `YYYY-MM-DD/` directory name.

    **This was a hardcoded constant and it caused a real corruption.** On
    2026-07-30 the founder supplied a fresh export; the ingest read the new file
    and stamped every row `2026-07-27`, silently merging two different exports
    under one `as_of_date`. Nothing failed and nothing warned -- the row count
    simply grew from 538 to 570, which looks like a successful ingest.

    That is precisely the look-ahead-adjacent failure CLAUDE.md §6.1 exists to
    prevent: `as_of_date` is the field the whole pipeline trusts to know *when*
    something was true, and a wrong one is worse than a missing one.

    The directory name is the export date by construction -- `README.md` in
    `data/raw/founder-export/` instructs the founder to create it as today's
    date. Falls back to the legacy constant only when the path carries no ISO
    date, so an ad-hoc `--csv` outside the export tree still works.
    """
    parent = csv_path.resolve().parent.name
    return parent if _EXPORT_DATE_RE.match(parent) else AS_OF_DATE

_NEW_COLUMNS = {
    "scoring_format": "TEXT",
    "tier": "INTEGER",
    "bye_week": "INTEGER",
    "sos_season": "INTEGER",
}

_QUARANTINE_SQL = """
CREATE TABLE IF NOT EXISTS rankings_quarantine (
    source TEXT NOT NULL,
    season INTEGER NOT NULL,
    as_of_date TEXT NOT NULL,
    rk INTEGER,
    player_name_raw TEXT,
    team TEXT,
    position TEXT,
    reason TEXT NOT NULL,
    quarantined_at TEXT NOT NULL,
    PRIMARY KEY (source, season, as_of_date, rk)
)
"""


def _strip_pos_rank(pos: str) -> str:
    """'RB1' -> 'RB', 'TE89' -> 'TE'."""
    return re.sub(r"\d+$", "", str(pos).strip())


def _parse_sos(val: str) -> int | None:
    if not isinstance(val, str):
        return None
    m = re.match(r"(\d+)\s+out of 5 stars", val.strip())
    return int(m.group(1)) if m else None


def _parse_int_or_none(val) -> int | None:
    s = str(val).strip()
    if s in ("", "-", "nan"):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _normalize_name(name: str) -> str:
    s = name.lower()
    s = s.replace("'", "").replace(".", "")
    s = re.sub(r"\s+(jr|sr|ii|iii|iv|v)\.?$", "", s)
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["position"] = df["POS"].map(_strip_pos_rank)
    df["sos_season"] = df["SOS SEASON"].map(_parse_sos)
    df["bye_week"] = df["BYE WEEK"].map(_parse_int_or_none)
    df["delta"] = df["ECR VS. ADP"].map(
        lambda v: _parse_int_or_none(str(v).replace("+", "")) if str(v).strip() not in ("-", "") else None
    )
    df["adp_value"] = df.apply(
        lambda r: (r["RK"] + r["delta"]) if pd.notna(r["delta"]) else None, axis=1
    )
    df["norm_name"] = df["PLAYER NAME"].map(_normalize_name)
    return df


# Known nickname/legal-name mismatches that appear in NEITHER nflreadpy's
# ff_playerids crosswalk NOR load_players()'s display_name/football_name/
# common_first_name fields. Not fuzzy matching -- a short, explicit,
# hand-verified alias table, each entry checked against a public source
# before being added here. Every use is logged at ingest time (see ingest()).
# key: (normalized_alias_name, position) -> normalized_real_name
_KNOWN_ALIASES: dict[tuple[str, str], str] = {
    # Marquise "Hollywood" Brown -- self-adopted nickname (jersey/media name),
    # not present in nflreadpy's name fields under any spelling checked
    # 2026-07-27 (display_name, football_name, common_first_name all say
    # "Marquise"). Verified against public reporting, not guessed.
    ("hollywood brown", "WR"): "marquise brown",
}


def build_crosswalk() -> dict[tuple[str, str], str]:
    """(normalized_name, position) -> gsis_id.

    Two sources, merged with nflreadpy's static `ff_playerids` snapshot taking
    priority (it's the longer-established, more heavily cross-referenced
    source). `load_players()` is layered on top as a supplement: it is
    refreshed more frequently and, as of 2026-07-27, already carries gsis_ids
    for 2026 draft-class rookies that ff_playerids' static snapshot does not
    (e.g. Jeremiyah Love, Carnell Tate, Jordyn Tyson -- confirmed present in
    load_players() with real gsis_ids, absent from ff_playerids). Kickers are
    normalized to "PK" to match ff_playerids' label convention (see the K/PK
    comment in ingest()); load_players() itself uses "K" natively, so entries
    are added under both keys where the position is "K".

    Each player's `football_name` (nickname/short form, e.g. "Mitch" for
    "Mitchell Tinsley") is also indexed against the same gsis_id, since some
    rankings exports use the short form rather than the legal first name.
    This is exact-match against a real nflverse-supplied field, not fuzzy
    matching.
    """
    update_config(cache_mode="filesystem")

    lookup: dict[tuple[str, str], str] = {}

    ids = _load_ff_playerids()
    for name, position, gsis_id in ids:
        lookup.setdefault((_normalize_name(name), position), gsis_id)

    players = nfl.load_players().select(
        ["display_name", "football_name", "last_name", "position", "gsis_id"]
    )
    players = players.filter(players["gsis_id"].is_not_null())
    for display_name, football_name, last_name, position, gsis_id in players.iter_rows():
        position_keys = {position}
        if position == "K":
            position_keys.add("PK")
        for pos_key in position_keys:
            if display_name:
                lookup.setdefault((_normalize_name(display_name), pos_key), gsis_id)
            if football_name and last_name:
                nickname_full = f"{football_name} {last_name}"
                lookup.setdefault((_normalize_name(nickname_full), pos_key), gsis_id)

    return lookup


def ensure_schema(conn: sqlite3.Connection) -> None:
    existing = {r[1] for r in conn.execute('PRAGMA table_info("rankings")')}
    for col, coltype in _NEW_COLUMNS.items():
        if col not in existing:
            conn.execute(f'ALTER TABLE "rankings" ADD COLUMN {col} {coltype}')
    conn.execute(_QUARANTINE_SQL)


def ingest(csv_path: Path, db_path: Path) -> dict:
    df = load_csv(csv_path)
    crosswalk = build_crosswalk()
    as_of = as_of_date_for(csv_path)

    conn = sqlite3.connect(db_path)
    ensure_schema(conn)
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()

    n_rows = 0
    quarantined: list[tuple] = []
    for _, r in df.iterrows():
        # nflreadpy's crosswalk labels kickers "PK", this export labels them "K" --
        # a known, documented label difference, not a guess.
        lookup_pos = "PK" if r["position"] == "K" else r["position"]
        gsis_id = crosswalk.get((r["norm_name"], lookup_pos))
        if gsis_id is None:
            alias_key = (r["norm_name"], r["position"])
            aliased_name = _KNOWN_ALIASES.get(alias_key)
            if aliased_name is not None:
                gsis_id = crosswalk.get((aliased_name, lookup_pos))
                if gsis_id is not None:
                    print(
                        f"  [alias] {r['PLAYER NAME']!r} ({r['position']}) -> "
                        f"{aliased_name!r} via _KNOWN_ALIASES -> gsis_id={gsis_id}"
                    )
        if gsis_id is None:
            reason = (
                "DST has no individual gsis_id (by design, per crosswalk structure)"
                if r["position"] == "DST"
                else "name/position not found in nflreadpy ff_playerids crosswalk"
            )
            quarantined.append(
                (
                    SOURCE,
                    SEASON,
                    as_of,
                    int(r["RK"]),
                    r["PLAYER NAME"],
                    r["TEAM"],
                    r["position"],
                    reason,
                    ingested_at,
                )
            )
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO rankings
                (ranking_source, source, season, player_id, player_name, team,
                 adp_rank, adp_value, spread_sd, rank_best, rank_worst,
                 as_of_date, position, is_preseason_final, ingested_at,
                 scoring_format, tier, bye_week, sos_season)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                RANKING_SOURCE,
                SOURCE,
                SEASON,
                gsis_id,
                r["PLAYER NAME"],
                r["TEAM"],
                int(r["RK"]),
                float(r["adp_value"]) if pd.notna(r["adp_value"]) else None,
                None,
                None,
                None,
                as_of,
                r["position"],
                IS_PRESEASON_FINAL,
                ingested_at,
                SCORING_FORMAT,
                int(r["TIERS"]) if pd.notna(r["TIERS"]) else None,
                r["bye_week"],
                r["sos_season"],
            ),
        )
        n_rows += 1

    conn.execute(
        "DELETE FROM rankings_quarantine WHERE source = ? AND season = ? AND as_of_date = ?",
        (SOURCE, SEASON, as_of),
    )
    conn.executemany(
        """
        INSERT OR REPLACE INTO rankings_quarantine
            (source, season, as_of_date, rk, player_name_raw, team, position, reason, quarantined_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        quarantined,
    )
    conn.commit()
    conn.close()

    return {
        "rows_ingested": n_rows,
        "rows_quarantined": len(quarantined),
        "quarantine_detail": quarantined,
        "total_csv_rows": len(df),
        "delta_populated": int(df["delta"].notna().sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument(
        "--skip-scoring-check",
        action="store_true",
        help="ingest even if the half-PPR ordering check fails (you almost certainly do not want this)",
    )
    args = parser.parse_args()

    # Runs BEFORE the ingest, deliberately. A wrong-scoring export produces no
    # symptom downstream -- the row count is right, every name resolves, and the
    # board is simply ranked on rules that are not this league's.
    print(f"Source: {args.csv.parent.name}/{args.csv.name}")
    try:
        print(assert_half_ppr_ordering(args.csv))
    except ValueError as exc:
        if not args.skip_scoring_check:
            raise SystemExit(f"\n{exc}\n\nRefusing to ingest. Pass --skip-scoring-check to override.")
        print(f"WARNING, overridden by --skip-scoring-check:\n{exc}")

    result = ingest(args.csv, args.db)
    print(f"Ingested: {result['rows_ingested']} / {result['total_csv_rows']} rows")
    print(f"Quarantined: {result['rows_quarantined']}")
    for row in result["quarantine_detail"]:
        print(f"  RK={row[3]} {row[4]!r} ({row[5]}, {row[6]}) -- {row[7]}")
    print(f"ECR vs ADP delta populated: {result['delta_populated']} / {result['total_csv_rows']}")


if __name__ == "__main__":
    main()
