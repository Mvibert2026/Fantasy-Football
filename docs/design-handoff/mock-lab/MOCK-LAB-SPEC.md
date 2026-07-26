# Screen — Mock Lab
**Spec id:** `mocklab` · **Pinned:** 26 Jul 2026 · **Reference:** `reference/01-empty` … `07-aggregate`
**Machine-readable:** `spec/mocklab-tokens.json`, `spec/mocklab-screen.json` · **Assert against:** `spec/mocklab-screen.json#checks`

---

## 1. The problem is arithmetic, not analytics

Validating the calibration claim needs ~30 mocks × ~160 picks = **~4,800 entries**. There is one mock
logged. Every extra interaction per pick costs 4,800 interactions across the target, so entry cost is
the only thing on this screen that decides whether the claim ever becomes true.

That produces one design rule: **make the model's own prediction the fastest input device.**

Before every pick the model already ranks the five players most likely to go next. Those five are
rendered as a numbered list, so the common case is **one keystroke** — press `2`, the pick is logged,
the list re-ranks, focus never moves. Typing is the fallback, not the default. And it compounds
correctly: the better calibrated the model gets, the more picks its top five covers, and the faster
logging becomes.

Three modes, because the realistic user arrives in three different situations:

| Mode | Cost | When |
|---|---|---|
| **Keyboard** | ~2s / pick · ≈5 min per mock | logging live as the mock happens |
| **Paste** | one action + reconcile · ≈1 min | the mock site ended on a results grid |
| **Grid** | ~4s / pick · ≈11 min | working from a screenshot, or fixing gaps |

Paste is the 100× win and should be the marketed path. It is also where the honesty risk lives (§4).

**Header budget.** The top bar is a single non-wrapping row. Every string in it must fit a 924px
viewport with all seven state chips reachable: the state eyebrow is short (`REF · LOGGING`) with the
long form in a `title`, the league line shrinks with `min-width:0` and carries its full form in a
`title`, and the chip group is `flex:0 1 auto; min-width:0; overflow-x:auto` so it scrolls rather
than pushing content off-screen. Assert `documentElement.scrollWidth === clientWidth`.

**Autofocus is load-bearing, not a nicety.** The screen prints "never needs the mouse" beneath the
field, so focus must be asserted on mount *and* re-asserted when the input node attaches — a one-shot
guard that fires before the element is focusable leaves the claim false on load.

## 2. Keyboard entry — the details that carry the speed

```
ON THE CLOCK  R3.01  The Cucked Commish     LOGGED 22/160  2.1s/pick  ~5m left
┌──────────────────────────────────────────────────────────┐
│ Type a name — ⏎ logs the highlighted pick, 1–5 by number │  ← autofocused
└──────────────────────────────────────────────────────────┘
⏎ log highlighted   1–5 log by number   ↑↓ move   ⌫ undo last   never needs the mouse
MODEL'S TOP FIVE — MOST LIKELY OFF THE BOARD NEXT        frozen on entry
 1  Ja'Marr Chase      WR1  CIN  #1   39%
 2  Bijan Robinson     RB1  ATL  #2   26%
```

- **Autofocus on mount.** A person logging 160 picks should never click into the field.
- **Digits 1–5 commit directly.** `⏎` commits the highlighted row. `↑↓` moves. `⌫` on an empty field
  undoes the last pick — undo must be reachable without leaving the keyboard.
- **Auto-advance.** Committing clears the field, advances the pick counter and re-ranks. No "next" button.
- **Tempo readout is live**: seconds per pick and an estimated finish, computed from real entry
  timestamps. It exists so the grind is visibly finite. It is a measurement, not a motivator.
- **Off-board players still log.** A name outside our 70-player board records as
  `player_id = unknown` with the typed text kept, and is **excluded from calibration rather than
  dropped** — dropping would bias the exact thing this screen measures.

## 3. Predictions are shown as they were made

Every probability in the review table was written when the pick was entered and is never recomputed.
The review screen states this in a locked banner rather than a footnote, because the constraint is
the product's premise: **a wrong prediction is the most valuable row on this screen.**

Review grid: `38px 62px minmax(0,1.1fr) 44px minmax(0,1.1fr) 78px 74px 62px` —
`# · TEAM · ACTUAL PICK · POS · OUR TOP CALL · WE SAID · VERDICT · SURPRISE`

Verdict is HIT / MISS with a filled or hollow dot as the non-colour cue.
`surprise = board.overall_rank − pick.n`; positive means he went later than our board said. It
describes the draft, not the manager.

Fields: `mock.picks[].predicted_top`, `predicted_p`, `in_top_5` — write-once at entry.

## 4. Calibration, communicated visually

The claim a reader cares about is *"when it says 33%, does it happen about a third of the time?"* So
each bucket is **one row of ten dots** — reusing the existing frequency idiom rather than inventing a
second one:

```
WE SAID   WHAT HAPPENED          OBSERVED  READING                              CALLS
35%       ●●●●○○○○○○                  40%  it happened more often than we said     92
             ▲                              — under-confident by 5 points
```

- **Filled dots = what happened.** Ten dots are ten drafts.
- **▲ sits under the dot index we predicted.** Triangle left of the fill edge → under-confident.
  Right of it → over-confident. Under the edge → honest. That comparison is readable without knowing
  the word "calibration".
- **A plain-language reading per row**, generated from the numbers, never hand-written.
- **Thin buckets** (< 50 calls) get the existing `--hatch` on the call count and a reading that
  refuses to interpret: *"2 of 9 — too few calls to read."*
- **Brier score is kept and demoted** — small, mono, in a "for the record" card with a tooltip
  explaining it. It is the measure; the dots are the claim.

Direction of error is carried by the ▲ position *and* the sentence, so colour is never the only cue.

## 5. Progress toward 30 — without homework

The aggregate view shows 30 squares, one per mock, filled for logged. Above it sits the thing that
actually changes: **the width of the confidence band.**

```
1 mock    ±32 pts   one draft is an anecdote
10 mocks  ±10 pts   tails still untested
20 mocks  ±7 pts    middle of the range readable
30 mocks  ±6 pts    every bucket testable
```

Bar length is the real 95% Wilson half-width at that sample size. **No badges, streaks, levels or
congratulation.** The honest incentive already exists — filling a square narrows the band — and the
screen says exactly that: *"the only thing that changes when you fill one is that the band above gets
narrower."*

The near-empty state (one mock) is the **real** starting case and gets its own reference file. It
leads with "one draft is an anecdote" rather than drawing a confident chart over nine calls.

## 5a. Configuration and staleness

**Amended 26 Jul 2026.** Originally out of scope; now build-blocking. A mock's calibration value
depends entirely on the league configuration it was logged under, so the configuration is part of the
record — not metadata about it.

### The stamp
Every mock stores `league_settings_hash` **at log time**, using the same 15-field hash as Settings,
plus `config_summary` for display (`10T · 0.5 PPR · 3WR/2FLEX · no K`).

Write it on `POST /api/mocks`, never on read. A hash computed at read time is the same defect as a
prediction recomputed at read time: it will always look consistent and always mean nothing.

### Three configuration states — not two

| State | Condition | Calibration | Why |
|---|---|---|---|
| `current` | hash matches the league's hash now | **included** | describes the league you are in |
| `stale` | hash present, differs | **excluded by default, includable** | describes a real league, just not this one |
| `unknown` | hash is `null` | **excluded, and NOT includable** | logged before the field existed |

`unknown` is not hypothetical. Every mock logged before the field ships is permanently unstampable,
and a mock whose configuration is unknown can be neither honestly included nor honestly excluded — so
it is excluded, counted, and labelled, with **no affordance to opt in.** There is no basis on which a
user could make that call, so offering the choice would be false precision dressed as control.

This is why the field cannot wait: at one logged mock it costs nothing, and every mock logged without
it is unrecoverable.

### Configuration is the grouping key, not a flag
If the 30-mock target is per configuration — the current default — this stamp **is the grouping key for
the entire calibration analysis**. The aggregate view is therefore *pooled within a configuration*,
never *pooled across mocks*:

- A **configuration selector** heads the aggregate view: one row per distinct hash with its
  `config_summary`, mock count, and whether it is the current league. Default is the current config.
- The 30-square target array and the evidence ladder both count **within the selected configuration**.
- Old configurations stay viewable as history, labelled as not describing this league.

### What goes stale inside a mock — and what does not
**Not everything in a stale mock is stale.** The draft happened; the picks are facts. Only model
outputs are invalidated.

| Column | On a stale mock | Why |
|---|---|---|
| `#`, `TEAM`, `ACTUAL PICK`, `POS` | **fresh** | facts about what happened |
| `WE SAID`, `OUR TOP CALL`, `VERDICT` | **stale** | availability outputs under the old scoring |
| `SURPRISE` | **stale** | derived from `board.overall_rank`, which moves with scoring |

Treating the whole row as stale would be the easier build and the wrong one: it would imply we are no
longer sure what the manager picked.

### Treatment per state

**Review state.** The mock header gains a configuration chip:
- `current` — tag chip, `--dim2`, showing `config_summary`.
- `stale` — tag chip in `--down`: *"logged under 10T · 0.5 PPR — your league is now 1.0 PPR"*. The
  three derived columns take the standard stale treatment (`--hatch`, dagger, `--dim2`); the fact
  columns do not. The frozen-prediction banner stays — predictions are still shown as they were made.
- `unknown` — tag chip in `--dim2`: *"configuration not recorded — logged before we stamped mocks"*.
  Same column split, excluded from every aggregate, and the chip says so.

**Calibration dots.** A stale or unknown bucket keeps its filled dots — the observation is real — but
drops them to `--dim2`, adds `--hatch` behind the dot row, a dagger after the observed value, and dims
the generated reading. The marker stays at full contrast: where we said it would land is still a fact
about what we claimed.

**Aggregate view.** The header is always explicit:

```
POOLED WITHIN 10T · 1.0 PPR · 3WR/2FLEX · no K        [ configuration v ]
3 of 8 mocks included · 4 excluded (different configuration) · 1 excluded (configuration not recorded)
```

An **Include other configurations** toggle exists for the stale set only. When on:
1. every bucket row takes the stale treatment,
2. the header states which configurations are mixed and in what proportion,
3. **the Brier score is suppressed entirely** — replaced by *"not computed across mixed
   configurations"*. A single score spanning two scoring systems is not a worse number, it is not a
   number. Showing nothing is the honest option.

**All mocks stale — the realistic case right after a scoring change.** Not an error state. The
aggregate renders its empty form:

> **0 of 8 mocks describe your current configuration.** Calibration for 10T · 1.0 PPR starts from
> zero. Your eight logged mocks are still here and still valid for the configuration they were logged
> under — switch configuration above to read them.

The evidence ladder resets to the one-mock rung and the 30-square array shows zero filled for this
configuration. This is the harshest consequence of per-configuration targeting and the screen states
it plainly. Softening it would misrepresent how much evidence exists, which is the one thing this
screen exists not to do.

**Banner.** Mock Lab gains `StatusBanner` in the `stale` variant whenever the selected configuration is
not the league's current one: *"Reading calibration for a configuration your league no longer uses."*

### Backend additions

```json
POST /api/mocks   -> { "mock_id": "mk_002", "league_settings_hash": "teams=10·…·rtd=6",
                       "config_summary": "10T · 0.5 PPR · 3WR/2FLEX · no K" }
GET  /api/mocks   -> each mock carries hash, config_summary, config_state
GET  /api/validation?config_hash=…
                  -> { "buckets": [...],
                       "configs": [{ "hash": "…", "summary": "…", "mocks": 4, "is_current": false }],
                       "excluded": { "different_config": 4, "unrecorded": 1 } }
```

`config_state` is derived server-side (`current`|`stale`|`unknown`) so the client never re-implements the
comparison. Validation **must** accept a config hash; a pooled-across-everything response has no
honest use.

## 6. States

| File | State | Why it exists |
|---|---|---|
| `01-empty` | no mocks | `mocks = []`; sells the three entry modes and what logging buys |
| `02-one-logged` | **one mock — the real case** | nine calls cannot separate calibrated from lucky, and it says so |
| `03-logging` | entry in progress | the speed design; tempo readout live |
| `04-paste-reconcile` | **added** — bulk paste | exact / fuzzy / no-match rows before commit |
| `05-review` | pick-by-pick | predictions as made, locked banner |
| `06-calibration` | one mock's calibration | every bucket thin; the honest read says so |
| `07-aggregate` | pooled + progress | 7 mocks, band narrowing, thin buckets still marked |
| `08-stale-config` | **added** — stale review + mixed aggregate | the treatment above, at build fidelity |
| `09-all-stale` | **added** — every mock stale | the realistic state right after a scoring change |

`04-paste-reconcile` was not in the brief. It is included because paste is the only mode whose cost
does not scale with 160, so it is the mode most likely to decide whether 30 mocks happen — and it is
the one that needs a reconcile design, since a fuzzy name match that silently resolves wrong would
corrupt the calibration data quietly.

## 7. Backend contract

```json
POST /api/mocks                        → { "mock_id": "mk_002", "teams": 10, "slot": 3 }
POST /api/mocks/:id/pick
{ "n": 27, "team_slot": 6, "player_id": 17,
  "raw_text": "Team 7  Trey McBride  TE  ARI",
  "predicted_top": 17, "predicted_p": 0.62, "in_top_5": true,
  "entered_at": "2026-07-26T18:04:11Z" }
POST /api/mocks/:id/picks/bulk         → { "committed": 148, "unresolved": 12 }
GET  /api/mocks/:id/review             → picks with predictions as written
GET  /api/validation?mock_id=…|pooled  → { "buckets":[{"stated_mid":0.35,"n":92,"observed":37}] }
```

Requirements: `predicted_*` are **write-once** — reject an update rather than overwrite.
`raw_text` is retained on every row so a bad match stays auditable. `entered_at` per pick is what
makes the tempo readout real. Validation returns **counts**, never percentages.

---

## 8. Decisions for the founder

1. **Does offering the model's top five bias the logged data?** Presenting our own prediction as the
   fastest key risks a user hammering `1` and logging what we guessed rather than what happened.
   Mitigations range from doing nothing, to hiding probabilities during entry, to a periodic blind
   spot-check. *No recommendation — this trades the entry speed the whole screen depends on against
   the integrity of the only data that validates the product. It needs your call, not mine.*
2. **Is 30 the right target, and is it per league or global?** A 10-team half-PPR mock may not
   validate a 12-team full-PPR league. If the target is per league the grind multiplies. *No
   recommendation — depends on whether calibration is claimed per league or per model.*
3. **Do other people's mocks count?** Pooling across users reaches 30 far faster and is the obvious
   growth loop, but it changes the claim from "calibrated for you" to "calibrated on average".
   *Recommendation: keep the personal view primary, treat pooled as a separate labelled number.*
4. **Is a partial mock worth logging?** Rounds 1–6 carry nearly all the availability decisions.
   Accepting partials would cut the cost per mock by two-thirds. *Recommendation: accept them, and
   record `rounds_logged` so calibration can weight or filter.* Confirm.

## 9. Questions for the backend engineer

These are facts about the system I had to assume. Each one changes the design if the answer is no.

1. **Can `predicted_top` and `predicted_p` be written at entry time and made immutable?** The whole
   review and calibration design rests on it. If predictions can only be recomputed on read, §3 and
   §4 are both invalid.
2. **Is there a bulk pick endpoint, and does it return per-row resolution?** The reconcile table needs
   per-row exact / fuzzy / no-match status, not an aggregate count.
3. **Does the player matcher exist server-side, or does the client fuzzy-match?** The reference
   fuzzy-matches client-side against a 70-player board. Against 378 players with nicknames and
   suffixes, this should be a server endpoint.
4. **Can a pick store `player_id = unknown` plus `raw_text`?** Required so off-board players are
   excluded from calibration rather than dropped.
5. **Is `entered_at` recorded per pick?** Without it the tempo readout and the "logged in 6m 12s"
   figure are not real numbers and must come out.
6. **Are validation buckets available per-mock as well as pooled?** `06-calibration` needs per-mock;
   `07-aggregate` needs pooled.
