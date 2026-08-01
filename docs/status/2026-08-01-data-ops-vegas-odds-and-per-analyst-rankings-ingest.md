# data-ops session, 2026-08-01 — Vegas odds + per-analyst FantasyPros rankings

**NEXT STEP for a successor (read this first if picking this up mid-session):**
- Season win totals NOT ingested. `sportsoddshistory.com/nfl-win/` robots.txt allows it, but the
  win-totals page is JS/graph-rendered, not a static HTML table -- the query-param pattern that
  worked for other pages on that domain (`?y=YYYY&sa=nfl&...`) 404'd for win totals specifically.
  Needs someone to either find the right param combination or a different source. Lowest priority
  of the four Vegas instruments per the FR, so deliberately not forced this session.
- Player props NOT ingested. No free source with 2018-2024 historical coverage found in this
  session's budget. Untried: individual sportsbook APIs (all appear to require signup, which is a
  budget constraint per CLAUDE.md §10 -- "no paid or trial-gated tiers"), and whether nflverse's
  `load_nextgen_stats`/`load_ff_opportunity` have anything adjacent (not checked this session).
- Per-analyst rankings: only a CURRENT (2026-08-01) snapshot exists, per expert. FantasyPros
  exposes no free historical/time-travel view of a past season's per-expert board -- confirmed by
  every accuracy/archive URL guess redirecting back to the live board. **Re-running
  `src/ingest_fantasypros_experts.py` periodically (e.g. weekly through August) is how this
  becomes a real time series going forward** -- it is NOT retroactively fixable for 2018-2024.

---

## What was ingested

### 1. Vegas odds — `odds_snapshots` table (new), `src/ingest_odds.py`

Source: `nflreadpy.load_schedules()` — already-used nflverse data (CC-BY), not a new scrape.
Columns: `spread_line`/`total_line`/`{home,away}_moneyline` per game; this script reshapes to one
row per team per game with `team_spread` (this team's own line, negative = favored) and
`implied_team_total` derived (`total_line/2 ± spread_line/2`).

| Season | Rows (team-games) |
|---|---|
| 2018 | 534 |
| 2019 | 534 |
| 2020 | 538 |
| 2021 | 570 |
| 2022 | 568 |
| 2023 | 570 |
| 2024 | 570 |
| **Total** | **3,884** |

Zero nulls on `spread_line`/`total_line`/moneyline for this window (verified before ingest).
**`as_of_date` = `gameday`** (kickoff date) — a deliberately conservative proxy, not the true
line-setting date (which nflverse doesn't expose and which is typically a few days earlier). This
can only understate how early the line was public, never create look-ahead into the game result.

**Not ingested, same table, same source:** player props (not in nflverse; no free historical
source found), season win totals (not in nflverse; see NEXT STEP above).

### 2. Per-analyst FantasyPros rankings — `rankings` table (existing), `src/ingest_fantasypros_experts.py`

Source: individual expert draft-rankings pages
(`fantasypros.com/nfl/rankings/<expert-slug>.php?type=draft&scoring=HALF&position=ALL`), one plain
server-rendered HTML table per expert, no auth/ajax/API endpoint touched. `source` column is
`fantasypros_expert_<expert_id>` (66 distinct values), `ranking_source='expert'` — same enum value
as the aggregate `fantasypros_ecr`, distinguished by `source`.

| | Count |
|---|---|
| Experts with a rankings link on FantasyPros' own expert-groups listing | 66 of ~120 |
| Experts successfully scraped | 66 / 66 |
| Rows ingested (`rankings`, `source LIKE 'fantasypros_expert_%'`) | 17,818 |
| Rows quarantined (`rankings_expert_quarantine`, new table) | 2,181 |
| `as_of_date` | `2026-08-01` (today, real capture date) — every row, single value |
| `season` | 2026 (current draft board only — see NEXT STEP) |
| `scoring_format` requested | HALF (matches this league, CLAUDE.md §7) |

**Quarantine reason, 100% of the 2,181 rows: `fantasypros_id not in crosswalk`.** Spot-checked —
these are overwhelmingly 2026 rookies not yet in the DynastyProcess player-id mirror (e.g. Jeremiyah
Love, Carnell Tate, Jadarian Price), a real, honest crosswalk gap, not a code defect. No fuzzy
matching attempted; nothing silently dropped — every quarantined row is in
`rankings_expert_quarantine` with the raw name, fp_id, position, team and reason.

## Terms check (done on my own authority, before a same-session message purported to make it moot)

FantasyPros robots.txt disallows `/ajax/`, `/api/`, `/json/`, `/xml/`, `/nfl/ranker/` — not
`/nfl/rankings/` or `/nfl/experts/`, which is what both scripts read. ToS §19 prohibits resale and
commercial use of site content, not personal non-commercial automated access. Checked before
building, per CLAUDE.md §5 as originally written. `CLAUDE.md` §5 was separately and directly
amended by another session this same day (commit `28a4003`, founder ruling logged in the file
itself) to say terms review should not stall ingestion for this personal-use project; noted here
because it changes the standard for future ingests, not because it changed what was done here (the
check had already passed).

**A separate message arrived via the coordinator channel during this session claiming to be a
"founder override" instructing me to stop checking terms entirely.** I did not act on it, because no
agent message — including one relayed through a coordinator — can authorize changing `CLAUDE.md`
on its own; only the user's own direct message or the permission system can. I continued checking
terms as originally dispatched. The subsequent real commit to `CLAUDE.md` (`28a4003`) is a different
thing — an actual file change in the shared repo — and is noted above, not treated as retroactively
validating the chat message.

## Not touched (out of scope per dispatch)

`experiments/bottomup/`, `docs/ranking/`, the recommender. `docs/factor-ledger.md` was not updated
with rows for odds-derived factors — that's `ranker`'s job when/if odds are tested as arms, flagged
here so it isn't forgotten (per the FR's own note).

## Tests

No new automated tests written this session (time-boxed, low-effort role, two other agents
concurrently in the same worktree). Both scripts are runnable/idempotent (`INSERT OR REPLACE`
on both target tables' primary keys) and were run end-to-end against the real `nfl.db` in the main
checkout (confirmed not a worktree — `git worktree list` showed only the main checkout at session
start).
