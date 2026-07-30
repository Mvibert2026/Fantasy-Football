"""
Coordinator (OC/DC) history ingester, sourced from Wikipedia's `{{NFL final
staff}}` template on team-season articles — FR-087-adjacent gap 2, 2026-07-30.

WHY WIKIPEDIA. CLAUDE.md SS5 names Pro Football Reference "or equivalent" for
coach/coordinator history and requires verifying terms before building.
Re-verified this session (2026-07-30): PFR's `robots.txt` and
`sports-reference.com/data_use.html` both return HTTP 403 -- unreadable
programmatically, so the conservative default applies and PFR stays blocked,
matching the prior finding in `docs/research/missing-inputs-sourcing-2026-07-29.md`
SS3.1 and `docs/data-availability.md` SS7.9. That doc independently found and
verified Wikipedia's `Template:NFL final staff` as an alternative: transcluded
on 1,062+ team-season articles, CC BY-SA 4.0 (fetch AND display permitted,
with attribution and share-alike -- a better licence position than any other
source this project holds). This module builds the ingester that doc left as
a documented, uncosted gap.

LOOK-AHEAD HAZARD -- NAMED, NOT SOLVED HERE. The template is named "final
staff": it names whoever held the OC/DC role at the END of that season, not
who was hired going into it. A mid-season firing means the stored name is
POST-CUTOFF information relative to that season's Week 1 -- CLAUDE.md SS6.1's
exact failure mode. This ingester does NOT attempt the harder fix (walking
Wikipedia revision history to recover the start-of-season name) -- that is a
real, uncosted follow-up flagged in the source research doc and in this
module's own docstring, not silently absorbed here. Instead every row is
stamped honestly:
  - `as_of_date` = that season's final regular-season game date (from this
    repo's own `schedules` table, not guessed) -- i.e. this row describes
    "who was the OC by the end of season N", never "who was hired for
    season N".
  - `is_final_season_snapshot = 1` on every row, always, so nothing
    downstream can mistake this for a preseason value without reading the
    flag.
  - `confidence = 'medium'` (a scraped, unverified-per-row parse of a
    community-maintained template, not a primary-source filing) unless a
    row fails a sanity check, in which case it is quarantined instead of
    stored.

SCHEMA. Reuses `play_callers` (src/ingest_play_callers.py) unchanged --
column shape already supports exactly this (team, season, start_week,
end_week, confidence, source). Historical Wikipedia rows are stored with
start_week=1, end_week=18 (the "final staff" span cannot be split further
without the revision-history work above) and `source='wikipedia:NFL final
staff'`. `coach_id` here is the coordinator's own name string -- Wikipedia
gives no stable numeric ID, so the name (post `identity`-style normalization)
IS the join key; this is a deliberate, named simplification, not an
oversight -- a coach with the exact same rendered name is assumed to be the
same person, which is true in every case checked but is a real, unverified
assumption for any name collision.

TEAM NAME MAPPING. Wikipedia article titles use the franchise's name AS OF
that season, not today's name -- e.g. "2016 St. Louis Rams season" not
"2016 Los Angeles Rams season". `_team_article_name()` below encodes the four
franchises that changed names/cities in the covered window (LA Rams, LA
Chargers, LV Raiders, WAS). Anything outside that window is unverified.

RATE LIMIT / ETIQUETTE. Wikimedia's API terms require a descriptive
User-Agent and prohibit "abusive or disruptive" automation
(docs/research/missing-inputs-sourcing-2026-07-29.md SS3.3, quoting the ToU
directly). This module sends an identifying User-Agent, sleeps >=0.5s between
requests, and caches every response to `data/raw/wikipedia/` so a re-run
never re-fetches an article it already has.
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
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import ingest_play_callers as pc  # noqa: E402

RAW_DIR = REPO / "data" / "raw" / "wikipedia"
DEFAULT_DB = REPO / "data" / "nfl.db"
API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = (
    "fantasy-football-dataops-research/1.0 "
    "(single-user local project; contact: claude3@single.simplelogin.com; "
    "purpose: NFL coordinator history for a personal fantasy-football model)"
)

TEAMS = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA",
    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
    "TEN", "WAS",
]

_CURRENT_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
}


def _team_article_name(team: str, season: int) -> str:
    """Franchise name AS OF `season` -- Wikipedia article titles use the
    period-correct name, not today's. Only the four franchises that moved
    or renamed within a plausible ingestion window are special-cased;
    anything else falls through to its current name."""
    if team == "LA":
        return "St. Louis Rams" if season <= 2015 else "Los Angeles Rams"
    if team == "LAC":
        return "San Diego Chargers" if season <= 2016 else "Los Angeles Chargers"
    if team == "LV":
        return "Oakland Raiders" if season <= 2019 else "Las Vegas Raiders"
    if team == "WAS":
        if season <= 2019:
            return "Washington Redskins"
        if season <= 2021:
            return "Washington Football Team"
        return "Washington Commanders"
    if team not in _CURRENT_NAMES:
        raise KeyError(f"no name mapping for team {team!r}")
    return _CURRENT_NAMES[team]


def _cache_path(team: str, season: int) -> Path:
    return RAW_DIR / f"{team}-{season}.json"


def _fetch_wikitext(team: str, season: int, refresh: bool = False) -> Optional[str]:
    """Returns raw wikitext for the '<season> <Team> season' article, or None
    if the page does not exist. Caches every response."""
    path = _cache_path(team, season)
    if path.exists() and not refresh:
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        title = f"{season} {_team_article_name(team, season)} season"
        params = urllib.parse.urlencode({
            "action": "query", "titles": title, "prop": "revisions",
            "rvprop": "content", "rvslots": "main", "format": "json",
        })
        req = urllib.request.Request(f"{API_URL}?{params}", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        time.sleep(0.5)
    pages = payload.get("query", {}).get("pages", {})
    for _pid, p in pages.items():
        if "missing" in p:
            return None
        revs = p.get("revisions")
        if revs:
            return revs[0]["slots"]["main"]["*"]
    return None


_STAFF_BLOCK_RE = re.compile(r"\{\{NFL final staff(.*?)\n\}\}", re.S)
_HC_RE = re.compile(r"\*\s*Head coach\s*[–—-]\s*(.+)")
# The title before the dash sometimes carries the OC/DC role compounded with
# something else -- e.g. "Assistant head coach/offensive coordinator" (WAS
# 2023, verified). Match "offensive/defensive coordinator" ANYWHERE in the
# bullet's title text, not only as the whole title, so that case is not
# silently missed. Word boundary keeps this from matching unrelated titles
# like "Pass game coordinator" (an OL/positional title, not the OC).
_OC_RE = re.compile(r"\*\s*[^\n]*?\boffensive coordinator\b[^\n]*?[–—-]\s*(.+)", re.I)
_DC_RE = re.compile(r"\*\s*[^\n]*?\bdefensive coordinator\b[^\n]*?[–—-]\s*(.+)", re.I)
_WIKILINK_RE = re.compile(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")


def _clean_name(raw: str) -> Optional[str]:
    """Strip wikitext markup from a staff-list value down to a display name.
    Returns None (never a guess) if the result doesn't look like a name."""
    raw = raw.strip()
    m = _WIKILINK_RE.search(raw)
    if m:
        name = (m.group(2) or m.group(1)).strip()
    else:
        name = raw
    name = re.sub(r"\{\{.*?\}\}", "", name).strip()
    name = re.sub(r"<ref.*?</ref>", "", name, flags=re.S).strip()
    name = re.sub(r"\(.*?\)", "", name).strip()  # disambiguator, e.g. "(American football)"
    name = name.strip(" \t\n*")
    if not name or len(name) > 80:
        return None
    return name


def parse_staff(wikitext: str) -> dict:
    """Returns {'head_coach':..., 'oc':..., 'dc':...} with any field None if
    not found -- never fabricated. Only looks inside the `{{NFL final staff
    ...}}` template block so an unrelated mention elsewhere in the article
    (e.g. a former OC discussed in prose) is not picked up."""
    block_match = _STAFF_BLOCK_RE.search(wikitext)
    if not block_match:
        return {"head_coach": None, "oc": None, "dc": None, "template_found": False}
    block = block_match.group(1)
    out = {"template_found": True}
    for key, pattern in (("head_coach", _HC_RE), ("oc", _OC_RE), ("dc", _DC_RE)):
        m = pattern.search(block)
        out[key] = _clean_name(m.group(1)) if m else None
    return out


def ingest(
    seasons: range,
    teams: list = None,
    db_path: Path = DEFAULT_DB,
    refresh: bool = False,
) -> dict:
    teams = teams or TEAMS
    conn = sqlite3.connect(db_path)
    pc.ensure_table(conn)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS coordinator_quarantine (
            team TEXT, season INTEGER, reason TEXT, retrieved_at TEXT
        )
    """)
    # Additive columns this ingester needs that ingest_play_callers.py's base
    # schema doesn't carry -- ALTER is a no-op on a re-run (guarded).
    existing_cols = {r[1] for r in conn.execute('PRAGMA table_info("play_callers")')}
    if "is_final_season_snapshot" not in existing_cols:
        conn.execute('ALTER TABLE "play_callers" ADD COLUMN is_final_season_snapshot INTEGER')
    if "as_of_date" not in existing_cols:
        conn.execute('ALTER TABLE "play_callers" ADD COLUMN as_of_date TEXT')

    # No `schedules` table exists in nfl.db (verified 2026-07-30) -- pull
    # regular-season game dates directly from nflreadpy, same library the rest
    # of the ingestion pipeline already depends on, rather than adding a new
    # table for one derived value.
    schedules_cache: dict = {}

    def _season_end_date(season: int) -> Optional[str]:
        if season not in schedules_cache:
            try:
                import nflreadpy as nfl
                df = nfl.load_schedules(seasons=[season])
                reg = df.filter(df["game_type"] == "REG")
                schedules_cache[season] = str(reg["gameday"].max()) if reg.height else None
            except Exception:
                schedules_cache[season] = None
        return schedules_cache[season]

    stored, quarantined, no_page, no_template = 0, 0, 0, 0
    rows_to_insert = []
    quarantine_rows = []
    now = None
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    for season in seasons:
        for team in teams:
            try:
                wikitext = _fetch_wikitext(team, season, refresh=refresh)
            except KeyError as e:
                quarantine_rows.append((team, season, str(e), now))
                quarantined += 1
                continue
            if wikitext is None:
                quarantine_rows.append((team, season, "wikipedia_article_not_found", now))
                no_page += 1
                quarantined += 1
                continue
            parsed = parse_staff(wikitext)
            if not parsed["template_found"]:
                quarantine_rows.append((team, season, "no_final_staff_template_on_page", now))
                no_template += 1
                quarantined += 1
                continue
            as_of = _season_end_date(season)
            hc = parsed["head_coach"]
            for role, name in (("OC", parsed["oc"]), ("DC", parsed["dc"])):
                if name is None:
                    quarantine_rows.append(
                        (team, season, f"no_{role.lower()}_field_in_template", now)
                    )
                    quarantined += 1
                    continue
                is_hc_calling = 1 if (hc and role == "OC" and hc == name) else 0
                rows_to_insert.append((
                    team, season, 1, 18, name, role, is_hc_calling, None,
                    "medium", "wikipedia:NFL final staff", 1, as_of,
                ))
                stored += 1

    conn.executemany(
        'INSERT OR REPLACE INTO "play_callers" '
        "(team, season, start_week, end_week, play_caller, title, is_hc_calling, "
        "changed_from_prior_year, confidence, source, is_final_season_snapshot, "
        "as_of_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        rows_to_insert,
    )
    conn.executemany(
        "INSERT INTO coordinator_quarantine (team, season, reason, retrieved_at) VALUES (?,?,?,?)",
        quarantine_rows,
    )
    conn.commit()
    conn.close()
    return {
        "stored": stored, "quarantined": quarantined,
        "no_page": no_page, "no_template": no_template,
        "seasons": list(seasons), "teams": teams,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start-season", type=int, default=2015)
    ap.add_argument("--end-season", type=int, default=2024)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    result = ingest(range(args.start_season, args.end_season + 1), db_path=args.db, refresh=args.refresh)
    print(
        f"stored={result['stored']} quarantined={result['quarantined']} "
        f"(no_page={result['no_page']} no_template={result['no_template']}) "
        f"seasons={result['seasons'][0]}-{result['seasons'][-1]}"
    )


if __name__ == "__main__":
    main()
