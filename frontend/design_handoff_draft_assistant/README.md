# Handoff: Fantasy Football Draft Assistant — backend integration

## Overview
An interactive draft tool for a single user in one 10-team, half-PPR, no-kicker league (user drafts 3rd).
Two modes: **Prep** (Board, Availability Explorer, Opponents, Strategy Guide, Methodology) and **Draft**
(one dense screen: command bar, available players, recommendation, roster + log).

The prototype is feature-complete on the front end and runs entirely on in-memory sample data.
This document is the contract for replacing that sample data with a real backend.

## About the design files
`Draft Assistant.dc.html` in this folder is a **design reference** — a working HTML prototype showing
intended look and behaviour. It is not production code to copy. Recreate it in the target codebase's
environment (React + TypeScript is the natural fit; the prototype is React-shaped already) using that
project's established patterns. All layout is inline-styled by design; move it to the codebase's styling
system.

## Fidelity
**High fidelity.** Colours, type, density, spacing and interactions are final. Everything below the
"Design tokens" heading should be reproduced exactly.

---

# What the backend needs to provide

## 1. Player board — `GET /api/board?leagueId=…`
The single most important payload. One row per player (~378 in production; 70 in the prototype).

```json
{
  "generated_at": "2026-07-22T14:03:00Z",
  "consensus_source": "blend:4",
  "consensus_state": "preseason_moving",
  "replacement_levels": { "RB": 28, "WR": 41, "TE": 11, "QB": 10, "DEF": 10 },
  "players": [
    {
      "id": 1,
      "overall_rank": 1,
      "player": "Bijan Robinson",
      "position": "RB",
      "positional_rank": 1,
      "team": "ATL",
      "bye_week": 5,
      "projected_points": 168.5,
      "ci_low": 120.3,
      "ci_high": 210.7,
      "vbd": 84.2,
      "consensus_rank": 2,
      "delta_vs_consensus": 1,
      "tier": 1,
      "structural_adjustment": 6,
      "evaluative_adjustment": 2,
      "availability": { "3": 0.42, "18": 0.01, "23": 0.0 }
    }
  ]
}
```

Hard requirements learned from building the UI:

- **The attribution must be exactly additive.** The panel renders
  `consensus_rank − structural_adjustment − evaluative_adjustment = overall_rank`.
  If the three numbers don't reconcile, the differentiating feature reads as broken. Reconcile server-side.
- `consensus_rank` must be unique across players. Ties break the sort and the delta column.
- `delta_vs_consensus = consensus_rank − overall_rank` (positive = we like him more than the market).
- `tier` is per position. The board also renders **global tiers** for the "All" view — the prototype
  computes those client-side from VBD gaps (new tier when the drop between consecutive players exceeds
  ~4.5 points of value, max 9 per tier). Either send `global_tier` or keep computing it client-side.
- `ci_low`/`ci_high` are required wherever a projection appears. Never ship a projection without them.

## 2. Availability — `GET /api/availability?leagueId=…&scenario=…`
The product's unique capability, and the thing that must be correct.

```json
{
  "scenario": "repeat_2025",
  "valid_for": { "teams": 10, "draft_slot": 3, "manager_set_hash": "…" },
  "picks": [3, 18, 23, 38, 43, 58, 63],
  "noise_band": 0.08,
  "players": { "12": { "23": 0.34, "38": 0.02 } },
  "tier_summary": { "TE": { "tier": 1, "23": 0.34, "18": 0.61 } }
}
```

- Three scenarios must be addressable by name: `repeat_2025`, `half_repeat`, `no_repeat`.
- **Availability must be conditional on the live draft state**, not static. The prototype recomputes from
  a per-pick hazard model as picks are marked, and every figure in the UI (rows, watchlist, "if you wait",
  explorer, player panel) reads from the same function. Two options:
  1. `POST /api/availability` with the current list of taken player ids and the current overall pick,
     returning updated probabilities. Needs to answer in **under ~150 ms** — it is called after every pick.
  2. Return a hazard curve per player (probability he is taken at each remaining pick) and let the client
     do the survival product locally. **This is the recommended shape** — it keeps the draft room instant
     and offline-tolerant, which matters at a draft table.
- `noise_band` drives the "±8 points of probability" copy on the explorer. Send it; don't hardcode it.
- `valid_for` drives invalidation (see §6).

## 3. Opponents — `GET /api/opponents?leagueId=…`
Nine cards plus the user's slot.

```json
{
  "draft_order": ["The Cucked Commish", "Shit Leopards", "Two balls no Kupp", "…"],
  "user_slot": 3,
  "managers": [
    {
      "slot": 2,
      "name": "Shit Leopards",
      "first_pick_by_position": "WR in R1 (2 of 3)",
      "tendencies": "WR-WR opens, reaches TE in R3",
      "consensus_adherence": 0.79,
      "classification": "average",
      "note": "Took Bowers at 3.02 (#22) in 2025 after opening WR-WR…",
      "between_user_picks": true
    }
  ]
}
```
`between_user_picks` drives the highlighted treatment on the managers holding 19–22.
`classification` is one of `sharp | average | disengaged`.

## 4. Strategy results — `GET /api/strategy?leagueId=…`
Everything on the Strategy Guide is a measured result and must be traceable, including the decision rules
shown in the draft room. Same source, two surfaces.

```json
{
  "comparisons": [
    { "strategy": "Elite TE at 23 when available", "roster_points": 1883,
      "delta_vs_baseline": 41, "seasons_positive": "4 of 4", "inside_noise": false }
  ],
  "noise_threshold_points": 25,
  "null_results": [
    { "title": "Spike weeks are not a player trait", "body": "…", "seasons_tested": 26 }
  ],
  "decision_rules": [
    { "id": "qb", "rule": "Don't reach for QB before round 6.",
      "evidence": "…measured cost 115 pts across 4 seasons, 0 of 4 positive.",
      "source_run_id": "sim-2026-07-19-qb" }
  ]
}
```
Rules render with an "evidence" expander and must never be assertable without an evidence string.

## 5. Player profile — `GET /api/players/:id/profile`
Currently generated sample data in the prototype; the layout is final.

```json
{
  "seasons": [ { "year": 2025, "games": 15, "stats": { "TGT": 148, "REC": 99, "YDS": 1326, "TD": 9 } } ],
  "weekly_finishes": [ { "week": 1, "positional_finish": 4 }, { "week": 8, "bye": true } ],
  "consistency_pct": 59,
  "insights": ["…"],
  "notes": []
}
```
- `positional_finish` is the player's rank at his position that week — the heat map colours from it
  against the startable threshold (QB 12, RB 18, WR 24, TE 8, DEF 10). Send the threshold set with the
  league config rather than hardcoding.
- The same endpoint (bulk form, `GET /api/weekly-finishes`) backs the full-screen consistency heat map,
  currently marked coming soon.

## 6. League settings and invalidation — the part most likely to be got wrong

Two tiers, and they must behave differently.

**Tier 1 (instant, no backend call):** teams, starting slots (QB/RB/WR/TE/FLEX/DEF), kicker on/off, bench,
IR, draft slot. These only change *replacement level*, which changes VBD, which changes rank order. The
client already does this arithmetic:
```
replacement(pos) = teams × starters(pos) + round(flex_share(pos) × teams × flex_slots)
flex_share = { RB: 0.40, WR: 0.55, TE: 0.05 }     // reproduces RB28 / WR41 / TE11 / QB10 at defaults
vbd(pos)   = projected_points − (replacement_points(pos) − slope(pos) × (replacement − default_replacement))
slope      = { RB: 1.8, WR: 1.6, TE: 2.2, QB: 3.0, DEF: 1.0 }   // points per rank slot near replacement
```
Keep this client-side — the panel's whole point is that the effect is immediate and visible. What the
backend should supply is the *curve* the slope approximates: projected points at each rank near replacement,
per position, so the recalculation stops being a linear approximation.

**Tier 2 (requires recompute):** PPR value, passing TD, interception, rushing/receiving TD, yardage bonus
thresholds and values. These change projected points for every player.
- `POST /api/recompute { leagueId, scoring }` → job id → poll or stream → new board payload.
- Must never auto-apply. The UI holds edits in a pending state behind an explicit **Recalculate** button
  and shows "results are still the old ones until you recalculate".
- Prototype fakes ~1.5 s. Real target: keep it under ~5 s or send progress.

**Invalidation.** Availability, strategy results and opponent profiles are simulated against *this* league —
10 teams, these nine managers, pick 3. If `teams` or `draft_slot` diverge from the real league, every
availability figure in the app greys out and shows:

> Availability data reflects your actual league (10 teams, pick 3). Reset settings or re-run the simulation.

The client decides this by comparing current settings to `valid_for` on the availability payload. The
backend must send `valid_for`, and must not return stale probabilities as if current. A wrong availability
percentage that looks authoritative at a draft table is worse than showing nothing.

## 7. Draft state — persistence and sync
```
POST /api/draft/pick   { leagueId, overall_pick, player_id }
DELETE /api/draft/pick/:overall_pick        // undo / correct, renumbers subsequent picks
GET  /api/draft/state  → { picks: [{ overall_pick, player_id, team_slot }], watchlist: [id] }
```
- Writes must be **fire-and-forget with optimistic local state**. The command bar targets one second per
  pick for ~157 opponent picks; nothing may block on the network.
- Local storage is the source of truth during a live draft (the prototype persists picks, watchlist,
  theme and settings under one key) and the server is a mirror. On reconnect, last-write-wins per pick
  number is fine for a single user.
- Team-at-pick is derived, not stored: snake order, `round = ceil(pick / teams)`, index reverses on
  even rounds.
- Live league sync (auto-marking picks from Yahoo) is the coming-soon feature this endpoint should
  eventually be fed by; keep manual entry as the permanent fallback.

## 8. Recommendation engine
Currently client-side. It scores each of the top ~26 available players:
```
score = vbd
      + 8   if the position is still an unfilled starting need
      + 18  if tier-1 TE
      − 25  if QB and round < 6            // from the measured rules
      − 40  if DEF and round < 13
      + (1 − P(available at next pick)) × 14 × (need ? 1 : 0.4)
```
Reasons, the "what you give up" comparison and the "if you wait" panel are all generated from that same
set. If this moves server-side, it must return the alternatives and rationale strings together with the
pick so the centre column stays a single render.

## 9. Glossary
Every technical term has a plain-language entry reachable from an info affordance. Keep them in one
source (`GET /api/glossary`) keyed by term id: `avail, vbd, repl, ci, tier, struct, evalv, cons`.
The Methodology screen and the inline popovers render the same records.

---

# Front-end notes the backend work depends on

## State
`screen`, `draft` (mode), `picks[]`, `watchlist[]`, `settings`, `pending` (tier-2 edits), `scenario`,
`detail` (open player), `q`/`sel` (search), `bview` (table vs round grid), `explorerPick`, `theme`.
Persisted: picks, watchlist, settings, theme.

## Performance budget
- Search keystroke → filtered results: synchronous, no network.
- Enter → player marked, board refiltered, availability updated, input cleared and refocused: one frame.
- Anything that touches the network during a live draft must be optimistic.

## Design tokens
```
bg #0a0d12   panel #0f131a   panel2 #151a23   line #222937   line2 #2e3646
txt #e7ecf3  dim #8b95a7     dim2 #5b6474
up  #4cc9f0 (we rank higher) down #f0a35e (lower) acc #7dd3a0 (positive/recommend) live #ff5f56
QB #b39ddb  RB #4dd0b1  WR #f2a65a  TE #6fa8ff  DEF #94a0b0    soon #3b4354
light theme: bg #f3f4f6 panel #fff line #dde1e8 txt #111620 dim #5c6675
```
Type: IBM Plex Sans (UI) / IBM Plex Mono (**all numbers** — tabular alignment is a requirement).
Sizes: 9–11px mono labels, 12.5–13px body, 15px screen titles, 21–26px player names, 40px headline stat.
No border radius anywhere. 1px borders. No gradients or shadows except the side-panel drop shadow.
Colour never carries meaning alone — deltas pair colour with ▲/▼, heat map cells show the finish number.

## Files
- `Draft Assistant.dc.html` — the complete prototype (all screens, all interactions).

## Assets
None. No images or icon files; all glyphs are text characters.


---

# Addendum — open questions for engineering

**Answered (calls taken, design updated to match):** coverage cutoff is now read from
`board.projection_coverage_rank` (no hard-coded 28); availability band width is read from
`availability.noise_band` and described in the UI as measured, not chosen — send the real value;
hazard curves confirmed client-side (Batch A/C), no server round-trip; league comparison starts
empty rather than backfilling projection-at-lock; `roster.player_id = unknown` is a designed
state, not an error.


Written after the design changed: scenarios removed, thresholds corrected, season + manager
views added, one floating assistant replacing the two query surfaces.

## Blocking questions (answers change the design, not just the code)

1. **How many players will actually have projections?** The design now treats "rank but no
   projection" as the default state (~60%). If bottom-up projections eventually cover the whole
   board, several screens (compare, trades, lineup totals) get simpler and less defensive. If
   coverage stays partial, we should agree the cutoff rule and expose it as a field
   (`board.projection_coverage_rank`) rather than hard-coding 28.
2. **Can availability be served as per-pick hazard curves** rather than point probabilities?
   The client needs to recompute after every recorded pick with no network call. Shape:
   `{player_id: [{pick, p_taken}]}`. If it must be a request/response, it has to answer under
   ~150 ms or the command bar stalls.
3. **What is the real noise band on availability?** The UI now reports every probability as a
   range and the width is currently a placeholder function of the midpoint. Send
   `availability.noise_band` (or per-player interval bounds) — the honest width is a modelling
   answer, not a design one.
4. **Do we have per-manager weekly decision data for all ten managers**, including
   projection-at-lock? The league comparison view scores decisions against the pre-game
   projection, which requires storing the projection at the moment lineups locked, not
   recomputing it later. If that snapshot does not exist historically, the comparison view
   starts empty and only fills going forward — worth knowing now.
5. **Rosters beyond our board.** Other managers hold players outside the 70-player board; the UI
   shows those slots as `roster.player_id = unknown`. Is a full league roster feed available
   (names at minimum)? If yes, the sparse treatment shrinks to projections only.

## Requests

- **Named fields for everything on screen.** The constraint we designed to: no rendered value
  without a named backend field, and nulls rendered as nulls. Please keep field names stable —
  they appear in the UI (trace affordances, source lines in the assistant), so renaming a field
  is a visible change, not an internal one.
- **Source metadata on any external content**: `{source_name, url, fetched_at}`. The assistant
  marks anything older than 48 hours in-season as stale and says so; without `fetched_at` it
  cannot make that call and will refuse instead.
- **An offline contract.** Board + simulation data must be usable from cache with no network;
  anything requiring a live fetch should fail loudly rather than serve a stale value silently.
- **Scoring recompute as a job** (`POST /api/recompute` → job id → poll/stream), target under
  5 seconds or send progress. Never auto-apply.
- **`availability.valid_for`** on every availability payload so the client can grey out
  invalidated numbers. This is the one thing that must not be got wrong.

## Things deliberately not built, so nobody builds them by accident

- No scenario switch. Prior-year opponent behaviour is not a model input; it is display context
  on the opponent card.
- No evaluative adjustment. The entire consensus-to-our-rank difference is format arithmetic.
- No archetype in the model. Labels are display-only and UNDETERMINED by default.
- No verdicts the data cannot support: trade grades, keeper value, breakout calls. The assistant
  refuses these by design, and the refusal state is a designed screen, not an error.


---

# Addendum 2 — multi-league, mock lab, inline glossary (added 25 Jul 2026)

Three surfaces exist in the prototype that this document did not previously cover. Each carries new
backend requirements.

## 10. Multiple leagues — `GET /api/leagues`
The app is no longer single-league. The top bar is a league selector; every board, availability,
strategy, mock and draft-state call is scoped by `leagueId`.

```json
{ "leagues": [
  { "id": "lg_dod", "name": "Dynasty of Dorks", "platform": "Sleeper",
    "draft_type": "Snake", "draft_date": "2026-08-30T19:00:00Z",
    "settings": { "teams": 10, "slot": 3, "qb": 1, "rb": 2, "wr": 3, "te": 1, "flex": 2,
                  "def": 1, "k": false, "bench": 6, "ir": 1,
                  "ppr": 0.5, "ptd": 4, "intp": -2, "rtd": 6 },
    "sim_generated_at": "2026-07-19T04:12:00Z",
    "sim_settings_hash": "teams=10·qb=1·…·rtd=6",
    "projections_generated_at": "2026-07-22T06:40:00Z",
    "mocks": 14 } ] }
```

- `platform` ∈ Sleeper | ESPN | Yahoo | NFL.com | Manual. `draft_type` ∈ Snake | Linear |
  3rd-round reversal | Auction. Both are display + future-import metadata today; the mock grid
  currently assumes snake geometry (see open questions).
- `draft_date` is nullable and renders as `league.draft_date = null`, not as a blank.
- Create/edit is client-driven; `POST /api/leagues` and `PATCH /api/leagues/:id` mirror it.
- Draft state, watchlist and mocks are per league. The client keys local storage the same way.
- **Team count is dynamic everywhere.** Nothing may assume 10. The mock board renders
  `teams` columns and `teams × 16` picks; snake order is derived from the league's own
  `teams`, not from the active app setting.

### Invalidation via settings hash — replaces the `valid_for` rule in §6
The client compares three things:
```
hash(current in-app settings)  vs  hash(league.settings)  vs  league.sim_settings_hash
```
- All three equal → availability and strategy render normally (`CURRENT`).
- `sim_settings_hash` differs → `STALE`: numbers grey out app-wide with the reason and the
  timestamp they were generated under. The assistant refuses to quote them.
- `sim_generated_at = null` → `NEVER GENERATED`: availability renders as an explicit null,
  never as 0%.
Send both fields on every league record. Regeneration is `POST /api/simulate { leagueId }`
(~20,000 drafts); the UI shows progress and rewrites both fields on completion.

### Two-tier recompute — revised timing
Tier 1 (slots, roster shape, team count, draft slot) stays instant and client-side, as in §6.
Tier 2 (scoring) is now specified as **~60 s with progress**, not 5 s. The UI:
- holds edits in `pending` and renders a saved-but-not-applied diff (old → new per field),
- shows an app-wide banner while pending or running,
- keeps **every displayed number at its pre-edit value** until the job completes — no partial
  application, no optimistic projections,
- reports the stage string from the job (`re-scoring 378 players under new values`, etc).
Send stage + percent on the poll/stream. `projections_generated_at` updates on completion.

## 11. Mock drafts — `GET /api/mocks?leagueId=…`, `POST /api/mocks/:id/pick`
Mocks are the validation instrument for the availability model. All picks are entered, not just
the user's — opponent picks are the data.

```json
{ "mocks": [ { "id": "mk_014", "league": "lg_dod", "label": "Mock 14",
    "when": "2026-07-24T19:40:00Z", "teams": 10, "slot": 3,
    "picks": 160, "calls": 9, "hits": 6, "brier": 0.121 } ] }
```

Per-pick record — **written at entry time, never recomputed**:
```json
{ "n": 37, "team_slot": 6, "player_id": 112,
  "predicted_top": 98, "predicted_p": 0.41, "in_top_5": true }
```
The prediction must be frozen when the pick is logged; recomputing it later against a changed
board destroys the comparison. The review screen reads exactly these fields, plus
`surprise = board.overall_rank − n`.

Availability calls at the user's picks are scored separately:
```json
{ "pick": 23, "player_id": 44, "predicted_p": 0.34,
  "noise_band": 0.12, "observed_available": false, "taken_at": 19 }
```

Prototype note: per-pick review rows are deterministic sample data derived from the board;
mock summary rows are fixtures. Both are labelled as such in the UI.

## 12. Model validation — `GET /api/validation`
Pooled across all logged mocks in all leagues (stated as such on screen — this measures the
model, not a league).
```json
{ "buckets": [ { "stated_mid": 0.35, "n": 92, "observed": 36 } ],
  "mocks_logged": 7, "mean_brier": 0.155 }
```
Send counts (`n`, `observed`), not percentages — the client computes 95% Wilson intervals and
flags buckets whose stated value falls outside its own interval. Buckets under n = 50 are marked
thin. The screen states plainly that a handful of mocks is not a validation set.

## 13. Glossary — inline layer
`GET /api/glossary` now backs a hover/click affordance anywhere in the app, not only the
Methodology screen. Term ids in use: `avail, vbd, repl, ci, tier, struct, cons, calib, wilson,
surprise, stale, pending`. Each popover offers "Ask the assistant" (sends the term plus the
current screen context) and "Full entry" (Methodology). Terms carry a dotted underline; `?`
chips are used where a label has no natural text to underline.

## Open questions added by this work

6. **Non-snake draft geometry.** The mock entry board is snake-shaped. Linear and 3rd-round
   reversal need different pick-order math; auction needs a different screen entirely (budget,
   nomination order). Which do we support at launch?
7. **Mock storage.** Are mocks stored server-side per league (so validation pools across
   devices), or local-only until the user opts in? Validation is far more useful pooled.
8. **Do platform imports give us opponent picks in mocks?** If Sleeper/ESPN mock rooms can be
   read directly, manual entry becomes a fallback rather than the primary path, and the
   validation set grows much faster.


---

# Addendum 3 — design tokens, live availability, scarcity, queue/watchlist (26 Jul 2026)

Driven by the competitive UX research pass. The visual work is token-level, not structural:
every row that was on screen before is still on screen.

## 14. Design tokens

Two font roles. Humanist sans for names, labels, prose, nav; mono **only** for numeric cells,
with `font-variant-numeric: tabular-nums` scoped to those cells rather than set globally.
Position and team codes (WR1, LV) are labels, not measurements — sans at small size with
`letter-spacing: .045em`, never mono.

```css
--f-ui:  'IBM Plex Sans', system-ui, -apple-system, sans-serif;
--f-num: 'IBM Plex Mono', ui-monospace, monospace;
```

Surfaces are elevation steps, not hairlines. Hairlines remain only where two regions at the
same elevation abut.

| Token | Dark | Light | Role |
|---|---|---|---|
| `--bg` | `#0b0e12` | `#f6f7f9` | canvas (near-black / off-white, never pure) |
| `--panel` | `#12161d` | `#ffffff` | raised surface — cards, rails, table containers |
| `--panel2` | `#181d25` | `#eceff4` | second step: selected rows, header strips, insets |
| `--s3` | `#1e242e` | `#ffffff` | third step, reserved for stacked overlays |
| `--line` | `#20262f` | `#e3e7ed` | hairline |
| `--line2` | `#2c3440` | `#cbd2dc` | emphasis hairline, control borders |
| `--txt` | `#f1f4f8` | `#131821` | primary text |
| `--dim` / `--dim2` | `#98a2b1` / `#69737f` | `#4f5867` / `#79828f` | secondary / tertiary |
| `--acc` | `#5ecf9e` | `#0d8a57` | accent 1 — yours, good, on pace |
| `--down` | `#f0993f` | `#a85c07` | accent 2 — attention, scarcity, stale |
| `--up` | `#5bb4f2` | `#0a6ec2` | semantic positive delta |
| `--live` | `#ff5f56` | `#cf3a30` | live-draft state only |
| `--r-c` / `--r-m` | 6px / 12px | same | chrome radius / overlay radius |

**Light mode is its own design, not an inversion.** Elevation goes *up* toward white (canvas
off-white, surfaces pure white) and every accent carries higher chroma, because light
backgrounds swallow desaturated colour.

**Radius on chrome only.** 6px on cards, buttons, chips, filter pills, table *containers*;
12px on modals and overlays; **0 on data cells and table rows** — square cells keep the grid
scannable. Buttons and inputs get 5px from a base rule.

**Accent discipline.** Two accents plus semantics. Position colours were desaturated so they
read as labels; saturated amber is now reserved for attention and staleness, so it means one
thing again.

**Colourblind safety.** Blue/orange is the primary distinguishing axis, and every
colour-carried meaning has a redundant non-colour cue (the number itself, a ▲/▼ glyph, or a
weight change). Green/red is not used as a good/bad axis.

## 15. Live availability — TWO numbers, never one

**This is a hard requirement. Do not collapse the pair into a single number, and do not let
the adjusted number replace the baseline.** The user must be able to see that the model is
reasoning from tonight's draft rather than from history alone.

`GET /api/availability?leagueId=…&pick=…` per player:

```json
{ "player_id": 44, "pick": 23,
  "baseline_p": 0.34,
  "live_p": 0.28,
  "noise_band": 0.12,
  "signal_strength": "ok",
  "adjustment": { "need": -0.21, "run": -0.34 },
  "run_context": { "position": "WR", "count": 3, "of": 5 },
  "picks_logged": 18, "picks_required": 5 }
```

- `baseline_p` — the marginal survival probability from the simulation. Unchanged by draft state.
- `live_p` — baseline adjusted by roster-need arithmetic over the teams picking between now
  and the user's pick, plus positional-run detection over the last five picks. Applied as a
  shift in log-odds, so it can never leave (0,1).
- `signal_strength` ∈ `none` | `thin` | `ok`:
  - `none` — fewer than `picks_required` (half a round) logged. **`live_p` MUST be null.** The UI
    renders "not yet" with the picks-logged count. It must never fall back to the baseline
    silently, and it must never render `0%`.
  - `thin` — at least half a round but under a full round. `live_p` is returned, the UI marks the
    row thin and widens the band by ×1.6.
  - `ok` — a full round or more.
- `adjustment.need` / `adjustment.run` are returned **separately** — they are shown in the player
  panel and in the board row tooltip. A single combined delta is not sufficient.
- Recompute is client-side per pick; no server round-trip during a draft.

Displayed in three places: the board's availability column (`34% → 28%` compact pair), the
queue rows (baseline, live, signed delta, dot array), and the player panel (full pair with both
adjustment components and the run context).

## 16. Probability as frequency — dot arrays

Every availability probability is paired with a 10-dot discrete visual ("3 in 10 drafts"), per
the 2016 election-needle findings on bare probabilities. Round to the nearest tenth for the dot
fill; do not print more precision than the model supports. Projection CIs now render as a
whisker under the point estimate at true relative width — a rookie's wider interval *is* the
message, so do not normalise it.

## 17. Position scarcity — `GET /api/scarcity?leagueId=…`

```json
{ "positions": [ { "pos": "RB", "total": 22, "remaining": 14, "gone": 8,
    "pace_vs_consensus": 2, "tier1_remaining": 0, "tier2_remaining": 3,
    "under_50pct_by_next_pick": 6, "startable_pool": 30 } ] }
```

Remaining/total, depletion pace against consensus order, tier-1 and tier-2 remaining, and how
many sit under 50% to reach the user's next pick. A depletion warning fires when every
remaining tier-1 player at a position is under 50% to survive — that is the only urgency claim
we make, and it is derived, not editorial.

## 18. Queue and watchlist are TWO objects

Currently conflated in the client; split them server-side too.

- `draft.queue[]` — **draft-scoped and self-pruning.** A queued player is removed the moment
  anyone drafts him; there is no dead-pick state and no error to clear. Resets with the draft.
- `account.watchlist[]` — **account-wide.** Persists across seasons and leagues, carries no draft
  state, and shows a per-league "drafted / available" annotation rather than disappearing.

Both are user-visible as field names via trace affordances.

## 19. Sparse data

Consecutive empty sections collapse into **one** line naming everything missing at once
("No archetype, notes or news for Brock yet — one season of usage on file, and the news feed
isn't connected"). Three stacked empty headers read as broken rather than candid.
`0%` must never render where the claim is "not computed": availability under 0.5% renders
`<1%`, and an uncomputed value renders `—` with the reason on hover.

## 20. Glossary

`GET /api/glossary` gains a `category` per term (`prob` | `value` | `draft` | `state`) and a
`field` naming the backend field it describes. The Glossary is now its own nav destination
grouped by category; the inline hover layer is unchanged and carries "Ask the assistant".

## Open questions added by this round

9. **Where does the live adjustment run?** The client can recompute per pick from state it
   already has, which is what the prototype does. If the model gets heavier than log-odds
   shifts, it needs a server endpoint — and then it needs a latency budget under a pick clock.
10. **Are `adjustment.need` and `adjustment.run` the final decomposition?** If the Strategist adds
    a third signal, the UI shows components individually and will need a design decision at
    four or more.
11. **Does the watchlist need per-league annotations server-side**, or does the client join
    `account.watchlist[]` against the active league's draft state?


## 21. Player panel — anatomy and new fields

Now a **right side sheet (~440px) with no backdrop**: the board and the pick clock stay visible,
per the research's point that losing sight of the board to read a player is a real cost under a
clock. Order is fixed and deliberate:

1. **Identity strip** — headshot, team-colour chip, POS rank, bye, our rank, tier.
2. **Verdict line** — one sentence, generated (below).
3. **Number block** — projection with a visible interval, VBD.
4. **Availability** — baseline → live pair, dot array, both adjustment components.
5. **Why our rank differs** — moved *below* the numbers; also now inline on the board row.
6. Archetype as a display-only pill, 7. weekly finishes, 8. three-season table, 9. takeaways.
10. **Sticky action bar** — Mark taken (accent fill), Add to queue, Watchlist, Compare, Ask.

### New fields
```json
{ "player_id": 44,
  "headshot_url": "https://a.espncdn.com/i/headshots/nfl/players/full/<espn_id>.png",
  "team_color": "#fb4f14" }
```
- `profile.headshot_url` — nullable, hotlinked, **URL only, never cached or re-hosted**. Source is
  the nflverse roster join (ESPN CDN). Private use only for now; revisit before any public launch.
  **Not populated in the prototype** — no player in the sample board has a real ESPN id and we do
  not invent them, so every card renders the null state: initials on the team colour. Wire the
  nflverse join and the images appear with no UI change.
- Team colours ship client-side as a 32-team map keyed by team abbreviation. Used as a chip and
  as the initials background only — never as a data colour, so it cannot collide with the accents.

### The verdict line is generated, not written
Assembled from measured fields in a fixed order, so it works for all 378 players with no copy:
`board.position_tier` (position within tier and how many remain) → `availability.live_p` (with the
frequency phrasing) → `board.vbd` (gap to the next player at the position). Null-safe: no
projection yields "no projection, so this is a rank-and-availability call only"; stale
availability yields "availability is stale for this league, so waiting is unpriced". No adjectives,
no ranking language, nothing that isn't arithmetic on a named field.

## 22. Inline rank derivation on the board row

"Why our rank differs" is no longer modal-only. Each board row's delta cell carries a `why`
toggle that expands the derivation in place — replacement level, roster shape, kicker — each with
its value and backing field. Same data as the panel section; no extra endpoint.

## 23. Prose screens

Strategy Guide and Methodology were re-laid-out, not rewritten. Both open with a raised hero band
(eyebrow, title, measured-facts strip). Methodology is now the methodology — a four-step pipeline
(consensus → format correction → projection+interval → VBD/tiers, each with its field), an
is/is-not-an-input pair, and limitations as severity-chipped cards; the flat term dump moved to
the Glossary. Section headings carry an accent rule.
