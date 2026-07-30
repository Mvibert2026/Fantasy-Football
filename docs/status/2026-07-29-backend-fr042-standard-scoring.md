# 2026-07-29 — backend — fr042-standard-scoring

Executed `docs/founder-requests/FR-042-presets-must-use-standard-scoring-only-westwood.md`, a
decision, not a question: only the primary (Westwood) league carries the custom stacking-bonus
scoring ruleset; every other league gets standard scoring, varying PPR only.

**The defect.** `generate_config_matrix.py`'s 24 presets and `league_builder.py`'s
`create_league()` both deep-copied `scoring.LEAGUE` (Westwood's verified custom ruleset,
stacking yardage bonuses at 100/150/200/300/350/400, ADR-052) and only swapped/overrode the
reception value. A preset labeled "ESPN-default, 12 teams, half scoring" was Westwood with a
different name. `generate_config_matrix.py`'s docstring also self-contradicted: claimed the bonus
structure "happens to match ESPN's confirmed platform defaults exactly" twelve lines above
admitting the ESPN fetch was blocked and never verified.

**Fix.** New `src/standard_scoring.py::STANDARD_LEAGUE` — a genuinely separate ruleset. Offense
matches the founder's own explicit FR-042 definition verbatim (25 yd/pt passing, 4 pt passing TD,
-2 INT, 10 yd/pt rushing/receiving, 6 pt TD, -2 fumble lost, no yardage bonuses). Minor categories
not named in the ruling (return-TD, two-point, offensive-fumble-return-TD) kept at conventional
flat values, flagged as a judgment call. Defense — also not named — is a conventional, explicitly
UNVERIFIED placeholder, deliberately distinct from Westwood's own defense dict so it can't
silently reintroduce the bug. Both `generate_config_matrix.scoring_variant()` and
`league_builder.build_scoring()` now build on this, not `scoring.LEAGUE`. Only the primary league
is unreachable through either path (both reject `league_id="primary"`).

**Contract 1.14.0 -> 1.15.0 (additive).** `league.json` gains `scoring_ruleset_note`, stating on
screen which ruleset a league actually uses (the founder's explicit "state the assumption on the
screen" instruction). Handoff thread 093 opened to frontend.

**Regenerated, not edited:** all 24 presets, `ethans_expert_league` (a real, previously-created
custom league that also carried Westwood's defense silently — found in the course of this work,
not part of the literal "24 presets" ask, fixed via its existing `scripts/
rebuild_ethans_expert_league.py`), and the primary league's own export (to pick up the contract
bump; `scoring.LEAGUE` itself untouched).

**Evidence — before/after, `espn_10_half`:** Bijan Robinson 303.16 -> 296.68 pts (VBD 162.94 ->
158.20), Ja'Marr Chase 276.48 -> 267.48 pts, Josh Allen 359.01 -> 351.55 pts — all real movement
from removed stacking bonuses, not noise. **Westwood's own board verified byte-identical**: Bijan
Robinson 303.16 pts / VBD 172.17, unchanged before and after regenerating the primary export.

**ADR-062** in `docs/decisions.md` has the full writeup and evidence table. (Drafted as ADR-061
first; renumbered after `tools/handoffs.py adr next` caught a genuine allocator race against a
concurrent session's own ADR-061 -- resolved via the tool, not by hand, `check` confirms clean.)

Also regenerated: primary league's `glossary.json`/`nulls.json`/`opponents.json` and
`strategies.json` (~13 min real Monte Carlo re-run; diffed to confirm every strategy margin is
byte-identical, only `contract_version`/`generated_utc` changed -- Westwood's scoring was never
touched). Regenerating the primary board incidentally also closed an ADR-060 gap (stale
`consensus_source_note` ADR-018 text) that session's missing `nfl.db` had left open.

New/changed tests: `tests/test_standard_scoring.py` (new, 7 checks, written before the callers
were changed, per CLAUDE.md ordering), plus one regression test each in
`test_generate_config_matrix.py` and `test_league_builder.py` asserting the standard ruleset (no
bonuses, distinct from Westwood) is what actually gets used, plus `test_rosters_export.py`'s
version-bump guard updated to 1.15.0.

**Tests: 763 passed, 6 failed** (full suite, real `nfl.db`). All 6 failures pre-existing/unrelated:
the known ADR-054/055 mailbox collision, one unrelated pre-existing `sqlite3.connect` finding in
`ingest_sleeper_projections.py`, and 4 tests in the FFC-ADP/Sleeper ingestion suites that hardcode
`as_of_date="2026-07-29"` against real wall-clock "today" and broke when the session crossed into
2026-07-30 mid-run (fail identically in isolation, no dependency on this change).

**Open for frontend:** handoff thread 093 (contract 1.15.0 bump, `scoring_ruleset_note` field) —
frontend's call whether/where to surface it in the UI.

