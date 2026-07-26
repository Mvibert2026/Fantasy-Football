# Draft Assistant — Front-End Implementation Spec
**Version:** 1.0 · **Date:** 26 July 2026 · **Source of truth:** `Draft Assistant.dc.html` in this bundle

This file is self-contained. It is written so a front-end implementation can reproduce the
prototype exactly without reading the prototype's source. Where a formula or a constant appears
below, it is the one the prototype runs — not an approximation.

**Read order:** §1 principles (they constrain everything) → §2 tokens → §3 geometry → §4 state →
§5 formulas → §6 API → §7 screens → §8 null states → §9 acceptance checklist.

---

# 1. Non-negotiable principles

These four rules produced most of the design decisions below. Breaking one silently is worse than
shipping the screen late.

1. **No rendered value without a named backend field behind it.** Every number on screen traces to
   a field in §6. Field names are user-visible via trace affordances, so **renaming a field is a
   product change**, not an internal refactor.
2. **Any registered null must be displayable as an explicit null.** `0%`, `0`, `—` and "not
   computed" are four different claims. Never substitute one for another. Never fall back to a
   different number to avoid an empty cell.
3. **Never part-apply a recompute.** While a scoring recompute is in flight, every displayed number
   stays at its pre-edit value. A half-updated board is worse than an old one.
4. **Density is the product.** Premium here means better-organised, not roomier. Do not raise font
   sizes or add whitespace to "modernise" — the reference failure case (ESPN 2025) did exactly that
   and users experienced it as losing information per screen.

---

# 2. Design tokens

## 2.1 Type — exactly two roles

```css
--f-ui:  'IBM Plex Sans', system-ui, -apple-system, sans-serif;
--f-num: 'IBM Plex Mono', ui-monospace, monospace;
```

Load IBM Plex Sans 400/500/600/700 and IBM Plex Mono 400/500/600.

| Use | Font | Notes |
|---|---|---|
| Player names, prose, nav, buttons, labels, section headings | `--f-ui` | |
| Every numeric cell: projections, CI bounds, VBD, ranks, percentages, byes, counts, timestamps | `--f-num` + `font-variant-numeric: tabular-nums` | tabular figures **scoped to the cell**, never set globally — proportional figures read better inside prose |
| Position and team codes (WR1, LV, BUF) | `--f-ui`, small, `letter-spacing:.045em` | **They are labels, not measurements.** Mono here is what made the board read as a terminal dump |
| Eyebrow labels (SECTION HEADERS, ALL CAPS) | `--f-ui`, 9–11px, `letter-spacing:.10–.14em` | |
| Field-name provenance strings | `--f-num`, 9–10px, `--dim2` | e.g. `board.projected_points · ci_low · ci_high` |

**Hierarchy comes from weight and colour, not size.** Player name 600 at 13–14px; secondary
metadata 400 at 10–12px in `--dim`/`--dim2`; numbers 400–600.

## 2.2 Colour

Dark is the designed default. Light is **its own design, not an inversion** — elevation goes *up*
toward white and accents carry higher chroma, because light backgrounds swallow desaturated colour.

| Token | Dark | Light | Role |
|---|---|---|---|
| `--bg` | `#090c10` | `#f4f6f8` | canvas — near-black / off-white, never pure |
| `--panel` | `#14191f` | `#ffffff` | elevation 1: cards, rails, table containers, sheets |
| `--panel2` | `#1c222a` | `#eaeef3` | elevation 2: selected rows, header strips, insets |
| `--s3` | `#232a33` | `#ffffff` | elevation 3: stacked overlays |
| `--line` | `#232a33` | `#e1e6ec` | hairline |
| `--line2` | `#323a45` | `#c7cfda` | emphasis hairline, control border |
| `--txt` | `#f1f4f8` | `#131821` | primary text |
| `--dim` | `#98a2b1` | `#4f5867` | secondary text |
| `--dim2` | `#69737f` | `#79828f` | tertiary text, provenance |
| `--acc` | `#5ecf9e` | `#0d8a57` | **accent 1** — yours / good / on pace / primary action |
| `--down` | `#f0993f` | `#a85c07` | **accent 2** — attention / scarcity / stale / pending |
| `--up` | `#5bb4f2` | `#0a6ec2` | positive delta (semantic only) |
| `--live` | `#ff5f56` | `#cf3a30` | live-draft state **only** |
| `--qb` | `#9d93c4` | `#5b3ab0` | position label |
| `--rb` | `#63b39b` | `#07715c` | position label |
| `--wr` | `#c39468` | `#8f5205` | position label |
| `--te` | `#7d9fcf` | `#1a55b5` | position label |
| `--def` | `#8b939f` | `#525c6b` | position label |
| `--soon` | `#39414e` | `#c8cfda` | not-yet-built affordances |
| `--sh` | `0 1px 0 rgba(255,255,255,.03), 0 10px 28px rgba(0,0,0,.38)` | `0 1px 2px rgba(16,22,32,.07), 0 6px 18px rgba(16,22,32,.06)` | card shadow |

**Rules that matter more than the hex values:**
- Elevation via lightness steps, not borders. Keep a hairline **only where two regions at the same
  elevation abut**.
- **Two accents plus semantics, and they are reserved.** Position colours are deliberately
  desaturated so they read as labels; saturated amber (`--down`) means attention or staleness and
  nothing else. If amber starts appearing on five unrelated things, it means nothing.
- Blue/orange is the primary distinguishing axis. **Green/red is never a good/bad axis.**
- **Every colour-carried meaning needs a redundant non-colour cue** — the number in the cell, a
  ▲/▼ glyph, a weight change, or a rule. Example: heatmap cells below a player's startable line
  carry a 2px bottom rule in `--down`, not just a hue shift.
- Team colours (§6.9) are used **only** for the identity chip and the initials background. They are
  never a data colour, so they cannot collide with the accents.

## 2.3 Radius — chrome only

```css
--r-c: 6px;   /* cards, buttons, chips, filter pills, table CONTAINERS, inputs (5px) */
--r-m: 12px;  /* modals, overlays, popovers, the assistant dock */
```

**Zero radius on data cells and table rows.** Square cells preserve grid legibility; radius on the
chrome is what signals modern. Pills that are genuinely pill-shaped (archetype labels, severity
chips) use `999px`.

Base rules: `button{border-radius:5px}`, `input,select,textarea{border-radius:5px}`.

## 2.4 Density

| Property | Value |
|---|---|
| Row height, data tables | 28–34px |
| Horizontal gap between numeric columns | 10–14px |
| Vertical padding in rows | 6–8px |
| Row separation | low-contrast hairline; **no zebra striping** |
| Tier grouping | tier header gets a surface lift + player count; the tier is the visual unit |
| Number alignment | numerics right-aligned, text left-aligned, CI bounds right-align on the closing paren |
| Sticky headers | required on any table taller than the viewport, and applied **consistently** |
| Bars/meters | always paired with the number; always render a faint track so an empty bar ≠ a missing bar |

---

# 3. Layout geometry

## 3.1 Shell

```
┌───────────────────────────────────────────────────────────────────┐
│ top bar · 46px · --panel · hairline bottom                        │
│ [logo] [DRAFT LIVE?] ......... [league selector] [settings] [☾/☀] │
│                                          [Prep | Draft | Season]  │
├──────────┬────────────────────────────────────────────────────────┤
│ nav rail │ screen area (flex:1, min-height:0, own scroll)          │
│ 216px    │                                                        │
│ (hidden  │                                                        │
│ in Draft)│                                                        │
└──────────┴────────────────────────────────────────────────────────┘
```

- Pending-recompute banner, when active, sits **between** the top bar and the body, full width,
  `--down` border, clickable to open League settings.
- Nav rail is hidden in Draft mode (the draft hub tabs replace it).

## 3.2 Draft room — three panes

`grid-template-columns` computed from props, normalised to 100%:

```js
board  = clamp(props.boardPaneWidth  ?? 35, 20, 60)
center = clamp(props.centerPaneWidth ?? 40, 20, 65)
right  = max(14, 100 - board - center)
total  = board + center + right
// each column: minmax(0, <value/total*100>%)
```

**When the draft hub tab is not `board`,** the first column widens by taking 42% of the centre
pane's share (`wide = board + center*0.42`, `mid = center*0.58`) so the opponents grid and the
predictions table have room. The right roster rail never changes width.

Pane 1 must carry `min-width:0; overflow:hidden` — its header rows contain intrinsically-sized
children and will otherwise paint outside the pane.

| Pane | Contents |
|---|---|
| 1 · Board hub | Tab bar (Board / Opponents / Predictions), then the tab body |
| 2 · Centre rail | On the clock: recommendation card, alternatives, "if you wait" table. Off the clock: position scarcity, queue/watchlist tabs, next decision, decision rules |
| 3 · Roster rail | Slot chips (QB 0/1 …), my roster slot list, bye warnings |

## 3.3 Overlays

| Surface | Geometry |
|---|---|
| Player side sheet | `position:fixed; top:0; right:0; bottom:0`; width `props.detailWidth ?? 440` (min 420); `max-width:96vw`; z-index 90; **transparent click-catcher at z-index 80 — no dark scrim.** The board and pick clock must stay visible |
| Sticky action bar | inside the sheet, `position:sticky; bottom:0`, `--panel` background, top hairline, upward shadow |
| League settings drawer | right drawer, 620px, dark scrim at z-index 95 (this one *is* modal) |
| Assistant dock | `position:fixed`, bottom-right, width `props.assistantWidth ?? 430`, max-height `props.assistantHeight ?? 72`vh, z-index 86, radius `--r-m`. Collapsed by default in Draft mode |
| Glossary popover | `position:fixed` at the trigger's `bottom+8`, left clamped to `[12, viewport-352]`, width 340px, z-index 120 |

## 3.4 Tweakable props (host-exposed)

```json
{"boardPaneWidth":{"editor":"range","default":35,"min":20,"max":55,"step":1,"unit":"%","section":"Draft panes"},
 "centerPaneWidth":{"editor":"range","default":40,"min":20,"max":60,"step":1,"unit":"%","section":"Draft panes"},
 "detailWidth":{"editor":"range","default":440,"min":420,"max":1000,"step":20,"unit":"px","section":"Popouts"},
 "assistantWidth":{"editor":"range","default":430,"min":340,"max":760,"step":10,"unit":"px","section":"Popouts"},
 "assistantHeight":{"editor":"range","default":72,"min":40,"max":92,"step":2,"unit":"vh","section":"Popouts"}}
```

---

# 4. Client state

```ts
type State = {
  // navigation
  mode: 'prep' | 'draft' | 'season';
  screen: 'board'|'explorer'|'opponents'|'strategy'|'method'|'glossary'
        | 'mock'|'mockreview'|'validation'
        | 'lineup'|'consistency'|'waivers'|'decisions'|'trades'|'league'|'writeup'
        | 'sync'|'bottomup'|'news'|'inseason'|'startability';   // 'coming soon' screens
  draft: boolean;              // draft mode active
  dtab: 'board'|'opponents'|'predict';
  railTab: 'queue'|'watch';
  theme: 'dark'|'light';

  // leagues
  leagues: League[];
  leagueId: string;
  leagueMenu: boolean;
  settings: LeagueSettings;    // live, may differ from leagues[i].settings
  pending: LeagueSettings;     // scoring edits held here until recompute
  dirty: boolean;              // scoring edited, not applied
  recomputing: boolean;
  recalcPct: number; recalcT: number;
  simRun: { pct: number } | null;

  // draft
  picks: { n: number; pid: number }[];      // append-only, undoable
  picksByLeague: Record<string, Pick[]>;    // preserved across league switches
  queue: number[];                          // draft-scoped, self-pruning
  watch: number[];                          // account-wide
  cmp: number[];                            // compare tray, max 3
  detail: number | null;                    // open player id
  bexp: number | null;                      // board row with derivation expanded
  q: string; sel: number;                   // pick-entry search

  // mock lab
  mockPicks: MockPick[]; mockQ: string; mockSel: number;
  mockId: string; mockRound: number;

  // misc
  tip: { k: string; x: number; y: number } | null;
  trace: TracePayload | null;
  manager: number;             // season view: which of the N managers
  filled: boolean;             // prototype-only: example vs empty content
};
```

## 4.1 Persistence

`localStorage` key `ffda_v6`, versioned and seed-guarded:

```json
{ "v": 6, "seed": "<hash of the shipped league seed>",
  "picks": [], "watch": [], "theme": "dark", "settings": {},
  "leagueId": "lg_dod", "leagues": [], "picksByLeague": {} }
```

On load: **if `v` or `seed` does not match the shipped build, discard the stored state entirely and
re-seed.** Never merge a stale payload — that produces a UI claiming CURRENT while showing numbers
generated under different settings. Never clear storage keys you did not write.

## 4.2 Draft mechanics

```js
teamAt(n)     // 0-indexed slot on the clock at overall pick n, snake order
  const rd = Math.ceil(n / teams), i = (n - 1) % teams;
  return rd % 2 ? i : teams - 1 - i;

userPicks()   // every overall pick the user owns, rounds 1..17
  for (r = 1; r <= 17; r++)
    out.push(r % 2 ? teams*(r-1) + slot : teams*(r-1) + (teams - slot + 1));

cur()         // current overall pick = picks.length + 1
nextUser()    // first userPicks() value >= cur(), else null
```

**Roster slot order** (used for the roster rail and opponent cards):
`QB×qb, RB×rb, WR×wr, TE×te, FLEX×flex, DEF×def, K×(k?1:0)`, then bench.
FLEX eligibility = `RB | WR | TE`. A drafted player fills exactly one slot; fill in the order above.

---

# 5. Formulas

Implement these exactly. They are what the displayed numbers mean.

## 5.1 Settings hash (drives every staleness check)

```js
hashOf(s) = ['teams','qb','rb','wr','te','flex','def','k','bench','ir','slot',
             'ppr','ptd','intp','rtd'].map(k => k + '=' + s[k]).join('·')
```

Compare three values: `hash(live settings)` vs `hash(league.settings)` vs `league.sim_settings_hash`.

| Condition | State | UI |
|---|---|---|
| all three equal | `CURRENT` | availability and strategy render normally |
| `sim_settings_hash` differs | `STALE` | numbers grey out app-wide with the reason and the timestamp they were generated under; the assistant refuses to quote them |
| `sim_generated_at == null` | `NEVER GENERATED` | availability renders as an explicit null, **never 0%** |

## 5.2 Live availability — the two-number model

```js
FLAT = 0.2                                   // flat share per position group
minPicks = max(4, round(teams * 0.5))        // half a round

between = [teamAt(cur), ..., teamAt(pick-1)] // teams picking before your turn
if (between.length === 0 || picksLogged < minPicks)
  return { base, live: null, signal: 'none' }   // EXPLICIT NULL — do not fall back to base

// roster-need demand over the intervening teams
demand = Σ over between: needs.total ? (needs.gap[pos] / needs.total) : FLAT

// positional run over the last five picks
recent = last 5 drafted players
runN   = count(recent where pos === player.pos)
runZ   = recent.length >= 3 ? (runN / recent.length - FLAT) : 0

needZ   = (demand - between.length * FLAT) / max(1, sqrt(between.length))
needAdj = -0.62 * needZ
runAdj  = -1.25 * runZ

live = clamp(sigmoid(logit(base) + needAdj + runAdj), 0.01, 0.99)

signal = picksLogged < teams ? 'thin' : 'ok'
```

`logit(v) = ln(v/(1-v))` with `v` clamped to `[0.005, 0.995]`; `sigmoid(z) = 1/(1+e^-z)`.

**Roster need** per team:
```js
want = { QB: qb, RB: rb + 1, WR: wr + 1, TE: te, DEF: def }   // +1 on RB/WR absorbs flex
gap[k] = max(0, want[k] - have[k]);  total = Σ gap
```

**Band:** `w = noise_band × (signal === 'thin' ? 1.6 : 1)`; `lo = max(0, v - w)`, `hi = min(1, v + w)`.
`noise_band` is **0.12 in the prototype and is a placeholder** — swap the real bootstrapped width.

**Display contract — this is the requirement, not a preference:**
- Baseline and live are shown **together, always**. The adjusted number never replaces the baseline.
- `adjustment.need` and `adjustment.run` are surfaced **separately** (panel + row tooltip). A single
  combined delta is not sufficient.
- `signal: 'none'` renders "not yet" plus the picks-logged count. `signal: 'thin'` renders the number,
  marks the row thin, and widens the band ×1.6.
- Recompute runs **client-side per pick**. No server round-trip during a draft.

## 5.3 Probability as frequency

```js
dotsFilled = round(p * 10)        // 10 dots, filled = dotsFilled
freqText   = dotsFilled + ' in 10 drafts'
```

Every availability probability carries the dot array. A bare percentage presented alone reads as
decisive — this is the specific failure the product exists to avoid. Do not print more precision
than the model supports.

## 5.4 Wilson score interval (validation buckets)

```js
z = 1.96; p = k / n; d = 1 + z*z/n;
centre = (p + z*z/(2*n)) / d;
half   = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / d;
lo = max(0, centre - half); hi = min(1, centre + half);
```

Send **counts** from the server (`n`, `observed`), never percentages — the client computes the
interval. Flag a bucket when its stated probability falls outside its own interval. Mark buckets
with `n < 50` as thin.

## 5.5 Position scarcity

```js
remaining        = players at pos not yet drafted
gone             = total - remaining
expected         = count(players at pos where consensus_rank < currentPick)
pace             = gone - expected          // + = going faster than the market expects
tier1_remaining  = count(remaining where tier <= 1)
under50_by_next  = count(remaining where avail(p, nextUserPick) < 0.5)
startable_pool   = perPositionStarters × teams
```

Depletion warning fires when `tier1_remaining > 0 && under50_by_next >= tier1_remaining`:
*"All N remaining tier-1 {POS} sit under 50% to reach pick X. If you want one, this is the turn."*
That is the only urgency claim the product makes, and it is derived.

## 5.6 Verdict line (generated, never written)

Three clauses in fixed order, joined with ` · ` and closed with a period:

1. **Structure** — position within tier and how many remain:
   `"Top of tier 1 at QB, 3 in the tier"` / `"Last of 3 in tier 2 at WR"` /
   `"2 of 4 in tier 2 at RB"` / `"The only TE left in tier 1"`
2. **Cost of waiting** — `live_p` with the frequency phrasing:
   `"48% to reach your pick at 23 (5 in 10 drafts)"`
   → if `live_p == null`: `"34% to reach your pick at 23 on the baseline, with no live adjustment yet"`
   → if stale: `"availability is stale for this league, so waiting is unpriced"`
3. **Value over the alternative** — VBD gap to the next player at the position:
   `"12 VBD points clear of Jackson, the next QB on the board"`
   → if no projection: `"no projection, so this is a rank-and-availability call only"`

No adjectives, no ranking language, nothing that is not arithmetic on a named field. It must work
for all ~378 players with zero hand-written copy.

## 5.7 Two-tier recompute

| Tier | Trigger | Behaviour |
|---|---|---|
| 1 | slots, roster shape, team count, draft slot | **instant, client-side.** No job, no spinner |
| 2 | any scoring value (`ppr`, `ptd`, `intp`, `rtd`) | explicit **Recalculate** required; ~60s job |

Tier-2 UI: hold edits in `pending`; show a saved-but-not-applied diff (old → new per field); show an
app-wide banner while pending or running; **keep every displayed number at its pre-edit value until
the job completes**; report the server's stage string and percent. Stage strings in the prototype:

`reading game logs · 2023–2025` → `re-scoring 378 players under new values` →
`refitting replacement levels` → `rebuilding tiers and VBD` → `writing board.projected_points`

On completion, update `projections_generated_at`. Availability/strategy regeneration is a **separate**
job (`POST /api/simulate`, ~20,000 drafts) that rewrites `sim_generated_at` and `sim_settings_hash`.

---

# 6. API contract

REST, JSON, all league-scoped calls take `leagueId`. Every field named here appears on screen
somewhere, so treat the names as public.

## 6.1 `GET /api/leagues`

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

`platform` ∈ `Sleeper|ESPN|Yahoo|NFL.com|Manual` · `draft_type` ∈ `Snake|Linear|3rd-round reversal|Auction`
`draft_date` is nullable and renders as `league.draft_date = null`, never blank.
`POST /api/leagues`, `PATCH /api/leagues/:id` mirror the shape. Draft state, queue and mocks are
per-league. **Nothing may assume 10 teams** — team count is dynamic everywhere.

## 6.2 `GET /api/board?leagueId=…`

```json
{ "players": [
  { "player_id": 44, "name": "Ja'Marr Chase", "position": "WR", "team": "CIN", "bye_week": 10,
    "overall_rank": 1, "position_rank": 1, "consensus_rank": 1,
    "position_tier": 1, "global_tier": 1,
    "projected_points": 262, "ci_low": 205, "ci_high": 315,
    "vbd": 96, "format_correction": 0 } ],
  "projection_coverage_rank": 28,
  "projections_generated_at": "2026-07-22T06:40:00Z",
  "consensus_blended_at": "2026-07-22T00:00:00Z",
  "consensus_sources": 4,
  "players_loaded": 70, "players_total": 378 }
```

`projected_points`, `ci_low`, `ci_high`, `vbd` are **nullable together**. ~60% of the board has a rank
and no projection; that is a designed state. `projection_coverage_rank` is the rank past which
projections stop.

## 6.3 `GET /api/availability?leagueId=…&pick=…`

```json
{ "pick": 23,
  "players": [
   { "player_id": 44,
     "baseline_p": 0.34,
     "live_p": 0.28,
     "noise_band": 0.12,
     "signal_strength": "ok",
     "adjustment": { "need": -0.21, "run": -0.34 },
     "run_context": { "position": "WR", "count": 3, "of": 5 },
     "picks_logged": 18, "picks_required": 5 } ] }
```

`signal_strength` ∈ `none|thin|ok`. **When `none`, `live_p` MUST be `null`.**
Also serve `generated_at` and `model_inputs` for the trace affordance:
`availability.model_inputs = [consensus_rank, teams, draft_slot]` — prior-year manager behaviour is
**not** an input (it was fit, could not be identified, and was retired).

## 6.4 `POST /api/simulate` → `{ leagueId }`

Regenerates availability + strategy (~20,000 drafts). Stream or poll `{ pct }`. On completion,
rewrite `sim_generated_at` and `sim_settings_hash` on the league record.

## 6.5 `GET /api/scarcity?leagueId=…`

```json
{ "positions": [ { "pos": "RB", "total": 22, "remaining": 14, "gone": 8,
    "pace_vs_consensus": 2, "tier1_remaining": 0, "tier2_remaining": 3,
    "under_50pct_by_next_pick": 6, "startable_pool": 30 } ] }
```

## 6.6 Mocks — `GET /api/mocks?leagueId=…`, `POST /api/mocks/:id/pick`

```json
{ "mocks": [ { "id": "mk_014", "league": "lg_dod", "label": "Mock 14",
    "when": "2026-07-24T19:40:00Z", "teams": 10, "slot": 3,
    "picks": 160, "calls": 9, "hits": 6, "brier": 0.121 } ] }
```

Per-pick record — **written at entry time, never recomputed:**

```json
{ "n": 37, "team_slot": 6, "player_id": 112,
  "predicted_top": 98, "predicted_p": 0.41, "in_top_5": true }
```

Recomputing the prediction later against a changed board destroys the comparison. Availability calls
at the user's own picks are scored separately:

```json
{ "pick": 23, "player_id": 44, "predicted_p": 0.34,
  "noise_band": 0.12, "observed_available": false, "taken_at": 19 }
```

Review-screen derived value: `surprise = board.overall_rank − pick.n` (positive = went later than our
board said). It describes the mock; it is not a judgement of the manager.

## 6.7 `GET /api/validation`

```json
{ "buckets": [ { "stated_mid": 0.35, "n": 92, "observed": 36 } ],
  "mocks_logged": 7, "mean_brier": 0.155 }
```

Pooled across all mocks in all leagues — state that on screen; it measures the model, not a league.

## 6.8 `GET /api/glossary`

```json
{ "terms": [ { "id": "avail", "term": "Availability probability", "body": "…",
               "category": "prob", "field": "availability.baseline_p" } ] }
```

`category` ∈ `prob` (probability & uncertainty) | `value` (value & ranking) | `draft` (draft
mechanics) | `state` (data state). Term ids in use: `avail, live, signal, ci, calib, wilson, noise,
vbd, repl, cons, tier, struct, queue, watchlist, run, surprise, slot, stale, pending, nullproj,
coverage`.

## 6.9 Player profile — `GET /api/players/:id`

```json
{ "player_id": 44,
  "headshot_url": "https://a.espncdn.com/i/headshots/nfl/players/full/<espn_id>.png",
  "team_color": "#fb4f14",
  "archetype": null, "archetype_reason": "Rookie or near-rookie — one season of usage is not enough to label a role.",
  "news": [], "weekly_finishes": [], "seasons": [] }
```

- `headshot_url` — **nullable, hotlinked, URL only, never cached or re-hosted.** Source is the
  nflverse roster join (ESPN CDN). **Not populated in the prototype** — no sample player has a real
  ESPN id and we do not invent them, so every card renders the null state (initials on the team
  colour). Wire the join and images appear with no UI change. Private use only as built; licensing
  needs review before any public launch.
- **Implementation note:** do not put the URL in a template-interpolated `src`. Mount the `<img>`
  only when a URL exists, otherwise the browser fetches the literal placeholder string.
- Team colours ship client-side as a 32-team map keyed by abbreviation (ARI `#97233f`, ATL `#a71930`,
  BAL `#241773`, BUF `#00338d`, CAR `#0085ca`, CHI `#0b162a`, CIN `#fb4f14`, CLE `#ff3c00`, DAL
  `#041e42`, DEN `#fb4f14`, DET `#0076b6`, GB `#203731`, HOU `#03202f`, IND `#002c5f`, JAX `#006778`,
  KC `#e31837`, LV `#a5acaf`, LAC `#0080c6`, LAR `#003594`, MIA `#008e97`, MIN `#4f2683`, NE
  `#002244`, NO `#d3bc8d`, NYG `#0b2265`, NYJ `#125740`, PHI `#004c54`, PIT `#ffb612`, SF `#aa0000`,
  SEA `#69be28`, TB `#d50a0a`, TEN `#4b92db`, WAS `#5a1414`).

## 6.10 Queue and watchlist — two distinct objects

| Object | Field | Scope | Behaviour |
|---|---|---|---|
| Queue | `draft.queue[]` | **draft-scoped** | **Self-pruning:** a queued player is removed the moment anyone drafts him. No dead-pick state, no error to clear. Resets with the draft |
| Watchlist | `account.watchlist[]` | **account-wide** | Persists across seasons and leagues. Never disappears; shows a per-league "drafted / available" annotation instead |

Both names are user-visible via trace affordances.

---

# 7. Screen inventory

Every screen below exists in the prototype. `data-screen-label` values match these names.

## 7.1 Draft mode

**Header:** pick-entry search (type a name, ↑↓ to choose, ⏎ to mark taken, esc to clear) · undo
chip (also `U`) · Auto-fill to my pick · ON THE CLOCK / PICKS UNTIL YOU / YOUR NEXT counters.

**Hub tab — Board.** Position filter chips (ALL/QB/RB/WR/TE/DEF), sort row (our rank / consensus /
delta / proj pts), then tier-grouped rows:

```
rank(20) · name(flex, min 52) · POS(30) · TM(22) · Δ+why(24) · base→live(58) · ✕(mark taken)
```

The Δ cell carries a `why` toggle that expands the rank derivation **in place** (replacement level,
roster shape, kicker — each with value and field). This was our strongest differentiator sitting two
clicks deep; it must be one interaction on the row.

**Hub tab — Opponents.** Card per team, `repeat(auto-fill, minmax(232px, 1fr))`: team name, next
pick number, the full slot list with filled/empty state and position colour, starters filled count,
bench count, and "still needs" chips (`QB ×1`) derived from the roster gap.

**Hub tab — Predictions.** The live availability table:
```
player+queue(1.5fr) · POS(46) · BASELINE(64) · LIVE(64) · Δ(44) · IN 10 DRAFTS(108) · RANGE(96)
```
Header states the signal condition in plain language (how many picks logged, whether the adjustment
is live, thin, or not yet computed).

**Centre rail, on the clock:** RECOMMENDED card (name, position, projection with a CI bar, the
reason, Draft button, "what you give up" panel) → ALTERNATIVES → "if you wait" table.

**Centre rail, off the clock:** POSITION SCARCITY (bar per position, remaining/total, pace, tier
line, "N <50% by pick X", depletion warnings, run note) → QUEUE / WATCHLIST tabs → NEXT DECISION →
DECISION RULES.

**Right rail:** slot chips, my roster slot list with bye flags, bye-collision warning.

## 7.2 Player side sheet — fixed order

1. **Identity strip** — headshot (or initials on team colour), name, POS rank, team chip, bye, our
   rank, tier. Sticky at the top of the sheet.
2. **Verdict line** — §5.6. Left accent rule, 14.5px, with the provenance line beneath.
3. **Projection** — point estimate 26px, honest range as a **visual bar with a mid tick**, VBD,
   plain-language gloss. CI weight sits **below** the point estimate, never above.
4. **Availability at your picks** — the baseline→live pair, dot array, frequency phrasing, band, and
   both adjustment components with the run context. Then the per-pick strip for your next 5 picks.
5. **Why our rank differs from the market** — consensus / format correction / our rank, then the
   component breakdown with fields. **Below** the numbers, not above.
6. **Archetype** — display-only pill (`999px`, `--f-ui`, muted) with the disclosure
   *"descriptive · not sortable · not an input to any rank"*.
7. **Weekly finishes** — 18-cell heatmap, gradient over positional finish, **2px bottom rule** on
   cells below that player's startable line (the redundant non-colour cue).
8. **Three-season table** · 9. **Bullet takeaways**
10. **Sticky action bar** — Mark taken (accent fill) · Add to queue · Watchlist · Compare · Ask.

## 7.3 Prep mode

| Screen | Notes |
|---|---|
| **Board** | Full table: RANK · PLAYER · POS · TM · BYE · PROJ (CI) with whisker · CONS · Δ+why · VBD · TIER. Grid `60px 170px 66px 48px 48px 192px 62px 74px 64px 58px`. Also a round-grade grid view and a delta view. Export CSV / PDF |
| **Availability Explorer** | Pick selector, five position columns with per-player dot arrays, tier-availability card with dots and frequency phrasing |
| **Opponents** | The nine other managers, their tendencies, marked NOT A MODEL INPUT where relevant |
| **Strategy Guide** | Hero band (eyebrow, title, replacement-level strip vs public defaults) · plan cards per pick · strategy comparison table with noise-band caveat · league-specific corrections |
| **Methodology** | Hero band · **four-step pipeline** (consensus → format correction → projection+interval → VBD/tiers, each with its field) · is/is-not-an-input pair · data sources table · limitations as severity-chipped cards |
| **Glossary** | Four categories, two-column cards, backing field + "Ask the assistant" per term |
| **Mock entry** | Pick entry for **all** teams; prediction recorded before each pick; board grid sized `44px repeat(teams, minmax(62–74px,1fr))`; `teams × 16` picks |
| **Mock review** | Per-mock: picks logged, top-prediction hit rate, availability calls, Brier; availability calls at your picks; pick-by-pick with surprise index |
| **Model validation** | Calibration by stated probability with Wilson intervals, thin-bucket flags, and a plain statement that a handful of mocks is not a validation set |
| **Coming soon** | Live league sync · bottom-up projections · news & injuries · in-season tools · startability scores. Real layouts at 55% opacity with an honest note |

## 7.4 Season mode

Manager selector across all screens. Weekly lineup (projection-at-lock scoring, confidence
intervals, coverage disclosure) · Consistency heatmap · Waivers/FAAB · Decision log · Trades ·
League comparison (error bars with "read the bars, not the order") · Write-up.

## 7.5 Cross-cutting

- **Inline glossary** — dotted terms and `i` chips. Hover/click → popover with definition, "Ask the
  assistant" (sends term + current screen context), "Full entry".
- **Assistant dock** — context-aware (mode, screen, focused player). Provenance is the layout:
  colour-coded left rules for MODEL / SOURCE / INFERENCE, not a footnote.
- **Trace popover** — any number can name its field, value and source.
- **Compare tray** — up to 3 players.

---

# 8. Null and edge states

| Situation | Render | Never |
|---|---|---|
| No projection (~60% of board) | `—` plus "no projection"; rank still shown | `0`, blank, or an inferred number |
| Availability < 0.5% | `<1%` | `0%` |
| Availability not computed | `—` with the reason on hover | `0%` or the baseline |
| `live_p` with `signal:'none'` | "not yet" + picks-logged count | the baseline repeated silently |
| Sim never generated | "Never simulated · `availability.players = null`" | `0%` |
| Sim stale | old numbers, greyed, labelled with generation timestamp | fresh-looking numbers |
| Scoring recompute pending | pre-edit numbers everywhere + banner | partially updated numbers |
| Empty queue | `draft.queue = []` + what queuing does | a generic "nothing here" |
| Empty watchlist | `account.watchlist = []` + that it is account-wide | — |
| No mocks for this league | `mocks[league=…] = []` + how to log one | another league's mocks |
| Multiple empty sections on one player | **one** collapsed line naming everything missing at once | three stacked empty headers |
| Unknown roster player (outside our board) | `roster.player_id = unknown` | omit the row |
| Aggregate over incomplete set | coverage disclosure: *"this total covers 7 of them and nothing else"* | a bare total |
| Source older than 48h in season | "treat as last-seen, not current" | an unqualified value |

**Coverage disclosure is a reusable component.** Apply it anywhere a total, average or rank
aggregates over an incomplete set.

---

# 9. Acceptance checklist

Ship-blocking. Each line is checkable in a browser.

**Tokens**
- [ ] No monospace on any player name, prose paragraph, nav item, button label, or position/team code
- [ ] `tabular-nums` present on numeric cells and absent from prose
- [ ] Zero border-radius on data cells and table rows; 6px on cards/buttons/chips; 12px on overlays
- [ ] Light mode is not an inversion: canvas off-white, surfaces white, accents higher chroma
- [ ] Saturated amber appears only on attention/scarcity/stale states
- [ ] Every colour-carried meaning has a non-colour cue

**Live availability**
- [ ] Baseline and live are both visible on the board row, in the queue, and in the player panel
- [ ] `adjustment.need` and `adjustment.run` are shown separately, not combined
- [ ] With fewer than `max(4, teams/2)` picks logged, live reads "not yet" and never the baseline
- [ ] Between half a round and a full round, rows are marked thin and the band is 1.6× wider
- [ ] No availability figure appears without its 10-dot array

**Recompute and staleness**
- [ ] Changing a roster slot updates instantly with no job
- [ ] Changing a scoring value changes **nothing** on screen until Recalculate completes
- [ ] A pending scoring change shows the app-wide banner and a per-field old → new diff
- [ ] Editing settings marks availability STALE app-wide, and the assistant refuses to quote it
- [ ] A league that has never been simulated shows explicit nulls, not zeros

**Structure**
- [ ] Player detail is a right side sheet at 440px with **no dark scrim**; board and clock stay visible
- [ ] The panel order is identity → verdict → numbers → availability → derivation
- [ ] The action bar is sticky at the bottom of the sheet with an accent-filled primary
- [ ] Rank derivation expands inline on the board row, not only in the panel
- [ ] Mock grid and opponent cards render `teams` columns for any team count, not 10
- [ ] Switching leagues preserves each league's own draft state

**Honesty**
- [ ] No value on screen lacks a named backend field
- [ ] `0%` never appears where the claim is "not computed"
- [ ] Consecutive empty sections collapse to one line
- [ ] Sample or generated data is labelled as such on screen

---

# 10. Known gaps and decisions needed

1. **Non-snake drafts.** Mock entry grid and opponent cards assume snake order. Linear and
   3rd-round reversal need different pick-order maths; auction needs a different screen (budget,
   nomination order). Which ship at launch?
2. **Prep board at laptop width.** Needs ~880px, gets ~708px at a 924px window — VBD and TIER fall
   off the right edge. Fits at normal desktop widths. Fixing it means dropping or collapsing two
   columns below a breakpoint: a density decision.
3. **Headshots are plumbed but unpopulated** (§6.9).
4. **`noise_band` is a placeholder 0.12.** Swap the real bootstrapped width.
5. **Where does the live adjustment run?** Client-side per pick today. Anything heavier than
   log-odds shifts needs an endpoint plus a latency budget under a pick clock.
6. **Is `{need, run}` the final decomposition?** We show components individually; a third signal is
   fine, four needs a design decision.
7. **Mock storage** — server-side per league (so validation pools across devices) or local until
   opt-in?
8. **Platform mock imports** — if mock rooms can be read directly, manual entry becomes the fallback
   and the validation set grows much faster.
9. **Per-league watchlist annotations** — server-side join or client-side?

---

# 11. Prototype data caveat

Availability figures, mock logs, calibration buckets, weekly finishes and the three-season tables
are sample or deterministically generated data, labelled as such on screen. 70 of 378 players are
loaded. **The layouts, the formulas and the null states are final; the wiring is the work.**
