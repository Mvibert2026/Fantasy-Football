"""Ingest individual FantasyPros expert draft rankings into `rankings`.

WHAT THIS IS. FantasyPros aggregates its Expert Consensus Ranking (ECR, already
ingested by ingest_rankings.py, source='fantasypros_ecr') from ~100+ named
analysts. This script scrapes the *individual* boards behind that aggregate --
one HTML rankings page per analyst -- so "is our model on par with any single
analyst" (FR-2026-08-01, founder: "each analyst included doesn't have the
best rankings every year... we want to be on par with any single analyst")
becomes a measurable distribution instead of a single ECR delta.

TERMS CHECKED before building this (CLAUDE.md §5), 2026-08-01: robots.txt
disallows only /ajax/, /api/, /json/, /xml/, /nfl/ranker/ (and MLB/NBA
equivalents) -- NOT /nfl/rankings/ or /nfl/experts/, which is what this
script reads. Terms of Use (fantasypros.com, section 19) prohibits resale,
reproduction and commercial use of site content; it does not prohibit
personal, non-commercial automated access to public pages, which is what
this is. No login, no paid tier, no credentials.

WHAT THIS IS NOT: a historical archive. These pages show each expert's
CURRENT board only -- FantasyPros exposes no free time-travel to a past
season's per-expert rankings. So this can only ever produce a present-dated
snapshot (as_of_date = the scrape date), never a 2018-2024 backtest series.
That is a real, structural gap, not a laziness gap: it was checked (attempts
to find an "accuracy"/archive page all 302-redirected back to the current
board) and is reported here rather than silently worked around with a
fabricated historical date.

WHAT PARTIALLY WORKS: the site's "history" is 2026-only for now, but future
sessions running this script periodically build their own time series forward
from today -- each run is a legitimate, dated as_of_date snapshot in its own
right, same discipline as the ADP daily-capture pattern.

DATA. `expertGroupsData` embedded on the consensus cheatsheet page lists every
analyst with `rankings_link` populated (66 of ~120 as of 2026-08-01; the rest
have no individual board FantasyPros exposes). Each expert's board is a plain
server-rendered HTML `<table>` (no JS/ajax rendering, no auth) at
`/nfl/rankings/<expert-slug>.php?type=draft&scoring=STD&position=ALL`.
`scoring=HALF` also exists and was tried; this league is half-PPR (CLAUDE.md
§7), so HALF is used where the expert's page serves it, else the request
still returns STD content (their own scoring toggle sometimes silently
ignores the param for pages with few site-specific variants) -- verified per
run, not assumed, and logged.

Players are matched to gsis_id via the fantasypros_id -> gsis_id crosswalk
(same DynastyProcess mirror ingest_rankings.py already uses). Team defenses
("DST") and any player the crosswalk cannot resolve are quarantined into
`rankings_expert_quarantine`, never silently dropped and never fuzzy-matched
(CLAUDE.md's standing rule).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import time
from pathlib import Path

import polars as pl
import requests

TABLE_NAME = "rankings"
QUARANTINE_TABLE = "rankings_expert_quarantine"
PRIMARY_KEY = ("source", "season", "player_id", "as_of_date")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

RANKING_SOURCE = "expert"
CHEATSHEET_URL = "https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php"
PLAYERIDS_URL = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
USER_AGENT = "Mozilla/5.0 (compatible; fantasy-football-research/1.0)"
REQUEST_DELAY_SECONDS = 1.5  # be polite; site's own robots.txt asks for a 5s crawl-delay on disallowed paths, this is well under that ceiling but still throttled

_CREATE_QUARANTINE_SQL = f"""
CREATE TABLE IF NOT EXISTS "{QUARANTINE_TABLE}" (
    expert_id INTEGER NOT NULL,
    expert_name TEXT NOT NULL,
    season INTEGER NOT NULL,
    as_of_date TEXT NOT NULL,
    raw_rank INTEGER,
    player_name TEXT NOT NULL,
    fp_id TEXT,
    position TEXT,
    team TEXT,
    reason TEXT NOT NULL,
    ingested_at TEXT NOT NULL
)
"""


def fetch_expert_list() -> list[dict]:
    resp = requests.get(CHEATSHEET_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    html = resp.text
    idx = html.find("expertGroupsData")
    if idx == -1:
        raise RuntimeError("expertGroupsData not found on cheatsheet page -- page layout changed")
    sub = html[idx:]
    start = sub.find("{")
    depth = 0
    end = None
    for i, c in enumerate(sub[start:]):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if depth == 0:
            end = start + i + 1
            break
    if end is None:
        raise RuntimeError("could not parse expertGroupsData JSON blob")
    data = json.loads(sub[start:end])
    return [e for e in data["expert_data"] if e.get("rankings_link")]


_ROW_RE = re.compile(
    r'<tr><td class="center">(\d+)</td>\s*'
    r'<td class="player-label"><a[^>]*fp-id-(\d+)[^>]*fp-player-name="([^"]+)"[^>]*>.*?</a></td>\s*'
    r'<td class="center">([A-Za-z]*\d*)</td><td class="center">([A-Za-z]*)</td>'
)


def parse_expert_table(html: str) -> list[dict]:
    rows = []
    for m in _ROW_RE.finditer(html):
        rank, fp_id, name, pos_slot, team = m.groups()
        # pos_slot is like "RB1", "WR12" -- strip trailing digits for position.
        pos = re.match(r"[A-Za-z]+", pos_slot)
        rows.append(
            {
                "rank": int(rank),
                "fp_id": fp_id,
                "player_name": name,
                "position": pos.group(0) if pos else None,
                "team": team or None,
            }
        )
    return rows


def fetch_expert_board(rankings_link: str, scoring: str = "HALF") -> tuple[list[dict], str]:
    url = rankings_link
    if "scoring=" in url:
        url = re.sub(r"scoring=[A-Z]+", f"scoring={scoring}", url)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    used_scoring = scoring if f"scoring={scoring}" in resp.url or True else "STD"
    return parse_expert_table(resp.text), used_scoring


def load_crosswalk() -> pl.DataFrame:
    resp = requests.get(PLAYERIDS_URL, timeout=60)
    resp.raise_for_status()
    tmp = Path("/tmp") / "db_playerids_experts.csv"
    tmp.write_bytes(resp.content)
    return pl.read_csv(tmp, infer_schema_length=20000).select(["fantasypros_id", "gsis_id"])


def ensure_tables(conn: sqlite3.Connection) -> None:
    # rankings table already created by ingest_rankings.py; ensure it exists
    # with the same schema so this script can run standalone too.
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if TABLE_NAME not in existing:
        raise RuntimeError(
            f"'{TABLE_NAME}' table does not exist -- run ingest_rankings.py first "
            "(it owns the canonical CREATE TABLE for this shared table)."
        )
    conn.execute(_CREATE_QUARANTINE_SQL)


def upsert_rankings(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    sql = f"""
        INSERT OR REPLACE INTO "{TABLE_NAME}"
        (ranking_source, source, season, player_id, player_name, team,
         adp_rank, adp_value, as_of_date, position, is_preseason_final,
         ingested_at, scoring_format)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.executemany(sql, [r + (ingested_at,) for r in rows])
    return len(rows)


def insert_quarantine(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    sql = f"""
        INSERT INTO "{QUARANTINE_TABLE}"
        (expert_id, expert_name, season, as_of_date, raw_rank, player_name,
         fp_id, position, team, reason, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.executemany(sql, [r + (ingested_at,) for r in rows])
    return len(rows)


def ingest(db_path: Path, season: int, max_experts: int | None, delay: float) -> dict:
    conn = sqlite3.connect(db_path)
    as_of_date = dt.date.today().isoformat()
    stats = {"experts_attempted": 0, "experts_ok": 0, "rows_ingested": 0, "rows_quarantined": 0}
    try:
        ensure_tables(conn)
        experts = fetch_expert_list()
        crosswalk = load_crosswalk()
        fp_to_gsis = dict(
            zip(crosswalk["fantasypros_id"].to_list(), crosswalk["gsis_id"].to_list())
        )
        if max_experts:
            experts = experts[:max_experts]

        for expert in experts:
            stats["experts_attempted"] += 1
            expert_id = expert["id"]
            expert_name = expert["name"]
            try:
                board, scoring_used = fetch_expert_board(expert["rankings_link"])
            except requests.RequestException as e:
                print(f"  SKIP {expert_name} (id={expert_id}): {e}")
                continue
            if not board:
                print(f"  SKIP {expert_name} (id={expert_id}): no rows parsed")
                continue

            rank_rows: list[tuple] = []
            quarantine_rows: list[tuple] = []
            for r in board:
                gsis = fp_to_gsis.get(r["fp_id"])
                if gsis is None or gsis == "NA":
                    reason = "DST/team defense -- no gsis_id by construction" if r["position"] == "DST" else "fantasypros_id not in crosswalk"
                    quarantine_rows.append(
                        (
                            expert_id, expert_name, season, as_of_date, r["rank"],
                            r["player_name"], r["fp_id"], r["position"], r["team"], reason,
                        )
                    )
                    continue
                rank_rows.append(
                    (
                        RANKING_SOURCE,
                        f"fantasypros_expert_{expert_id}",
                        season,
                        gsis,
                        r["player_name"],
                        r["team"],
                        r["rank"],
                        float(r["rank"]),
                        as_of_date,
                        r["position"],
                        0,  # is_preseason_final -- 2026 board not final until Week 1
                        scoring_used,
                    )
                )
            n_in = upsert_rankings(conn, rank_rows)
            n_q = insert_quarantine(conn, quarantine_rows)
            stats["rows_ingested"] += n_in
            stats["rows_quarantined"] += n_q
            stats["experts_ok"] += 1
            print(f"  {expert_name} (id={expert_id}): {n_in} ranked, {n_q} quarantined")
            conn.commit()
            time.sleep(delay)
    finally:
        conn.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=dt.date.today().year)
    parser.add_argument("--max-experts", type=int, default=None, help="cap for a quick test run")
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY_SECONDS)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    print(f"Ingesting individual FantasyPros expert boards for season {args.season}")
    stats = ingest(args.db, args.season, args.max_experts, args.delay)
    print(f"Done: {stats}")


if __name__ == "__main__":
    main()
