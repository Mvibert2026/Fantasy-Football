# Table-stakes inventory — 2026-07-27 (Priority 2A, FR-007)

**Standard applied:** an item is `VERIFIED` only if an executable check (a test that fails when the
property breaks) exists and re-runs after data refreshes. "The code handles it" without a pinning
test is `NOT-VERIFIED`. "Nothing handles it" is `NOT BUILT`. Where I could not establish status from
the repo, the entry says `UNKNOWN — unresolved`, not a guess.

**Headline:** the floor has one crack that outranks everything else on this list — **the consensus
input to the entire board is the wrong scoring format.** `src/ingest_rankings.py:25-36` documents
that the ECR source is the DynastyProcess "redraft-overall" mirror, which has **no half-PPR
variant**, while the league is half-PPR. Every downstream artifact — board order, VBD, the
rank→points curves, availability, the backtest's consensus baseline — inherits a consensus that
values pass-catchers on the wrong reception weight. It is known (thread 018; the fix is escalated
in unmerged worktree commit `a246696` "escalate live-API scoring=HALF switch") and unresolved, and
no executable check even asserts which format the stored rankings are. Under FR-007's own logic
this gates everything: a 5% modelling edge cannot be evaluated against a consensus baseline that is
itself mis-scored.

---

## Inventory

Status per item, with the evidence. Work orders (T-numbers) follow the table.

| # | Table stake | Status | Evidence |
|---|---|---|---|
| 1 | **Consensus source matches league scoring format (half-PPR)** | **NOT-VERIFIED — known mismatch** | `ingest_rankings.py:25-36`: source is standard-scoring; league is half-PPR. Fix escalated, not landed (`a246696`, unmerged). No test asserts the stored format. → **T1** |
| 2 | Scoring engine implements this league's rules (values) | VERIFIED (values) / **UNKNOWN (source of truth)** | `scoring.py:11-45` matches CLAUDE.md §7 line by line; `test_scoring.py` covers thresholds/bonuses. But §7 itself says "reconstructed… **verify against the live league settings before relying**" and no verification record exists anywhere in `docs/`. The **stacking** interpretation (at 400 pass yds: +1.0+1.5+2.0 = +4.5, `score_offensive_game`'s `>=` loop) is an assumption, not a confirmed platform behaviour. PR-002 found the 150/200 bonuses nearly irrelevant, which shrinks but does not close the risk; the 100-yd and 300-yd bonuses are material. → **T2** |
| 3 | Bye weeks current and complete for the live board | **NOT-VERIFIED** | Bye lookup is schedule-derived (`export_contract.py:70-76`) and **fails open to "unknown"** (`export_history.py:100-103`). Tests pin only the honesty of the failure (`test_export_history.py:117-135`) — nothing asserts that 2026 board players actually *have* byes. A FantasyPros-vs-nflverse team-code mismatch (e.g. `JAC`/`JAX`) silently yields no bye for that team's entire roster and no test fails. → **T3** |
| 4 | Known suspensions deducted, with appeal status | **NOT BUILT** | Zero matches for suspension handling in `src/` and `tests/` (grepped). The data question is open in thread 057 (unanswered). This is the item FR-007 was coined over. → **T4** |
| 5 | Injured / season-ending players reflected | **NOT BUILT (live)** | `injuries` table is historical (2010–2024, `ingest_reference.py`; 2025 lacks `date_modified` upstream — CURRENT-STATE). The live injury pipeline is **deliberately deferred** (`operating-model.md:94-96`). The board reflects injuries only as far as the ECR snapshot happens to; nothing records or checks that snapshot's date. → **T5**, and T1's `as_of` fix is a prerequisite |
| 6 | Retired / holdout / non-rostered players removed or flagged | **NOT BUILT** | No roster-membership check exists in `src/` (grep). A post-snapshot retirement stays on the board silently. → **T6** |
| 7 | IR and practice-squad designations | **NOT BUILT** | Same gap as #6 — no NFL roster-status ingestion at all (the existing `rosters.json` is *fantasy league* rosters from draft picks, `test_rosters_export.py`). → **T6** (one work order covers 6+7) |
| 8 | Offseason team changes correct | **NOT-VERIFIED** | Team comes from the latest ECR ingest (`export_contract.py:119-123`), so it is as current as the snapshot — whose age nothing records or bounds. No cross-check against an independent source. → **T5** (freshness) + **T6** (roster cross-check) |
| 9 | Depth charts current | **NOT-VERIFIED — contested** | `CURRENT-STATE.md` "Not built" says depth charts end 2024 (blocking `RB_HANDCUFF`); `RECONCILIATION-2026-07.md:56-59` says the file elsewhere contradicts this and instructs "resolve by checking the data." Still unresolved. → **T7** |
| 10 | Position eligibility, incl. position changes | **NOT-VERIFIED** | Positions come solely from ECR rows (`export_contract.py:119-123`); no check that ECR's position agrees with nflverse's for the same player, and no multi-eligibility concept (`league_config.py:37` is a fixed tuple). A source disagreement (TE/WR edge cases) would ship silently. → **T8** |
| 11 | Rookies present without silent prior-season dependence | **VERIFIED** (board + archetypes) | Board projection depends only on (position, consensus rank) — `make_board.py:19-38` — so rookies need no prior stats; archetypes return `UNDETERMINED reason='rookie'` by construction (`archetypes.py:10-11, 291-313`) with tests in `test_archetypes.py`. Caveat: this holds *because* the board is consensus-derived; the bottom-up framework (ADR-E) must re-earn this property — flagged in the 2B review. |
| 12 | Name collisions and suffix handling | **VERIFIED** | `identity.py:27` (collisions excluded, never guessed), `_SUFFIX_RE`/`normalize_name` (`identity.py:55-64`); pinned by `test_identity.py:101` (collision excluded from coverage but counted) and `:120` (suffix/punctuation normalization). The thread-052 join-key failure family now carries a measured check (371/378 resolve — CURRENT-STATE). |
| 13 | Team abbreviation changes across 26 seasons | **UNKNOWN — unresolved** | No canonical team-code crosswalk anywhere in `src/` (grepped `OAK|LV|SD|LAC|STL|team_abbr` — nothing). Historical joins keyed by team+season exist (`ingest_play_callers.py:147`, `ingest_league_metrics.py`). Whether nflverse's own codes are internally consistent across the 26-season window was not established from the repo. → **T9** |
| 14 | Scoring settings: league size / roster shape | **VERIFIED** | 10 teams, 16 drafted rounds verified against the primary league's actual numbers, with the off-by-one (IR counted) mistake documented so it stays dead (`league_builder.py:73-80`); `league_config.py` validates shape; `test_league_config.py` / `test_league_builder.py` exist. CLAUDE.md §7's "league size not yet confirmed" is stale. |
| 15 | Kicker exclusion | **VERIFIED (by config)** | `make_board.py:84` ("no kicker in this league") is consistent with the primary league's starters (no K slot, `league_builder.py:76-78`). Subject to T2's live-settings verification like everything §7-derived. |
| 16 | DST handling | VERIFIED (as a declared non-goal) | "No DST scoring ingested — declared in `league.json`, not an oversight" (CURRENT-STATE, statistical constants). Honest null, deliberate, recorded. |
| 17 | Ranking-row uniqueness (one row per player/source/season) | **UNKNOWN — unresolved** | Ingest uses `INSERT OR REPLACE` (`ingest_rankings.py:200`) which dedupes only if the table's key covers (player, source, season) — the DDL was not checked this pass. A duplicate player on the board is the same silent-corruption family as #12. → **T10** |
| 18 | Board/ECR snapshot freshness ("the board is not stale") | **NOT BUILT** | Nothing records when the live ECR was pulled or refuses to build a board from an old snapshot. This single mechanism is the interim mitigation for #5, #6, #8 — every "reflected in ECR eventually" argument is only as good as snapshot age. → **T5** |
| 19 | Bye-week *display* honesty (missing ≠ bye) | VERIFIED | `test_export_history.py:117-135` — fail-open to unknown, never fabricate; `bye=true` schedule-derived and distinct. This is the shape-level guarantee that T3 must extend with a coverage guarantee. |
| 20 | Join-key integrity board→history exports | VERIFIED (measured) | Thread 052 / ADR-048: `player_id_gsis` populated, 378/378 carry it, 371/378 resolve with the 7 misses being honest nulls (CURRENT-STATE, Built section). |

Summary: **7 verified, 6 not-verified, 5 not built, 2 unknown.** The verified column is real — the
identity layer and the null-honesty conventions are genuinely strong — but the floor items closest
to draft-day correctness (formats, byes-positive-coverage, suspensions, injuries, rosters,
freshness) are the unverified ones, which is the precise shape FR-007 warns about.

---

## Work orders

All sonnet-executable; owner in brackets. Ordering is by severity × cheapness.

**T1 — Half-PPR consensus source** [data-ops for the pull, backend for the check]
Complete thread 018's escalated switch: pull FantasyPros live API `type=ST&scoring=HALF` for the
2026 preseason snapshot (per `ingest_rankings.py:28`), store `scoring_format` and `as_of_date`
columns on `rankings` rows, re-run board build. Executable check: a test asserting every
`fantasypros_ecr` row used by a board build carries `scoring_format='HALF'`; the board builder
refuses (raises) on any other value. Backfill rows keep their true format label and are excluded
from live-board eligibility. Note: the founder-facing consequence (the current board's RB/WR order
inherits standard-scoring consensus) should be stated in the round report — it affects trust in
the current artifact, not just future ones.

**T2 — Verify scoring against the live league page** [founder, 10 minutes; backend, small]
Founder screenshots or exports the platform's scoring settings page. Backend transcribes it into a
fixture (`tests/fixtures/league_scoring_live.json`) and adds a test asserting `scoring.LEAGUE`
equals the fixture, including whether bonuses stack or replace at each threshold. Record the
verification date in `decisions.md`. Until then, CLAUDE.md §7's own "verify before relying" caveat
stands unmet — four seasons of that caveat is enough.

**T3 — Positive bye coverage** [backend, small]
Test: for the live season, every board player's team resolves to a non-null bye week; failure
lists the unresolved team codes. This converts the current fail-open into fail-loud at build time
while keeping the honest-null export shape. Include a canonicalisation step (or crosswalk table)
for FantasyPros↔nflverse team codes, which T9 generalises.

**T4 — Suspensions** [blocked on thread 057's data answer; then data-ops + backend]
When 057 identifies a source: `suspensions` table (player, games, appeal_status, `as_of_date`);
board rows for suspended players carry a flag and a games-adjusted projection or an explicit
"not adjusted" marker. Interim executable check that does not wait for 057: a hand-curated fixture
of known 2026 suspensions (a 10-minute founder/researcher task) asserted against board flags — the
check exists first, the automated feed replaces its data source later.

**T5 — Snapshot freshness tripwire** [backend, small]
Record `as_of_date` on every live ECR pull (part of T1). Board build fails if the snapshot is
older than N days (suggest N=3 in-season of draft prep, founder-tunable in `league_config`).
`check`-level warning surfaces the age. This is the single cheapest mitigation for injuries,
retirements, and team changes until dedicated feeds exist, because it bounds how stale the board's
implicit knowledge can be.

**T6 — NFL roster-status ingest** [data-ops, ~1 session]
Ingest nflverse rosters for the live season (status: active / IR / PS / not-rostered). Executable
checks: (a) every board player inside draft-relevant depth resolves against the roster table;
(b) any board player whose status is not active is flagged on the board row; (c) a fixture with a
retired player asserts exclusion-or-flag. Covers items 6, 7, and the cross-check half of 8.

**T7 — Settle the depth-chart contradiction** [data-ops, minutes]
One query: `SELECT MAX(dt) FROM depth_charts`. Delete whichever CURRENT-STATE line is wrong
(RECONCILIATION already ordered this; it has not happened). If 2025+ exists, unblock
`RB_HANDCUFF`; if not, note the gap and its owner.

**T8 — Position cross-check** [backend, small]
Test: for every board player, ECR position == nflverse roster position (once T6 lands); mismatches
go to a quarantine list, never silently resolved — same pattern as `identity.py` collisions.

**T9 — Team-code canonicalisation** [backend, small]
A canonical team table with era mapping (OAK→LV, SD→LAC, STL→LA, plus code variants JAC/JAX etc.).
Test: every distinct team code in every table (`rankings`, `player_weekly_stats`, `play_callers`,
league metrics, schedules) resolves to a canonical franchise for its season. Whether this finds
zero problems or several, the result becomes a permanent regression check.

**T10 — Ranking uniqueness assertion** [backend, trivial]
Test: `SELECT player_name, COUNT(*) FROM rankings WHERE source='fantasypros_ecr' AND season=?
GROUP BY player_name HAVING COUNT(*)>1` returns empty for the live season, and the table's
uniqueness key covers (player, source, season). Closes the #17 unknown either way.

---

## What survives the attack

Stated plainly, per the mandate: the identity layer (#12, #20) is genuinely good — suffix
normalization, collision quarantine, and a measured join-coverage number are exactly what
"executable check" means, and the null-honesty discipline (#16, #19) is consistently applied and
tested. The project's floor problem is not sloppiness in what was built; it is that the items
*nobody built yet* (suspensions, rosters, freshness) and the one mis-formatted input (#1) are
precisely the ones a founder checking a single suspended or traded player would hit first.
