# Consistency audit — three handoffs, 17 states
**Generated:** 26 July 2026 · **Canonical tokens:** `tokens.json` · **Inventory:** `components.json`

Unkind as requested. Severity: **DEFECT** = ships wrong today · **DRIFT** = two ways to do one thing ·
**GAP** = a concept exists on one screen and is missing where it is needed.

Two findings change shipped screens. Both are called out as **RETROFIT** with a cost estimate.

---

## Null rendering — the most important section

The product's identity is that `0`, `0%`, `—` and "not computed" are four different claims. Audit
result: **the vocabulary is right and the application is not consistent.**

### NULL-01 · DEFECT · `·` carries two incompatible meanings
`·` is used for "no meaningful change" in every delta column (Draft board, prep board, Settings diff)
**and** for "live value not computed" in the Draft board's base→live cell.

So in one row, `·` in the delta column means "the market agrees with us" and `·` in the next column
means "we have no answer". Those are opposite epistemic claims sharing a glyph.
**Resolution:** `·` is reserved for "no meaningful change". The not-computed case in a narrow cell
renders `—`, with the reason in the existing `title`. `tokens.json#nullGlyphs` now states this.
**Cost:** one line in the Draft board row. **RETROFIT-1.**

### NULL-02 · DEFECT · "not yet" vs `·` for the same state
The same missing live probability renders three ways: `·` (Draft board), `not yet` (Draft
predictions), `not computed yet` (player panel). All three are honest; three phrasings for one state
is not a system.
**Resolution:** `—` in narrow cells with the reason in `title`; `not yet` plus the picks-logged count
wherever there is room for a phrase. Two treatments, chosen by space, documented.
**Cost:** copy only. **RETROFIT-1** (same edit).

### NULL-03 · DEFECT · Mock Lab overloads `—` for "outside the top five"
In the logging candidate list, the probability column renders `—` for a player the model did not rank
in its top five. That is not "no value exists" — the model has a view, it is just below the cutoff.
Rendering it as a null makes a real cutoff look like missing data.
**Resolution:** render `<5%` (below the display floor for that list) or an explicit `unranked`.
**Recommend `unranked`** — it is a categorical fact, not a small number.
**Cost:** one expression in `Mock Lab.dc.html`. **RETROFIT-2.**

### NULL-04 · PASS
`—` for absent projections, `<1%` for sub-floor availability, `player_id = unknown` for off-board
players, `league.draft_date = null` and `mocks[league=…] = []` as literal field states: consistent
across all three handoffs, and each states the field name. No action.

---

## The 10-dot frequency array

### DOTS-01 · DRIFT · five sizes for one idiom
Found at 5px (draft queue), 6px (draft predictions), 8px (player panel), 9px (explorer tier card),
11px (calibration rows).
**Resolution:** three sizes — `--dot-sm` 6px, `--dot-md` 8px, `--dot-lg` 11px. 5px and 9px retired.
**Cost:** two values in Draft, one in the explorer. Cosmetic; batch with the next Draft touch.

### DOTS-02 · NOT A DEFECT — document as variants
Availability dots fill in **band colour**; calibration dots fill in **neutral `--txt`** with a ▲
marker. I checked whether this was drift. It is not, and the distinction is worth keeping: an
availability figure is *actionable* so colour carries urgency, while a calibration figure is *being
audited* so colour must not editorialise the number under inspection. Colouring calibration dots by
band would tell the reader what to think about the very number they are checking.
**Action:** recorded as two named variants in `components.json`, not flattened.

### DOTS-03 · PASS
`fill = round(p*10)` and the "N in 10 drafts" phrasing are identical in both places.

---

## Numeric vs label typography

### TYPE-01 · DEFECT · position labels lose their letter-spacing in Settings
Roster slot labels (`QB`, `RB`, `FLEX`) render as plain sans 600 at 13px with no letter-spacing,
while the same codes in Draft and Mock Lab use `--f-ui` at 10.5–11px with `letter-spacing:.045em`.
Same token, two treatments — and the Settings one reads as a word rather than a code.
**Resolution:** apply the label treatment. **Cost:** one style string. **RETROFIT-3** (trivial).

### TYPE-02 · PASS
No monospace on any name, prose, nav item or button label across 17 states. `tabular-nums` is present
on numeric cells and absent from prose. Team codes are sans everywhere except where TYPE-01 applies.

### TYPE-03 · NOTE
Mock Lab's mini board grid uses `--f-num` at 8px for round and team indices. Those are ordinals, not
measurements — arguably `--f-ui`. At 8px it is indistinguishable; leaving it, flagged so nobody
"fixes" it in one place only.

---

## Stale, loading and disabled

### STALE-01 · GAP · RETROFIT · Mock Lab needs staleness and does not have it
This is the important find. Settings established that a scoring or roster change invalidates every
derived number. **Calibration buckets are derived numbers.** A mock logged under 0.5 PPR was scored
against availability probabilities computed for 0.5 PPR; change the league to 1.0 PPR and those
buckets describe a league that no longer exists.

Today Mock Lab has no stale treatment at all, so after a scoring change the calibration screens keep
presenting their dots at full contrast. That is exactly the failure Settings was designed to prevent,
on the screen whose entire purpose is honesty about what we know.

**Resolution:** three parts.
1. Store `league_settings_hash` on every mock at log time.
2. Any bucket pooling mocks whose hash ≠ the league's current hash renders with the existing stale
   treatment (`--hatch`, dagger, `--dim2`) and a section tag naming when they were logged.
3. Mock Lab gains the `StatusBanner` component in a `stale` variant.

**Cost:** one new field, one comparison, and reuse of an existing component. **Do this before the
fourth screen** — the alternative is a calibration curve that silently mixes two scoring systems,
which is worse than having no curve.

### STALE-02 · GAP · abandoned mocks have no representation
Per Part 1: partials are not missing at random — people abandon lopsided drafts, which may correlate
with what is being predicted. There is currently no state for a mock that stopped at round 7.
**Resolution:** a mock has `rounds_logged` and a status of `complete` | `partial`. A partial renders
as a countable artifact with its round count, never as an error or a lesser row, and the aggregate
view states how many of its calls came from partials. **RETROFIT-4** — needs a small design pass,
folded into the next Mock Lab touch.

### DISABLED-01 · PASS
Settings steppers go inert rather than hidden during a job, with the reason in the banner. This is the
right pattern and the only place it currently occurs; `components.json` records it as the rule.

---

## Colour carrying meaning alone — all 17 states

### COLOUR-01 · PASS with one note
Every colour-carried signal audited has a redundant cue: deltas carry ▲▼, verdicts carry ●○, scarcity
pace carries a signed number, stale carries hatch + dagger, calibration direction carries the ▲
position **and** a generated sentence, pending values carry strikethrough plus an arrow.

The one thin case: the queue toggle differs by colour (`--acc` when queued) **and** by word
(`queued` / `+ queue`). The word carries it, so it passes — but the word is the cue, not the colour,
and a future "compact" variant that drops the label would break it. Noted so it is not dropped.

### COLOUR-02 · PASS · `--fail` vs `--live`
Confirmed distinct in both themes and never co-occurring. Failure is not urgency.

---

## Cross-cutting structural findings

### STRUCT-01 · DRIFT · ValuePair built twice
`baseline → live` (Draft) and `in force → edited` (Settings) are the same component: two values, the
second never replacing the first, with a rule that makes rendering one alone impossible. They were
built independently with different markup.
**Resolution:** one `ValuePair` with two variants — `components/value-pair.dc.html`. This is the
highest-value merge in the audit and the one most likely to diverge further if left.

### STRUCT-02 · DRIFT · TypeAhead built twice, and the better one is not in Draft
Draft's pick entry has type-ahead with ↑↓ and Enter. Mock Lab's adds **digits 1–5 committing
directly** and `Backspace` undo, which is materially faster.
**Resolution:** back-port digit shortcuts and Backspace-undo to Draft's pick entry. Same component.
**Cost:** small. High value — Draft entry is used under a pick clock.

### STRUCT-03 · DRIFT · five progress treatments
Job bar, banner rail, count bar, target array, evidence ladder. Four are genuinely different claims
and stay. The banner rail (3px) and job bar (5px) are the same claim at two heights.
**Resolution:** 3px in banners, 5px in panels. Documented, not merged.

### STRUCT-04 · DRIFT · chip radius was inconsistent
Five treatments where three were intended. Now explicit: `--r-c` rounded = interactive filter,
`--r-pill` = display-only and non-sortable, square = structural label or verdict.

### STRUCT-05 · NOTE · grid budget was learned twice
Both Settings and Mock Lab shipped a clipped-column defect caught in review (`minmax(0,…)` collapsing
a text column; a non-wrapping header pushing chips off-screen). The rule is now in
`tokens.json#density.gridBudget` so the third screen does not learn it a third time.

---

## Retrofit summary

| # | What | Where | Cost | When |
|---|---|---|---|---|
| RETROFIT-1 | `·` → `—` for not-computed; two phrasings not three | Draft board, predictions, player panel | one expression + copy | next Draft touch |
| RETROFIT-2 | `—` → `unranked` for below-cutoff candidates | Mock Lab logging | one expression | next Mock Lab touch |
| RETROFIT-3 | position-label typography in Settings | Settings roster rows | one style string | next Settings touch |
| RETROFIT-4 | abandoned/partial mocks as countable artifacts | Mock Lab | small design pass | next Mock Lab touch |
| **STALE-01** | **mock calibration must go stale on settings change** | **Mock Lab + backend field** | **one field, one comparison, existing component** | **before the fourth screen** |

Everything except STALE-01 can wait for the next natural touch of its screen. STALE-01 should not —
it is the one finding where the current build makes a claim it cannot support.

---

## Part 1 items now folded in

- `entry_mode` per pick is assumed to exist. It must be **visible in the review state** so a user
  auditing their own mock can see how each pick was entered. Added to `components.json` under
  `data-row` variants and to the Mock Lab retrofit list.
- **Randomising the order of the five** is adopted as the recommended mitigation: still one keystroke,
  but position no longer encodes our confidence. It needs a paired change — the displayed probability
  must stay attached to its player, so the list is shuffled while the numbers travel with the rows.
  Flagged in `components.json#typeahead`.
- Per-league calibration targets, personal-primary pooling, and partials-with-`rounds_logged` are all
  reflected above.

---

# Retrofit specifications

**Added 26 Jul 2026.** The table above says what is wrong and what it costs. This section says what to
build, so each can be picked up at its screen's next touch without re-deriving anything.

## RETROFIT-1 · not-computed glyphs · Draft
**Files:** Draft board row, predictions table, player panel availability block.

Two treatments, chosen by available space, and nothing else:

| Space | Renders | Also |
|---|---|---|
| narrow cell (< 70px) | `—` | full reason in `title` |
| roomy (panel, wide column) | `not yet` + the count that would satisfy it | no title needed |

Concretely: the Draft board's base-to-live cell renders `—` where it currently renders `·`. The
predictions table and player panel keep `not yet` but must use that exact string — `not computed yet`
is retired.

**`·` is reserved for "no meaningful change" in a delta column and must not appear anywhere else.** Add
a lint-style check: any `·` outside a delta column is a defect.

**Done when:** no screen renders `·` for a missing value, and the phrase appears in exactly one form.

## RETROFIT-2 · below-cutoff is not null · Mock Lab
**File:** Mock Lab logging, candidate list probability column.

A player the model did not rank in its top five has a view attached to him — he is below a cutoff, not
absent from the data. Render `unranked` in `--dim2`, not `—`.

Rationale worth keeping in the code comment: `—` claims no value exists. A cutoff is a categorical
fact, and rendering it as a null teaches the user to distrust every other `—` in the product.

**Done when:** the candidate list shows `unranked` for out-of-top-five rows and `—` for nothing at all.

## RETROFIT-3 · position-label typography · Settings
**File:** Settings roster slot rows.

Change the slot label from `font-size:13px;font-weight:600` to the canonical position-code treatment:

```
font-family: var(--f-ui);
font-size: 11px;
font-weight: 600;
letter-spacing: .045em;
```

The colour rule stays as-is (the 3px position-coloured rule left of the label). Applies to QB, RB, WR,
TE, FLEX, DEF; **not** to Bench and IR, which are words rather than position codes and keep sentence
case at 13px.

**Done when:** a position code renders identically in Settings, Draft and Mock Lab.

## RETROFIT-4 · partial mocks as countable artifacts · Mock Lab
**Files:** Mock Lab mock list, review header, aggregate header. **Includes the design pass.**

A mock has `rounds_logged` and `status: 'complete' | 'partial'`. Per the founder note, partials are
**not missing at random** — people abandon lopsided drafts, which may correlate with what is being
predicted.

- **Mock list row.** A partial shows `R1–R7` in the picks column instead of a total, in `--dim` not
  `--down`. No warning icon, no lesser styling, no error colour. It is a shorter artifact, not a
  failed one.
- **Review header.** Tag chip: *"partial — rounds 1–7 logged"*. Rounds 8–16 render as one explicit empty
  region stating `picks 71–160 not logged`, never as blank rows.
- **Aggregate header.** One added clause: *"N of M calls came from partial mocks (rounds 1–7)."* This is
  the sentence that matters — a reader must be able to see that the evidence leans early-round.
- **Calibration.** Partials are **included** by default. Excluding them would discard most of the
  availability decisions in the product, since rounds 1–6 carry nearly all of them.
- **The bias, stated once** in the aggregate footnote: *"Abandoned drafts are not a random sample.
  Managers stop when a draft goes lopsided, which may correlate with the picks we are predicting."*

**Done when:** a partial is countable, readable, visually equal to a complete mock, and the early-round
lean is stated where the pooled numbers are read.

## RETROFIT-5 · TypeAhead back-port · Draft
Specified in `design_handoff_draft_assistant/screens/01-draft-board.md` §Pick entry. Same component as
Mock Lab logging: digits 1–5 commit, Backspace undoes, autofocus asserted on mount and on node attach,
candidate order randomised so position does not encode confidence.

**Done when:** Draft pick entry and Mock Lab logging use one component with one key map.
