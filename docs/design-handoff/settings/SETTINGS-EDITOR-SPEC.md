# Screen — Settings editor
**Spec id:** `settings.editor` · **Pinned:** 26 Jul 2026 · **Reference:** `Settings_Editor_reference.dc.html`
**Machine-readable:** `spec/settings-tokens.json`, `spec/settings-screen.json` · **Assert against:** `spec/settings-screen.json#checks`

---

## 1. The decision, up front

**Shadow recompute with an atomic, user-triggered swap.** The job runs in the background, the app
stays fully usable, nothing on screen changes, and the new values land only when the user presses
**Apply**.

### Why not the two obvious options

**Freeze the app behind a modal.** Satisfies principle #3 trivially, and it is the wrong trade. Sixty
seconds is long enough that a modal reads as a hang, and the user's reason for being here — checking
what their format does to the board — is exactly what gets taken away. It also makes failure worse:
if the job dies at 40s the user has paid the whole cost for nothing.

**Let them navigate with every affected number marked stale.** A scoring change invalidates
essentially every number in the product, so this hatches out the entire app. It is a slower freeze
with more visual noise, and it teaches the user to ignore the stale treatment — which we need them
to respect later, for the case where it is genuinely load-bearing (§5).

### The reframe that makes the third option work

**The pre-edit numbers are not stale. They are correct.** The change has not been applied, so the
scoring in force is still the old scoring, and every number computed under it is exactly right. What
is happening in the background is a *proposal*.

That reframing dissolves the problem:

- Nothing is greyed, hatched, or disabled during the 60 seconds. The app is trustworthy because it
  is showing true values.
- Principle #3 is satisfied **by construction**, not by vigilance: there is no moment when some
  numbers are new and others old, because the swap is one state transition.
- Failure is trivially safe. Nothing was applied, so there is nothing to unwind and no "recovery"
  flow to design (§6).
- The user is never ambushed. Auto-applying at second 60 would rearrange the board under someone
  mid-scan; requiring Apply means the change lands when they are ready for it.

The banner does the honest work: *"Every number in the product is still under the scoring in force."*
That sentence is the whole design.

---

## 2. Two tiers of change

| Tier | Trigger | Cost | Behaviour |
|---|---|---|---|
| **1** | roster slots, bench, IR, flex eligibility, team count, draft slot | recomputes replacement levels, VBD, tiers | **Applies instantly, client-side.** No job, no spinner, no pending state |
| **2** | any scoring value: PPR, pass TD, rush/rec TD, interception, fumble, yardage bonus thresholds | recomputes 378 projections, then everything downstream | **Pending until an explicit recompute + apply.** ~60s job |

**Both tiers invalidate the availability simulation**, which is a separate 20,000-draft job. This is
the asymmetry worth designing for: a tier-1 change is instant *and* leaves availability stale. A user
who adds a bench slot gets new VBD immediately and a hatched availability column until they rerun the
simulation. Label the sections with their tier so this is predictable rather than surprising.

---

## 3. Editing surface

Two-column layout: editor (fluid) | status rail (372px, own scroll).

**Roster shape** — one row per slot: colour rule in the position colour, label, count in mono at
15px, −/+ steppers, backing field. Slots: QB, RB, WR, TE, FLEX, DEF, Bench, IR. Reference league:
1/2/3/1/2/1, 6 bench, 1 IR.

**FLEX eligibility** — a checkbox row of RB / WR / TE / QB rendered as chips. QB off by default;
turning it on is superflex. Field `league.flex_eligible`.

**Scoring rules** — grid `minmax(88px,1fr) 52px 14px 52px 80px minmax(120px,1.15fr)`, gap 8px, columns:
RULE · IN FORCE · → · EDITED · steppers + revert · FIELD.

An edited row shows **both values**: in-force struck through in `--dim2`, edited in `--down` at
weight 600, arrow between, row background lifted to `--panel2`, and a ↺ revert for that rule alone.
The container border turns `--down` while any edit is pending. This is the same
never-collapse-two-numbers-into-one rule as the availability pair on the Draft screens.

**Yardage bonuses** — threshold rows (100 / 150 / 200 yards → points), same old→new treatment.
Field `league.yardage_bonuses[]`.

**Field-name affordance.** A field cell may drop a prefix that the whole column shares, provided the
column header names it (`FIELD · league.scoring.*`) and the **full dotted path is in a `title`**.
Field names are user-visible trace affordances; a truncated one with no hover fallback is a broken
affordance, not a cosmetic issue. Assert `scrollWidth <= clientWidth` on every field cell, not a
pixel floor — a 100px track passes a ">= 84px" check while still clipping `rush_rec_td`.

**Track sizing constraint.** All three grids on this screen live in the fluid left pane, which is
502px at a 924px viewport. Every track set must fit that width, and **no track may use a zero floor**
(`minmax(0,…)`) — the FIELD column collapses to invisible if it does, which breaks the trace
affordance that makes field names user-visible. Assert `scrollWidth === clientWidth` on the roster,
scoring and board-preview grids.

Steppers are inert while a job is in flight — editing mid-recompute would invalidate the result the
user is waiting for. Do not hide them; let them not respond, with the reason in the banner.

---

## 4. The six states

One state machine drives the banner, the status rail, and the treatment of every number in the app.

| State | Field condition | Banner | App |
|---|---|---|---|
| **in force** | `pending_settings = null` | none | everything fresh |
| **pending** | edits held, no job | `SCORING CHANGE QUEUED` — "Every number in the product is still under the scoring in force." | fully usable, all fresh |
| **computing** | job running | `RECOMPUTING` + stage + percent + 3px progress rail | fully usable, all fresh, steppers inert |
| **ready** | job complete, not applied | `NEW VALUES READY` — "Review the diff, then apply. The swap is one step." + **Apply** / **Keep old** | still showing old values |
| **failed** | job errored | `RECOMPUTE FAILED` — "Nothing was applied." + **Retry** / **Discard edit** | still showing old values |
| **applied** | new scoring live | `AVAILABILITY STALE` — projections current, availability simulated under old settings | projections fresh, availability hatched |

The banner sits between the top bar and the body, full width, and persists across navigation. It is
the only always-visible carrier of this state, so it must survive route changes.

### Status rail per state
Tag + one-sentence headline + a paragraph of what is true right now + the diff + actions. The copy
matters more than the layout here; the reference file carries the exact strings.

### Progress feedback
`recompute.stage` + `recompute.pct` from the backend, rendered as: percent at 26px in `--down`,
elapsed against `~60s`, a 5px bar, then the **stage list** with all five stages visible and each
marked ✓ done / ▸ active / · pending with its completion percent. A single indeterminate spinner is
not enough at this duration — the user needs to see that something specific is happening and roughly
how much is left. Stage names:

`reading game logs · 2023–2025` (18%) → `re-scoring 378 players` (46%) →
`refitting replacement levels` (72%) → `rebuilding tiers and VBD` (92%) →
`writing board.projected_points` (100%)

Also show `recompute.job_id` — it is what a support conversation needs.

### The diff
Per changed rule: label, in-force value struck through, arrow, new value in `--down`. Then one
honest impact line: *"Recomputes 378 player values — projections, replacement levels, VBD and tiers —
in about 60 seconds. Availability then needs its own 20,000-draft simulation."*

Count in the header (`2 rules`). With no edits, the panel states `league.pending_settings = null`
rather than showing an empty box.

---

## 5. Fresh / stale / null — three states, three treatments

| | Fresh | Stale | Null |
|---|---|---|---|
| **Means** | computed under the settings in force | a real number, computed under settings this league no longer has | no value exists — never computed, or not computable |
| **Value** | `41%` | `41%` | `—` |
| **Colour** | `--txt` | `--dim2` | `--dim2` |
| **Background** | none | 45° hatch, `--hatch` | none |
| **Glyph** | none | dagger `†` | em dash is itself the glyph |
| **Section cue** | none | `STALE` tag + generation timestamp | reason on hover |
| **Assistant** | quotable | **refuses to quote** | refuses to quote |

Stale carries **four** cues — hatch, dagger, reduced contrast, section tag — of which three survive
greyscale. Null carries no hatch, deliberately: there is nothing to invalidate. The distinction a
user must be able to make instantly is *stale vs null*, not *stale vs fresh*, because a stale number
looks plausible and a null one does not.

We keep showing stale numbers rather than blanking them. A wrong-but-labelled number is more useful
than a hole, and blanking would make a settings change feel like data loss.

---

## 6. Failure

A failed job needs no recovery flow, which is the second dividend of the shadow-recompute design.

Copy: *"The recompute failed. You are in a known-good state."* Then: which stage it stopped at, how
long it ran, and the reason there is nothing to unwind — *"Because values only ever change on an
explicit apply, there is no partial state to unwind."*

Fields surfaced: `recompute.job_id`, `recompute.failed_stage`, and the explicit statement
`league.settings unchanged · league.pending_settings retained`.

Actions: **Retry recompute** (same job from the start) and **Discard edit**. The edit is kept by
default — the user's typing is not the thing that failed.

`--fail` (`#e5544b` dark / `#c0392f` light) is a **new token**, separate from `--live`. Failure and
live-draft state must never share a colour: one is "pay attention, this is happening now" and the
other is "something broke".

---

## 7. Backend contract

```json
PATCH /api/leagues/:id/settings
{ "tier": 1, "settings": { "bench": 7 } }
→ { "applied": true, "replacement_levels": {...}, "availability_invalidated": true }

POST /api/leagues/:id/recompute
{ "pending_settings": { "ppr": 1.0, "ptd": 6 } }
→ { "job_id": "rc_8f21c4", "estimated_seconds": 60 }

GET /api/recompute/:job_id          (poll or stream)
→ { "job_id": "rc_8f21c4", "state": "running|complete|failed",
    "stage": "refitting replacement levels", "pct": 62,
    "failed_stage": null, "error": null }

POST /api/leagues/:id/recompute/:job_id/apply
→ { "applied_at": "...", "projections_generated_at": "...",
    "availability_stale": true }
```

**Contract requirements:**
- `apply` is a separate call from job completion. The server must hold the computed result until the
  client asks for it, and must not mutate `league.settings` before that call.
- A result is **superseded** if the pending settings change while it is held. Return
  `superseded: true` rather than applying a stale computation.
- `availability_stale` is returned by both endpoints. Tier-1 changes set it too.
- Job ownership is the **league**, not the session: navigating away, closing the tab, or another
  device must all see the same state.

---

## 8. Decisions for the founder

Marked rather than picked silently.

1. **Scoring edits during a live draft.** The reference blocks tier-2 edits while a draft is live —
   changing scoring mid-draft would rebase every recommendation the user has already acted on. But
   this is a product call about trust versus flexibility, not a design one. *(Recommendation: block,
   with the reason stated.)*
2. **Auto-apply when nobody is looking.** If the user starts a recompute and closes the tab, does the
   result apply on next open, or wait? *(Recommendation: wait. Ambush is worse than staleness.)*
3. **Superseded results.** If a user edits again mid-job, do we cancel and restart automatically, or
   ask? *(Recommendation: restart automatically and say so — a held result nobody wants is clutter.)*
4. **Who can edit.** Commissioner-only, or anyone with the league open? Not a design question, but it
   determines whether the banner needs an actor name.
