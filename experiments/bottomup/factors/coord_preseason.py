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

WHERE THE PRESEASON NAME ACTUALLY LIVES -- measured, not assumed. The obvious
version of this (fetch the season article's pre-Week-1 revision and re-run the
`{{NFL final staff}}` parser) returns NOTHING: 32/32 team-seasons in a 2018 probe
had no such template, because "final staff" is a static block editors substitute
in AFTER the season. What the in-season article carries instead is a
`==Staff==` section transcluding the team's LIVE navbox, e.g.
`{{Chicago Bears staff}}` -- whose content is whatever it is today, not what it
was in 2018. So this module makes TWO dated reads: the article revision before
kickoff (to learn which navbox that season's article pointed at) and then that
NAVBOX PAGE's own revision before the same kickoff. Verified to work back to at
least 2013 (`Template:Kansas City Chiefs staff` @2013-08-05 -> Doug Pederson OC).

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
import re
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
    coach_id TEXT,                    -- the coordinator's name; NULL if the
                                      -- navbox listed no such role. NEVER a
                                      -- guess: "no OC line" usually means the
                                      -- head coach called plays, but that
                                      -- inference is left to the feature layer
                                      -- where it is visible and testable.
    head_coach TEXT,
    is_hc_calling INTEGER,
    as_of_date TEXT NOT NULL,         -- timestamp of the navbox revision read
    revid INTEGER,
    days_before_kickoff REAL,
    navbox TEXT,
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


def _cache_path(key: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", key)
    return RAW_DIR / f"{safe}.json"


def _revision_before(title: str, kickoff: str, refresh: bool = False
                     ) -> Optional[dict]:
    """The newest revision of `title` at or before midnight on `kickoff`.

    `rvstart` + `rvdir=older` is exactly "the page as a reader would have seen it
    the day before Week 1". Returns None if the page does not exist, and a dict
    with `wikitext=None` if it exists but had no revision that early.
    """
    # `redirects=1` matters and is not cosmetic. Four franchises renamed inside
    # the covered window (Redskins, Oakland Raiders, San Diego Chargers, St.
    # Louis Rams). Their season articles point at the PERIOD-CORRECT navbox
    # title, but that page was later MOVED, so the old title is now a redirect
    # with no revision before that season's kickoff -- 28 team-seasons came back
    # empty for exactly four clubs, which is a non-random hole, not noise.
    # Following the redirect reaches the moved page, whose history travelled with
    # it. Version-tagged in the cache key so the pre-redirect responses are not
    # silently reused.
    path = _cache_path(f"r2:{title}@{kickoff}")
    if path.exists() and not refresh:
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        params = urllib.parse.urlencode({
            "action": "query", "titles": title, "prop": "revisions",
            "rvprop": "content|timestamp|ids", "rvslots": "main",
            "rvlimit": 1, "rvdir": "older", "redirects": 1,
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


_STAFF_SECTION_RE = re.compile(
    r"==+\s*(?:Coaching\s+)?[Ss]taff\s*==+\s*\n+\s*\{\{([^}|\n]+?)\}\}")
_NAVBOX_GUESS_RE = re.compile(r"\{\{([A-Z][^}|\n]{2,60}? staff)\}\}")
_HC_LINE_RE = re.compile(r"\*\s*[^\n]*?\bhead coach\b[^\n]*?[–—-]\s*(.+)", re.I)


def _navbox_title(article_wikitext: str) -> Optional[str]:
    """Which live staff navbox that season's article pointed at.

    Read out of the article rather than constructed from the team code, so a
    franchise rename is handled by whatever the article itself said at the time
    instead of by a hardcoded mapping that would have to be maintained.
    """
    m = _STAFF_SECTION_RE.search(article_wikitext) or \
        _NAVBOX_GUESS_RE.search(article_wikitext)
    if not m:
        return None
    name = m.group(1).strip()
    if not name.lower().endswith("staff"):
        return None
    return name if name.lower().startswith("template:") else f"Template:{name}"


def parse_navbox_staff(wikitext: str) -> dict:
    """HC / OC / DC out of a team staff navbox. Any field None if absent --
    never fabricated. Reuses the coordinator regexes from the production
    ingester so the two sources cannot drift apart in what counts as an OC."""
    out = {}
    for key, pattern in (("head_coach", _HC_LINE_RE),
                         ("oc", W._OC_RE), ("dc", W._DC_RE)):
        m = pattern.search(wikitext)
        out[key] = W._clean_name(m.group(1)) if m else None
    return out


def ingest(seasons, teams=None, db_path: Path = DEFAULT_DB,
           refresh: bool = False) -> dict:
    teams = teams or W.TEAMS
    kicks = week1_dates(db_path)
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute(_CREATE_SQL)
    conn.execute(_QUAR_SQL)
    now = datetime.now(timezone.utc).isoformat()

    rows, quar = [], []
    stats = {"team_seasons": 0, "stored": 0, "oc_missing": 0, "dc_missing": 0,
             "no_page": 0, "no_navbox_link": 0, "no_navbox_page": 0,
             "no_revision_before_kickoff": 0}
    for season in seasons:
        kickoff = kicks.get(season)
        if not kickoff:
            quar.append(("*", season, "no_week1_date_in_schedules", now))
            continue
        for team in teams:
            stats["team_seasons"] += 1
            try:
                title = f"{season} {W._team_article_name(team, season)} season"
            except KeyError as e:
                quar.append((team, season, str(e), now))
                continue
            art = _revision_before(title, kickoff, refresh=refresh)
            if art is None:
                quar.append((team, season, "wikipedia_article_not_found", now))
                stats["no_page"] += 1
                continue
            if not art.get("wikitext"):
                quar.append((team, season, "no_article_revision_before_kickoff", now))
                stats["no_revision_before_kickoff"] += 1
                continue
            nav = _navbox_title(art["wikitext"])
            if not nav:
                quar.append((team, season, "no_staff_navbox_in_preseason_article", now))
                stats["no_navbox_link"] += 1
                continue
            navrev = _revision_before(nav, kickoff, refresh=refresh)
            if navrev is None:
                quar.append((team, season, f"navbox_page_missing:{nav}", now))
                stats["no_navbox_page"] += 1
                continue
            if not navrev.get("wikitext"):
                quar.append((team, season, f"no_navbox_revision_before_kickoff:{nav}", now))
                stats["no_revision_before_kickoff"] += 1
                continue
            parsed = parse_navbox_staff(navrev["wikitext"])
            ts = navrev["timestamp"]
            try:
                days = (datetime.fromisoformat(f"{kickoff}T00:00:00+00:00")
                        - datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        ).total_seconds() / 86400
            except Exception:
                days = None
            hc = parsed["head_coach"]
            for role, name in (("OC", parsed["oc"]), ("DC", parsed["dc"])):
                if name is None:
                    stats[f"{role.lower()}_missing"] += 1
                    quar.append((team, season,
                                 f"no_{role.lower()}_line_in_preseason_navbox", now))
                rows.append((team, season, role, name, hc,
                             1 if (hc and role == "OC" and name and hc == name) else 0,
                             ts, navrev.get("revid"), days, nav,
                             "wikipedia:team staff navbox @pre-week1 revision",
                             "medium" if name else "low", now))
                if name:
                    stats["stored"] += 1

    conn.executemany(
        f'INSERT OR REPLACE INTO "{TABLE}" (team, season, title, coach_id, head_coach, '
        "is_hc_calling, as_of_date, revid, days_before_kickoff, navbox, source, "
        "confidence, retrieved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
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
