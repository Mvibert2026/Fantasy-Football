# 2026-07-30 — backend — Yahoo Fantasy Sports connector (FR-062, ADR-063)

**Dispatch:** direct task, not a handoff thread. Founder promoted FR-062 to near-term work in his
own words ("add the yahoo connection work to our near term work... sooner than later"). Read
`docs/founder-requests/FR-062-...md` and `docs/research/yahoo-espn-league-connection-2026-07-30.md`
(thread 095, staged `TO: pm`, unallocated) first per the dispatch instruction; did not re-derive
the research.

**Constraint that shaped the build:** no real Yahoo credential exists (the founder's own account,
registration undone at build time), and Yahoo hosts are not fetched by agents. Everything is built
against documented shapes, tested against constructed fixtures, never a live response.

## What was built

`src/providers/` — new package, adapter pattern per CLAUDE.md SS4:
- `base.py` — `LeagueProvider` ABC, `Bonus(points, target)`/`StatModifier`/`RosterPositionSpec`/
  `LeagueSettings`/`DraftPick`/`DraftResult` dataclasses, `ProviderUnavailable` exception.
- `yahoo_oauth.py` — OAuth2 Installed-Application flow (authorization URL, code exchange, hourly
  refresh), `TokenStore` (file-backed, gitignored `data/.yahoo_token.json`), minimal stdlib `.env`
  loader (no python-dotenv dependency added).
- `mapping.py` — signature-key-based recursive JSON extraction (never a fixed path — Yahoo's
  actual response shape has never been read by this project), `LeagueSettings.parse_warnings` on
  every mismatch instead of a crash, `diff_against_claude_md_westwood()` for the "free correctness
  audit" the research doc recommends running first.
- `yahoo.py` — `YahooProvider`: `get_league_settings`, `get_draft_results`, `get_live_draft_picks`
  (caveated, `is_live_estimate=True`, never asserted reliable), `discover_leagues`. 401 triggers one
  refresh-and-retry. `from_env()` raises `ProviderUnavailable` with a stated, checkable reason
  (missing credentials, or credentials-but-no-authorization) instead of crashing.
- `espn.py` — `ESPNProvider`, implements the interface, always raises `ProviderUnavailable` citing
  Disney ToU SS2.B.x/SS2.A/SS3.H by section.

`scripts/yahoo_connect.py` — one-time interactive OAuth authorize (opens a URL, prompts for the
verification code, saves the token). `scripts/yahoo_pull_league_settings.py` — fetch, print, diff
against CLAUDE.md SS7; `--out` writes a report file only if passed explicitly (default is
fetch-print-discard, per the retention decision below).

`.env.example` (new, repo root) documents `YAHOO_CLIENT_ID`/`YAHOO_CLIENT_SECRET`/
`YAHOO_REDIRECT_URI`. `.gitignore` gained `data/.yahoo_token.json`. `requirements.txt` gained
`requests==2.32.5` (already a transitive dependency, now pinned directly).

## Real finding: `yfpy` does not currently install here

`pip install yfpy` failed: its `yahoo-oauth` dependency pulls in `myql` and `rauth` (unmaintained
legacy Yahoo Query Language packages), whose `setup.py` raises `AttributeError: install_layout`
under the installed `setuptools`. Verified by running the install, not assumed. Per CLAUDE.md's
"a source swap is not a substitution" guardrail, this changed the design: the connector talks to
Yahoo's OAuth2 + REST v2 endpoints directly via `requests`, defining its own dataclasses matching
yfpy's *documented* field shapes (verified in the research doc by reading `yfpy`'s `models.py`
source) rather than vendoring a library that doesn't build in this environment.

## Two architectural decisions made, not deferred

1. **Fetch-on-demand only.** The research doc's [SNIPPET]-tagged reading of Yahoo's 24-hour
   retention clause is treated as binding pending verification against Yahoo's actual Fantasy
   Sports APIs Terms of Use (never read by this project). Nothing in `src/providers/` writes to
   `nfl.db`; it's correctly outside the `sqlite3.connect()` ingestion allowlist because it never
   opens a connection. The only Yahoo-derived persistence anywhere is the OAuth token itself.
2. **Live draft picks: designed for, not depended on.** Rests on a single undated SDK docstring.
   `get_live_draft_picks()` exists and returns a caveated result; a structural test
   (`test_no_pick_write_capability_exists_on_the_provider`) asserts no write path was added,
   consistent with every source read (no wrapper documents a draft-pick write endpoint).

Full reasoning: ADR-063, `docs/decisions.md`.

## Tests

58 new, all passing without network or credentials:
`tests/test_providers_base.py` (7), `tests/test_providers_mapping.py` (16),
`tests/test_providers_yahoo_oauth.py` (19), `tests/test_providers_yahoo.py` (12),
`tests/test_providers_espn.py` (4). Fixtures in `tests/fixtures/yahoo/*.json` carry an explicit
`_fixture_note` field labeling them constructed, not captured.

Full suite: `python3 -m pytest -q` → 34 failed / 795 passed / 12 skipped / 9 errors, all
pre-existing (missing `data/nfl.db` in this worktree; the already-known
`ingest_sleeper_projections.py` sqlite-allowlist finding from thread 094; the pre-existing
ADR-054/055 mailbox collision). None touch `src/providers/` or its tests — confirmed by running
the new test files in isolation (58/58 pass) and by inspecting each failure's traceback.

## Not done here, and why

- **Cannot be verified end-to-end.** No real Yahoo credential exists. STATUS on FR-062 is left at
  `IN PROGRESS`, not `SHIPPED` — the founder's own five-minute test (register, authorize, pull
  Westwood's settings, diff against CLAUDE.md) is the remaining gate, and it's his to run.
- **No contract-version bump.** This doesn't touch `board.json` or any frontend export; no handoff
  to frontend needed.
- **Thread 095 (`TO: pm`) not resolved by this session** — not backend's thread. This update
  documents what was built in response to the founder's own promotion of the work, recorded in
  FR-062's own file (`## Update 2026-07-30 (backend)`), not a resolution of someone else's thread.
- **Founder-said capture:** the promotion itself ("sooner than later") is recorded in FR-062's
  update section above, not as a separate new FR — same subject, same file, per
  `docs/founder-requests/README.md` rule 3 (status changes/updates are edits to the request's own
  file).

## Commit

See commit hash in the session's final report (this file is written before the commit that
includes it, per the write-back protocol).
