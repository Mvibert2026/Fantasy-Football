# Player archetype system — taxonomy proposal (FR-075)

**Researcher, 2026-07-30.** A specification, not an implementation. No code in `src/`,
`frontend/` or the ranking model was changed by this pass.

> **Nothing in this document is validated.** No archetype here has been tested against outcomes.
> No claim is made that any archetype predicts anything, improves a ranking, or beats a baseline.
> The existing archetype system (ADR-044) was never validated either — its own source brief said
> the thresholds were unmeasured conventions, and that verification pass has still not been run.
> Treat every threshold below as a **hypothesis with a stated derivation**, not a finding.

Founder scope, verbatim:

> "We need to get archetype built and I'd like to see it towards the top of the card (or inprep
> there is space next to the napes to the right before position comes into play"

> "take inspiration from the industry, and if there are players who don't fit a mold or you like
> other descriptors better, use them - just help define it"

---

## 0. The finding that reframes the request

**An archetype system already exists, is computed, and is exported. The player card does not read
it.** [VERIFIED — repo]

| Fact | Evidence |
|---|---|
| `src/archetypes.py` assigns 15 labels across RB/WR/TE | `src/archetypes.py:55-62` (ADR-044) |
| `src/player_descriptions.py` turns them into prose and writes `player_descriptions.json` | `src/player_descriptions.py:178-203` |
| The artifact is committed and carries a per-player `archetype` field | `data/export/player_descriptions.json`, `generated_utc` 2026-07-26, season 2026 |
| The frontend **loads** it into `Dataset.playerDescriptions` | `frontend/ui/data/load.ts:187,214` |
| The **assistant** reads it | `frontend/ui/assistant/retrieval.ts:507-519` |
| **`PlayerDetail.tsx` renders "Not computed: archetype. No backend field in this build."** | `frontend/ui/components/PlayerDetail.tsx:425-434` |

That comment says the field is "permanently absent, no field in any export, ever." That is true of
`board.json` and false of the app's own loaded dataset. **This is the most likely reason the
founder believes archetype was never built.** It is a wiring gap and a false on-screen claim, not
a missing model.

So FR-075 splits into three independently actionable pieces:

1. **A display gap** — the label exists and does not reach the card. Cheapest fix in the project.
2. **A taxonomy gap** — the existing labels are demonstrably degenerate in practice (§1).
3. **A coverage gap** — QB has no taxonomy at all; the file covers RB/WR/TE only
   (`src/archetypes.py:109`, `positions=("RB","WR","TE")`).

---

## 1. How the existing taxonomy actually performs — measured, not assumed

Counted directly from the committed `data/export/player_descriptions.json` (213 players; every
figure below sums to 213). [VERIFIED — artifact]

| Position | Label | n | % of position |
|---|---|---|---|
| **WR** | WR_ROTATIONAL | 46 | 41.4% |
| | WR_FIELD_STRETCHER | 38 | 34.2% |
| | WR_HIGH_VOLUME | 23 | 20.7% |
| | WR_POSSESSION | **4** | **3.6%** |
| | *WR total* | *111* | |
| **RB** | RB_COMMITTEE | 32 | 62.7% |
| | RB_BELL_COW | 12 | 23.5% |
| | RB_EARLY_DOWN | 4 | 7.8% |
| | RB_PASSING_DOWN | **3** | **5.9%** |
| | *RB total* | *51* | |
| **TE** | TE_SECONDARY_RECEIVER | 26 | 51.0% |
| | TE_PRIMARY_RECEIVER | 15 | 29.4% |
| | TE_BLOCKING | 10 | 19.6% |
| | *TE total* | *51* | |

Confidence split of the 213: 161 high, 52 medium. [VERIFIED — artifact]

**Three failure modes are visible in that table:**

- **A catch-all bucket per position.** RB_COMMITTEE holds 62.7% of running backs; WR_ROTATIONAL
  41.4% of receivers; TE_SECONDARY_RECEIVER 51.0% of tight ends. A label that fits the plurality
  of a position is not describing a type — for RBs and WRs the bucket is really "depth-chart
  position we did not otherwise name."
- **Near-empty labels.** WR_POSSESSION has 4 players and RB_PASSING_DOWN has 3, out of 213. Both
  are real football roles, so the labels are not wrong — the *thresholds* are cutting almost
  nobody.
- **The fall-through is enormous.** ADR-044 records the same run as 527 RB/WR/TE assigned, 237
  high confidence, 86 medium, 204 undetermined [VERIFIED — `docs/decisions.md:1256-1259`]. So 323
  players had enough games to be classified, and only 213 received a label. **≈110 players — about
  34% of everyone with sufficient data — met no criterion and became `*_UNDETERMINED`.** [derived
  from two VERIFIED figures; assumes the ADR's run and the committed artifact are the same run,
  which the shared date 2026-07-26 and shared `season: 2026` support but which was not re-executed
  this session]

ADR-044 predicted this and pinned it as a regression test rather than patching it: Keenan Allen
(2025: target share 0.224, snap share 0.555, aDOT 8.42) fails WR_HIGH_VOLUME (needs snap ≥0.70),
fails WR_POSSESSION (needs ≥0.60), and fails WR_ROTATIONAL (needs <0.55, he is at 0.555). He falls
into the exact mid-mass gap the original brief warned about. [VERIFIED — `docs/decisions.md:1233-1239`]

**This is precisely the founder's "players who don't fit a mold," and it is the dominant case, not
an edge case.** §4 is the design response.

---

## 2. Part 1 — what the industry actually uses

### 2.1 The headline finding about the vocabulary

**The vocabulary is near-universal; the definitions are not.** Across every source fetched, the
terms are used as if they were shared, and almost none carry a published numeric definition. Two
sources using "bell cow" or "field stretcher" are usually not making the same claim, and there is
no way to tell from the word alone.

This is the useful signal: it means **borrowing an industry word costs nothing and borrowing an
industry threshold is impossible**, because in most cases no threshold was ever published.

### 2.2 Terms with a real published quantitative definition

| Term | Definition | Source | Tag |
|---|---|---|---|
| **Bell cow** (RB) | "15+ games played" and "67+ percent of their team's offensive snaps per game" | Footballguys, *The Running Back By Committee Conundrum* | [VERIFIED — fetched] |
| **Committee leader** (RB) | "16+ games played" and "66.9-50 percent of their team's offensive snaps per game" | Footballguys, same article | [VERIFIED — fetched] |
| **Slot / balanced / outside** (WR) | slot-snap rate: 0-20% outside, 20-40% balanced, 40%+ slot | Dynasty League Football, *Dynasty Archetypes: Wide Receiver* | [SNIPPET — page returned HTTP 403 to direct fetch; definition seen only in search excerpt] |
| **Reception-reliant** (WR) | "36%+ of PPR output from receptions alone, with 66%+ of standard scoring from receiving yards" | Sharp Football Analysis, *Fantasy Notebook: WR Correlations, Usage, and Archetypes* | [VERIFIED — fetched] |
| **Yardage-dependent** (WR) | "75%+ of standard scoring from yardage while yardage comprises over 50% of PPR output" | Sharp Football, same | [VERIFIED — fetched] |
| **Touchdown-dependent** (WR) | "20%+ of career output from touchdowns while touchdowns account for 30%+ of standard output" | Sharp Football, same | [VERIFIED — fetched] |
| **Y-TE / U-TE** (TE) | Y = "typically on the line of scrimmage"; U = "off the line of scrimmage". U drew a 20.3% target rate in 12 personnel vs 16.0% for Y (2023) | PFF, *Studying tight end utilization* | [VERIFIED — fetched] |
| **X / Z / S receiver** | Alignment definitions (X on the line opposite the TE, Z off the line, S inside the X or Z) | PFF, *Studying wide receiver utilization* | [VERIFIED — fetched] |
| **Bell cow**, alt. | "at least 67 percent of their team's snaps per game across at least 15 games… approximately 4.8 backs each year meet this standard since 2021", worth "1.7 half-PPR points per game more than the average RB2" | RotoBaller | [SNIPPET — article body did not render on fetch, only navigation chrome; figures seen in search excerpt only] |

### 2.3 Terms in wide use with **no** published quantitative definition found

| Term | What was found | Tag |
|---|---|---|
| **Konami code** (QB) | Coined by Rich Hribar (Sharp Football) c. 2013; means a rushing QB is "a cheat code." FantasyPros' own 2024 article on the topic offers **no threshold at all** — the only definition given is "It's become a cheat code of sorts." | [VERIFIED that no threshold is given — fetched the FantasyPros article]; origin attribution [SECONDARY] |
| **Bell cow** as used by Fantasy Points | Their 2025 Bell Cow Report uses the term throughout with **no numeric definition**; closest is "63% of backfield-weighted opportunity… close to true bell cow usage" | [VERIFIED — fetched] |
| **Dual-threat**, **run-pass threat**, **running quarterback** | Used interchangeably with "Konami code" in the same article, undefined | [VERIFIED — fetched] |
| **Thunder and lightning**, **two-minute back**, **red-zone back**, **vulture**, **swing player** | Role labels in circulation, no thresholds published in the sources fetched | [VERIFIED — fetched, Fantasy Points + Footballguys] |
| **Alpha WR / WR1 target share** | "Season-long target share percentages above 20% have historically been associated with WR1 outcomes" attributed to PFF and Sharp Football | [SNIPPET — attribution appeared in a search summary, not on either named site's own page; do not cite as PFF's own claim] |
| **Move TE / F-TE vs Y-TE** | "The F-TE (also known as the move TE) is more of a glorified slot WR… lining up in the slot or off the line out-wide more often" | [SNIPPET] |

### 2.4 Where the industry openly disagrees

- **"Bell cow" is snap-defined by some and opportunity-defined by others.** Footballguys uses
  snap share with a games floor; Fantasy Points uses "backfield-weighted opportunity" and does not
  publish a cut. **This project's own code uses a third definition again** — `offense_pct ≥ 0.60`
  **and** `carry_share ≥ 0.55` **and** `target_share ≥ 0.07` with a games floor of 8
  (`src/archetypes.py:204`). Three sources, three incompatible definitions of the single
  best-defined term in fantasy football.
- **WR archetypes split on *what they measure*.** Alignment-based (PFF X/Z/S; DLF slot rate),
  usage-based (target share, aDOT — what this project does), and **scoring-composition-based**
  (Sharp Football: what fraction of a player's fantasy points came from receptions vs yards vs
  TDs). These three families do not map onto each other and produce different groupings for the
  same player.
- **TE taxonomies split the same way.** PFF's *utilization* piece uses formation role (Y/U,
  early-down/third-down); Sharp Football's *archetypes* piece uses snap rate × route rate ×
  targets-per-route. A "move TE" in the first sense and a "big wide receiver" (Sharp's 60%+ career
  snaps running routes) in the second overlap but are not the same set.

### 2.5 What the industry does **not** do

**No consumer draft product was found that surfaces a derived archetype label on a player card.**
FantasyPros' Draft Wizard offers "Player Tags" — *user-applied* labels for sleepers/targets/avoids,
not derived ones. Underdog's public help and strategy content describes archetypes in prose but no
in-product label was found. [GAP — this is an absence-of-evidence result from search plus help-doc
reading, not a product audit. Yahoo, ESPN and CBS hosts were **not fetched**, per this project's
standing block on those hosts, so any label those products show is unmeasured here and must not be
assumed absent.]

If that gap is real, putting a derived archetype chip next to the name is a genuine product
differentiator rather than table stakes. **It also means there is no convention to conform to** —
which is the strongest argument for taking the founder up on his offer to deviate.

---

## 3. Part 2 — the proposed taxonomy for this project

### 3.1 Four design rules, each with a reason

**R1. Dimensions are scored; the label is derived from them.** See §4.1 for the argument.

**R2. Absolute thresholds for workload, relative (within position-season percentile) for style.**
Workload level is the meaningful quantity in itself — "there were only four bell cows in 2025" is
a true and useful sentence, and a percentile cut would destroy it by manufacturing a fixed number
every year. Style is comparative — "deep threat" only means anything relative to the other
receivers that season, and absolute aDOT cuts drift with league-wide passing trends (the NFL is
non-stationary, `CLAUDE.md` §6.4). This rule is a judgement, not a measurement.

**R3. Every threshold below is a stated convention awaiting a distribution check.** The original
brief said: "before use, plot the actual distributions and check the thresholds land in valleys
rather than mid-mass" [VERIFIED — quoted in `src/archetypes.py:37-41`]. **That check has never been
run.** It is the single highest-value piece of follow-up work in this proposal and it is cheap.

**R4. Display-only stays display-only.** ADR-044 enforces, with a static-scan test, that
`archetypes.py`/`player_descriptions.py` are never imported by `narrate.py`, `scoring.py`,
`make_board.py`, `backtest.py`, `candidate_rankings.py`, or the board-building path
(`tests/test_player_descriptions.py:104-107`). **This proposal does not change that and no part of
it should be wired into a ranking without going through the factor-test process first.**

### 3.2 The dimensions

Each is a scored value every qualified player has, not a bucket.

| # | Dimension | What it measures | Fields needed | Derivable today? |
|---|---|---|---|---|
| D1 | **Workload** | Share of the offense the player was on the field for | `snap_counts.offense_pct` | **Yes**, 2013+ (`docs/data-availability.md` §7.3: 2013-2025, no interior gaps, fraction in [0,1]) |
| D2 | **Opportunity share** | Share of team carries and/or targets | `player_weekly_stats.carries`, `.targets` | **Yes**, but `targets` is unusable 2003-2008 (`data-availability.md` §2) |
| D3 | **Usage mix** | Split of a player's own opportunity between rushing and receiving | same as D2 | **Yes** |
| D4 | **Target depth** | aDOT | `player_weekly_stats.receiving_air_yards / targets` | **Yes**, 2009+ only |
| D5 | **Scoring composition** | Fraction of this league's fantasy points from receptions / yardage / TDs | `src/scoring.py::score_offensive_game` over masked stat dicts | **Yes** — the scoring engine already exists; this is arithmetic on it |
| D6 | **Volatility** | *reserved — see §3.7* | — | **Slot only.** Not defined here |
| D7 | **Role security** | Depth-chart rank and whether a superior exists | `depth_charts_snapshots.pos_rank` | **2026 only** — see §3.8 |
| D8 | **Alignment** | Slot rate / in-line rate | not in `nfl.db` | **No — BLOCKED**, see §3.9 |
| D9 | **Role stability** | Consecutive prior seasons carrying the same label | derived from D1-D5 across seasons | **Yes**, back to 2014 for any label using D1 |

### 3.3 RB — two dimensions, one derived chip

**Workload tier** (absolute, D1, games_qualified ≥ 12 for `high` confidence, 8-11 `medium`):

| Tier | Criterion | Derivable |
|---|---|---|
| `BELL_COW` | `offense_pct ≥ 0.67` | Yes |
| `LEAD` | `0.50 ≤ offense_pct < 0.67` | Yes |
| `ROTATIONAL` | `0.30 ≤ offense_pct < 0.50` | Yes |
| `MARGINAL` | `offense_pct < 0.30` | Yes |

The 0.67 / 0.50 cuts are **Footballguys' published definition** (§2.2), adopted deliberately over
the existing code's 0.60-plus-two-conjuncts rule. Two reasons: the industry cut is published and
checkable, and dropping the conjunction removes a fall-through mode. **The games floor is
deliberately 12, not Footballguys' 15** — 15 imports survivorship, since a bell cow who missed
three games was still a bell cow. That deviation is a judgement and should be recorded as one.

**Usage-mix modifier** (relative, D3, percentile among qualified RBs in the same season):

| Modifier | Criterion |
|---|---|
| `PASS_CATCHING` | player's receiving share of own opportunity ≥ 80th percentile |
| `EARLY_DOWN` | ≤ 20th percentile |
| *(none)* | in between — the chip shows the workload tier alone |

**Displayed chip** = workload tier, plus modifier when one fires: `Bell cow`, `Lead ·
pass-catching`, `Rotational · early-down`, `Marginal`.

**`HANDCUFF` is a D7 flag, not a tier** — a handcuff is a *rotational or marginal* back whose
depth-chart superior is a bell cow. Modelling it as a mutually exclusive label was part of why it
was never implemented. See §3.8.

### 3.4 WR

**Target-share tier** (absolute, D2, with a snap floor from D1):

| Tier | Criterion |
|---|---|
| `ALPHA` | `target_share ≥ 0.25` and `offense_pct ≥ 0.70` |
| `PRIMARY` | `target_share ≥ 0.20` |
| `COMPLEMENTARY` | `target_share ≥ 0.13` |
| `FRINGE` | below that |

The 0.20 boundary is the only WR number in the survey with any consensus behind it, and even that
is [SNIPPET]-grade (§2.3). 0.25 for ALPHA and 0.13 for COMPLEMENTARY are **this project's
conventions with no external support** — flagged as such, R3 applies to both.

**Depth modifier** (relative, D4, percentile among qualified WRs that season): `DEEP` at ≥80th,
`SHORT` at ≤20th, none in between.

**What this deliberately drops.** `WR_ROTATIONAL` disappears as a *type* — it was a snap-share
statement (41.4% of receivers, §1) masquerading as a style. It becomes `FRINGE`, which says the
same thing without implying we learned something about how he plays. `WR_POSSESSION` (4 players)
and `WR_FIELD_STRETCHER` (38) collapse into the `SHORT`/`DEEP` modifier, which every receiver has
a value on rather than four of them having a label.

### 3.5 TE

| Tier | Criterion |
|---|---|
| `PRIMARY_RECEIVER` | `target_share ≥ 0.18` and `offense_pct ≥ 0.65` |
| `ROTATION_RECEIVER` | `0.08 ≤ target_share < 0.18` and `offense_pct ≥ 0.50` |
| `BLOCKER` | `target_share < 0.08` and `offense_pct ≥ 0.45` |
| `FRINGE` | below that |

Thresholds carried over unchanged from `src/archetypes.py:234-239`, with `FRINGE` added as the
honest bottom tier so the "meets nothing" case is a *measured* low-usage statement rather than a
fall-through. **The in-line/move (Y/U) distinction — the one the industry actually cares about at
TE — is not derivable.** See §3.9.

### 3.6 QB — new; currently no taxonomy exists at all

`src/archetypes.py` covers RB/WR/TE only. A QB has no archetype today, which is conspicuous on a
card, and QB is the position where this league's scoring makes the distinction sharpest.

**Under `CLAUDE.md` §7's scoring, a rushing yard is worth 2.5× a passing yard (10 vs 25 yds/pt)
and a rushing TD 1.5× a passing TD (6 vs 4).** That is exactly the ratio the "Konami code"
argument rests on, and here it is a property of our own verified rules rather than a borrowed
assumption. [VERIFIED — `src/scoring.py:13-18`, `CLAUDE.md` §7]

**Primary dimension: rushing share of fantasy points (D5).** Computed by scoring each QB season
under `scoring.LEAGUE` and taking the fraction of points attributable to rushing yards, rushing
TDs and the rushing yardage bonuses.

| Label | Criterion | Derivable |
|---|---|---|
| `DUAL_THREAT` | rushing share of points ≥ 80th percentile among QBs with ≥8 starts, that season | Yes |
| `POCKET` | ≤ 20th percentile | Yes |
| `BALANCED` | in between | Yes |

**No absolute cut is proposed, on purpose.** Every source fetched declines to give one (§2.3), and
inventing one here would be exactly the plausible-number-filling-a-gap failure this project
forbids. The percentile rule is measurable, reproducible, and honest about the fact that the
absolute boundary is unknown. Whether the distribution has a valley that would justify an absolute
cut is an R3 question.

**A volume modifier** (`HIGH_VOLUME` at ≥80th percentile of pass attempts per game) is proposed
**conditionally**: confirm `attempts` exists as a column in `player_weekly_stats` before
specifying it. `docs/data-availability.md` §2 lists the outcome family as "`receptions`,
`receiving_yards`, `rushing_yards`, `passing_yards`, all TDs, `carries`" and does **not** name
`attempts`. [GAP — column presence unconfirmed; do not build against it until checked.]

**No bonus-driven QB archetype is proposed.** See §3.10.

### 3.7 Volatility (D6) — a reserved slot, not a definition

FR-086 is measuring volatility as a candidate dimension in a parallel `ranker` workstream. This
document **does not define it and does not depend on its result.** The interface it should slot
into: one more scored dimension alongside D1-D5, contributing at most a modifier to the chip (e.g.
`Bell cow · volatile`), never a tier of its own.

**One constraint that workstream must not walk into.** `docs/preregistration/PR-002-spike-week-persistence.md`
is a pre-registered, run, **NULL** test of a closely related question: whether the propensity to
clear this league's yardage bonuses *conditional on volume* persists year over year.
[VERIFIED — the file, `status: RUN`, `result: NULL`]

- WR receiving-100: r = +0.041, 95% CI [−0.018, +0.099]
- RB rushing-100: r = +0.063, 95% CI [−0.001, +0.124]
- 36 correlations attempted, 24 produced a p-value, **zero survived Benjamini-Hochberg correction**
- Its own conclusion: "There is no 'spike-week player' to identify. Project the yards and the
  bonuses follow mechanically."

**PR-002 tested bonus-threshold clearance shape. It did not test general week-to-week fantasy-point
dispersion.** Those are different quantities and FR-086 may well be measuring the second. But the
two are close enough that FR-086 must state explicitly which one it measures, and its multiplicity
budget must account for the 36 tests already on the run log. A volatility archetype presented as an
edge without that distinction would re-report a settled null.

### 3.8 Role security (D7) — partially unblocked since ADR-044

ADR-044 left `RB_HANDCUFF` unimplemented because it needs a preseason depth chart, which the
original brief said was unavailable. **That is now only half true.**
`docs/data-availability.md` §7.2 records `depth_charts_snapshots`: 923,162 rows, **348 dated
snapshots from 2025-08-03 to 2026-07-25**, all 32 teams present every month, `pos_rank`/`pos_slot`
populated, `dt` usable as a true `as_of_date`. [VERIFIED — the doc, which states it was measured]

| Use | Status |
|---|---|
| Assign `HANDCUFF` for the **2026 draft** | **Derivable now.** Criterion: RB with workload tier `ROTATIONAL`/`MARGINAL` whose team's `pos_rank = 1` RB on the latest pre-draft snapshot is tier `BELL_COW`. |
| **Backtest** it on any season before 2025 | **Blocked.** The pre-2025 table (`depth_charts_weekly`, 2001-2024) is a different, in-season weekly format. A Week-1 row could proxy a preseason chart; that is a **proxy** and must be labelled one, per `CLAUDE.md` §5. |

So `HANDCUFF` can ship as a live flag while remaining explicitly unvalidated — which is the same
status as every other item here, stated out loud.

### 3.9 Alignment (D8) — BLOCKED, and it blocks the industry's best-defined labels

Not derivable. `nfl.db` has no slot rate, no in-line rate, no route participation.
`ngs_receiving` was checked column by column and carries **no route field**
(`docs/research/nflverse-unused-data-audit-2026-07-29.md`). [VERIFIED — that audit]

**What this costs us, specifically:** the only WR taxonomy in the survey with published numeric
cuts is DLF's slot-rate bands (§2.2), and the TE distinction the industry treats as fundamental
(Y/in-line vs U/move) is an alignment fact. **Both are unavailable to us.** Any archetype naming
"slot," "in-line" or "move" would be an invention, and none is proposed.

**What would unblock it:** `nflreadpy.load_participation()`, 2016-2025, ~46-48K plays/season,
carrying `route` and `offense_players`. Counting route-tagged plays against plays-on-field-during-
dropbacks per player-game is a documented proxy for route participation. Not ingested. Named as
open item 10 in `docs/CURRENT-STATE.md`. [VERIFIED — the audit doc, `load_participation` row]

**It does not unblock everything.** `route` names the route type run by the *targeted* receiver
only, so it gives route participation, not alignment. Slot rate specifically would still be a
[GAP].

### 3.10 What this league's scoring changes, and what it does not

**Does change things.** Half-PPR at 0.5/reception halves the value of the reception-heavy profile
relative to the full-PPR leagues most published archetype work assumes. A taxonomy tuned for full
PPR over-rates high-catch, low-depth receivers here. **Scoring composition (D5) is therefore worth
carrying as a real dimension in this league specifically** — a receiver whose points come mostly
from receptions is worth less here than a generic half-PPR list implies, and D5 makes that visible
on the card. This is the Sharp Football framing (§2.2) and it is the one industry idea this
project's constraints argue *for* adopting rather than against.

**Does not change things — and this is the important one.** The stacking yardage bonuses do **not**
justify a ceiling/floor archetype. PR-002 tested that premise directly and returned NULL (§3.7).
Additionally, PR-002 measured that the upper bonus tiers barely occur league-wide across a full
season: receiving 200+ in **1 to 8 games per season** (2025: one), receiving 150+ in **18 to 41**.
[VERIFIED — PR-002 result section] The +1.5 @ 150 and +2 @ 200 tiers are close to irrelevant in
expectation.

`CLAUDE.md` §7 says the bonuses "reward ceiling outcomes over floor, which should influence how
variance is valued in rankings." **PR-002 is evidence against the operational version of that
claim.** The arithmetic in §7 is correct; what is not supported is that ceiling-shape is a
forecastable player trait. This proposal therefore treats D5 as a *level* correction that explains
why our re-scored rank differs from a generic list — never as an independent shape signal. Anyone
building a "high-ceiling" archetype should read PR-002 first.

*(That tension between `CLAUDE.md` §7's framing and PR-002's result is noted here as a finding, not
resolved. It is not a researcher's call to change `CLAUDE.md`; flagged for `strategist`/`pm`.)*

---

## 4. Part 3 — the players who don't fit

### 4.1 Single label, primary+secondary, or scored dimensions?

**Recommendation: scored dimensions, with a single derived chip for display.**

| Option | Why not |
|---|---|
| **Single label** | This is what exists, and §1 measured what it does: a catch-all bucket per position, near-empty labels, and ~34% of well-measured players falling through. A single label forces a conjunction of thresholds, and every conjunction manufactures a mid-mass gap. |
| **Primary + secondary** | Doubles the labels without touching the cause. A player who fails every primary rule now fails every secondary rule too. It also invites a false hierarchy — "is bell-cow more primary than pass-catching?" has no answer. |
| **Scored dimensions** | Every player has a value on every axis, so nobody falls out of the system. The chip is a *presentation* of the axes, and the card can always show the numbers underneath. Fall-through stops being an error state. |

**What we give up, stated plainly:**

1. **The chip becomes unstable near boundaries.** A player one snap either side of 0.67 flips
   between "Bell cow" and "Lead." Mitigation: require a margin to *change* a label from the prior
   season's (hysteresis), and never re-derive a chip mid-render. This is a real cost and a real
   annoyance.
2. **A dimension vector is not a word,** and the founder asked for a word next to the name. The
   chip is a lossy summary by construction. Mitigation: the chip is always reversible — clicking
   through shows which dimension drove it and at what value.
3. **More numbers to keep honest.** Nine dimensions is more surface than 15 labels, and every one
   needs an `as_of` and a null state.
4. **It is more work than fixing the wiring.** §0's display gap could be closed today with the
   existing labels. The dimension redesign should not hold that hostage.

### 4.2 "Unclassified" must be honest — and it must be two different things

The existing system has one bottom state, `*_UNDETERMINED`, and it is currently absorbing both
"we could not measure him" and "we measured him and he is between our lines." Those are opposite
claims and must not share a bucket.

| Outcome | Meaning | Displays as |
|---|---|---|
| **`BALANCED`** | **Measured.** Every dimension within ±0.5 SD of the positional median. An informative statement: this player has no dominant trait. | `Balanced` |
| **`UNCLASSIFIED`** | **Not measured.** Fewer than 8 qualifying games, a null input, a rookie with no prior season, or a season before the 2013 data floor. Never a statement about how he plays. | `Not classified — <reason>` |

The reason string is mandatory and must name which of those four it is. `src/archetypes.py`
already populates a `reason` field for this (`ArchetypeAssignment.reason`) — the mechanism exists
and is under-used.

**The founder's test, made into an acceptance criterion:** *"If a third of the league lands there,
the taxonomy is wrong."* Turn that into a check that runs, not an intention:

- **Hard gate:** no single label may hold more than **35%** of qualified players at its position in
  a season. On the current system, RB_COMMITTEE (62.7%), TE_SECONDARY_RECEIVER (51.0%) and
  WR_ROTATIONAL (41.4%) all fail this today. [VERIFIED — §1]
- **Hard gate:** `UNCLASSIFIED` may not exceed **10%** of players who have ≥8 qualifying games. The
  current system is at roughly 34% on that measure. [derived, §1]
- **Soft flag:** any label holding fewer than 3% of its position is a candidate for merging into a
  modifier. WR_POSSESSION (3.6% of WRs) and RB_PASSING_DOWN (5.9% of RBs) are the current
  candidates.
- The 35% / 10% / 3% numbers are **chosen conventions**, set to be a little stricter than the
  founder's "a third." They are not measured optima. State them as conventions wherever they appear.

### 4.3 Archetype drift — mid-career, and across the gap between data and draft

**The structural rule already in place is correct and should be kept.** An archetype for draft
season S is computed from season S−1 actuals only; using season S data would be look-ahead
(`CLAUDE.md` §6.1). `src/archetypes.py:5-8` enforces this and `test_no_archetype_uses_target_season_data_look_ahead`
locks it in. [VERIFIED — repo]

But that rule creates the exact problem the founder is asking about: **the label is always one
season stale, and it is most stale precisely for the players whose situation just changed** — the
free agent on a new team, the back-up promoted after a trade, the receiver whose target competition
left. Three responses, all derivable:

**1. Never call it a forecast. Change the noun.** The chip should read as a description of last
season's role, and the card should say which season it describes. "2025 role: Bell cow" is true.
"Archetype: Bell cow" implies a claim about 2026 that nothing here supports. **This single wording
change is the cheapest correctness fix in the proposal.**

**2. Carry a `role_change_risk` flag, from data we have.** Fires when any of:
   - the player's team on the latest pre-draft roster differs from his team in the data season
     (`rosters`, 2026 present per `data-availability.md` §1);
   - his `pos_rank` on the latest `depth_charts_snapshots` row differs from what his tier implies
     (2025+ only, §3.8);
   - he is a rookie (no prior season at all — already handled as `UNCLASSIFIED`, reason `rookie`).

   The flag says "this label may not survive the offseason." It does **not** predict the new label.
   Predicting the new label is a forecasting problem, it is not what an archetype is, and nothing
   in this project has earned the right to attempt it.

**3. Carry `archetype_stability` (D9): how many consecutive prior seasons produced the same
label.** Derivable back to 2014 for any label using snap share. Four straight `BELL_COW` seasons
and one are very different claims and the card currently cannot tell them apart. Cheap, honest,
and it makes drift visible instead of hidden.

**What is explicitly not proposed:** projecting a 2026 archetype from 2026 expectations. That is a
forecast wearing a description's clothes, it would be unfalsifiable on the card, and it would
reintroduce look-ahead risk into the one part of the system that is currently clean.

---

## 5. Derivability summary

| Archetype / dimension | Derivable today? | If not, what it needs |
|---|---|---|
| RB workload tiers (bell cow / lead / rotational / marginal) | **Yes** (2013+) | — |
| RB usage-mix modifier | **Yes** (2009+ for targets; 2003-2008 hole) | — |
| RB `HANDCUFF` flag, 2026 | **Yes** | — |
| RB `HANDCUFF`, backtestable | **No** | Week-1 `depth_charts_weekly` as a labelled proxy |
| WR target-share tiers | **Yes** (2009+) | — |
| WR depth modifier (aDOT) | **Yes** (2009+) | — |
| WR slot / outside | **No — BLOCKED** | Alignment data; `load_participation` gets route participation but **not** slot rate |
| TE tiers | **Yes** | — |
| TE in-line vs move (Y/U) | **No — BLOCKED** | Alignment data. Same blocker |
| QB dual-threat / pocket / balanced | **Yes** | — |
| QB volume modifier | **Unconfirmed** | Confirm `attempts` exists in `player_weekly_stats` |
| D5 scoring composition | **Yes** | — |
| D6 volatility | **Reserved** | FR-086's result; not defined here |
| D9 role stability | **Yes** (2014+) | — |
| Route participation / YPRR | **No** | `load_participation()` ingest + aggregation |
| Coach/scheme-conditioned archetypes | **No** | `play_callers` table does not exist in `nfl.db`; the module is parked awaiting an external source |
| DEF / K | **Out of scope** | Not proposed. No archetype is offered for these |

---

## 6. What would make any of this more than a vocabulary

Ranked by value per unit of effort. None has been done.

1. **Plot the distributions and check the cuts** (R3). The original brief asked for this in 2026-07-26
   and it has never been run. Every threshold in §3 is a convention until it is.
2. **Run the §4.2 gates against the current system and against this proposal**, and report both.
   If the new taxonomy also puts 50% of TEs in one bucket, it is not an improvement.
3. **Do archetypes predict anything?** The honest test: does knowing a player's t−1 archetype
   improve a t projection *beyond* the continuous dimensions it was derived from? If not, the
   archetype is a display convenience — which is a fine thing to be, and should then be stated as
   such rather than implied to be a model.
4. **Does the chip change a draft decision?** `CLAUDE.md` §6.6's point: better lists are a proxy;
   better rosters are the question.

---

## 7. Sources

Fetched directly this session:
[Footballguys — The Running Back By Committee Conundrum](https://www.footballguys.com/article/2025-running-back-by-committee-conundrum) ·
[Sharp Football — Fantasy Notebook: WR Correlations, Usage, and Archetypes](https://www.sharpfootballanalysis.com/fantasy/fantasy-notebook-wr-correlations-usage-and-archetypes/) ·
[Sharp Football — Tight End Archetypes and Usage](https://www.sharpfootballanalysis.com/fantasy/tight-end-archetypes-usage-snaps-routes-targets-2020/) ·
[PFF — Studying tight end utilization](https://www.pff.com/news/fantasy-football-studying-tight-end-utilization) ·
[PFF — Studying wide receiver utilization](https://www.pff.com/news/fantasy-football-studying-wide-receiver-utilization) ·
[FantasyPros — 7 Konami Code Rushing Quarterbacks](https://www.fantasypros.com/2024/08/konami-code-rushing-quarterbacks-august-fantasy-football/) ·
[Fantasy Points — 2025 UFL Bell Cow Report](https://www.fantasypoints.com/ufl/articles/2025/ufl-bell-cow-report) ·
[PlayerProfiler — Terms Glossary](https://www.playerprofiler.com/terms-glossary/)

Seen in search excerpts only, page did not render:
[Dynasty League Football — Dynasty Archetypes: Wide Receiver](https://dynastyleaguefootball.com/2026/03/27/dynasty-archetypes-wide-receiver-3/) (HTTP 403) ·
[Dynasty League Football — Dynasty Archetypes: Running Back](https://dynastyleaguefootball.com/2026/03/22/dynasty-archetypes-running-back-3/) ·
[RotoBaller — Bell Cow Running Backs 2025](https://www.rotoballer.com/4-bell-cow-fantasy-football-running-backs-to-target-in-drafts-2025/1626217) (body did not render) ·
[FTN — Fantasy Football Cheat Code: Find QBs that Run](https://www.ftnfantasy.com/articles/Eliot/26935/fantasy-football-cheat-code-find-qbs-that-run) (HTTP 403) ·
[FantasyPros — Draft Wizard draft software](https://draftwizard.fantasypros.com/football/draft-software/) ·
[RotoViz — Tools](https://www.rotoviz.com/tools-2/)

**Not fetched, by standing project rule:** Yahoo, ESPN and CBS hosts. Any archetype vocabulary
those products use is unmeasured here.
