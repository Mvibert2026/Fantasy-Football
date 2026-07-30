#!/usr/bin/env python
"""Preseason coordinator identity, recovered from Wikipedia REVISION HISTORY.

WHY THIS EXISTS. `src/ingest_coordinators_wikipedia.py` stores the
`{{NFL final staff}}` template as it reads TODAY, which names whoever held the
OC/DC role at the END of that season. `docs/handoffs/101-*` flagged that as a
look-ahead hazard for test-registry #29/#30 and handed the fix to a later
session without building it. This module builds option 2 from that thread:
fetch the article revision closest BEFORE that season's Week-1 kickoff and parse
the same template out of it, so the stored name is who was calling the offence
going INTO the season.

WHAT THIS BUYS, CONCRETELY. In any season with a mid-year coordinator firing the
final-staff row names the REPLACEMENT. A "did the OC change?" feature built from
final-staff rows therefore reads "changed" for a team that entered the season
with continuity and fired its OC in November -- and that firing is caused by the
season going badly, which is exactly the direction that manufactures fake signal.
Reading the pre-Week-1 revision removes that channel entirely.

WHAT IS STILL A PROXY, NAMED. The revision timestamp is the honest `as_of`, and
it is a few days before Week 1 -- i.e. after a late-August fantasy draft, not
before it. Coordinator hires are January-March events, so the practical risk is
small, but it is not zero and the `as_of_date` on every row states the truth
rather than a date that would be convenient. Nothing is backdated.

RESEARCH-GRADE, NOT PRODUCTION. This writes a JSON cache under
`data/raw/wikipedia-preseason/` and a research table `play_callers_preseason`.
Productionising it into `src/` and the rebuild script is data-ops' call, not
this module's -- see the thread this session opens.

LICENCE. Wikipedia content is CC BY-SA 4.0; fetch and display both permitted with
attribution and share-alike (`docs/research/missing-inputs-sourcing-2026-07-29.md`
SS3.3). Identifying User-Agent, >=0.5s between requests, every response cached so
a re-run never re-fetches.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import ingest_coordinators_wikipedia as W  # noqa: E402

RAW_DIR = REPO / "data" / "raw" / "wikipedia-preseason"
DEFAULT_DB = REPO / "data" / "nfl.db"
TABLE = "play_callers_preseason"

_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS "{TABLE}" (
    team TEXT NOT NULL,
    season INTEGER NOT NULL,
    title TEXT NOT NULL,              -- OC | DC
    coach_id TEXT,                    -- the coordinator's name; see docstring
    head_coach TEXT,
    is_hc_calling INTEGER,
    as_of_date TEXT NOT NULL,         -- timestamp of the Wikipedia revision read
    revid INTEGER,
    days_before_kickoff REAL,
    source TEXT NOT NULL,
    confidence TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    PRIMARY KEY (team, season, title)
)
"""

_QUAR_SQL = """
CREATE TABLE IF NOT EXISTS "play_callers_preseason_quarantine" (
    team TEXT, season INTEGER, reason TEXT, retrieved_at TEXT
)
"""


def week1_dates(db_path: Path = DEFAULT_DB) -> dict:
    """Season -> earliest REG gameday, straight from this repo's own schedules."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT season, MIN(gameday) FROM schedules WHERE game_type='REG' "
            "AND gameday IS NOT NULL GROUP BY season"
        ).fetchall()
    finally:
        conn.close()
    return {int(s): d for s, d in rows if d}


def _cache_path(team: str, season: int) -> Path:
    return RAW_DIR / f"{team}-{season}.json"


def _fetch_preseason_wikitext(team: str, season: int, kickoff: str,
                              refresh: bool = False) -> Optional[dict]:
    """Revision content as of the day before `kickoff`. None if no such page.

    `rvstart` + `rvdir=older` asks the API for the newest revision at or before
    that instant, which is precisely "the article as a reader would have seen it
    the day before Week 1".
    """
    path = _cache_path(team, season)
    if path.exists() and not refresh:
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        title = f"{season} {W._team_article_name(team, season)} season"
        params = urllib.parse.urlencode({
            "action": "query", "titles": title, "prop": "revisions",
            "rvprop": "content|timestamp|ids", "rvslots": "main",
            "rvlimit": 1, "rvdir": "older",
            "rvstart": f"{kickoff}T00:00:00Z",
            "format": "json", "formatversion": "2",
        })
        req = urllib.request.Request(f"{W.API_URL}?{params}",
                                     headers={"User-Agent": W.USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        time.sleep(0.5)
    pages = payload.get("query", {}).get("pages", [])
    if isinstance(pages, dict):                      # formatversion=1 fallback
        pages = list(pages.values())
    for p in pages:
        if p.get("missing"):
            return None
        revs = p.get("revisions")
        if not revs:
            return {"wikitext": None, "timestamp": None, "revid": None}
        r = revs[0]
        slots = r.get("slots", {}).get("main", {})
        return {"wikitext": slots.get("content") or slots.get("*"),
                "timestamp": r.get("timestamp"), "revid": r.get("revid")}
    return None


def ingest(seasons, teams=None, db_path: Path = DEFAULT_DB,
           refresh: bool = False) -> dict:
    teams = teams or W.TEAMS
    kicks = week1_dates(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(_CREATE_SQL)
    conn.execute(_QUAR_SQL)
    now = datetime.now(timezone.utc).isoformat()

    rows, quar = [], []
    stats = {"stored": 0, "quarantined": 0, "no_page": 0, "no_template": 0,
             "no_revision_before_kickoff": 0}
    for season in seasons:
        kickoff = kicks.get(season)
        if not kickoff:
            quar.append(("*", season, "no_week1_date_in_schedules", now))
            stats["quarantined"] += 1
            continue
        for team in teams:
            try:
                got = _fetch_preseason_wikitext(team, season, kickoff, refresh=refresh)
            except KeyError as e:
                quar.append((team, season, str(e), now))
                stats["quarantined"] += 1
                continue
            if got is None:
                quar.append((team, season, "wikipedia_article_not_found", now))
                stats["no_page"] += 1
                stats["quarantined"] += 1
                continue
            if not got.get("wikitext"):
                quar.append((team, season, "no_revision_before_kickoff", now))
                stats["no_revision_before_kickoff"] += 1
                stats["quarantined"] += 1
                continue
            parsed = W.parse_staff(got["wikitext"])
            if not parsed["template_found"]:
                quar.append((team, season, "no_final_staff_template_in_preseason_revision", now))
                stats["no_template"] += 1
                stats["quarantined"] += 1
                continue
            ts = got["timestamp"]
            try:
                days = (datetime.fromisoformat(f"{kickoff}T00:00:00+00:00")
                        - datetime.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds() / 86400
            except Exception:
                days = None
            hc = parsed["head_coach"]
            for role, name in (("OC", parsed["oc"]), ("DC", parsed["dc"])):
                if name is None:
                    quar.append((team, season, f"no_{role.lower()}_field_in_preseason_revision", now))
                    stats["quarantined"] += 1
                    continue
                rows.append((team, season, role, name, hc,
                             1 if (hc and role == "OC" and hc == name) else 0,
                             ts, got.get("revid"), days,
                             "wikipedia:NFL final staff @preseason-revision",
                             "medium", now))
                stats["stored"] += 1

    conn.executemany(
        f'INSERT OR REPLACE INTO "{TABLE}" (team, season, title, coach_id, head_coach, '
        "is_hc_calling, as_of_date, revid, days_before_kickoff, source, confidence, "
        "retrieved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.executemany(
        'INSERT INTO "play_callers_preseason_quarantine" '
        "(team, season, reason, retrieved_at) VALUES (?,?,?,?)", quar)
    conn.commit()
    conn.close()
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start-season", type=int, default=2010)
    ap.add_argument("--end-season", type=int, default=2025)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    s = ingest(range(a.start_season, a.end_season + 1), db_path=a.db, refresh=a.refresh)
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
