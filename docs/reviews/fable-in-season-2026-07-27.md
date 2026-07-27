# The in-season half of the product — 2026-07-27 (Extended mandate, Priority 2)

**Verdict: the architecture extends, with named modifications — provided nobody bolts in-season
questions onto the hazard engine, which cannot express them.** The hazard-over-a-pick-sequence
core is a draft-time availability engine and should stay one. What in-season management needs is
(a) the week-indexed projection object the Priority 1 review already ordered for other reasons
(R3), (b) a second Monte Carlo consumer — a season/standings simulator — structurally parallel to
`draft_sim.py` rather than an extension of it, (c) a week-leverage weighting utility, specified
once below, and (d) export-contract growth. The raw data layer is already general; the export
contract is draft-shaped; the schema has one real hole (no fantasy-league standings/matchup
tables). None of this requires a rewrite. All of it goes wrong if deferred until after the draft
tool calcifies further.

## 1 · Inventory from the code, per phase

Measured by reading `src/` (36 modules) and `frontend/ui/views/` (10 views), not the roadmap.

| Phase | What exists (code, not plans) | Assessment |
|---|---|---|
| **Live draft** | `live_availability.py` (per-pick hazard, λ=0.352, δ=0.10) · `availability.py` · `draft_sim.py` (160-pick snake sim, opponent model, paired bootstrap, sign test) · `mock_lab_store.py` (event-sourced pick log) · `candidate_rankings.py` · `lambda_estimation.py` · the 25-dir config matrix · views: `DraftRoom` (typeahead pick entry, tier headers, 10-dot availability), `Availability`, `Opponents`, `RoundGrid` | The centre of gravity. The engine's only *probabilistic* consumer. |
| **Draft prep** | `make_board.py` · `export_strategies.py` · `narrate.py` (Facts layer) · `archetypes.py` · `player_descriptions.py` · views: `Board`, `StrategyGuide`, `Methodology`, `Glossary`, `Predictions` (absent from shipped app per CURRENT-STATE) · FR-008's on-deck conditional recommendations: specified (thread 059), not built | Served by rankings + prose, as the PM's prior said — *incidentally*: prep is a read-only projection of draft assets, with no prep-specific computation (no tiering-for-prep, no scenario planner). |
| **In-season** | `draft_sim.py:53`: "**NO IN-SEASON MANAGEMENT. No waivers, trades, or IR**" (explicit refusal, citing test-registry #62: in-season acquisition may account for much of a championship roster) · `league_config.py:55-58`: `playoff_teams=4`, `playoff_weeks=(16,17)`, `trade_deadline` — **config fields exist, nothing consumes them** · `ingest_weekly_stats.py:34`: partial-season data "wanted, for in-season use" — an intention in a comment · `narrate.py:204` mentions waiver value in display prose · weekly history exports (`weekly_finishes.json`) — history views, not live-week tools | **Absent.** Not one module, view, or export answers a single in-season question. The PM's "~85% live draft / prep incidental / in-season essentially absent" prior is confirmed by the code — the only correction is that in-season is not "essentially" absent, it is *declaredly* absent, with the refusal documented at the top of the simulator. |

## 2 · Are the four in-season capabilities expressible in this engine?

The engine's native object is **P(player survives the pick sequence to my next pick)**. Testing
each capability against that object:

| Capability | Native question | Expressible in the hazard engine? | What it actually needs |
|---|---|---|---|
| **Waiver priority** | "Which free agent adds the most rest-of-season roster value?" | **No.** There is no pick sequence; 10-team waiver contention is second-order and, where it matters (FAAB timing), it is a different scarcity model over a different actor population. | Rest-of-season **week-indexed** projection (R3 vector, truncated at current week) + roster-value delta (machinery exists: `draft_sim`'s roster scoring / VBD) + leverage weighting (§4). |
| **Start/sit** | "Which of two rostered players scores more THIS week?" | **No.** The engine has no week-level projection at all — every projection object in the repo is a season aggregate. | A weekly projection layer (matchup, home/away, injury status). **The single biggest genuinely new lift** in the product's future. S1/S2's decomposition feeds it (opportunity persists week-to-week too) but the model class and evaluation loop (Brier on weekly H2H calls) are new. |
| **Trade valuation** | "Is roster A minus X plus Y better positioned for the championship?" | **No.** | Rest-of-season vector for both sides + **playoff-leverage weighting** (§4) + roster-context (bye alignment, positional depth). Roster scoring exists; leverage does not. |
| **Playoff-odds-aware risk** | "I'm 3–5; should I prefer variance?" | **No — but this is the structurally closest one.** A standings simulation is the same *shape* as `draft_sim`: Monte Carlo over discrete events, a scoring function, paired comparison across policies. The code pattern, seeding discipline, and bootstrap layer port directly. | A **season simulator**: weekly score distributions per team → standings → P(playoffs), P(championship) per policy. New module, old skeleton. |

**The through-line: all four consume the same two missing objects** — the week-indexed
rest-of-season projection (R3) and the leverage weights (§4) — plus one new simulator. None of
them consume the hazard model. The answer to the mandate's "or do they need a different core?"
is precisely: *a different consumer, the same substrate.* Bolting them onto the draft engine
(e.g., expressing a waiver claim as a pseudo-pick in a pseudo-draft) would fight the design and
produce untraceable numbers; building a sibling simulator next to `draft_sim` will not.

## 3 · Is the data layer general enough?

Three layers, three different answers:

- **Raw store: general.** `player_weekly_stats` is week-grained, 1999–2025, with `season_type`;
  `injuries` and `depth_charts_weekly` are week-grained; ingest explicitly anticipates partial
  in-season pulls (`ingest_weekly_stats.py:34`). Nothing here is draft-shaped. Good.
- **Reference layer: snapshot-shaped by design, correctly.** `rankings`/`adp_snapshots` carry
  `as_of_date` — that discipline serves in-season use (weekly re-pulls) exactly as well as
  draft prep. No change needed, only more frequent snapshots once in-season starts.
- **Export contract: draft-shaped, and this is where extension lands.** Every artifact is a
  draft asset (board, strategies, availability, rosters-from-draft-picks). `weekly_finishes.json`
  is a *history* view. Missing for in-season: live my-roster state, weekly matchup/opponent
  exports, standings, a current-week projection artifact. Contract-level additions, no schema
  migration.
- **One real schema hole:** there are **no fantasy-league standings/matchup/transaction tables
  at all** — the league's own weekly results have no home in the DB. Every in-season capability
  in §2 needs them. Cheap to add now (`league_matchups`, `league_transactions`, both with
  `league_id` + `as_of_date` per the multi-user schema principle); annoying to retrofit under
  a live season.

## 4 · Week-weighting — the shared primitive, specified once

Nowhere in the repo. `playoff_weeks=(16,17)` sits unconsumed in `league_config`. Specification,
so this exists exactly once (a `league_config`-driven utility, consumed by suspension valuation,
bye cost, start/sit thresholds, trade evaluation, and R3's integrals):

- **Object:** `leverage: week -> weight`, normalised to mean 1 over the season, defined per
  league from config (this league: regular weeks 1–15, playoff weeks 16–17, 4 teams, no
  reseed).
- **Semantics:** `leverage(w)` = the marginal effect of one expected win in week `w` on
  P(championship), estimated by the §2 season simulator (simulate seasons; measure
  dP(championship)/d(win_w) by paired perturbation). This makes the weights *measured, not
  assumed* — same discipline as everything else here.
- **Interim default until the simulator exists** (flagged unvalidated, D-004-style): uniform
  1.0 across weeks 1–15, `L_p` on playoff weeks with `L_p ≈ (1/P(reach)) × share of
  championship variance` — honestly hand-set to 2.0 and labelled as such. Also encode the
  structural asymmetry the founder's league imposes: **no reseeding + 4 teams means early-season
  losses compound** (CLAUDE.md §7 calls the slow start "a real constraint, not a preference"),
  so any refinement should be checked against the simulator before weights 1–4 are discounted.
- **Consumers, named now so the primitive is built once:** suspension cost = Σ leverage(w)
  over missed weeks × projected ppg; bye cost = leverage(bye_week) × ppg; missed-early-weeks
  injury valuation = the same integral with a recovery ramp; start/sit and trade valuation
  integrate rest-of-season vectors against it.

## 5 · Verdict and work orders

**Extends with named modifications.** The current design will not fight in-season work *unless*
in-season is expressed through the hazard engine — the one bolt-on the mandate worried about,
and the one §2 rules out capability-by-capability.

- **N1** [backend, small, do before the draft while it is cheap] — add `league_matchups` /
  `league_transactions` tables (empty is fine; `league_id`, `as_of_date` from day one).
- **N2** [strategist spec, then backend] — season/standings simulator as a sibling of
  `draft_sim.py` (same seeding/bootstrap discipline), outputs P(playoffs)/P(championship) and
  the §4 leverage estimates. This is FR-005's "simulation-resampled questions have unlimited n"
  insight applied to the season, and it is buildable the day R3's vector exists.
- **N3** [backend, small] — the §4 leverage utility in `league_config` terms, interim default
  flagged unvalidated, replaced by N2's measurement when it lands.
- **N4** [PM, sequencing] — declare in the roadmap that start/sit (weekly projection layer) is
  the one genuinely new modelling lift, and that it is NOT a prerequisite for waiver/trade/
  playoff-odds tools, which need only R3 + N2 + N3. Sequencing the cheap three first gets an
  in-season product this season; sequencing start/sit first gets nothing until it is done.
- **N5** [librarian, minutes] — `draft_sim.py:53`'s refusal comment should point at this review
  and N2, so the next reader knows the refusal is scoped to *that module*, not to the product.

One prep-phase note in passing (observed while inventorying, cheap to state): `frontend/src/`
contains a byte-identical dead copy of the backend Python tree (26 files, subtree-merge
residue; nothing imports it — the server imports only `scripts/sync-exports`). It is the exact
substrate for an edited-the-wrong-file failure and belongs in the Priority 3 pre-mortem, where
it is taken up.
