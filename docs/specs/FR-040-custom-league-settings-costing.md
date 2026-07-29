# FR-040 — Custom league option in League settings: spec and costing

Backend spec/costing pass, 2026-07-29. Scope was explicitly **spec and costing, no contract
version bump, no changes to `src/export_contract.py` beyond reading**. This document challenges
PM's "Initial read" in `docs/founder-requests/FR-040-custom-league-option-in-league-settings-two-hard.md`
against the real code and a live run, then answers A/B/C as asked.

**Superseding correction received mid-run, addressed throughout below:** `docs/founder-requests/
FR-042-presets-must-use-standard-scoring-only-westwood.md` — the founder ruled the 24 presets must
carry **standard** scoring (no yardage bonuses, varying PPR only) and that Weswood alone keeps the
custom ruleset and opponent modelling. That is a decision, not a question, and it changes the single
most important sequencing point in this doc — see §C.

---

## What was actually run, vs. what was read

This session had a real `data/nfl.db` (copied from the main checkout per `docs/environment.md` §4
— worktrees do not inherit it) and ran `league_builder.create_and_export_league(...)` end to end
twice: once with a malformed scoring override (crashed, see §C/§B) and once with a corrected one
(succeeded, 7 real artifacts written, real re-scored `board.json`). Everything under "Verified by
running" below was observed directly, not inferred from source reading. Everything under "Verified
by reading" was traced through the actual current source, not assumed from docstrings — per
`CLAUDE.md`'s standing warning that a docstring's framing of a source has previously been wrong
(`src/ingest_rankings.py`).

---

## Challenge 1 — "The backend for this already exists"

**Mostly true, with two real gaps found by running it, not reading it.**

Ran `league_builder.create_and_export_league()` for a fabricated 12-team, full-PPR league with
non-Westwood TD values (passing TD 6, rushing/receiving TD 8) and a passing-yardage bonus at 250
yards. Result:

1. **First attempt crashed.** Passed the bonus as `{"threshold": 250, "bonus": 3}` — the natural
   shape a JSON-consuming settings form would produce. `scoring.score_offensive_game` unpacks
   `for threshold, bonus in off["passing_yards"]["bonuses"]`, which expects a list of 2-tuples, not
   objects. Crash was a `TypeError: '>=' not supported between instances of 'int' and 'str'` five
   stack frames deep inside `scoring.py`, nowhere near the actual input error, and would surface to
   whoever submits the form as an opaque 500. **`league_builder.build_scoring()` validates only that
   override keys are known offense fields (`src/league_builder.py:88-95`) — it does zero shape
   validation on nested structures** (bonus lists, points-allowed tiers). This is a real, load-bearing
   gap for §B: the settings screen (or an API layer in front of this function) must validate bonus
   shape before calling `create_league`, or the founder gets a stack trace instead of a rejected form.
2. **Second attempt, corrected shape (`[(250, 3)]`), succeeded** and wrote all 7 artifacts:
   `board.json` (880KB, 510 players), `availability.json`, `league.json`, `rosters.json`,
   `glossary.json`, `nulls.json`, `opponents.json`. `board.json` genuinely reflects the new scoring
   — Bijan Robinson's `projected_points` came back **361.94** (inflated by the +8-point TDs vs.
   Westwood's 6), confirming the curve was refit against stats re-scored under the new rules, not
   copied from Westwood. This is real re-scoring, not a cosmetic label change.

**Does it produce `availability.json` and `strategies.json`, or the stub/absent state the
config-matrix leagues start in?** Checked directly: `availability.json` **is written but is the
same empty stub every fresh non-primary league starts in** — `by_player: {}`, `by_tier: {}` —
because `build_availability_json` reads `data/leagues/<id>/availability.csv`, which
`export_league()` never generates (that requires a separate `run_availability.py` pass, a real,
~minutes-scale simulation job, not part of this path). **`strategies.json` is not written at all**
(absent, not empty) — `export_league()` calls `ec.write_all(...)` without a `strategies=` argument,
and `write_all` only emits that key when one is passed. Both facts match the module's own docstring
claims, which for once were accurate — verified by running, not just reading.

**Does it handle a scoring override that changes TD values and bonus thresholds, not just
reception value?** Yes, mechanically — once the bonus shape is a list of 2-tuples. `build_scoring()`
shallow-merges any `scoring_overrides` dict key into the offense block, so `passing_td`,
`rushing_td`, `receiving_td`, `interception`, `fumbles_lost`, and the three yardage-bonus blocks are
all reachable. **But it starts from `scoring.LEAGUE` — Westwood's ruleset — and only overrides what
you explicitly pass.** A caller who sets `ppr=1.0` and forgets to also null out the yardage bonuses
gets Westwood's stacking +1/+1.5/+2 bonuses on a "generic" league. This is the exact defect class
FR-042 just corrected in `generate_config_matrix.py` (§C) — it exists a second time here,
independently, in `league_builder.py`, and was not previously reported. **New finding for FR-043**
(capability audit): `league_builder.py` has no caller anywhere in the app or in any script besides
`scripts/rebuild_ethans_expert_league.py`; the defect above has therefore never been exercised by
anything before this session.

**Bottom line for §A of FR-040:** the backend claim holds for computation. It does not hold for "no
gaps" — there is a real crash-on-natural-input bug and a real silent-Westwood-default bug, both in
the one function every custom-league path must go through.

---

## Challenge 2 — the client-side feasibility split

**PM's table is directionally right but overstates what "ships today" without a small, currently
unexported field.**

### Team count / roster shape / flex slots → VBD

Traced `export_contract.build_board_json` → `make_board.build_board` → `ReplacementLevels.
baselines()` (`src/scoring.py:161-169`):

```
baselines[pos] = teams * starters[pos] + round(total_flex * flex_split[pos])
```

and VBD is `curve.predict(player_rank) - curve.predict(baselines[pos])` — i.e. a player's own
`projected_points` minus the `projected_points` of whichever player sits at position `baselines[pos]`
in that position's rank order. **Confirmed by running:** `board.json` already exports
`replacement_levels_used` (e.g. `{"QB": 12, "RB": 30, "WR": 30, "TE": 12}` for the 12-team test
league above) and every player row already carries `positional_rank`, so *for the league exactly as
exported*, VBD recompute needs no new data — the replacement counts and every player's points are
already shipped.

**The gap: `flex_split` itself is never exported anywhere** — not in `board.json`, not in
`league.json`. It lives only as a Python module constant in `scoring.py`
(`{"RB": 0.52, "WR": 0.48, "TE": 0.00}`, ADR-029, measured for Westwood over 26 seasons) and is the
fallback used for *every* non-primary league whose own split hasn't been measured (which, per
ADR-029's own text, is every league that isn't Westwood — no other league's split has ever been
measured). So: if the founder previews the *exact currently-exported* team count/roster shape,
nothing needs recomputing — the board already has the answer. **If he changes team count or roster
shape live in the settings screen and expects an instant new `replacement_levels_used` and VBD
without a round trip, the browser needs `flex_split` to compute the new baseline counts itself, and
that value does not exist in the contract today.** Two honest options, not costed further here since
no contract change is authorized this pass: (a) export `flex_split` as a new top-level scalar-ish
field (three floats — cheap, no payload concern, but it is a genuine contract addition and needs the
version bump + frontend handoff the constraints of this run explicitly forbid doing now), or (b)
duplicate the constant client-side, which creates a drift risk the moment a league's split is ever
actually measured server-side and the two copies diverge silently.

**Draft slot / playoff weeks/teams:** confirmed genuinely feasible with zero scoring dependency.
`league.json`'s `pick_sequence` is pure arithmetic from `teams` + `draft_type` + `user_draft_slot`
(verified in the test export — a 12-team snake from slot 3 produced `[3, 22, 27, 46, 51, ...]`,
which is exactly snake-draft arithmetic, no DB or scoring lookup involved). This half of PM's claim
holds without qualification.

### Scoring (PPR, TD values, bonuses, INT, fumbles, defense)

Confirmed correctly infeasible client-side, and confirmed *why* precisely (§A below): `board.json`'s
player rows carry only `projected_points`, `vbd`, `ci_low`/`ci_high` and metadata — no
`passing_yards`, `receptions`, `rushing_tds`, or any other raw or projected component (dumped a full
player row above; the field list is exhaustive, nothing was omitted). There is nothing in the export
a browser could re-score from. PM's claim holds without qualification.

---

## A. Component projections — the question that decides everything

**Confirmed: the pipeline does not have per-player component projections for the target season. The
model is `points ≈ intercept + slope · ln(consensus_rank)`, fit per position, and a player's
`projected_points` is a single lookup of that curve at their consensus rank
(`src/make_board.py::RankCurve.predict`, `src/make_board.py:274-395 fit_rank_curves`/`build_board`).
There are no per-player passing yards, receptions, or TD-count projections anywhere upstream of
`board.json` — the idea in Task A is dead, exactly as the prompt anticipated it might be.**

What the pipeline *does* have: real historical per-game component stats
(`player_weekly_stats` → `dbmod.actual_season_outcomes` → `score_offensive_game`, which does consume
real `passing_yards`/`receptions`/`rushing_tds`/etc. columns). But that data is only ever used to
compute **last season's actual total fantasy points** under a given scoring config, which becomes
one `(rank, points)` training observation for the curve fit. It is never projected forward per
player. Confirmed by running: re-scoring the same historical games under the test league's TD values
(6/8/8 instead of 4/6/6) genuinely changed the fitted curve and the resulting `projected_points`
(Bijan Robinson 361.94 under the test scoring vs. a lower figure under Westwood's) — this is real
proof the *re-scoring* path works end-to-end, and equally real proof that it requires re-running the
whole training pipeline (`fit_rank_curves` over `player_weekly_stats`), not a lookup against a
per-player stat line that could be shipped to a browser.

**Cost if built anyway.** Building real per-player forward component projections (expected passing
yards, receptions, TDs, etc., per player, for the 2026 season) is not a contract change — it is a new
model. It would need its own training target per stat category, its own holdout discipline (§6.3 of
`CLAUDE.md`), a way to recombine correlated per-category errors into a single scoring formula without
overstating combined confidence, and a red-team pass on whether component-level fitting overfits
harder than the single rank curve does with ~200-300 players/season. That is Statistician-tier
(Opus, effort 4) work measured in weeks, not a payload-size line item. **Recommend: do not pursue
this. It answers a UI convenience question with a real modelling program.**

**What this means for "custom" scoring in practice:** the only correct path to a genuinely custom
scoring ruleset is what §Challenge 1 already demonstrated works — a real backend recompute through
`league_builder.export_league()` (confirmed ~end-to-end in this session, no timing measured this
pass but `create_and_export_league`'s own docstring cites ~7-10s per the existing config-matrix
timing, consistent with `ADR-047`'s measured 7s/config). That is inherently a server-side or
CI-triggered step, not a static-site computation — see §B.

---

## B. The spec the frontend build needs

### B.0 The static-hosting collision this doc must flag before anything else

`docs/design-handoff/settings/SETTINGS-EDITOR-SPEC.md` (pinned 26 Jul, still live and cited) already
specifies a full settings-editor UI, and its §7 "Backend contract" is a real job-queue API:
`PATCH /api/leagues/:id/settings`, `POST /api/leagues/:id/recompute`, a pollable `GET
/api/recompute/:job_id`, and a separate `apply` call. **`draft.maplerock.net` / the Cloudflare Worker
deploy (`docs/CURRENT-STATE.md`, verified 2026-07-29) serves a static Vite build with no Python
behind it at all.** There is no server to receive that `PATCH`/`POST`, no job runner, no `job_id` to
poll. That spec's Tier-2 (scoring) flow **cannot be built as written against the current hosting
decision** — it assumes an API layer FR-040's own "Initial read" correctly identifies as not
existing (option (b), "contradicts the current no-backend hosting decision"). This is a genuine,
previously-unflagged contradiction between two live documents and belongs in front of PM/frontend
before either builds against the older spec. Its Tier-1 claim ("Applies instantly, client-side. No
job, no spinner") is *closer* to true per Challenge 2 above, but still needs `flex_split` exported to
be exactly true for an arbitrary new roster shape, not just the currently-exported one.

### B.1 What can ship now, unblocked, static-only

- **Team count, roster shape (starters/flex/bench/IR), draft slot, playoff teams/weeks/reseeding**
  for a **preview**, using only what `board.json`/`league.json` already export for the *current*
  league — genuinely instant, client-side, zero backend calls. This is real and shippable today.
- The moment the founder wants to preview a **different** team count or roster shape than the one
  currently exported, the client cannot produce a correct new `replacement_levels_used` without
  `flex_split` (§Challenge 2). **The screen must either (a) ship a hardcoded copy of the same
  `{RB:0.52, WR:0.48, TE:0.00}` fallback scoring.py uses today with a visible "not measured for this
  league" caveat identical to the one `board.json`'s `replacement_levels_flex_split_note` already
  carries, or (b) refuse to preview a changed roster shape client-side until `flex_split` is a real
  export field.** Recommend (a) short-term (same number, same caveat, zero contract change) with an
  explicit TODO to replace it with (b) once a contract bump is authorized — this is the cheapest
  correct interim, not a shortcut around the caveat rule.

### B.2 What must go through a real backend recompute (server-side, not this static site)

- Any change to PPR, TD values (passing/rushing/receiving), interception, fumbles, yardage-bonus
  thresholds/amounts, or defensive scoring. Confirmed no shortcut exists (§A). The only real path is
  `league_builder.create_and_export_league()` — which is already built, already tested by this
  session's live run, and already produces all 7 artifacts for an arbitrary scoring ruleset (modulo
  the two bugs in §Challenge 1). **This needs a trigger**, which does not exist today: no API
  endpoint, no CI job, no button anywhere calls this function. Building that trigger — however
  thin (a GitHub Action `workflow_dispatch` that runs a script and commits the new `data/export/
  <id>/` directory, or a genuinely separate small API service if one is ever justified) — is real,
  separately-scoped backend work, not covered by this pass.
- **What the screen must refuse to offer, precisely:** any scoring-affecting control must be visibly
  disabled from producing a live board preview until that recompute has actually run and its output
  has actually loaded. **Do not let the UI compute a client-side placeholder VBD/projection under
  the new scoring and show it next to the old board** — there is no formula available to do that
  honestly (§A), so a fabricated placeholder is indistinguishable from a real number to the founder
  and is exactly the failure mode named in the ask ("a settings screen that lets the founder type a
  TD value and then shows him a board scored under a different TD value"). Concretely: scoring
  fields should be editable, but the "preview"/board panel must stay on the *currently exported*
  numbers, tagged with which ruleset produced them, until a real regenerate has completed — this is
  the same "pre-edit numbers are not stale, they are correct" framing
  `SETTINGS-EDITOR-SPEC.md` §1 already argues for, just without the job-queue machinery that spec
  assumes exists.

### B.3 Field names, ranges, validation, `league_id`

Traced directly from `src/league_config.py` (`LeagueConfig.validate()`) and
`src/league_builder.py`:

| Field | Type / range | Enforced where | Notes |
|---|---|---|---|
| `name` | non-empty string | `slugify()` raises on no usable chars | drives `league_id` |
| `league_id` | derived slug of `name`, disambiguated with `_2`, `_3`, ... on collision | `unique_league_id()` | **reserved word `primary` is rejected** (`ValueError`) — the screen must block a name that slugifies to exactly `primary` |
| `teams` | int > 0 | `validate()` | no upper bound enforced in code; a sane UI ceiling (e.g. 20) should exist but isn't a backend constraint |
| `starters` | dict of `{position: int}`, positions restricted to `QB,RB,WR,TE,K,DEF` | `validate()` rejects unknown positions | K/DEF accepted as roster slots but **produce no ranked board rows** (`ReplacementLevels.SCOREABLE_POSITIONS` excludes them, ADR-039) — the screen should say this explicitly for any league with K/DEF starters, not let the founder infer it from an absent section |
| `flex_slots` | int ≥ 0 | not independently bounded | |
| `flex_eligible` | tuple of positions, each **must already be in `starters`** | `validate()` | e.g. adding `TE` to flex when there's no `TE` starter slot is rejected |
| `bench`, `ir` | int ≥ 0 | not independently bounded | |
| `user_draft_slot` | int in `[1, teams]` | `validate()` | |
| `platform` | one of `yahoo, espn, sleeper, mfl, other` | `validate()` | metadata only, no live adapter (`league_config.py` docstring, unchanged this pass) |
| `draft_type` | `snake` or `auction` | `validate()` | |
| `ppr` (reception value) | float, no bound enforced | passed straight into `scoring.receptions` | |
| `scoring_overrides` | dict, keys restricted to `scoring.LEAGUE["offense"]` keys | `build_scoring()` checks key membership **only** | **shape of nested values (bonus lists, tiers) is NOT validated** — this session's crash (§Challenge 1) is the concrete proof. A settings screen (or a thin validation layer in front of `create_league`) must enforce: bonus values are `[[threshold:number, bonus:number], ...]` pairs, not objects, before calling this function, or route through a schema that normalizes object-shaped input to tuples before it reaches `scoring.py` |
| `flex_split` | optional dict `{position: float}`, positions ⊆ `flex_eligible` | `validate()` checks membership only, **not that values sum to ≤ 1 or are non-negative** | leave unset for any new league — see `create_league()`'s own docstring; do not let a settings screen invent a measured-looking split for an unmeasured league |
| `playoff_teams`, `playoff_weeks`, `reseeding`, `trade_deadline`, `faab_budget` | as typed | no cross-field validation | |

**Where a new league is stored:** `data/leagues/<league_id>.json` (via `LeagueConfig.save()`), export
directory `data/export/<league_id>/` (via `export_dir_for()`). Both are filesystem paths in this
repo today — there is no database row, no multi-tenant storage, consistent with `CLAUDE.md` §1's
"single user, local only" current scope.

---

## C. What "two hardwired" leagues need that presets do not — and the FR-042 correction

**Confirmed, then superseded mid-session.** Read `src/generate_config_matrix.py` directly (not the
docstring alone): all 24 presets are `copy.deepcopy(scoring.LEAGUE)` with only `receptions` swapped
(`generate_config_matrix.py:71-74`) — Westwood's stacking +1/+1.5/+2 yardage bonuses, TD values,
interception value, and defensive scoring are identical across all 24. **This is exactly what
`docs/founder-requests/FR-042-presets-must-use-standard-scoring-only-westwood.md` just ruled
incorrect** — the founder's own words: *"All the other pre sets should be standard scoring (with
different PPR) not Westwood custom. Only Westwood should have the custom."* FR-042 is a decision,
already recorded, not re-litigated here.

**Docstring self-contradiction, resolved as asked.** `generate_config_matrix.py:6-11` claims the
ruleset *"happens to match ESPN's confirmed platform defaults exactly."* The same file, twelve lines
later (`:52-53`), and `docs/decisions.md`'s ADR-047 entry itself (`ESPN ... scoring unverified —
bot detection blocked the fetch`) both say ESPN scoring was never confirmed. **These cannot both be
true, and the correct one, as best this pass can determine, is "unverified."** No citation, research
doc, or fetched source anywhere in the repo supports the "confirmed exact match" claim — it appears
to have been written as an assumption that got restated with false confidence twelve lines after the
file's own more careful sentence. Recommend: correct both the docstring and the ADR-047 entry itself
the next time either is touched (out of this pass's scope to edit — `docs/decisions.md` is an
append-only log, corrections go in a new entry, not an edit to the old one).

**What this changes for FR-040's sequencing — the single most important point in this document, per
the coordinator's flag.** A custom-league builder must **not** start from `scoring.LEAGUE`
(Westwood's ruleset) as its base and rely on the caller remembering to override every bonus field.
`league_builder.build_scoring()` does exactly that today (§Challenge 1) — it is the same defect
class FR-042 just corrected in the preset matrix, sitting undetected in the one function every
future custom league will go through. **Fixing `generate_config_matrix.py` alone (FR-042's literal
ask) without also fixing `league_builder.build_scoring()`'s default base ruleset reintroduces the
identical bug the moment the custom-league screen ships**, just through a different entry point.
Recommend whichever chain implements FR-042 also correct `build_scoring()`'s base — starting it from
an explicit "standard" ruleset (25 yd/pt passing, 4 pt passing TD, −2 INT, 10 yd/pt rushing/
receiving, 6 pt TD, −2 fumble, **no yardage bonuses**, per FR-042's own definition) with Westwood's
full ruleset reachable only via the reserved `primary` path, never as a silent default for a new
league. Not fixed in this pass — flagged, per the run constraints (no contract bump, spec/costing
only), and because a second backend agent is working in a separate worktree this session and this
file must not collide with FR-042 implementation work already possibly underway there.

**Two structurally separate tracks, confirmed as the right shape by everything found this session:**
Westwood keeps the full custom ruleset (verified against the live platform, ADR-052) and the only
opponent modelling this project has any data to support (`opponents.json`'s two known-opponent
entries — genuinely thin, and honestly stated as such in `export_static.py`'s own docstring). Every
other league — presets and the FR-040 custom builder alike — gets standard scoring (PPR-only
variation) and no opponent modelling, because there is no data to model strangers from. This doc's
findings support exactly that split: the "custom" screen only needs to expose the FR-042 "standard"
base plus scoring dimensions, never Westwood's bonus structure as an implicit default.

---

## Summary table

| Claim | Verdict | Evidence |
|---|---|---|
| Backend exists for arbitrary custom leagues | **Mostly true** — real gaps in shape validation and default-ruleset base | Live run, 2 defects found |
| Produces `availability.json`/`strategies.json` real vs. stub | **Confirmed stub/absent**, same as config matrix | Live run |
| Handles TD-value/bonus overrides | **Yes, mechanically**, once bonus shape is corrected | Live run (crashed, then succeeded) |
| Team count/roster/slot/playoffs client-recomputable | **True for the currently-exported config; not true for an arbitrary new one** without `flex_split`, which isn't exported | Source trace + live export dump |
| Scoring client-recomputable | **False, confirmed** — no components anywhere in the contract, and none exist internally to export | Full player-row dump + source trace |
| Component projections exist internally | **No** — single rank-curve, not per-stat | `make_board.py` source trace |
| 24 presets vary reception value only | **True, and just overridden by founder decision (FR-042)** | Source read, cross-checked against FR-042 |
| ESPN bonus structure "confirmed" match | **Unsupported claim** — the file's own later text and ADR-047 both say unverified | Source + decisions log |

## No contract version bump, no code changes made

Per this run's explicit constraint. `src/export_contract.py` was read only. The `flex_split`
export gap (§Challenge 2, §B.1) and the shape-validation/default-ruleset bugs in
`league_builder.py` (§Challenge 1, §C) are findings, not fixes applied here.
