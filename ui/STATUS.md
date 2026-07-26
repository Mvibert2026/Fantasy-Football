# PREP front end — status

**Branch:** `frontend-prep` (git worktree at `../fantasy-football-prep`)
**Built against:** export contract **1.4.0**
**Last updated:** 2026-07-26

Run it with one command. Nothing else is needed:

```bash
npm install && npm run dev
```

`predev` copies `data/export/*.json` into `public/`, so the app always starts against
whatever the backend last generated.

---

## Done

**Board** — 378 players, table plus snake round grid. Built sparse-first: 233 of 378 rows
carry no displayable projection and no interval, and that is the designed default, not a
degraded state. Those rows keep full-weight type and each suppressed value explains itself
on hover using the export's own `projection_note`. Filters by position, tier, delta and
"no projection"; empty results read as a state, not an error.

**Attribution panel** — structural only, one honest claim. No evaluative row, suppressed
or otherwise: the board assigns every player at the same positional consensus rank an
identical projection, so it holds no player-level opinion and there is nothing to
attribute. A zeroed-out row would imply a measurement that was never taken.

**Strategy guide** — `sign_test_p` is never rendered against a 0.05 threshold (the floor is
0.125 at n=4, so nothing can clear it), and `power_floor.plain_english` sits beside every
significance number. Season interval and simulation SE are kept visually apart because
they are different uncertainties.

**Glossary, Methodology** — straight from the exports, including the registered nulls as a
first-class section rather than an appendix.

**Assistant** — one entry point, three lanes, every claim tagged:
- `MODEL` — deterministic templates over the exports, citing a field path and run id.
- `SOURCE` — news feed items with publisher, URL, timestamp, and age past ~48h. No body
  text is stored or re-rendered; the prose is licensed.
- `INFERENCE` — model prose over retrieved context only, via a local proxy.

Six templates. A question matching none is reported as unmatched, never guessed at.

**Provenance** — every rendered value goes through a `Cell`, so it carries the field path
it came from. Absence is a variant of the same type with a reason attached, which is why
the sparse case renders as easily as the dense one.

**Trace-field registry** (`ui/data/trace-fields.ts`) — field paths are user-visible text
(tooltips, provenance lines), so renaming one is a product change. The registry pins them
to a contract version with a changelog, and a test fails if the export adds, drops or
renames a displayed field.

**Refresh data control** — visible in the top bar. Re-reads `data/export/`, reports a
before/after table, and says "no update available" explicitly rather than doing nothing
visible. This is what makes the app testable after both sessions go quiet.

**Reasoning proxy** — Vite dev-server middleware, so `npm run dev` stays the only command.
Key read from a gitignored `.env` in Node; never enters the client bundle. No-key,
proxy-down, offline, no-credit, bad-key and rate-limited are all permanent first-class
states with plain-language remedies — never placeholders.

**Tests** — 44 across 6 files, each with a positive control so a broken assertion cannot
pass silently:
- fails if a component renders a literal number not sourced from an export
- fails on any untagged claim from any lane
- app renders and answers export queries with the proxy stopped
- trace-field registry matches the export
- Refresh control: changed, unchanged, server-gone
- board filters (regression cover)

---

## Verified

| Check | Result |
|---|---|
| Thresholds render RB30/WR40/TE10 | ✓ read from `league.json`, never hardcoded |
| Drift banner clears at matching contract | ✓ empty at 1.4.0 |
| `league.json` parses as strict JSON | ✓ fixed upstream at 1.4.0; sanitiser removed |
| Refresh: no-op path | ✓ "No update available" |
| Refresh: change path | ✓ before/after table, applies without page reload |
| Reasoning lane authenticates | ✓ key valid — reaches billing, not auth |
| Reasoning lane degrades cleanly | ✓ plain-language message, other lanes unaffected |
| Key absent from `dist/` | ✓ literal, fragment, `sk-ant-` pattern, `ANTHROPIC` string |
| `.env` gitignored | ✓ hidden from `git status`, `!!` under `--ignored` |
| Typecheck + build | ✓ clean |

---

## Left

**Blocked on you**

- **The reasoning lane cannot complete a call — the Anthropic account has no credit.** The
  key authenticates (an invalid key returns `401`; this reaches a billing check). Add
  credit and the lane works with no code change.
- **That key is in the session transcript.** Rotate it when convenient.
- **The design reference never reached this session.** Tokens in `ui/styles/tokens.css` are
  a reading of the described language — no radius, 1px borders, dense, mono numerals.
  Every visual value lives in that one file, so restyling to the real reference is a
  single-file change, not a component sweep.

**Backend, filed and acknowledged**

- `league.json` `Infinity` token — **fixed at 1.4.0.** The copy-time sanitiser has been
  removed; `sync-exports.mjs` now validates and fails loudly with file, line and token if
  it ever regresses.
- DEF has no replacement level while the roster starts one. Not fixed, and correctly so —
  no DST data is ingested, so any level would be invented. The app renders the board's own
  `def_note` in that row.
- `strategies.json` is still at `1.0.0` while the other six artifacts are at `1.4.0`.
  Surfaced as behind-expected rather than assumed stale, in case it is deliberate.
- `league.json` carries no `generated_utc`, so its run id falls back to
  `league@unversioned`. Cosmetic; the contract version is still reported.

**Deliberately not built**

- Availability, opponents, draft room, player profiles, season mode — out of scope. Not
  stubbed either: a greyed-out tab implies something is coming.
- News ranking, relevance scoring, recency weighting, dedup, retrieval tuning. There is no
  corpus, so anything built now would be guesswork. The contract, the routing, the empty
  state and the staleness rule are in place; the tuning is not.

**Known rough edges**

- The reasoning lane's retrieval is plain substring matching on player names and glossary
  terms. Adequate for a board this size, and deliberately untuned for the same reason the
  news lane is.
- `best available at pick N` assumes the preceding picks took the top N−1 board players.
  The assumption is stated in the answer itself rather than hidden, because availability
  modelling is out of scope.
